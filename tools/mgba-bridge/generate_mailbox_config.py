"""Generate the build-local Lua mailbox address configuration."""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys


EWRAM_START = 0x02000000
EWRAM_END = 0x02040000
SYMBOL = "gBattleAgentMailbox"
_DEFAULT_OUTPUT = pathlib.Path("tools/mgba-bridge/generated/mailbox_address.lua")
_NM_RECORD = re.compile(r"^[0-9A-Fa-f]{8}$")
_LUA_COMMENT = (
    "-- Generated from the current pokeemerald.elf; do not commit or reuse after rebuilding.\n"
)


class AddressConfigError(ValueError):
    """Raised when the mailbox address cannot safely be configured."""


def _validate_ewram_address(address: int) -> None:
    if isinstance(address, bool) or not isinstance(address, int):
        raise AddressConfigError("mailbox address must be an integer")
    if not EWRAM_START <= address < EWRAM_END:
        raise AddressConfigError("mailbox address is outside EWRAM")


def parse_mailbox_address(nm_output: str) -> int:
    """Return the unique EWRAM address of ``gBattleAgentMailbox`` from nm output."""
    records = [
        line.split()
        for line in nm_output.splitlines()
        if line.split() and line.split()[-1] == SYMBOL
    ]
    if len(records) != 1:
        raise AddressConfigError("mailbox symbol must appear exactly once")

    if len(records[0]) != 3:
        raise AddressConfigError("mailbox symbol record is not a global nm address record")

    address_token, symbol_type, _ = records[0]
    if not _NM_RECORD.fullmatch(address_token) or not re.fullmatch(r"[A-Z]", symbol_type):
        raise AddressConfigError("mailbox symbol record is not a global nm address record")

    try:
        address = int(address_token, 16)
    except ValueError as error:
        raise AddressConfigError("mailbox symbol has no hexadecimal address") from error

    _validate_ewram_address(address)
    return address


def write_lua_config(address: int, output_path: pathlib.Path) -> None:
    """Write a Lua configuration containing one validated mailbox address."""
    _validate_ewram_address(address)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        f"{_LUA_COMMENT}MAILBOX_ADDRESS = 0x{address:08X}\n", encoding="utf-8"
    )


def _parse_arguments(arguments: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the mGBA bridge mailbox address configuration."
    )
    parser.add_argument("--elf", required=True, help="path to the current pokeemerald.elf")
    parser.add_argument("--nm", default="arm-none-eabi-nm", help="nm executable")
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=_DEFAULT_OUTPUT,
        help="generated Lua output path",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    """Generate the Lua config and return a process-compatible exit status."""
    arguments = _parse_arguments(arguments)
    try:
        result = subprocess.run(
            [arguments.nm, "-n", arguments.elf],
            check=True,
            text=True,
            capture_output=True,
        )
        write_lua_config(parse_mailbox_address(result.stdout), arguments.output)
    except subprocess.CalledProcessError as error:
        print(
            f"mailbox config generation failed: nm exited with status {error.returncode}",
            file=sys.stderr,
        )
        return 1
    except OSError:
        print("mailbox config generation failed: unable to run nm", file=sys.stderr)
        return 1
    except AddressConfigError as error:
        print(f"mailbox config generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
