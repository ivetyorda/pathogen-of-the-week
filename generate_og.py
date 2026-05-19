#!/usr/bin/env python3
"""
generate_og.py — Render the dashboard's social-share thumbnail (1200x630 og-image.png)
from data.json. Matches the dashboard's dark briefing-room theme.

Usage:
    python3 generate_og.py [data.json] [og-image.png]

Defaults to ./data.json and ./og-image.png in the script's directory.
Requires Pillow:  pip install Pillow --break-system-packages
"""
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("ERROR: Pillow is not installed. Run: pip install Pillow --break-system-packages")


# -----------------------------------------------------------------------------
# Theme — matches the dashboard's CSS custom properties.
# -----------------------------------------------------------------------------
W, H = 1200, 630

BG        = (11, 16, 32)        # #0b1020
BG_ELEV   = (19, 26, 50)        # #131a32
INK       = (232, 234, 240)     # primary text
INK_DIM   = (148, 158, 184)     # secondary text
LINE      = (40, 48, 78)        # subtle borders
ACCENT    = (110, 231, 255)     # #6ee7ff — cyan
ACCENT_2  = (167, 139, 250)     # #a78bfa — purple
CRIT      = (248, 113, 113)     # #f87171 — red (acute)
WARN      = (251, 191, 36)      # #fbbf24 — amber (smolder)
OK        = (74, 222, 128)      # green (ok)

TAG_COLORS = {
    "acute":   CRIT,
    "smolder": WARN,
    "watch":   ACCENT,
}

# Candidate font paths — try macOS first, then Linux, then PIL default.
FONT_CANDIDATES = {
    "regular": [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "bold": [
        "/System/Library/Fonts/Helvetica.ttc",  # macOS Helvetica has bold inside
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "italic": [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
    ],
}


def load_font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES.get(weight, []):
        if Path(path).exists():
            try:
                # macOS .ttc files: index 1 is usually bold for Helvetica.ttc
                if path.endswith(".ttc"):
                    idx = 1 if weight == "bold" else (2 if weight == "italic" else 0)
                    return ImageFont.truetype(path, size=size, index=idx)
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


# -----------------------------------------------------------------------------
# Drawing helpers
# -----------------------------------------------------------------------------
def text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    """Width of `text` rendered with `font`."""
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    return draw.textsize(text, font=font)[0]


def text_h(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]
    return draw.textsize(text, font=font)[1]


def truncate(draw, text, font, max_w):
    if text_w(draw, text, font) <= max_w:
        return text
    while text and text_w(draw, text + "…", font) > max_w:
        text = text[:-1]
    return text + "…"


def radial_glow(img: Image.Image, center, radius, color, alpha):
    """Paint a soft radial glow onto `img`."""
    cx, cy = center
    r = radius
    glow = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    # Layered concentric ellipses for a smooth falloff
    steps = 32
    for i in range(steps, 0, -1):
        a = int(alpha * (i / steps) ** 2)
        rr = int(r * (i / steps))
        g_draw.ellipse([r - rr, r - rr, r + rr, r + rr], fill=(*color, a))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=24))
    img.alpha_composite(glow, (cx - r, cy - r))


def rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Wrapper around Pillow rounded_rectangle for older versions."""
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    else:
        draw.rectangle(xy, fill=fill, outline=outline, width=width)


def draw_chip(draw, x, y, label, font, fill, text_color=(255, 255, 255), pad_x=14, pad_y=7):
    tw = text_w(draw, label, font)
    th = text_h(draw, label, font)
    w = tw + pad_x * 2
    h = th + pad_y * 2
    rounded_rect(draw, [x, y, x + w, y + h], radius=h // 2, fill=fill)
    draw.text((x + pad_x, y + pad_y - 2), label, font=font, fill=text_color)
    return w, h


def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if text_w(draw, candidate, font) <= max_w:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# -----------------------------------------------------------------------------
# Composition
# -----------------------------------------------------------------------------
def render_og(data: dict, out_path: Path) -> None:
    img = Image.new("RGBA", (W, H), (*BG, 255))

    # --- background atmospherics: deep gradient + two radial glows -----------
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad)
    for y in range(H):
        # subtle top-to-bottom darkening
        t = y / H
        shade = int(8 * (1 - t))
        g_draw.line([(0, y), (W, y)], fill=(shade, shade, shade + 4, 255))
    img.alpha_composite(grad)

    radial_glow(img, (-60, -40), 520, ACCENT_2, alpha=70)
    radial_glow(img, (W + 60, H + 80), 620, ACCENT, alpha=55)

    # subtle grid lines
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 60):
        gd.line([(x, 0), (x, H)], fill=(*LINE, 35), width=1)
    for y in range(0, H, 60):
        gd.line([(0, y), (W, y)], fill=(*LINE, 35), width=1)
    img.alpha_composite(grid)

    draw = ImageDraw.Draw(img)

    # --- typography ----------------------------------------------------------
    f_brand    = load_font("bold",    40)
    f_brand_sm = load_font("regular", 18)
    f_chip     = load_font("bold",    16)
    f_chip_sm  = load_font("bold",    14)
    f_tag      = load_font("bold",    18)
    f_title    = load_font("bold",    72)
    f_title_2  = load_font("bold",    62)
    f_latin    = load_font("italic",  22)
    f_stat_num = load_font("bold",    62)
    f_stat_lbl = load_font("regular", 16)
    f_url      = load_font("bold",    20)
    f_compose  = load_font("regular", 18)

    # --- top bar -------------------------------------------------------------
    PAD = 56
    top_y = 48

    # brand mark: small accent square
    mark_size = 42
    rounded_rect(draw, [PAD, top_y, PAD + mark_size, top_y + mark_size],
                 radius=10, fill=(*ACCENT, 255))
    rounded_rect(draw, [PAD + 8, top_y + 8, PAD + mark_size - 8, top_y + mark_size - 8],
                 radius=4, fill=(*BG, 255))
    # tiny "P" inside
    p_font = load_font("bold", 22)
    pw = text_w(draw, "P", p_font)
    draw.text((PAD + mark_size // 2 - pw // 2, top_y + 9), "P",
              font=p_font, fill=(*ACCENT, 255))

    # brand text
    brand_x = PAD + mark_size + 14
    draw.text((brand_x, top_y - 2), "Pathogen of the Week",
              font=f_brand, fill=INK)
    draw.text((brand_x, top_y + 44), "Weekly briefing for policymakers",
              font=f_brand_sm, fill=INK_DIM)

    # week chip (top-right)
    week_start = data["week_start"]   # e.g. 2026-05-18
    week_end   = data["week_end"]
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    m_start = months[int(week_start.split("-")[1]) - 1]
    m_end   = months[int(week_end.split("-")[1]) - 1]
    d_start = int(week_start.split("-")[2])
    d_end   = int(week_end.split("-")[2])
    if m_start == m_end:
        date_range = f"{d_start}–{d_end} {m_end} {data['iso_year']}"
    else:
        date_range = f"{d_start} {m_start} – {d_end} {m_end} {data['iso_year']}"
    chip_label = f"WEEK {data['iso_week']}  ·  {date_range}"
    chip_w = text_w(draw, chip_label, f_chip) + 32
    chip_h = 38
    chip_x = W - PAD - chip_w
    chip_y = top_y + 6
    rounded_rect(draw, [chip_x, chip_y, chip_x + chip_w, chip_y + chip_h],
                 radius=chip_h // 2, fill=(*BG_ELEV, 235),
                 outline=(*ACCENT, 180), width=1)
    draw.text((chip_x + 16, chip_y + 9), chip_label, font=f_chip, fill=INK)

    # --- lead pathogen panel ------------------------------------------------
    lead = next((p for p in data["pathogens"] if p.get("is_lead")), data["pathogens"][0])

    panel_top = 150
    panel_h   = 392
    panel_x0  = PAD
    panel_x1  = W - PAD
    rounded_rect(draw, [panel_x0, panel_top, panel_x1, panel_top + panel_h],
                 radius=22,
                 fill=(*BG_ELEV, 220),
                 outline=(*LINE, 255), width=1)

    # tag chip
    tag_color = TAG_COLORS.get(lead["tag"], ACCENT)
    tag_text  = lead["tag_label"].upper()
    # shorten if too long
    if len(tag_text) > 56:
        tag_text = tag_text[:53] + "…"
    draw_chip(draw, panel_x0 + 32, panel_top + 28, tag_text, f_tag,
              fill=(*tag_color, 235),
              text_color=(*BG, 255),
              pad_x=14, pad_y=8)

    # lead title — choose size that fits
    title = lead["name"]
    title_font = f_title
    if text_w(draw, title, title_font) > (panel_x1 - panel_x0 - 64):
        title_font = f_title_2
    if text_w(draw, title, title_font) > (panel_x1 - panel_x0 - 64):
        title = truncate(draw, title, title_font, panel_x1 - panel_x0 - 64)
    title_y = panel_top + 86
    draw.text((panel_x0 + 32, title_y), title, font=title_font, fill=INK)

    # scientific name (italic) — wrap if needed, max 2 lines
    sci = lead["scientific_name"]
    sci_max_w = panel_x1 - panel_x0 - 64
    sci_lines = wrap_text(draw, sci, f_latin, sci_max_w)[:2]
    if len(sci_lines) == 2 and text_w(draw, sci_lines[1], f_latin) > sci_max_w:
        sci_lines[1] = truncate(draw, sci_lines[1], f_latin, sci_max_w)
    sci_y = title_y + (74 if title_font is f_title else 64)
    for i, line in enumerate(sci_lines):
        draw.text((panel_x0 + 32, sci_y + i * 28),
                  line if i < len(sci_lines) - 1 or text_w(draw, line, f_latin) <= sci_max_w
                       else truncate(draw, line, f_latin, sci_max_w),
                  font=f_latin, fill=INK_DIM)

    # --- stat tiles ----------------------------------------------------------
    stats = lead.get("stats", [])[:3]
    tiles_top = panel_top + panel_h - 150
    tile_gap  = 18
    tile_w    = (panel_x1 - panel_x0 - 64 - tile_gap * (len(stats) - 1)) // max(1, len(stats))
    tile_h    = 118
    for i, s in enumerate(stats):
        tx = panel_x0 + 32 + i * (tile_w + tile_gap)
        rounded_rect(draw, [tx, tiles_top, tx + tile_w, tiles_top + tile_h],
                     radius=14,
                     fill=(*BG, 200),
                     outline=(*LINE, 255), width=1)
        # accent strip on top
        strip_color = {"crit": CRIT, "warn": WARN, "ok": OK}.get(s.get("tone", "neutral"), ACCENT)
        rounded_rect(draw, [tx, tiles_top, tx + tile_w, tiles_top + 4],
                     radius=4, fill=(*strip_color, 255))

        # number — center horizontally
        num = s["num"]
        num_font = f_stat_num
        # downscale font if too wide
        nw = text_w(draw, num, num_font)
        if nw > tile_w - 28:
            num_font = load_font("bold", 48)
            nw = text_w(draw, num, num_font)
        nx = tx + (tile_w - nw) // 2
        draw.text((nx, tiles_top + 18), num, font=num_font, fill=strip_color)

        # label — wrapped to 2 lines max, centered
        lbl_lines = wrap_text(draw, s["label"], f_stat_lbl, tile_w - 24)[:2]
        if len(lbl_lines) == 2 and text_w(draw, lbl_lines[1], f_stat_lbl) > tile_w - 24:
            lbl_lines[1] = truncate(draw, lbl_lines[1], f_stat_lbl, tile_w - 24)
        ly = tiles_top + tile_h - 18 - len(lbl_lines) * 20
        for j, line in enumerate(lbl_lines):
            lw = text_w(draw, line, f_stat_lbl)
            draw.text((tx + (tile_w - lw) // 2, ly + j * 20),
                      line, font=f_stat_lbl, fill=INK_DIM)

    # --- footer --------------------------------------------------------------
    foot_y = panel_top + panel_h + 26
    # composite + secondary pathogens
    others = [p for p in data["pathogens"] if not p.get("is_lead")][:2]
    others_text = "  ·  ".join(f"{p['name']}" for p in others)
    if others_text:
        draw.text((PAD, foot_y),
                  f"Also tracking:  {others_text}",
                  font=f_compose, fill=INK_DIM)

    # url right
    url = data.get("site_url", "")
    url_display = url.replace("https://", "").rstrip("/")
    uw = text_w(draw, url_display, f_url)
    draw.text((W - PAD - uw, foot_y - 2), url_display, font=f_url, fill=ACCENT)

    # ------------------------------------------------------------------------
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, format="PNG", optimize=True)


import re


def update_meta_tags(index_path: Path, data: dict) -> bool:
    """Rewrite OG/Twitter meta tags in index.html from data.json. Returns True if updated."""
    if not index_path.exists():
        print(f"WARN: {index_path} not found, skipping meta-tag update")
        return False
    lead = next((p for p in data["pathogens"] if p.get("is_lead")), data["pathogens"][0])
    # Build dynamic title and description
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    m_end   = months[int(data["week_end"].split("-")[1]) - 1]
    d_start = int(data["week_start"].split("-")[2])
    d_end   = int(data["week_end"].split("-")[2])
    title = (
        f"Pathogen of the Week — Week {data['iso_week']}, {data['iso_year']}: "
        f"{lead['name']}"
    )
    # Short description: top 3 stats (preserve original label casing — acronyms, place names)
    stat_bits = []
    for s in lead.get("stats", [])[:3]:
        stat_bits.append(f"{s['num']} {s['label']}")
    short_desc = (
        f"Week {data['iso_week']} · {d_start}–{d_end} {m_end} {data['iso_year']}. "
        + " · ".join(stat_bits)
    )
    if len(short_desc) > 280:
        short_desc = short_desc[:277] + "..."

    html = index_path.read_text(encoding="utf-8")
    # Bust the og:image cache so social platforms fetch the new PNG.
    image_url = f"https://ivetyorda.github.io/pathogen-of-the-week/og-image.png?v={data['iso_year']}-W{data['iso_week']:02d}"

    replacements = [
        (r'(<meta property="og:title" content=")[^"]*(")',          rf'\g<1>{_attr_escape(title)}\g<2>'),
        (r'(<meta property="og:description" content=")[^"]*(")',    rf'\g<1>{_attr_escape(short_desc)}\g<2>'),
        (r'(<meta property="og:image" content=")[^"]*(")',          rf'\g<1>{_attr_escape(image_url)}\g<2>'),
        (r'(<meta property="og:image:alt" content=")[^"]*(")',      rf'\g<1>{_attr_escape(title)}\g<2>'),
        (r'(<meta name="twitter:title" content=")[^"]*(")',         rf'\g<1>{_attr_escape(title)}\g<2>'),
        (r'(<meta name="twitter:description" content=")[^"]*(")',   rf'\g<1>{_attr_escape(short_desc)}\g<2>'),
        (r'(<meta name="twitter:image" content=")[^"]*(")',         rf'\g<1>{_attr_escape(image_url)}\g<2>'),
    ]
    changed = False
    for pat, repl in replacements:
        new_html, n = re.subn(pat, repl, html, count=1)
        if n:
            html = new_html
            changed = True
    if changed:
        index_path.write_text(html, encoding="utf-8")
        print(f"Updated meta tags in {index_path}")
    else:
        print(f"No meta tags found to update in {index_path} (run once to insert them manually)")
    return changed


def _attr_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace('"', "&quot;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def main():
    here = Path(__file__).parent
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "data.json"
    out_path  = Path(sys.argv[2]) if len(sys.argv) > 2 else here / "og-image.png"

    if not data_path.exists():
        sys.exit(f"ERROR: data file not found: {data_path}")

    data = json.loads(data_path.read_text(encoding="utf-8"))
    render_og(data, out_path)
    size = out_path.stat().st_size
    print(f"Wrote {out_path}  ({size:,} bytes, 1200x630 PNG)")

    # Keep index.html's social-share metadata in sync with this week's lead.
    update_meta_tags(here / "index.html", data)


if __name__ == "__main__":
    main()
