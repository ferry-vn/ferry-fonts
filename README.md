# Ferry VN Fonts

Bộ font chính thức của [Ferry VN](https://ferryvn.com): 4 họ, 23 style, đủ tiếng Việt, phát hành theo SIL Open Font License 1.1.

**Phiên bản hiện tại: 1.0.0** · [Trang demo](https://fonts.ferry.vn/1.0.0/) · [Tải về (Releases)](https://github.com/ferry-vn/ferry-fonts/releases/latest) · [CHANGELOG](CHANGELOG.md)

| Họ | Dùng cho | Style | Nền |
|---|---|---|---|
| **Ferry VN Display** | Quảng cáo, tiêu đề | Light, Regular, Bold, Black, Bold Oblique | Be Vietnam Pro |
| **Ferry VN Text** | Nội dung, giao diện app | Regular, Medium, SemiBold, Bold + Italic từng độ đậm | Be Vietnam Pro |
| **Ferry VN Mono** | Web, app, API, mã vé, vé in nhiệt | Regular, Medium, Bold, Italic, Bold Italic | JetBrains Mono 2.304 |
| **Ferry VN Nerd Mono** | Terminal, IDE | Regular, Medium, Bold, Italic, Bold Italic | JetBrains Mono + Nerd Fonts 3.5.1 |

Specimen: [Display](specimens/FerryVN-Display-1.0.png) · [Text](specimens/FerryVN-Text-1.0.png) · [Mono](specimens/FerryVN-Mono-1.0.png) · [So sánh độ rộng với 29 font sans](specimens/FerryVN-width-benchmark.png)

## Dùng trên web

Một dòng, nạp Display + Text + Mono từ CDN `fonts.ferry.vn`:

```html
<link rel="preconnect" href="https://fonts.ferry.vn" crossorigin>
<link rel="stylesheet" href="https://fonts.ferry.vn/1.0.0/css/ferry-vn-fonts.css">
```

```css
h1, h2 { font-family: "Ferry VN Display", system-ui, sans-serif; }
body   { font-family: "Ferry VN Text", system-ui, sans-serif; }
code   { font-family: "Ferry VN Mono", ui-monospace, monospace; }
.gia   { font-variant-numeric: tabular-nums; }   /* hoặc class .ferry-tnum: số thẳng cột cho giá, giờ tàu */
.ma-ve { font-feature-settings: "zero" 1; }      /* hoặc class .ferry-zero: số 0 gạch chéo cho mã đặt chỗ */
```

Nạp sớm font quan trọng nhất (tuỳ chọn):

```html
<link rel="preload" href="https://fonts.ferry.vn/1.0.0/fonts/ferry-vn-display-bold.woff2" as="font" type="font/woff2" crossorigin>
```

| CSS | Nội dung | Dung lượng font |
|---|---|---|
| `css/ferry-vn-fonts.css` | Display + Text + Mono | ~40 KB/style (Display, Text), ~60 KB/style (Mono) |
| `css/ferry-vn-display.css` · `ferry-vn-text.css` · `ferry-vn-mono.css` | Từng họ riêng | như trên |
| `css/ferry-vn-nerd-mono.css` | Nerd Mono, **không** nằm trong CSS chung | ~1 MB/style |

Font web là WOFF2 đã cắt gọn còn Latin + tiếng Việt (Mono giữ thêm ký hiệu box-drawing, Powerline và icon Ferry). Nerd Mono giữ đầy đủ glyph, chỉ nạp khi thật sự cần, ví dụ terminal chạy trên web.

### Chính sách đường dẫn

Mỗi phiên bản nằm ở một đường dẫn riêng (`/1.0.0/`, `/1.0.1/`, `/1.1.0/`, ...) và **không bao giờ đổi nội dung** sau khi công bố. Server trả `Cache-Control: public, max-age=31536000, immutable` và `Access-Control-Allow-Origin: *`. Muốn nhận bản sửa lỗi thì đổi số phiên bản trong URL.

## Cài trên máy

Tải `FerryVN-Fonts-<phiên bản>.zip` ở [Releases](https://github.com/ferry-vn/ferry-fonts/releases/latest), giải nén, cài các file TTF trong `desktop/`:

- `desktop/Display/`, `desktop/Text/`: designer, Figma, Office.
- `desktop/Mono/`: IDE, tài liệu kỹ thuật (~270 KB/style).
- `desktop/NerdMono/`: terminal có prompt Powerline / icon Nerd Fonts (~2,5 MB/style).

## Icon Ferry (Mono và Nerd Mono)

| Mã | Icon | Mã | Icon | Mã | Icon |
|---|---|---|---|---|---|
| U+E100 | logo | U+E105 | neo | U+E10A | hành lý |
| U+E101 | tàu cao tốc | U+E106 | sóng | U+E10B | phao cứu sinh |
| U+E102 | vé | U+E107 | tuyến | U+E10C | QR (chỉ trang trí) |
| U+E103 | ghế | U+E108 | giờ tàu | | |
| U+E104 | bến | U+E109 | hành khách | | |

HTML: `&#xE101;` · CSS: `content: "\E101";` · JS: `"\uE101"`. Icon chỉ hiển thị khi phần tử dùng `Ferry VN Mono` hoặc `Ferry VN Nerd Mono`.

## Cấu trúc repo

```
site/                 Gốc CDN fonts.ferry.vn, deploy nguyên trạng
  _headers            CORS cho mọi file, cache 1 năm cho thư mục phiên bản
  _redirects          / → /1.0.0/ (trang demo)
  1.0.0/              index.html (demo), css/, fonts/ (WOFF2)
desktop/              23 file TTF, chia theo họ: Display, Text, Mono, NerdMono
specimens/            Ảnh specimen và phân tích độ rộng
source/               Script dựng font, đo benchmark, kiểm tra phát hành
LICENSES/             OFL của từng font gốc, NOTICE, giấy phép Nerd Fonts
wrangler.jsonc        Cấu hình Cloudflare Worker phục vụ site/
OFL.txt               SIL Open Font License 1.1
```

`source/` là script đã dùng để dựng bản 1.0.0, lưu để tham khảo. Các script dựng font cần font gốc (Be Vietnam Pro, JetBrains Mono, bản vá Nerd Fonts) không có trong repo, đường dẫn đầu vào phải sửa trước khi chạy lại. Riêng `qa_release.py` chạy được ngay trên repo:

```bash
pip install fonttools
python source/qa_release.py desktop
```

Script kiểm tra: đủ 146 ký tự tiếng Việt có dấu, tên PostScript không trùng, cho phép cài đặt và nhúng (`fsType 0`), version 1.000, Mono rộng đúng 600 và đủ 13 icon Ferry, lưu lại file không lỗi.

## Phát hành phiên bản mới

1. Thêm thư mục `site/<phiên bản mới>/` và **giữ nguyên mọi thư mục phiên bản cũ**. Mỗi lần deploy, Cloudflare thay toàn bộ asset bằng nội dung `site/` hiện tại; thiếu thư mục cũ là đường dẫn cũ bị mất.
2. Thêm khối `Cache-Control` cho thư mục mới trong `site/_headers`; đổi đích trong `site/_redirects` nếu muốn trang demo mặc định trỏ bản mới.
3. Cập nhật TTF trong `desktop/`, `CHANGELOG.md`, số phiên bản trong README.
4. Chạy `python source/qa_release.py desktop`.
5. Deploy: `npx wrangler deploy` (cần quyền Workers Scripts + Workers Custom Domains trên account chứa zone `ferry.vn`).
6. Tạo tag `v<phiên bản>` và GitHub Release kèm file zip.

## Hạn chế đã biết (1.0.0)

- Nghiêng của Display là nghiêng cơ học 8,2°, chưa chỉnh quang học.
- Kerning chân lướt do thuật toán tính, chưa duyệt tay.
- Glyph đã sửa trong Mono và icon Ferry chưa hinting; icon chưa tinh chỉnh dưới 16px.

Chi tiết trong [CHANGELOG.md](CHANGELOG.md).

## Giấy phép

Font phát hành theo [SIL Open Font License 1.1](OFL.txt): được dùng, nhúng, sửa và phân phối lại (kể cả thương mại), không được bán riêng file font. Xem [LICENSES/NOTICE.md](LICENSES/NOTICE.md) cho nguồn gốc từng họ.

**Ferry VN Nerd Mono** chứa các bộ icon do Nerd Fonts gộp vào, mỗi bộ giữ giấy phép riêng; phân phối lại phải kèm [LICENSES/NerdFonts-README.md](LICENSES/NerdFonts-README.md).

Giấy phép font không cấp quyền dùng tên và nhãn hiệu Ferry VN.
