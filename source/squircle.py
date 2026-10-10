"""
Squircle geometry for Ferry VN 2.0 — every round is drawn with the continuous-corner curve of an app icon.
Rounds are merged into one cubic per quadrant (qu2cu), handles are pushed toward the tangent corner
(curve tension), then converted back to TrueType quadratics (cu2qu). Tangents and extrema are untouched,
so stems, overshoots and joins stay where they were. Counters get slightly more tension than outer
contours so the diagonal 'corners' of a bowl do not thicken.
"""
import math
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.basePen import AbstractPen

def _area(pts):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2


from fontTools.misc.bezierTools import splitCubicAtT

def _roots(a, b, c):
    if abs(a) < 1e-9:
        return [-c / b] if abs(b) > 1e-9 else []
    d = b * b - 4 * a * c
    if d < 0: return []
    d = math.sqrt(d); return [(-b + d) / (2 * a), (-b - d) / (2 * a)]

def _extrema_ts(p0, p1, p2, p3):
    ts = []
    for i in (0, 1):
        a = -p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]
        b = 2 * (p0[i] - 2 * p1[i] + p2[i])
        c = p1[i] - p0[i]
        ts += [t for t in _roots(3 * a, 3 * b, 3 * c) if 0.02 < t < 0.98]
    return sorted(set(round(t, 6) for t in ts))

def _split_extrema(segs):
    out = []
    for sg in segs:
        if sg[0] != "curveTo": out.append(sg); continue
        ts = _extrema_ts(*sg[1:5])
        if not ts: out.append(sg); continue
        for piece in splitCubicAtT(*sg[1:5], *ts):
            out.append(("curveTo",) + tuple(piece))
    return out

def _is_axis(vec):
    L = math.hypot(*vec)
    return L < 1e-6 or abs(vec[0]) / L < 0.02 or abs(vec[1]) / L < 0.02

def _bez(p0, p1, p2, p3, t):
    m = 1 - t
    return (m**3*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t**3*p3[0], m**3*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t**3*p3[1])

def _fit(group):
    """one cubic through a run of cubics, endpoint tangents fixed, handle lengths by least squares"""
    P0, P3 = group[0][1], group[-1][4]
    h1 = group[0][2] if group[0][2] != P0 else group[0][3]
    h2 = group[-1][3] if group[-1][3] != P3 else group[-1][2]
    u = (h1[0] - P0[0], h1[1] - P0[1]); v = (h2[0] - P3[0], h2[1] - P3[1])
    lu, lv = math.hypot(*u), math.hypot(*v)
    if lu < 1e-6 or lv < 1e-6: return None
    u = (u[0] / lu, u[1] / lu); v = (v[0] / lv, v[1] / lv)
    pts = [P0]
    for sg in group:
        for k in range(1, 9): pts.append(_bez(*sg[1:5], k / 8))
    d = [0.0]
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    if d[-1] < 1e-6: return None
    S11 = S12 = S22 = R1 = R2 = 0.0
    for q, dd in zip(pts, d):
        t = dd / d[-1]; m = 1 - t
        base = (m**3*P0[0] + 3*m*m*t*P0[0] + 3*m*t*t*P3[0] + t**3*P3[0], m**3*P0[1] + 3*m*m*t*P0[1] + 3*m*t*t*P3[1] + t**3*P3[1])
        A = (3*m*m*t*u[0], 3*m*m*t*u[1]); B = (3*m*t*t*v[0], 3*m*t*t*v[1])
        r = (q[0] - base[0], q[1] - base[1])
        S11 += A[0]*A[0] + A[1]*A[1]; S12 += A[0]*B[0] + A[1]*B[1]; S22 += B[0]*B[0] + B[1]*B[1]
        R1 += A[0]*r[0] + A[1]*r[1]; R2 += B[0]*r[0] + B[1]*r[1]
    det = S11 * S22 - S12 * S12
    if abs(det) < 1e-9: return None
    al = (R1 * S22 - R2 * S12) / det; be = (S11 * R2 - S12 * R1) / det
    if al <= 0 or be <= 0: return None
    cand = ("curveTo", P0, (P0[0] + u[0]*al, P0[1] + u[1]*al), (P3[0] + v[0]*be, P3[1] + v[1]*be), P3)
    dense = [_bez(*cand[1:5], k / 96) for k in range(97)]
    err = max(min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in dense) for q in pts)
    return cand if err < 6.0 else None

def _merge_quadrants(segs):
    out = []; run = []
    def flush():
        if not run: return
        if len(run) == 1: out.append(run[0])
        else:
            m = _fit(run)
            out.extend([m] if m else run)
        run.clear()
    for sg in segs:
        if sg[0] != "curveTo": flush(); out.append(sg); continue
        if run:
            prev = run[-1]
            tin = (prev[4][0] - prev[3][0], prev[4][1] - prev[3][1])
            tout = (sg[2][0] - sg[1][0], sg[2][1] - sg[1][1])
            Lin, Lout = math.hypot(*tin), math.hypot(*tout)
            smooth = Lin > 1e-6 and Lout > 1e-6 and abs(tin[0]*tout[1] - tin[1]*tout[0]) / (Lin*Lout) < 0.03 and (tin[0]*tout[0] + tin[1]*tout[1]) > 0
            if not smooth or _is_axis(tin): flush()
        run.append(sg)
    flush()
    return out

class TensionPen(AbstractPen):
    def __init__(self, out, s_outer, s_inner):
        self.out, self.so, self.si = out, s_outer, s_inner; self.c = None
    def moveTo(self, p): self.c = [("moveTo", (p,))]
    def lineTo(self, p): self.c.append(("lineTo", (p,)))
    def curveTo(self, *pts): self.c.append(("curveTo", pts))
    def qCurveTo(self, *pts): self.c.append(("qCurveTo", pts))
    def addComponent(self, *a): self.out.addComponent(*a)
    def endPath(self): self._flush(close=False)
    def closePath(self): self._flush(close=True)
    def _flush(self, close):
        c = self.c; self.c = None
        if not c or c[0][0] != "moveTo" or any(op == "qCurveTo" for op, _ in c):
            for op, args in (c or []): getattr(self.out, op)(*args)
            self.out.closePath() if close else self.out.endPath(); return
        oncurve = [args[-1] for op, args in c]
        s = self.si if _area(oncurve) > 0 else self.so      # CCW (positive) = counter
        start = c[0][1][0]; segs = []; cur = start
        for op, args in c[1:]:
            segs.append((op, cur) + tuple(args)); cur = args[-1]
        if close and cur != start: segs.append(("lineTo", cur, start))
        segs = _merge_quadrants(_split_extrema(segs))
        self.out.moveTo(start)
        for sg in segs:
            if sg[0] == "lineTo": self.out.lineTo(sg[2])
            else:
                self.out.curveTo(*self._tension(sg[1], sg[2], sg[3], sg[4], s))
        self.out.closePath() if close else self.out.endPath()
    @staticmethod
    def _tension(P0, H1, H2, P3, s):
        u = (H1[0] - P0[0], H1[1] - P0[1]); v = (H2[0] - P3[0], H2[1] - P3[1])
        lu, lv = math.hypot(*u), math.hypot(*v)
        if lu < 1 or lv < 1: return (H1, H2, P3)
        u = (u[0] / lu, u[1] / lu); v = (v[0] / lv, v[1] / lv)
        den = u[0] * v[1] - u[1] * v[0]
        if abs(den) < 1e-6: return (H1, H2, P3)            # parallel tangents: straight or S-curve
        dx, dy = P3[0] - P0[0], P3[1] - P0[1]
        a = (dx * v[1] - dy * v[0]) / den                    # P0 + a·u == P3 + b·v
        b = (dx * u[1] - dy * u[0]) / den
        if a <= 0 or b <= 0: return (H1, H2, P3)            # inflected / not a corner
        turn = math.degrees(math.acos(max(-1, min(1, -(u[0] * v[0] + u[1] * v[1])))))
        if not (25 <= turn <= 155): return (H1, H2, P3)
        chord = math.hypot(dx, dy)
        if a > 3 * chord or b > 3 * chord: return (H1, H2, P3)
        t0, t1 = lu / a, lv / b
        n0 = min(0.94, t0 + s * (1 - t0)); n1 = min(0.94, t1 + s * (1 - t1))
        return ((P0[0] + u[0] * a * n0, P0[1] + u[1] * a * n0),
                (P3[0] + v[0] * b * n1, P3[1] + v[1] * b * n1), P3)

def squircle_font(f, s_outer, s_inner, slant_tan=0.0, skip=()):
    """apply in place to every simple glyph; composites inherit through their components"""
    glyf = f["glyf"]; gs = f.getGlyphSet(); done = 0
    for name in f.getGlyphOrder():
        g = glyf[name]
        if name in skip or g.isComposite() or g.numberOfContours <= 0: continue
        tt = TTGlyphPen(None)
        cu2qu = Cu2QuPen(tt, max_err=0.8, reverse_direction=False)
        res = TransformPen(cu2qu, (1, 0, slant_tan, 1, 0, 0)) if slant_tan else cu2qu
        ten = TensionPen(res, s_outer, s_inner)
        qu2cu = Qu2CuPen(ten, max_err=1.0, all_cubic=True)
        src = TransformPen(qu2cu, (1, 0, -slant_tan, 1, 0, 0)) if slant_tan else qu2cu
        try:
            gs[name].draw(src); ng = tt.glyph()
        except Exception as e:
            continue
        glyf[name] = ng; done += 1
    for name in f.getGlyphOrder():
        g = glyf[name]; g.recalcBounds(glyf)
        f["hmtx"][name] = (f["hmtx"][name][0], g.xMin if g.numberOfContours else 0)
    return done
