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
local VERSION = 5
local REQUEST_PENDING = 1
local RESPONSE_READY = 1

local OFFSET_MAGIC = 0
local OFFSET_VERSION = 4
local OFFSET_REQUEST_STATUS = 6
local OFFSET_RESPONSE_STATUS = 7
local OFFSET_REQUEST_SEQUENCE = 8
local OFFSET_BATTLE_MODE = 12
local OFFSET_CONTROLLED_COUNT = 13
local OFFSET_TURN_SEQUENCE = 14
local OFFSET_BATTLER_COUNT = 16
local OFFSET_CONTROLLED_BATTLERS = 17
local OFFSET_LEGAL_ACTION_COUNTS = 19
local OFFSET_SNAPSHOT = 24
local OFFSET_LEGAL_ACTIONS = 1072
local OFFSET_RESPONSE_SEQUENCE = 1468
local OFFSET_RESPONSE_ACTION_COUNT = 1472
local OFFSET_RESPONSE_BATTLERS = 1473
local OFFSET_RESPONSE_ACTION_INDEXES = 1475

local REQUEST_PAYLOAD_SIZE = 1369
local RESPONSE_PAYLOAD_SIZE = 9
local REQUEST_FRAME_SIZE = 1377
local RESPONSE_FRAME_SIZE = 17
local BATTLER_SIZE = 48
local MOVE_SIZE = 12
local SNAPSHOT_BATTLER_MOVES = 240
local SNAPSHOT_PARTY = 448
local PARTY_SIZE = 6
local PARTY_RECORD_SIZE = 100

local TRAINER_SINGLE = 1
local TRAINER_DOUBLE = 2
local TRAINER_TWO_OPPONENT_DOUBLE = 3
local MAX_ACTIONS_PER_BATTLER = 22
local ACTION_RECORD_SIZE = 9
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
        battle_mode = emu:read8(MAILBOX_ADDRESS + OFFSET_BATTLE_MODE),
        controlled_count = emu:read8(MAILBOX_ADDRESS + OFFSET_CONTROLLED_COUNT),
        battler_count = emu:read8(MAILBOX_ADDRESS + OFFSET_BATTLER_COUNT),
        controlled = {
            emu:read8(MAILBOX_ADDRESS + OFFSET_CONTROLLED_BATTLERS),
            emu:read8(MAILBOX_ADDRESS + OFFSET_CONTROLLED_BATTLERS + 1),
        },
        action_counts = {
            emu:read8(MAILBOX_ADDRESS + OFFSET_LEGAL_ACTION_COUNTS),
            emu:read8(MAILBOX_ADDRESS + OFFSET_LEGAL_ACTION_COUNTS + 1),
        },
    }
end

local function is_forwardable(header)
    if header == nil then
        return false
    end

    return header.magic == MAGIC
        and header.version == VERSION
        and header.request_status == REQUEST_PENDING
        and (header.battle_mode == TRAINER_SINGLE
            or header.battle_mode == TRAINER_DOUBLE
            or header.battle_mode == TRAINER_TWO_OPPONENT_DOUBLE)
        and header.controlled_count >= 1 and header.controlled_count <= 2
        and header.battler_count >= 2 and header.battler_count <= 4
        and header.controlled[1] >= 0 and header.controlled[1] <= 3
        and header.action_counts[1] >= 1 and header.action_counts[1] <= MAX_ACTIONS_PER_BATTLER
        and (header.controlled_count == 1 or (header.controlled[2] >= 0 and header.controlled[2] <= 3 and header.controlled[1] ~= header.controlled[2] and header.action_counts[2] >= 1 and header.action_counts[2] <= MAX_ACTIONS_PER_BATTLER))
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

local function append_battler_record(parts, base, moves_base)
    append_u16(parts, emu:read16(base)); append_u8(parts, emu:read8(base + 20))
    for offset = 21, 23 do append_u8(parts, emu:read8(base + offset)) end
    append_u16(parts, emu:read16(base + 24)); append_u16(parts, emu:read16(base + 26))
    append_u16(parts, emu:read16(base + 2)); append_u16(parts, emu:read16(base + 4))
    for offset = 28, 36, 2 do append_u16(parts, emu:read16(base + offset)) end
    append_u32(parts, emu:read32(base + 8)); append_u32(parts, emu:read32(base + 40)); append_u32(parts, emu:read32(base + 44))
    for offset = 12, 19 do append_u8(parts, emu:read8(base + offset)) end
    for slot = 0, 3 do
        local move = moves_base + slot * MOVE_SIZE
        append_u16(parts, emu:read16(move)); append_u8(parts, emu:read8(move + 2)); append_u8(parts, emu:read8(move + 3)); append_u8(parts, emu:read8(move + 4)); append_u8(parts, emu:read8(move + 5)); append_u16(parts, emu:read16(move + 6)); append_u8(parts, emu:read8(move + 8)); append_u8(parts, emu:read8(move + 10)); append_u8(parts, emu:read8(move + 11)); append_u8(parts, 0)
    end
end

local function append_battler(parts, battler)
    local base = MAILBOX_ADDRESS + OFFSET_SNAPSHOT + battler * BATTLER_SIZE
    local moves_base = MAILBOX_ADDRESS + OFFSET_SNAPSHOT + SNAPSHOT_BATTLER_MOVES + battler * 4 * MOVE_SIZE
    append_battler_record(parts, base, moves_base)
end

local function append_party_member(parts, slot)
    local base = MAILBOX_ADDRESS + OFFSET_SNAPSHOT + SNAPSHOT_PARTY + slot * PARTY_RECORD_SIZE
    append_u8(parts, slot)
    append_u8(parts, emu:read8(base + 96))
    append_u8(parts, emu:read8(base + 97))
    append_u8(parts, emu:read8(base + 98))
    append_battler_record(parts, base, base + BATTLER_SIZE)
end

local function send_request(header)
    local payload = {}
    append_u32(payload, header.sequence)
    append_u8(payload, header.battle_mode)
    append_u8(payload, header.controlled_count)
    append_u16(payload, emu:read16(MAILBOX_ADDRESS + OFFSET_TURN_SEQUENCE))
    append_u8(payload, header.battler_count)
    append_u8(payload, header.controlled[1])
    append_u8(payload, header.controlled[2])
    append_u8(payload, header.action_counts[1])
    append_u8(payload, header.action_counts[2])
    append_u8(payload, 0)
    for battler = 0, 3 do append_battler(payload, battler) end
    append_u16(payload, emu:read16(MAILBOX_ADDRESS + OFFSET_SNAPSHOT + 432))
    append_u8(payload, emu:read8(MAILBOX_ADDRESS + OFFSET_SNAPSHOT + 434))
    append_u32(payload, emu:read32(MAILBOX_ADDRESS + OFFSET_SNAPSHOT + 436))
    append_u32(payload, emu:read32(MAILBOX_ADDRESS + OFFSET_SNAPSHOT + 440))
    append_u32(payload, emu:read32(MAILBOX_ADDRESS + OFFSET_SNAPSHOT + 444))
    for slot = 0, PARTY_SIZE - 1 do append_party_member(payload, slot) end
    for list = 0, 1 do
        for index = 0, MAX_ACTIONS_PER_BATTLER - 1 do
            local action = MAILBOX_ADDRESS + OFFSET_LEGAL_ACTIONS + (list * MAX_ACTIONS_PER_BATTLER + index) * ACTION_RECORD_SIZE
            for field = 0, ACTION_RECORD_SIZE - 1 do append_u8(payload, emu:read8(action + field)) end
        end
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
    local action_count = string.byte(frame, 13)
    local battler_one = string.byte(frame, 14)
    local action_one = string.byte(frame, 15)
    local battler_two = string.byte(frame, 16)
    local action_two = string.byte(frame, 17)
    if action_count < 1 or action_count > 2 or battler_one > 3 or action_one >= MAX_ACTIONS_PER_BATTLER
     or (action_count == 1 and (battler_two ~= 255 or action_two ~= 255))
     or (action_count == 2 and (battler_two > 3 or action_two >= MAX_ACTIONS_PER_BATTLER or battler_one == battler_two)) then
        return nil
    end

    return {
        sequence = sequence,
        action_count = action_count,
        battlers = {battler_one, battler_two},
        action_indexes = {action_one, action_two},
    }
end

local function response_matches_current(response)
    local header = read_mailbox_header()
    return is_forwardable(header)
        and forwarded_sequence == response.sequence
        and committed_sequence ~= response.sequence
        and header.sequence == response.sequence
        and response.action_count == header.controlled_count
        and response.battlers[1] == header.controlled[1]
        and response.action_indexes[1] < header.action_counts[1]
        and (response.action_count == 1 or (response.battlers[2] == header.controlled[2] and response.action_indexes[2] < header.action_counts[2]))
end

local function commit_response(response)
    if not response_matches_current(response) then
        log("BAGB response rejected")
        return false
    end

    emu:write32(MAILBOX_ADDRESS + OFFSET_RESPONSE_SEQUENCE, response.sequence)
    emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_COUNT, response.action_count)
    emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_BATTLERS, response.battlers[1])
    emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_BATTLERS + 1, response.battlers[2])
    emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEXES, response.action_indexes[1])
    emu:write8(MAILBOX_ADDRESS + OFFSET_RESPONSE_ACTION_INDEXES + 1, response.action_indexes[2])
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
        disconnect_client("response frame exceeded 17 bytes")
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
