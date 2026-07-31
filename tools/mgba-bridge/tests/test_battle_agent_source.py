"""Source-level regression checks for battle-agent presentation behavior."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = REPOSITORY_ROOT / "src" / "battle_agent.c"


class BattleAgentSourceTests(unittest.TestCase):
    def test_thinking_status_renders_atomically(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"void BattleAgent_UpdateThinkingStatus\(u32 battler, bool32 playerActionConfirmed\)\n"
            r"\{(?P<body>.*?)^\}",
            source,
            re.MULTILINE | re.DOTALL,
        )

        self.assertIsNotNone(match)
        body = match.group("body")
        self.assertIn("BattleAgent_RenderThinkingStatus", body)

        renderer = re.search(
            r"static void BattleAgent_RenderThinkingStatus\(u32 battler\)\n"
            r"\{(?P<body>.*?)^\}",
            source,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(renderer)
        self.assertIn("TEXT_SKIP_DRAW", renderer.group("body"))
        self.assertNotIn("BattlePutTextOnWindow", renderer.group("body"))

    def test_thinking_status_does_not_cycle_dots(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"static bool32 BattleAgent_UpdateThinkingStatusState\(u32 battler, bool32 playerActionConfirmed, bool32 messageWindowIdle\)\n"
            r"\{(?P<body>.*?)^\}",
            source,
            re.MULTILINE | re.DOTALL,
        )

        self.assertIsNotNone(match)
        body = match.group("body")
        self.assertIn("BATTLE_AGENT_THINKING_TWO_DOTS", body)
        self.assertNotIn("++status->frames", body)


if __name__ == "__main__":
    unittest.main()
