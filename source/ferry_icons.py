"""
Ferry VN icon set for Ferry VN Mono — Nerd-Font style: one cell wide (600), placed in a Private Use
range that Nerd Fonts leaves empty (U+E100–U+E10C). Built from geometric primitives with the same
squircle corner (handle ratio 0.70) used across the Ferry VN typefaces.
"""
import math, pathops
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen

K = 0.5523   # circle
KS = 0.70    # squircle corner

def P(): return pathops.Path()
def simp(p): return pathops.simplify(p, fix_winding=True, clockwise=True)
def U(*ps):
    out = ps[0]
    for q in ps[1:]: out = pathops.op(out, q, pathops.PathOp.UNION, fix_winding=True, clockwise=True)
    return out
def D(a, *bs):
    for b in bs: a = pathops.op(a, b, pathops.PathOp.DIFFERENCE, fix_winding=True, clockwise=True)
    return a
def I(a, b): return pathops.op(a, b, pathops.PathOp.INTERSECTION, fix_winding=True, clockwise=True)

def circle(cx, cy, r):
    p = P(); pen = p.getPen(); k = K * r
    pen.moveTo((cx + r, cy))
    pen.curveTo((cx + r, cy + k), (cx + k, cy + r), (cx, cy + r))
    pen.curveTo((cx - k, cy + r), (cx - r, cy + k), (cx - r, cy))
    pen.curveTo((cx - r, cy - k), (cx - k, cy - r), (cx, cy - r))
    pen.curveTo((cx + k, cy - r), (cx + r, cy - k), (cx + r, cy))
    pen.closePath(); return p

def rrect(x0, y0, x1, y1, r, k=KS):
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2); c = r * (1 - k)
    p = P(); pen = p.getPen()
    pen.moveTo((x0 + r, y0)); pen.lineTo((x1 - r, y0))
    pen.curveTo((x1 - c, y0), (x1, y0 + c), (x1, y0 + r)); pen.lineTo((x1, y1 - r))
    pen.curveTo((x1, y1 - c), (x1 - c, y1), (x1 - r, y1)); pen.lineTo((x0 + r, y1))
    pen.curveTo((x0 + c, y1), (x0, y1 - c), (x0, y1 - r)); pen.lineTo((x0, y0 + r))
    pen.curveTo((x0, y0 + c), (x0 + c, y0), (x0 + r, y0)); pen.closePath(); return p

def poly(pts):
    p = P(); pen = p.getPen(); pen.moveTo(pts[0])
    for q in pts[1:]: pen.lineTo(q)
    pen.closePath(); return p

def stroke(pts, w, cap="round", curve=None):
    p = P(); pen = p.getPen(); pen.moveTo(pts[0])
    if curve:
        for seg in curve: pen.curveTo(*seg)
    else:
        for q in pts[1:]: pen.lineTo(q)
    pen.endPath()
    p.stroke(w, pathops.LineCap.ROUND_CAP if cap == "round" else pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    p.convertConicsToQuads(); return simp(p)

def wave(x0, x1, y, amp, n, w):
    seg = (x1 - x0) / n; pts = [(x0, y)]; curve = []
    for i in range(n):
        a = x0 + i * seg; b = a + seg; s = 1 if i % 2 == 0 else -1
        curve.append(((a + seg * 0.35, y + s * amp), (b - seg * 0.35, y + s * amp), (b, y)))
    return stroke(pts, w, curve=curve)

# icon box: x 40..560, y 100..620, centre (300, 360)
def icons(stroke_w):
    w = stroke_w; cx, cy = 300, 360; out = {}
    # E100 Ferry VN mark: disc, rising hull slices, wave below
    disc = circle(cx, cy, 255)
    s1 = poly([(70, 380), (560, 520), (560, 470), (130, 330)])
    s2 = poly([(60, 300), (560, 420), (560, 380), (90, 255)])
    wv = wave(60, 560, 205, 36, 3, w * 0.9)
    out["ferry-mark"] = D(disc, s1, s2, wv)
    # E101 high-speed boat
    hull = poly([(50, 250), (470, 250), (565, 345), (50, 345)])
    cabin = rrect(150, 345, 420, 470, 40)
    win = [rrect(185 + i * 80, 380, 245 + i * 80, 435, 14) for i in range(3)]
    boat = D(U(hull, cabin), *win)
    out["ferry-boat"] = U(boat, wave(50, 560, 170, 28, 4, w * 0.8))
    # E102 ticket
    t = rrect(45, 210, 555, 510, 46)
    notch = [circle(45, 360, 52), circle(555, 360, 52)]
    perf = [rrect(392, 240 + i * 62, 412, 278 + i * 62, 10) for i in range(5)]
    out["ferry-ticket"] = D(t, *notch, *perf)
    # E103 seat
    back = rrect(150, 300, 255, 610, 48)
    seat = rrect(150, 250, 470, 345, 40)
    leg = rrect(300, 110, 350, 260, 18); foot = rrect(220, 100, 430, 140, 18)
    out["ferry-seat"] = U(back, seat, leg, foot)
    # E104 port pin
    head = circle(cx, 445, 165)
    tip = poly([(158, 365), (442, 365), (300, 100)])
    out["ferry-pin"] = D(U(head, tip), circle(cx, 445, 70))
    # E105 anchor
    ring = D(circle(cx, 560, 60), circle(cx, 560, 28))
    shaft = rrect(cx - w / 2, 190, cx + w / 2, 505, w / 2)
    bar = rrect(185, 440, 415, 440 + w, w / 2)
    arms = stroke([(95, 300)], w, curve=[((110, 170), (220, 115), (300, 115)), ((380, 115), (490, 170), (505, 300))])
    tips = U(circle(95, 300, w * 0.75), circle(505, 300, w * 0.75))
    out["ferry-anchor"] = U(ring, shaft, bar, arms, tips)
    # E106 waves
    out["ferry-wave"] = U(wave(55, 545, 455, 42, 4, w), wave(55, 545, 300, 42, 4, w), wave(55, 545, 150, 42, 4, w * 0.75))
    # E107 route A → B
    a = D(circle(110, 360, 70), circle(110, 360, 32)); b = circle(490, 360, 70)
    line = rrect(180, 360 - w * 0.4, 400, 360 + w * 0.4, w * 0.4)
    head2 = poly([(385, 300), (425, 360), (385, 420), (370, 400), (395, 360), (370, 320)])
    out["ferry-route"] = U(a, b, line)
    # E108 clock
    face = D(circle(cx, cy, 250), circle(cx, cy, 250 - w))
    hands = stroke([(cx, cy + 165), (cx, cy), (cx + 120, cy - 70)], w)
    out["ferry-clock"] = U(face, hands, circle(cx, cy, w * 0.7))
    # E109 passenger
    out["ferry-passenger"] = U(circle(cx, 520, 95), rrect(130, 100, 470, 400, 110))
    # E10A luggage
    body = rrect(90, 110, 510, 500, 60)
    handle = D(rrect(200, 470, 400, 620, 50), rrect(240, 470, 360, 580, 22))
    straps = [rrect(185, 150, 185 + w * 0.8, 460, w * 0.4), rrect(415 - w * 0.8, 150, 415, 460, w * 0.4)]
    out["ferry-luggage"] = U(D(body, *straps), handle)
    # E10B lifebuoy
    ringb = D(circle(cx, cy, 255), circle(cx, cy, 135))
    cuts = [rrect(cx - 260, cy - 18, cx + 260, cy + 18, 4), rrect(cx - 18, cy - 260, cx + 18, cy + 260, 4)]
    out["ferry-lifebuoy"] = D(ringb, *cuts)
    # E10C QR (decorative, not scannable)
    def finder(x, y):
        return U(D(rrect(x, y, x + 150, y + 150, 26), rrect(x + 30, y + 30, x + 120, y + 120, 14)), rrect(x + 52, y + 52, x + 98, y + 98, 8))
    cellpos = [(r, c) for r in range(9) for c in range(4, 10) if not (c >= 7 and r >= 7)]
    pick = [cellpos[i] for i in range(len(cellpos)) if (i * 7 + 3) % 5 in (0, 2)]
    mods = [rrect(234 + (c - 4) * 50, 132 + r * 50, 270 + (c - 4) * 50, 168 + r * 50, 8) for r, c in pick if 234 + (c - 4) * 50 + 36 <= 545]
    out["ferry-qr"] = U(finder(60, 460), finder(390, 460), finder(60, 130), *mods)
    return out

ORDER = ["ferry-mark", "ferry-boat", "ferry-ticket", "ferry-seat", "ferry-pin", "ferry-anchor", "ferry-wave",
         "ferry-route", "ferry-clock", "ferry-passenger", "ferry-luggage", "ferry-lifebuoy", "ferry-qr"]
CODEPOINTS = {n: 0xE100 + i for i, n in enumerate(ORDER)}

def to_glyph(path):
    path = simp(path); path.convertConicsToQuads()
    tt = TTGlyphPen(None); path.draw(Cu2QuPen(tt, max_err=1.0, reverse_direction=False))
    return tt.glyph()
