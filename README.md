# Screen Translator

App Windows nhỏ để dịch chữ trên màn hình theo thời gian thực (lấy ý tưởng từ [Translumo](https://github.com/ramjke/translumo)).
Bấm phím tắt → kéo chuột chọn vùng (ví dụ khung thoại trong game) → app tự OCR và dịch mỗi khi chữ trong vùng đổi.

## Phím tắt mặc định

| Phím | Chức năng |
|---|---|
| `Alt+Q` | Chọn vùng mới và bắt đầu dịch liên tục |
| `Alt+W` | Tạm dừng / tiếp tục dịch |
| `Alt+E` | Dịch lại vùng hiện tại ngay |
| `Alt+H` | Ẩn / hiện khung dịch |
| `Ctrl+Alt+X` | Thoát |

Khung dịch: kéo bằng chuột trái để di chuyển, chuột phải để mở menu (copy bản dịch, hiện chữ gốc...).
App cũng có icon ở khay hệ thống (góc phải thanh taskbar).

## Cài và chạy

1. Cài [Python 3.10+](https://www.python.org/downloads/) — nhớ tick **Add python.exe to PATH**.
2. Nháy đúp `run.bat` (lần đầu sẽ tự tạo `.venv` và cài thư viện).

Muốn có file `.exe` để chạy không cần Python: nháy đúp `build.bat` → lấy `dist\ScreenTranslator.exe`.

> Nếu phím tắt không ăn khi đang ở trong game chạy quyền Admin, hãy chạy app bằng *Run as administrator*.

## Cấu hình (`config.json`)

File được tạo tự động lần chạy đầu (cạnh `run.bat` hoặc cạnh file `.exe`). Sửa xong thì khởi động lại app.

| Khóa | Ý nghĩa |
|---|---|
| `hotkeys` | Đổi phím tắt, ví dụ `"ctrl+shift+t"` |
| `ocr_engine` | `windows` (OCR có sẵn của Win10/11, nhanh) hoặc `tesseract` |
| `ocr_lang` | Ngôn ngữ chữ gốc cho Windows OCR: `en-US`, `ja`, `ko`, `zh-Hans-CN`... |
| `source_lang` / `target_lang` | Mã ngôn ngữ cho máy dịch: `auto`, `en`, `ja`, `zh-CN`, `vi`... |
| `translator` | `google` (miễn phí) hoặc `deepl` (cần điền `deepl_api_key`) |
| `interval_ms` | Bao lâu chụp lại vùng một lần (mặc định 600 ms) |
| `change_threshold` | Ảnh phải đổi bao nhiêu mới OCR lại — tăng lên nếu nền động làm app dịch liên tục |
| `upscale` | Phóng to ảnh trước khi OCR, giúp đọc chữ nhỏ |
| `overlay.position` | `below` (dưới vùng), `above` (trên), `over` (đè lên vùng) |
| `overlay.*` | Font, cỡ chữ, màu, độ trong suốt |

### Đọc tiếng Nhật / Trung / Hàn bằng Windows OCR

Windows chỉ OCR được những ngôn ngữ đã cài gói ngôn ngữ. Vào **Settings → Time & language → Language & region → Add a language**, thêm ngôn ngữ cần đọc (chỉ cần phần *Optical character recognition*). Kiểm tra bằng PowerShell:

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'Language.OCR*'
```

Sau đó đặt `"ocr_lang": "ja"` (ví dụ) trong `config.json`.

### Dùng Tesseract thay thế

Cài [Tesseract cho Windows](https://github.com/UB-Mannheim/tesseract/wiki) kèm gói ngôn ngữ, rồi đặt `"ocr_engine": "tesseract"`, `"tesseract_lang": "jpn"` và đường dẫn `tesseract_cmd`.

## Cách hoạt động

```
phím tắt ─▶ chọn vùng ─▶ [luồng nền] chụp vùng (mss) ─▶ ảnh đổi? ─▶ OCR ─▶ chữ đổi? ─▶ dịch (có cache) ─▶ khung dịch
```

- Chỉ OCR khi ảnh trong vùng thay đổi, chỉ gọi máy dịch khi chữ thay đổi → nhẹ máy, ít bị Google chặn.
- Khung dịch được ẩn khỏi ảnh chụp màn hình (Win10 2004+), nên đặt đè lên vùng cũng không bị đọc lại chính nó.

| File | Nội dung |
|---|---|
| `screentrans/app.py` | Khởi động, phím tắt, khay hệ thống, điều phối |
| `screentrans/selector.py` | Lớp phủ toàn màn hình để chọn vùng |
| `screentrans/overlay.py` | Khung hiện bản dịch |
| `screentrans/worker.py` | Luồng chụp → OCR → dịch |
| `screentrans/ocr.py` | Windows OCR / Tesseract |
| `screentrans/translator.py` | Google / DeepL + cache |
| `screentrans/config.py` | Đọc/ghi `config.json` |
