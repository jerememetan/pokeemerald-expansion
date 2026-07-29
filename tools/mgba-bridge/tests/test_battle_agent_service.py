"""Focused tests for read-only battle-agent tools."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


BRIDGE_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BRIDGE_DIRECTORY))

from battle_agent_service import (  # noqa: E402
    ToolError,
    analyze_action,
    choose_action,
    get_battle_state,
    list_legal_actions,
)
from bridge_protocol import LegalAction  # noqa: E402


class BattleAgentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = (
            LegalAction(0, 0, 0, 2, 1, 0),
            LegalAction(1, 1, 0, 3, 1, 1),
        )

    def test_list_legal_actions_exposes_only_rom_action_indexes(self) -> None:
        self.assertEqual(list_legal_actions(self.actions), [{"action_index": 0}, {"action_index": 1}])

    def test_choose_action_rejects_unlisted_index(self) -> None:
        with self.assertRaises(ToolError):
            choose_action(self.actions, 2)

    def test_action_analysis_reports_only_rom_derived_facts(self) -> None:
        self.assertEqual(
            analyze_action(self.actions, 1),
            {"action_index": 1, "move_slot": 1, "target_battler": 0,
             "type_effectiveness": 3, "has_stab": True, "can_faint_target": True},
        )

    def test_battle_state_reports_request_metadata_without_memory_access(self) -> None:
        self.assertEqual(
            get_battle_state(sequence=7, turn_sequence=3, requesting_battler=1),
            {"request_sequence": 7, "turn_sequence": 3, "requesting_battler": 1},
        )


if __name__ == "__main__":
    unittest.main()
