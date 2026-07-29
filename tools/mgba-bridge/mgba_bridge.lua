-- Phase 3A loopback bridge.
--
-- The ROM remains authoritative for move selection. This script only writes a
-- bounded response mailbox record, which Phase 3A ROM code deliberately ignores.

local function script_directory()
    local source = debug.getinfo(1, "S").source
    if type(source) ~= "string" or source:sub(1, 1) ~= "@" then
        error("BAGB startup failed: load mgba_bridge.lua from a file")
    end

    local path = source:sub(2)
    local directory = path:match("^(.*[\\/])")
    if directory == nil or directory == "" then
        error("BAGB startup failed: could not determine script directory")
    end

    return directory
end

local function load_required_file(directory, filename)
    local chunk, load_error = loadfile(directory .. filename)
    if chunk == nil then
        error("BAGB startup failed: could not load " .. filename .. ": " .. tostring(load_error))
    end

    local ok, run_error = pcall(chunk)
    if not ok then
        error("BAGB startup failed: could not run " .. filename .. ": " .. tostring(run_error))
    end
end

local directory = script_directory()
load_required_file(directory, "bridge_settings.lua")
load_required_file(directory, "generated/mailbox_address.lua")

if BRIDGE_HOST ~= "127.0.0.1" then
    error("BAGB startup failed: BRIDGE_HOST must be 127.0.0.1")
end

if type(BRIDGE_PORT) ~= "number" or BRIDGE_PORT ~= math.floor(BRIDGE_PORT)
    or BRIDGE_PORT < 1 or BRIDGE_PORT > 65535 then
    error("BAGB startup failed: BRIDGE_PORT must be an integer from 1 through 65535")
end

if type(MAX_LINE_BYTES) ~= "number" or MAX_LINE_BYTES ~= 96 then
    error("BAGB startup failed: MAX_LINE_BYTES must be 96")
end

if type(MAILBOX_ADDRESS) ~= "number" then
    error("BAGB startup failed: generated mailbox_address.lua did not set MAILBOX_ADDRESS")
end

local ok_console, console_log = pcall(function()
    return console.log
end)
if not ok_console or type(console_log) ~= "function" then
    error("BAGB startup failed: mGBA console.log is unavailable")
end

local function log(message)
    console:log(message)
end

-- mGBA exposes successful socket operations to Lua as numeric true (1), not
-- as the underlying C SOCKERR.OK value (0).
local LUA_SOCKET_SUCCESS = 1

if type(socket) ~= "table" or type(socket.bind) ~= "function" then
    error("BAGB startup failed: mGBA global socket.bind is unavailable")
end

local ok_bind, listener, bind_error = pcall(socket.bind, BRIDGE_HOST, BRIDGE_PORT)
if not ok_bind or listener == nil then
    error("BAGB startup failed: could not bind 127.0.0.1:" .. BRIDGE_PORT .. ": " .. tostring(bind_error))
end

local ok_listen, listen_result, listen_error = pcall(listener.listen, listener)
if not ok_listen or listen_result ~= LUA_SOCKET_SUCCESS then
    local reason = listen_error
    if not ok_listen then
        reason = listen_result
    elseif reason == nil then
        reason = listen_result
    end
    error("BAGB startup failed: could not listen on 127.0.0.1:" .. BRIDGE_PORT .. ": " .. tostring(reason))
end

local MAGIC = 0x42414732
local VERSION = 2
local REQUEST_PENDING = 1
local RESPONSE_READY = 1

local OFFSET_MAGIC = 0
local OFFSET_VERSION = 4
local OFFSET_REQUEST_STATUS = 6
local OFFSET_RESPONSE_STATUS = 7
local OFFSET_REQUEST_SEQUENCE = 8
local OFFSET_REQUESTING_BATTLER = 12
local OFFSET_BATTLE_MODE = 13
local OFFSET_SNAPSHOT = 16
local OFFSET_LEGAL_ACTION_COUNT = 464
local OFFSET_LEGAL_ACTIONS = 468
local OFFSET_RESPONSE_SEQUENCE = 500
local OFFSET_RESPONSE_ACTION_INDEX = 504

local REQUEST_PAYLOAD_SIZE = 417
local RESPONSE_PAYLOAD_SIZE = 5
local REQUEST_FRAME_SIZE = 425
local RESPONSE_FRAME_SIZE = 13
local BATTLER_SIZE = 48
local MOVE_SIZE = 12
local SNAPSHOT_BATTLER_MOVES = 240

local TRAINER_SINGLE = 1
local client_accepted = false
local client_socket = nil
local client_disconnected = false
local listener_disabled = false
local receive_buffer = ""
local forwarded_sequence = nil
local committed_sequence = nil

local function read_mailbox_header()
    local magic = emu:read32(MAILBOX_ADDRESS + OFFSET_MAGIC)
    local version = emu:read16(MAILBOX_ADDRESS + OFFSET_VERSION)
    if magic ~= MAGIC or version ~= VERSION then
        return nil
    end

    return {
        magic = magic,
        version = version,
        request_status = emu:read8(MAILBOX_ADDRESS + OFFSET_REQUEST_STATUS),
        sequence = emu:read32(MAILBOX_ADDRESS + OFFSET_REQUEST_SEQUENCE),
        requester = emu:read8(MAILBOX_ADDRESS + OFFSET_REQUESTING_BATTLER),
        battle_mode = emu:read8(MAILBOX_ADDRESS + OFFSET_BATTLE_MODE),
        action_count = emu:read8(MAILBOX_ADDRESS + OFFSET_LEGAL_ACTION_COUNT),
    }
end

local function is_forwardable(header)
    if header == nil then
        return false
    end

    return header.magic == MAGIC
        and header.version == VERSION
        and header.request_status == REQUEST_PENDING
        and header.requester >= 0 and header.requester <= 3
        and header.battle_mode == TRAINER_SINGLE
        and header.action_count >= 1 and header.action_count <= 4
end

local function disconnect_client(reason)
    if client_disconnected then
        return
    end

    client_disconnected = true
    client_socket = nil
    receive_buffer = ""
    log("BAGB client disconnected: " .. reason)
end

local function append_u8(parts, value)
    parts[#parts + 1] = string.char(value % 256)
end

local function append_u16(parts, value)
    append_u8(parts, value)
    append_u8(parts, math.floor(value / 256))
end

local function append_u32(parts, value)
    append_u16(parts, value)
    append_u16(parts, math.floor(value / 65536))
end

local function append_battler(parts, battler)
    local base = MAILBOX_ADDRESS + OFFSET_SNAPSHOT + battler * BATTLER_SIZE
    append_u16(parts, emu:read16(base)); append_u8(parts, emu:read8(base + 20))
    for offset = 21, 23 do append_u8(parts, emu:read8(base + offset)) end
    append_u16(parts, emu:read16(base + 24)); append_u16(parts, emu:read16(base + 26))
    append_u16(parts, emu:read16(base + 2)); append_u16(parts, emu:read16(base + 4))
    for offset = 28, 36, 2 do append_u16(parts, emu:read16(base + offset)) end
    append_u32(parts, emu:read32(base + 8)); append_u32(parts, emu:read32(base + 40)); append_u32(parts, emu:read32(base + 44))
    for offset = 12, 19 do append_u8(parts, emu:read8(base + offset)) end
    for slot = 0, 3 do
        local move = MAILBOX_ADDRESS + OFFSET_SNAPSHOT + SNAPSHOT_BATTLER_MOVES + (battler * 4 + slot) * MOVE_SIZE
        append_u16(parts, emu:read16(move)); append_u8(parts, emu:read8(move + 2)); append_u8(parts, emu:read8(move + 3)); append_u8(parts, emu:read8(move + 4)); append_u8(parts, emu:read8(move + 5)); append_u16(parts, emu:read16(move + 6)); append_u8(parts, emu:read8(move + 8)); append_u8(parts, emu:read8(move + 10)); append_u8(parts, emu:read8(move + 11)); append_u8(parts, 0)
    end
end

local function send_request(header)
    local payload = {}
    append_u32(payload, header.sequence)
    append_u8(payload, header.requester)
    append_u8(payload, header.battle_mode)
    append_u16(payload, emu:read16(MAILBOX_ADDRESS + 14))
    append_u8(payload, 2)
    for battler = 0, 3 do append_battler(payload, battler) end
    append_u16(payload, emu:read16(MAILBOX_ADDRESS + 448))
    append_u8(payload, emu:read8(MAILBOX_ADDRESS + 450))
    append_u32(payload, emu:read32(MAILBOX_ADDRESS + 452))
    append_u32(payload, emu:read32(MAILBOX_ADDRESS + 456))
    append_u32(payload, emu:read32(MAILBOX_ADDRESS + 460))
    append_u8(payload, header.action_count)
    for index = 0, 3 do
        local action = MAILBOX_ADDRESS + OFFSET_LEGAL_ACTIONS + index * 8
        for field = 0, 5 do append_u8(payload, emu:read8(action + field)) end
    end
    local payload_bytes = table.concat(payload)
    if #payload_bytes ~= REQUEST_PAYLOAD_SIZE then
        disconnect_client("request assembly has invalid size: " .. #payload_bytes)
        return false
    end
    local request_frame = "BAGB" .. string.char(VERSION, 1, REQUEST_PAYLOAD_SIZE % 256, math.floor(REQUEST_PAYLOAD_SIZE / 256)) .. payload_bytes
    local ok_send, send_result, send_error = pcall(client_socket.send, client_socket, request_frame)
    if not ok_send or send_result == nil or send_result ~= #request_frame then
        local reason = send_error
        if not ok_send then
            reason = send_result
        end
        disconnect_client("could not forward request: " .. tostring(reason))
        return false
    end

    receive_buffer = ""
    forwarded_sequence = header.sequence
    log("BAGB request forwarded: " .. header.sequence)
    return true
end

local function parse_response_frame(frame)
    if #frame ~= RESPONSE_FRAME_SIZE
     or frame:sub(1, 4) ~= "BAGB"
     or string.byte(frame, 5) ~= VERSION
     or string.byte(frame, 6) ~= 2
     or string.byte(frame, 7) ~= RESPONSE_PAYLOAD_SIZE
     or string.byte(frame, 8) ~= 0 then
        return nil
    end
    local sequence = string.byte(frame, 9) + string.byte(frame, 10) * 256 + string.byte(frame, 11) * 65536 + string.byte(frame, 12) * 16777216
    local action_index = string.byte(frame, 13)
    if action_index > 3 then
        return nil
    end

    return {
        sequence = sequence,
        action_index = action_index,
    }
end

local function response_matches_current(response)
    local header = read_mailbox_header()
    return is_forwardable(header)
        and forwarded_sequence == response.sequence
        and committed_sequence ~= response.sequence
        and header.sequence == response.sequence
        and response.action_index < header.action_count
end

local function commit_response(response)
    if not response_matches_current(response) then
        log("BAGB response rejected")
        return false
    end

    emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)
    emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEX, response.action_index)
    emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_STATUS, RESPONSE_READY)
    committed_sequence = response.sequence
    log("BAGB response written: " .. response.sequence)
    return true
end

local function disable_listener(reason)
    if listener_disabled then
        return
    end

    listener_disabled = true
    log("BAGB listener disabled: " .. reason)
end

local function on_frame()
    if listener_disabled then
        return
    end

    if not client_accepted then
        local ok_ready, ready, ready_error = pcall(listener.hasdata, listener)
        if not ok_ready or ready == nil then
            local reason = ready_error
            if not ok_ready then
                reason = ready
            end
            disable_listener("error while polling for a client: " .. tostring(reason))
            return
        end

        if ready ~= true and ready ~= 1 then
            return
        end

        local ok_accept, client, accept_error = pcall(listener.accept, listener)
        if not ok_accept then
            disable_listener("error while accepting a client: " .. tostring(client))
            return
        end

        if client == nil then
            disable_listener("reported a pending client but accepted none: " .. tostring(accept_error))
            return
        end

        client_socket = client
        client_accepted = true
        log("BAGB client connected")
        return
    end

    if client_disconnected or client_socket == nil then
        return
    end

    local header = read_mailbox_header()
    if is_forwardable(header) and forwarded_sequence ~= header.sequence then
        send_request(header)
        return
    end

    local ok_ready, ready, ready_error = pcall(client_socket.hasdata, client_socket)
    if not ok_ready or ready == nil then
        local reason = ready_error
        if not ok_ready then
            reason = ready
        end
        disconnect_client("error while polling for response: " .. tostring(reason))
        return
    end

    if ready ~= true and ready ~= 1 then
        return
    end

    if #receive_buffer >= RESPONSE_FRAME_SIZE then
        disconnect_client("response frame exceeded 13 bytes")
        return
    end

    local ok_receive, chunk, receive_error = pcall(
        client_socket.receive,
        client_socket,
        RESPONSE_FRAME_SIZE - #receive_buffer
    )
    if not ok_receive or chunk == nil then
        local reason = receive_error
        if not ok_receive then
            reason = chunk
        end
        disconnect_client("response receive failed: " .. tostring(reason))
        return
    end

    receive_buffer = receive_buffer .. chunk
    if #receive_buffer > RESPONSE_FRAME_SIZE then
        disconnect_client("response frame has extra bytes")
        return
    end
    if #receive_buffer < RESPONSE_FRAME_SIZE then
        return
    end
    local frame = receive_buffer
    receive_buffer = ""
    local response = parse_response_frame(frame)
    if response == nil then
        disconnect_client("malformed response")
        return
    end

    commit_response(response)
end

callbacks:add("frame", on_frame)
log("BAGB listener ready 127.0.0.1:" .. BRIDGE_PORT)
