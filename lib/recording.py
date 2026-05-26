import csv
import json
import struct
from pathlib import Path

from .fh6 import PACKET_FIELDS, PACKET_SIZE, parse_packet


MAGIC = b"FH6R"
VERSION = 1
_HEADER_FORMAT = "<4sBH"  # magic, version, packet_size
HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)
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
    """Append raw telemetry packets to a binary recording file.

    File layout: 7-byte header (magic + version + packet size), then
    concatenated raw UDP packets at PACKET_SIZE bytes each.
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

    def write(self, raw_packet):
        if len(raw_packet) < PACKET_SIZE:
            raise ValueError(f"Short packet: {len(raw_packet)} bytes")
        self._file.write(raw_packet[:PACKET_SIZE])
        self._file.flush()
        self.count += 1


def read_raw_packets(path):
    with open(path, "rb") as f:
        _read_header(f)
        while True:
            chunk = f.read(PACKET_SIZE)
            if len(chunk) < PACKET_SIZE:
                break
            yield chunk


def read_packets(path):
    for chunk in read_raw_packets(path):
        yield parse_packet(chunk)


def count_packets(path):
    file_size = Path(path).stat().st_size
    return max(0, (file_size - HEADER_SIZE) // PACKET_SIZE)


def export_jsonl(src, dst):
    with open(dst, "w") as f:
        for packet in read_packets(src):
            f.write(json.dumps(packet) + "\n")


def export_csv(src, dst):
    with open(dst, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PACKET_FIELDS)
        writer.writeheader()
        for packet in read_packets(src):
            writer.writerow(packet)


EXPORTERS = {
    "jsonl": export_jsonl,
    "csv": export_csv,
}
