"""
Ferry VN Text 0.5 — body/UI companion to Ferry VN Display. Derivative of Be Vietnam Pro (SIL OFL 1.1).
Big idea: "Đọc đúng ngay lần đầu" — the display signature becomes function.
  l tail (l/I/1), text-scaled soft corners, no gliding feet, tnum, slashed zero, arrows, ttfautohint.
0.5: italics (built in unslanted space, then re-slanted 12°), tabular width that keeps the 4 breathing,
     → ← arrows, pair kerning for the l tail.
"""
import math, os, sys, unicodedata, importlib.util
spec = importlib.util.spec_from_file_location("ft", "ferry_tools.py")
ft = importlib.util.module_from_spec(spec); spec.loader.exec_module(ft)
b2 = ft.b2
import pathops
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot, ttProgram
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen

CAP = 740
SIG_T = set("ALFYl")

def text_glyph(getp, name, base, M):
    p = getp(name); stem, hbar = M["stem"], M["hbar"]; extra = 0
    if base == "l":
        cs = b2.contours_of(p); bs = b2.bottom_segments(cs)
        if bs:
            x0, x1 = min(bs, key=lambda t: t[0])
            ext, h = stem * 0.95, hbar * 0.88
            p = b2.union(p, b2.rect(x0 + 3, 0, x1 + ext, h)); cs = b2.contours_of(p)
            b2.round_at(cs, (x1, h), stem * 0.38, "reflex", tol=4)
            b2.round_at(cs, (x0, 0), stem * 0.45, "convex", tol=4)
            b2.round_at(cs, (x1 + ext, h), stem * 0.30, "convex", tol=4)
            extra = ext * 0.72
        return cs, extra
    cs = b2.contours_of(p); vs = b2.base_vertices(cs, CAP)
    if not vs: return cs, 0
    xs = [v[2][0] for v in vs]; xmin, xmax = min(xs), max(xs)
    if base == "A":
        tops = [v for v in vs if v[3] == "convex" and v[2][1] >= CAP - 3]
        if tops: b2.round_at(cs, min(tops, key=lambda v: v[2][0])[2], stem * 0.42, "convex")
    elif base == "L":
        q = b2.nearest(vs, (xmin, 0), "convex");     q and b2.round_at(cs, q, stem * 0.42, "convex")
        q = b2.nearest(vs, (xmax, hbar), "convex");  q and b2.round_at(cs, q, stem * 0.32, "convex")
    elif base == "F":
        q = b2.nearest(vs, (xmin, CAP), "convex");   q and b2.round_at(cs, q, stem * 0.42, "convex")
        c = [v for v in vs if v[3] == "convex" and CAP - hbar * 1.6 < v[2][1] < CAP - 10]
        if c: b2.round_at(cs, max(c, key=lambda v: v[2][0])[2], stem * 0.32, "convex")
    elif base == "Y":
        c = [v for v in vs if v[3] == "reflex" and CAP * 0.15 < v[2][1] < CAP * 0.45]
        for v in c: b2.round_at(cs, v[2], stem * 0.7, "reflex")
    return cs, 0

def add_feature(f, tag, mapping):
    g = f["GSUB"].table
    lk = ot.Lookup(); lk.LookupType = 1; lk.LookupFlag = 0
    st = ot.SingleSubst(); st.mapping = dict(mapping); lk.SubTable = [st]; lk.SubTableCount = 1
    g.LookupList.Lookup.append(lk); g.LookupList.LookupCount = len(g.LookupList.Lookup)
    li = len(g.LookupList.Lookup) - 1
    recs = g.FeatureList.FeatureRecord
    pos = sum(1 for r in recs if r.FeatureTag <= tag)
    fr = ot.FeatureRecord(); fr.FeatureTag = tag
    fr.Feature = ot.Feature(); fr.Feature.FeatureParams = None
    fr.Feature.LookupListIndex = [li]; fr.Feature.LookupCount = 1
    recs.insert(pos, fr); g.FeatureList.FeatureCount = len(recs)
    for sr in g.ScriptList.ScriptRecord:
        for ls in [sr.Script.DefaultLangSys] + [l.LangSys for l in sr.Script.LangSysRecord]:
            if ls is None: continue
            ls.FeatureIndex = sorted([i + 1 if i >= pos else i for i in ls.FeatureIndex] + [pos])
            ls.FeatureCount = len(ls.FeatureIndex)
            if ls.ReqFeatureIndex != 0xFFFF and ls.ReqFeatureIndex >= pos: ls.ReqFeatureIndex += 1

def build_text(src_file, out_path, family, style, weight_class, italic_deg=0.0):
    f = TTFont(src_file)
    gs = f.getGlyphSet(); glyf = f["glyf"]; hmtx = f["hmtx"]; cmap = f.getBestCmap()
    tan = math.tan(math.radians(italic_deg))
    def getp(name):                                   # work in upright space
        p = b2.to_path(gs, name)
        return ft.slant_path(p, -tan) if tan else p
    def put(name, path_or_cs):
        pen = TTGlyphPen(None); tgt = TransformPen(pen, (1, 0, tan, 1, 0, 0)) if tan else pen
        if isinstance(path_or_cs, list): b2.draw_contours(path_or_cs, tgt)
        else: path_or_cs.draw(tgt)
        return pen.glyph()

    H = getp(cmap[ord("H")]); r = b2.runs_x(H, 600, H.bounds[0], H.bounds[2])[0]
    E = getp(cmap[ord("E")]); eb = E.bounds
    M = {"stem": r[1] - r[0], "hbar": b2.runs_y(E, (eb[0] + eb[2]) / 2 + 40, 0, 400)[0][1]}

    targets = {g: unicodedata.normalize("NFD", chr(cp))[0] for cp, g in cmap.items()
               if unicodedata.normalize("NFD", chr(cp))[0] in SIG_T}
    built = {n: text_glyph(getp, n, base, M) for n, base in targets.items()}
    for n, (cs, extra) in built.items():
        glyf[n] = put(n, cs); hmtx[n] = (int(round(hmtx[n][0] + extra)), hmtx[n][1])
    l_extra = M["stem"] * 0.95 * 0.72

    # slashed zero
    z = cmap[ord("0")]; zp = getp(z); x0, y0, x1, y1 = zp.bounds
    th = M["stem"] * 0.62; w = x1 - x0
    ax, ay, bx, by = x0 + w * 0.30, y0 + (y1 - y0) * 0.22, x1 - w * 0.30, y1 - (y1 - y0) * 0.22
    nx, ny = -(by - ay), (bx - ax); L = math.hypot(nx, ny); nx, ny = nx / L * th / 2, ny / L * th / 2
    sl = b2.rect(0, 0, 1, 1); sl = pathops.Path(); pen = sl.getPen()
    pen.moveTo((ax - nx, ay - ny)); pen.lineTo((ax + nx, ay + ny)); pen.lineTo((bx + nx, by + ny)); pen.lineTo((bx - nx, by - ny)); pen.closePath()
    ft.add_glyph(f, "zero.slash", put("zero.slash", b2.union(zp, sl)), hmtx[z][0])

    # tabular figures: width = zero, widened only as far as needed so the widest digit keeps 70% of zero's sidebearings
    digits = [cmap[ord(c)] for c in "0123456789"]
    def ink(n):
        p = getp(n); return p.bounds[2] - p.bounds[0]
    sbz = (hmtx[z][0] - ink(z)) / 2
    W = int(math.ceil(max([hmtx[z][0]] + [ink(d) + 2 * 0.7 * sbz for d in digits])))
    tmap, zmap = {}, {z: "zero.slash"}
    for d in digits + ["zero.slash"]:
        # centre the ink (not the advance) so every tabular digit is optically centred
        p = getp(d); cx = (p.bounds[0] + p.bounds[2]) / 2
        dx = int(round(W / 2 - cx))
        pen = TTGlyphPen(f.getGlyphSet()); pen.addComponent(d, (1, 0, 0, 1, dx, 0))
        ft.add_glyph(f, d + ".tf", pen.glyph(), W)
        if d != "zero.slash": tmap[d] = d + ".tf"
    zmap[z + ".tf"] = "zero.slash.tf"
    add_feature(f, "tnum", tmap); add_feature(f, "zero", zmap)

    ft.add_arrows(f)

    for n in f.getGlyphOrder():
        g = glyf[n]; g.recalcBounds(glyf)
        hmtx[n] = (hmtx[n][0], g.xMin if g.numberOfContours else 0)
        if hasattr(g, "program"): g.program = ttProgram.Program(); g.program.fromBytecode(b"")
    for t in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX", "DSIG"):
        if t in f: del f[t]

    # naming / style linking
    f["OS/2"].usWeightClass = weight_class
    is_it = italic_deg != 0; wname = style.replace(" Italic", "").replace("Italic", "") or "Regular"
    rib_bold = wname == "Bold"; rib = wname in ("Regular", "Bold")
    n1 = family if rib else f"{family} {wname}"
    n2 = ("Bold " if rib_bold else "") + ("Italic" if is_it else ("Regular" if not rib_bold else ""))
    n2 = n2.strip() or "Regular"
    full = f"{family} {style}"; ps = (family + "-" + style).replace(" ", "")
    nm = f["name"]
    for nid in (1, 2, 3, 4, 6, 16, 17, 21, 22): nm.removeNames(nameID=nid)
    for nid, val in [(1, n1), (2, n2), (3, f"0.5;FVN;{ps}"), (4, full), (6, ps), (16, family), (17, style)]:
        nm.setName(val, nid, 3, 1, 0x409)
    nm.setName("Body/UI companion to Ferry VN Display. Derivative of Be Vietnam Pro (SIL OFL 1.1).", 10, 3, 1, 0x409)
    o = f["OS/2"]; fs = o.fsSelection & ~(0x01 | 0x20 | 0x40)
    if rib_bold: fs |= 0x20
    if is_it: fs |= 0x01
    if not (fs & 0x21): fs |= 0x40
    o.fsSelection = fs; f["head"].macStyle = (0x01 if rib_bold else 0) | (0x02 if is_it else 0)
    f.save(out_path)
    return M, l_extra, W

if __name__ == "__main__":
    out = "/home/claude/fonts/text5/"; os.makedirs(out, exist_ok=True)
    S = "/home/claude/fonts/BeVietnamPro-{}.ttf"
    jobs = [("Regular", "Regular", 400, 0), ("Medium", "Medium", 500, 0), ("SemiBold", "SemiBold", 600, 0), ("Bold", "Bold", 700, 0),
            ("Italic", "Italic", 400, 12), ("MediumItalic", "Medium Italic", 500, 12),
            ("SemiBoldItalic", "SemiBold Italic", 600, 12), ("BoldItalic", "Bold Italic", 700, 12)]
    for src, style, wc, it in jobs:
        p = out + "FerryVNText-" + style.replace(" ", "") + ".ttf"
        M, lx, W = build_text(S.format(src), p, "Ferry VN Text", style, wc, it)
        rep = ft.kern_feet(p, S.format(src), ["l"], {"l": lx}, p)
        ft.autohint(p, increase_x_height=14)
        print(style, M, "tnum W", W, "l-pairs", len(rep))
