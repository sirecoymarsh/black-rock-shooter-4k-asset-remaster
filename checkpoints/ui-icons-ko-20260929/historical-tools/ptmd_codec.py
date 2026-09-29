#!/usr/bin/env python3
"""Lossless codec for Black Rock Shooter PSP indexed PTMD UI textures.

The UI variant of PTMD used by this project has a fixed 16-byte header,
PSP-style 16-byte by 8-row swizzled index data, and a trailing CLUT:

* texture mode 4: T4 (4-bit indexes, 16 CLUT entries)
* texture mode 5: T8 (8-bit indexes, 256 CLUT entries)
* palette code 0x20: RGBA4444
* palette code 0x30: RGBA8888

RGBA4444 stores R in bits 0..3, G in bits 4..7, B in bits 8..11, and
A in bits 12..15.  RGBA8888 is stored as four literal R, G, B, A bytes.
T4 stores the left pixel in the low nibble.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Sequence


HEADER_SIZE = 16
MAGIC = b"PTMD"
MODE_T4 = 4
MODE_T8 = 5
PALETTE_RGBA4444 = 0x20
PALETTE_RGBA8888 = 0x30
PALETTE_OFFSET = struct.Struct("<I")
RGBA = tuple[int, int, int, int]


class PtmdError(ValueError):
    """Raised when a PTMD texture violates the supported UI format."""


@dataclass(frozen=True)
class PtmdTexture:
    """Decoded PTMD texture.

    ``indexes`` is row-major, one byte per pixel even for T4.  ``header`` is
    retained verbatim so decode -> encode preserves all header bytes.
    """

    header: bytes
    width: int
    height: int
    mode: int
    palette_code: int
    palette_offset: int
    indexes: bytes
    palette_rgba: tuple[RGBA, ...]

    @property
    def bits_per_index(self) -> int:
        return 4 if self.mode == MODE_T4 else 8

    @property
    def palette_format(self) -> str:
        return (
            "RGBA4444"
            if self.palette_code == PALETTE_RGBA4444
            else "RGBA8888"
        )

    @property
    def palette_entry_count(self) -> int:
        return 16 if self.mode == MODE_T4 else 256

    @property
    def rgba_bytes(self) -> bytes:
        output = bytearray(self.width * self.height * 4)
        cursor = 0
        for index in self.indexes:
            color = self.palette_rgba[index]
            output[cursor : cursor + 4] = bytes(color)
            cursor += 4
        return bytes(output)

    def with_indexes(self, indexes: bytes | bytearray | Iterable[int]) -> "PtmdTexture":
        return replace(self, indexes=bytes(indexes))

    def with_palette(self, palette: Sequence[Sequence[int]]) -> "PtmdTexture":
        return replace(
            self,
            palette_rgba=tuple(_validate_rgba(color) for color in palette),
        )


def _validate_rgba(color: Sequence[int]) -> RGBA:
    if len(color) != 4:
        raise PtmdError(f"RGBA color must have four components, got {len(color)}")
    result = tuple(int(component) for component in color)
    if any(component < 0 or component > 255 for component in result):
        raise PtmdError(f"RGBA component outside 0..255: {result}")
    return result  # type: ignore[return-value]


def _dimensions_from_header(header: bytes) -> tuple[int, int]:
    width_exponent = header[7] >> 4
    if width_exponent > 15:
        raise PtmdError(f"invalid width exponent: {width_exponent}")
    width = 1 << width_exponent
    height = header[6] | ((header[7] & 0x0F) << 8)
    if not width or not height:
        raise PtmdError(f"invalid dimensions: {width}x{height}")
    return width, height


def _row_bytes(width: int, mode: int) -> int:
    if mode == MODE_T4:
        if width & 1:
            raise PtmdError("T4 width must be even")
        return width // 2
    if mode == MODE_T8:
        return width
    raise PtmdError(f"unsupported texture mode {mode}; expected 4 (T4) or 5 (T8)")


def _palette_geometry(mode: int, palette_code: int) -> tuple[int, int]:
    if mode == MODE_T4:
        count = 16
    elif mode == MODE_T8:
        count = 256
    else:
        raise PtmdError(f"unsupported texture mode: {mode}")
    if palette_code == PALETTE_RGBA4444:
        bytes_per_entry = 2
    elif palette_code == PALETTE_RGBA8888:
        bytes_per_entry = 4
    else:
        raise PtmdError(
            f"unsupported palette code 0x{palette_code:02X}; "
            "expected 0x20 (RGBA4444) or 0x30 (RGBA8888)"
        )
    return count, bytes_per_entry


def unswizzle_psp(swizzled: bytes, row_bytes: int, height: int) -> bytes:
    """Convert PSP 16-byte x 8-row tile order to linear rows."""

    if row_bytes <= 0 or height <= 0:
        raise PtmdError("row width and height must be positive")
    if row_bytes % 16:
        raise PtmdError(f"swizzled row width must be a multiple of 16, got {row_bytes}")
    if height % 8:
        raise PtmdError(f"swizzled height must be a multiple of 8, got {height}")
    expected = row_bytes * height
    if len(swizzled) != expected:
        raise PtmdError(f"swizzled data size {len(swizzled)} != expected {expected}")

    tiles_x = row_bytes // 16
    linear = bytearray(expected)
    for y in range(height):
        row_base = y * row_bytes
        tile_row = y // 8
        within_y = y & 7
        for x in range(row_bytes):
            tile_index = tile_row * tiles_x + x // 16
            source = tile_index * 128 + within_y * 16 + (x & 15)
            linear[row_base + x] = swizzled[source]
    return bytes(linear)


def swizzle_psp(linear: bytes, row_bytes: int, height: int) -> bytes:
    """Convert linear rows to PSP 16-byte x 8-row tile order."""

    if row_bytes <= 0 or height <= 0:
        raise PtmdError("row width and height must be positive")
    if row_bytes % 16:
        raise PtmdError(f"linear row width must be a multiple of 16, got {row_bytes}")
    if height % 8:
        raise PtmdError(f"linear height must be a multiple of 8, got {height}")
    expected = row_bytes * height
    if len(linear) != expected:
        raise PtmdError(f"linear data size {len(linear)} != expected {expected}")

    tiles_x = row_bytes // 16
    swizzled = bytearray(expected)
    for y in range(height):
        row_base = y * row_bytes
        tile_row = y // 8
        within_y = y & 7
        for x in range(row_bytes):
            tile_index = tile_row * tiles_x + x // 16
            destination = tile_index * 128 + within_y * 16 + (x & 15)
            swizzled[destination] = linear[row_base + x]
    return bytes(swizzled)


def _decode_indexes(linear: bytes, mode: int, pixel_count: int) -> bytes:
    if mode == MODE_T8:
        indexes = linear
    else:
        unpacked = bytearray(len(linear) * 2)
        for offset, value in enumerate(linear):
            unpacked[offset * 2] = value & 0x0F
            unpacked[offset * 2 + 1] = value >> 4
        indexes = bytes(unpacked)
    if len(indexes) != pixel_count:
        raise PtmdError(f"decoded index count {len(indexes)} != {pixel_count}")
    return indexes


def _encode_indexes(indexes: bytes, mode: int) -> bytes:
    if mode == MODE_T8:
        return indexes
    packed = bytearray(len(indexes) // 2)
    for offset in range(0, len(indexes), 2):
        packed[offset // 2] = indexes[offset] | (indexes[offset + 1] << 4)
    return bytes(packed)


def _decode_palette(payload: bytes, code: int, count: int) -> tuple[RGBA, ...]:
    if code == PALETTE_RGBA8888:
        return tuple(
            tuple(payload[offset : offset + 4])  # type: ignore[misc]
            for offset in range(0, count * 4, 4)
        )

    colors: list[RGBA] = []
    for (value,) in struct.iter_unpack("<H", payload):
        colors.append(
            (
                (value & 0x000F) * 17,
                ((value >> 4) & 0x000F) * 17,
                ((value >> 8) & 0x000F) * 17,
                ((value >> 12) & 0x000F) * 17,
            )
        )
    if len(colors) != count:
        raise PtmdError(f"decoded palette count {len(colors)} != {count}")
    return tuple(colors)


def _quantize_nibble(component: int) -> int:
    # Round to the nearest 4-bit level. Multiples of 17 round-trip exactly.
    return min(15, (component + 8) // 17)


def _encode_palette(palette: Sequence[Sequence[int]], code: int) -> bytes:
    colors = tuple(_validate_rgba(color) for color in palette)
    if code == PALETTE_RGBA8888:
        return b"".join(bytes(color) for color in colors)

    output = bytearray(len(colors) * 2)
    for index, (red, green, blue, alpha) in enumerate(colors):
        value = (
            _quantize_nibble(red)
            | (_quantize_nibble(green) << 4)
            | (_quantize_nibble(blue) << 8)
            | (_quantize_nibble(alpha) << 12)
        )
        struct.pack_into("<H", output, index * 2, value)
    return bytes(output)


def decode_ptmd(data: bytes | bytearray | memoryview) -> PtmdTexture:
    """Parse one supported UI PTMD payload."""

    payload = bytes(data)
    if len(payload) < HEADER_SIZE:
        raise PtmdError(f"PTMD is too small: {len(payload)} bytes")
    header = payload[:HEADER_SIZE]
    if header[:4] != MAGIC:
        raise PtmdError(f"bad PTMD magic: {header[:4]!r}")
    width, height = _dimensions_from_header(header)
    mode = header[8]
    palette_code = header[9]
    count, bytes_per_entry = _palette_geometry(mode, palette_code)
    row_bytes = _row_bytes(width, mode)
    if row_bytes % 16 or height % 8:
        raise PtmdError(
            f"unsupported non-tiled dimensions: {width}x{height}, "
            f"{row_bytes} bytes/row"
        )

    palette_offset = PALETTE_OFFSET.unpack_from(header, 12)[0]
    expected_index_size = row_bytes * height
    expected_palette_offset = HEADER_SIZE + expected_index_size
    if palette_offset != expected_palette_offset:
        raise PtmdError(
            f"palette offset 0x{palette_offset:X} != expected "
            f"0x{expected_palette_offset:X}"
        )
    palette_size = count * bytes_per_entry
    expected_size = palette_offset + palette_size
    if len(payload) != expected_size:
        raise PtmdError(f"PTMD size {len(payload)} != expected {expected_size}")

    swizzled = payload[HEADER_SIZE:palette_offset]
    linear = unswizzle_psp(swizzled, row_bytes, height)
    indexes = _decode_indexes(linear, mode, width * height)
    if indexes and max(indexes) >= count:
        raise PtmdError(f"palette index {max(indexes)} outside 0..{count - 1}")
    palette = _decode_palette(payload[palette_offset:], palette_code, count)
    return PtmdTexture(
        header=header,
        width=width,
        height=height,
        mode=mode,
        palette_code=palette_code,
        palette_offset=palette_offset,
        indexes=indexes,
        palette_rgba=palette,
    )


def encode_ptmd(texture: PtmdTexture) -> bytes:
    """Encode one texture while preserving its 16-byte header verbatim."""

    if len(texture.header) != HEADER_SIZE or texture.header[:4] != MAGIC:
        raise PtmdError("texture does not contain a valid 16-byte PTMD header")
    header_width, header_height = _dimensions_from_header(texture.header)
    header_mode = texture.header[8]
    header_palette_code = texture.header[9]
    header_palette_offset = PALETTE_OFFSET.unpack_from(texture.header, 12)[0]
    if (header_width, header_height) != (texture.width, texture.height):
        raise PtmdError("texture dimensions disagree with retained header")
    if header_mode != texture.mode:
        raise PtmdError("texture mode disagrees with retained header")
    if header_palette_code != texture.palette_code:
        raise PtmdError("palette code disagrees with retained header")
    if header_palette_offset != texture.palette_offset:
        raise PtmdError("palette offset disagrees with retained header")

    count, bytes_per_entry = _palette_geometry(texture.mode, texture.palette_code)
    pixel_count = texture.width * texture.height
    if len(texture.indexes) != pixel_count:
        raise PtmdError(f"index count {len(texture.indexes)} != {pixel_count}")
    if texture.indexes and max(texture.indexes) >= count:
        raise PtmdError(f"palette index {max(texture.indexes)} outside 0..{count - 1}")
    if len(texture.palette_rgba) != count:
        raise PtmdError(
            f"palette has {len(texture.palette_rgba)} colors; expected {count}"
        )

    row_bytes = _row_bytes(texture.width, texture.mode)
    packed_indexes = _encode_indexes(texture.indexes, texture.mode)
    if len(packed_indexes) != row_bytes * texture.height:
        raise PtmdError("packed index size does not match dimensions")
    swizzled = swizzle_psp(packed_indexes, row_bytes, texture.height)
    palette = _encode_palette(texture.palette_rgba, texture.palette_code)
    if len(palette) != count * bytes_per_entry:
        raise AssertionError("internal palette encoder size mismatch")
    encoded = texture.header + swizzled + palette
    expected_size = texture.palette_offset + len(palette)
    if len(encoded) != expected_size:
        raise PtmdError(f"encoded size {len(encoded)} != expected {expected_size}")
    return encoded


def decode_file(path: Path) -> PtmdTexture:
    return decode_ptmd(path.read_bytes())


def encode_file(path: Path, texture: PtmdTexture) -> None:
    encoded = encode_ptmd(texture)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def image_to_indexes(
    rgba: bytes | bytearray | memoryview,
    texture: PtmdTexture,
    *,
    exact: bool = False,
) -> bytes:
    """Map row-major RGBA bytes to the retained PTMD palette.

    Exact palette hits are preferred.  Otherwise the nearest color in
    straight RGBA squared distance is selected.  ``exact=True`` rejects
    colors not already present in the palette.
    """

    pixels = bytes(rgba)
    expected = texture.width * texture.height * 4
    if len(pixels) != expected:
        raise PtmdError(f"RGBA byte count {len(pixels)} != expected {expected}")
    exact_map: dict[RGBA, int] = {}
    for index, color in enumerate(texture.palette_rgba):
        exact_map.setdefault(color, index)
    cache: dict[RGBA, int] = {}
    indexes = bytearray(texture.width * texture.height)
    for pixel_index, offset in enumerate(range(0, len(pixels), 4)):
        color: RGBA = tuple(pixels[offset : offset + 4])  # type: ignore[assignment]
        # Preserve the template's exact index whenever its rendered color did
        # not change. This keeps PNG decode -> encode byte-identical even when
        # two CLUT slots contain the same RGBA value.
        template_index = texture.indexes[pixel_index]
        palette_index = (
            template_index
            if texture.palette_rgba[template_index] == color
            else exact_map.get(color)
        )
        if palette_index is None:
            if exact:
                raise PtmdError(
                    f"pixel {pixel_index} color {color} is not in the PTMD palette"
                )
            palette_index = cache.get(color)
            if palette_index is None:
                palette_index = min(
                    range(len(texture.palette_rgba)),
                    key=lambda candidate: (
                        sum(
                            (texture.palette_rgba[candidate][channel] - color[channel])
                            ** 2
                            for channel in range(4)
                        ),
                        candidate,
                    ),
                )
                cache[color] = palette_index
        indexes[pixel_index] = palette_index
    return bytes(indexes)


def replace_from_rgba(
    texture: PtmdTexture,
    rgba: bytes | bytearray | memoryview,
    *,
    exact: bool = False,
) -> PtmdTexture:
    return texture.with_indexes(image_to_indexes(rgba, texture, exact=exact))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def roundtrip_tree(root: Path, reference_png_root: Path | None = None) -> dict[str, object]:
    """Decode and re-encode every ``*.ptm`` below *root* byte-identically."""

    files = sorted(root.rglob("*.ptm"), key=lambda path: path.as_posix().casefold())
    if not files:
        raise FileNotFoundError(f"no .ptm files below {root}")
    records: list[dict[str, object]] = []
    failures: list[str] = []
    for path in files:
        original = path.read_bytes()
        texture = decode_ptmd(original)
        rebuilt = encode_ptmd(texture)
        relative = _safe_relative(path, root)
        record: dict[str, object] = {
            "path": relative,
            "size": len(original),
            "sha256": sha256_bytes(original),
            "width": texture.width,
            "height": texture.height,
            "mode": texture.mode,
            "texture_mode": "T4" if texture.mode == MODE_T4 else "T8",
            "palette_code": f"0x{texture.palette_code:02X}",
            "palette_format": texture.palette_format,
            "palette_offset": texture.palette_offset,
            "byte_identical": rebuilt == original,
        }
        rgba_rebuilt = encode_ptmd(
            replace_from_rgba(texture, texture.rgba_bytes, exact=True)
        )
        record["rgba_reencode_byte_identical"] = rgba_rebuilt == original
        if rgba_rebuilt != original:
            record["rgba_reencode_sha256"] = sha256_bytes(rgba_rebuilt)
            failures.append(f"{relative} (RGBA re-encode)")
        if rebuilt != original:
            first_difference = next(
                (
                    index
                    for index, (left, right) in enumerate(zip(original, rebuilt))
                    if left != right
                ),
                min(len(original), len(rebuilt)),
            )
            record["rebuilt_sha256"] = sha256_bytes(rebuilt)
            record["first_difference"] = first_difference
            failures.append(relative)

        if reference_png_root is not None:
            png_name = relative.replace("/", "__") + ".png"
            png_path = reference_png_root / png_name
            record["reference_png"] = png_path.as_posix()
            if png_path.is_file():
                try:
                    from PIL import Image

                    image = Image.open(png_path).convert("RGBA")
                    reference_match = (
                        image.size == (texture.width, texture.height)
                        and image.tobytes() == texture.rgba_bytes
                    )
                except Exception as error:  # pragma: no cover - diagnostic path
                    reference_match = False
                    record["reference_png_error"] = f"{type(error).__name__}: {error}"
                record["reference_png_match"] = reference_match
                if not reference_match:
                    failures.append(f"{relative} (reference PNG)")
            else:
                record["reference_png_match"] = None
        records.append(record)

    by_mode: dict[str, int] = {}
    by_palette: dict[str, int] = {}
    for record in records:
        mode = str(record["texture_mode"])
        palette = str(record["palette_format"])
        by_mode[mode] = by_mode.get(mode, 0) + 1
        by_palette[palette] = by_palette.get(palette, 0) + 1
    return {
        "schema": "brs-ptmd-roundtrip-v1",
        "root": str(root.resolve()),
        "file_count": len(records),
        "byte_identical_count": sum(
            bool(record["byte_identical"]) for record in records
        ),
        "rgba_reencode_byte_identical_count": sum(
            bool(record["rgba_reencode_byte_identical"]) for record in records
        ),
        "reference_png_match_count": sum(
            record.get("reference_png_match") is True for record in records
        ),
        "mode_counts": dict(sorted(by_mode.items())),
        "palette_counts": dict(sorted(by_palette.items())),
        "failures": failures,
        "passed": not failures,
        "files": records,
    }


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _write_roundtrip_markdown(path: Path, report: dict[str, object]) -> None:
    failures = report["failures"]
    lines = [
        "# PTMD 코덱 왕복 검증",
        "",
        f"- 파일: **{report['file_count']}개**",
        f"- 바이트 동일: **{report['byte_identical_count']}개**",
        f"- RGBA 재인코딩 바이트 동일: "
        f"**{report['rgba_reencode_byte_identical_count']}개**",
        f"- 기준 PNG 일치: **{report['reference_png_match_count']}개**",
        f"- 모드: `{json.dumps(report['mode_counts'], ensure_ascii=False)}`",
        f"- 팔레트: `{json.dumps(report['palette_counts'], ensure_ascii=False)}`",
        f"- 결과: **{'PASS' if report['passed'] else 'FAIL'}**",
        "",
    ]
    if failures:
        lines.extend(["## 실패", "", *[f"- `{failure}`" for failure in failures], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, path)


def _cmd_decode(args: argparse.Namespace) -> int:
    from PIL import Image

    texture = decode_file(args.input)
    image = Image.frombytes("RGBA", (texture.width, texture.height), texture.rgba_bytes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    if args.metadata:
        metadata = {
            "input": str(args.input.resolve()),
            "output": str(args.output.resolve()),
            "width": texture.width,
            "height": texture.height,
            "mode": texture.mode,
            "palette_format": texture.palette_format,
            "palette": texture.palette_rgba,
        }
        _atomic_json(args.metadata, metadata)
    return 0


def _cmd_encode(args: argparse.Namespace) -> int:
    from PIL import Image

    texture = decode_file(args.template)
    image = Image.open(args.input).convert("RGBA")
    if image.size != (texture.width, texture.height):
        raise PtmdError(
            f"PNG size {image.size} != template size "
            f"{(texture.width, texture.height)}"
        )
    patched = replace_from_rgba(texture, image.tobytes(), exact=args.exact)
    encode_file(args.output, patched)
    if args.output.stat().st_size != args.template.stat().st_size:
        raise AssertionError("encoded PTMD size changed")
    return 0


def _cmd_roundtrip(args: argparse.Namespace) -> int:
    report = roundtrip_tree(args.root, args.reference_png_root)
    _atomic_json(args.report, report)
    if args.markdown:
        _write_roundtrip_markdown(args.markdown, report)
    print(
        json.dumps(
            {
                "file_count": report["file_count"],
                "byte_identical_count": report["byte_identical_count"],
                "reference_png_match_count": report["reference_png_match_count"],
                "passed": report["passed"],
                "report": str(args.report.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["passed"] else 1


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    project = _default_project_root()
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    decode_parser = subparsers.add_parser("decode", help="decode PTMD to RGBA PNG")
    decode_parser.add_argument("input", type=Path)
    decode_parser.add_argument("output", type=Path)
    decode_parser.add_argument("--metadata", type=Path)
    decode_parser.set_defaults(handler=_cmd_decode)

    encode_parser = subparsers.add_parser(
        "encode", help="encode RGBA PNG using a PTMD template"
    )
    encode_parser.add_argument("template", type=Path)
    encode_parser.add_argument("input", type=Path)
    encode_parser.add_argument("output", type=Path)
    encode_parser.add_argument(
        "--exact", action="store_true", help="reject colors absent from the CLUT"
    )
    encode_parser.set_defaults(handler=_cmd_encode)

    roundtrip_parser = subparsers.add_parser(
        "roundtrip", help="verify byte-identical decode/encode for a PTMD tree"
    )
    roundtrip_parser.add_argument(
        "root", type=Path, nargs="?", default=project / "work" / "lpk"
    )
    roundtrip_parser.add_argument(
        "--reference-png-root",
        type=Path,
        default=project / "work" / "ui_audit_local" / "correct_decoded",
    )
    roundtrip_parser.add_argument(
        "--report",
        type=Path,
        default=Path(__file__).resolve().parent / "ptmd_roundtrip_report.json",
    )
    roundtrip_parser.add_argument(
        "--markdown",
        type=Path,
        default=Path(__file__).resolve().parent / "ptmd_roundtrip_report.md",
    )
    roundtrip_parser.set_defaults(handler=_cmd_roundtrip)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (OSError, PtmdError, ValueError) as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    raise SystemExit(main())
