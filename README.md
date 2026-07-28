# personal-website

A minimalist personal site for Vince Huang. Black canvas, `JetBrains Mono`, a
colored-ASCII rendering of **Mānana (Rabbit Island)** off the windward coast of
O'ahu as the hero. Distinct objects in the scene are the navigation:

- **Mānana (the island)** → About
- **Kāohikaipu (the front islet)** → Writing
- **the clouds** → Outside

Hover an object and it lights up, tiling its section name across itself; click to
open that section. Built as a single self-contained page.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The entire site (markup, styles, interaction). |
| `ascii-data.js` | Generated colored-ASCII grid (`window.ASCII_DATA`). |
| `convert.py` | Regenerates `ascii-data.js` from `manana.jpg`. |
| `embed_essay.py` | Embeds an essay `.docx` into the Writing panel. |
| `manana.jpg` | Source photo for the ASCII scene. |
| `*_web.jpg` | EXIF-stripped, web-optimized photos for the Outside gallery. |

## Regenerating the ASCII

```bash
pip install pillow
python3 convert.py        # rewrites ascii-data.js from manana.jpg
```

## Running

It's a static page — open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server
```
