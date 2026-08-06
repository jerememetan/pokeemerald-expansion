"""Local, tool-only decision helpers for the BAGB/4 trainer agent."""

from __future__ import annotations

import json
import argparse
import socket
import struct
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from bridge_protocol import (
    ACTION_KIND_MOVE,
    ACTION_KIND_SWITCH,
    LegalAction,
    REQUEST_FRAME_SIZE,
    format_response_frame,
    parse_request_frame,
)


class ToolError(ValueError):
    """Raised when a model attempts an unavailable or illegal action."""


class ModelSelectionError(RuntimeError):
    """Raised before bridge startup when no local Ollama model is available."""


@dataclass(frozen=True)
class AgentDecision:
    """Validated actor-keyed model actions and the read-only tools used."""

    actions: tuple[tuple[int, int], ...]
    tools_used: tuple[str, ...]


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:7b"
PREFERRED_OLLAMA_MODEL = OLLAMA_MODEL
MAX_TOOL_CALLS = 12
OLLAMA_RESPONSE_TIMEOUT_SECONDS = 20.0
TOOL_EXCHANGE_TIMEOUT_SECONDS = 45.0
MODEL_RESPONSE_PREVIEW_LIMIT = 240
FORMAT_RETRY_MESSAGE = (
    "Your previous reply was not a valid tool call. Reply with exactly one "
    "supported tool call; do not answer in prose or malformed JSON."
)
CATALOG_PATH = Path(__file__).with_name("catalog_v2.json")
LOOPBACK_HOST = "127.0.0.1"
TYPE_NAMES = ("NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG", "GHOST", "STEEL", "MYSTERY", "FIRE", "WATER", "GRASS", "ELECTRIC", "PSYCHIC", "ICE", "DRAGON", "DARK", "FAIRY")
STAT_CHANGE_NAMES = ("attack", "defense", "speed", "special_attack", "special_defense", "accuracy", "evasion")


def parse_ollama_model_list(output: str) -> tuple[str, ...]:
    """Return installed model names from the human-readable `ollama list` table."""
    models = []
    for line in output.splitlines():
        fields = line.split()
        if fields and fields[0] != "NAME":
            models.append(fields[0])
    return tuple(models)


def default_model_index(models: tuple[str, ...]) -> int:
    """Prefer the established Qwen default when it is locally installed."""
    if PREFERRED_OLLAMA_MODEL in models:
        return models.index(PREFERRED_OLLAMA_MODEL)
    return 0


def advance_model_index(index: int, delta: int, count: int) -> int:
    """Move through a non-empty model list, wrapping at either end."""
    return (index + delta) % count


def decode_types(raw_types: tuple[int, int, int]) -> list[str]:
    """Return unique non-placeholder type names from ROM type IDs."""
    return list(dict.fromkeys(TYPE_NAMES[type_id] for type_id in raw_types if 0 <= type_id < len(TYPE_NAMES) and type_id != 9))


def decode_major_status(status1: int) -> list[str]:
    """Name persistent major statuses; volatile bitfields remain separate."""
    if status1 & 7:
        return ["SLEEP"]
    for bit, name in ((1 << 3, "POISON"), (1 << 4, "BURN"), (1 << 5, "FREEZE"), (1 << 6, "PARALYSIS"), (1 << 7, "TOXIC_POISON"), (1 << 12, "FROSTBITE")):
        if status1 & bit:
            return [name]
    return []


def decode_stat_changes(raw_stages: tuple[int, ...]) -> dict[str, int]:
    """Convert engine stages with neutral value six to signed named deltas."""
    return {name: raw_stages[index] - 6 for index, name in enumerate(STAT_CHANGE_NAMES)}


def decode_volatile_status(status2: int, status3: int) -> list[str]:
    """Name directly published battle-only effects, omitting timer/source bits."""
    status2_flags = ((7, "CONFUSION"), (1 << 3, "FLINCHED"), (0x70, "UPROAR"), (0x300, "BIDE"), (0xC00, "LOCK_CONFUSE"), (1 << 12, "MULTIPLETURNS"), (1 << 13, "WRAPPED"), (1 << 14, "POWDER"), (0xF0000, "INFATUATION"), (1 << 20, "FOCUS_ENERGY"), (1 << 21, "TRANSFORMED"), (1 << 22, "RECHARGE"), (1 << 23, "RAGE"), (1 << 24, "SUBSTITUTE"), (1 << 25, "DESTINY_BOND"), (1 << 26, "ESCAPE_PREVENTION"), (1 << 27, "NIGHTMARE"), (1 << 28, "CURSED"), (1 << 29, "FORESIGHT"), (1 << 30, "DEFENSE_CURL"), (1 << 31, "TORMENT"))
    status3_flags = ((1 << 2, "LEECH_SEED"), (0x18, "ALWAYS_HITS"), (1 << 5, "PERISH_SONG"), (1 << 6, "ON_AIR"), (1 << 7, "UNDERGROUND"), (1 << 8, "MINIMIZED"), (1 << 9, "CHARGED_UP"), (1 << 10, "ROOTED"), (0x1800, "YAWN"), (1 << 13, "IMPRISONED_OTHERS"), (1 << 14, "GRUDGE"), (1 << 15, "CANT_SCORE_A_CRIT"), (1 << 16, "GASTRO_ACID"), (1 << 17, "EMBARGO"), (1 << 18, "UNDERWATER"), (1 << 21, "SMACKED_DOWN"), (1 << 22, "ME_FIRST"), (1 << 23, "TELEKINESIS"), (1 << 24, "PHANTOM_FORCE"), (1 << 25, "MIRACLE_EYE"), (1 << 26, "MAGNET_RISE"), (1 << 27, "HEAL_BLOCK"), (1 << 28, "AQUA_RING"), (1 << 29, "LASER_FOCUS"), (1 << 30, "POWER_TRICK"), (1 << 31, "SKY_DROPPED"))
    return [name for flag, name in status2_flags if status2 & flag] + [name for flag, name in status3_flags if status3 & flag]


def decode_field_state(weather: int, terrain: int, field: int, player_side: int, opponent_side: int) -> dict[str, object]:
    """Convert published weather and effect flags into names for the local agent."""
    weather_flags = ((0xF, "RAIN"), (0x30, "SANDSTORM"), (0x1C0, "SUN"), (0x600, "HAIL"), (1 << 11, "STRONG_WINDS"), (0x3000, "SNOW"))
    field_flags = ((1 << 0, "MAGIC_ROOM"), (1 << 1, "TRICK_ROOM"), (1 << 2, "WONDER_ROOM"), (1 << 3, "MUD_SPORT"), (1 << 4, "WATER_SPORT"), (1 << 5, "GRAVITY"), (1 << 6, "GRASSY_TERRAIN"), (1 << 7, "MISTY_TERRAIN"), (1 << 8, "ELECTRIC_TERRAIN"), (1 << 9, "PSYCHIC_TERRAIN"), (1 << 10, "ION_DELUGE"), (1 << 11, "FAIRY_LOCK"))
    side_flags = ((1 << 0, "REFLECT"), (1 << 1, "LIGHT_SCREEN"), (1 << 2, "STICKY_WEB"), (1 << 4, "SPIKES"), (1 << 5, "SAFEGUARD"), (1 << 8, "MIST"), (1 << 10, "TAILWIND"), (1 << 11, "AURORA_VEIL"), (1 << 13, "TOXIC_SPIKES"), (1 << 14, "STEALTH_ROCK"), (1 << 18, "QUICK_GUARD"), (1 << 19, "WIDE_GUARD"), (1 << 22, "STEELSURGE"))
    terrain_names = ("GRASS", "LONG_GRASS", "SAND", "UNDERWATER", "WATER", "POND", "MOUNTAIN", "CAVE", "BUILDING", "PLAIN")
    names = lambda value, flags: [name for flag, name in flags if value & flag]
    return {"weather": names(weather, weather_flags), "terrain": terrain_names[terrain] if 0 <= terrain < len(terrain_names) else "UNKNOWN", "field_effects": names(field, field_flags), "player_side_effects": names(player_side, side_flags), "opponent_side_effects": names(opponent_side, side_flags)}


def decode_move_target(target: int) -> str:
    """Name the move-targeting category published by the battle engine."""
    return {0: "SELECTED_TARGET", 1: "DEPENDS", 2: "USER_OR_SELECTED", 4: "RANDOM_OPPONENT", 8: "BOTH_OPPONENTS", 16: "USER", 32: "FOES_AND_ALLY", 64: "OPPONENTS_FIELD", 128: "ALLY", 272: "ALL_BATTLERS"}.get(target, "UNKNOWN")


def decode_move_split(split: int) -> str:
    """Name the physical/special/status category of a move."""
    return ("PHYSICAL", "SPECIAL", "STATUS")[split] if 0 <= split <= 2 else "UNKNOWN"


def discover_ollama_models() -> tuple[str, ...]:
    """List locally installed Ollama models without contacting mGBA."""
    try:
        completed = subprocess.run(["ollama", "list"], check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise ModelSelectionError("No local Ollama models found. Run 'ollama list' or 'ollama pull <model>'.") from error
    models = parse_ollama_model_list(completed.stdout)
    if not models:
        raise ModelSelectionError("No local Ollama models found. Run 'ollama list' or 'ollama pull <model>'.")
    return models


def select_ollama_model(models: tuple[str, ...]) -> str:
    """Select a local model, using arrow keys in an interactive Windows terminal."""
    index = default_model_index(models)
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return models[index]
    if sys.platform != "win32":
        for number, model in enumerate(models, 1):
            print(f"{number}. {model}")
        answer = input(f"Select model [{index + 1}]: ").strip()
        return models[int(answer) - 1] if answer else models[index]
    import msvcrt
    while True:
        print("\nSelect local Ollama model (Up/Down, Enter):")
        for number, model in enumerate(models):
            print(f"{'>' if number == index else ' '} {model}")
        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            key = msvcrt.getwch()
        if key == "H":
            index = advance_model_index(index, -1, len(models))
        elif key == "P":
            index = advance_model_index(index, 1, len(models))
        elif key == "\r":
            return models[index]
EFFECTIVENESS_LABELS = {
    0: "immune",
    1: "not-very-effective",
    2: "neutral",
    3: "super-effective",
}


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


def format_console_audit(message: str, ansi_enabled: bool) -> str:
    """Highlight accepted action lines without changing the plain audit record."""
    if not ansi_enabled or not message.startswith("audit #"):
        return message
    highlighted = []
    for line in message.splitlines():
        if line.startswith("  selected:") or (line.startswith("  battler ") and " ROM facts:" in line):
            highlighted.append(f"\x1b[1;92m{line}\x1b[0m")
        else:
            highlighted.append(line)
    return "\n".join(highlighted)


def log(message: str) -> None:
    """Emit concise local diagnostics; no battle data is persisted."""
    print(f"BAGB service: {format_console_audit(message, sys.stdout.isatty())}", flush=True)


def _label(category: str, value: int) -> str:
    return CATALOG[category].get(str(value), "UNKNOWN")

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "get_battle_state", "description": "Read request metadata and all active battlers.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_field_state", "description": "Read weather, terrain, and side conditions.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_battler", "description": "Read one active battler.", "parameters": {"type": "object", "properties": {"battler_id": {"type": "integer"}}, "required": ["battler_id"]}}},
    {"type": "function", "function": {"name": "get_battler_moves", "description": "Read one active battler's moves.", "parameters": {"type": "object", "properties": {"battler_id": {"type": "integer"}}, "required": ["battler_id"]}}},
    {"type": "function", "function": {"name": "get_party", "description": "Read the six-slot opponent party, including current usability. This does not itself switch a Pokémon.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_legal_actions", "description": "List all ROM-authorized actions, grouped by controlled battler. Move actions include published move data plus STAB, effectiveness, and KO facts.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "analyze_action", "description": "Read ROM-derived facts for one legal action.", "parameters": {"type": "object", "properties": {"battler_id": {"type": "integer"}, "action_index": {"type": "integer"}}, "required": ["battler_id", "action_index"]}}},
    {"type": "function", "function": {"name": "compare_speed", "description": "Compare active battlers' normal speed order; move priority can override it.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "choose_actions", "description": "Terminally select exactly one legal action for each controlled battler.", "parameters": {"type": "object", "properties": {"actions": {"type": "array", "items": {"type": "object", "properties": {"battler_id": {"type": "integer"}, "action_index": {"type": "integer"}}, "required": ["battler_id", "action_index"]}}}, "required": ["actions"]}}},
]


def _battler_offset(battler_id: int) -> int:
    if isinstance(battler_id, bool) or not isinstance(battler_id, int) or not 0 <= battler_id < 4:
        raise ToolError("battler_id must identify an active battler")
    return 14 + battler_id * 92


def _decode_battler(payload: bytes, offset: int, battler_id: int | None = None) -> dict[str, int | list[int]]:
    species, = struct.unpack_from("<H", payload, offset)
    ability, item, hp, max_hp = struct.unpack_from("<HHHH", payload, offset + 6)
    level, type1, type2, type3 = payload[offset + 2], payload[offset + 3], payload[offset + 4], payload[offset + 5]
    attack, defense, speed, sp_attack, sp_defense = struct.unpack_from("<HHHHH", payload, offset + 14)
    status1, status2, status3 = struct.unpack_from("<III", payload, offset + 24)
    raw_stages = tuple(payload[offset + 36 : offset + 44])
    result: dict[str, int | list[int] | dict[str, int]] = {"species": species, "species_name": _label("species", species), "level": level, "types": decode_types((type1, type2, type3)), "ability": ability, "ability_name": _label("abilities", ability), "item": item, "item_name": _label("items", item), "hp": hp, "max_hp": max_hp, "attack": attack, "defense": defense, "speed": speed, "sp_attack": sp_attack, "sp_defense": sp_defense, "major_status": decode_major_status(status1), "volatile_status": decode_volatile_status(status2, status3), "stat_changes": decode_stat_changes(raw_stages)}
    if battler_id is not None:
        result["battler_id"] = battler_id
    return result


def get_battler(payload: bytes, battler_id: int) -> dict[str, int | list[int]]:
    """Decode one active battler from the canonical V4 request payload."""
    return _decode_battler(payload, _battler_offset(battler_id), battler_id)


def get_battler_moves(payload: bytes, battler_id: int) -> list[dict[str, int]]:
    """Decode the four fixed-width move records for one active battler."""
    offset = _battler_offset(battler_id) + 44
    moves = []
    for slot in range(4):
        move, pp, move_type, power, accuracy, effect, target, priority, split = struct.unpack_from("<HBBBBHHbB", payload, offset + slot * 12)
        moves.append({"slot": slot, "move": move, "move_name": _label("moves", move), "pp": pp, "type": TYPE_NAMES[move_type] if 0 <= move_type < len(TYPE_NAMES) else "UNKNOWN", "power": power, "accuracy": accuracy, "effect": effect, "effect_name": _label("effects", effect), "target_category": decode_move_target(target), "priority": priority, "split": decode_move_split(split)})
    return moves


def get_field_state(payload: bytes) -> dict[str, int | list[int]]:
    """Decode field and side status data from the canonical V4 payload."""
    weather, = struct.unpack_from("<H", payload, 382)
    field_statuses, player_side, opponent_side = struct.unpack_from("<III", payload, 385)
    return decode_field_state(weather, payload[384], field_statuses, player_side, opponent_side)


def get_party(payload: bytes) -> list[dict[str, int | bool | str | list[int]]]:
    """Decode all six opponent-party records from the read-only BAGB/5 snapshot."""
    party = []
    for party_slot in range(6):
        offset = 397 + party_slot * 96
        member = _decode_battler(payload, offset + 4)
        owner_battler = payload[offset + 3]
        if owner_battler == 1:
            owner = "opponent-left"
        elif owner_battler == 3:
            owner = "opponent-right"
        else:
            owner = "shared"
        member.update({
            "party_slot": payload[offset],
            "is_active": bool(payload[offset + 1]),
            "is_usable": bool(payload[offset + 2]),
            "owner_battler": owner_battler,
            "owner": owner,
        })
        party.append(member)
    return party


def get_battle_state(*, sequence: int, turn_sequence: int, controlled_battlers: tuple[int, ...], battler_count: int, payload: bytes) -> dict[str, object]:
    """Return request metadata and the complete active-battler snapshot."""
    return {
        "request_sequence": sequence,
        "turn_sequence": turn_sequence,
        "controlled_battlers": list(controlled_battlers),
        "active_battlers": [get_battler(payload, battler_id) for battler_id in range(battler_count)],
    }


def _format_legal_action(
    action: LegalAction,
    actor_moves: list[dict[str, int | str]] | None = None,
) -> dict[str, int | str | bool]:
    """Expose one ROM-authorized action without granting selection authority."""
    entry: dict[str, int | str] = {
        "action_index": action.action_index,
        "kind": "move" if action.kind == ACTION_KIND_MOVE else "switch",
    }
    if action.kind == ACTION_KIND_MOVE:
        entry.update({"move_slot": action.move_slot, "target_battler": action.target_battler})
        if actor_moves is not None:
            if action.move_slot >= len(actor_moves):
                raise ToolError("legal action references an unavailable actor move")
            entry.update(actor_moves[action.move_slot])
            entry.update({
                "type_effectiveness": action.type_effectiveness,
                "has_stab": bool(action.has_stab),
                "can_faint_target": bool(action.can_faint_target),
            })
    else:
        entry["party_slot"] = action.party_slot
    return entry


def list_legal_actions(
    actions_by_battler: dict[int, tuple[LegalAction, ...]],
    requested_battler_id: int | None = None,
    payload: bytes | None = None,
) -> list[dict[str, object]]:
    """Expose every, or one requested, ROM-authorized actor action list."""
    result = []
    for battler_id, actions in actions_by_battler.items():
        if requested_battler_id is not None and battler_id != requested_battler_id:
            continue
        actor_moves = get_battler_moves(payload, battler_id) if payload is not None else None
        result.append({"battler_id": battler_id, "actions": [_format_legal_action(action, actor_moves) for action in actions]})
    return result


def choose_actions(
    actions_by_battler: dict[int, tuple[LegalAction, ...]],
    selected_actions: object,
) -> tuple[tuple[int, int], ...]:
    """Validate one terminal action per controlled battler, atomically."""
    if not isinstance(selected_actions, list) or len(selected_actions) != len(actions_by_battler):
        raise ToolError("choose_actions must select every controlled battler exactly once")
    selected: list[tuple[int, int]] = []
    selected_party_slots: set[int] = set()
    for choice in selected_actions:
        if not isinstance(choice, dict) or set(choice) != {"battler_id", "action_index"}:
            raise ToolError("each selected action must contain battler_id and action_index")
        battler_id, action_index = choice["battler_id"], choice["action_index"]
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (battler_id, action_index)):
            raise ToolError("selected battler_id and action_index must be integers")
        actions = actions_by_battler.get(battler_id)
        if actions is None or any(actor == battler_id for actor, _ in selected):
            raise ToolError("selected battler is not uniquely controlled by this request")
        action = next((candidate for candidate in actions if candidate.action_index == action_index), None)
        if action is None:
            raise ToolError("selected action is not legal for this battler")
        if action.kind == ACTION_KIND_SWITCH:
            if action.party_slot in selected_party_slots:
                raise ToolError("two battlers cannot switch to the same party slot")
            selected_party_slots.add(action.party_slot)
        selected.append((battler_id, action_index))
    return tuple(selected)


def analyze_action(actions: tuple[LegalAction, ...], action_index: int, actor_moves: list[dict[str, int]] | None = None) -> dict[str, int | bool | str]:
    """Expose the ROM's deterministic analysis for one legal action."""
    for action in actions:
        if action.action_index == action_index:
            result: dict[str, int | bool | str] = {"action_index": action.action_index, "kind": "move" if action.kind == ACTION_KIND_MOVE else "switch"}
            if action.kind == ACTION_KIND_SWITCH:
                result["party_slot"] = action.party_slot
                return result
            result.update({"move_slot": action.move_slot, "target_battler": action.target_battler, "type_effectiveness": action.type_effectiveness, "has_stab": bool(action.has_stab), "can_faint_target": bool(action.can_faint_target)})
            if actor_moves is not None and action.move_slot < len(actor_moves):
                result.update(actor_moves[action.move_slot])
            return result
    raise ToolError("action_index is not legal for this request")


def compare_speed(payload: bytes, battler_count: int) -> dict[str, object]:
    """Order ROM-calculated active speeds, applying the field's Trick Room rule."""
    speeds = {f"battler_{battler_id}": get_battler(payload, battler_id)["speed"] for battler_id in range(battler_count)}
    field_statuses, = struct.unpack_from("<I", payload, 385)
    trick_room_active = bool(field_statuses & (1 << 1))
    ordered = sorted(
        range(battler_count),
        key=lambda battler_id: (int(speeds[f"battler_{battler_id}"]), battler_id) if trick_room_active else (-int(speeds[f"battler_{battler_id}"]), battler_id),
    )
    return {
        "speeds": speeds,
        "normal_order": [f"battler_{battler_id}" for battler_id in ordered],
        "trick_room_active": trick_room_active,
        "note": "Order uses the ROM's effective active speed and reverses under Trick Room. Move priority can override it; equal speeds still use the game's speed-tie resolution.",
    }


def format_legal_action(action: LegalAction, actor_moves: list[dict[str, int]]) -> str:
    """Format one ROM-authorized action without attributing it to the model."""
    if action.kind == ACTION_KIND_SWITCH:
        return f"{action.action_index}=SWITCH->party {action.party_slot}"
    if action.move_slot >= len(actor_moves):
        raise ToolError("legal action references an unavailable actor move")
    return f"{action.action_index}={actor_moves[action.move_slot]['move_name']}->battler {action.target_battler}"


def format_decision_audit(
    sequence: int,
    battler_count: int,
    decision: AgentDecision,
    actions_by_battler: dict[int, tuple[LegalAction, ...]],
    payload: bytes,
) -> str:
    """Return one deterministic, operator-facing audit for an atomic choice."""
    selected_actions: list[tuple[int, LegalAction]] = []
    for battler_id, action_index in decision.actions:
        selected = next((action for action in actions_by_battler.get(battler_id, ()) if action.action_index == action_index), None)
        if selected is None:
            raise ToolError("decision references an unavailable legal action")
        selected_actions.append((battler_id, selected))
    speed_context = ", ".join(compare_speed(payload, battler_count)["normal_order"])
    tools_used = ", ".join(decision.tools_used) if decision.tools_used else "none"
    legal_actions = "; ".join(
        f"battler {battler_id}: " + ", ".join(format_legal_action(action, get_battler_moves(payload, battler_id)) for action in actions)
        for battler_id, actions in actions_by_battler.items()
    )
    selected_summary = "; ".join(
        f"battler {battler_id}: {format_legal_action(action, get_battler_moves(payload, battler_id))}"
        for battler_id, action in selected_actions
    )
    lines = [
        f"audit #{sequence}",
        f"  tools used: {tools_used}",
        f"  legal actions: {legal_actions}",
        f"  selected: {selected_summary}",
    ]
    for battler_id, selected in selected_actions:
        if selected.kind == ACTION_KIND_MOVE:
            actor_moves = get_battler_moves(payload, battler_id)
            selected_facts = analyze_action(actions_by_battler[battler_id], selected.action_index, actor_moves)
            effectiveness = EFFECTIVENESS_LABELS.get(selected_facts["type_effectiveness"])
            if effectiveness is None:
                raise ToolError("decision has an unknown effectiveness category")
            lines.append(
                f"  battler {battler_id} ROM facts: "
                + f"STAB={'yes' if selected_facts['has_stab'] else 'no'}, effectiveness={effectiveness}, "
                + f"KO={'yes' if selected_facts['can_faint_target'] else 'no'}, priority={selected_facts['priority']}"
            )
        else:
            lines.append(f"  battler {battler_id} ROM facts: switch_to_party_slot={selected.party_slot}")
    lines.append(f"  speed context: {speed_context}")
    return "\n".join(lines)


def request_ollama(messages: list[dict[str, object]], model: str = OLLAMA_MODEL) -> dict[str, object]:
    """Call only the local Ollama chat endpoint with the bounded tool schema."""
    body = json.dumps({"model": model, "stream": False, "messages": messages, "tools": TOOL_SCHEMAS}).encode()
    request = Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=OLLAMA_RESPONSE_TIMEOUT_SECONDS) as response:
        decoded = json.loads(response.read().decode())
    if not isinstance(decoded, dict) or not isinstance(decoded.get("message"), dict):
        raise ToolError("Ollama response has no message object")
    return decoded["message"]


def format_model_response_preview(message: dict[str, object]) -> str:
    """Return one bounded console-safe preview of an assistant response."""
    content = message.get("content")
    preview = repr(content) if isinstance(content, str) else repr(message)
    return preview.replace("\r", " ").replace("\n", " ")[:MODEL_RESPONSE_PREVIEW_LIMIT]


def describe_malformed_tool_call(message: dict[str, object]) -> str:
    """Classify an assistant response that the existing parser cannot accept."""
    calls = message.get("tool_calls")
    if calls is not None:
        if not isinstance(calls, list):
            return "native_tool_calls_not_list"
        if len(calls) != 1:
            return f"native_tool_calls_count={len(calls)}"
        if not isinstance(calls[0], dict):
            return "native_tool_call_not_object"
        function = calls[0].get("function")
        if not isinstance(function, dict):
            return "native_function_not_object"
        if not isinstance(function.get("name"), str):
            return "native_function_name_not_string"
        if not isinstance(function.get("arguments"), dict):
            return "native_function_arguments_not_object"
        return "valid"

    content = message.get("content")
    if content is None:
        return "content_missing"
    if not isinstance(content, str):
        return "content_not_string"
    try:
        compatibility_call = json.loads(content)
    except json.JSONDecodeError:
        return "content_invalid_json"
    if not isinstance(compatibility_call, dict):
        return "content_not_object"
    if set(compatibility_call) != {"name", "arguments"}:
        return "content_unexpected_keys"
    if not isinstance(compatibility_call["name"], str):
        return "content_name_not_string"
    if (compatibility_call["name"] == "choose_actions"
            and isinstance(compatibility_call["arguments"], list)):
        return "valid"
    if not isinstance(compatibility_call["arguments"], dict):
        return "content_arguments_not_object"
    return "valid"


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
    if not isinstance(compatibility_call["name"], str):
        return None
    if (compatibility_call["name"] == "choose_actions"
            and isinstance(compatibility_call["arguments"], list)):
        return compatibility_call["name"], {"actions": compatibility_call["arguments"]}
    if not isinstance(compatibility_call["arguments"], dict):
        return None
    return compatibility_call["name"], compatibility_call["arguments"]


def run_tool_agent(
    sequence: int,
    turn_sequence: int,
    controlled_battlers: tuple[int, ...],
    battler_count: int,
    actions_by_battler: dict[int, tuple[LegalAction, ...]],
    payload: bytes,
    model: str = OLLAMA_MODEL,
) -> AgentDecision | None:
    """Run a bounded local model/tool exchange and return one atomic legal plan."""
    messages: list[dict[str, object]] = [{"role": "system", "content": "Use only the supplied read-only tools to inspect this battle. Make exactly one tool call per response; never emit multiple calls. Do not answer in prose. Return only one JSON object with exactly name and arguments. For an ordinary move turn, call get_battle_state, then list_legal_actions, then choose_actions: the legal-action list already includes each move's ROM facts. Call get_party before choosing a voluntary switch; call other inspection tools only when their extra information is necessary. Finish exactly once with choose_actions and exactly one legal action for every controlled battler."}]
    started = time.monotonic()
    format_retry_used = False
    tools_used: list[str] = []
    for _ in range(MAX_TOOL_CALLS):
        elapsed = time.monotonic() - started
        if elapsed >= TOOL_EXCHANGE_TIMEOUT_SECONDS:
            log(f"request {sequence} exchange deadline reached after {elapsed:.1f}s")
            return None
        try:
            message = request_ollama(messages, model)
            tool_call = extract_tool_call(message)
            if tool_call is None:
                diagnostic = (
                    f"request {sequence} malformed tool call: "
                    f"{describe_malformed_tool_call(message)}; "
                    f"response={format_model_response_preview(message)}"
                )
                if format_retry_used:
                    log(diagnostic + "; retry exhausted")
                    return None
                format_retry_used = True
                log(diagnostic + "; retrying once")
                messages.append({"role": "system", "content": FORMAT_RETRY_MESSAGE})
                continue
            name, arguments = tool_call
            log(f"request {sequence} tool {name}")
            if name == "choose_actions" and set(arguments) == {"actions"}:
                selected_actions = choose_actions(actions_by_battler, arguments["actions"])
                log(f"request {sequence} chose actions {selected_actions}")
                return AgentDecision(selected_actions, tuple(tools_used + [name]))
            if name == "get_battle_state" and not arguments:
                result = get_battle_state(sequence=sequence, turn_sequence=turn_sequence, controlled_battlers=controlled_battlers, battler_count=battler_count, payload=payload)
            elif name == "get_field_state" and not arguments:
                result = get_field_state(payload)
            elif name == "get_battler" and set(arguments) == {"battler_id"}:
                result = get_battler(payload, arguments["battler_id"])
            elif name == "get_battler_moves" and set(arguments) == {"battler_id"}:
                result = get_battler_moves(payload, arguments["battler_id"])
            elif name == "get_party" and not arguments:
                result = get_party(payload)
            elif name == "list_legal_actions":
                if arguments:
                    log(f"request {sequence} normalized list_legal_actions arguments: argument_keys={sorted(arguments)!r}")
                result = list_legal_actions(actions_by_battler, payload=payload)
            elif name == "analyze_action" and set(arguments) == {"battler_id", "action_index"} and arguments["battler_id"] in actions_by_battler:
                result = analyze_action(actions_by_battler[arguments["battler_id"]], arguments["action_index"], get_battler_moves(payload, arguments["battler_id"]))
            elif name == "compare_speed" and not arguments:
                result = compare_speed(payload, battler_count)
            else:
                log(f"request {sequence} unsupported tool call: name={name!r}, argument_keys={sorted(arguments)!r}")
                return None
            tools_used.append(name)
            messages.append(message)
            messages.append({"role": "tool", "content": json.dumps(result)})
        except (OSError, ValueError, ToolError) as error:
            log(f"request {sequence} rejected: {error}")
            return None
    return None


def handle_request_frame(frame: bytes, model: str = OLLAMA_MODEL) -> bytes | None:
    """Decode one bridge request and return a response only for a valid model choice."""
    request = parse_request_frame(frame)
    log(f"request {request.sequence} received")
    decision = run_tool_agent(
        request.sequence,
        request.turn_sequence,
        request.controlled_battlers,
        request.battler_count,
        request.actions_by_battler,
        request.payload,
        model,
    )
    if decision is None:
        log(f"request {request.sequence} produced no response")
        log(f"audit #{request.sequence}: no legal model decision; vanilla_fallback")
        return None
    try:
        log(format_decision_audit(
            request.sequence,
            request.battler_count,
            decision,
            request.actions_by_battler,
            request.payload,
        ))
        return format_response_frame(request.sequence, decision.actions)
    except (ToolError, ValueError) as error:
        log(f"request {request.sequence} audit rejected: {error}")
        return None


def _connect(port: int) -> socket.socket:
    """Connect to mGBA's one-client Lua listener, retrying until it is ready."""
    while True:
        try:
            connection = socket.create_connection((LOOPBACK_HOST, port), timeout=1)
            connection.settimeout(None)
            return connection
        except OSError:
            time.sleep(0.25)


def _serve_connection(connection: socket.socket, model: str = OLLAMA_MODEL) -> None:
    """Forward complete fixed request frames over one established Lua connection."""
    buffer = b""
    while True:
        try:
            chunk = connection.recv(REQUEST_FRAME_SIZE - len(buffer))
        except OSError:
            return
        if not chunk:
            return
        buffer += chunk
        if len(buffer) != REQUEST_FRAME_SIZE:
            continue
        try:
            response = handle_request_frame(buffer, model)
        except (ToolError, ValueError):
            response = None
        if response is not None:
            try:
                connection.sendall(response)
            except OSError:
                return
        buffer = b""


def serve(host: str = LOOPBACK_HOST, port: int = 57621, model: str = OLLAMA_MODEL) -> None:
    """Connect once to mGBA's loopback listener and process its request frames."""
    if host != LOOPBACK_HOST:
        raise ValueError("battle-agent service connects only to the loopback Lua listener")
    log(f"connecting to mGBA at {host}:{port}")
    with _connect(port) as connection:
        log("mGBA bridge connected")
        _serve_connection(connection, model)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=57621)
    parser.add_argument("--model")
    args = parser.parse_args()
    try:
        model = args.model or select_ollama_model(discover_ollama_models())
    except ModelSelectionError as error:
        parser.error(str(error))
    print(f"BAGB service: using Ollama model {model}")
    serve(args.host, args.port, model)


if __name__ == "__main__":
    main()
