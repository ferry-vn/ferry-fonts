import unicodedata, statistics as stt, glob, json, os
import uharfbuzz as hb
from fontTools.ttLib import TTFont
def strip(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
CAPS  = strip("RẠCH GIÁ PHÚ QUỐC CÔN ĐẢO LÝ SƠN NAM DU HÀ TIÊN VŨNG TÀU CÁT BÀ FERRY LƯỚT APP LƯỚT SÓNG ĐẶT VÉ TÀU CAO TỐC")
TITLE = strip("Lướt App. Lướt Sóng. Đặt Vé Tàu Cao Tốc Đi Phú Quốc, Côn Đảo, Lý Sơn Chỉ Trong Một Chạm")
BODY  = strip("Ký một lần với Ferry VN để bán vé của mọi hãng trên cùng một hệ thống, từ lịch tàu, sơ đồ ghế đến xuất vé. "
              "Nạp tiền một lần, xuất vé tự động kể cả ngoài giờ hành chính. Mã đặt chỗ được gửi qua email và tin nhắn.")
def adv(path, text):
    face = hb.Face(hb.Blob.from_file_path(path)); font = hb.Font(face)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(font, buf, {"kern": True})
    return sum(p.x_advance for p in buf.glyph_positions)
def hgt(f, ch):
    g = f["glyf"][f.getBestCmap()[ord(ch)]]; g.recalcBounds(f["glyf"]); return g.yMax
def measure(path):
    f = TTFont(path); cap = hgt(f, "H"); xh = hgt(f, "x"); hm = f["hmtx"]; cm = f.getBestCmap()
    a = lambda ch: hm[cm[ord(ch)]][0]
    return dict(caps=adv(path, CAPS) / cap / len(CAPS), title=adv(path, TITLE) / cap / len(TITLE),
                body_x=adv(path, BODY) / xh / len(BODY), body_c=adv(path, BODY) / cap / len(BODY),
                O=a("O") / cap, H=a("H") / cap, n=a("n") / xh, o=a("o") / xh, xh_cap=xh / cap)
if __name__ == "__main__":
    res = {}
    for p in sorted(glob.glob("*-400.ttf") + glob.glob("*-700.ttf")):
        fam, w = os.path.basename(p)[:-4].rsplit("-", 1)
        res.setdefault(fam, {})[w] = measure(p)
    ours = {"Ferry 0.6": ("/home/claude/fonts/text6/FerryVNText-Regular.ttf", "/home/claude/fonts/display6/FerryVNDisplay-Bold.ttf"),
            "Ferry 0.7": ("/home/claude/fonts/text7/FerryVNText-Regular.ttf", "/home/claude/fonts/display7/FerryVNDisplay-Bold.ttf")}
    for k, (t, d) in ours.items(): res[k] = {"400": measure(t), "700": measure(d)}
    json.dump(res, open("bench.json", "w"), indent=1)
    def show(w, key):
        rows = sorted(((v[w][key], k) for k, v in res.items() if w in v), reverse=True)
        bench = [x for x, k in rows if not k.startswith("Ferry")]
        q = stt.quantiles(bench, n=4)
        print(f"\n== {key} @ {w}: median {stt.median(bench):.3f}  IQR {q[0]:.3f}–{q[2]:.3f}  (n={len(bench)})")
        print("  ".join(f"{k} {x:.3f}" for x, k in rows))
    show("700", "caps"); show("700", "title"); show("400", "body_x"); show("400", "body_c"); show("700", "O"); show("400", "o")
