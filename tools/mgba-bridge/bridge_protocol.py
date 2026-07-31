"""Strict, bounded BAGB bridge protocols shared by mGBA bridge tools."""

from dataclasses import dataclass
import struct


MAX_LINE_BYTES = 96
PROTOCOL = b"BAGB/1"
_U32_MAX = 0xFFFFFFFF

MAGIC = b"BAGB"
VERSION = 3
KIND_REQUEST = 1
KIND_RESPONSE = 2
REQUEST_PAYLOAD_SIZE = 1049
RESPONSE_PAYLOAD_SIZE = 5
REQUEST_FRAME_SIZE = 8 + REQUEST_PAYLOAD_SIZE
RESPONSE_FRAME_SIZE = 8 + RESPONSE_PAYLOAD_SIZE
_BATTLER_WIRE_SIZE = 92
_ACTIVE_BATTLERS_OFFSET = 9
_FIELD_OFFSET = _ACTIVE_BATTLERS_OFFSET + 4 * _BATTLER_WIRE_SIZE
_PARTY_OFFSET = _FIELD_OFFSET + 15
_PARTY_WIRE_SIZE = 96
_PARTY_COUNT = 6
_LEGAL_ACTION_COUNT_OFFSET = _PARTY_OFFSET + _PARTY_COUNT * _PARTY_WIRE_SIZE
_LEGAL_ACTION_OFFSET = _LEGAL_ACTION_COUNT_OFFSET + 1
_LEGAL_ACTION_SIZE = 8
MAX_LEGAL_ACTIONS = 10
ACTION_KIND_MOVE = 0
ACTION_KIND_SWITCH = 1
ACTION_NONE = 0xFF


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


@dataclass(frozen=True)
class LegalAction:
    action_index: int
    kind: int
    move_slot: int
    target_battler: int
    party_slot: int
    type_effectiveness: int
    has_stab: int
    can_faint_target: int


@dataclass(frozen=True)
class FrameRequest:
    sequence: int
    requesting_battler: int
    battle_mode: int
    turn_sequence: int
    battler_count: int
    payload: bytes
    legal_actions: tuple[LegalAction, ...]


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


def _parse_frame(frame: bytes, kind: int, payload_size: int) -> bytes:
    if not isinstance(frame, bytes) or len(frame) != 8 + payload_size:
        raise ProtocolError("frame has invalid fixed length")
    magic, version, actual_kind, length = struct.unpack_from("<4sBBH", frame)
    if magic != MAGIC or version != VERSION or actual_kind != kind or length != payload_size:
        raise ProtocolError("frame has invalid header")
    return frame[8:]


def parse_request_frame(frame: bytes) -> FrameRequest:
    """Parse exactly one fixed-size BAGB/3 request frame."""
    payload = _parse_frame(frame, KIND_REQUEST, REQUEST_PAYLOAD_SIZE)
    sequence = struct.unpack_from("<I", payload, 0)[0]
    requesting_battler = payload[4]
    battle_mode = payload[5]
    turn_sequence = struct.unpack_from("<H", payload, 6)[0]
    battler_count = payload[8]
    legal_count = payload[_LEGAL_ACTION_COUNT_OFFSET]
    if requesting_battler > 3 or battle_mode != 1 or battler_count != 2:
        raise ProtocolError("request has unsupported battle metadata")
    if not 1 <= legal_count <= MAX_LEGAL_ACTIONS:
        raise ProtocolError("request has invalid legal action count")

    for party_slot in range(_PARTY_COUNT):
        offset = _PARTY_OFFSET + party_slot * _PARTY_WIRE_SIZE
        if payload[offset] != party_slot or payload[offset + 1] > 1 or payload[offset + 2] > 1 or payload[offset + 3] != 0:
            raise ProtocolError("request has invalid party metadata")

    actions = []
    for index in range(legal_count):
        offset = _LEGAL_ACTION_OFFSET + index * _LEGAL_ACTION_SIZE
        action = LegalAction(*payload[offset : offset + _LEGAL_ACTION_SIZE])
        if action.action_index != index or action.kind not in (ACTION_KIND_MOVE, ACTION_KIND_SWITCH):
            raise ProtocolError("request has invalid legal action")
        if action.kind == ACTION_KIND_MOVE:
            if action.move_slot > 3 or action.target_battler > 3 or action.party_slot != ACTION_NONE:
                raise ProtocolError("request has invalid move action")
        elif action.move_slot != ACTION_NONE or action.target_battler != ACTION_NONE or action.party_slot >= _PARTY_COUNT:
            raise ProtocolError("request has invalid switch action")
        if action.type_effectiveness > 3 or action.has_stab > 1 or action.can_faint_target > 1:
            raise ProtocolError("request has invalid legal action analysis")
        actions.append(action)

    return FrameRequest(
        sequence=sequence,
        requesting_battler=requesting_battler,
        battle_mode=battle_mode,
        turn_sequence=turn_sequence,
        battler_count=battler_count,
        payload=payload,
        legal_actions=tuple(actions),
    )


def format_response_frame(sequence: int, action_index: int) -> bytes:
    """Return one fixed-size BAGB/3 response frame."""
    _validate_u32(sequence, "sequence")
    if isinstance(action_index, bool) or not isinstance(action_index, int) or not 0 <= action_index < MAX_LEGAL_ACTIONS:
        raise ProtocolError("action index is outside legal-action range")
    return struct.pack("<4sBBHIB", MAGIC, VERSION, KIND_RESPONSE, RESPONSE_PAYLOAD_SIZE, sequence, action_index)
