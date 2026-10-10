"""
Optical condensing with stem compensation (RMX-style) for Ferry VN 0.7.
Each glyph is scaled horizontally by a factor chosen from its shape group (rounds condense most,
straight letters barely), then every point is pushed outward horizontally by e along its outline
normal so vertical stems keep their original weight; horizontal bars and all heights are untouched.
Advance widths, composite offsets, kerning and mark anchors are transformed consistently.
"""
import math, unicodedata
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

ROUND_UC = set("OQCGDÐ"); BOWL_UC = set("RBPS"); DIAG_UC = set("AVWXYKMNZ"); MID_UC = set("HUJ")
ROUND_LC = set("ocedabpqgsđ"); NARROW = set("iljı!|.,:;'’\"")

def ratio_for(ch, prof):
    if ch is None: return prof["other"]
    if ch in NARROW: return 1.0
    if ch.isdigit(): return prof["digit"]
    if ch in ROUND_UC: return prof["round_uc"]
    if ch in BOWL_UC or ch in DIAG_UC: return prof["bowl_uc"]
    if ch in MID_UC: return prof["mid_uc"]
    if ch.isupper(): return prof["straight_uc"]
    if ch in ROUND_LC: return prof["round_lc"]
    if ch.islower(): return prof["other_lc"]
    return prof["other"]

PHI_LINEAR = True
def _phi(n): return max(-1.0, min(1.0, n)) if PHI_LINEAR else max(-1.0, min(1.0, n / 0.25))

def _area(pts):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2

def transform_contour(pts, on, s, e, sign):
    n = len(pts); sp = [(x * s, y) for x, y in pts]; out = []
    for i in range(n):
        P = sp[i]; A = sp[i - 1]; B = sp[(i + 1) % n]
        d1 = (P[0] - A[0], P[1] - A[1]); d2 = (B[0] - P[0], B[1] - P[1])
        l1, l2 = math.hypot(*d1), math.hypot(*d2)
        def nx(d, L): return sign * (-d[1] / L) if L > 1e-9 else 0.0
        if on[i] and l1 > 1e-9 and l2 > 1e-9:
            cosang = (d1[0] * d2[0] + d1[1] * d2[1]) / (l1 * l2)
            if cosang < math.cos(math.radians(12)):               # corner: offset both edges, intersect
                h1, h2 = e * _phi(nx(d1, l1)), e * _phi(nx(d2, l2))
                den = d1[0] * (-d2[1]) - d1[1] * (-d2[0])
                if abs(den) > 1e-9:
                    rx = h2 - h1
                    a = (rx * (-d2[1])) / den
                    Q = (P[0] + h1 + a * d1[0], P[1] + a * d1[1])
                    if math.hypot(Q[0] - P[0], Q[1] - P[1]) <= 3 * e + 1:
                        out.append(Q); continue
                out.append((P[0] + (h1 + h2) / 2, P[1])); continue
        t = (B[0] - A[0], B[1] - A[1]); L = math.hypot(*t)
        out.append((P[0] + (e * _phi(sign * (-t[1] / L)) if L > 1e-9 else 0), P[1]))
    return out

def condense(src, dst, prof, stem, slant_deg=0.0):
    f = TTFont(src); glyf = f["glyf"]; hmtx = f["hmtx"]
    tan = math.tan(math.radians(slant_deg))
    rev = {}
    for cp, g in f.getBestCmap().items(): rev.setdefault(g, cp)
    order = f.getGlyphOrder()
    gdef = f["GDEF"].table.GlyphClassDef.classDefs if "GDEF" in f and f["GDEF"].table.GlyphClassDef else {}
    def base_char(g):
        cp = rev.get(g)
        if cp is None:
            stem_name = g.split(".")[0]
            cp = rev.get(stem_name)
        return unicodedata.normalize("NFD", chr(cp))[0] if cp is not None else None
    S, E = {}, {}
    for g in order:
        gl = glyf[g]
        if gdef.get(g) == 3: S[g], E[g] = 1.0, 0.0; continue          # marks keep their shape
        r = ratio_for(base_char(g), prof)
        gl.recalcBounds(glyf)
        w = (gl.xMax - gl.xMin) if gl.numberOfContours else 0
        if r >= 0.999 or w <= stem * 1.2: S[g], E[g] = 1.0, 0.0; continue
        s = max(0.66, min(1.0, (r * w - stem) / (w - stem)))
        S[g], E[g] = s, stem * (1 - s) / 2
    # ink centres before change (for composites)
    cx = {}
    for g in order:
        gl = glyf[g]; gl.recalcBounds(glyf); cx[g] = (gl.xMin + gl.xMax) / 2 if gl.numberOfContours else 0
    for g in order:
        gl = glyf[g]; s, e = S[g], E[g]
        if gl.isComposite():
            for c in gl.components:
                ch = c.glyphName
                c.x = int(round(s * (c.x + cx[ch]) + e - (S[ch] * cx[ch] + E[ch])))
        elif gl.numberOfContours > 0 and (s != 1.0):
            coords = list(gl.coordinates); flags = gl.flags; ends = gl.endPtsOfContours
            un = [(x - y * tan, y) for x, y in coords]
            contours = []; st = 0
            for en in ends: contours.append((st, en)); st = en + 1
            big = max(contours, key=lambda c: abs(_area(un[c[0]:c[1] + 1])))
            sign = 1.0 if _area(un[big[0]:big[1] + 1]) < 0 else -1.0     # fill on the right (TrueType) vs left
            new = []
            for a, b in contours:
                new += transform_contour(un[a:b + 1], [bool(flags[i] & 1) for i in range(a, b + 1)], s, e, sign)
            new = [(x + e + y * tan, y) for x, y in new]
            gl.coordinates = GlyphCoordinates([(round(x), round(y)) for x, y in new])
        hmtx[g] = (int(round(s * hmtx[g][0] + 2 * e)), hmtx[g][1])
    for g in order:
        gl = glyf[g]; gl.recalcBounds(glyf)
        hmtx[g] = (hmtx[g][0], gl.xMin if gl.numberOfContours else 0)
        if hasattr(gl, "program"):
            from fontTools.ttLib.tables import ttProgram
            gl.program = ttProgram.Program(); gl.program.fromBytecode(b"")
    for t in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX"):
        if t in f: del f[t]
    # GPOS: kerning scaled by the pair's mean factor (class kerning: global mean), anchors follow their glyph
    kscale = prof["kern"]
    def scale_vr(v):
        if v is None: return
        for at in ("XAdvance", "XPlacement"):
            if hasattr(v, at) and getattr(v, at): setattr(v, at, int(round(getattr(v, at) * kscale)))
    def anc(a, g):
        if a is not None: a.XCoordinate = int(round(S[g] * a.XCoordinate + E[g]))
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            t = lk.LookupType
            if t == 9: st, t = st.ExtSubTable, st.ExtensionLookupType
            if t == 2:
                if st.Format == 1:
                    for ps in st.PairSet:
                        for r in ps.PairValueRecord: scale_vr(r.Value1); scale_vr(r.Value2)
                else:
                    for c1 in st.Class1Record:
                        for c2 in c1.Class2Record: scale_vr(c2.Value1); scale_vr(c2.Value2)
            elif t == 1:
                scale_vr(getattr(st, "Value", None))
            elif t == 4:
                for g, r in zip(st.MarkCoverage.glyphs, st.MarkArray.MarkRecord): anc(r.MarkAnchor, g)
                for g, r in zip(st.BaseCoverage.glyphs, st.BaseArray.BaseRecord):
                    for a in r.BaseAnchor: anc(a, g)
            elif t == 6:
                for g, r in zip(st.Mark1Coverage.glyphs, st.Mark1Array.MarkRecord): anc(r.MarkAnchor, g)
                for g, r in zip(st.Mark2Coverage.glyphs, st.Mark2Array.Mark2Record):
                    for a in r.Mark2Anchor: anc(a, g)
    f.save(dst)
    return S

DISPLAY = dict(round_uc=0.82, bowl_uc=0.90, mid_uc=0.93, straight_uc=0.97, round_lc=0.88, other_lc=0.93, digit=0.88, other=0.95, kern=0.90)
TEXT    = dict(round_uc=0.90, bowl_uc=0.95, mid_uc=0.97, straight_uc=1.0, round_lc=0.94, other_lc=0.97, digit=0.94, other=0.98, kern=0.95)

def scale_font(src, dst, s, slant_deg=0.0):
    """Clean affine horizontal scale (used with a heavier source weight so stems land on target)."""
    f = TTFont(src); glyf = f["glyf"]; hmtx = f["hmtx"]; tan = math.tan(math.radians(slant_deg))
    for g in f.getGlyphOrder():
        gl = glyf[g]
        if gl.isComposite():
            for c in gl.components: c.x = int(round(c.x * s))
        elif gl.numberOfContours > 0:
            gl.coordinates = GlyphCoordinates([(round((x - y * tan) * s + y * tan), y) for x, y in gl.coordinates])
        hmtx[g] = (int(round(hmtx[g][0] * s)), hmtx[g][1])
    for g in f.getGlyphOrder():
        gl = glyf[g]; gl.recalcBounds(glyf); hmtx[g] = (hmtx[g][0], gl.xMin if gl.numberOfContours else 0)
        if hasattr(gl, "program"):
            from fontTools.ttLib.tables import ttProgram
            gl.program = ttProgram.Program(); gl.program.fromBytecode(b"")
    for t in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX"):
        if t in f: del f[t]
    def vr(v):
        if v is None: return
        for at in ("XAdvance", "XPlacement"):
            if getattr(v, at, None): setattr(v, at, int(round(getattr(v, at) * s)))
    def an(a):
        if a is not None: a.XCoordinate = int(round(a.XCoordinate * s))
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            t = lk.LookupType
            if t == 9: st, t = st.ExtSubTable, st.ExtensionLookupType
            if t == 2:
                if st.Format == 1:
                    for ps in st.PairSet:
                        for r in ps.PairValueRecord: vr(r.Value1); vr(r.Value2)
                else:
                    for c1 in st.Class1Record:
                        for c2 in c1.Class2Record: vr(c2.Value1); vr(c2.Value2)
            elif t == 1: vr(getattr(st, "Value", None))
            elif t == 4:
                for r in st.MarkArray.MarkRecord: an(r.MarkAnchor)
                for r in st.BaseArray.BaseRecord:
                    for a in r.BaseAnchor: an(a)
            elif t == 6:
                for r in st.Mark1Array.MarkRecord: an(r.MarkAnchor)
                for r in st.Mark2Array.Mark2Record:
                    for a in r.Mark2Anchor: an(a)
    f.save(dst)
