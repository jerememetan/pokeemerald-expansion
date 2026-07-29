"""Local, tool-only decision helpers for the BAGB/2 trainer agent."""

from __future__ import annotations

from bridge_protocol import LegalAction


class ToolError(ValueError):
    """Raised when a model attempts an unavailable or illegal action."""


def get_battle_state(*, sequence: int, turn_sequence: int, requesting_battler: int) -> dict[str, int]:
    """Return only request metadata decoded from the current bridge frame."""
    return {
        "request_sequence": sequence,
        "turn_sequence": turn_sequence,
        "requesting_battler": requesting_battler,
    }


def list_legal_actions(actions: tuple[LegalAction, ...]) -> list[dict[str, int]]:
    """Expose ROM-authorized action indexes without granting move/target authority."""
    return [{"action_index": action.action_index} for action in actions]


def choose_action(actions: tuple[LegalAction, ...], action_index: int) -> int:
    """Validate the terminal model choice against the current ROM action list."""
    if isinstance(action_index, bool) or not isinstance(action_index, int):
        raise ToolError("action_index must be an integer")
    if any(action.action_index == action_index for action in actions):
        return action_index
    raise ToolError("action_index is not legal for this request")


def analyze_action(actions: tuple[LegalAction, ...], action_index: int) -> dict[str, int | bool]:
    """Expose the ROM's deterministic analysis for one legal action."""
    for action in actions:
        if action.action_index == action_index:
            return {
                "action_index": action.action_index,
                "move_slot": action.move_slot,
                "target_battler": action.target_battler,
                "type_effectiveness": action.type_effectiveness,
                "has_stab": bool(action.has_stab),
                "can_faint_target": bool(action.can_faint_target),
            }
    raise ToolError("action_index is not legal for this request")
