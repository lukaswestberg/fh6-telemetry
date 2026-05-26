import csv
import json
import struct
from pathlib import Path

from .fh6 import (
    PACKET_FIELDS,
    PACKET_SIZE,
    TELE_TIMESTAMP_FIELD,
    TELEMETRY_FIELDS,
    parse_packet,
)


MAGIC = b"FH6R"
VERSION = 2
_HEADER_FORMAT = "<4sBH"  # magic, version, packet_size
HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)
_RECORD_PREFIX = struct.Struct("<I")  # teleTimestampMs
RECORD_SIZE = _RECORD_PREFIX.size + PACKET_SIZE
EXTENSION = ".fh6r"


def _write_header(f):
    f.write(struct.pack(_HEADER_FORMAT, MAGIC, VERSION, PACKET_SIZE))


def _read_header(f):
    raw = f.read(HEADER_SIZE)
    if len(raw) < HEADER_SIZE:
        raise ValueError("File too short to be a recording")
    magic, version, packet_size = struct.unpack(_HEADER_FORMAT, raw)
    if magic != MAGIC:
        raise ValueError(f"Not an FH6 recording (magic={magic!r})")
    if version != VERSION:
        raise ValueError(f"Unsupported recording version: {version}")
    if packet_size != PACKET_SIZE:
        raise ValueError(
            f"Packet size mismatch: file={packet_size}, expected={PACKET_SIZE}"
        )
    return version, packet_size


class Recorder:
    """Append telemetry packets to a binary recording file.

    File layout: 7-byte header (magic + version + packet size), then a
    sequence of records. Each record is a u32 teleTimestampMs followed by
    PACKET_SIZE raw packet bytes.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.count = 0
        self._file = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.path, "wb")
        _write_header(self._file)
        self._file.flush()
        return self

    def __exit__(self, *_):
        if self._file:
            self._file.close()
            self._file = None

    def write(self, tele_ms, raw_packet):
        if len(raw_packet) < PACKET_SIZE:
            raise ValueError(f"Short packet: {len(raw_packet)} bytes")
        self._file.write(_RECORD_PREFIX.pack(tele_ms))
        self._file.write(raw_packet[:PACKET_SIZE])
        self._file.flush()
        self.count += 1


def read_raw_packets(path):
    """Yield (teleTimestampMs, raw_packet) tuples."""
    with open(path, "rb") as f:
        _read_header(f)
        while True:
            chunk = f.read(RECORD_SIZE)
            if len(chunk) < RECORD_SIZE:
                break
            (tele_ms,) = _RECORD_PREFIX.unpack_from(chunk, 0)
            yield tele_ms, chunk[_RECORD_PREFIX.size:]


def read_packets(path):
    for tele_ms, chunk in read_raw_packets(path):
        packet = parse_packet(chunk)
        packet[TELE_TIMESTAMP_FIELD] = tele_ms
        yield packet


def count_packets(path):
    file_size = Path(path).stat().st_size
    return max(0, (file_size - HEADER_SIZE) // RECORD_SIZE)


def export_jsonl(src, dst):
    with open(dst, "w") as f:
        for packet in read_packets(src):
            f.write(json.dumps(packet) + "\n")


def export_csv(src, dst):
    with open(dst, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TELEMETRY_FIELDS)
        writer.writeheader()
        for packet in read_packets(src):
            writer.writerow(packet)


EXPORTERS = {
    "jsonl": export_jsonl,
    "csv": export_csv,
}
