"""
Bến Display 0.3 — Xanh-Display-style construction on Be Vietnam Pro (SIL OFL 1.1).
Signature system (no waterline):
  1. Góc mềm  — one soft corner where a stroke begins/turns (L bottom-left, F top-left, A apex top-left, l bottom-left)
  2. Chân lướt — diagonal legs land with a big soft curve and slide forward into a short foot (A, R, K, k)
  3. Tab mềm  — bar ends get one rounded corner (L foot, F top bar, l foot)
  4. Khớp cong — Y arms flow into the stem through a U-curve instead of a sharp crotch
Everything is applied to every precomposed Vietnamese variant (Ấ, Ặ, Ỵ …) by geometry, not by name.
"""
import math, sys, os, unicodedata
import pathops
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen

SRC = "/home/claude/fonts/BeVietnamPro-{}.ttf"
CAP = 740

def to_path(gs, name):
    rec = DecomposingRecordingPen(gs); gs[name].draw(rec)
    p = pathops.Path(); rec.replay(p.getPen())
    return pathops.simplify(p, fix_winding=True, clockwise=True)

def rect(x0, y0, x1, y1):
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return p

def union(a, b): return pathops.op(a, b, pathops.PathOp.UNION, fix_winding=True, clockwise=True)

def runs_x(p, y, x0, x1):
    out = []; inside = False; s = None
    for x in range(int(x0) - 2, int(x1) + 3):
        c = p.contains((x, y))
        if c and not inside: s = x; inside = True
        if not c and inside: out.append((s, x)); inside = False
    return out

def runs_y(p, x, y0, y1):
    out = []; inside = False; s = None
    for y in range(int(y0), int(y1)):
        c = p.contains((x, y))
        if c and not inside: s = y; inside = True
        if not c and inside: out.append((s, y)); inside = False
    return out

# ---------- contour model ----------
class Raw(list):
    """contour kept verbatim (e.g. all-off-curve dots/rings)."""

def contours_of(path):
    rec = RecordingPen(); path.draw(rec)
    groups = []; g = None
    for op_, args in rec.value:
        if op_ == "moveTo" or g is None:
            g = []; groups.append(g)
        g.append((op_, args))
        if op_ in ("closePath", "endPath"): g = None
    cs = []
    for g in groups:
        if any(a is None for _, args in g for a in args) or g[0][0] != "moveTo":
            cs.append(Raw(g)); continue
        segs = []; cur = start = None
        for op_, args in g:
            if op_ == "moveTo": cur = start = tuple(args[0])
            elif op_ == "lineTo":
                p = tuple(args[0]); segs.append(["L", cur, p]); cur = p
            elif op_ == "qCurveTo":
                pts = [tuple(a) for a in args]; segs.append(["Q", cur] + pts); cur = pts[-1]
            elif op_ == "curveTo":
                pts = [tuple(a) for a in args]; segs.append(["C", cur] + pts); cur = pts[-1]
            elif op_ in ("closePath", "endPath"):
                if cur != start: segs.append(["L", cur, start])
        if segs: cs.append(segs)
    return cs

def draw_contours(cs, pen):
    for segs in cs:
        if isinstance(segs, Raw):
            for op_, args in segs: getattr(pen, op_)(*args)
            continue
        pen.moveTo(segs[0][1])
        for s in segs:
            if s[0] == "L": pen.lineTo(s[2])
            elif s[0] == "Q": pen.qCurveTo(*s[2:])
            else: pen.curveTo(*s[2:])
        pen.closePath()

def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    return (dx / L, dy / L), L

def vertices(cs, ylo=-3, yhi=CAP + 3):
    """line-line vertices: (ci, si, P, kind) kind = 'convex' | 'reflex'."""
    out = []
    for ci, segs in enumerate(cs):
        if isinstance(segs, Raw): continue
        n = len(segs)
        for si in range(n):
            a, b = segs[si], segs[(si + 1) % n]
            if a[0] != "L" or b[0] != "L": continue
            P = a[2]
            if not (ylo <= P[1] <= yhi): continue
            (u1, l1), (u2, l2) = _unit(a[1], P), _unit(P, b[2])
            if l1 < 1 or l2 < 1: continue
            cross = u1[0] * u2[1] - u1[1] * u2[0]
            if abs(cross) < 0.05: continue
            out.append((ci, si, P, "convex" if cross < 0 else "reflex"))
    return out

def round_at(cs, P, t_req, kind=None, tol=2.5):
    """Replace the vertex at P with a circular (2-quad) fillet of tangent length t."""
    best = None
    for ci, si, Q, k in vertices(cs, -9999, 9999):
        if kind and k != kind: continue
        d = math.hypot(Q[0] - P[0], Q[1] - P[1])
        if d <= tol and (best is None or d < best[0]): best = (d, ci, si)
    if best is None: return False
    _, ci, si = best; segs = cs[ci]; n = len(segs); sj = (si + 1) % n
    A, V, B = segs[si][1], segs[si][2], segs[sj][2]
    (u1, l1), (u2, l2) = _unit(A, V), _unit(V, B)
    t = min(t_req, 0.49 * l1, 0.49 * l2)
    phi = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))
    if t < 2 or phi < math.radians(4): return False
    rho = t / math.tan(phi / 2); k = rho * math.tan(phi / 4)
    P1 = (V[0] - u1[0] * t, V[1] - u1[1] * t); P2 = (V[0] + u2[0] * t, V[1] + u2[1] * t)
    C1 = (P1[0] + u1[0] * k, P1[1] + u1[1] * k); C2 = (P2[0] - u2[0] * k, P2[1] - u2[1] * k)
    segs[si] = ["L", A, P1]
    segs[sj] = ["L", P2, B]
    segs.insert(si + 1, ["Q", P1, C1, C2, P2])
    return True

def base_vertices(cs, top):
    return [v for v in vertices(cs, -3, top + 3)]

def nearest(vs, target, kind):
    c = [v for v in vs if v[3] == kind]
    if not c: return None
    return min(c, key=lambda v: math.hypot(v[2][0] - target[0], v[2][1] - target[1]))[2]

def bottom_segments(cs):
    out = []
    for segs in cs:
        if isinstance(segs, Raw): continue
        for s in segs:
            if s[0] == "L" and abs(s[1][1]) < 1 and abs(s[2][1]) < 1 and abs(s[1][0] - s[2][0]) > 5:
                out.append((min(s[1][0], s[2][0]), max(s[1][0], s[2][0])))
    return out

def outer_slope(cs, xo):
    """dx/dy of the edge leaving (xo, 0) upward."""
    for segs in cs:
        if isinstance(segs, Raw): continue
        for s in segs:
            if s[0] != "L": continue
            for a, b in ((s[1], s[2]), (s[2], s[1])):
                if abs(a[0] - xo) < 1 and abs(a[1]) < 1 and b[1] > 5:
                    return (b[0] - a[0]) / (b[1] - a[1])
    return 0.0

# ---------- signature operations ----------
def op_kick(path, M):
    """Chân lướt: rightmost leg lands with a big soft curve and slides into a short foot."""
    cs = contours_of(path); bs = bottom_segments(cs)
    if not bs: return path, 0
    xi, xo = max(bs, key=lambda b: b[1])
    s = outer_slope(cs, xo)
    u = max(M["stem"], 0.16 * CAP)
    h, ext = M["hbar"] * 0.92, u * 0.42
    path = union(path, rect(xi + 3, 0, xo + ext, h))
    cs = contours_of(path)
    round_at(cs, (xi, 0), u * 0.62, "convex", tol=4)
    round_at(cs, (xo + s * h, h), M["stem"] * 0.30, "reflex", tol=6)
    return cs, ext

def build_glyph(gs, name, base, M):
    """returns (contours or path, extra_advance)"""
    p = to_path(gs, name)
    stem, hbar = M["stem"], M["hbar"]
    u = max(stem, 0.16 * CAP)
    big, tab = u * 0.55, u * 0.45
    extra = 0
    if base in ("A", "R", "K", "k"):
        cs, extra = op_kick(p, M)
        if not isinstance(cs, list): cs = contours_of(cs)
    elif base == "l":
        cs = contours_of(p); bs = bottom_segments(cs)
        if bs:
            x0, x1 = min(bs, key=lambda b: b[0])
            ext, h = u * 0.78, hbar * 0.9
            p = union(p, rect(x0 + 3, 0, x1 + ext, h)); cs = contours_of(p)
            round_at(cs, (x1, h), stem * 0.32, "reflex", tol=4)
            round_at(cs, (x0, 0), big, "convex", tol=4)
            round_at(cs, (x1 + ext, h), tab, "convex", tol=4)
            extra = ext * 0.8
        return cs, extra
    else:
        cs = contours_of(p)
    top = CAP if base.isupper() else 560
    vs = base_vertices(cs, top)
    if not vs: return cs, extra
    xs = [v[2][0] for v in vs]; xmin, xmax = min(xs), max(xs)
    if base == "A":
        tops = [v for v in vs if v[3] == "convex" and v[2][1] >= CAP - 3]
        if tops: round_at(cs, min(tops, key=lambda v: v[2][0])[2], u * 0.5, "convex")
    elif base == "L":
        q = nearest(vs, (xmin, 0), "convex");      q and round_at(cs, q, big, "convex")
        q = nearest(vs, (xmax, hbar), "convex");   q and round_at(cs, q, tab, "convex")
    elif base == "F":
        q = nearest(vs, (xmin, CAP), "convex");    q and round_at(cs, q, big, "convex")
        c = [v for v in vs if v[3] == "convex" and CAP - hbar * 1.6 < v[2][1] < CAP - 10]
        if c: round_at(cs, max(c, key=lambda v: v[2][0])[2], tab, "convex")
    elif base == "Y":
        c = [v for v in vs if v[3] == "reflex" and CAP * 0.15 < v[2][1] < CAP * 0.45]
        for v in c: round_at(cs, v[2], u * 0.95, "reflex")
    return cs, extra

SIG = set("ARKkLFYl")

def build(src_weight, out_path, family, style, slant_deg=0.0, weight_class=None):
    f = TTFont(SRC.format(src_weight))
    gs = f.getGlyphSet(); glyf = f["glyf"]; hmtx = f["hmtx"]; cmap = f.getBestCmap()
    H = to_path(gs, cmap[ord("H")]); r = runs_x(H, 600, H.bounds[0], H.bounds[2])[0]
    E = to_path(gs, cmap[ord("E")]); eb = E.bounds
    M = {"stem": r[1] - r[0], "hbar": runs_y(E, (eb[0] + eb[2]) / 2 + 40, 0, 400)[0][1]}
    shear = math.tan(math.radians(slant_deg))

    targets = {}
    for cp, g in cmap.items():
        b = unicodedata.normalize("NFD", chr(cp))[0]
        if b in SIG and not glyf[g].isComposite(): targets[g] = b

    new = {}
    for name, base in targets.items():
        try:
            new[name] = build_glyph(gs, name, base, M)
        except Exception as e:
            print("FAIL", name, e, file=sys.stderr)

    for name in f.getGlyphOrder():
        pen = TTGlyphPen(None)
        tgt = TransformPen(pen, (1, 0, shear, 1, 0, 0)) if shear else pen
        if name in new:
            cs, extra = new[name]
            draw_contours(cs, tgt)
            hmtx[name] = (int(round(hmtx[name][0] + extra)), hmtx[name][1])
        else:
            rec = DecomposingRecordingPen(gs); gs[name].draw(rec); rec.replay(tgt)
        g = pen.glyph(); glyf[name] = g
    for name in f.getGlyphOrder():
        g = glyf[name]; g.recalcBounds(glyf)
        hmtx[name] = (hmtx[name][0], g.xMin if g.numberOfContours else 0)

    for t in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX", "DSIG"):
        if t in f: del f[t]
    gasp = newTable("gasp"); gasp.version = 1; gasp.gaspRange = {0xFFFF: 0x000F}; f["gasp"] = gasp
    f["maxp"].maxSizeOfInstructions = 0
    if slant_deg:
        f["post"].italicAngle = -slant_deg
        f["hhea"].caretSlopeRise = 1000; f["hhea"].caretSlopeRun = int(round(1000 * shear))
        f["OS/2"].fsSelection = (f["OS/2"].fsSelection | 0x01) & ~0x40
        f["head"].macStyle |= 0x02
    if weight_class: f["OS/2"].usWeightClass = weight_class
    nm = f["name"]; full = f"{family} {style}"; ps = (family + "-" + style).replace(" ", "")
    for nid in (1, 2, 3, 4, 6, 16, 17, 21, 22): nm.removeNames(nameID=nid)
    for nid, val in [(1, full), (2, "Regular"), (3, f"0.3;FVN;{ps}"), (4, full), (6, ps), (16, family), (17, style)]:
        nm.setName(val, nid, 3, 1, 0x409)
    nm.setName("Concept derivative of Be Vietnam Pro (SIL OFL 1.1). Ferry VN brand study.", 10, 3, 1, 0x409)
    f.save(out_path)
    return M, len(new)

SPECS = [("Light", "Light", 0, 300), ("Regular", "Regular", 0, 400), ("Bold", "Bold", 0, 700),
         ("Black", "Black", 0, 900), ("Bold", "Bold Oblique", 8.2, 700)]
if __name__ == "__main__":
    out = "/home/claude/fonts/out3/"; os.makedirs(out, exist_ok=True)
    for src, style, slant, wc in SPECS:
        M, n = build(src, out + "BenDisplay-" + style.replace(" ", "") + ".ttf", "Ben Display", style, slant, wc)
        print(style, M, "glyphs modified:", n)
