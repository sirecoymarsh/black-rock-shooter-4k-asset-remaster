#!/usr/bin/env python3
"""Build and verify the BRS PSP Korean multibyte font.

The US build decodes UTF-8 script text to UCS-2, looks the scalar up in
SYSTEM.VOL/ucs2jis.bin, converts the returned JIS row/cell to Shift-JIS, and
selects a 15x15 glyph from font.lpk.  Hangul is represented in scripts by safe
BMP aliases.  This keeps common Korean syllables at two UTF-8 bytes and avoids
an executable patch.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import glob
import hashlib
import json
import math
import struct
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from PIL import Image, ImageDraw, ImageFont

try:
    from fontTools.ttLib import TTFont
except ImportError:  # pragma: no cover - Pillow-only fallback
    TTFont = None


LPK_HEADER = struct.Struct("<4sIII")
FONT_BITMAP_OFFSET = 0x60
FONT_CELL_WIDTH = 15
FONT_CELL_HEIGHT = 15
FONT_CELL_PIXELS = FONT_CELL_WIDTH * FONT_CELL_HEIGHT
FONT_CELL_BYTES = (FONT_CELL_PIXELS + 1) // 2
KANJI_SLOT_MIN_SJIS = 0x889F
UCS2JIS_SIZE = 0x10000 * 2

DEFAULT_TARGET_FIELDS = (
    "translation",
    "target",
    "korean",
    "ko",
    "text_ko",
    "translated",
    "translated_text",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_int(value: str) -> int:
    return int(value, 0)


def is_hangul(character: str) -> bool:
    cp = ord(character)
    return (
        0x1100 <= cp <= 0x11FF
        or 0x3130 <= cp <= 0x318F
        or 0xA960 <= cp <= 0xA97F
        or 0xAC00 <= cp <= 0xD7A3
        or 0xD7B0 <= cp <= 0xD7FF
    )


def shift_jis_to_jis(code: int) -> int:
    """Convert a standard two-byte Shift-JIS value to JIS X 0208 row/cell."""
    lead, trail = code >> 8, code & 0xFF
    if not (0x81 <= lead <= 0x9F or 0xE0 <= lead <= 0xEF):
        raise ValueError(f"not a standard two-byte Shift-JIS code: {code:#06x}")
    if not (0x40 <= trail <= 0xFC) or trail == 0x7F:
        raise ValueError(f"invalid Shift-JIS trail byte: {code:#06x}")
    row = (lead - (0x81 if lead <= 0x9F else 0xC1)) * 2 + 0x21
    if trail >= 0x9F:
        row += 1
        cell = trail - 0x7E
    else:
        adjusted = trail - 1 if trail >= 0x80 else trail
        cell = adjusted - 0x1F
    if not (0x21 <= row <= 0x7E and 0x21 <= cell <= 0x7E):
        raise ValueError(f"invalid JIS result for {code:#06x}: {row:#x}/{cell:#x}")
    return row << 8 | cell


def jis_to_shift_jis(code: int) -> int:
    """Convert a JIS X 0208 row/cell value to standard two-byte Shift-JIS."""
    row, cell = code >> 8, code & 0xFF
    if not (0x21 <= row <= 0x7E and 0x21 <= cell <= 0x7E):
        raise ValueError(f"not a JIS X 0208 row/cell: {code:#06x}")
    lead = ((row - 0x21) // 2) + 0x81
    if lead > 0x9F:
        lead += 0x40
    if row & 1:
        trail = cell + 0x1F
        if trail >= 0x7F:
            trail += 1
    else:
        trail = cell + 0x7E
    result = lead << 8 | trail
    if shift_jis_to_jis(result) != code:
        raise AssertionError("JIS/Shift-JIS conversion is not reversible")
    return result


@dataclasses.dataclass(frozen=True)
class LpkEntry:
    index: int
    offset: int
    size: int


@dataclasses.dataclass(frozen=True)
class FontLayout:
    lpk_font_offset: int
    lpk_font_size: int
    glyph_count: int
    glyph_width: int
    glyph_height: int
    bitmap_offset: int
    bitmap_bytes: int
    code_table_offset: int
    code_table_bytes: int
    codes: tuple[int, ...]
    palette_rgba: tuple[tuple[int, int, int, int], ...]

    @property
    def palette_alpha(self) -> tuple[int, ...]:
        return tuple(entry[3] for entry in self.palette_rgba)


@dataclasses.dataclass(frozen=True)
class GlyphAlias:
    character: str
    unicode_codepoint: int
    frequency: int
    alias_character: str
    alias_codepoint: int
    alias_utf8_hex: str
    alias_utf8_bytes: int
    font_index: int
    shift_jis_code: int
    jis_code: int
    original_ucs2jis: int
    original_cell_sha256: str
    patched_cell_sha256: str


def parse_lpk(data: bytes) -> tuple[int, int, tuple[LpkEntry, ...]]:
    if len(data) < LPK_HEADER.size:
        raise ValueError("LPK is truncated")
    magic, count, flags, data_offset = LPK_HEADER.unpack_from(data)
    if magic != b"LPK\0" or count < 1:
        raise ValueError("not an LPK archive")
    table_end = LPK_HEADER.size + (count - 1) * 4 + count * 4
    if not (table_end <= data_offset <= len(data)):
        raise ValueError("invalid LPK table/data boundary")
    cursor = LPK_HEADER.size
    offsets = [data_offset]
    if count > 1:
        offsets.extend(struct.unpack_from(f"<{count - 1}I", data, cursor))
        cursor += (count - 1) * 4
    sizes = struct.unpack_from(f"<{count}I", data, cursor)
    entries: list[LpkEntry] = []
    previous = data_offset
    for index, (offset, size) in enumerate(zip(offsets, sizes)):
        if offset < previous or offset + size > len(data):
            raise ValueError(f"LPK entry {index} has invalid bounds")
        entries.append(LpkEntry(index, offset, size))
        previous = offset
    return count, flags, tuple(entries)


def parse_font_layout(font_lpk: bytes) -> tuple[FontLayout, bytes]:
    count, _flags, entries = parse_lpk(font_lpk)
    if count < 1:
        raise ValueError("font.lpk has no entries")
    entry = entries[0]
    payload = font_lpk[entry.offset : entry.offset + entry.size]
    if len(payload) < FONT_BITMAP_OFFSET:
        raise ValueError("font payload is truncated")
    code_table_offset = struct.unpack_from("<I", payload, 0x00)[0]
    bitmap_bytes = struct.unpack_from("<I", payload, 0x08)[0]
    code_table_bytes = struct.unpack_from("<I", payload, 0x0C)[0]
    glyph_count = struct.unpack_from("<H", payload, 0x18)[0]
    glyph_width, glyph_height = payload[0x1A], payload[0x1B]
    if (glyph_width, glyph_height) != (FONT_CELL_WIDTH, FONT_CELL_HEIGHT):
        raise ValueError(
            f"unexpected cell dimensions: {glyph_width}x{glyph_height}"
        )
    if bitmap_bytes != glyph_count * FONT_CELL_BYTES:
        raise ValueError(
            f"bitmap size mismatch: {bitmap_bytes} != "
            f"{glyph_count}*{FONT_CELL_BYTES}"
        )
    if code_table_bytes != glyph_count * 2:
        raise ValueError("font code-table size mismatch")
    if code_table_offset != FONT_BITMAP_OFFSET + bitmap_bytes:
        raise ValueError("font code-table offset does not follow bitmap cells")
    if code_table_offset + code_table_bytes > len(payload):
        raise ValueError("font code table extends beyond payload")
    codes = struct.unpack_from(f"<{glyph_count}H", payload, code_table_offset)
    if len(set(codes)) != glyph_count:
        raise ValueError("font code table contains duplicates")
    if any(left >= right for left, right in zip(codes, codes[1:])):
        raise ValueError("font code table is not strictly sorted")
    palette = tuple(
        tuple(payload[0x20 + index * 4 : 0x24 + index * 4])
        for index in range(16)
    )
    layout = FontLayout(
        lpk_font_offset=entry.offset,
        lpk_font_size=entry.size,
        glyph_count=glyph_count,
        glyph_width=glyph_width,
        glyph_height=glyph_height,
        bitmap_offset=FONT_BITMAP_OFFSET,
        bitmap_bytes=bitmap_bytes,
        code_table_offset=code_table_offset,
        code_table_bytes=code_table_bytes,
        codes=tuple(codes),
        palette_rgba=palette,
    )
    return layout, payload


def read_ucs2jis(ucs2jis: bytes, codepoint: int) -> int:
    if len(ucs2jis) != UCS2JIS_SIZE:
        raise ValueError(f"unexpected ucs2jis size: {len(ucs2jis)}")
    if not 0 <= codepoint <= 0xFFFF:
        raise ValueError(f"code point does not fit the UCS-2 table: U+{codepoint:X}")
    return struct.unpack_from("<H", ucs2jis, codepoint * 2)[0]


def font_index_for_codepoint(
    codepoint: int, ucs2jis: bytes, code_to_index: dict[int, int]
) -> int | None:
    jis = read_ucs2jis(ucs2jis, codepoint)
    if not (0x2121 <= jis <= 0x7E7E):
        return None
    try:
        sjis = jis_to_shift_jis(jis)
    except ValueError:
        return None
    return code_to_index.get(sjis)


def unpack_cell_indexes(cell: bytes) -> list[int]:
    if len(cell) != FONT_CELL_BYTES:
        raise ValueError(f"cell must be {FONT_CELL_BYTES} bytes")
    indexes: list[int] = []
    for packed in cell:
        indexes.extend((packed >> 4, packed & 0x0F))
    return indexes[:FONT_CELL_PIXELS]


def pack_cell_indexes(indexes: Sequence[int]) -> bytes:
    if len(indexes) != FONT_CELL_PIXELS:
        raise ValueError(f"cell must contain {FONT_CELL_PIXELS} pixels")
    if any(not 0 <= value <= 15 for value in indexes):
        raise ValueError("palette index outside 0..15")
    padded = list(indexes)
    padded.append(0)
    return bytes(
        padded[index] << 4 | padded[index + 1]
        for index in range(0, len(padded), 2)
    )


def cell_bytes(payload: bytes, layout: FontLayout, font_index: int) -> bytes:
    if not 0 <= font_index < layout.glyph_count:
        raise IndexError(font_index)
    start = layout.bitmap_offset + font_index * FONT_CELL_BYTES
    return payload[start : start + FONT_CELL_BYTES]


def decoded_cell_image(
    cell: bytes, palette_rgba: Sequence[Sequence[int]]
) -> Image.Image:
    image = Image.new("RGBA", (FONT_CELL_WIDTH, FONT_CELL_HEIGHT))
    image.putdata([tuple(palette_rgba[index]) for index in unpack_cell_indexes(cell)])
    return image


def load_font(
    font_path: Path, font_size: int, font_index: int = 0
) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path), font_size, index=font_index)


def validate_font_coverage(
    font_path: Path, characters: Iterable[str], font_index: int = 0
) -> list[str]:
    if TTFont is None:
        return []
    kwargs: dict[str, Any] = {}
    if font_path.suffix.lower() in {".ttc", ".otc"}:
        kwargs["fontNumber"] = font_index
    font = TTFont(str(font_path), lazy=True, **kwargs)
    try:
        cmap = font.getBestCmap() or {}
        return sorted(character for character in characters if ord(character) not in cmap)
    finally:
        font.close()


def render_cell(
    character: str,
    font: ImageFont.FreeTypeFont,
    palette_alpha: Sequence[int],
    *,
    x_offset: int = 0,
    y_offset: int = 0,
) -> bytes:
    """Render and quantize one baseline-aligned glyph to the game's palette.

    `(1, -1)` is not an arbitrary aesthetic choice: it is the placement used
    by the PPSSPP-proven native Korean smoke patch.  Centering each bounding
    box independently makes syllables with different ink extents jump by one
    pixel even though they share the same font baseline.
    """
    bbox = font.getbbox(character)
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if width <= 0 or height <= 0:
        raise ValueError(f"font produced an empty glyph for {character!r}")
    x = 1 + x_offset
    y = -1 + y_offset
    translated_bbox = (
        x + bbox[0],
        y + bbox[1],
        x + bbox[2],
        y + bbox[3],
    )
    if (
        width > FONT_CELL_WIDTH
        or height > FONT_CELL_HEIGHT
        or translated_bbox[0] < 0
        or translated_bbox[1] < 0
        or translated_bbox[2] > FONT_CELL_WIDTH
        or translated_bbox[3] > FONT_CELL_HEIGHT
    ):
        raise ValueError(
            f"glyph {character!r} bbox {bbox} does not fit the "
            f"{FONT_CELL_WIDTH}x{FONT_CELL_HEIGHT} cell at origin "
            f"({x}, {y}); reduce --font-size or adjust offsets"
        )
    canvas = Image.new("L", (FONT_CELL_WIDTH, FONT_CELL_HEIGHT), 0)
    ImageDraw.Draw(canvas).text((x, y), character, font=font, fill=255)
    alphas = list(canvas.getdata())
    if not any(alphas):
        raise ValueError(f"font produced a blank raster for {character!r}")
    indexes = [
        min(
            range(16),
            key=lambda palette_index: (
                abs(palette_alpha[palette_index] - alpha),
                palette_index,
            ),
        )
        for alpha in alphas
    ]
    return pack_cell_indexes(indexes)


def iter_all_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_all_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_all_strings(child)


def iter_target_strings(
    value: Any,
    fields: set[str],
    *,
    include_all_strings: bool = False,
    top_level: bool = True,
    selected: bool = False,
) -> Iterator[str]:
    if isinstance(value, str):
        if include_all_strings or top_level or selected:
            yield value
        return
    if isinstance(value, list):
        for child in value:
            if isinstance(child, str):
                if include_all_strings or top_level or selected:
                    yield child
            else:
                yield from iter_target_strings(
                    child,
                    fields,
                    include_all_strings=include_all_strings,
                    top_level=False,
                    selected=selected,
                )
        return
    if not isinstance(value, dict):
        return
    if top_level and value and all(isinstance(child, str) for child in value.values()):
        yield from value.values()
        return
    for key, child in value.items():
        if isinstance(child, str):
            if include_all_strings or key in fields:
                yield child
        else:
            yield from iter_target_strings(
                child,
                fields,
                include_all_strings=include_all_strings,
                top_level=False,
                selected=key in fields,
            )


def expand_json_inputs(specifications: Sequence[str]) -> list[Path]:
    result: list[Path] = []
    for specification in specifications:
        path = Path(specification)
        if path.is_dir():
            result.extend(sorted(path.rglob("*.json")))
        elif path.is_file():
            result.append(path)
        else:
            matches = [Path(item) for item in glob.glob(specification, recursive=True)]
            result.extend(item for item in matches if item.is_file())
    unique: list[Path] = []
    seen: set[str] = set()
    for path in result:
        resolved = str(path.resolve()).casefold()
        if resolved not in seen:
            unique.append(path)
            seen.add(resolved)
    if not unique:
        raise ValueError("no translation JSON input files matched")
    return unique


def load_json_documents(paths: Sequence[Path]) -> list[tuple[Path, Any]]:
    documents: list[tuple[Path, Any]] = []
    for path in paths:
        documents.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return documents


def collect_closure(
    documents: Sequence[tuple[Path, Any]],
    target_fields: set[str],
    *,
    include_all_strings: bool = False,
) -> tuple[collections.Counter[str], set[int], int]:
    frequency: collections.Counter[str] = collections.Counter()
    reserved_codepoints: set[int] = set()
    target_string_count = 0
    for _path, document in documents:
        for text in iter_all_strings(document):
            reserved_codepoints.update(ord(character) for character in text if ord(character) <= 0xFFFF)
        for text in iter_target_strings(
            document, target_fields, include_all_strings=include_all_strings
        ):
            target_string_count += 1
            frequency.update(character for character in text if is_hangul(character))
    return frequency, reserved_codepoints, target_string_count


def alias_candidates(reserved: set[int]) -> Iterator[tuple[int, int]]:
    """Yield `(codepoint, UTF-8 byte length)`, compact aliases first."""
    compact_ranges = (
        range(0x0500, 0x0800),  # avoids BRS's U+0400 marker range
        range(0x0100, 0x0400),
        range(0x00A0, 0x0100),  # omit C1 control scalars
    )
    emitted: set[int] = set()
    for values in compact_ranges:
        for cp in values:
            if cp in emitted or cp in reserved:
                continue
            character = chr(cp)
            category = unicodedata.category(character)
            if unicodedata.combining(character) or category in {"Cc", "Cf", "Cs"}:
                continue
            emitted.add(cp)
            yield cp, 2
    for cp in range(0xE000, 0xF900):
        if cp not in reserved:
            yield cp, 3


def reserved_font_indexes(
    strings: Iterable[str], ucs2jis: bytes, layout: FontLayout
) -> set[int]:
    code_to_index = {code: index for index, code in enumerate(layout.codes)}
    indexes: set[int] = set()
    for text in strings:
        for character in text:
            index = font_index_for_codepoint(ord(character), ucs2jis, code_to_index)
            if index is not None:
                indexes.add(index)
    return indexes


def build_alias_font(
    font_lpk: bytes,
    ucs2jis: bytes,
    frequency: collections.Counter[str],
    *,
    font_path: Path,
    font_size: int = 14,
    font_index: int = 0,
    reserved_alias_codepoints: set[int] | None = None,
    preserved_font_indexes: set[int] | None = None,
    min_slot_sjis: int = KANJI_SLOT_MIN_SJIS,
    x_offset: int = 0,
    y_offset: int = 0,
) -> tuple[bytes, bytes, list[GlyphAlias], dict[str, Any]]:
    if len(ucs2jis) != UCS2JIS_SIZE:
        raise ValueError(f"unexpected ucs2jis size: {len(ucs2jis)}")
    layout, payload_bytes = parse_font_layout(font_lpk)
    missing = validate_font_coverage(font_path, frequency, font_index)
    if missing:
        display = " ".join(f"U+{ord(character):04X}" for character in missing[:20])
        raise ValueError(f"font lacks {len(missing)} required glyphs: {display}")
    preserved = set(preserved_font_indexes or ())
    slots = [
        (index, code)
        for index, code in enumerate(layout.codes)
        if code >= min_slot_sjis and index not in preserved
    ]
    # Frequent syllables receive compact aliases, with codepoint as stable tie-break.
    characters = sorted(frequency, key=lambda character: (-frequency[character], ord(character)))
    if len(characters) > len(slots):
        raise ValueError(
            f"Hangul closure has {len(characters)} glyphs but only "
            f"{len(slots)} reusable cells"
        )
    candidate_pool = list(alias_candidates(set(reserved_alias_codepoints or ())))
    if len(characters) > len(candidate_pool):
        raise ValueError(
            f"Hangul closure has {len(characters)} glyphs but only "
            f"{len(candidate_pool)} safe BMP aliases"
        )
    aliases = candidate_pool[: len(characters)]
    font = load_font(font_path, font_size, font_index)
    patched_payload = bytearray(payload_bytes)
    patched_ucs2jis = bytearray(ucs2jis)
    records: list[GlyphAlias] = []
    for character, (slot_index, sjis), (alias_cp, alias_bytes) in zip(
        characters, slots, aliases
    ):
        jis = shift_jis_to_jis(sjis)
        original_mapping = read_ucs2jis(ucs2jis, alias_cp)
        struct.pack_into("<H", patched_ucs2jis, alias_cp * 2, jis)
        original_cell = cell_bytes(payload_bytes, layout, slot_index)
        patched_cell = render_cell(
            character,
            font,
            layout.palette_alpha,
            x_offset=x_offset,
            y_offset=y_offset,
        )
        start = layout.bitmap_offset + slot_index * FONT_CELL_BYTES
        patched_payload[start : start + FONT_CELL_BYTES] = patched_cell
        records.append(
            GlyphAlias(
                character=character,
                unicode_codepoint=ord(character),
                frequency=frequency[character],
                alias_character=chr(alias_cp),
                alias_codepoint=alias_cp,
                alias_utf8_hex=chr(alias_cp).encode("utf-8").hex(),
                alias_utf8_bytes=alias_bytes,
                font_index=slot_index,
                shift_jis_code=sjis,
                jis_code=jis,
                original_ucs2jis=original_mapping,
                original_cell_sha256=sha256_bytes(original_cell),
                patched_cell_sha256=sha256_bytes(patched_cell),
            )
        )
    patched_lpk = bytearray(font_lpk)
    start = layout.lpk_font_offset
    patched_lpk[start : start + len(patched_payload)] = patched_payload
    stats = {
        "glyph_count": len(records),
        "available_slot_count": len(slots),
        "preserved_font_index_count": len(preserved),
        "compact_alias_count": sum(record.alias_utf8_bytes == 2 for record in records),
        "pua_alias_count": sum(record.alias_utf8_bytes == 3 for record in records),
        "compact_alias_capacity": sum(
            byte_length == 2 for _codepoint, byte_length in candidate_pool
        ),
        "safe_bmp_alias_capacity": len(candidate_pool),
        "weighted_original_hangul_bytes": sum(
            record.frequency * len(record.character.encode("utf-8"))
            for record in records
        ),
        "weighted_alias_bytes": sum(
            record.frequency * record.alias_utf8_bytes for record in records
        ),
    }
    stats["weighted_bytes_saved"] = (
        stats["weighted_original_hangul_bytes"] - stats["weighted_alias_bytes"]
    )
    return bytes(patched_lpk), bytes(patched_ucs2jis), records, stats


def mapping_lookup(records: Sequence[GlyphAlias] | Sequence[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for record in records:
        if isinstance(record, GlyphAlias):
            result[record.character] = record.alias_character
        else:
            alias = record.get("alias_character")
            if not alias:
                alias = chr(record["alias_codepoint"])
            result[record["character"]] = alias
    return result


def encode_text(text: str, character_to_alias: dict[str, str]) -> str:
    missing = sorted(
        {
            character
            for character in text
            if is_hangul(character) and character not in character_to_alias
        },
        key=ord,
    )
    if missing:
        display = " ".join(f"{character}(U+{ord(character):04X})" for character in missing)
        raise ValueError(f"Hangul glyphs absent from alias map: {display}")
    return "".join(character_to_alias.get(character, character) for character in text)


def decode_text(text: str, character_to_alias: dict[str, str]) -> str:
    alias_to_character = {alias: character for character, alias in character_to_alias.items()}
    return "".join(alias_to_character.get(character, character) for character in text)


def transform_json_fields(
    value: Any,
    fields: set[str],
    mapping: dict[str, str],
    *,
    decode: bool = False,
    include_all_strings: bool = False,
    top_level: bool = True,
    selected: bool = False,
) -> Any:
    transform = decode_text if decode else encode_text
    if isinstance(value, str):
        if include_all_strings or top_level or selected:
            return transform(value, mapping)
        return value
    if isinstance(value, list):
        output_list: list[Any] = []
        for child in value:
            if isinstance(child, str):
                output_list.append(
                    transform(child, mapping)
                    if include_all_strings or top_level or selected
                    else child
                )
            else:
                output_list.append(
                    transform_json_fields(
                        child,
                        fields,
                        mapping,
                        decode=decode,
                        include_all_strings=include_all_strings,
                        top_level=False,
                        selected=selected,
                    )
                )
        return output_list
    if not isinstance(value, dict):
        return value
    string_map = top_level and value and all(
        isinstance(child, str) for child in value.values()
    )
    output: dict[str, Any] = {}
    for key, child in value.items():
        if isinstance(child, str):
            output[key] = (
                transform(child, mapping)
                if include_all_strings or string_map or key in fields
                else child
            )
        else:
            output[key] = transform_json_fields(
                child,
                fields,
                mapping,
                decode=decode,
                include_all_strings=include_all_strings,
                top_level=False,
                selected=key in fields,
            )
    return output


def write_actual_preview(
    destination: Path,
    patched_lpk: bytes,
    records: Sequence[GlyphAlias],
    *,
    columns: int = 24,
    scale: int = 4,
) -> None:
    layout, payload = parse_font_layout(patched_lpk)
    rows = max(1, math.ceil(len(records) / columns))
    background = (22, 22, 26, 255)
    image = Image.new(
        "RGBA",
        (columns * FONT_CELL_WIDTH * scale, rows * FONT_CELL_HEIGHT * scale),
        background,
    )
    for position, record in enumerate(records):
        cell = cell_bytes(payload, layout, record.font_index)
        glyph = decoded_cell_image(cell, layout.palette_rgba)
        glyph = glyph.resize(
            (FONT_CELL_WIDTH * scale, FONT_CELL_HEIGHT * scale),
            Image.Resampling.NEAREST,
        )
        x = position % columns * FONT_CELL_WIDTH * scale
        y = position // columns * FONT_CELL_HEIGHT * scale
        image.alpha_composite(glyph, (x, y))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


def mapping_json_payload(
    records: Sequence[GlyphAlias],
    *,
    font_path: Path,
    font_size: int,
    font_index: int,
    inputs: Sequence[Path],
    original_font_lpk: bytes,
    original_ucs2jis: bytes,
    patched_font_lpk: bytes,
    patched_ucs2jis: bytes,
    stats: dict[str, Any],
    target_fields: set[str],
) -> dict[str, Any]:
    return {
        "schema": "brs-korean-glyph-alias-v2",
        "strategy": "BMP UTF-8 alias -> ucs2jis JIS -> Shift-JIS font cell",
        "font": {
            "path": str(font_path),
            "size": font_size,
            "index": font_index,
        },
        "target_fields": sorted(target_fields),
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)} for path in inputs
        ],
        "hashes": {
            "original_font_lpk": sha256_bytes(original_font_lpk),
            "original_ucs2jis": sha256_bytes(original_ucs2jis),
            "patched_font_lpk": sha256_bytes(patched_font_lpk),
            "patched_ucs2jis": sha256_bytes(patched_ucs2jis),
        },
        "stats": stats,
        "aliases": [dataclasses.asdict(record) for record in records],
    }


def verify_build(
    original_font_lpk: bytes,
    original_ucs2jis: bytes,
    patched_font_lpk: bytes,
    patched_ucs2jis: bytes,
    mapping: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    if len(original_font_lpk) != len(patched_font_lpk):
        errors.append("font.lpk size changed")
    if len(original_ucs2jis) != len(patched_ucs2jis):
        errors.append("ucs2jis.bin size changed")
    original_layout, original_payload = parse_font_layout(original_font_lpk)
    patched_layout, patched_payload = parse_font_layout(patched_font_lpk)
    if original_layout.codes != patched_layout.codes:
        errors.append("Shift-JIS font code table changed")
    if original_layout.palette_rgba != patched_layout.palette_rgba:
        errors.append("font palette changed")
    records = mapping["aliases"]
    alias_codepoints: set[int] = set()
    font_indexes: set[int] = set()
    allowed_font_offsets: set[int] = set()
    allowed_ucs_offsets: set[int] = set()
    for record in records:
        alias_cp = int(record["alias_codepoint"])
        font_index = int(record["font_index"])
        if alias_cp in alias_codepoints:
            errors.append(f"duplicate alias code point U+{alias_cp:04X}")
        if font_index in font_indexes:
            errors.append(f"duplicate font index {font_index}")
        alias_codepoints.add(alias_cp)
        font_indexes.add(font_index)
        try:
            mapped_jis = read_ucs2jis(patched_ucs2jis, alias_cp)
            if mapped_jis != int(record["jis_code"]):
                errors.append(f"alias U+{alias_cp:04X} has wrong JIS mapping")
            if jis_to_shift_jis(mapped_jis) != int(record["shift_jis_code"]):
                errors.append(f"alias U+{alias_cp:04X} does not reach its font cell")
            if patched_layout.codes[font_index] != int(record["shift_jis_code"]):
                errors.append(f"font index {font_index} code-table mismatch")
        except (ValueError, IndexError) as error:
            errors.append(str(error))
        original_cell = cell_bytes(original_payload, original_layout, font_index)
        patched_cell = cell_bytes(patched_payload, patched_layout, font_index)
        if sha256_bytes(original_cell) != record["original_cell_sha256"]:
            errors.append(f"font index {font_index} original-cell hash mismatch")
        if sha256_bytes(patched_cell) != record["patched_cell_sha256"]:
            errors.append(f"font index {font_index} patched-cell hash mismatch")
        if not any(patched_layout.palette_alpha[index] for index in unpack_cell_indexes(patched_cell)):
            errors.append(f"font index {font_index} is blank")
        global_start = (
            patched_layout.lpk_font_offset
            + patched_layout.bitmap_offset
            + font_index * FONT_CELL_BYTES
        )
        allowed_font_offsets.update(range(global_start, global_start + FONT_CELL_BYTES))
        allowed_ucs_offsets.update((alias_cp * 2, alias_cp * 2 + 1))
    font_diffs = {
        index
        for index, (before, after) in enumerate(
            zip(original_font_lpk, patched_font_lpk)
        )
        if before != after
    }
    ucs_diffs = {
        index
        for index, (before, after) in enumerate(
            zip(original_ucs2jis, patched_ucs2jis)
        )
        if before != after
    }
    unexpected_font = font_diffs - allowed_font_offsets
    unexpected_ucs = ucs_diffs - allowed_ucs_offsets
    if unexpected_font:
        errors.append(
            f"{len(unexpected_font)} font.lpk bytes changed outside selected cells"
        )
    if unexpected_ucs:
        errors.append(
            f"{len(unexpected_ucs)} ucs2jis bytes changed outside selected aliases"
        )
    character_to_alias = mapping_lookup(records)
    probe = "".join(record["character"] for record in records)
    if decode_text(encode_text(probe, character_to_alias), character_to_alias) != probe:
        errors.append("text alias round-trip failed")
    expected_hashes = mapping.get("hashes", {})
    actual_hashes = {
        "original_font_lpk": sha256_bytes(original_font_lpk),
        "original_ucs2jis": sha256_bytes(original_ucs2jis),
        "patched_font_lpk": sha256_bytes(patched_font_lpk),
        "patched_ucs2jis": sha256_bytes(patched_ucs2jis),
    }
    for key, expected in expected_hashes.items():
        if key in actual_hashes and expected != actual_hashes[key]:
            errors.append(f"{key} hash mismatch")
    return {
        "schema": "brs-font-verification-v1",
        "ok": not errors,
        "errors": errors,
        "glyph_count": len(records),
        "font_changed_byte_count": len(font_diffs),
        "ucs2jis_changed_byte_count": len(ucs_diffs),
        "unexpected_font_byte_count": len(unexpected_font),
        "unexpected_ucs2jis_byte_count": len(unexpected_ucs),
        "hashes": actual_hashes,
    }


def inspect_assets(font_lpk: bytes, ucs2jis: bytes) -> dict[str, Any]:
    layout, _payload = parse_font_layout(font_lpk)
    _count, flags, entries = parse_lpk(font_lpk)
    known_mappings = {
        f"U+{cp:04X}": f"0x{read_ucs2jis(ucs2jis, cp):04X}"
        for cp in (0x0041, 0x3042, 0x30A2, 0x4E00, 0xAC00)
    }
    return {
        "schema": "brs-font-inspection-v1",
        "font_lpk_size": len(font_lpk),
        "font_lpk_sha256": sha256_bytes(font_lpk),
        "lpk_flags": flags,
        "entries": [dataclasses.asdict(entry) for entry in entries],
        "font_layout": {
            **{
                key: value
                for key, value in dataclasses.asdict(layout).items()
                if key not in {"codes", "palette_rgba"}
            },
            "first_shift_jis": f"0x{layout.codes[0]:04X}",
            "last_shift_jis": f"0x{layout.codes[-1]:04X}",
            "kanji_slot_count": sum(
                code >= KANJI_SLOT_MIN_SJIS for code in layout.codes
            ),
            "palette_rgba": layout.palette_rgba,
        },
        "ucs2jis_size": len(ucs2jis),
        "ucs2jis_sha256": sha256_bytes(ucs2jis),
        "known_mappings": known_mappings,
    }


def read_mapping(path: Path) -> dict[str, Any]:
    mapping = json.loads(path.read_text(encoding="utf-8"))
    if mapping.get("schema") != "brs-korean-glyph-alias-v2":
        raise ValueError(f"unsupported alias-map schema: {mapping.get('schema')!r}")
    return mapping


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def command_inspect(args: argparse.Namespace) -> int:
    report = inspect_assets(args.font_lpk.read_bytes(), args.ucs2jis.read_bytes())
    if args.output:
        write_json(args.output, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def command_build(args: argparse.Namespace) -> int:
    input_paths = expand_json_inputs(args.input)
    documents = load_json_documents(input_paths)
    fields = {field.strip() for field in args.fields.split(",") if field.strip()}
    frequency, reserved_codepoints, target_string_count = collect_closure(
        documents, fields, include_all_strings=args.all_strings
    )
    if not frequency:
        raise ValueError("selected translation fields contain no Hangul")
    original_font_lpk = args.font_lpk.read_bytes()
    original_ucs2jis = args.ucs2jis.read_bytes()
    layout, _payload = parse_font_layout(original_font_lpk)
    all_strings = (
        text
        for _path, document in documents
        for text in iter_all_strings(document)
    )
    preserve_indexes = reserved_font_indexes(
        all_strings, original_ucs2jis, layout
    )
    patched_font_lpk, patched_ucs2jis, records, stats = build_alias_font(
        original_font_lpk,
        original_ucs2jis,
        frequency,
        font_path=args.font,
        font_size=args.font_size,
        font_index=args.font_index,
        reserved_alias_codepoints=reserved_codepoints,
        preserved_font_indexes=preserve_indexes,
        min_slot_sjis=args.min_slot_sjis,
        x_offset=args.x_offset,
        y_offset=args.y_offset,
    )
    stats["target_string_count"] = target_string_count
    stats["input_file_count"] = len(input_paths)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    output_font = out_dir / "font.lpk"
    output_ucs = out_dir / "ucs2jis.bin"
    output_mapping = out_dir / "glyph_alias_map.json"
    output_preview = out_dir / "glyph_preview.png"
    output_verification = out_dir / "verification.json"
    output_closure = out_dir / "glyph_closure.txt"
    output_font.write_bytes(patched_font_lpk)
    output_ucs.write_bytes(patched_ucs2jis)
    mapping = mapping_json_payload(
        records,
        font_path=args.font,
        font_size=args.font_size,
        font_index=args.font_index,
        inputs=input_paths,
        original_font_lpk=original_font_lpk,
        original_ucs2jis=original_ucs2jis,
        patched_font_lpk=patched_font_lpk,
        patched_ucs2jis=patched_ucs2jis,
        stats=stats,
        target_fields=fields,
    )
    write_json(output_mapping, mapping)
    output_closure.write_text(
        "\n".join(
            f"{record.character}\tU+{record.unicode_codepoint:04X}\t"
            f"{record.frequency}\tU+{record.alias_codepoint:04X}\t"
            f"{record.alias_utf8_hex}\t{record.font_index}\t"
            f"0x{record.shift_jis_code:04X}"
            for record in records
        )
        + "\n",
        encoding="utf-8",
    )
    write_actual_preview(
        output_preview,
        patched_font_lpk,
        records,
        columns=args.preview_columns,
        scale=args.preview_scale,
    )
    verification = verify_build(
        original_font_lpk,
        original_ucs2jis,
        patched_font_lpk,
        patched_ucs2jis,
        mapping,
    )
    write_json(output_verification, verification)
    if not verification["ok"]:
        raise ValueError("verification failed: " + "; ".join(verification["errors"]))
    print(
        f"built {len(records)} glyphs: "
        f"{stats['compact_alias_count']} compact + {stats['pua_alias_count']} PUA; "
        f"saved {stats['weighted_bytes_saved']} weighted UTF-8 bytes"
    )
    return 0


def command_verify(args: argparse.Namespace) -> int:
    report = verify_build(
        args.original_font_lpk.read_bytes(),
        args.original_ucs2jis.read_bytes(),
        args.patched_font_lpk.read_bytes(),
        args.patched_ucs2jis.read_bytes(),
        read_mapping(args.mapping),
    )
    if args.output:
        write_json(args.output, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def command_transform_json(args: argparse.Namespace, *, decode: bool) -> int:
    mapping_payload = read_mapping(args.mapping)
    lookup = mapping_lookup(mapping_payload["aliases"])
    fields = {field.strip() for field in args.fields.split(",") if field.strip()}
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    transformed = transform_json_fields(
        payload,
        fields,
        lookup,
        decode=decode,
        include_all_strings=args.all_strings,
    )
    write_json(args.output, transformed)
    # Prove exact semantic round trip immediately.
    round_tripped = transform_json_fields(
        transformed,
        fields,
        lookup,
        decode=not decode,
        include_all_strings=args.all_strings,
    )
    if round_tripped != payload:
        raise ValueError("JSON alias semantic round-trip failed")
    print(f"{'decoded' if decode else 'encoded'} {args.input} -> {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="inspect original assets")
    inspect_parser.add_argument("--font-lpk", type=Path, required=True)
    inspect_parser.add_argument("--ucs2jis", type=Path, required=True)
    inspect_parser.add_argument("--output", type=Path)
    inspect_parser.set_defaults(handler=command_inspect)

    build_parser_ = subparsers.add_parser("build", help="build patched font assets")
    build_parser_.add_argument("--font-lpk", type=Path, required=True)
    build_parser_.add_argument("--ucs2jis", type=Path, required=True)
    build_parser_.add_argument(
        "--input",
        action="append",
        required=True,
        help="translation JSON file, directory, or glob; repeatable",
    )
    build_parser_.add_argument(
        "--fields", default=",".join(DEFAULT_TARGET_FIELDS)
    )
    build_parser_.add_argument("--all-strings", action="store_true")
    build_parser_.add_argument("--font", type=Path, required=True)
    build_parser_.add_argument("--font-size", type=int, default=14)
    build_parser_.add_argument("--font-index", type=int, default=0)
    build_parser_.add_argument(
        "--min-slot-sjis", type=parse_int, default=KANJI_SLOT_MIN_SJIS
    )
    build_parser_.add_argument("--x-offset", type=int, default=0)
    build_parser_.add_argument("--y-offset", type=int, default=0)
    build_parser_.add_argument("--out-dir", type=Path, required=True)
    build_parser_.add_argument("--preview-columns", type=int, default=24)
    build_parser_.add_argument("--preview-scale", type=int, default=4)
    build_parser_.set_defaults(handler=command_build)

    verify_parser = subparsers.add_parser("verify", help="verify a built font patch")
    verify_parser.add_argument("--original-font-lpk", type=Path, required=True)
    verify_parser.add_argument("--original-ucs2jis", type=Path, required=True)
    verify_parser.add_argument("--patched-font-lpk", type=Path, required=True)
    verify_parser.add_argument("--patched-ucs2jis", type=Path, required=True)
    verify_parser.add_argument("--mapping", type=Path, required=True)
    verify_parser.add_argument("--output", type=Path)
    verify_parser.set_defaults(handler=command_verify)

    for name, decode in (("encode-json", False), ("decode-json", True)):
        transform_parser = subparsers.add_parser(name)
        transform_parser.add_argument("--mapping", type=Path, required=True)
        transform_parser.add_argument("--input", type=Path, required=True)
        transform_parser.add_argument("--output", type=Path, required=True)
        transform_parser.add_argument(
            "--fields", default=",".join(DEFAULT_TARGET_FIELDS)
        )
        transform_parser.add_argument("--all-strings", action="store_true")
        transform_parser.set_defaults(
            handler=lambda args, decode=decode: command_transform_json(
                args, decode=decode
            )
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
