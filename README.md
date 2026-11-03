# Screen Translator

[![Download latest](https://img.shields.io/github/v/release/DaoLongVu2107/screen_translate?label=download&color=0a7cff)](https://github.com/DaoLongVu2107/screen_translate/releases/latest)
[![Windows 10/11](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows)](https://github.com/DaoLongVu2107/screen_translate/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**English** · [Tiếng Việt](README.vi.md)

**Real-time screen translator for Windows.** Press a hotkey, drag over any part of the screen (game dialogue, video subtitles, chat windows, documents) and the text is read with OCR and translated live, every time it changes. A free, lightweight alternative to Translumo with Google Translate, DeepL and AI translation (Claude, ChatGPT, Gemini, Grok).

![The translation box shows right under the game dialogue](docs/images/demo.png)

## Download

Go to **[Releases](https://github.com/DaoLongVu2107/screen_translate/releases/latest)**, download `ScreenTranslator.exe` and run it. Nothing else to install.

> Windows may show a SmartScreen warning because the file is not code-signed yet: click **More info → Run anyway**.

Requirements: Windows 10 or 11.

> The interface is available in **English** and **Vietnamese** and follows your Windows language by default (change it in Settings → Appearance → Interface language). It translates between English, Japanese, Chinese, Korean, Russian, French, German, Spanish, Portuguese, Italian, Thai and Vietnamese.

## Features

**Translate**
- Live translation: pick an area once, it re-translates every time the text changes
- One-shot translation (Google Lens style): select an area, get the translation with a Copy button
- Translation engines: free Google Translate, Google Cloud Translation, DeepL, or AI (Claude, ChatGPT, Gemini, Grok) with your own API key
- Engine fallback chain: if the first engine is rate-limited or offline, the next one takes over automatically
- AI translation keeps the conversation context, consistent pronouns and character names, and follows your own glossary notes

**Read text accurately**
- OCR with the built-in Windows OCR, or Tesseract
- Image filters before OCR (keep only the text color, contrast, invert, sharpen, black and white) with a live preview
- Automatic OCR cleanup and speaker name detection: only the dialogue is translated, names are kept
- Fix misread text and translate again; a substitution table automatically fixes words OCR keeps getting wrong

**Translation box**
- Drag it anywhere, resize it, scroll back through the history of previous lines
- Subtitle mode: only the latest line, large text, centered at the bottom of the screen
- Click-through mode: the box stays on top of the game while your clicks go through to the game
- Hover over a word in the original text to see its meanings, hold `Shift` and drag to look up a whole phrase
- Hides itself when the area has no text, light and dark themes, custom font, colors and transparency

**Works with your apps and games**
- Remembers the area per app: open the game and it starts translating, move the window and the area follows, resize it and the area scales
- Show and adjust the area border directly without selecting again
- Only translates while the app is in front; pauses when minimized or when you switch windows
- Checks your settings and points out problems (missing API keys, missing OCR language packs, duplicate hotkeys...)
- English and Vietnamese interface, start with Windows, proxy support, update notifications

## Hotkeys

| Key | Action |
|---|---|
| `Alt + Q` | Select an area to translate (starts live translation) |
| `Alt + W` | Pause / resume |
| `Alt + E` | Translate again now |
| `Alt + D` | One-shot translation: select an area, see the translation, done |
| `Alt + H` | Show / hide the translation box |
| `Alt + C` | Toggle click-through for the translation box |
| `Alt + R` | Show the area border to adjust it; press again or `Enter` to save, `Esc` to cancel |
| `Alt + V` | Switch between subtitle mode and history mode |
| `Alt + S` | Open settings |
| `Ctrl + Alt + X` | Quit |

All hotkeys can be changed in Settings.

## How to use

1. Run `ScreenTranslator.exe`. The app lives in the system tray (bottom right of the taskbar).
2. Press `Alt + Q` and drag around the text you want to translate. Press `Esc` or right-click to cancel.
3. The translation appears in a small box right under the area and updates whenever the text changes.
   - Drag anywhere on the box to move it, drag the bottom-right corner to resize it.
   - New lines appear at the bottom and older ones move up; scroll to read them again.
   - Hold `Ctrl` and scroll on the box to change its transparency.
   - Right-click the box to copy the translation, show the original text, fix misread text, pick a new area...
4. Press `Alt + S` (or right-click the tray icon → **Open settings**) to change languages, engines, appearance, hotkeys and per-app behavior.

![Settings window](docs/images/settings.png)

## Translating with AI

AI translations read much more naturally, follow the flow of the conversation and keep names consistent.

1. Open Settings → **Translation** tab and pick an AI engine.
2. Click **Get key** to open the provider's API key page, then paste the key into **API key**.
3. Choose a model (click **Load list** to fetch the latest models), then click **Test** to check it works.
4. Optionally write notes for the AI, for example: *"Keep character names unchanged; casual tone"*.
5. Add it to the **Engine order** together with other engines as backups.

AI usage is billed by the provider based on the amount of text. The app only calls the AI when the text on screen changes.

## Tips

- **Reading Japanese, Chinese, Korean...**: Windows needs the OCR language pack. Go to *Settings → Time & language → Language & region → Add a language* and add the language you want to read.
- **Busy or animated backgrounds**: open the **Image filter** tab, capture a preview and click on the text to keep only that color.
- **Rate-limited by Google**: add another engine to the engine order, or increase the send interval in the **Translation** tab.
- **Hotkeys don't work inside a game**: right-click `ScreenTranslator.exe` → *Run as administrator*.
- **Fullscreen games**: switch the game to *Borderless* or *Windowed* mode so the translation box can stay on top.
- **Select only the text area**: translation is faster and more accurate.

## Build from source

Install [Python 3.10+](https://www.python.org/downloads/), then run `build.bat`. The executable is created at `dist\ScreenTranslator.exe`. Use `run.bat` to run the app without building.

## License

[MIT](LICENSE)
