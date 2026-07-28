"""Strict, bounded line protocol shared by the mGBA bridge responder."""

from dataclasses import dataclass


MAX_LINE_BYTES = 96
PROTOCOL = b"BAGB/1"
_U32_MAX = 0xFFFFFFFF


class ProtocolError(ValueError):
    """Raised when a bridge protocol line is not valid."""


@dataclass(frozen=True)
class Request:
    sequence: int
    action_count: int


@dataclass(frozen=True)
class Response:
    sequence: int
    action_index: int


def _split_line(line: bytes, message_type: bytes) -> tuple[bytes, bytes]:
    if not isinstance(line, bytes):
        raise ProtocolError("line must be bytes")
    if len(line) > MAX_LINE_BYTES:
        raise ProtocolError("line exceeds byte limit")
    if b"\0" in line:
        raise ProtocolError("line contains NUL")

    try:
        line.decode("ascii")
    except UnicodeDecodeError as error:
        raise ProtocolError("line is not ASCII") from error

    if not line.endswith(b"\n") or line.count(b"\n") != 1:
        raise ProtocolError("line must contain one terminal newline")

    tokens = line[:-1].split(b" ")
    if len(tokens) != 4 or tokens[0] != PROTOCOL or tokens[1] != message_type:
        raise ProtocolError("invalid protocol tokens")
    return tokens[2], tokens[3]


def _parse_u32(token: bytes) -> int:
    if not token or any(character not in b"0123456789" for character in token):
        raise ProtocolError("value is not unsigned decimal")
    value = int(token)
    if value > _U32_MAX:
        raise ProtocolError("value exceeds u32")
    return value


def _validate_u32(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= _U32_MAX:
        raise ProtocolError(f"{name} must be a u32")


def parse_request(line: bytes) -> Request:
    """Parse a bounded BAGB/1 request line."""
    sequence_token, action_count_token = _split_line(line, b"REQUEST")
    sequence = _parse_u32(sequence_token)
    action_count = _parse_u32(action_count_token)
    if not 1 <= action_count <= 4:
        raise ProtocolError("action count is outside 1..4")
    return Request(sequence=sequence, action_count=action_count)


def parse_response(line: bytes) -> Response:
    """Parse a bounded BAGB/1 response line."""
    sequence_token, action_index_token = _split_line(line, b"RESPONSE")
    sequence = _parse_u32(sequence_token)
    action_index = _parse_u32(action_index_token)
    if not 0 <= action_index <= 3:
        raise ProtocolError("action index is outside 0..3")
    return Response(sequence=sequence, action_index=action_index)


def format_response(sequence: int, action_index: int) -> bytes:
    """Return one validated BAGB/1 response line."""
    _validate_u32(sequence, "sequence")
    if (
        isinstance(action_index, bool)
        or not isinstance(action_index, int)
        or not 0 <= action_index <= 3
    ):
        raise ProtocolError("action index is outside 0..3")
    return b"%s RESPONSE %d %d\n" % (PROTOCOL, sequence, action_index)
