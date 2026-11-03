"""Ban tieng Anh cua giao dien. Khoa la chuoi tieng Viet goc trong code."""
EN = {
    # --- Khung dich, trang thai ---
    "[AI từ chối dịch đoạn này]": "[The AI declined to translate this]",
    "Chưa nhập API key cho {name} (Cài đặt → Dịch).": "No API key for {name} yet (Settings → Translation).",
    "Không biết nhà cung cấp AI: {name}": "Unknown AI provider: {name}",
    "app không ở phía trước": "app is not in front",
    "● đang dịch": "● translating",
    "app bị thu nhỏ": "app is minimized",
    "↻ đang dịch lại…": "↻ translating again…",
    "vùng dịch đã cập nhật": "area updated",
    "menu ở khay hệ thống": "the tray menu",
    "mở cài đặt (ngôn ngữ, phím tắt, giao diện)": "open settings (languages, hotkeys, appearance)",
    " (vùng đã lưu)": " (saved area)",
    "vùng hiện tại không gắn với app nào": "the current area is not tied to any app",
    "❚❚ tạm dừng": "❚❚ paused",
    "chưa có câu nào để sửa": "nothing to fix yet",
    "chuột xuyên qua: tắt": "click-through: off",
    "Quên vùng của app hiện tại": "Forget the current app's area",
    "app đã đóng": "app closed",
    "đã quên vùng của {exe}": "forgot the area of {exe}",
    "Có bản mới {tag}. Mở trang tải về?": "Version {tag} is available. Open the download page?",
    "App đang chạy rồi. Tìm biểu tượng ở khay hệ thống (góc phải thanh taskbar).":
        "The app is already running. Look for its icon in the system tray (bottom right of the taskbar).",
    "Cài đặt chưa đúng": "Settings need attention",
    "chuột xuyên qua: bật, tắt bằng {hk}": "click-through: on, turn off with {hk}",
    "dịch nhanh một lần": "one-shot translation",
    "\nMở Cài đặt để xem chi tiết.": "\nOpen Settings for details.",
    "Lỗi OCR: {e}": "OCR error: {e}",
    "Dịch lại thất bại: {e}": "Translating again failed: {e}",
    "tạm dừng / tiếp tục": "pause / resume",
    "chọn vùng cần dịch": "select an area to translate",
    "App đang chạy ở khay hệ thống (góc phải thanh taskbar).":
        "The app is running in the system tray (bottom right of the taskbar).",
    "Google không trả lời (HTTP {code})": "Google did not answer (HTTP {code})",
    "Luồng dịch bị lỗi: {e}": "The translation worker stopped with an error: {e}",
    "Không khởi tạo được OCR hoặc máy dịch:": "Could not start OCR or the translation engine:",
    "máy dịch tạm chặn, thử lại sau {n}s": "translation engine is rate-limiting, retrying in {n}s",

    # --- Sua chu OCR ---
    "Sửa chữ gốc rồi dịch lại": "Fix the original text and translate again",
    "Sửa những chỗ OCR đọc nhầm rồi bấm Dịch lại:": "Fix what OCR misread, then click Translate again:",
    "Lưu các chỗ sửa vào bảng thay thế OCR để lần sau tự sửa":
        "Save these fixes to the OCR substitution table to fix them automatically next time",
    "Hủy": "Cancel",
    "Dịch lại": "Translate again",

    # --- Menu khung dich ---
    "Chọn vùng mới": "Select a new area",
    "Tạm dừng / tiếp tục": "Pause / resume",
    "Dịch lại ngay": "Translate again now",
    "Sửa chữ gốc rồi dịch lại…": "Fix the original text and translate again…",
    "Copy câu mới nhất": "Copy the latest translation",
    "Copy chữ gốc mới nhất": "Copy the latest original text",
    "Copy toàn bộ lịch sử": "Copy the whole history",
    "Hiện / ẩn chữ gốc": "Show / hide the original text",
    "Xóa lịch sử": "Clear history",
    "Chế độ phụ đề / lịch sử": "Subtitle / history mode",
    "Chuột bấm xuyên qua khung": "Click through the box",
    "Quên vùng của app này": "Forget this app's area",
    "Cài đặt…": "Settings…",
    "Ẩn khung": "Hide the box",
    "Thoát": "Quit",
    "độ trong suốt {p}%": "transparency {p}%",
    "chuột xuyên qua": "click-through",
    "Không tra được: {e}": "Lookup failed: {e}",
    "(không có nghĩa)": "(no meaning found)",
    "Giữ Shift và kéo qua nhiều từ để tra cả cụm": "Hold Shift and drag over several words to look up a phrase",

    # --- Dich nhanh, chon vung, chinh vung ---
    "Đang dịch…": "Translating…",
    "Sửa": "Fix",
    "Không đọc được chữ trong vùng này.": "No text could be read in this area.",
    "Đã copy": "Copied",
    "Dịch nhanh": "Quick translation",
    "Lỗi: ": "Error: ",
    "Kéo để dời vùng · kéo viền để chỉnh · {keys} lưu · Esc hủy":
        "Drag to move · drag the border to resize · {keys} save · Esc cancel",
    "Kéo chuột để chọn vùng cần dịch     Esc hoặc chuột phải để hủy":
        "Drag to select the area to translate     Esc or right-click to cancel",

    # --- Cua so cai dat: chung ---
    "Cài đặt – Screen Translator": "Settings – Screen Translator",
    "Cài đặt": "Settings",
    "Lưu": "Save",
    "Khôi phục mặc định": "Restore defaults",
    "Đưa mọi cài đặt về mặc định?": "Reset all settings to their defaults?",
    "Có ô nhập số không hợp lệ.": "A number field has an invalid value.",
    "Có hai chức năng đang dùng chung một phím tắt.": "Two actions are using the same hotkey.",
    "Có chỗ cài đặt chưa đúng:": "Some settings need attention:",
    "Có chỗ cài đặt chưa đúng:\n": "Some settings need attention:\n",
    "Vẫn lưu?": "Save anyway?",
    "… và {n} chỗ khác, xem các tab có dấu ⚠": "… and {n} more, see the tabs marked ⚠",
    "Lên": "Up",
    "Xuống": "Down",
    "Xóa": "Delete",
    "Thêm": "Add",
    "Đổi": "Change",

    # Ten tab
    "Ngôn ngữ": "Languages",
    "Nhận dạng": "OCR",
    "Dịch": "Translation",
    "Giao diện": "Appearance",
    "Lọc ảnh": "Image filter",
    "Thay thế": "Substitutions",
    "Nâng cao": "Advanced",
    "Hệ thống": "System",
    "Phím tắt": "Hotkeys",

    # Tab Ngon ngu
    "Ngôn ngữ gốc": "Source language",
    "Với Windows OCR, máy cần cài gói ngôn ngữ này: Settings → Time & language → Language & region → Add a language.":
        "Windows OCR needs this language pack installed: Settings → Time & language → Language & region → Add a language.",
    "Dịch sang": "Translate into",

    # Tab Nhan dang
    "Bộ nhận dạng chữ": "OCR engine",
    "Đường dẫn tesseract.exe": "Path to tesseract.exe",
    "Chọn tesseract.exe": "Choose tesseract.exe",
    "Tần suất quét": "Scan interval",
    "Tính bằng mili giây. Càng nhỏ thì dịch càng nhanh nhưng tốn CPU hơn.":
        "In milliseconds. Lower values translate faster but use more CPU.",
    "Phóng to ảnh trước khi đọc": "Upscale before reading",
    "Giúp đọc chữ nhỏ chính xác hơn.": "Helps read small text more accurately.",

    # Tab Dich
    "Thứ tự máy dịch": "Engine order",
    "Dùng máy trên cùng trước; máy đó bị chặn, mất mạng hay lỗi thì tự chuyển sang máy kế tiếp.":
        "The top engine is used first; if it is rate-limited, offline or fails, the next one takes over.",
    "Máy dịch": "Engine",
    "Thêm vào thứ tự": "Add to order",
    "Chọn một máy để xem và nhập API key, model của máy đó.": "Pick an engine to see and enter its API key and model.",
    "Cần giữ ít nhất một máy dịch.": "Keep at least one engine.",
    "Lấy miễn phí tại deepl.com/pro-api, chọn gói Free.": "Get one free at deepl.com/pro-api with the Free plan.",
    "Bản chính thức của Google Dịch, không bị chặn khi dịch nhiều. Bật “Cloud Translation API” trong Google Cloud rồi tạo API key ở mục Credentials. Mỗi tháng được miễn phí một lượng ký tự.":
        "The official Google Translate API, not rate-limited for heavy use. Enable “Cloud Translation API” in Google Cloud, "
        "then create an API key under Credentials. A monthly amount of characters is free.",
    "Lấy key": "Get key",
    "Tải danh sách": "Load list",
    "Có thể gõ tên model bất kỳ. Bấm “Tải danh sách” để lấy các model mới nhất bằng key của bạn.":
        "You can type any model name. Click “Load list” to fetch the latest models with your key.",
    "Nhập API key trước.": "Enter the API key first.",
    "Đang tải…": "Loading…",
    "Không tải được danh sách model:": "Could not load the model list:",
    "Số câu trước gửi kèm": "Previous lines sent",
    "Giúp AI hiểu mạch hội thoại, xưng hô nhất quán. 0 = không gửi.":
        "Helps the AI follow the conversation and keep pronouns consistent. 0 = none.",
    "Ghi chú cho AI": "Notes for the AI",
    "Ví dụ: “Doctor dịch là Tiến sĩ; giữ nguyên tên nhân vật; giọng văn trẻ trung.”":
        "Example: “Keep character names unchanged; casual, friendly tone.”",
    "Thử dịch": "Test",
    "Đang thử…": "Testing…",
    "Lỗi: {err}": "Error: {err}",
    "Làm sạch chữ OCR trước khi dịch": "Clean up OCR text before translating",
    "Tách tên người nói, giữ nguyên tên": "Detect the speaker's name and keep it untranslated",
    "Câu trước gửi kèm": "Previous lines sent",
    "Số câu trước gửi kèm cho Google Dịch miễn phí, 0 là tắt. Google trả về không tách đúng thì tự dịch riêng câu hiện tại.":
        "Previous lines sent with free Google Translate for context, 0 = off. If Google merges the lines, "
        "the current line is translated on its own.",
    "Giãn cách gửi dịch": "Send interval",
    "Tính bằng giây: hai lần gửi dịch cách nhau ít nhất bấy nhiêu. Tăng lên nếu hay bị Google chặn, giảm xuống nếu muốn câu mới hiện nhanh hơn.":
        "Minimum seconds between two translation requests. Increase it if Google rate-limits you, "
        "decrease it for faster updates.",

    # Tab Giao dien
    "Kiểu khung dịch": "Box style",
    "Phụ đề chỉ hiện câu mới nhất, chữ to, căn giữa phía dưới màn hình.":
        "Subtitle shows only the latest line in large text at the bottom center of the screen.",
    "Cỡ chữ phụ đề": "Subtitle size",
    "Vị trí khung dịch": "Box position",
    "Phông chữ": "Font",
    "Cỡ chữ": "Size",
    "Màu": "Colors",
    "Chữ": "Text",
    "Nền": "Background",
    "Mẫu màu": "Presets",
    "Độ trong suốt": "Transparency",
    "Áp dụng cho cả khung lẫn chữ. Giữ Ctrl và lăn chuột trên khung dịch để chỉnh nhanh.":
        "Applies to both the box and the text. Hold Ctrl and scroll on the box to adjust it quickly.",
    "Hiện cả chữ gốc phía trên bản dịch": "Show the original text above the translation",
    "Rê chuột vào chữ gốc để tra từ, giữ Shift kéo để tra cụm":
        "Hover the original text to look up words, Shift + drag for phrases",
    "Tự ẩn khung khi vùng dịch không còn chữ": "Hide the box when the area has no text",
    "Xem trước": "Preview",
    "Tiến sĩ, nhiệm vụ đã sẵn sàng.": "Doctor, the mission is ready.",
    "Cửa sổ cài đặt": "Settings window",
    "Giao diện sáng hoặc tối. Bấm Lưu rồi mở lại cửa sổ cài đặt để thấy thay đổi.":
        "Light or dark theme. Save, then reopen the settings window to see the change.",
    "Ngôn ngữ giao diện (Language)": "Interface language",
    "Bấm Lưu rồi mở lại cửa sổ cài đặt để thấy ngôn ngữ mới.":
        "Save, then reopen the settings window to see the new language.",
    "Tự động theo Windows": "Same as Windows",

    # Tab App
    "Nhớ vùng dịch theo từng app": "Remember the area per app",
    "Khi chọn vùng trên cửa sổ một app, vùng đó được nhớ theo app. Kéo cửa sổ app đi đâu, vùng dịch đi theo; thu nhỏ hoặc tắt app thì tự dừng.":
        "An area selected on an app's window is remembered for that app. Move the window and the area follows; "
        "minimize or close the app and translation stops.",
    "Tự bật dịch khi mở app đã lưu vùng": "Start translating when an app with a saved area opens",
    "Vùng dịch co giãn theo kích thước cửa sổ app": "Scale the area with the app window size",
    "Đổi kích thước cửa sổ hoặc độ phân giải thì vùng dịch phóng to thu nhỏ theo. Di chuyển cửa sổ không ảnh hưởng, vùng dịch luôn đi theo.":
        "Resizing the window or changing the resolution scales the area. Moving the window doesn't, the area just follows.",
    "Chỉ dịch khi app đang ở phía trước": "Only translate while the app is in front",
    "Chuyển sang cửa sổ khác thì tạm dừng và ẩn khung dịch, tránh dịch nhầm chữ của cửa sổ khác. Quay lại app thì dịch tiếp.":
        "Switching to another window pauses and hides the box so other windows' text isn't translated. "
        "Back in the app, translation resumes.",
    "App đã lưu vùng:": "Apps with a saved area:",
    "Xóa app đã chọn": "Remove selected app",
    "Chưa có. Bấm phím chọn vùng trên cửa sổ một app để lưu.":
        "None yet. Press the select hotkey on an app's window to save one.",

    # Tab Loc anh
    "Lọc theo màu chữ": "Filter by text color",
    "Chỉ giữ chữ có màu": "Keep only text of color",
    "Bỏ hết nền, chỉ giữ chữ đúng màu này. Bấm vào ảnh gốc bên dưới để lấy màu chữ.":
        "Removes the background and keeps only text of this color. Click the original image below to pick the color.",
    "Độ lệch màu": "Color tolerance",
    "Phần trăm lệch so với màu chữ vẫn được giữ. Tăng nếu chữ bị mất nét.":
        "How far (in %) from the text color is still kept. Increase it if letters lose strokes.",
    "Xử lý thêm": "Extra processing",
    "Tăng tương phản": "Increase contrast",
    "Đảo màu": "Invert",
    "Làm nét": "Sharpen",
    "Chuyển đen trắng": "Black and white",
    "Ngưỡng sáng tính theo %, điểm sáng hơn thành trắng, tối hơn thành đen. 0 là tắt.":
        "Brightness threshold in %: brighter pixels become white, darker ones black. 0 = off.",
    "Chụp vùng dịch để xem trước": "Capture the area to preview",
    "Chưa có vùng dịch. Bấm phím chọn vùng trước.": "No area yet. Press the select hotkey first.",
    "Ảnh gốc": "Original",
    "Sau khi lọc": "Filtered",
    "Đang đọc chữ…": "Reading text…",
    "Chữ đọc được: ": "Text read: ",
    "(không đọc được chữ nào)": "(no text read)",
    "Đã lấy màu chữ {c}": "Text color set to {c}",

    # Tab Thay the
    "Tự sửa những chữ OCR hay đọc nhầm trước khi dịch, ví dụ “rn” thành “m”, “0” thành “O”. Áp dụng từ trên xuống dưới.":
        "Automatically fixes text OCR often misreads before translating, e.g. “rn” to “m”, “0” to “O”. Applied top to bottom.",
    "Chữ OCR đọc nhầm": "Misread text",
    "Sửa thành": "Replace with",
    "Cả từ": "Whole word",
    "Sửa dòng đang chọn": "Update selected",
    "“Cả từ”: chỉ sửa khi đứng riêng thành một từ, để “Dr” → “Doctor” không làm hỏng chữ “Drone”.":
        "“Whole word”: only replace standalone words, so “Dr” → “Doctor” doesn't break “Drone”.",
    "Thử:": "Try:",

    # Tab Nang cao
    "Ngưỡng thay đổi": "Change threshold",
    "Phần trăm điểm ảnh trong vùng phải đổi thì mới đọc lại chữ. Để thấp cho chắc không sót câu; chỉ tăng nếu nền động làm máy chạy nặng.":
        "Percentage of pixels in the area that must change before the text is read again. Keep it low so no line "
        "is missed; only increase it if an animated background makes the app work too hard.",
    "Mức đổi một điểm ảnh": "Pixel change level",
    "Một điểm ảnh sáng hoặc tối đi bao nhiêu phần trăm thì mới tính là đổi. Tăng nếu nhiễu hình làm app đọc lại liên tục.":
        "How much (in %) a pixel must get brighter or darker to count as changed. Increase it if image noise keeps "
        "triggering new reads.",
    "Số lần đọc giống nhau": "Identical reads needed",
    "Đọc ra cùng một chữ bấy nhiêu lần liên tiếp mới dịch, tránh dịch chữ đang hiện dần. 1 là dịch ngay.":
        "The same text must be read this many times in a row before translating, so text that is still appearing "
        "isn't translated. 1 = translate immediately.",
    "Số lần đọc khác nhau": "Changing reads limit",
    "Chữ đổi liên tục bấy nhiêu lần thì dịch luôn bản mới nhất. 0 là tắt.":
        "If the text keeps changing this many times in a row, translate the latest version anyway. 0 = off.",
    "Nghỉ khi bị chặn": "Pause when rate-limited",
    "Số giây tạm nghỉ khi máy dịch báo gửi quá nhiều, lần sau gấp đôi.":
        "Seconds to pause when an engine reports too many requests; doubles each time.",
    "Số câu trong lịch sử": "History length",
    "Số câu giữ lại trong khung dịch để lăn chuột xem lại.": "Number of lines kept in the box to scroll back through.",
    "Ẩn khi không thấy chữ": "Hide after empty reads",
    "Đọc bấy nhiêu lần liên tiếp không thấy chữ thì tự ẩn khung, nếu bật tự ẩn.":
        "Hide the box after this many reads in a row without text, when auto-hide is on.",
    "Ghi log chi tiết để tìm lỗi": "Detailed logging for troubleshooting",
    "Ghi từng lần đọc chữ và dịch vào app.log. Chỉ bật khi cần tìm lỗi.":
        "Writes every read and translation to app.log. Only turn on when troubleshooting.",
    "Đặt lại mục này về mặc định": "Reset this tab to defaults",

    # Tab He thong
    "Khởi động cùng Windows": "Start with Windows",
    "App tự chạy ẩn ở khay hệ thống mỗi khi bật máy.": "The app starts hidden in the system tray when you sign in.",
    "Dùng khi mạng chặn Google hoặc phải đi qua proxy công ty, ví dụ http://127.0.0.1:8080. Để trống là không dùng.":
        "Use it when your network blocks Google or requires a company proxy, e.g. http://127.0.0.1:8080. "
        "Leave empty for none.",
    "Tự kiểm tra bản mới khi mở app": "Check for updates when the app starts",
    "Phiên bản hiện tại: {v}": "Current version: {v}",
    "Kiểm tra ngay": "Check now",
    "Đang kiểm tra…": "Checking…",
    "Không kiểm tra được: {err}": "Could not check: {err}",
    "Có bản mới {tag}": "Version {tag} is available",
    "Cập nhật": "Update",
    "Đang dùng bản mới nhất.": "You have the latest version.",
    "Chưa có bản phát hành nào trên GitHub.": "No release on GitHub yet.",
    "config.json và app.log nằm cùng thư mục với app, chép cả thư mục sang máy khác là dùng được ngay.":
        "config.json and app.log live next to the app; copy the whole folder to another PC and it just works.",

    # Tab Phim tat
    "Nhấn phím…": "Press keys…",
    "Bấm “Đổi” rồi nhấn tổ hợp phím mới, Esc để hủy.": "Click “Change” and press the new key combination, Esc to cancel.",

    # --- May dich: loi ---
    "Chưa nhập API key cho Google Cloud (Cài đặt → Dịch).": "No Google Cloud API key yet (Settings → Translation).",
    "phản hồi rỗng": "empty response",
    "Chưa nhập DeepL API key.": "No DeepL API key yet.",
    "phản hồi không hợp lệ": "invalid response",
    "Không kết nối được tới Google Dịch ({detail}). Kiểm tra mạng.":
        "Could not reach Google Translate ({detail}). Check your connection.",
    "Không có máy dịch nào dùng được. ": "No usable translation engine. ",
    "Mọi máy dịch đều lỗi: ": "All translation engines failed: ",
    "Google tạm chặn ({detail})": "Google is rate-limiting ({detail})",
    "không kết nối được: {name}": "connection failed: {name}",
    "dịch bằng {engine} ({failed} đang lỗi)": "translated with {engine} ({failed} unavailable)",

    # --- Kiem tra cai dat ---
    "Ngôn ngữ gốc trùng với ngôn ngữ dịch sang.": "The source language is the same as the target language.",
    "Không còn máy dịch nào dùng được. Nhập API key hoặc thêm Google Dịch vào thứ tự.":
        "No usable engine left. Enter an API key or add Google Translate to the order.",
    "Màu chữ để lọc không hợp lệ.": "The text color for the filter is invalid.",
    "Proxy phải có dạng http://máy:cổng, ví dụ http://127.0.0.1:8080.":
        "The proxy must look like http://host:port, e.g. http://127.0.0.1:8080.",
    "{engine} chưa có API key nên sẽ bị bỏ qua.": "{engine} has no API key and will be skipped.",
    "Phím tắt bị trùng: ": "Duplicate hotkeys: ",
    "Không đăng ký được phím {combo}, có thể app khác đang dùng.":
        "Could not register {combo}; another app may be using it.",
    "Không tìm thấy tesseract.exe ở “{cmd}”.": "tesseract.exe not found at “{cmd}”.",
    "Windows chưa cài gói nhận dạng chữ cho {lang}. Vào Settings → Time & language → Language & region → Add a language để thêm.":
        "Windows has no OCR language pack for {lang}. Add it in Settings → Time & language → Language & region → "
        "Add a language.",
    "Tesseract chưa có dữ liệu cho {lang} ({code}).": "Tesseract has no data for {lang} ({code}).",
    "Không chạy được Tesseract: {e}": "Could not run Tesseract: {e}",

    # --- Ten ngon ngu ---
    "Tiếng Anh": "English",
    "Tiếng Nhật": "Japanese",
    "Tiếng Trung giản thể": "Chinese (Simplified)",
    "Tiếng Trung phồn thể": "Chinese (Traditional)",
    "Tiếng Hàn": "Korean",
    "Tiếng Nga": "Russian",
    "Tiếng Pháp": "French",
    "Tiếng Đức": "German",
    "Tiếng Tây Ban Nha": "Spanish",
    "Tiếng Bồ Đào Nha": "Portuguese",
    "Tiếng Ý": "Italian",
    "Tiếng Thái": "Thai",
    "Tiếng Việt": "Vietnamese",

    # --- Ten phim tat ---
    "Chọn vùng dịch": "Select area",
    "Ẩn / hiện khung dịch": "Show / hide the box",
    "Dịch nhanh một lần": "One-shot translation",
    "Chỉnh vùng dịch": "Adjust area",
    "Chế độ phụ đề": "Subtitle mode",
    "Chuột xuyên qua khung": "Click-through",
    "Mở cài đặt": "Open settings",

    # --- Lua chon ---
    "Google Dịch": "Google Translate",
    "Bên dưới vùng chọn": "Below the area",
    "Bên trên vùng chọn": "Above the area",
    "Đè lên vùng chọn": "Over the area",
    "Sáng": "Light",
    "Tối": "Dark",
    "Lịch sử các câu": "History of lines",
    "Phụ đề câu mới nhất": "Subtitle of the latest line",
    "Phụ đề vàng": "Yellow subtitle",
    "Xanh đêm": "Night blue",
    "Xanh lá": "Green",
}
