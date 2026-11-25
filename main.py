#!/usr/bin/env python3
"""One picture of Wednesday 25 November 2026's world news.

This program is the entry for make.fun's news-image-20261125 bounty:
it paints a newspaper front page for 25 November 2026 and saves it as
entry.png. Six stories lead the page -- the Trump administration poised
to unveil new tariffs after its Section 301 trade probe, the Houthi
drone strike on Riyadh's PIF tower, China's Shenzhou-24 launch
carrying Pakistan's first astronaut to the Tiangong station, the CAS
ruling restoring Senegal's Africa Cup title, the graft probe into
Shanghai party chief Chen Jining, and the slide in Asian stocks on
tariff fears -- and four shorter items sit in the footer strip. All
ten were checked against mainstream reporting in the morning editions
of 25 November 2026 (Reuters above all); SOURCES.md gives the
story-by-story evidence.

Nothing here needs the network or any package beyond the Python
standard library. The lettering is a built-in 5x7 dot font stored as
one 35-character string per letter, the pictures are simple shapes
drawn on a pixel grid, and the PNG bytes are assembled by hand. There
is no Pillow, no font file read from disk, and no timestamp in the
output, so running the program twice writes the same bytes twice --
including under `python3 -P -s`, which is how the grader runs it.

    python3 main.py            write entry.png to $MAKEFUN_OUTPUT_DIR
                               (or /output when that is unset)
    python3 main.py --list     show the stories the picture carries
    python3 main.py --check    confirm entry.png next to this file
                               matches a fresh render, byte for byte
"""

from __future__ import annotations

import argparse, binascii, math, os, struct, sys, zlib

PAGE_W, PAGE_H = 1024, 1024
BYTE_LIMIT = 1048576

PAPER = 246, 241, 230
INK = 20, 20, 26
BODY = 52, 48, 42
NAVY = 20, 49, 92
CRIMSON = 179, 35, 42
HAIRLINE = 216, 207, 186
WHITE = 255, 255, 255

DAY = "WEDNESDAY 25 NOVEMBER 2026"
NAME = "THE WORLD IN ONE IMAGE"

# Each story is (headline, section tag, body copy, accent colour, emblem).
# The body is laid out by the renderer on at most three lines, and the
# headline on at most two, so the copy below is condensed to fit while
# keeping every fact from the morning editions.
NEWS = [
    ("TRUMP TO UNVEIL NEW TARIFFS", "TRADE",
     "Section 301 probe covers 16 trading partners, incl. China and "
     "the EU; new duties expected Tue/Wed.",
     (11, 95, 165), "globe"),
    ("HOUTHI DRONE HITS RIYADH TOWER", "RIYADH",
     "Houthis hit the PIF tower in Riyadh on Tue, second attack in "
     "under a week; 11 hurt, Civil Defence said.",
     (140, 47, 57), "warning"),
    ("PAKISTAN'S FIRST ASTRONAUT IN SPACE", "SPACE",
     "Shenzhou-24 launched Wed carrying Zeeshan Ali, 40, first "
     "Pakistani on Tiangong, for a 5-10 day stay.",
     (43, 58, 103), "rocket"),
    ("CAS GIVES SENEGAL ITS AFRICA CUP TITLE BACK", "FOOTBALL",
     "CAS reinstated Senegal as 2025 AFCON winners; referee made no "
     "error of law resuming final vs Morocco.",
     (30, 122, 70), "ball"),
    ("SHANGHAI PARTY CHIEF PROBED IN GRAFT PURGE", "CHINA",
     "Chen Jining, Politburo member, probed for severe violations of "
     "discipline and laws; 4th since 2025.",
     (107, 63, 160), "court"),
    ("ASIAN STOCKS SLIDE AS TARIFF THREATS RETURN", "MARKETS",
     "Korea fell 5.3%, Taiwan 5.1%, Nikkei 2.9% as tariff threats hit "
     "sentiment; Nvidia gave back 5.9%.",
     (178, 106, 0), "bars"),
]

# Short items for the footer, as (label, sentence); rendered "label: sentence".
EXTRA = [
    ("GAZA", "Israeli strike kills Hamas security chief Naeem Abu Nahel; 7 dead."),
    ("UKRAINE", "Russian strike on Zaporizhzhia flats kills 2, wounds 40, 4 children."),
    ("HUNGARY", "PM Magyar meets Zelensky in Uzhhorod; first visit, gas and rail deals."),
    ("OIL", "Brent crude falls to $90.97 on supply-glut worries."),
]


# ---------------------------------------------------------------------------
# Lettering. A glyph is one 35-character string: seven rows of five dots,
# '#' for a filled cell, '.' for an empty one, read left to right, top
# to bottom. Small letters sit on rows 3-7; g, j, p, q and y drop below
# the line. Only the characters the stories need are listed here.
# ---------------------------------------------------------------------------
GLYPHS = {
    'A': '.###.#...##...#######...##...##...#',
    'B': '####.#...##...#####.#...##...#####.',
    'C': '.#####....#....#....#....#.....####',
    'D': '####.#...##...##...##...##...#####.',
    'E': '######....#....####.#....#....#####',
    'F': '######....#....####.#....#....#....',
    'G': '.#####....#....#.####...##...#.###.',
    'H': '#...##...##...#######...##...##...#',
    'I': '#####..#....#....#....#....#..#####',
    'J': '..###...#....#....#....#.#..#..##..',
    'K': '#...##..#.#.#..##...#.#..#..#.#...#',
    'L': '#....#....#....#....#....#....#####',
    'M': '#...###.###.#.##.#.##...##...##...#',
    'N': '#...###..###..##.#.##..###..###...#',
    'O': '.###.#...##...##...##...##...#.###.',
    'P': '####.#...##...#####.#....#....#....',
    'Q': '.###.#...##...##...##.#.##..#..##.#',
    'R': '####.#...##...#####.#.#..#..#.#...#',
    'S': '.#####....#.....###.....#....#####.',
    'T': '#####..#....#....#....#....#....#..',
    'U': '#...##...##...##...##...##...#.###.',
    'V': '#...##...##...##...##...#.#.#...#..',
    'W': '#...##...##...##.#.##.#.###.###...#',
    'X': '#...##...#.#.#...#...#.#.#...##...#',
    'Y': '#...##...#.#.#...#....#....#....#..',
    'Z': '#####....#...#...#...#...#....#####',
    'a': '...........###.....#.#####...#.####',
    'b': '#....#....####.#...##...##...#####.',
    'c': '...........#####....#....#.....####',
    'd': '....#....#.#####...##...##...#.####',
    'e': '...........###.#...#######.....###.',
    'f': '..##..#..#.#...####..#....#....#...',
    'g': '......###.#...##...#.###.....####..',
    'h': '#....#....####.#...##...##...##...#',
    'i': '.......#........##....#....#...###.',
    'j': '........#........##....#....#.##...',
    'k': '#....#....#..#.#.#..##...#.#..#..#.',
    'l': '.##....#....#....#....#....#...###.',
    'm': '..........##.#.#.#.##.#.##.#.##.#.#',
    'n': '..........####.#...##...##...##...#',
    'o': '...........###.#...##...##...#.###.',
    'p': '.....####.#...##...#####.#....#....',
    'q': '......#####...##...#.####...#...##.',
    'r': '..........#.##.##..##....#....#....',
    's': '...........#####.....###.....#####.',
    't': '.#....#...####..#....#....#.....##.',
    'u': '..........#...##...##...##...#.###.',
    'v': '..........#...##...##...#.#.#...#..',
    'w': '..........#...##.#.##.#.##.#.#.#.#.',
    'x': '..........#...#.#.#...#...#.#.#...#',
    'y': '..........#...##...#.####....#.###.',
    'z': '..........#####...#...#...#...#####',
    '0': '.###.#...##..###.#.###..##...#.###.',
    '1': '..#...##....#....#....#....#...###.',
    '2': '.###.#...#....#...#...#...#...#####',
    '3': '####.....#....#.###.....#....#####.',
    '4': '...#...##..#.#.#..#.#####...#....#.',
    '5': '######....####.....#....##...#.###.',
    '6': '.###.#....#....####.#...##...#.###.',
    '7': '#####....#...#....#...#....#....#..',
    '8': '.###.#...##...#.###.#...##...#.###.',
    '9': '.###.#...##...#.####....#....#.###.',
    ' ': '...................................',
    '.': '................................#..',
    ',': '...........................#...#...',
    "'": '..#....#...........................',
    '"': '.#.#..#.#..........................',
    '-': '................###................',
    ':': '............#..............#.......',
    ';': '............#..............#...#...',
    '!': '..#....#....#....#....#.........#..',
    '?': '.###.#...#....#...#...#.........#..',
    '/': '....#....#...#...#...#...#....#....',
    '(': '...#...#...#....#....#.....#.....#.',
    ')': '.#.....#.....#....#....#...#...#...',
    '$': '..#...#####.#...###...#.#####...#..',
    '%': '##..###.#....#...#...#...#.##.#..##',
    '+': '............#...###...#............',
    '=': '...........###.......###...........',
    '_': '..............................#####',
}


def measure(text, scale):
    """Width in pixels of `text` drawn at `scale`."""
    return len(text) * 6 * scale - scale


def split_lines(text, scale, limit):
    """Break `text` into lines no wider than `limit` pixels."""
    done, current = [], ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if measure(trial, scale) <= limit:
            current = trial
        else:
            if current:
                done.append(current)
            current = word
    if current:
        done.append(current)
    return done


class Sheet:
    """An RGB pixel grid with a few drawing primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.pixels = bytearray(bytes(bg) * (w * h))

    def box(self, x, y, w, h, colour):
        r, g, b = colour
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        if x1 <= x0 or y1 <= y0:
            return
        stripe = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            at = (yy * self.w + x0) * 3
            self.pixels[at:at + len(stripe)] = stripe

    def disc(self, cx, cy, r, colour):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.box(cx - dx, cy + dy, 2 * dx + 1, 1, colour)

    def tri(self, cx, base, height, half, colour):
        for row in range(height):
            span = (row + 1) * half // height
            self.box(cx - span, base - height + row, 2 * span, 1, colour)

    def glyph(self, ch, x, y, scale, colour):
        rows = GLYPHS[ch]
        for r in range(7):
            for c in range(5):
                if rows[r * 5 + c] == "#":
                    self.box(x + c * scale, y + r * scale,
                             scale, scale, colour)

    def text(self, s, x, y, scale, colour):
        for ch in s:
            self.glyph(ch, x, y, scale, colour)
            x += 6 * scale


def chunk(kind, data):
    body = kind + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF))


def to_png(sheet):
    """Encode a Sheet as PNG bytes (truecolour, no filtering)."""
    raw = bytearray()
    stride = sheet.w * 3
    for y in range(sheet.h):
        raw.append(0)
        raw += sheet.pixels[y * stride:(y + 1) * stride]
    head = struct.pack(">IIBBBBB", sheet.w, sheet.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# Emblems. Each one is drawn in a 64 by 64 square at (ox, oy).
# ---------------------------------------------------------------------------
def emblem(sheet, kind, ox, oy, colour):
    if kind == "globe":
        sheet.disc(ox + 32, oy + 32, 28, colour)
        sheet.box(ox + 6, oy + 28, 52, 8, PAPER)
        sheet.box(ox + 28, oy + 6, 8, 52, PAPER)
    elif kind == "chip":
        sheet.box(ox + 14, oy + 14, 36, 36, colour)
        sheet.box(ox + 24, oy + 24, 16, 16, PAPER)
        for k in range(3):
            sheet.box(ox + 4, oy + 18 + k * 12, 10, 6, colour)
            sheet.box(ox + 50, oy + 18 + k * 12, 10, 6, colour)
            sheet.box(ox + 18 + k * 12, oy + 4, 6, 10, colour)
            sheet.box(ox + 18 + k * 12, oy + 50, 6, 10, colour)
    elif kind == "warning":
        sheet.tri(ox + 32, oy + 58, 52, 30, colour)
        sheet.text("!", ox + 26, oy + 30, 2, WHITE)
    elif kind == "ballot":
        sheet.box(ox + 12, oy + 12, 40, 40, colour)
        for dx, dy in ((8, 20), (14, 26), (20, 14), (26, 6)):
            sheet.box(ox + 12 + dx, oy + 12 + dy, 8, 8, PAPER)
    elif kind == "mountains":
        sheet.tri(ox + 22, oy + 58, 40, 22, colour)
        sheet.tri(ox + 46, oy + 58, 30, 16, colour)
    elif kind == "court":
        sheet.tri(ox + 32, oy + 26, 18, 28, colour)
        for k in range(3):
            sheet.box(ox + 12 + k * 14, oy + 30, 6, 24, colour)
        sheet.box(ox + 8, oy + 54, 48, 6, colour)
    elif kind == "rocket":
        sheet.tri(ox + 32, oy + 12, 12, 7, colour)
        sheet.box(ox + 25, oy + 12, 14, 30, colour)
        sheet.box(ox + 29, oy + 20, 6, 6, PAPER)
        sheet.box(ox + 18, oy + 34, 7, 10, colour)
        sheet.box(ox + 39, oy + 34, 7, 10, colour)
        sheet.tri(ox + 32, oy + 56, 12, 5, colour)
    elif kind == "ball":
        sheet.disc(ox + 32, oy + 32, 26, colour)
        sheet.disc(ox + 32, oy + 32, 14, PAPER)
        sheet.disc(ox + 32, oy + 32, 5, colour)
    elif kind == "bars":
        sheet.box(ox + 10, oy + 40, 12, 18, colour)
        sheet.box(ox + 26, oy + 28, 12, 30, colour)
        sheet.box(ox + 42, oy + 16, 12, 42, colour)
    else:
        raise ValueError("no such emblem: %r" % (kind,))


MARGIN, GRID_Y = 28, 122
CELL_W, CELL_H = 476, 236
GAP_X, GAP_Y = 16, 12


def front_page():
    """Paint the whole front page and hand back its PNG bytes."""
    page = Sheet(PAGE_W, PAGE_H, PAPER)
    page.text(NAME, (PAGE_W - measure(NAME, 4)) // 2, 18, 4, NAVY)
    page.text(DAY, (PAGE_W - measure(DAY, 5)) // 2, 56, 5, CRIMSON)
    page.box(MARGIN, 100, PAGE_W - 2 * MARGIN, 2, NAVY)
    page.box(MARGIN, 104, PAGE_W - 2 * MARGIN, 1, NAVY)

    for n, (headline, tag, body, accent, kind) in enumerate(NEWS):
        x0 = MARGIN + (n % 2) * (CELL_W + GAP_X)
        y0 = GRID_Y + (n // 2) * (CELL_H + GAP_Y)
        page.box(x0, y0, CELL_W, 1, HAIRLINE)
        page.box(x0, y0 + CELL_H - 1, CELL_W, 1, HAIRLINE)
        page.box(x0, y0, 1, CELL_H, HAIRLINE)
        page.box(x0 + CELL_W - 1, y0, 1, CELL_H, HAIRLINE)
        page.box(x0, y0, CELL_W, 8, accent)
        page.box(x0 + 16, y0 + 24, 64, 64, accent)
        digit = str(n + 1)
        page.text(digit, x0 + 16 + (64 - measure(digit, 4)) // 2,
                  y0 + 24 + (64 - 7 * 4) // 2, 4, WHITE)
        emblem(page, kind, x0 + 96, y0 + 24, accent)
        page.text(tag, x0 + CELL_W - 16 - measure(tag, 2),
                  y0 + 28, 2, accent)
        heads = split_lines(headline, 3, CELL_W - 32)
        if len(heads) > 2:
            raise ValueError("headline spills to %d lines: %r"
                             % (len(heads), headline))
        for i, line in enumerate(heads):
            page.text(line, x0 + 16, y0 + 100 + i * 24, 3, INK)
        paras = split_lines(body, 2, CELL_W - 32)
        if len(paras) > 3:
            raise ValueError("body spills to %d lines: %r"
                             % (len(paras), body))
        for i, line in enumerate(paras):
            page.text(line, x0 + 16, y0 + 152 + i * 22, 2, BODY)

    foot = GRID_Y + 3 * CELL_H + 2 * GAP_Y + 18
    page.box(MARGIN, foot, PAGE_W - 2 * MARGIN, 2, NAVY)
    page.text("ALSO TODAY", MARGIN, foot + 12, 2, CRIMSON)
    for i, (label, sentence) in enumerate(EXTRA):
        line = label + ": " + sentence
        y = foot + 34 + i * 20
        if measure(line, 2) > PAGE_W - 2 * MARGIN - 20:
            raise ValueError("footer line too wide: %r" % (line,))
        page.box(MARGIN, y + 3, 8, 8, NAVY)
        page.text(line, MARGIN + 20, y, 2, BODY)
    return to_png(page)


def show_stories():
    lines = [DAY + " — " + NAME, ""]
    for n, (headline, tag, body, accent, kind) in enumerate(NEWS, 1):
        lines.append("%d. %s [%s]" % (n, headline, tag))
        lines.append("   " + body)
        lines.append("")
    lines.append("ALSO:")
    for label, sentence in EXTRA:
        lines.append("   - %s: %s" % (label, sentence))
    return "\n".join(lines)


def cli(argv=None):
    parser = argparse.ArgumentParser(
        description="Draw the 25 November 2026 world-news image.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true",
                       help="print the stories the image encodes")
    group.add_argument("--check", action="store_true",
                       help="verify entry.png beside this script matches "
                            "a fresh render, byte for byte")
    args = parser.parse_args(argv)
    if args.list:
        print(show_stories())
        return 0
    data = front_page()
    if args.check:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "entry.png")
        if not os.path.isfile(path):
            print("entry.png not found beside main.py", file=sys.stderr)
            return 1
        with open(path, "rb") as handle:
            stored = handle.read()
        if stored == data:
            print("ok: entry.png matches a fresh render "
                  "(%d bytes)" % len(data))
            return 0
        print("entry.png differs from a fresh render", file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    with open(dest, "wb") as handle:
        handle.write(data)
    if len(data) > BYTE_LIMIT:
        print("entry.png is %d bytes, over the 1 MiB limit"
              % len(data), file=sys.stderr)
        return 1
    print("wrote %s (%d bytes, %dx%d)"
          % (dest, len(data), PAGE_W, PAGE_H))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
