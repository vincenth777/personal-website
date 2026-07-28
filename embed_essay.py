#!/usr/bin/env python3
"""Embed the essay from the .docx directly into the Writing panel of index.html.

Replaces the essay body + header in the existing `panel article` block.
CSS for the article layout already lives in index.html, so it is NOT re-injected.
"""
import zipfile, re, html

DOCX = "Moral Philosophy 2.docx"
HTML = "index.html"
DATE = "May 2024"

HEADERS = {3, 11, 15}   # section headings
BLOCKQUOTE = {1}        # the evolutionary debunking argument
STEPS = {8, 9, 10}      # the formal reflective-equilibrium steps

# ---- extract paragraphs from the docx ----
xml = zipfile.ZipFile(DOCX).read("word/document.xml").decode("utf-8")
paras = []
for chunk in re.split(r"</w:p>", xml):
    text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", chunk, re.S))
    text = html.unescape(text).strip()
    if text:
        paras.append(text)

TITLE = paras[0]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---- build the essay body ----
lines = []
for i, p in enumerate(paras):
    if i == 0:
        continue
    t = esc(p)
    if i in HEADERS:
        lines.append("      <h2>%s</h2>" % t)
    elif i in BLOCKQUOTE:
        lines.append("      <blockquote>%s</blockquote>" % t)
    elif i in STEPS:
        lines.append('      <p class="step">%s</p>' % t)
    else:
        lines.append("      <p>%s</p>" % t)
body = "\n".join(lines)

panel = (
    '  <div class="panel article" id="panel-essay">\n'
    '    <div class="inner">\n'
    '      <div class="label">Kāohikaipu &middot; Writing</div>\n'
    '      <h1>' + esc(TITLE) + '</h1>\n'
    '      <div class="meta">' + DATE + '</div>\n'
    + body + '\n'
    '      <span class="back" data-back>&larr; back</span>\n'
    '    </div>\n'
    '  </div>'
)

# ---- rewrite only the writing panel block ----
src = open(HTML, encoding="utf-8").read()
new_src, n = re.subn(
    r'  <div class="panel[^"]*" id="panel-essay">.*?</div>\s*</div>',
    lambda m: panel,
    src, count=1, flags=re.S,
)
assert n == 1, "essay panel block not found"
open(HTML, "w", encoding="utf-8").write(new_src)
print("embedded revised essay (%d paragraphs) into %s" % (len(paras), HTML))
