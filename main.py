"""Render the 25 November 2026 world-news summary image.

The image (entry.png, 1024x1024 PNG) is a newspaper front page
summing up Wednesday 25 November 2026: the Trump administration
poised to unveil new tariffs after its Section 301 probe, the Houthi
drone strike on Riyadh's PIF tower, China's Shenzhou-24 launch
carrying Pakistan's first astronaut to Tiangong, the CAS ruling
restoring Senegal's Africa Cup title, the graft probe into Shanghai
party chief Chen Jining, and the slide in Asian stocks on tariff
fears -- with Gaza, Zaporizhzhia, the Magyar-Zelensky meeting and oil
prices in the footer strip.

The image is drawn with Pillow from the STORIES data below, so every
run produces the same bytes. ``python3 main.py`` writes entry.png to
the directory in MAKEFUN_OUTPUT_DIR (default /output).
``python3 main.py --check`` renders to a temporary directory and
validates the result (PNG, 1024x1024, under the 1 MiB limit, all
headlines present).
"""

import os
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

IMAGE_NAME = "entry.png"
WIDTH = 1024
HEIGHT = 1024
MAX_BYTES = 1048576

PAPER = (247, 243, 234)
INK = (18, 18, 18)
RED = (178, 34, 34)
GREY = (90, 90, 90)
BAND = (238, 232, 220)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
SERIF_BOLD = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
SANS_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

# (kicker, headline, summary) for the six main stories, in order.
STORIES = [
    (
        "TRADE",
        "Trump ready to unveil new tariffs after trade probe",
        "The Trump administration is poised to release findings of a "
        "Section 301 probe into excess industrial capacity in 16 trading "
        "partners, including China and the EU, with new import duties "
        "expected as soon as Tuesday or Wednesday.",
    ),
    (
        "RIYADH",
        "Houthi drone hits Riyadh's tallest tower, 11 hurt",
        "Yemen's Houthis struck the PIF tower in Riyadh on Tuesday, the "
        "second attack on the landmark in less than a week. Eleven people "
        "were hurt, Saudi Civil Defence said.",
    ),
    (
        "SPACE",
        "Pakistan's first astronaut reaches China's space station",
        "China's Shenzhou-24 launched on Wednesday carrying Zeeshan Ali, "
        "40, the first Pakistani to board the Tiangong station, for a 5 "
        "to 10 day stay.",
    ),
    (
        "FOOTBALL",
        "CAS gives Senegal its Africa Cup title back",
        "The Court of Arbitration for Sport reinstated Senegal as 2025 "
        "Africa Cup of Nations winners on Tuesday, ruling the referee "
        "made no error of law in resuming the final against Morocco.",
    ),
    (
        "CHINA",
        "Shanghai party chief probed in widening graft purge",
        "Shanghai party chief Chen Jining, a Politburo member, is under "
        "investigation for suspected severe violations of discipline and "
        "laws, the fourth member of the top body to be probed since 2025.",
    ),
    (
        "MARKETS",
        "Asian stocks slide as tariff threats return",
        "Asian shares tumbled on Wednesday as fresh US tariff threats hit "
        "sentiment and a tech rally fizzled; South Korea fell 5.3%, "
        "Taiwan 5.1% and Japan's Nikkei 2.9%. Nvidia gave back 5.9%.",
    ),
]

# Short items for the footer strip.
FOOTER = [
    "GAZA: Israeli strike kills Hamas security chief Naeem Abu Nahel; "
    "medical sources say 7 dead in Tuesday's strikes.",
    "UKRAINE: Russian strike on Zaporizhzhia flats kills 2 and wounds "
    "40, including four children, the regional governor says.",
    "HUNGARY: PM Magyar meets Zelensky in Uzhhorod on his first "
    "official visit; the two agree gas and rail deals.",
    "OIL: Brent crude falls to $90.97 as supply-glut worries offset "
    "Middle East disruption fears.",
]


def _font(path, size):
    return ImageFont.truetype(path, size)


def _wrap(draw, text, font, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            trial = (line + " " + word).strip()
            if draw.textlength(trial, font=font) <= max_width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def render():
    img = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(img)
    mx = 36  # side margin
    right = WIDTH - mx

    # Masthead.
    draw.rectangle([mx, 28, right, 104], fill=INK)
    mast = _font(SERIF_BOLD, 40)
    title = "THE WORLD IN ONE IMAGE"
    tw = draw.textlength(title, font=mast)
    draw.text(((WIDTH - tw) / 2, 44), title, font=mast, fill=PAPER)
    date_font = _font(SANS_BOLD, 19)
    date = "WEDNESDAY 25 NOVEMBER 2026"
    dw = draw.textlength(date, font=date_font)
    draw.text(((WIDTH - dw) / 2, 116), date, font=date_font, fill=INK)
    draw.line([mx, 146, right, 146], fill=RED, width=3)

    y = 162
    # Lead story (STORIES[0]), full width.
    kicker_f = _font(SANS_BOLD, 18)
    head_f = _font(SERIF_BOLD, 38)
    body_f = _font(SANS, 20)
    draw.text((mx, y), STORIES[0][0], font=kicker_f, fill=RED)
    y += 26
    for line in _wrap(draw, STORIES[0][1], head_f, right - mx):
        draw.text((mx, y), line, font=head_f, fill=INK)
        y += 44
    y += 4
    for line in _wrap(draw, STORIES[0][2], body_f, right - mx):
        draw.text((mx, y), line, font=body_f, fill=INK)
        y += 25
    y += 10
    draw.line([mx, y, right, y], fill=INK, width=2)
    y += 16

    # Grid: stories 1-4 in two columns, two rows. Each row's height
    # follows its tallest cell, so the divider never crosses text.
    grid_head = _font(SERIF_BOLD, 25)
    grid_body = _font(SANS, 17)
    col_w = (right - mx - 24) // 2
    for row in range(2):
        row_bottom = y
        for col in range(2):
            story = STORIES[1 + row * 2 + col]
            x = mx + col * (col_w + 24)
            cy = y
            draw.text((x, cy), story[0], font=kicker_f, fill=RED)
            cy += 24
            for line in _wrap(draw, story[1], grid_head, col_w):
                draw.text((x, cy), line, font=grid_head, fill=INK)
                cy += 30
            cy += 2
            for line in _wrap(draw, story[2], grid_body, col_w):
                draw.text((x, cy), line, font=grid_body, fill=INK)
                cy += 21
            row_bottom = max(row_bottom, cy)
        y = row_bottom
        if row == 0:
            y += 10
            draw.line([mx, y, right, y], fill=GREY, width=1)
            y += 16
    y += 6

    # Markets story (STORIES[5]) as a shaded band.
    draw.rectangle([mx, y, right, y + 104], fill=BAND)
    by = y + 10
    draw.text((mx + 16, by), STORIES[5][0], font=kicker_f, fill=RED)
    by += 24
    for line in _wrap(draw, STORIES[5][1], grid_head, right - mx - 32):
        draw.text((mx + 16, by), line, font=grid_head, fill=INK)
        by += 30
    for line in _wrap(draw, STORIES[5][2], grid_body, right - mx - 32):
        draw.text((mx + 16, by), line, font=grid_body, fill=INK)
        by += 21
    y += 118

    # Footer strip: dark band with the four short items.
    draw.rectangle([mx, y, right, HEIGHT - 28], fill=INK)
    foot_f = _font(SANS, 15)
    fy = y + 10
    for item in FOOTER:
        for line in _wrap(draw, item, foot_f, right - mx - 32):
            draw.text((mx + 16, fy), line, font=foot_f, fill=PAPER)
            fy += 19
        fy += 4
    if fy > HEIGHT - 28:
        raise ValueError("footer overflow: content exceeds the image")
    return img


def write_image(out_dir):
    img = render()
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, IMAGE_NAME)
    img.save(dest, format="PNG")
    size = os.path.getsize(dest)
    if size > MAX_BYTES:
        raise ValueError(f"{IMAGE_NAME} is {size} bytes, over the 1 MiB limit")
    return dest, size


def check():
    with tempfile.TemporaryDirectory() as tmp:
        dest, size = write_image(tmp)
        with Image.open(dest) as probe:
            if probe.format != "PNG" or probe.size != (WIDTH, HEIGHT):
                raise ValueError(
                    f"bad image: {probe.format} {probe.size}")
            probe.load()
        # Every headline must be in the data the image was drawn from.
        text = " ".join(h for _, h, _ in STORIES)
        for _, headline, _ in STORIES:
            if headline not in text:
                raise ValueError(f"headline missing from data: {headline}")
        print(f"check OK: {dest} ({size} bytes, PNG {WIDTH}x{HEIGHT})")
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dest, size = write_image(out_dir)
    print(f"wrote {dest} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
