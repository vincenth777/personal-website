#!/usr/bin/env python3
"""Convert manana.jpg into a colored-ASCII data file for the website.

Mirrors the idea behind zixihong/portfolio-3.0's generate-ascii.ts:
each cell gets a character (by brightness) and keeps its true color.
Distinct scene objects become clickable nav regions.
"""
import json
import math
from collections import deque
from PIL import Image

SRC = "manana.jpg"
OUT = "ascii-data.js"

COLS = 220
CHAR_ASPECT = 2.05          # monospace cell height / width
QUANT = 20                  # color quantization step (fewer spans, cleaner runs)
BOOST = 1.14                # brighten colors for a black background

# light -> dense: brighter pixels get denser ink so bright cliff/clouds pop on black
RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

# 4x4 Bayer matrix for ordered dithering (breaks up banding in thinned areas)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def lum(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def quant(v):
    return min(255, (v // QUANT) * QUANT + QUANT // 2)


def is_land(r, g, b):
    # land (green vegetation / tan cliff / red-brown rock): warm, red or green
    # at least matches blue. Even shadowed island greens satisfy this; only the
    # clearly blue-dominant sky & ocean are excluded. Loose enough to keep the
    # whole island connected as one flood-fill component.
    l = lum(r, g, b)
    # Land (green vegetation / tan cliff / red-brown rock) is a warm, saturated
    # color. Requiring saturation excludes the near-white surf between the two
    # islands (neutral: r~=g~=b) that would otherwise bridge them into one blob,
    # and excludes the blue-dominant sky and ocean.
    warm = max(r, g) >= b and max(r, g) > 48
    saturated = (max(r, g, b) - min(r, g, b)) >= 12
    return warm and saturated and l > 34


def main():
    img = Image.open(SRC).convert("RGB")
    w, h = img.size
    cell_w = w / COLS
    cell_h = cell_w * CHAR_ASPECT
    rows = int(h / cell_h)
    small = img.resize((COLS, rows), Image.LANCZOS)
    px = small.load()

    n = COLS * rows
    chars = [" "] * n
    colors = [""] * n
    land_mask = [False] * n
    sky_mask = [False] * n
    lum_map = [0.0] * n

    for y in range(rows):
        for x in range(COLS):
            r, g, b = px[x, y]
            i = y * COLS + x
            l = lum(r, g, b)
            lum_map[i] = l
            land = is_land(r, g, b)
            bright_sky = (not land) and l > 120 and y < rows * 0.5
            if land:
                land_mask[i] = True
            elif bright_sky:
                sky_mask[i] = True

            # Density modulation: density tracks the *subject*, not brightness,
            # so the island floats on negative space (the reference aesthetic).
            #  - island (land): full ink -> solid subject
            #  - sky: driven by whiteness, so plain blue sky is ~empty and only
            #         the wispy clouds stipple in
            #  - ocean: heavily thinned -> a faint ripple texture
            base = l / 255.0
            if land:
                shade = min(1.0, base * 1.2)
            elif bright_sky:
                # only genuine clouds (whitish, high min channel) stipple in;
                # plain blue sky falls to black so the island floats
                whiteness = min(r, g, b) / 255.0
                shade = (whiteness - 0.60) / 0.30
            else:
                shade = (base ** 1.7) * 0.6   # ocean ripple (dark water is interactive)
            # ordered dither to avoid flat banding in the thinned regions
            shade += (BAYER[y % 4][x % 4] / 16.0 - 0.5) * 0.05
            shade = 0.0 if shade < 0 else 1.0 if shade > 1 else shade

            ci = int(shade * (len(RAMP) - 1))
            ch = RAMP[ci]
            if ch != " ":
                cr = min(255, int(quant(r) * BOOST))
                cg = min(255, int(quant(g) * BOOST))
                cb = min(255, int(quant(b) * BOOST))
                chars[i] = ch
                colors[i] = "#%02x%02x%02x" % (cr, cg, cb)

    # ---- flood fill land to de-speckle (drop isolated surf/glint pixels) ----
    visited = [False] * n
    land_cells = []
    for start in range(n):
        if not land_mask[start] or visited[start]:
            continue
        q = deque([start])
        visited[start] = True
        cells = []
        while q:
            idx = q.popleft()
            cells.append(idx)
            cy, cx = divmod(idx, COLS)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < rows and 0 <= nx < COLS:
                        ni = ny * COLS + nx
                        if land_mask[ni] and not visited[ni]:
                            visited[ni] = True
                            q.append(ni)
        if len(cells) >= 20:      # keep only real landmasses
            land_cells.extend(cells)

    # ---- assign land to regions by the natural split line between the two
    # islands. The main island (Manana) sits at rows < SPLIT; the low foreground
    # islet (Kaohikaipu) sits at rows >= SPLIT. This is robust because the
    # near-white surf makes the two masses touch, defeating pure connectivity.
    SPLIT = 35
    regions = [None] * n
    about_ct = writing_ct = 0
    for idx in land_cells:
        if chars[idx] == " ":
            continue
        y = idx // COLS
        if y < SPLIT:
            regions[idx] = "about"       # Manana, the main island
            about_ct += 1
        else:
            regions[idx] = "writing"     # Kaohikaipu, the front islet
            writing_ct += 1

    # ---- sky -> outside (only cells that actually drew ink) ----
    sky_count = 0
    for i in range(n):
        if sky_mask[i] and chars[i] != " " and regions[i] is None:
            regions[i] = "outside"
            sky_count += 1

    # ---- favorites -> a jagged 45-degree wedge in the bottom-left water ----
    # The diagonal meets the left edge at FAV_APEX and opens down-right. Cells
    # are CHAR_ASPECT times taller than wide, so advancing CHAR_ASPECT columns
    # per row is a true 45 degrees on screen. A little sine jitter keeps the
    # edge jagged/wave-bitten rather than a ruled line.
    FAV_APEX = int(rows * 0.55)
    fav_count = 0
    for i in range(n):
        if regions[i] is not None or chars[i] == " ":
            continue
        y, x = divmod(i, COLS)
        if y < FAV_APEX:
            continue
        edge = (y - FAV_APEX) * CHAR_ASPECT
        edge += 3.5 * math.sin(y * 1.7) + 2.0 * math.sin(y * 0.6 + 1.3)
        if x <= edge:
            regions[i] = "favorites"
            fav_count += 1

    data = {
        "cols": COLS,
        "rows": rows,
        "chars": "".join(chars),
        "colors": colors,
        "regions": regions,
    }
    with open(OUT, "w") as f:
        f.write("window.ASCII_DATA = ")
        json.dump(data, f, separators=(",", ":"))
        f.write(";\n")

    print("grid %dx%d (%d cells)" % (COLS, rows, n))
    print("about: %d  writing: %d  outside: %d  favorites: %d"
          % (about_ct, writing_ct, sky_count, fav_count))
    print("wrote %s (%.2f MB)" % (OUT, len(json.dumps(data)) / 1048576))


if __name__ == "__main__":
    main()
