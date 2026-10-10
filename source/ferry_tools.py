"""Shared finishing tools for Ferry VN Display / Text: arrows, pair-kerning for the new feet, hinting."""
import math, unicodedata, importlib.util, os
import pathops, uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.otlLib.builder import buildPairPosClassesSubtable, buildLookup, buildValue
spec = importlib.util.spec_from_file_location("b2", "build_display.py")
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)

# ---------------- glyph plumbing ----------------
def add_glyph(f, name, glyph, adv, unicode=None):
    order = f.getGlyphOrder()
    if name not in order:
        order.append(name); f.setGlyphOrder(order)
    f["glyf"].glyphs[name] = glyph
    if name not in f["glyf"].glyphOrder: f["glyf"].glyphOrder.append(name)
    glyph.recalcBounds(f["glyf"])
    f["hmtx"].metrics[name] = (int(round(adv)), glyph.xMin if glyph.numberOfContours else 0)
    if "GDEF" in f and f["GDEF"].table.GlyphClassDef:
        f["GDEF"].table.GlyphClassDef.classDefs[name] = 1
    if unicode is not None:
        for t in f["cmap"].tables:
            if t.isUnicode(): t.cmap[unicode] = name

def slant_path(p, tan):
    q = pathops.Path(); p.draw(TransformPen(q.getPen(), (1, 0, tan, 1, 0, 0)))
    return pathops.simplify(q, fix_winding=True, clockwise=True)

# ---------------- arrows ----------------
def add_arrows(f):
    """→ ← built from the font's own hyphen weight: straight shaft, mitred open head."""
    gs = f.getGlyphSet(); cmap = f.getBestCmap()
    hy = b2.to_path(gs, cmap[ord("-")]); x0, y0, x1, y1 = hy.bounds
    t = (y1 - y0); yc = f["OS/2"].sCapHeight / 2          # centred on cap height: works with caps, figures and mixed case
    upm = f["head"].unitsPerEm; L = 0.64 * upm; arm = 0.27 * upm; sb = 0.07 * upm
    xs, xt = sb, sb + L
    head = pathops.Path(); pen = head.getPen()
    pen.moveTo((xt - arm, yc + arm)); pen.lineTo((xt - t * 0.35, yc)); pen.lineTo((xt - arm, yc - arm)); pen.endPath()
    head.stroke(t, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 8)
    shaft = b2.rect(xs, yc - t / 2, xt - t * 0.6, yc + t / 2)
    right = pathops.simplify(b2.union(shaft, head), fix_winding=True, clockwise=True)
    adv = L + 2 * sb
    left = pathops.Path(); right.draw(TransformPen(left.getPen(), (-1, 0, 0, 1, adv, 0)))
    left = pathops.simplify(left, fix_winding=True, clockwise=True)
    for name, path, uni in (("arrowright", right, 0x2192), ("arrowleft", left, 0x2190)):
        pen = TTGlyphPen(None); path.draw(pen); add_glyph(f, name, pen.glyph(), adv, uni)

# ---------------- kerning for the new feet ----------------
RIGHT_BASES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") + \
              list("ĐđƠơƯư.,:;!?)]}\"'’”-–—/&@%")

def _hb_font(path):
    return hb.Font(hb.Face(hb.Blob.from_file_path(path)))

def _pair_advance(hbf, a, b):
    buf = hb.Buffer(); buf.add_str(a + b); buf.guess_segment_properties()
    hb.shape(hbf, buf, {"kern": True})
    return buf.glyph_positions[0].x_advance

from fontTools.pens.basePen import BasePen
class _Flat(BasePen):
    def __init__(self):
        super().__init__(None); self.polys = []; self.cur = []
    def _moveTo(self, p): self.cur = [p]; self.polys.append(self.cur)
    def _lineTo(self, p): self.cur.append(p)
    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for k in range(1, 17):
            t = k / 16
            self.cur.append(((1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t*t*p2[0], (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t*t*p2[1]))
    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for k in range(1, 21):
            t = k / 20; m = 1 - t
            self.cur.append((m**3*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t**3*p3[0], m**3*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t**3*p3[1]))
    def _closePath(self):
        if self.cur: self.cur.append(self.cur[0])

def _profiles(path, ys):
    fp = _Flat(); path.draw(fp)
    segs = [(a, b) for pts in fp.polys for a, b in zip(pts, pts[1:]) if a[1] != b[1]]
    L, R = {}, {}
    for y in ys:
        xs = [a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) for a, b in segs
              if (a[1] <= y < b[1]) or (b[1] <= y < a[1])]
        if len(xs) >= 2: L[y], R[y] = min(xs), max(xs)
    return L, R

def _min_dist(advk, rprofL, lprofR):
    ds = [advk + lprofR[y] - rprofL[y] for y in rprofL if y in lprofR]
    return min(ds) if ds else None

def kern_feet(new_path, orig_path, left_bases, extra_by_base, out_path, keep=0.72, floor=0.6):
    """For every left glyph whose advance grew (gliding foot / l tail), add a pair adjustment so that
    the closest approach to each right glyph stays >= keep * original, never looser than before,
    never tighter than the original advance. Writes a class-kerning lookup into 'kern'."""
    fN, fO = TTFont(new_path), TTFont(orig_path)
    gsN, gsO = fN.getGlyphSet(), fO.getGlyphSet()
    cmN, cmO = fN.getBestCmap(), fO.getBestCmap()
    hbN, hbO = _hb_font(new_path), _hb_font(orig_path)
    ys = list(range(-240, 1000, 8))
    pcache = {}
    def prof(fontkey, gs, gname):
        k = (fontkey, gname)
        if k not in pcache: pcache[k] = _profiles(b2.to_path(gs, gname), ys)
        return pcache[k]
    # group glyphs by NFD base
    def family(cm, base):
        return sorted({g for cp, g in cm.items() if unicodedata.normalize("NFD", chr(cp))[0] == base})
    pairs = {}; report = []
    for lb in left_bases:
        lglyphs = frozenset(family(cmN, lb))
        _, rN = prof("N", gsN, cmN[ord(lb)]); _, rO = prof("O", gsO, cmO[ord(lb)])
        for rb in RIGHT_BASES:
            if ord(rb) not in cmN: continue
            lN, _ = prof("N", gsN, cmN[ord(rb)]); lO, _ = prof("O", gsO, cmO[ord(rb)])
            D0 = _min_dist(_pair_advance(hbO, lb, rb), rO, lO)
            D1 = _min_dist(_pair_advance(hbN, lb, rb), rN, lN)
            if D0 is None or D1 is None: continue
            ext = extra_by_base[lb]
            if D1 < floor * D0:                      # foot now crowds the neighbour: open up a little
                d = min(floor * D0 - D1, 0.5 * ext)
            else:                                    # foot has room: win back the extra advance
                d = max(-ext, min(0.0, keep * D0 - D1))
            d = int(round(d))
            if abs(d) >= 4:
                rglyphs = frozenset(g for g in family(cmN, rb) if g not in lglyphs or rb != lb) or frozenset(family(cmN, rb))
                pairs[(lglyphs, rglyphs)] = (buildValue({"XAdvance": d}), None)
                report.append((lb + rb, d))
    # right classes must be disjoint: they are (one family per base). Left classes disjoint too.
    if pairs:
        st = buildPairPosClassesSubtable(pairs, fN.getReverseGlyphMap())
        gpos = fN["GPOS"].table
        lk = buildLookup([st]); gpos.LookupList.Lookup.append(lk)
        gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup); li = gpos.LookupList.LookupCount - 1
        n = 0
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                fr.Feature.LookupListIndex.append(li); fr.Feature.LookupCount = len(fr.Feature.LookupListIndex); n += 1
        assert n, "no kern feature"
    fN.save(out_path)
    return report

def autohint(path, **kw):
    import ttfautohint
    tmp = path + ".tmp.ttf"; os.replace(path, tmp)
    f = TTFont(tmp)
    for t in ("fpgm", "prep", "cvt "):
        if t in f: del f[t]
    f.save(tmp)
    ttfautohint.ttfautohint(in_file=tmp, out_file=path, hinting_range_min=8, hinting_range_max=50,
                            windows_compatibility=True, no_info=True, **kw)
    os.remove(tmp)
