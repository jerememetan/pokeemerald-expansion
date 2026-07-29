"""Local, tool-only decision helpers for the BAGB/2 trainer agent."""

from __future__ import annotations

import json
import argparse
import socket
import struct
import time
from pathlib import Path
from urllib.request import Request, urlopen

from bridge_protocol import LegalAction, REQUEST_FRAME_SIZE, format_response_frame, parse_request_frame


class ToolError(ValueError):
    """Raised when a model attempts an unavailable or illegal action."""


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:7b"
MAX_TOOL_CALLS = 12
SERVICE_TIMEOUT_SECONDS = 12.0
CATALOG_PATH = Path(__file__).with_name("catalog_v2.json")


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, dict[str, str]]:
    """Load the checked-in labels used only for already-authorized snapshot IDs."""
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ToolError("battle-agent catalog is unavailable") from error
    if not isinstance(catalog, dict) or any(not isinstance(catalog.get(key), dict) for key in ("species", "moves", "abilities", "items", "effects")):
        raise ToolError("battle-agent catalog is malformed")
    return catalog


CATALOG = load_catalog()


def log(message: str) -> None:
    """Emit concise local diagnostics; no battle data is persisted."""
    print(f"BAGB service: {message}", flush=True)


def _label(category: str, value: int) -> str:
    return CATALOG[category].get(str(value), "UNKNOWN")

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "get_battle_state", "description": "Read request metadata.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_field_state", "description": "Read weather, terrain, and side conditions.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_battler", "description": "Read one active battler.", "parameters": {"type": "object", "properties": {"battler_id": {"type": "integer"}}, "required": ["battler_id"]}}},
    {"type": "function", "function": {"name": "get_battler_moves", "description": "Read one active battler's moves.", "parameters": {"type": "object", "properties": {"battler_id": {"type": "integer"}}, "required": ["battler_id"]}}},
    {"type": "function", "function": {"name": "list_legal_actions", "description": "List ROM-authorized action indexes.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "analyze_action", "description": "Read ROM-derived facts for one legal action.", "parameters": {"type": "object", "properties": {"action_index": {"type": "integer"}}, "required": ["action_index"]}}},
    {"type": "function", "function": {"name": "compare_speed", "description": "Compare active battlers' normal speed order; move priority can override it.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "choose_action", "description": "Terminally select one legal action index.", "parameters": {"type": "object", "properties": {"action_index": {"type": "integer"}}, "required": ["action_index"]}}},
]


def _battler_offset(battler_id: int) -> int:
    if isinstance(battler_id, bool) or not isinstance(battler_id, int) or not 0 <= battler_id < 2:
        raise ToolError("battler_id must identify an active battler")
    return 9 + battler_id * 92


def get_battler(payload: bytes, battler_id: int) -> dict[str, int | list[int]]:
    """Decode one active battler from the canonical V2 request payload."""
    offset = _battler_offset(battler_id)
    species, = struct.unpack_from("<H", payload, offset)
    ability, item, hp, max_hp = struct.unpack_from("<HHHH", payload, offset + 6)
    level, type1, type2, type3 = payload[offset + 2], payload[offset + 3], payload[offset + 4], payload[offset + 5]
    attack, defense, speed, sp_attack, sp_defense = struct.unpack_from("<HHHHH", payload, offset + 14)
    status1, status2, status3 = struct.unpack_from("<III", payload, offset + 24)
    return {"battler_id": battler_id, "species": species, "species_name": _label("species", species), "level": level, "types": [type1, type2, type3], "ability": ability, "ability_name": _label("abilities", ability), "item": item, "item_name": _label("items", item), "hp": hp, "max_hp": max_hp, "attack": attack, "defense": defense, "speed": speed, "sp_attack": sp_attack, "sp_defense": sp_defense, "status1": status1, "status2": status2, "status3": status3, "stat_stages": list(payload[offset + 36 : offset + 44])}


def get_battler_moves(payload: bytes, battler_id: int) -> list[dict[str, int]]:
    """Decode the four fixed-width move records for one active battler."""
    offset = _battler_offset(battler_id) + 44
    moves = []
    for slot in range(4):
        move, pp, move_type, power, accuracy, effect, target, priority, split, _ = struct.unpack_from("<HBBBBHBbBB", payload, offset + slot * 12)
        moves.append({"slot": slot, "move": move, "move_name": _label("moves", move), "pp": pp, "type": move_type, "power": power, "accuracy": accuracy, "effect": effect, "effect_name": _label("effects", effect), "target_category": target, "priority": priority, "split": split})
    return moves


def get_field_state(payload: bytes) -> dict[str, int | list[int]]:
    """Decode field and side status data from the canonical V2 payload."""
    weather, = struct.unpack_from("<H", payload, 377)
    field_statuses, player_side, opponent_side = struct.unpack_from("<III", payload, 380)
    return {"weather": weather, "terrain": payload[379], "field_statuses": field_statuses, "side_statuses": [player_side, opponent_side]}


def get_battle_state(*, sequence: int, turn_sequence: int, requesting_battler: int, payload: bytes) -> dict[str, object]:
    """Return request metadata and the two active battler snapshots."""
    return {
        "request_sequence": sequence,
        "turn_sequence": turn_sequence,
        "requesting_battler": requesting_battler,
        "active_battlers": [get_battler(payload, 0), get_battler(payload, 1)],
    }


def list_legal_actions(actions: tuple[LegalAction, ...]) -> list[dict[str, int]]:
    """Expose ROM-authorized action indexes without granting move/target authority."""
    return [{"action_index": action.action_index, "move_slot": action.move_slot, "target_battler": action.target_battler} for action in actions]


def choose_action(actions: tuple[LegalAction, ...], action_index: int) -> int:
    """Validate the terminal model choice against the current ROM action list."""
    if isinstance(action_index, bool) or not isinstance(action_index, int):
        raise ToolError("action_index must be an integer")
    if any(action.action_index == action_index for action in actions):
        return action_index
    raise ToolError("action_index is not legal for this request")


def analyze_action(actions: tuple[LegalAction, ...], action_index: int, requester_moves: list[dict[str, int]] | None = None) -> dict[str, int | bool | str]:
    """Expose the ROM's deterministic analysis for one legal action."""
    for action in actions:
        if action.action_index == action_index:
            result: dict[str, int | bool | str] = {
                "action_index": action.action_index,
                "move_slot": action.move_slot,
                "target_battler": action.target_battler,
                "type_effectiveness": action.type_effectiveness,
                "has_stab": bool(action.has_stab),
                "can_faint_target": bool(action.can_faint_target),
            }
            if requester_moves is not None:
                result.update(requester_moves[action.move_slot])
            return result
    raise ToolError("action_index is not legal for this request")


def compare_speed(payload: bytes) -> dict[str, int | str]:
    """Compare current active-battler speed while warning that priority wins first."""
    battler_0_speed = get_battler(payload, 0)["speed"]
    battler_1_speed = get_battler(payload, 1)["speed"]
    if battler_0_speed > battler_1_speed:
        order = "battler_0_first"
    elif battler_1_speed > battler_0_speed:
        order = "battler_1_first"
    else:
        order = "speed_tie"
    return {
        "battler_0_speed": battler_0_speed,
        "battler_1_speed": battler_1_speed,
        "normal_order": order,
        "note": "Move priority can override normal speed order.",
    }


def request_ollama(messages: list[dict[str, object]]) -> dict[str, object]:
    """Call only the local Ollama chat endpoint with the bounded tool schema."""
    body = json.dumps({"model": OLLAMA_MODEL, "stream": False, "messages": messages, "tools": TOOL_SCHEMAS}).encode()
    request = Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=SERVICE_TIMEOUT_SECONDS) as response:
        decoded = json.loads(response.read().decode())
    if not isinstance(decoded, dict) or not isinstance(decoded.get("message"), dict):
        raise ToolError("Ollama response has no message object")
    return decoded["message"]


def extract_tool_call(message: dict[str, object]) -> tuple[str, dict[str, object]] | None:
    """Normalize one native Ollama call or qwen's exact JSON-content form."""
    calls = message.get("tool_calls")
    if isinstance(calls, list) and len(calls) == 1 and isinstance(calls[0], dict):
        function = calls[0].get("function")
        if isinstance(function, dict) and isinstance(function.get("name"), str) and isinstance(function.get("arguments"), dict):
            return function["name"], function["arguments"]
        return None

    content = message.get("content")
    if not isinstance(content, str):
        return None
    try:
        compatibility_call = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(compatibility_call, dict) or set(compatibility_call) != {"name", "arguments"}:
        return None
    if not isinstance(compatibility_call["name"], str) or not isinstance(compatibility_call["arguments"], dict):
        return None
    return compatibility_call["name"], compatibility_call["arguments"]


def run_tool_agent(sequence: int, turn_sequence: int, requesting_battler: int, actions: tuple[LegalAction, ...], payload: bytes) -> int | None:
    """Run a bounded local model/tool exchange and return one legal index or None."""
    messages: list[dict[str, object]] = [{"role": "system", "content": "Use only the supplied read-only tools to inspect this battle. Do not answer in text. Finish exactly once with choose_action using a legal action_index."}]
    started = time.monotonic()
    for _ in range(MAX_TOOL_CALLS):
        if time.monotonic() - started >= SERVICE_TIMEOUT_SECONDS:
            return None
        try:
            message = request_ollama(messages)
            tool_call = extract_tool_call(message)
            if tool_call is None:
                return None
            name, arguments = tool_call
            log(f"request {sequence} tool {name}")
            if name == "choose_action":
                action_index = choose_action(actions, arguments.get("action_index"))
                log(f"request {sequence} chose action {action_index}")
                return action_index
            if name == "get_battle_state" and not arguments:
                result = get_battle_state(sequence=sequence, turn_sequence=turn_sequence, requesting_battler=requesting_battler, payload=payload)
            elif name == "get_field_state" and not arguments:
                result = get_field_state(payload)
            elif name == "get_battler" and set(arguments) == {"battler_id"}:
                result = get_battler(payload, arguments["battler_id"])
            elif name == "get_battler_moves" and set(arguments) == {"battler_id"}:
                result = get_battler_moves(payload, arguments["battler_id"])
            elif name == "list_legal_actions" and not arguments:
                result = list_legal_actions(actions)
            elif name == "analyze_action" and set(arguments) == {"action_index"}:
                result = analyze_action(actions, arguments["action_index"], get_battler_moves(payload, requesting_battler))
            elif name == "compare_speed" and not arguments:
                result = compare_speed(payload)
            else:
                return None
            messages.append(message)
            messages.append({"role": "tool", "content": json.dumps(result)})
        except (OSError, ValueError, ToolError) as error:
            log(f"request {sequence} rejected: {error}")
            return None
    return None


def handle_request_frame(frame: bytes) -> bytes | None:
    """Decode one bridge request and return a response only for a valid model choice."""
    request = parse_request_frame(frame)
    log(f"request {request.sequence} received")
    action_index = run_tool_agent(
        request.sequence,
        request.turn_sequence,
        request.requesting_battler,
        request.legal_actions,
        request.payload,
    )
    if action_index is None:
        log(f"request {request.sequence} produced no response")
        return None
    return format_response_frame(request.sequence, action_index)


def serve(host: str = "127.0.0.1", port: int = 57621) -> None:
    """Serve one loopback client; malformed/incomplete frames receive no response."""
    if host != "127.0.0.1":
        raise ValueError("battle-agent service binds only to loopback")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen(1)
        log(f"listening on {host}:{port}")
        while True:
            connection, _ = listener.accept()
            with connection:
                log("bridge connected")
                buffer = b""
                while True:
                    chunk = connection.recv(REQUEST_FRAME_SIZE - len(buffer))
                    if not chunk:
                        break
                    buffer += chunk
                    if len(buffer) != REQUEST_FRAME_SIZE:
                        continue
                    try:
                        response = handle_request_frame(buffer)
                    except (ToolError, ValueError):
                        response = None
                    if response is not None:
                        connection.sendall(response)
                    buffer = b""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=57621)
    args = parser.parse_args()
    serve(args.host, args.port)


if __name__ == "__main__":
    main()
