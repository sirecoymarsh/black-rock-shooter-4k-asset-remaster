#!/usr/bin/env python3
"""Hash-bound archive/ISO/delta pipeline for Black Rock Shooter: The Game (PSP).

The source ISO is always opened read-only.  ISO builds are made through a
temporary copy and atomically renamed only after every replacement verifies.
Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable, Iterator


SECTOR = 2048
BASELINE_SHA256 = "4735b0d0f59d480991fd8cf034e5b0f2d98798cec275ab4162df09b8a6d23f0e"
BASELINE_SIZE = 1_360_363_520
RTDP_HEADER = struct.Struct("<4sIIII12s")
RTDP_ENTRY = struct.Struct("<32sII")
LPK_HEADER = struct.Struct("<4sIII")
DELTA_MAGIC = b"BRSPATCH1\n"
DELTA_RECORD = struct.Struct("<QII")


def align(value: int, boundary: int) -> int:
    if boundary < 1:
        raise ValueError("alignment must be positive")
    return (value + boundary - 1) // boundary * boundary


def sha256_file(path: Path, limit: int | None = None) -> str:
    digest = hashlib.sha256()
    remaining = limit
    with path.open("rb") as stream:
        while remaining is None or remaining:
            size = 1024 * 1024 if remaining is None else min(1024 * 1024, remaining)
            block = stream.read(size)
            if not block:
                break
            digest.update(block)
            if remaining is not None:
                remaining -= len(block)
    if remaining not in (None, 0):
        raise EOFError(f"{path}: expected {limit} bytes")
    return digest.hexdigest()


def sha256_range(stream: BinaryIO, offset: int, size: int) -> str:
    digest = hashlib.sha256()
    stream.seek(offset)
    remaining = size
    while remaining:
        block = stream.read(min(1024 * 1024, remaining))
        if not block:
            raise EOFError("unexpected EOF while hashing range")
        digest.update(block)
        remaining -= len(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def safe_relative(raw: str) -> PurePosixPath:
    path = PurePosixPath(raw.replace("\\", "/"))
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"unsafe relative path: {raw!r}")
    return path


@dataclass(frozen=True)
class RtdpItem:
    index: int
    raw_name: bytes
    name: str
    size: int
    relative_offset: int


class Rtdp:
    """RTDP parser/repacker. Entry identity is the stable numeric index."""

    def __init__(self, data: bytes) -> None:
        if len(data) < RTDP_HEADER.size:
            raise ValueError("RTDP is too small")
        magic, data_offset, count, declared_size, marker, reserved = RTDP_HEADER.unpack_from(data)
        if magic != b"RTDP":
            raise ValueError("not RTDP")
        if declared_size != len(data):
            raise ValueError(f"RTDP declared size {declared_size} != {len(data)}")
        table_end = RTDP_HEADER.size + count * RTDP_ENTRY.size
        if table_end > data_offset:
            raise ValueError("RTDP table overlaps payloads")
        self.data = data
        self.data_offset = data_offset
        self.count = count
        self.marker = marker
        self.reserved = reserved
        self.items: list[RtdpItem] = []
        for index in range(count):
            raw_name, size, relative = RTDP_ENTRY.unpack_from(
                data, RTDP_HEADER.size + index * RTDP_ENTRY.size
            )
            name = raw_name.split(b"\0", 1)[0].decode("ascii", "strict")
            if relative + size > len(data) - data_offset:
                raise ValueError(f"RTDP item {index} extends past EOF")
            self.items.append(RtdpItem(index, raw_name, name, size, relative))

    @classmethod
    def read(cls, path: Path) -> "Rtdp":
        return cls(path.read_bytes())

    def payload(self, item: RtdpItem) -> bytes:
        start = self.data_offset + item.relative_offset
        return self.data[start : start + item.size]

    def repack(self, replacements: dict[int, bytes], alignment: int = 32) -> bytes:
        unknown = set(replacements) - set(range(self.count))
        if unknown:
            raise ValueError(f"unknown RTDP replacement indices: {sorted(unknown)}")
        payloads = [replacements.get(item.index, self.payload(item)) for item in self.items]
        # Preserve the original table-to-data gap. The entry count never changes.
        minimum_data = align(RTDP_HEADER.size + self.count * RTDP_ENTRY.size, alignment)
        data_offset = max(self.data_offset, minimum_data)
        relatives: list[int] = []
        cursor = 0
        for payload in payloads:
            cursor = align(cursor, alignment)
            relatives.append(cursor)
            cursor += len(payload)
        total_size = align(data_offset + cursor, alignment)
        output = bytearray(total_size)
        RTDP_HEADER.pack_into(
            output,
            0,
            b"RTDP",
            data_offset,
            self.count,
            total_size,
            self.marker,
            self.reserved,
        )
        for item, payload, relative in zip(self.items, payloads, relatives):
            RTDP_ENTRY.pack_into(
                output,
                RTDP_HEADER.size + item.index * RTDP_ENTRY.size,
                item.raw_name,
                len(payload),
                relative,
            )
            start = data_offset + relative
            output[start : start + len(payload)] = payload
        # Parse the result and verify every entry before releasing bytes.
        check = Rtdp(bytes(output))
        for index, expected in enumerate(payloads):
            if check.payload(check.items[index]) != expected:
                raise AssertionError(f"RTDP verification failed at index {index}")
        return bytes(output)


@dataclass(frozen=True)
class LpkItem:
    index: int
    offset: int
    size: int


class Lpk:
    """LPK parser/repacker with 16-byte payload alignment."""

    def __init__(self, data: bytes) -> None:
        if len(data) < LPK_HEADER.size:
            raise ValueError("LPK is too small")
        magic, count, flags, data_offset = LPK_HEADER.unpack_from(data)
        if magic != b"LPK\0" or count < 1:
            raise ValueError("not LPK")
        table_end = LPK_HEADER.size + (count - 1) * 4 + count * 4
        if table_end > data_offset or data_offset > len(data):
            raise ValueError("invalid LPK table")
        positions = [data_offset]
        cursor = LPK_HEADER.size
        if count > 1:
            positions.extend(struct.unpack_from(f"<{count - 1}I", data, cursor))
            cursor += (count - 1) * 4
        sizes = struct.unpack_from(f"<{count}I", data, cursor)
        self.data = data
        self.count = count
        self.flags = flags
        self.data_offset = data_offset
        self.items: list[LpkItem] = []
        for index, (offset, size) in enumerate(zip(positions, sizes)):
            if offset + size > len(data):
                raise ValueError(f"LPK item {index} extends past EOF")
            self.items.append(LpkItem(index, offset, size))

    @classmethod
    def read(cls, path: Path) -> "Lpk":
        return cls(path.read_bytes())

    def payload(self, item: LpkItem) -> bytes:
        return self.data[item.offset : item.offset + item.size]

    def repack(self, replacements: dict[int, bytes], alignment: int = 16) -> bytes:
        unknown = set(replacements) - set(range(self.count))
        if unknown:
            raise ValueError(f"unknown LPK replacement indices: {sorted(unknown)}")
        payloads = [replacements.get(item.index, self.payload(item)) for item in self.items]
        minimum_data = align(LPK_HEADER.size + (self.count - 1) * 4 + self.count * 4, alignment)
        data_offset = max(self.data_offset, minimum_data)
        offsets: list[int] = []
        cursor = data_offset
        for payload in payloads:
            cursor = align(cursor, alignment)
            offsets.append(cursor)
            cursor += len(payload)
        total_size = align(cursor, alignment)
        output = bytearray(total_size)
        LPK_HEADER.pack_into(output, 0, b"LPK\0", self.count, self.flags, data_offset)
        table_cursor = LPK_HEADER.size
        if self.count > 1:
            struct.pack_into(f"<{self.count - 1}I", output, table_cursor, *offsets[1:])
            table_cursor += (self.count - 1) * 4
        struct.pack_into(
            f"<{self.count}I", output, table_cursor, *(len(payload) for payload in payloads)
        )
        for offset, payload in zip(offsets, payloads):
            output[offset : offset + len(payload)] = payload
        check = Lpk(bytes(output))
        for index, expected in enumerate(payloads):
            if check.payload(check.items[index]) != expected:
                raise AssertionError(f"LPK verification failed at index {index}")
        return bytes(output)


@dataclass(frozen=True)
class IsoEntry:
    path: str
    extent: int
    size: int
    flags: int
    record_offset: int

    @property
    def is_dir(self) -> bool:
        return bool(self.flags & 2)


class Iso9660:
    """Minimal ISO9660 reader that also records file directory-record offsets."""

    def __init__(self, path: Path, writable: bool = False) -> None:
        self.path = path
        self.stream = path.open("r+b" if writable else "rb")
        self.writable = writable
        self.descriptors = self._descriptors()
        primary = next((item for item in self.descriptors if item["type"] == 1), None)
        if primary is None:
            raise ValueError("ISO9660 primary volume descriptor not found")
        self.pvd_offset = int(primary["offset"])
        self.volume_sectors = int(primary["volume_sectors"])
        self.root = self._record(
            self._read_at(self.pvd_offset + 156, self._read_at(self.pvd_offset + 156, 1)[0]),
            PurePosixPath("."),
            self.pvd_offset + 156,
        )
        self.entries = self._walk()
        self.by_path: dict[str, IsoEntry] = {}
        for entry in self.entries:
            key = entry.path.replace("\\", "/").casefold()
            if key in self.by_path:
                raise ValueError(f"duplicate normalized ISO path: {entry.path}")
            self.by_path[key] = entry

    def close(self) -> None:
        self.stream.close()

    def __enter__(self) -> "Iso9660":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _read_at(self, offset: int, size: int) -> bytes:
        self.stream.seek(offset)
        data = self.stream.read(size)
        if len(data) != size:
            raise EOFError(f"ISO read short at {offset:#x}")
        return data

    def _descriptors(self) -> list[dict[str, int]]:
        result: list[dict[str, int]] = []
        for sector in range(16, 256):
            offset = sector * SECTOR
            raw = self._read_at(offset, SECTOR)
            if raw[1:6] != b"CD001":
                if result:
                    break
                continue
            descriptor_type = raw[0]
            le = int.from_bytes(raw[80:84], "little")
            be = int.from_bytes(raw[84:88], "big")
            if descriptor_type in (1, 2) and le != be:
                raise ValueError("ISO volume-space both-endian fields disagree")
            result.append(
                {
                    "type": descriptor_type,
                    "sector": sector,
                    "offset": offset,
                    "volume_sectors": le if descriptor_type in (1, 2) else 0,
                }
            )
            if descriptor_type == 255:
                break
        return result

    @staticmethod
    def _name(raw: bytes) -> str:
        if raw == b"\0":
            return "."
        if raw == b"\1":
            return ".."
        return raw.decode("ascii", "strict").split(";", 1)[0]

    def _record(self, raw: bytes, parent: PurePosixPath, offset: int) -> IsoEntry:
        if len(raw) < 34 or raw[0] != len(raw):
            raise ValueError(f"malformed ISO directory record at {offset:#x}")
        extent_le = int.from_bytes(raw[2:6], "little")
        extent_be = int.from_bytes(raw[6:10], "big")
        size_le = int.from_bytes(raw[10:14], "little")
        size_be = int.from_bytes(raw[14:18], "big")
        if extent_le != extent_be or size_le != size_be:
            raise ValueError(f"ISO both-endian record fields disagree at {offset:#x}")
        length = raw[32]
        name = self._name(raw[33 : 33 + length])
        path = str(parent / name) if str(parent) != "." else name
        return IsoEntry(path, extent_le, size_le, raw[25], offset)

    def _children(self, directory: IsoEntry) -> list[IsoEntry]:
        start = directory.extent * SECTOR
        data = self._read_at(start, directory.size)
        parent = PurePosixPath(directory.path) if directory.path not in ("", ".") else PurePosixPath(".")
        result: list[IsoEntry] = []
        position = 0
        while position < len(data):
            length = data[position]
            if length == 0:
                position = align(position + 1, SECTOR)
                continue
            raw = data[position : position + length]
            name_length = raw[32] if len(raw) >= 33 else 0
            raw_name = raw[33 : 33 + name_length]
            if raw_name in (b"\0", b"\1"):
                position += length
                continue
            record = self._record(raw, parent, start + position)
            result.append(record)
            position += length
        return result

    def _walk(self) -> list[IsoEntry]:
        result: list[IsoEntry] = []
        pending = [self.root]
        seen: set[tuple[int, int]] = set()
        while pending:
            directory = pending.pop()
            identity = (directory.extent, directory.size)
            if identity in seen:
                continue
            seen.add(identity)
            children = self._children(directory)
            result.extend(children)
            pending.extend(reversed([entry for entry in children if entry.is_dir]))
        return sorted(result, key=lambda item: item.path.casefold())

    def get(self, path: str) -> IsoEntry:
        key = str(safe_relative(path)).casefold()
        try:
            return self.by_path[key]
        except KeyError:
            raise KeyError(f"ISO path not found: {path}") from None

    def read_entry(self, entry: IsoEntry) -> bytes:
        if entry.is_dir:
            raise IsADirectoryError(entry.path)
        return self._read_at(entry.extent * SECTOR, entry.size)

    def hash_entry(self, entry: IsoEntry) -> str:
        if entry.is_dir:
            raise IsADirectoryError(entry.path)
        return sha256_range(self.stream, entry.extent * SECTOR, entry.size)

    def _write_both_u32(self, offset: int, value: int) -> None:
        if not self.writable:
            raise PermissionError("ISO opened read-only")
        if not 0 <= value <= 0xFFFFFFFF:
            raise OverflowError(value)
        self.stream.seek(offset)
        self.stream.write(value.to_bytes(4, "little") + value.to_bytes(4, "big"))

    def patch_entry(self, entry: IsoEntry, payload: bytes, mode: str) -> dict[str, object]:
        if not self.writable:
            raise PermissionError("ISO opened read-only")
        if entry.is_dir:
            raise IsADirectoryError(entry.path)
        if mode == "exact" and len(payload) != entry.size:
            raise ValueError(
                f"{entry.path}: exact mode requires {entry.size} bytes, got {len(payload)}"
            )
        capacity = align(entry.size, SECTOR)
        relocate = len(payload) > capacity
        if relocate and mode != "relocate":
            raise ValueError(
                f"{entry.path}: {len(payload)} bytes exceed {capacity}-byte allocation; "
                "use relocate mode"
            )
        if not relocate:
            target_extent = entry.extent
            self.stream.seek(target_extent * SECTOR)
            self.stream.write(payload)
            # Preserve pre-existing ISO sector padding for exact-size replacements.
            # It may contain mastering data and is outside the visible file extent.
            if len(payload) < entry.size:
                self.stream.write(b"\0" * (capacity - len(payload)))
        else:
            self.stream.seek(0, os.SEEK_END)
            file_size = self.stream.tell()
            padded = align(file_size, SECTOR)
            if padded > file_size:
                self.stream.write(b"\0" * (padded - file_size))
            target_extent = padded // SECTOR
            self.stream.write(payload)
            tail = align(len(payload), SECTOR) - len(payload)
            if tail:
                self.stream.write(b"\0" * tail)
        if target_extent != entry.extent:
            self._write_both_u32(entry.record_offset + 2, target_extent)
        if len(payload) != entry.size:
            self._write_both_u32(entry.record_offset + 10, len(payload))
        return {
            "iso_path": entry.path,
            "old_extent": entry.extent,
            "new_extent": target_extent,
            "old_size": entry.size,
            "new_size": len(payload),
            "relocated": relocate,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    def finish_volume(self) -> int:
        if not self.writable:
            raise PermissionError("ISO opened read-only")
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.stream.seek(0, os.SEEK_END)
        size = self.stream.tell()
        if size % SECTOR:
            self.stream.write(b"\0" * (align(size, SECTOR) - size))
            size = align(size, SECTOR)
        sectors = size // SECTOR
        if sectors != self.volume_sectors:
            for descriptor in self.descriptors:
                if descriptor["type"] in (1, 2):
                    self._write_both_u32(int(descriptor["offset"]) + 80, sectors)
        self.stream.flush()
        os.fsync(self.stream.fileno())
        return sectors


def parse_replacements(values: list[str]) -> dict[int, bytes]:
    result: dict[int, bytes] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"replacement must be INDEX=FILE: {value!r}")
        raw_index, raw_path = value.split("=", 1)
        index = int(raw_index, 0)
        if index in result:
            raise ValueError(f"duplicate replacement index: {index}")
        result[index] = Path(raw_path).read_bytes()
    return result


def cmd_rtdp(args: argparse.Namespace) -> None:
    archive = Rtdp.read(args.input)
    output = archive.repack(parse_replacements(args.replace), args.alignment)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(json.dumps({"output": str(args.output), "size": len(output), "sha256": hashlib.sha256(output).hexdigest()}))


def cmd_lpk(args: argparse.Namespace) -> None:
    archive = Lpk.read(args.input)
    output = archive.repack(parse_replacements(args.replace), args.alignment)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(json.dumps({"output": str(args.output), "size": len(output), "sha256": hashlib.sha256(output).hexdigest()}))


def cmd_xor(args: argparse.Namespace) -> None:
    payload = args.input.read_bytes()
    output = bytes(value ^ args.key for value in payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(json.dumps({"output": str(args.output), "size": len(output), "sha256": hashlib.sha256(output).hexdigest()}))


def cmd_gzip_pack(args: argparse.Namespace) -> None:
    payload = args.input.read_bytes()
    # Empty filename + fixed mtime makes repeated builds byte-for-byte deterministic.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=args.level, mtime=0) as stream:
            stream.write(payload)
    if gzip.decompress(args.output.read_bytes()) != payload:
        raise AssertionError("gzip round-trip verification failed")
    print(json.dumps({"output": str(args.output), "size": args.output.stat().st_size, "sha256": sha256_file(args.output)}))


def cmd_gzip_unpack(args: argparse.Namespace) -> None:
    payload = gzip.decompress(args.input.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(json.dumps({"output": str(args.output), "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}))


def iso_summary(path: Path) -> dict[str, object]:
    with Iso9660(path) as iso:
        return {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
            "volume_sectors": iso.volume_sectors,
            "descriptor_types": [item["type"] for item in iso.descriptors],
            "file_count": sum(not item.is_dir for item in iso.entries),
            "directory_count": sum(item.is_dir for item in iso.entries),
        }


def cmd_iso_inspect(args: argparse.Namespace) -> None:
    result = iso_summary(args.iso)
    if args.output:
        atomic_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_iso_extract(args: argparse.Namespace) -> None:
    source_hash = sha256_file(args.iso)
    if args.require_sha256 and source_hash.casefold() != args.require_sha256.casefold():
        raise ValueError(f"source ISO SHA-256 mismatch: {source_hash}")
    destination = args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix.replace("\\", "/").strip("/")
    records: list[dict[str, object]] = []
    with Iso9660(args.iso) as iso:
        for entry in iso.entries:
            if entry.is_dir:
                continue
            if prefix and not (
                entry.path.casefold() == prefix.casefold()
                or entry.path.casefold().startswith(prefix.casefold() + "/")
            ):
                continue
            relative = safe_relative(entry.path)
            output = destination.joinpath(*relative.parts).resolve()
            try:
                output.relative_to(destination)
            except ValueError:
                raise ValueError(f"ISO entry escapes extraction root: {entry.path}") from None
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_name(f".{output.name}.extracting-{os.getpid()}")
            digest = hashlib.sha256()
            iso.stream.seek(entry.extent * SECTOR)
            remaining = entry.size
            try:
                with temporary.open("wb") as target:
                    while remaining:
                        block = iso.stream.read(min(1024 * 1024, remaining))
                        if not block:
                            raise EOFError(f"unexpected EOF extracting {entry.path}")
                        target.write(block)
                        digest.update(block)
                        remaining -= len(block)
                os.replace(temporary, output)
            finally:
                if temporary.exists():
                    temporary.unlink()
            records.append(
                {
                    "iso_path": entry.path,
                    "extent": entry.extent,
                    "size": entry.size,
                    "sha256": digest.hexdigest(),
                    "relative_output": PurePosixPath(*relative.parts).as_posix(),
                }
            )
    result = {
        "schema": "brs-psp-extraction/v1",
        "source_iso": {
            "path_hint": str(args.iso),
            "size": args.iso.stat().st_size,
            "sha256": source_hash,
        },
        "prefix": prefix,
        "destination": str(destination),
        "file_count": len(records),
        "files": records,
    }
    atomic_json(args.manifest, result)
    print(json.dumps({"destination": str(destination), "file_count": len(records), "manifest": str(args.manifest)}))


def cmd_hash_tree(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    records: list[dict[str, object]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: str(item).casefold()):
        relative = path.relative_to(root)
        records.append(
            {
                "path": PurePosixPath(*relative.parts).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    result = {
        "schema": "brs-file-tree/v1",
        "root": str(root),
        "file_count": len(records),
        "total_bytes": sum(int(item["size"]) for item in records),
        "files": records,
    }
    atomic_json(args.output, result)
    print(json.dumps({"root": str(root), "file_count": len(records), "output": str(args.output)}))


def cmd_manifest(args: argparse.Namespace) -> None:
    replacement_root = args.replacement_root.resolve()
    replacement_files = sorted(path for path in replacement_root.rglob("*") if path.is_file())
    if not replacement_files:
        raise ValueError("replacement root contains no files")
    source_hash = sha256_file(args.iso)
    if not args.allow_unknown_source and (
        source_hash.casefold() != BASELINE_SHA256 or args.iso.stat().st_size != BASELINE_SIZE
    ):
        raise ValueError(
            "source is not the trusted NPUH-10126 baseline; "
            "use --allow-unknown-source only after an independent provenance audit"
        )
    replacements: list[dict[str, object]] = []
    with Iso9660(args.iso) as iso:
        for replacement in replacement_files:
            relative = replacement.relative_to(replacement_root)
            iso_path = PurePosixPath(*relative.parts).as_posix()
            entry = iso.get(iso_path)
            if entry.is_dir:
                raise IsADirectoryError(iso_path)
            patched_size = replacement.stat().st_size
            capacity = align(entry.size, SECTOR)
            if args.mode == "exact" and patched_size != entry.size:
                raise ValueError(f"{iso_path}: exact mode size mismatch")
            if args.mode == "allocation" and patched_size > capacity:
                raise ValueError(f"{iso_path}: replacement exceeds existing allocation")
            replacements.append(
                {
                    "iso_path": entry.path,
                    "replacement_file": PurePosixPath("replacements", *relative.parts).as_posix(),
                    "baseline": {
                        "extent": entry.extent,
                        "size": entry.size,
                        "sha256": iso.hash_entry(entry),
                    },
                    "patched": {
                        "size": patched_size,
                        "sha256": sha256_file(replacement),
                    },
                }
            )
        descriptors = [item["type"] for item in iso.descriptors]
        volume_sectors = iso.volume_sectors
    manifest = {
        "schema": "brs-psp-korean-patch/v1",
        "game": {
            "title": "Black Rock Shooter: The Game",
            "product_id": "NPUH-10126",
            "release": "USA PSN PSP",
        },
        "source_iso": {
            "size": args.iso.stat().st_size,
            "sha256": source_hash,
            "known_baseline": source_hash == BASELINE_SHA256,
            "expected_known_size": BASELINE_SIZE,
        },
        "iso9660": {"volume_sectors": volume_sectors, "descriptor_types": descriptors},
        "mode": args.mode,
        "replacements": replacements,
    }
    atomic_json(args.output, manifest)
    print(json.dumps({"manifest": str(args.output), "replacement_count": len(replacements), "source_sha256": source_hash}))


def load_manifest(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "brs-psp-korean-patch/v1":
        raise ValueError("unsupported manifest schema")
    if not isinstance(value.get("replacements"), list):
        raise ValueError("manifest replacements is not a list")
    return value


def preflight_manifest(
    manifest_path: Path, source_iso: Path, package_root: Path
) -> tuple[dict[str, object], list[tuple[dict[str, object], Path]]]:
    manifest = load_manifest(manifest_path)
    expected_source = manifest["source_iso"]
    actual_size = source_iso.stat().st_size
    if actual_size != int(expected_source["size"]):
        raise ValueError(f"source ISO size mismatch: {actual_size} != {expected_source['size']}")
    actual_hash = sha256_file(source_iso)
    if actual_hash.casefold() != str(expected_source["sha256"]).casefold():
        raise ValueError(f"source ISO SHA-256 mismatch: {actual_hash}")
    package_root = package_root.resolve()
    checked: list[tuple[dict[str, object], Path]] = []
    seen: set[str] = set()
    with Iso9660(source_iso) as iso:
        for replacement in manifest["replacements"]:
            iso_path = str(replacement["iso_path"])
            key = iso_path.casefold()
            if key in seen:
                raise ValueError(f"duplicate manifest ISO path: {iso_path}")
            seen.add(key)
            entry = iso.get(iso_path)
            baseline = replacement["baseline"]
            if entry.size != int(baseline["size"]) or entry.extent != int(baseline["extent"]):
                raise ValueError(f"{iso_path}: baseline metadata mismatch")
            if iso.hash_entry(entry).casefold() != str(baseline["sha256"]).casefold():
                raise ValueError(f"{iso_path}: baseline payload hash mismatch")
            rel = safe_relative(str(replacement["replacement_file"]))
            candidate = package_root.joinpath(*rel.parts).resolve()
            try:
                candidate.relative_to(package_root)
            except ValueError:
                raise ValueError(f"replacement escapes package root: {candidate}") from None
            if not candidate.is_file():
                raise FileNotFoundError(candidate)
            patched = replacement["patched"]
            if candidate.stat().st_size != int(patched["size"]):
                raise ValueError(f"{iso_path}: replacement size mismatch")
            if sha256_file(candidate).casefold() != str(patched["sha256"]).casefold():
                raise ValueError(f"{iso_path}: replacement hash mismatch")
            checked.append((replacement, candidate))
    return manifest, checked


def cmd_build_iso(args: argparse.Namespace) -> None:
    source_resolved = args.iso.resolve()
    output_resolved = args.output.resolve()
    if source_resolved == output_resolved:
        raise ValueError("refusing to modify source ISO in place")
    manifest, checked = preflight_manifest(args.manifest, args.iso, args.package_root)
    if not args.allow_unknown_source and not bool(manifest["source_iso"].get("known_baseline")):
        raise ValueError(
            "manifest is not bound to the trusted NPUH-10126 baseline; "
            "use --allow-unknown-source only after an independent provenance audit"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.building-{os.getpid()}")
    if temporary.exists():
        temporary.unlink()
    try:
        shutil.copyfile(args.iso, temporary)
        changes: list[dict[str, object]] = []
        with Iso9660(temporary, writable=True) as iso:
            # A supplementary descriptor would require patching a second directory tree.
            if any(item["type"] == 2 for item in iso.descriptors):
                raise ValueError("Joliet/supplementary directory tree is not supported")
            for replacement, candidate in checked:
                entry = iso.get(str(replacement["iso_path"]))
                changes.append(iso.patch_entry(entry, candidate.read_bytes(), str(manifest["mode"])))
            sectors = iso.finish_volume()
        # Re-open and verify all visible file records and hashes.
        with Iso9660(temporary) as verify:
            for replacement, _candidate in checked:
                entry = verify.get(str(replacement["iso_path"]))
                patched = replacement["patched"]
                if entry.size != int(patched["size"]):
                    raise AssertionError(f"{entry.path}: built size verification failed")
                if verify.hash_entry(entry).casefold() != str(patched["sha256"]).casefold():
                    raise AssertionError(f"{entry.path}: built payload verification failed")
        result = {
            "schema": "brs-psp-korean-build/v1",
            "source_sha256": manifest["source_iso"]["sha256"],
            "patched_iso": {
                "path": str(args.output),
                "size": temporary.stat().st_size,
                "sha256": sha256_file(temporary),
                "volume_sectors": sectors,
            },
            "changes": changes,
        }
        os.replace(temporary, args.output)
        atomic_json(args.result, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        if temporary.exists():
            temporary.unlink()


def cmd_verify_iso(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    result: dict[str, object] = {
        "iso": str(args.iso),
        "size": args.iso.stat().st_size,
        "sha256": sha256_file(args.iso),
        "entries": [],
    }
    with Iso9660(args.iso) as iso:
        for replacement in manifest["replacements"]:
            entry = iso.get(str(replacement["iso_path"]))
            expected = replacement["patched"]
            actual_hash = iso.hash_entry(entry)
            ok = entry.size == int(expected["size"]) and actual_hash.casefold() == str(expected["sha256"]).casefold()
            result["entries"].append(
                {
                    "iso_path": entry.path,
                    "size": entry.size,
                    "sha256": actual_hash,
                    "ok": ok,
                }
            )
        result["ok"] = all(item["ok"] for item in result["entries"])
    if args.output:
        atomic_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(2)


def difference_runs(before: bytes, after: bytes, base: int, gap: int = 32) -> Iterator[tuple[int, bytes]]:
    """Yield target-byte runs, coalescing tiny equal gaps to reduce record overhead."""
    maximum = max(len(before), len(after))
    position = 0
    while position < maximum:
        before_byte = before[position] if position < len(before) else None
        after_byte = after[position] if position < len(after) else None
        if before_byte == after_byte:
            position += 1
            continue
        start = position
        last_difference = position
        position += 1
        while position < maximum:
            before_byte = before[position] if position < len(before) else None
            after_byte = after[position] if position < len(after) else None
            if before_byte != after_byte:
                last_difference = position
            elif position - last_difference > gap:
                break
            position += 1
        end = last_difference + 1
        if start >= len(after):
            # Target truncation needs no bytes; target_size in the header handles it.
            continue
        end = min(end, len(after))
        yield base + start, after[start:end]


def cmd_make_delta(args: argparse.Namespace) -> None:
    if args.source.resolve() == args.target.resolve():
        raise ValueError("source and target must differ")
    source_hash = sha256_file(args.source)
    target_hash = sha256_file(args.target)
    temporary_records = args.output.with_name(f".{args.output.name}.records-{os.getpid()}")
    count = 0
    changed_bytes = 0
    try:
        with args.source.open("rb") as source, args.target.open("rb") as target, temporary_records.open("wb") as records:
            offset = 0
            while True:
                before = source.read(args.block_size)
                after = target.read(args.block_size)
                if not before and not after:
                    break
                if before != after:
                    for record_offset, payload in difference_runs(before, after, offset):
                        compressed = zlib.compress(payload, 9)
                        records.write(DELTA_RECORD.pack(record_offset, len(payload), len(compressed)))
                        records.write(compressed)
                        count += 1
                        changed_bytes += len(payload)
                offset += max(len(before), len(after))
        header = {
            "schema": "brs-binary-delta/v1",
            "source": {"size": args.source.stat().st_size, "sha256": source_hash},
            "target": {"size": args.target.stat().st_size, "sha256": target_hash},
            "record_count": count,
            "changed_bytes": changed_bytes,
            "compression": "zlib",
        }
        encoded = json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = args.output.with_name(f".{args.output.name}.tmp-{os.getpid()}")
        with temporary_output.open("wb") as output, temporary_records.open("rb") as records:
            output.write(DELTA_MAGIC)
            output.write(struct.pack("<I", len(encoded)))
            output.write(encoded)
            shutil.copyfileobj(records, output, 1024 * 1024)
        os.replace(temporary_output, args.output)
        print(json.dumps({**header, "patch": str(args.output), "patch_size": args.output.stat().st_size}, indent=2))
    finally:
        if temporary_records.exists():
            temporary_records.unlink()


def read_delta_header(stream: BinaryIO) -> dict[str, object]:
    if stream.read(len(DELTA_MAGIC)) != DELTA_MAGIC:
        raise ValueError("not a BRSPATCH1 delta")
    raw_length = stream.read(4)
    if len(raw_length) != 4:
        raise EOFError("truncated delta header")
    length = struct.unpack("<I", raw_length)[0]
    if length > 16 * 1024 * 1024:
        raise ValueError("unreasonable delta header size")
    encoded = stream.read(length)
    if len(encoded) != length:
        raise EOFError("truncated delta header JSON")
    header = json.loads(encoded.decode("utf-8"))
    if header.get("schema") != "brs-binary-delta/v1":
        raise ValueError("unsupported delta schema")
    return header


def cmd_apply_delta(args: argparse.Namespace) -> None:
    if args.source.resolve() == args.output.resolve():
        raise ValueError("refusing to modify source file in place")
    with args.patch.open("rb") as patch:
        header = read_delta_header(patch)
        source = header["source"]
        if args.source.stat().st_size != int(source["size"]):
            raise ValueError("delta source size mismatch")
        actual_source_hash = sha256_file(args.source)
        if actual_source_hash.casefold() != str(source["sha256"]).casefold():
            raise ValueError(f"delta source hash mismatch: {actual_source_hash}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(f".{args.output.name}.applying-{os.getpid()}")
        if temporary.exists():
            temporary.unlink()
        try:
            shutil.copyfile(args.source, temporary)
            target_size = int(header["target"]["size"])
            with temporary.open("r+b") as output:
                output.truncate(target_size)
                previous_end = 0
                count = 0
                while True:
                    raw = patch.read(DELTA_RECORD.size)
                    if not raw:
                        break
                    if len(raw) != DELTA_RECORD.size:
                        raise EOFError("truncated delta record")
                    offset, raw_size, compressed_size = DELTA_RECORD.unpack(raw)
                    if raw_size < 1 or compressed_size < 1 or offset < previous_end:
                        raise ValueError("invalid or overlapping delta record")
                    encoded = patch.read(compressed_size)
                    if len(encoded) != compressed_size:
                        raise EOFError("truncated delta payload")
                    payload = zlib.decompress(encoded)
                    if len(payload) != raw_size or offset + raw_size > target_size:
                        raise ValueError("invalid delta payload extent")
                    output.seek(offset)
                    output.write(payload)
                    previous_end = offset + raw_size
                    count += 1
                output.flush()
                os.fsync(output.fileno())
            if count != int(header["record_count"]):
                raise ValueError(f"delta record count mismatch: {count}")
            actual_target_hash = sha256_file(temporary)
            if actual_target_hash.casefold() != str(header["target"]["sha256"]).casefold():
                raise ValueError(f"delta target hash mismatch: {actual_target_hash}")
            os.replace(temporary, args.output)
            print(json.dumps({"output": str(args.output), "size": args.output.stat().st_size, "sha256": actual_target_hash}))
        finally:
            if temporary.exists():
                temporary.unlink()


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    for name, handler, default_alignment in (("rtdp-repack", cmd_rtdp, 32), ("lpk-repack", cmd_lpk, 16)):
        sub = commands.add_parser(name)
        sub.add_argument("input", type=Path)
        sub.add_argument("output", type=Path)
        sub.add_argument("--replace", action="append", default=[], metavar="INDEX=FILE")
        sub.add_argument("--alignment", type=int, default=default_alignment)
        sub.set_defaults(handler=handler)

    sub = commands.add_parser("xor")
    sub.add_argument("input", type=Path)
    sub.add_argument("output", type=Path)
    sub.add_argument("--key", type=lambda item: int(item, 0), default=0x55)
    sub.set_defaults(handler=cmd_xor)

    sub = commands.add_parser("gzip-pack")
    sub.add_argument("input", type=Path)
    sub.add_argument("output", type=Path)
    sub.add_argument("--level", type=int, choices=range(1, 10), default=9)
    sub.set_defaults(handler=cmd_gzip_pack)

    sub = commands.add_parser("gzip-unpack")
    sub.add_argument("input", type=Path)
    sub.add_argument("output", type=Path)
    sub.set_defaults(handler=cmd_gzip_unpack)

    sub = commands.add_parser("iso-inspect")
    sub.add_argument("iso", type=Path)
    sub.add_argument("--output", type=Path)
    sub.set_defaults(handler=cmd_iso_inspect)

    sub = commands.add_parser("iso-extract")
    sub.add_argument("iso", type=Path)
    sub.add_argument("destination", type=Path)
    sub.add_argument("--prefix", default="")
    sub.add_argument("--manifest", type=Path, required=True)
    sub.add_argument("--require-sha256", default=BASELINE_SHA256)
    sub.set_defaults(handler=cmd_iso_extract)

    sub = commands.add_parser("hash-tree")
    sub.add_argument("root", type=Path)
    sub.add_argument("output", type=Path)
    sub.set_defaults(handler=cmd_hash_tree)

    sub = commands.add_parser("make-manifest")
    sub.add_argument("iso", type=Path)
    sub.add_argument("replacement_root", type=Path)
    sub.add_argument("output", type=Path)
    sub.add_argument("--mode", choices=("exact", "allocation", "relocate"), default="exact")
    sub.add_argument("--allow-unknown-source", action="store_true")
    sub.set_defaults(handler=cmd_manifest)

    sub = commands.add_parser("build-iso")
    sub.add_argument("iso", type=Path, help="trusted, read-only source ISO")
    sub.add_argument("manifest", type=Path)
    sub.add_argument("package_root", type=Path)
    sub.add_argument("output", type=Path)
    sub.add_argument("--result", type=Path, required=True)
    sub.add_argument("--allow-unknown-source", action="store_true")
    sub.set_defaults(handler=cmd_build_iso)

    sub = commands.add_parser("verify-iso")
    sub.add_argument("iso", type=Path)
    sub.add_argument("manifest", type=Path)
    sub.add_argument("--output", type=Path)
    sub.set_defaults(handler=cmd_verify_iso)

    sub = commands.add_parser("make-delta")
    sub.add_argument("source", type=Path)
    sub.add_argument("target", type=Path)
    sub.add_argument("output", type=Path)
    sub.add_argument("--block-size", type=int, default=1024 * 1024)
    sub.set_defaults(handler=cmd_make_delta)

    sub = commands.add_parser("apply-delta")
    sub.add_argument("source", type=Path)
    sub.add_argument("patch", type=Path)
    sub.add_argument("output", type=Path)
    sub.set_defaults(handler=cmd_apply_delta)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
