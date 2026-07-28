"""Tests for generating a build-local mGBA mailbox address config."""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


BRIDGE_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BRIDGE_DIRECTORY))

from generate_mailbox_config import (  # noqa: E402
    EWRAM_END,
    EWRAM_START,
    SYMBOL,
    AddressConfigError,
    main,
    parse_mailbox_address,
    write_lua_config,
)


class ParseMailboxAddressTests(unittest.TestCase):
    def test_parses_the_unique_ewram_mailbox_symbol(self) -> None:
        self.assertEqual(
            parse_mailbox_address("02001234 B gBattleAgentMailbox\n"),
            0x02001234,
        )

    def test_rejects_a_missing_mailbox_symbol(self) -> None:
        with self.assertRaises(AddressConfigError):
            parse_mailbox_address("02001234 B anotherSymbol\n")

    def test_rejects_duplicate_mailbox_symbols(self) -> None:
        with self.assertRaises(AddressConfigError):
            parse_mailbox_address(
                "02001234 B gBattleAgentMailbox\n02005678 B gBattleAgentMailbox\n"
            )

    def test_rejects_a_mailbox_symbol_outside_ewram(self) -> None:
        with self.assertRaises(AddressConfigError):
            parse_mailbox_address("03001234 B gBattleAgentMailbox\n")

    def test_rejects_a_lowercase_local_symbol_type(self) -> None:
        with self.assertRaises(AddressConfigError):
            parse_mailbox_address("02001234 b gBattleAgentMailbox\n")

    def test_rejects_a_mailbox_record_with_extra_fields(self) -> None:
        with self.assertRaises(AddressConfigError):
            parse_mailbox_address("02001234 B unexpected gBattleAgentMailbox\n")

    def test_rejects_a_mailbox_record_without_an_eight_digit_address(self) -> None:
        with self.assertRaises(AddressConfigError):
            parse_mailbox_address("2001234 B gBattleAgentMailbox\n")

    def test_rejects_a_mailbox_record_without_a_hex_address(self) -> None:
        with self.assertRaises(AddressConfigError):
            parse_mailbox_address("not-an-address B gBattleAgentMailbox\n")


class WriteLuaConfigTests(unittest.TestCase):
    def test_writes_the_exact_generated_lua_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "nested" / "mailbox_address.lua"

            write_lua_config(0x02001234, output_path)

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "-- Generated from the current pokeemerald.elf; do not commit or reuse after rebuilding.\n"
                "MAILBOX_ADDRESS = 0x02001234\n",
            )

    def test_rejects_an_address_outside_ewram(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "mailbox_address.lua"
            for address in (EWRAM_START - 1, EWRAM_END):
                with self.subTest(address=address):
                    with self.assertRaises(AddressConfigError):
                        write_lua_config(address, output_path)


class CommandLineTests(unittest.TestCase):
    def test_uses_the_default_nm_and_output_path(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="02001234 B gBattleAgentMailbox\n", stderr=""
        )
        with mock.patch("generate_mailbox_config.subprocess.run", return_value=completed) as run:
            with mock.patch("generate_mailbox_config.write_lua_config") as write:
                self.assertEqual(main(["--elf", "build/pokeemerald.elf"]), 0)

        run.assert_called_once_with(
            ["arm-none-eabi-nm", "-n", "build/pokeemerald.elf"],
            check=True,
            text=True,
            capture_output=True,
        )
        write.assert_called_once_with(
            0x02001234,
            Path("tools/mgba-bridge/generated/mailbox_address.lua"),
        )

    def test_honors_an_explicit_nm_and_output_path(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="02001234 B gBattleAgentMailbox\n", stderr=""
        )
        with mock.patch("generate_mailbox_config.subprocess.run", return_value=completed) as run:
            with mock.patch("generate_mailbox_config.write_lua_config") as write:
                self.assertEqual(
                    main(
                        [
                            "--elf",
                            "build/pokeemerald.elf",
                            "--nm",
                            "custom-nm",
                            "--output",
                            "temporary/mailbox.lua",
                        ]
                    ),
                    0,
                )

        run.assert_called_once_with(
            ["custom-nm", "-n", "build/pokeemerald.elf"],
            check=True,
            text=True,
            capture_output=True,
        )
        write.assert_called_once_with(0x02001234, Path("temporary/mailbox.lua"))

    def test_reports_a_nonzero_nm_failure_without_a_traceback(self) -> None:
        failure = subprocess.CalledProcessError(
            1,
            ["arm-none-eabi-nm", "-n", "build/pokeemerald.elf"],
            stderr="nm: build/pokeemerald.elf: No such file\n",
        )
        stderr = io.StringIO()
        with mock.patch(
            "generate_mailbox_config.subprocess.run", side_effect=failure
        ):
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(main(["--elf", "build/pokeemerald.elf"]), 1)

        self.assertIn("mailbox config generation failed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_reports_an_nm_invocation_error_without_a_traceback(self) -> None:
        stderr = io.StringIO()
        with mock.patch(
            "generate_mailbox_config.subprocess.run", side_effect=OSError("x" * 1000)
        ):
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(main(["--elf", "build/pokeemerald.elf"]), 1)

        self.assertEqual(
            stderr.getvalue(), "mailbox config generation failed: unable to run nm\n"
        )
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
