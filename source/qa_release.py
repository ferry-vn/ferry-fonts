# Kiểm tra phát hành: python source/qa_release.py [thư mục TTF, mặc định desktop]
import glob, os, sys, tempfile, unicodedata
from fontTools.ttLib import TTFont
R = sys.argv[1] if len(sys.argv) > 1 else "desktop"
VIET = set()
for v in "aăâeêioôơuưy":
    for m in ["", "\u0300", "\u0301", "\u0309", "\u0303", "\u0323"]:
        for c in (v, v.upper()): VIET.add(unicodedata.normalize("NFC", c + m))
VIET |= {"đ", "Đ"}
ok = True; seen_ps = set(); rows = []
for p in sorted(glob.glob(os.path.join(R, "**", "*.ttf"), recursive=True)):
    f = TTFont(p); nm = f["name"]; cm = f.getBestCmap(); issues = []
    miss = [c for c in VIET if ord(c) not in cm]
    if miss: issues.append(f"thiếu {len(miss)} ký tự Việt")
    ps = nm.getDebugName(6)
    if ps in seen_ps: issues.append("trùng tên PostScript")
    seen_ps.add(ps)
    if f["OS/2"].fsType != 0: issues.append(f"fsType {f['OS/2'].fsType}")
    if nm.getDebugName(5) != "Version 1.000": issues.append("version")
    if "Mono" in ps:
        advs = {f["hmtx"][g][0] for g in f.getGlyphOrder()}
        if not advs <= {0, 600}: issues.append(f"advance {sorted(advs)[:5]}")
        if f["post"].isFixedPitch != 1: issues.append("isFixedPitch")
        if any(cp not in cm for cp in range(0xE100, 0xE10D)): issues.append("thiếu icon Ferry")
    for g in ("A", "a", "Ạ", "ự"):
        gl = f["glyf"][cm[ord(g)]]
        if not gl.isComposite() and gl.numberOfContours == 0: issues.append(f"glyph rỗng {g}")
    with tempfile.TemporaryFile() as tmp: TTFont(p).save(tmp)   # round-trip compile
    rows.append((ps, nm.getDebugName(1), nm.getDebugName(2), len(f.getGlyphOrder()), "OK" if not issues else "; ".join(issues)))
    ok &= not issues
for r in rows: print(f"{r[0]:32s} | {r[1]:26s} | {r[2]:12s} | {r[3]:6d} glyph | {r[4]}")
print("Fonts:", len(rows), "| Vietnamese set:", len(VIET), "ký tự kiểm tra"); print("ALL OK" if ok and rows else "CÓ LỖI"); sys.exit(0 if ok and rows else 1)
