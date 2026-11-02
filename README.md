# Screen Translator

App Windows nhỏ dịch chữ trên màn hình theo thời gian thực. Bấm phím tắt, kéo chuột chọn một vùng (khung thoại trong game, phụ đề video, cửa sổ chat...). App sẽ tự đọc chữ trong vùng đó và hiện bản dịch tiếng Việt mỗi khi chữ thay đổi.


## Tải về

Vào trang **[Releases](../../releases/latest)**, tải `ScreenTranslator.exe` rồi chạy. Không cần cài đặt gì thêm.

> Windows có thể hiện cảnh báo SmartScreen vì file chưa có chữ ký số: bấm **More info → Run anyway**.

Yêu cầu: Windows 10 hoặc 11.

## Phím tắt

| Phím | Chức năng |
|---|---|
| `Alt + Q` | Chọn vùng cần dịch (bắt đầu dịch tự động) |
| `Alt + W` | Tạm dừng / tiếp tục dịch |
| `Alt + E` | Dịch lại ngay |
| `Alt + H` | Ẩn / hiện khung dịch |
| `Alt + S` | Mở cài đặt |
| `Ctrl + Alt + X` | Thoát |

Mọi phím tắt đều đổi được trong phần Cài đặt.

## Cách dùng

1. Chạy `ScreenTranslator.exe`. App nằm ở khay hệ thống (góc phải thanh taskbar).
2. Bấm `Alt + Q`, kéo chuột quanh vùng có chữ cần dịch. Bấm `Esc` hoặc chuột phải để hủy.
3. Bản dịch hiện trong một khung nhỏ ngay dưới vùng đã chọn và tự cập nhật khi chữ thay đổi.
   - Kéo khung để di chuyển.
   - Chuột phải vào khung để copy bản dịch, xem chữ gốc, chọn vùng mới...
4. Bấm `Alt + S` (hoặc chuột phải icon ở khay → **Mở cài đặt**) để chỉnh:
   - **Ngôn ngữ**: ngôn ngữ gốc và ngôn ngữ cần dịch sang
   - **Nhận dạng chữ**: Windows OCR hoặc Tesseract, tốc độ quét
   - **Dịch**: Google Dịch (miễn phí) hoặc DeepL
   - **Giao diện**: phông chữ, cỡ chữ, màu, độ trong suốt, vị trí khung dịch
   - **Phím tắt**

## Mẹo

- **Dịch tiếng Nhật, Trung, Hàn...**: Windows cần có gói ngôn ngữ đó. Vào *Settings → Time & language → Language & region → Add a language* và thêm ngôn ngữ cần đọc.
- **Phím tắt không ăn khi đang trong game**: chuột phải `ScreenTranslator.exe` → *Run as administrator*.
- **Nên chọn vùng vừa khít phần chữ**: dịch sẽ nhanh và chính xác hơn.
