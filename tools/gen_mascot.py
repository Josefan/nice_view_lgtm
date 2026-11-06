#!/usr/bin/env python3
"""Generate the Claude Code mascot (Clawd) frames for the nice_view_lgtm shield.

The sprite is read from a PNG (default: tools/source/clawd.png, the 12x8 base
emoji from github.com/afspies/clawdmoji, MIT). The PNG is converted to BMP with
macOS `sips`, read with a small pure-Python BMP parser, and sampled down to its
pixel-art grid. Animation frames are then built procedurally from that grid:

    idle, blink              - resting (blink now and then)
    tap_left, tap_right      - reacting to key presses on the right half
    work_0..3                - Claude is working: thinking dots + gentle bob
    need_0..3                - Claude needs you: bounce, waving arms, "!" bubble

Frames are drawn upright in portrait coordinates (as seen on the keyboard), then
rotated 90 degrees clockwise into the panel's native landscape orientation and
written as LVGL 1-bit indexed images (LV_COLOR_FORMAT_I1).

    python3 -I tools/gen_mascot.py --preview   # print the frames
    python3 -I tools/gen_mascot.py             # write .../assets/mascot.c
"""

import argparse
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools/source/clawd.png"
OUT = ROOT / "boards/shields/nice_view_lgtm/assets/mascot.c"

W, H = 68, 100      # portrait frame size
GRID_W, GRID_H = 12, 8
SCALE = 5           # one sprite cell = 5x5 screen pixels
SPRITE_X = (W - GRID_W * SCALE) // 2
SPRITE_Y = 52       # top of the sprite when resting


# ---------------------------------------------------------------- PNG -> grid

def read_bmp(path):
    """Minimal reader for the uncompressed 24/32-bit BMPs that sips writes."""
    data = Path(path).read_bytes()
    if data[:2] != b"BM":
        raise ValueError("not a BMP file")
    offset = struct.unpack_from("<I", data, 10)[0]
    width, height = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]
    if bpp not in (24, 32):
        raise ValueError(f"unsupported BMP depth {bpp}")
    bottom_up = height > 0
    height = abs(height)
    bytes_pp = bpp // 8
    stride = (width * bytes_pp + 3) & ~3
    rows = []
    for y in range(height):
        src_y = height - 1 - y if bottom_up else y
        base = offset + src_y * stride
        row = []
        for x in range(width):
            b, g, r = data[base + x * bytes_pp: base + x * bytes_pp + 3]
            a = data[base + x * bytes_pp + 3] if bytes_pp == 4 else 255
            row.append((r, g, b, a))
        rows.append(row)
    return rows


def load_sprite(png, grid_w, grid_h):
    """Convert png with sips, keep the body colour, sample it to grid_w x grid_h cells."""
    with tempfile.TemporaryDirectory() as tmp:
        bmp = Path(tmp) / "sprite.bmp"
        subprocess.run(["sips", "-s", "format", "bmp", str(png), "--out", str(bmp)],
                       check=True, capture_output=True)
        px = read_bmp(bmp)

    # The body is the most common clearly visible, non-dark colour (Clawd orange).
    counts = {}
    for row in px:
        for r, g, b, a in row:
            if a > 128 and r + g + b > 150:
                counts[(r, g, b)] = counts.get((r, g, b), 0) + 1
    body = max(counts, key=counts.get)

    def is_body(p):
        r, g, b, a = p
        return a > 128 and abs(r - body[0]) + abs(g - body[1]) + abs(b - body[2]) < 90

    mask = [[is_body(p) for p in row] for row in px]
    ys = [y for y, row in enumerate(mask) if any(row)]
    xs = [x for row in mask for x, v in enumerate(row) if v]
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    cw, ch = (x1 - x0) / grid_w, (y1 - y0) / grid_h
    return [[mask[int(y0 + (gy + 0.5) * ch)][int(x0 + (gx + 0.5) * cw)]
             for gx in range(grid_w)] for gy in range(grid_h)]


# ---------------------------------------------------------------- drawing

class Canvas:
    def __init__(self):
        self.px = [[0] * W for _ in range(H)]

    def set(self, x, y, v=1):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = v

    def rect(self, x, y, w, h, v=1):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, v)

    def frame(self, x, y, w, h):
        self.rect(x, y, w, 1)
        self.rect(x, y + h - 1, w, 1)
        self.rect(x, y, 1, h)
        self.rect(x + w - 1, y, 1, h)


def draw_sprite(c, grid, dy=0, eyes_closed=False):
    oy = SPRITE_Y + dy
    for gy, row in enumerate(grid):
        for gx, on in enumerate(row):
            if on:
                c.rect(SPRITE_X + gx * SCALE, oy + gy * SCALE, SCALE, SCALE)
    if eyes_closed:
        # Eye cells are the holes in the head rows; close them to a thin line.
        for gy in range(2):
            for gx in range(1, GRID_W - 1):
                if not grid[gy][gx] and grid[gy][gx - 1] and grid[gy][gx + 1]:
                    x, y = SPRITE_X + gx * SCALE, oy + gy * SCALE
                    c.rect(x, y, SCALE, SCALE)
                    c.rect(x, y + SCALE // 2, SCALE, 1, 0)


def arm_cells(grid):
    """Cells of the left/right 'arms': columns that only exist in the widest rows."""
    widths = [sum(r) for r in grid]
    wide = [gy for gy, w in enumerate(widths) if w == max(widths)]
    left, right = [], []
    for gy in wide:
        for gx in range(GRID_W):
            if grid[gy][gx] and all(not grid[oy][gx] for oy in range(GRID_H) if oy not in wide):
                (left if gx < GRID_W // 2 else right).append((gx, gy))
    return left, right


def move_arm(grid, cells, dy):
    g = [row[:] for row in grid]
    for gx, gy in cells:
        g[gy][gx] = False
    for gx, gy in cells:
        if 0 <= gy + dy < GRID_H:
            g[gy + dy][gx] = True
    return g


def draw_exclaim_bubble(c):
    x, y, w, h = 22, 2, 24, 26
    c.frame(x, y, w, h)
    c.frame(x + 1, y + 1, w - 2, h - 2)
    c.rect(x + 9, y + 26, 6, 1)          # tail
    c.rect(x + 10, y + 27, 4, 1)
    c.rect(x + 11, y + 28, 2, 1)
    c.rect(x + 10, y + 5, 4, 11)          # "!"
    c.rect(x + 10, y + 18, 4, 4)


def draw_dots(c, n):
    for i in range(n):
        c.rect(16 + i * 14, 38, 6, 6)


def build_frames(grid):
    left, right = arm_cells(grid)
    frames = {}

    c = Canvas(); draw_sprite(c, grid); frames["idle"] = c.px
    c = Canvas(); draw_sprite(c, grid, eyes_closed=True); frames["blink"] = c.px

    for name, cells in (("tap_left", left), ("tap_right", right)):
        c = Canvas()
        draw_sprite(c, move_arm(grid, cells, 1), dy=1)
        frames[name] = c.px

    for i, (dots, dy) in enumerate(((1, 0), (2, -1), (3, 0), (0, -1))):
        c = Canvas()
        draw_dots(c, dots)
        draw_sprite(c, grid, dy=dy)
        frames[f"work_{i}"] = c.px

    for i, (dy, up, bubble) in enumerate(((0, left, True), (-6, right, True),
                                          (-10, left, False), (-6, right, False))):
        c = Canvas()
        if bubble:
            draw_exclaim_bubble(c)
        draw_sprite(c, move_arm(grid, up, -2), dy=dy)
        frames[f"need_{i}"] = c.px

    return frames


# ---------------------------------------------------------------- output

def rotate_cw(px):
    """Portrait -> native: rotate 90 degrees clockwise (portrait top becomes native right)."""
    h, w = len(px), len(px[0])
    return [[px[h - 1 - x][y] for x in range(h)] for y in range(w)]


def preview(grid, frames):
    print("sprite grid:")
    for row in grid:
        print("  " + "".join("#" if v else "." for v in row))
    names = list(frames)
    for i in range(0, len(names), 4):
        group = names[i:i + 4]
        print()
        print("   ".join(n.center(W) for n in group))
        for y in range(0, H, 2):
            line = []
            for n in group:
                top = frames[n][y]
                bot = frames[n][y + 1] if y + 1 < H else [0] * W
                line.append("".join(" ▀▄█"[t + 2 * b] for t, b in zip(top, bot)))
            print("   ".join(line))


def to_c(frames):
    out = [
        "/* Generated by tools/gen_mascot.py - do not edit by hand.",
        " * Mascot sprite: Clawd, from github.com/afspies/clawdmoji (MIT). */",
        "",
        "#include <lvgl.h>",
        "",
        "#ifndef LV_ATTRIBUTE_MEM_ALIGN",
        "#define LV_ATTRIBUTE_MEM_ALIGN",
        "#endif",
        "",
    ]
    for name, frame in frames.items():
        name = f"mascot_{name}"
        native = rotate_cw(frame)
        nh, nw = len(native), len(native[0])
        stride = (nw + 7) // 8
        data = []
        for row in native:
            for b in range(stride):
                byte = 0
                for bit in range(8):
                    x = b * 8 + bit
                    if x < nw and row[x]:
                        byte |= 0x80 >> bit
                data.append(byte)
        out += [
            f"const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST uint8_t {name}_map[] = {{",
            "#if CONFIG_NICE_VIEW_WIDGET_INVERTED",
            "    0x00, 0x00, 0x00, 0xff, /*Color of index 0*/",
            "    0xff, 0xff, 0xff, 0xff, /*Color of index 1*/",
            "#else",
            "    0xff, 0xff, 0xff, 0xff, /*Color of index 0*/",
            "    0x00, 0x00, 0x00, 0xff, /*Color of index 1*/",
            "#endif",
            "",
        ]
        for i in range(0, len(data), 15):
            out.append("    " + " ".join(f"0x{v:02x}," for v in data[i:i + 15]))
        out += [
            "};",
            "",
            f"const lv_image_dsc_t {name} = {{",
            "    .header.cf = LV_COLOR_FORMAT_I1,",
            f"    .header.w = {nw},",
            f"    .header.h = {nh},",
            f"    .data_size = {8 + len(data)},",
            f"    .data = {name}_map,",
            "};",
            "",
        ]
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, default=SOURCE, help="mascot PNG (default: %(default)s)")
    ap.add_argument("--grid", default=f"{GRID_W}x{GRID_H}", help="pixel-art grid size, WxH")
    ap.add_argument("--preview", action="store_true", help="print the frames instead of writing C")
    args = ap.parse_args()

    gw, gh = (int(v) for v in args.grid.lower().split("x"))
    if (gw, gh) != (GRID_W, GRID_H):
        ap.error("frame layout is tuned for a 12x8 sprite")
    sprite = load_sprite(args.source, gw, gh)
    frames = build_frames(sprite)
    if args.preview:
        preview(sprite, frames)
    else:
        OUT.write_text(to_c(frames))
        print(f"wrote {OUT} ({len(frames)} frames)")
