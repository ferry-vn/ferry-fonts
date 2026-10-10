# Changelog

## 1.0.0 — 10/2026
Phát hành đầu tiên. Big idea: "Lướt app. Lướt sóng."

- Ferry VN Display: Light, Regular, Bold, Black, Bold Oblique. Chân lướt (A, R, K, k), góc mềm, tab mềm, khớp cong Y,
  hình học squircle 0,30. Độ rộng ở trung vị của 29 font sans phổ biến; chỉ thu gọn chữ tròn. Kerning riêng cho chân lướt.
- Ferry VN Text: Regular, Medium, SemiBold, Bold và Italic từng độ đậm. Chữ l có đuôi, số bảng (tnum),
  số 0 gạch chéo (zero), mũi tên → ←, squircle 0,18, hinting ttfautohint.
- Ferry VN Mono: Regular, Medium, Bold, Italic, Bold Italic, dựng trên JetBrains Mono 2.304. Góc mềm A L F, khớp cong Y,
  13 icon Ferry ở U+E100–E10C, ký hiệu Powerline gốc của JetBrains Mono, ligature lập trình.
- Ferry VN Nerd Mono: như Ferry VN Mono, thêm toàn bộ icon Nerd Fonts 3.5.1 cho terminal.
- Web: WOFF2 cắt gọn Latin + tiếng Việt (Display/Text ~40 KB, Mono ~60 KB mỗi style); Nerd Mono WOFF2 đầy đủ (~1 MB mỗi style).

### Hạn chế đã biết
- Nghiêng của Display là nghiêng cơ học 8,2°, chưa chỉnh quang học.
- Hinting là ttfautohint (Display, Text) hoặc giữ của JetBrains Mono (Mono); glyph đã sửa trong Mono và icon Ferry chưa hinting.
- Kerning chân lướt do thuật toán tính, chưa duyệt tay.
- Icon Ferry dựng hình học, chưa tinh chỉnh dưới 16px; icon QR chỉ để trang trí.
