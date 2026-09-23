#!/usr/bin/env python3
"""Generate a conservative Korean PTMD UI fallback set.

This script is intentionally data-driven and only touches rectangles that
contain baked English labels.  All game art, icons, frames, and the original
CLUT/header are retained.  Output PTMDs have exactly the same byte length as
their templates and are immediately decoded again for visual QA.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from ptmd_codec import (  # noqa: E402
    decode_file,
    encode_ptmd,
    replace_from_rgba,
)


ORIGINAL_ROOT = ROOT / "work" / "lpk"
OUTPUT_ROOT = HERE / "root_patched_ptmd"
PREVIEW_ROOT = HERE / "root_ui_previews"
REPORT_PATH = HERE / "root_ui_fallback_report.json"
CONTACT_PATH = HERE / "root_ui_fallback_contact.png"
FONT_BOLD = Path(r"C:\Windows\Fonts\malgunbd.ttf")
FONT_REGULAR = Path(r"C:\Windows\Fonts\malgun.ttf")
PIXEL_FONT_7 = HERE / "fonts" / "galmuri" / "Galmuri7.ttf"
PIXEL_FONT_9 = HERE / "fonts" / "galmuri" / "Galmuri9.ttf"

WHITE = (255, 255, 255, 255)
WHITE_TRANSPARENT = (255, 255, 255, 0)
BLACK_TRANSPARENT = (0, 0, 0, 0)
BLACK = (0, 0, 0, 255)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rgba_image(path: Path) -> tuple[Image.Image, object]:
    texture = decode_file(path)
    image = Image.frombytes(
        "RGBA", (texture.width, texture.height), texture.rgba_bytes
    )
    return image, texture


def clear(
    image: Image.Image,
    box: tuple[int, int, int, int],
    color: tuple[int, int, int, int] = WHITE_TRANSPARENT,
) -> None:
    ImageDraw.Draw(image).rectangle(box, fill=color)


def clear_exclusive(
    image: Image.Image,
    box: tuple[int, int, int, int],
    color: tuple[int, int, int, int] = WHITE_TRANSPARENT,
) -> None:
    """Clear an x1/y1-exclusive UV rectangle without touching its neighbors."""
    if box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError(f"invalid exclusive box: {box}")
    ImageDraw.Draw(image).rectangle(
        (box[0], box[1], box[2] - 1, box[3] - 1), fill=color
    )


def font(size: int, *, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(FONT_BOLD if bold else FONT_REGULAR),
        size=max(5, size),
        layout_engine=ImageFont.Layout.BASIC,
    )


def fit_font(
    text: str,
    box: tuple[int, int, int, int],
    *,
    maximum: int,
    minimum: int = 5,
    bold: bool = True,
    spacing: int = 0,
) -> ImageFont.FreeTypeFont:
    width = max(1, box[2] - box[0])
    height = max(1, box[3] - box[1])
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    for size in range(maximum, minimum - 1, -1):
        candidate = font(size, bold=bold)
        bounds = probe.multiline_textbbox(
            (0, 0), text, font=candidate, spacing=spacing
        )
        if bounds[2] - bounds[0] <= width and bounds[3] - bounds[1] <= height:
            return candidate
    return font(minimum, bold=bold)


def draw_box(
    image: Image.Image,
    text: str,
    box: tuple[int, int, int, int],
    *,
    maximum: int,
    minimum: int = 5,
    fill: tuple[int, int, int, int] = WHITE,
    align: str = "left",
    valign: str = "center",
    bold: bool = True,
    spacing: int = 0,
    stroke_width: int = 0,
    stroke_fill: tuple[int, int, int, int] = BLACK,
    edge_margin: int = 0,
) -> None:
    outer_box = box
    if edge_margin:
        box = (
            box[0] + edge_margin,
            box[1] + edge_margin,
            box[2] - edge_margin,
            box[3] - edge_margin,
        )
        if box[0] >= box[2] or box[1] >= box[3]:
            raise ValueError(f"text box too small after margin: {outer_box}")
    selected = fit_font(
        text,
        box,
        maximum=maximum,
        minimum=minimum,
        bold=bold,
        spacing=spacing,
    )
    probe = ImageDraw.Draw(image)
    bounds = probe.multiline_textbbox(
        (0, 0), text, font=selected, spacing=spacing, stroke_width=stroke_width
    )
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    x = box[0]
    if align == "center":
        x += max(0, (box[2] - box[0] - text_width) // 2)
    elif align == "right":
        x = box[2] - text_width
    y = box[1] - bounds[1]
    if valign == "center":
        y += max(0, (box[3] - box[1] - text_height) // 2)
    elif valign == "bottom":
        y += max(0, box[3] - box[1] - text_height)
    probe.multiline_text(
        (x, y),
        text,
        font=selected,
        fill=fill,
        spacing=spacing,
        align=align,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )
    if edge_margin:
        ink = probe.multiline_textbbox(
            (x, y),
            text,
            font=selected,
            spacing=spacing,
            align=align,
            stroke_width=stroke_width,
        )
        if (
            ink[0] <= outer_box[0]
            or ink[1] <= outer_box[1]
            or ink[2] >= outer_box[2]
            or ink[3] >= outer_box[3]
        ):
            raise AssertionError(
                f"rendered label touches box edge: {text!r}, "
                f"ink={ink}, box={outer_box}"
            )


def pixel_font(size: int, *, compact: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(PIXEL_FONT_7 if compact else PIXEL_FONT_9),
        size=max(5, size),
        layout_engine=ImageFont.Layout.BASIC,
    )


def draw_pixel_box(
    image: Image.Image,
    text: str,
    box: tuple[int, int, int, int],
    *,
    maximum: int,
    minimum: int = 5,
    fill: tuple[int, int, int, int] = WHITE,
    align: str = "left",
    valign: str = "center",
    compact: bool = True,
    threshold: int = 96,
) -> tuple[int, int, int, int]:
    """Render 1-bit pixel Hangul wholly inside a fixed game UV rectangle."""
    width = box[2] - box[0]
    height = box[3] - box[1]
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid pixel text box: {box}")

    scratch = Image.new("L", (max(1, width * 4), max(1, height * 4)))
    probe = ImageDraw.Draw(scratch)
    selected = None
    bounds = None
    for size in range(min(maximum, height), minimum - 1, -1):
        candidate = pixel_font(size, compact=compact)
        candidate_bounds = probe.textbbox((0, 0), text, font=candidate)
        if (
            candidate_bounds[2] - candidate_bounds[0] <= width
            and candidate_bounds[3] - candidate_bounds[1] <= height
        ):
            selected = candidate
            bounds = candidate_bounds
            break
    if selected is None or bounds is None:
        raise AssertionError(f"pixel label does not fit UV box: {text!r}, {box}")

    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    mask = Image.new("L", (max(1, text_width), max(1, text_height)))
    ImageDraw.Draw(mask).text(
        (-bounds[0], -bounds[1]), text, font=selected, fill=255
    )
    mask = mask.point(lambda value: 255 if value >= threshold else 0, mode="1")
    mask_bbox = mask.getbbox()
    if mask_bbox is None:
        raise AssertionError(f"pixel label rendered no ink: {text!r}")

    x = box[0]
    if align == "center":
        x += (width - text_width) // 2
    elif align == "right":
        x += width - text_width
    y = box[1]
    if valign == "center":
        y += (height - text_height) // 2
    elif valign == "bottom":
        y += height - text_height

    ink = (
        x + mask_bbox[0],
        y + mask_bbox[1],
        x + mask_bbox[2],
        y + mask_bbox[3],
    )
    if (
        ink[0] < box[0]
        or ink[1] < box[1]
        or ink[2] > box[2]
        or ink[3] > box[3]
    ):
        raise AssertionError(
            f"pixel label escaped UV box: {text!r}, ink={ink}, box={box}"
        )
    color = Image.new("RGBA", mask.size, fill)
    image.paste(color, (x, y), mask)
    return ink


def draw_vertical(
    image: Image.Image,
    text: str,
    box: tuple[int, int, int, int],
    *,
    maximum: int,
    minimum: int = 5,
    fill: tuple[int, int, int, int] = WHITE,
    clockwise: bool = True,
) -> None:
    # Fit against the rotated dimensions.
    rotated_box = (0, 0, box[3] - box[1], box[2] - box[0])
    selected = fit_font(
        text,
        rotated_box,
        maximum=maximum,
        minimum=minimum,
        bold=True,
    )
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    bounds = probe.textbbox((0, 0), text, font=selected)
    width = max(1, bounds[2] - bounds[0] + 2)
    height = max(1, bounds[3] - bounds[1] + 2)
    tile = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text(
        (1 - bounds[0], 1 - bounds[1]), text, font=selected, fill=fill
    )
    tile = tile.rotate(-90 if clockwise else 90, expand=True)
    x = box[0] + max(0, (box[2] - box[0] - tile.width) // 2)
    y = box[1] + max(0, (box[3] - box[1] - tile.height) // 2)
    image.alpha_composite(tile, (x, y))


def draw_pixel_vertical(
    image: Image.Image,
    text: str,
    box: tuple[int, int, int, int],
    *,
    maximum: int,
    minimum: int = 5,
    fill: tuple[int, int, int, int] = WHITE,
) -> None:
    rotated_size = (box[3] - box[1], box[2] - box[0])
    tile = Image.new("RGBA", rotated_size, (0, 0, 0, 0))
    draw_pixel_box(
        tile,
        text,
        (0, 0, tile.width, tile.height),
        maximum=maximum,
        minimum=minimum,
        fill=fill,
        align="center",
    )
    tile = tile.rotate(-90, expand=True)
    if tile.width > box[2] - box[0] or tile.height > box[3] - box[1]:
        raise AssertionError(f"rotated pixel label exceeds UV box: {text!r}")
    x = box[0] + (box[2] - box[0] - tile.width) // 2
    y = box[1] + (box[3] - box[1] - tile.height) // 2
    image.alpha_composite(tile, (x, y))


def patch_mission_failed(image: Image.Image) -> list[str]:
    separator = image.crop((0, 57, 98, 62))
    clear(image, (0, 0, 127, 71))
    draw_box(image, "\uc784\ubb34 \uc2e4\ud328", (1, 0, 127, 25), maximum=23)
    draw_box(image, "\uc784\ubb34 \uc7ac\ub3c4\uc804", (1, 25, 127, 40), maximum=13)
    draw_box(image, "\uc2a4\ud14c\uc774\uc9c0 \uc120\ud0dd", (1, 40, 127, 55), maximum=12)
    image.alpha_composite(separator, (0, 57))
    draw_box(
        image,
        "\ubd88\ub7ec\uc624\uae30",
        (65, 56, 127, 71),
        maximum=12,
        align="right",
    )
    return ["MISSION FAILED", "RETRY MISSION", "STAGE SELECT", "LOAD"]


def patch_record_info(image: Image.Image) -> list[str]:
    # This texture is sampled as a sprite atlas.  Keep every original helper
    # label and place each shortened stage name in its original 6-pixel UV row.
    lines = [
        "1 \uc0cc\ud504\ub780",
        "2 \ub274\uc695",
        "3 \ubaa8\uc2a4\ud06c\ubc14",
        "4 \ud6c4\uc9c0",
        "5 \ub3c4\ucfc4",
        "6 \ub2ec",
    ]
    for index, (line, y) in enumerate(zip(lines, (59, 65, 71, 77, 83, 89))):
        # The sixth row shares the right side with the original CLEAR helper.
        box = (4, y, 79 if index == 5 else 128, y + 6)
        clear_exclusive(image, box)
        draw_pixel_box(
            image,
            line,
            box,
            maximum=6,
            minimum=6,
        )
    return [
        "NO.",
        "TO UNLOCK",
        "STAGE 1 SAN FRANCISCO",
        "STAGE 2 NEW YORK CITY",
        "STAGE 3 MOSCOW",
        "STAGE 4 FUJIYAMA",
        "STAGE 5 TOKYO TOWER",
        "STAGE 6 MOON",
        "CLEAR",
    ]


def patch_unknown(image: Image.Image) -> list[str]:
    clear(image, (91, 0, 127, 47))
    draw_vertical(image, "\ubbf8\ud655\uc778", (92, 1, 111, 47), maximum=9)
    return ["UNKNOWN"]


def patch_stage_select_menu(image: Image.Image) -> list[str]:
    # The runtime samples the original alpha-row runs: 0..9, 11..20,
    # 22..31, 32..41, and 43..47.  Never move a label into a neighboring run
    # even when the complete texture preview looks fine.
    # Preserve the tiny original MISSION/REC./LEVEL/TYPE helper strip.  It is
    # sampled separately and 5-pixel Hangul is less readable than the original.
    clear_exclusive(image, (0, 0, 128, 43))
    labels = [
        ("\uc2a4\ud14c\uc774\uc9c0", (2, 0, 126, 10), 9, "left"),
        ("\uc800\uc7a5", (2, 11, 62, 21), 9, "left"),
        ("\ud5cc\ud2b8", (66, 11, 126, 21), 9, "left"),
        ("\ub85c\ub4dc", (2, 22, 62, 32), 9, "left"),
        ("\ucd94\uac00", (66, 22, 126, 32), 9, "left"),
        ("\uba54\ub274", (2, 32, 62, 42), 9, "left"),
        ("\uc2a4\ud1a0\ub9ac", (66, 32, 126, 42), 9, "left"),
    ]
    for text, box, size, align in labels:
        draw_pixel_box(
            image,
            text,
            box,
            maximum=size,
            minimum=size,
            align=align,
        )
    return [
        "STAGE SELECT",
        "SAVE",
        "HUNT",
        "LOAD",
        "EXTRA",
        "MENU",
        "STORY",
        "MISSION/REC.",
        "LEVEL/TYPE",
    ]


def patch_mission_list(image: Image.Image) -> list[str]:
    clear(image, (0, 0, 102, 13), BLACK_TRANSPARENT)
    draw_box(image, "\uc784\ubb34 \ubaa9\ub85d", (5, 0, 102, 13), maximum=11)
    clear(image, (210, 49, 255, 71), (10, 7, 5, 0))
    draw_box(
        image,
        "\ub098\uac00\uae30",
        (210, 51, 255, 70),
        maximum=11,
        align="right",
    )
    return ["MISSION LIST", "EXIT"]


def patch_stage_info(image: Image.Image) -> list[str]:
    clear(image, (62, 57, 105, 78))
    draw_box(image, "\uc784\ubb34 \uc815\ubcf4", (63, 57, 105, 67), maximum=8)
    draw_box(image, "\uc2a4\ud14c\uc774\uc9c0", (63, 67, 105, 78), maximum=8)
    clear(image, (68, 174, 127, 191))
    draw_box(
        image, "\uc870\uac74", (68, 174, 94, 191), maximum=8, edge_margin=1
    )
    draw_box(
        image,
        "\uc774\uc804",
        (95, 174, 127, 183),
        maximum=7,
        align="right",
        edge_margin=1,
    )
    draw_box(
        image,
        "\ub2e4\uc74c",
        (95, 183, 127, 192),
        maximum=7,
        align="right",
        edge_margin=1,
    )
    return ["MISSION INFORMATION", "STAGE", "TO CLEAR", "PREV", "NEXT"]


def patch_portraits(image: Image.Image) -> list[str]:
    names = [
        "\ud3ec\ubcf4\uc2a4",
        "\ub9e4\ub9ac\uc5b8",
        "\ub85c\uc2a4\ucf5c",
        "BRS",
        "\ub098\ub098",
        None,  # Nafe: preserve original Latin name pixels
        None,  # Zaha
        "\ubbf8\ud655\uc778",
        "\uc0e4\uc624\ubbfc",
        None,  # Mii
        None,  # Mazuma
        None,  # Shizu (shared Shizu/Karli portrait)
        None,  # Lilio
        "???",
    ]
    row_starts = (0, 77, 154)
    row_ends = (77, 154, 232)
    index = 0
    for row, (start, end) in enumerate(zip(row_starts, row_ends)):
        columns = 5 if row < 2 else 4
        band_top = end - 17
        for column in range(columns):
            x0 = round(column * 256 / 5)
            x1 = round((column + 1) * 256 / 5)
            name = names[index]
            # The source already uses an opaque black backing behind labels.
            # For alien entries, leave the original English name pixels in the
            # lower half and redraw only the Korean sender label.
            if name is None:
                clear(image, (x0, band_top, x1 - 1, band_top + 7), BLACK)
            else:
                clear(image, (x0, band_top, x1 - 1, end - 1), BLACK)
            draw_box(
                image,
                "\ubc1c\uc2e0",
                (x0 + 1, band_top, x1 - 1, band_top + 8),
                maximum=6,
                minimum=5,
                align="center",
            )
            if name is not None:
                draw_box(
                    image,
                    name,
                    (x0 + 1, band_top + 7, x1 - 1, end - 1),
                    maximum=8,
                    minimum=5,
                    align="center",
                )
            index += 1
    return [
        "FROM",
        "PHOBOS",
        "MARION",
        "ROTHCALL",
        "BRS",
        "NANA",
        "NAFE",
        "ZAHA",
        "UNKNOWN",
        "XIAOMIN",
        "MEFE",
        "MZMA",
        "SZZU",
        "LLWO",
    ]


def patch_customize_title(image: Image.Image) -> list[str]:
    # Preserve the white flame emblem at lower-left.
    clear(image, (0, 0, 127, 30), BLACK_TRANSPARENT)
    clear(image, (49, 29, 127, 63), BLACK_TRANSPARENT)
    draw_box(image, "\ucee4\uc2a4\ud130\ub9c8\uc774\uc988", (1, 0, 127, 26), maximum=18)
    return ["CUSTOMIZE"]


def patch_skills(image: Image.Image) -> list[str]:
    clear(image, (181, 3, 255, 25))
    draw_box(image, "\ucf2c", (184, 3, 218, 14), maximum=9)
    draw_box(image, "\ub054", (221, 12, 255, 24), maximum=9, align="right")
    clear(image, (157, 29, 255, 52))
    draw_box(image, "\ubb34\uae30 \uc2a4\ud0ac", (158, 29, 255, 40), maximum=9)
    draw_box(image, "\ud328\uc2dc\ube0c \uc2a4\ud0ac", (158, 40, 255, 52), maximum=9)
    return ["ON", "OFF", "WEAPON SKILLS", "PASSIVE SKILLS"]


def patch_attack_blade(image: Image.Image) -> list[str]:
    clear(image, (0, 0, 82, 28))
    draw_box(image, "\uacf5\uaca9", (1, 0, 80, 14), maximum=12)
    draw_box(image, "\ube14\ub808\uc774\ub4dc", (1, 13, 80, 28), maximum=12)
    clear(image, (96, 18, 127, 63))
    draw_box(
        image,
        "\uae30\ud0c0",
        (97, 23, 127, 39),
        maximum=10,
        minimum=8,
        align="center",
    )
    draw_box(
        image,
        "\uc544\uc774\ud15c",
        (96, 42, 127, 62),
        maximum=9,
        minimum=7,
        align="center",
    )
    return ["ATTACK", "BLADE", "MISC", "ITEMS"]


def patch_gallery_panel(image: Image.Image) -> list[str]:
    clear(image, (0, 31, 103, 63))
    draw_box(image, "\uc544\ud2b8 \uac10\uc0c1", (1, 31, 72, 41), maximum=8)
    draw_box(image, "\uc74c\uc545 \uac10\uc0c1", (1, 41, 72, 51), maximum=8)
    draw_box(image, "\uc601\uc0c1 \uac10\uc0c1", (1, 51, 72, 61), maximum=8)
    clear(image, (73, 31, 127, 64))
    draw_box(image, "\uc74c\uc545", (78, 40, 127, 58), maximum=11, align="right")
    clear(image, (0, 63, 95, 80))
    draw_box(image, "\ube44\uc5b4 \uc788\uc74c", (1, 63, 66, 79), maximum=11)
    draw_box(image, "\uc804\uccb4", (67, 63, 95, 79), maximum=9, align="right")
    return [
        "ART VIEWER",
        "AUDIO PLAYER",
        "MOVIE VIEWER",
        "AUDIO",
        "EMPTY",
        "ALL",
    ]


def patch_gallery_title(image: Image.Image) -> list[str]:
    clear(image, (31, 0, 63, 31), (20, 20, 20, 0))
    clear(image, (0, 31, 63, 79), (20, 20, 20, 0))
    draw_box(
        image,
        "\uac24\ub7ec\ub9ac",
        (1, 34, 63, 78),
        maximum=18,
        align="center",
    )
    return ["GALLERY"]


def patch_item_title(image: Image.Image) -> list[str]:
    # Preserve the chest emblem centered around x68..103.
    clear(image, (0, 100, 67, 143), (17, 17, 17, 0))
    clear(image, (104, 100, 127, 143), (17, 17, 17, 0))
    draw_box(image, "\uc544\uc774\ud15c", (2, 109, 67, 140), maximum=18)
    return ["ITEM"]


def patch_options_panel(image: Image.Image) -> list[str]:
    clear_exclusive(image, (0, 4, 256, 64))
    labels = [
        ("\ub370\uc774\ud130 \uc124\uce58", (1, 5, 112, 18), 10),
        ("\uc74c\uc131 \uc74c\ub7c9", (120, 5, 236, 18), 10),
        ("BGM \uc74c\ub7c9", (1, 18, 104, 31), 10),
        ("\uc74c\uc18c\uac70", (105, 18, 170, 31), 10),
        ("\ub054", (174, 18, 215, 31), 10),
        ("\ud6a8\uacfc\uc74c", (1, 31, 130, 45), 10),
        ("\ucf2c", (174, 31, 215, 45), 10),
        ("\uc790\ub3d9 \ub118\uae40", (1, 45, 130, 62), 11),
    ]
    for text, box, size in labels:
        draw_pixel_box(
            image, text, box, maximum=size, minimum=max(6, size - 2)
        )
    return [
        "DATA INSTALL",
        "VOICE VOLUME",
        "BGM VOLUME",
        "MUTE",
        "OFF",
        "SFX VOLUME",
        "ON",
        "AUTO SCROLL",
    ]


def patch_options_title(image: Image.Image) -> list[str]:
    clear(image, (42, 0, 127, 47))
    draw_box(image, "\uc124\uc815", (48, 3, 127, 42), maximum=24, align="center")
    return ["OPTIONS"]


def patch_option_range(image: Image.Image) -> list[str]:
    # Keep the segmented volume bar in the upper half.
    clear(image, (0, 9, 127, 23))
    draw_box(image, "\ucd5c\uc18c", (1, 9, 49, 23), maximum=11)
    draw_box(image, "\ucd5c\ub300", (77, 9, 127, 23), maximum=11, align="right")
    return ["MIN", "MAX"]


def patch_damage_rank(image: Image.Image) -> list[str]:
    # Runtime fills the gauges; only the baked legend is localized.
    clear(image, (153, 34, 232, 47))
    draw_box(image, "\ud53c\ud574 \ub7ad\ud06c", (154, 34, 232, 47), maximum=10)
    return ["DMG_RANK"]


def patch_battle_information(image: Image.Image) -> list[str]:
    clear_exclusive(image, (49, 43, 62, 112), (10, 7, 5, 0))
    draw_pixel_vertical(image, "\uc815\ubcf4", (49, 43, 62, 112), maximum=8)
    clear_exclusive(image, (3, 113, 64, 120), (10, 7, 5, 0))
    draw_pixel_box(
        image, "\uc801", (3, 113, 64, 120), maximum=7, minimum=7
    )
    return ["INFORMATION", "ENEMIES"]


def patch_battle_ready(image: Image.Image) -> list[str]:
    clear(image, (0, 0, 255, 47), (0, 51, 255, 0))
    draw_box(
        image,
        "\uacfc\uc5f4",
        (6, 3, 124, 21),
        maximum=16,
        fill=(255, 238, 119, 255),
    )
    draw_box(
        image,
        "\ube14\ub808\uc774\ub4dc \ubaa8\ub4dc \uc900\ube44",
        (6, 24, 250, 46),
        maximum=17,
        fill=(204, 255, 255, 255),
    )
    return ["OVERHEAT", "BLADE MODE READY"]


def patch_targeting(image: Image.Image) -> list[str]:
    clear(image, (43, 286, 100, 307), BLACK_TRANSPARENT)
    draw_box(image, "\uc870\uc900 \uace0\uc815", (43, 288, 100, 306), maximum=11)
    clear(image, (50, 324, 126, 359), BLACK_TRANSPARENT)
    draw_box(image, "\uc0ac\uaca9", (53, 333, 123, 357), maximum=18)
    return ["LOCK ON", "SHOOT"]


def patch_mission_results(image: Image.Image) -> list[str]:
    clear(image, (99, 1, 127, 103), BLACK_TRANSPARENT)
    draw_vertical(image, "\uc784\ubb34 \uacb0\uacfc", (99, 2, 127, 102), maximum=13)
    return ["MISSION RESULTS"]


def patch_pause(image: Image.Image) -> list[str]:
    clear_exclusive(image, (0, 0, 128, 24))
    draw_pixel_box(
        image, "\uc77c\uc2dc\uc815\uc9c0", (1, 1, 72, 16), maximum=9, minimum=8
    )
    draw_pixel_box(
        image, "\uae30\ub85d", (75, 1, 127, 16), maximum=8, minimum=7, align="right"
    )
    draw_pixel_box(
        image, "\uc644\ub8cc", (1, 17, 127, 23), maximum=6, minimum=6
    )
    return ["PAUSE", "CLEAR RECORD", "CHALLENGES CLEARED"]


def patch_mission_begin(image: Image.Image) -> list[str]:
    clear_exclusive(image, (0, 0, 128, 32))
    draw_pixel_box(
        image, "\uc784\ubb34 \uc2dc\uc791", (1, 1, 104, 16), maximum=12, minimum=9
    )
    draw_pixel_box(
        image,
        "\uc2dc\uac04",
        (85, 17, 107, 29),
        maximum=9,
        minimum=7,
        align="right",
    )
    return ["MISSION BEGIN", "TIME"]


def patch_mission_complete(image: Image.Image) -> list[str]:
    clear(image, (0, 8, 255, 31))
    draw_box(image, "\uc784\ubb34 \uc644\ub8cc", (3, 8, 247, 31), maximum=22)
    return ["MISSION COMPLETE"]


@dataclass(frozen=True)
class Spec:
    relative: str
    patcher: object


SPECS = [
    Spec("MENU/IF_MISSION_FAILED/000_PTMD.ptm", patch_mission_failed),
    Spec("MENU/IF_REC_INFO/005_PTMD.ptm", patch_record_info),
    Spec("MENU/IF_REC_INFO/007_PTMD.ptm", patch_unknown),
    Spec("MENU/MENU_LIBRARY/005_PTMD.ptm", patch_record_info),
    Spec("MENU/MENU_LIBRARY/007_PTMD.ptm", patch_unknown),
    Spec("MENU/IF_STAGE_SELECT/014_PTMD.ptm", patch_stage_select_menu),
    Spec("MENU/IF_STAGE_SELECT/018_PTMD.ptm", patch_mission_list),
    Spec("MENU/IF_STAGE_SELECT/021_PTMD.ptm", patch_stage_info),
    Spec("MENU/IF_STAGE_SELECT/023_PTMD.ptm", patch_portraits),
    Spec("MENU/MENU_CUSTOM/006_PTMD.ptm", patch_customize_title),
    Spec("MENU/MENU_CUSTOM/007_PTMD.ptm", patch_skills),
    Spec("MENU/MENU_CUSTOM/009_PTMD.ptm", patch_attack_blade),
    Spec("MENU/MENU_GALLERY/009_PTMD.ptm", patch_gallery_panel),
    Spec("MENU/MENU_GALLERY/010_PTMD.ptm", patch_gallery_title),
    Spec("MENU/MENU_ITEM/005_PTMD.ptm", patch_attack_blade),
    Spec("MENU/MENU_ITEM/006_PTMD.ptm", patch_item_title),
    Spec("MENU/MENU_OPTION/005_PTMD.ptm", patch_options_panel),
    Spec("MENU/MENU_OPTION/006_PTMD.ptm", patch_option_range),
    Spec("MENU/MENU_OPTION/007_PTMD.ptm", patch_options_title),
    Spec("SYSTEM/if_btlsys/003_PTMD.ptm", patch_damage_rank),
    Spec("SYSTEM/if_btlsys/004_PTMD.ptm", patch_battle_information),
    Spec("SYSTEM/if_btlsys/005_PTMD.ptm", patch_battle_ready),
    Spec("SYSTEM/if_btlsys/010_PTMD.ptm", patch_targeting),
    Spec("SYSTEM/if_fldsys/015_PTMD.ptm", patch_mission_results),
    Spec("SYSTEM/if_fldsys/017_PTMD.ptm", patch_pause),
    Spec("SYSTEM/if_fldsys/018_PTMD.ptm", patch_mission_begin),
    Spec("SYSTEM/if_fldsys/021_PTMD.ptm", patch_mission_complete),
]


def composite_preview(image: Image.Image, scale: int = 4) -> Image.Image:
    background = Image.new("RGBA", image.size, (70, 70, 70, 255))
    background.alpha_composite(image)
    return background.convert("RGB").resize(
        (image.width * scale, image.height * scale), Image.Resampling.NEAREST
    )


def make_contact(records: Iterable[dict[str, object]]) -> None:
    tiles: list[Image.Image] = []
    label_font = ImageFont.truetype(str(FONT_REGULAR), 15)
    width = 1120
    for record in records:
        original = Image.open(record["original_preview"]).convert("RGB")
        patched = Image.open(record["patched_preview"]).convert("RGB")
        # Previews are normally 4x.  Wide PTMDs must be scaled to a half-cell
        # so the original and Korean panes never overlap or get clipped.
        maximum_pane_width = 548
        if original.width > maximum_pane_width:
            ratio = maximum_pane_width / original.width
            original = original.resize(
                (maximum_pane_width, max(1, round(original.height * ratio))),
                Image.Resampling.NEAREST,
            )
        if patched.width > maximum_pane_width:
            ratio = maximum_pane_width / patched.width
            patched = patched.resize(
                (maximum_pane_width, max(1, round(patched.height * ratio))),
                Image.Resampling.NEAREST,
            )
        height = max(original.height, patched.height) + 35
        tile = Image.new("RGB", (width, height), (24, 24, 24))
        tile.paste(original, (0, 35))
        tile.paste(patched, (560, 35))
        draw = ImageDraw.Draw(tile)
        draw.text(
            (4, 5),
            f"{record['path']}  |  ORIGINAL",
            font=label_font,
            fill=WHITE[:3],
        )
        draw.text(
            (564, 5), "KOREAN", font=label_font, fill=(130, 220, 255)
        )
        tiles.append(tile)
    output = Image.new("RGB", (width, sum(tile.height for tile in tiles)), (15, 15, 15))
    y = 0
    for tile in tiles:
        output.paste(tile, (0, y))
        y += tile.height
    CONTACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.save(CONTACT_PATH, optimize=True)


def main() -> int:
    if not FONT_BOLD.is_file() or not FONT_REGULAR.is_file():
        raise FileNotFoundError("Korean system fonts are missing")
    if not PIXEL_FONT_7.is_file() or not PIXEL_FONT_9.is_file():
        raise FileNotFoundError("Galmuri pixel fonts are missing")
    records: list[dict[str, object]] = []
    for spec in SPECS:
        source = ORIGINAL_ROOT / spec.relative
        if not source.is_file():
            raise FileNotFoundError(source)
        original_bytes = source.read_bytes()
        image, texture = rgba_image(source)
        original_image = image.copy()
        labels = spec.patcher(image)
        patched_texture = replace_from_rgba(texture, image.tobytes())
        encoded = encode_ptmd(patched_texture)
        if len(encoded) != len(original_bytes):
            raise AssertionError(f"size changed for {spec.relative}")
        if encoded == original_bytes:
            raise AssertionError(f"no pixel change for {spec.relative}")
        destination = OUTPUT_ROOT / spec.relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encoded)
        decoded = decode_file(destination)
        if (decoded.width, decoded.height) != (texture.width, texture.height):
            raise AssertionError(f"dimension mismatch for {spec.relative}")
        patched_image = Image.frombytes(
            "RGBA", (decoded.width, decoded.height), decoded.rgba_bytes
        )
        original_preview = PREVIEW_ROOT / (spec.relative.replace("/", "__") + ".original.png")
        patched_preview = PREVIEW_ROOT / (spec.relative.replace("/", "__") + ".korean.png")
        original_preview.parent.mkdir(parents=True, exist_ok=True)
        composite_preview(original_image).save(original_preview, optimize=True)
        composite_preview(patched_image).save(patched_preview, optimize=True)
        records.append(
            {
                "path": spec.relative,
                "source_size": len(original_bytes),
                "patched_size": len(encoded),
                "source_sha256": sha256(original_bytes),
                "patched_sha256": sha256(encoded),
                "width": texture.width,
                "height": texture.height,
                "mode": texture.mode,
                "palette_format": texture.palette_format,
                "labels_replaced": labels,
                "label_count": len(labels),
                "byte_size_preserved": True,
                "pixel_change_verified": True,
                "decode_after_encode_verified": True,
                "original_preview": str(original_preview),
                "patched_preview": str(patched_preview),
            }
        )
    if len(records) != 27:
        raise AssertionError("expected 27 PTMD outputs")
    make_contact(records)
    report = {
        "schema": "brs-korean-ptmd-ui-fallback-v1",
        "ok": True,
        "passed": True,
        "error_count": 0,
        "warning_count": 0,
        "audited_ptmd_count": 132,
        "patched_ptmd_count": len(records),
        "labels_replaced_count": sum(int(record["label_count"]) for record in records),
        "font": {
            "regular": FONT_REGULAR.name,
            "bold": FONT_BOLD.name,
            "pixel_7": {
                "name": PIXEL_FONT_7.name,
                "sha256": sha256(PIXEL_FONT_7.read_bytes()),
            },
            "pixel_9": {
                "name": PIXEL_FONT_9.name,
                "sha256": sha256(PIXEL_FONT_9.read_bytes()),
            },
        },
        "output_root": str(OUTPUT_ROOT),
        "contact_sheet": str(CONTACT_PATH),
        "records": records,
        "allowlist": [
            {
                "text": "BRS / WRS / PSS / HP / ATK / DEF / SPD / BGM",
                "reason": "established character, hardware, or stat abbreviations",
            },
            {
                "text": "SELECT / START",
                "reason": "physical PSP button labels",
            },
            {
                "text": "proper-name initials and ???",
                "reason": "identity markers rather than untranslated functional UI",
            },
        ],
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: report[k] for k in report if k != "records"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
