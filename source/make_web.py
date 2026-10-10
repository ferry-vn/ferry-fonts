"""Build the CDN package: WOFF2 subsets (Latin + Vietnamese), @font-face CSS, demo page, headers, npm manifest."""
import os, shutil, json
from fontTools import subset
from fontTools.ttLib import TTFont

VER = "1.0.0"
ROOT = "/home/claude/web/release"; DIST = f"{ROOT}/site/{VER}"
shutil.rmtree(ROOT, ignore_errors=True); os.makedirs(f"{DIST}/fonts"); os.makedirs(f"{DIST}/css")

# Latin + Latin-1/Ext-A/B + full Vietnamese + punctuation, currency (₫ €), arrows, math basics
TEXT_RANGE = ("U+0000-024F,U+0259,U+02B0-02FF,U+0300-036F,U+1E00-1EFF,U+2000-206F,U+20A0-20CF,"
              "U+2100-214F,U+2190-2199,U+2212,U+2215,U+FEFF,U+FFFD")
# Mono adds math operators, box drawing / blocks for terminal tables, Powerline separators and the Ferry icons
MONO_RANGE = TEXT_RANGE + ",U+2190-21FF,U+2200-22FF,U+2500-259F,U+25A0-25FF,U+E0A0-E0A2,U+E0B0-E0B3,U+E100-E10C"

FAMS = {
  "Ferry VN Display": ("/home/claude/fonts/release/FerryVNDisplay-{}.ttf", TEXT_RANGE,
      [("Light", 300, "normal"), ("Regular", 400, "normal"), ("Bold", 700, "normal"), ("Black", 900, "normal"), ("BoldOblique", 700, "italic")]),
  "Ferry VN Text": ("/home/claude/fonts/release/FerryVNText-{}.ttf", TEXT_RANGE,
      [("Regular", 400, "normal"), ("Medium", 500, "normal"), ("SemiBold", 600, "normal"), ("Bold", 700, "normal"),
       ("Italic", 400, "italic"), ("MediumItalic", 500, "italic"), ("SemiBoldItalic", 600, "italic"), ("BoldItalic", 700, "italic")]),
  "Ferry VN Mono": ("/home/claude/fonts/release/FerryVNMono-{}.ttf", MONO_RANGE,
      [("Regular", 400, "normal"), ("Medium", 500, "normal"), ("Bold", 700, "normal"), ("Italic", 400, "italic"), ("BoldItalic", 700, "italic")]),
}

def parse(r):
    out = []
    for part in r.split(","):
        part = part.strip().replace("U+", "")
        a, b = (part.split("-") + [part])[:2]
        out += list(range(int(a, 16), int(b, 16) + 1))
    return out

report = []; css_all = []
for fam, (pat, rng, styles) in FAMS.items():
    slug = fam.lower().replace(" ", "-"); css = [f"/* {fam} {VER} — SIL Open Font License 1.1 */"]
    for st, w, style in styles:
        src = pat.format(st); out = f"{DIST}/fonts/{slug}-{st.lower()}.woff2"
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]; opts.name_IDs = ["*"]
        opts.name_languages = ["*"]; opts.notdef_outline = True; opts.glyph_names = False; opts.hinting = True
        opts.drop_tables = [t for t in opts.drop_tables if t not in ("kern",)]
        f = TTFont(src); sub = subset.Subsetter(opts); sub.populate(unicodes=parse(rng)); sub.subset(f)
        subset.save_font(f, out, opts)
        report.append((os.path.basename(out), os.path.getsize(src) // 1024, os.path.getsize(out) // 1024, len(f.getGlyphOrder())))
        css.append(f"""@font-face {{
  font-family: "{fam}";
  src: url("../fonts/{os.path.basename(out)}") format("woff2");
  font-weight: {w};
  font-style: {style};
  font-display: swap;
  unicode-range: {rng.replace(',', ', ')};
}}""")
    open(f"{DIST}/css/{slug}.css", "w").write("\n".join(css) + "\n")
    css_all += css
helpers = """
/* Tiện ích */
.ferry-tnum { font-variant-numeric: tabular-nums; }      /* số thẳng cột: giờ tàu, giá vé */
.ferry-zero { font-feature-settings: "zero" 1; }          /* số 0 gạch chéo cho mã đặt chỗ (Ferry VN Text) */
"""
open(f"{DIST}/css/ferry-vn-fonts.css", "w").write("\n".join(css_all) + "\n" + helpers)


# Nerd Mono: full font, WOFF2 only (no subsetting: every Nerd icon stays)
from fontTools.ttLib import woff2
nerd = ["/* Ferry VN Nerd Mono 1.0.0 — SIL OFL 1.1; Nerd Fonts icons under their own licences (see LICENSES) */"]
for st, w, style in [("Regular", 400, "normal"), ("Medium", 500, "normal"), ("Bold", 700, "normal"), ("Italic", 400, "italic"), ("BoldItalic", 700, "italic")]:
    src = f"/home/claude/fonts/release/FerryVNNerdMono-{st}.ttf"; out = f"{DIST}/fonts/ferry-vn-nerd-mono-{st.lower()}.woff2"
    woff2.compress(src, out)
    report.append((os.path.basename(out), os.path.getsize(src) // 1024, os.path.getsize(out) // 1024, 0))
    nerd.append(f"""@font-face {{
  font-family: "Ferry VN Nerd Mono";
  src: url("../fonts/{os.path.basename(out)}") format("woff2");
  font-weight: {w};
  font-style: {style};
  font-display: swap;
}}""")
open(f"{DIST}/css/ferry-vn-nerd-mono.css", "w").write("\n".join(nerd) + "\n")
for r in report: print(f"{r[0]:42s} ttf {r[1]:5d} KB -> woff2 {r[2]:5d} KB")
