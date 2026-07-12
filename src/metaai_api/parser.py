"""DGW (Datagram WebSocket) frame parser and builder.

Meta AI uses a custom WebSocket protocol called DGW for real-time communication.
This module implements the binary frame format used by gateway.meta.ai.

Frame format:
    EstablishStream (ACK) frame — 6-byte header:
        [0x0F][stream_id:2 BE][payload_len:1][flags:2][JSON payload]

    DATA frame — 8-byte header:
        [0x0D][stream_id:2 BE][payload_len:3 LE][seq_num:1][flags:1=0x80][JSON payload]
"""
from __future__ import annotations

import enum
import json
import struct
from dataclasses import dataclass
from typing import Any, Dict, Optional


class FrameType(enum.IntEnum):
    """DGW frame types (from Meta's DgwFrameType enum)."""
    DRAIN = 3
    DEAUTH = 4
    SMALL_ACK = 7
    PING = 9
    PONG = 10
    ACK = 12
    DATA = 13
    END_OF_DATA = 14
    ESTAB_STREAM = 15


@dataclass
class DGWFrame:
    """A parsed DGW frame."""
    type: int
    stream_id: int
    payload_len: int
    seq_num: Optional[int]
    flags: bytes
    payload: bytes
    payload_json: Optional[Dict[str, Any]] = None

    @property
    def is_data(self) -> bool:
        return self.type == FrameType.DATA

    @property
    def is_end_of_data(self) -> bool:
        return self.type == FrameType.END_OF_DATA

    @property
    def is_ack(self) -> bool:
        return self.type == FrameType.ACK


def parse_frame(buf: bytes) -> DGWFrame:
    """Parse a DGW frame from a byte buffer."""
    if len(buf) < 2:
        return DGWFrame(0, 0, 0, None, b"", buf)

    msg_type = buf[0]
    stream_id = struct.unpack(">H", buf[1:3])[0]

    if msg_type == FrameType.ESTAB_STREAM and len(buf) >= 6:
        payload_len = buf[3]
        flags = buf[4:6]
        payload = buf[6:6 + payload_len]
        seq_num = None
    elif msg_type in (FrameType.DATA, FrameType.ACK, FrameType.END_OF_DATA) and len(buf) >= 8:
        payload_len = int.from_bytes(buf[3:6], "little")
        seq_num = buf[6]
        flags = buf[7:8]
        payload = buf[8:8 + payload_len]
    else:
        json_start = buf.find(b"{")
        payload = buf[json_start:] if json_start >= 0 else b""
        return DGWFrame(msg_type, stream_id, len(payload), None,
                        buf[:json_start] if json_start >= 0 else b"", payload)

    payload_json = None
    if payload and payload[0:1] == b"{":
        try:
            payload_json = json.loads(payload.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    return DGWFrame(msg_type, stream_id, payload_len, seq_num, flags, payload, payload_json)


def build_estab_stream_frame(conversation_id: str) -> bytes:
    """Build an EstablishStream frame for a conversation."""
    payload = json.dumps({
        "x-dgw-app-x-ecto-conversation-id": conversation_id,
        "x-dgw-app-client-payload-type": "PROTO_INSIDE_JSON",
    }, separators=(",", ":")).encode("utf-8")
    if len(payload) > 127:
        raise ValueError(f"ACK payload too long: {len(payload)} bytes (max 127)")
    return bytes([0x0F, 0x00, 0x00, len(payload), 0x00, 0x00]) + payload


def build_data_frame(payload_json: bytes, seq_num: int = 0, stream_id: int = 0) -> bytes:
    """Build a DATA frame with the given sequence number."""
    payload_len = len(payload_json)
    return (
        bytes([0x0D])
        + struct.pack(">H", stream_id)
        + payload_len.to_bytes(3, "little")
        + bytes([seq_num & 0x7F, 0x80])
        + payload_json
    )
