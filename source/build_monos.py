"""
Ferry VN Mono 0.9 — JetBrains Mono Nerd Font Mono (OFL) + Ferry VN signature + Ferry icon set.
  * Ferry 'screen' details from Ferry VN Text: soft corner on A apex, L, F (+ tabs), U-curve Y.
    No gliding feet: Mono, like Text, is a screen face; feet belong to Display.
  * JetBrains Mono already carries the rest of the idea: rounded-rectangle bowls (screen curve),
    l with a forward tail, dotted zero. Kept as is.
  * Ferry icons U+E100–U+E10C, one cell wide, Nerd-Font style, in a range Nerd Fonts leaves empty.
  * Original JetBrains Mono hinting is kept; only the reshaped glyphs and new icons are unhinted.
"""
import math, os, unicodedata, importlib.util
def load(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ft = load("ft", "ferry_tools.py"); bt = load("bt", "build_text.py"); fi = load("fi", "ferry_icons.py")
ft = bt.ft; b2 = bt.b2   # one module instance, so Raw contours are recognised
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.cu2quPen import Cu2QuPen

import sys
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "nerd"
if VARIANT == "plain":
    SRC = "/home/claude/mono/jbm/fonts/ttf/JetBrainsMono-{}.ttf"; FAM = "Ferry VN Mono"; PREFIX = "FerryVNMono"
    BASE_DESC = "JetBrains Mono 2.304 (SIL OFL 1.1)"
else:
    SRC = "/home/claude/mono/src/JetBrainsMonoNerdFontMono-{}.ttf"; FAM = "Ferry VN Nerd Mono"; PREFIX = "FerryVNNerdMono"
    BASE_DESC = "JetBrains Mono 2.304 (SIL OFL 1.1) patched by Nerd Fonts 3.5.1"
OUT = "/home/claude/fonts/release/"; os.makedirs(OUT, exist_ok=True)
JOBS = [("Regular", "Regular", 400, 0, 70, (FAM, "Regular")), ("Medium", "Medium", 500, 0, 78, (FAM + " Medium", "Regular")),
        ("Bold", "Bold", 700, 0, 90, (FAM, "Bold")), ("Italic", "Italic", 400, 9, 70, (FAM, "Italic")),
        ("BoldItalic", "Bold Italic", 700, 9, 90, (FAM, "Bold Italic"))]
bt.CAP = 730

def empty_program(g):
    g.program = ttProgram.Program(); g.program.fromBytecode(b"")

for src, style, wc, slant, icon_w, (n1, n2) in JOBS:
    f = TTFont(SRC.format(src)); gs = f.getGlyphSet(); glyf = f["glyf"]; hmtx = f["hmtx"]; cmap = f.getBestCmap()
    tan = math.tan(math.radians(slant))
    def getp(name):
        p = b2.to_path(gs, name); return ft.slant_path(p, -tan) if tan else p
    H = getp(cmap[ord("H")]); r = b2.runs_x(H, 600, H.bounds[0], H.bounds[2])[0]
    E = getp(cmap[ord("E")]); eb = E.bounds
    M = {"stem": r[1] - r[0], "hbar": b2.runs_y(E, (eb[0] + eb[2]) / 2 + 40, 0, 400)[0][1]}
    targets = {g: unicodedata.normalize("NFD", chr(cp))[0] for cp, g in cmap.items()
               if cp < 0x2000 and unicodedata.normalize("NFD", chr(cp))[0] in set("ALFY")}
    built = {}
    for name, base in targets.items():
        MR = dict(M, stem=max(M["stem"] * 1.25, 115))      # radii a notch larger than Text so the details survive at code sizes
        cs, extra = bt.text_glyph(getp, name, base, MR); assert extra == 0
        pen = TTGlyphPen(None); cq = Cu2QuPen(pen, max_err=1.0, reverse_direction=False)
        b2.draw_contours(cs, TransformPen(cq, (1, 0, tan, 1, 0, 0)) if tan else cq)
        built[name] = pen.glyph()
    for name, g in built.items():
        glyf[name] = g; empty_program(g)
    # icons: upright in every style, one cell wide
    ic = fi.icons(icon_w)
    for name in fi.ORDER:
        g = fi.to_glyph(ic[name]); empty_program(g)
        ft.add_glyph(f, name, g, 600, unicode=fi.CODEPOINTS[name])
    for name in list(built) + fi.ORDER:
        g = glyf[name]; g.recalcBounds(glyf); hmtx[name] = (hmtx[name][0], g.xMin if g.numberOfContours else 0)
    # names
    nm = f["name"]; full = f"{FAM} {style}"; ps = (FAM + "-" + style).replace(" ", "")
    for nid in (1, 2, 3, 4, 5, 6, 16, 17, 21, 22, 25): nm.removeNames(nameID=nid)
    f["head"].fontRevision = 1.0
    for nid, val in [(1, n1), (2, n2), (3, f"1.000;FVN;{ps}"), (4, full), (5, "Version 1.000"), (6, ps), (16, FAM), (17, style)]:
        nm.setName(val, nid, 3, 1, 0x409)
    nm.setName(f"{FAM}: {BASE_DESC}, with Ferry VN signature details and Ferry icons at U+E100-U+E10C.", 10, 3, 1, 0x409)
    o = f["OS/2"]; o.usWeightClass = wc; fs = o.fsSelection & ~(0x01 | 0x20 | 0x40)
    if "Bold" in n2: fs |= 0x20
    if "Italic" in n2: fs |= 0x01
    if not (fs & 0x21): fs |= 0x40
    o.fsSelection = fs; f["head"].macStyle = (0x01 if "Bold" in n2 else 0) | (0x02 if "Italic" in n2 else 0)
    p = OUT + f"{PREFIX}-{style.replace(' ', '')}.ttf"; f.save(p)
    advs = {f["hmtx"][n][0] for n in f.getGlyphOrder()}
    print(style, M, "reshaped", len(built), "advances", sorted(advs))
