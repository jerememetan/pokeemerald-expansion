"""Deterministic loopback responder for the mGBA bridge spike."""

import argparse
import socket
import time

from bridge_protocol import MAX_LINE_BYTES, ProtocolError, format_response, parse_request


LOOPBACK_HOST = "127.0.0.1"


def _parse_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be in 1..65535")
    return port


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=_parse_port, default=57621)
    return parser.parse_args()


def _connect(port: int) -> socket.socket:
    while True:
        try:
            connection = socket.create_connection((LOOPBACK_HOST, port), timeout=1)
            connection.settimeout(None)
            return connection
        except OSError:
            time.sleep(0.25)


def _serve(connection: socket.socket) -> None:
    buffered = bytearray()
    try:
        while True:
            try:
                received = connection.recv(MAX_LINE_BYTES)
            except OSError:
                return
            if not received:
                return

            buffered.extend(received)
            while b"\n" in buffered:
                newline_index = buffered.index(b"\n") + 1
                line = bytes(buffered[:newline_index])
                del buffered[:newline_index]
                try:
                    request = parse_request(line)
                    connection.sendall(format_response(request.sequence, 0))
                except (OSError, ProtocolError):
                    return

            if len(buffered) > MAX_LINE_BYTES:
                return
    finally:
        try:
            connection.close()
        except OSError:
            pass


def main() -> None:
    """Connect to the local Lua listener and respond to valid requests."""
    arguments = _parse_arguments()
    with _connect(arguments.port) as connection:
        _serve(connection)


if __name__ == "__main__":
    main()
