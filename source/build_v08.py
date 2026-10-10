"""Ferry VN 0.7 — narrower proportions (heavier source scaled horizontally), lighter squircle."""
import math, os, importlib.util
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
ft = load("ft", "ferry_tools.py"); sq = load("sq", "squircle.py")
bt = load("bt", "build_text.py"); v6 = None
b2 = ft.b2
from fontTools.ttLib import TTFont
SD = "/home/claude/fonts/c8D/BeVietnamPro-{}.ttf"; ST = "/home/claude/fonts/c8T/BeVietnamPro-{}.ttf"
b2.SRC = SD
VER = "0.8"

def set_version(f):
    for n in f["name"].names:
        if n.nameID == 3:
            s = n.toUnicode()
            for old in ("0.3;", "0.4;", "0.5;", "0.6;", "0.7;"): s = s.replace(old, VER + ";")
            n.string = s

def ribbi(p, n1, n2):
    f = TTFont(p); nm = f["name"]
    nm.removeNames(nameID=1); nm.removeNames(nameID=2); nm.setName(n1, 1, 3, 1, 0x409); nm.setName(n2, 2, 3, 1, 0x409)
    o = f["OS/2"]; fs = o.fsSelection & ~(0x01 | 0x20 | 0x40)
    if "Bold" in n2: fs |= 0x20
    if "Italic" in n2: fs |= 0x01
    if not (fs & 0x21): fs |= 0x40
    o.fsSelection = fs; f["head"].macStyle = (0x01 if "Bold" in n2 else 0) | (0x02 if "Italic" in n2 else 0)
    f.save(p)

def sheared_copy(src, dst, deg):
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    f = TTFont(src); gs = f.getGlyphSet(); tan = math.tan(math.radians(deg)); new = {}
    for n in f.getGlyphOrder():
        pen = TTGlyphPen(None); rec = DecomposingRecordingPen(gs); gs[n].draw(rec)
        rec.replay(TransformPen(pen, (1, 0, tan, 1, 0, 0))); new[n] = pen.glyph()
    for n, g in new.items(): f["glyf"][n] = g
    for n in f.getGlyphOrder():
        g = f["glyf"][n]; g.recalcBounds(f["glyf"]); f["hmtx"][n] = (f["hmtx"][n][0], g.xMin if g.numberOfContours else 0)
    f.save(dst)

# ---------- Display ----------
SQ_D = (0.30, 0.36)
FAM = "Ferry VN Display"
outD = "/home/claude/fonts/display8/"; os.makedirs(outD, exist_ok=True)
spec = [("Light", "Light", 0, 300, (FAM + " Light", "Regular")), ("Regular", "Regular", 0, 400, (FAM, "Regular")),
        ("Bold", "Bold", 0, 700, (FAM, "Bold")), ("Black", "Black", 0, 900, (FAM + " Black", "Regular")),
        ("Bold", "Bold Oblique", 8.2, 700, (FAM, "Bold Italic"))]
for src, style, slant, wc, (n1, n2) in spec:
    p = outD + "FerryVNDisplay-" + style.replace(" ", "") + ".ttf"
    M, n = b2.build(src, p, FAM, style, slant, wc)
    ribbi(p, n1, n2)
    f = TTFont(p); sq.squircle_font(f, *SQ_D, slant_tan=math.tan(math.radians(slant)) if slant else 0.0)
    ft.add_arrows(f); set_version(f); f.save(p)
    ref = SD.format(src)
    if slant:
        ref = "/home/claude/test/c8D-Bold-sheared.ttf"; sheared_copy(SD.format("Bold"), ref, slant)
    u = max(M["stem"], 0.16 * 740); ext = 0.42 * u
    rep = ft.kern_feet(p, ref, list("ARKkl"), {"A": ext, "R": ext, "K": ext, "k": ext, "l": 0.78 * u * 0.8}, p)
    ft.autohint(p)
    print("Display", style, M, "kern", len(rep))

# ---------- Text ----------
SQ_T = (0.18, 0.22)
outT = "/home/claude/fonts/text8/"; os.makedirs(outT, exist_ok=True)
jobs = [("Regular", "Regular", 400, 0), ("Medium", "Medium", 500, 0), ("SemiBold", "SemiBold", 600, 0), ("Bold", "Bold", 700, 0),
        ("Italic", "Italic", 400, 12), ("MediumItalic", "Medium Italic", 500, 12),
        ("SemiBoldItalic", "SemiBold Italic", 600, 12), ("BoldItalic", "Bold Italic", 700, 12)]
for src, style, wc, it in jobs:
    p = outT + "FerryVNText-" + style.replace(" ", "") + ".ttf"
    M, lx, W = bt.build_text(ST.format(src), p, "Ferry VN Text", style, wc, it)
    f = TTFont(p); sq.squircle_font(f, *SQ_T, slant_tan=math.tan(math.radians(it)) if it else 0.0)
    set_version(f); f.save(p)
    rep = ft.kern_feet(p, ST.format(src), ["l"], {"l": lx}, p)
    ft.autohint(p, increase_x_height=14)
    print("Text", style, M, "tnumW", W, "kern", len(rep))
