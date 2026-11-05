#!/usr/bin/env python3
"""Generate the bongo cat frames for the nice_view_lgtm shield.

The frames are drawn upright in portrait coordinates (as seen on the keyboard),
then rotated 90 degrees clockwise into the panel's native landscape orientation
and written as LVGL 1-bit indexed images (LV_COLOR_FORMAT_I1).

    python3 tools/gen_bongo.py --preview   # print the frames
    python3 tools/gen_bongo.py             # write boards/shields/nice_view_lgtm/assets/bongo.c
"""

import argparse
import math
from pathlib import Path

W, H = 68, 120  # portrait frame size
OUT = Path(__file__).resolve().parent.parent / "boards/shields/nice_view_lgtm/assets/bongo.c"


class Canvas:
    def __init__(self):
        self.px = [[0] * W for _ in range(H)]

    def set(self, x, y, v=1):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = v

    def line(self, x0, y0, x1, y1, v=1):
        x0, y0, x1, y1 = (int(round(c)) for c in (x0, y0, x1, y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, v)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def poly(self, pts, v=1):
        for a, b in zip(pts, pts[1:]):
            self.line(*a, *b, v)

    def fill_ellipse(self, cx, cy, rx, ry, v=1):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.set(x, y, v)

    def ellipse(self, cx, cy, rx, ry, v=1, a0=0, a1=360):
        steps = int(4 * (rx + ry)) + 8
        prev = None
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            p = (cx + rx * math.cos(a), cy + ry * math.sin(a))
            if prev:
                self.line(*prev, *p, v)
            prev = p

    def blob(self, cx, cy, rx, ry):
        """Opaque outlined ellipse (clears what is behind it)."""
        self.fill_ellipse(cx, cy, rx, ry, 0)
        self.ellipse(cx, cy, rx, ry)

    def fill_poly(self, pts, v=1):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(math.ceil(a)), int(math.floor(b)) + 1):
                    self.set(x, y, v)


# Layout (portrait)
HEAD_CX, HEAD_CY, HEAD_RX, HEAD_RY = 34, 44, 25, 19
DESK_Y = 101
DRUMS = (19, 49)  # viewer-left drum, viewer-right drum
DRUM_TOP_Y, DRUM_RX, DRUM_RY = 85, 12, 4
PAW_UP = ((9, 70), (59, 70))
PAW_DOWN = ((19, 82), (49, 82))
SHOULDER = ((13, 66), (55, 66))


def draw_frame(tap):
    """tap: None (idle), 0 (viewer-left paw down) or 1 (viewer-right paw down)."""
    c = Canvas()

    # Body, sitting behind the desk
    c.line(14, 58, 6, DESK_Y)
    c.line(54, 58, 62, DESK_Y)

    # Ears (drawn before the head so the head covers their base)
    left_ear = [(12, 40), (13, 14), (31, 28)]
    right_ear = [(2 * HEAD_CX - x, y) for x, y in left_ear]
    for ear in (left_ear, right_ear):
        c.fill_poly(ear, 0)
        c.poly(ear + ear[:1])
        # inner ear
        ix = sum(p[0] for p in ear) / 3
        iy = sum(p[1] for p in ear) / 3
        c.poly([(ix + (x - ix) * 0.45, iy + (y - iy) * 0.45) for x, y in ear[:2]])

    # Head
    c.blob(HEAD_CX, HEAD_CY, HEAD_RX, HEAD_RY)

    # Eyes: open when idle, happy squint while drumming
    for ex in (24, 44):
        if tap is None:
            c.fill_ellipse(ex, 43, 2.2, 2.6)
        else:
            c.poly([(ex - 3, 44), (ex, 41), (ex + 3, 44)])

    # Nose + ":3" mouth
    c.line(33, 48, 35, 48)
    c.set(34, 49)
    c.poly([(29, 51), (31, 53), (34, 50), (37, 53), (39, 51)])

    # Whiskers
    for dy in (-1, 2):
        c.line(14, 47 + dy, 4, 46 + dy * 2)
        c.line(54, 47 + dy, 64, 46 + dy * 2)

    # Desk
    c.line(0, DESK_Y, W - 1, DESK_Y)
    c.line(0, DESK_Y + 1, W - 1, DESK_Y + 1)

    # Bongos standing on the desk
    for i, dx in enumerate(DRUMS):
        top_y = DRUM_TOP_Y + (1 if tap == i else 0)  # drum skin dips when hit
        c.fill_poly([(dx - DRUM_RX, top_y), (dx + DRUM_RX, top_y),
                     (dx + 9, DESK_Y), (dx - 9, DESK_Y)], 0)
        c.line(dx - DRUM_RX, top_y, dx - 9, DESK_Y)
        c.line(dx + DRUM_RX, top_y, dx + 9, DESK_Y)
        c.blob(dx, top_y, DRUM_RX, DRUM_RY)
        c.ellipse(dx, top_y + 7, DRUM_RX - 1, DRUM_RY - 1, a0=0, a1=180)  # drum band
    c.line(DRUMS[0] + 10, 93, DRUMS[1] - 10, 93)  # bracket between drums
    c.line(DRUMS[0] + 10, 94, DRUMS[1] - 10, 94)

    # Paws
    for i in (0, 1):
        sx, sy = SHOULDER[i]
        if tap == i:
            px, py = PAW_DOWN[i]
            c.line(sx - 3, sy, px - 4, py)
            c.line(sx + 3, sy, px + 4, py)
            c.blob(px, py, 6, 4)
            # impact lines on the outer side of the drum
            out = -1 if i == 0 else 1
            ox = px + out * 9
            for k in range(3):
                c.line(ox + out * 2 * k, py - 7 + 2 * k, ox + out * (2 * k + 3), py - 9 + 2 * k)
        else:
            px, py = PAW_UP[i]
            c.blob(px, py, 6, 5)
            # toe beans
            for tx in (-2, 0, 2):
                c.set(px + tx, py - 2)
    return c.px


# Drop the empty margin above the ears and below the desk
CROP_TOP, CROP_BOTTOM = 8, 106
FRAMES = {
    name: draw_frame(tap)[CROP_TOP:CROP_BOTTOM]
    for name, tap in (("bongo_idle", None), ("bongo_left", 0), ("bongo_right", 1))
}


def rotate_cw(px):
    """Portrait -> native: rotate 90 degrees clockwise (portrait top becomes native right)."""
    h, w = len(px), len(px[0])
    return [[px[h - 1 - x][y] for x in range(h)] for y in range(w)]


def preview():
    names = list(FRAMES)
    print("   ".join(n.center(W // 1) for n in names))
    h = len(FRAMES[names[0]])
    for y in range(0, h, 2):
        row = []
        for n in names:
            top, bot = FRAMES[n][y], FRAMES[n][y + 1] if y + 1 < h else [0] * W
            row.append("".join(" ▀▄█"[t + 2 * b] for t, b in zip(top, bot)))
        print("   ".join(row))


def to_c():
    out = [
        "/* Generated by tools/gen_bongo.py - do not edit by hand. */",
        "",
        "#include <lvgl.h>",
        "",
        "#ifndef LV_ATTRIBUTE_MEM_ALIGN",
        "#define LV_ATTRIBUTE_MEM_ALIGN",
        "#endif",
        "",
    ]
    for name, frame in FRAMES.items():
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
    ap.add_argument("--preview", action="store_true", help="print the frames instead of writing C")
    args = ap.parse_args()
    if args.preview:
        preview()
    else:
        OUT.write_text(to_c())
        print(f"wrote {OUT}")
