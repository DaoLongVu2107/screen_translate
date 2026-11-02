"""Dich bang AI (Claude, ChatGPT, Gemini, Grok) voi API key cua nguoi dung."""
import logging
from collections import deque

log = logging.getLogger(__name__)

# ten -> (ten hien thi, model goi y, trang lay key)
PROVIDERS = {
    "claude": ("Claude", ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"],
               "https://platform.claude.com/settings/keys"),
    "openai": ("ChatGPT", ["gpt-5.4-mini", "gpt-5.4"],
               "https://platform.openai.com/api-keys"),
    "gemini": ("Gemini", ["gemini-flash-latest", "gemini-pro-latest"],
               "https://aistudio.google.com/apikey"),
    "grok": ("Grok", ["grok-4.3", "grok-4.6"], "https://console.x.ai"),
}
XAI_BASE_URL = "https://api.x.ai/v1"
# Model Claude ho tro tu chuyen sang model khac khi bi tu choi (server-side fallback)
CLAUDE_FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}

SYSTEM_PROMPT = """You translate text captured from the user's screen (games, videos, apps) from {src} into {dst}.
The text comes from OCR, so it may contain recognition mistakes, broken line breaks or stray symbols: silently fix obvious OCR errors.
Translate naturally, the way a fluent native {dst} speaker would write subtitles or game dialogue. Keep character names, pronouns and forms of address consistent with the earlier lines.
Reply with the translation only: no quotes, notes, explanations or the original text."""


class AiTranslator:
    def __init__(self, provider: str, api_key: str, model: str, src_name: str, dst_name: str,
                 notes: str = "", context_lines: int = 3):
        if not api_key:
            raise ValueError(f"Chưa nhập API key cho {PROVIDERS[provider][0]} (Cài đặt → Dịch).")
        self.provider, self.model = provider, model or PROVIDERS[provider][1][0]
        self.system = SYSTEM_PROMPT.format(src=src_name, dst=dst_name)
        if notes.strip():
            self.system += "\n\nUser's notes (glossary, style), always follow them:\n" + notes.strip()
        self.history: deque[tuple[str, str]] = deque(maxlen=max(0, context_lines))
        self._use_effort = True

        if provider == "claude":
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key, timeout=30, max_retries=1)
        elif provider in ("openai", "grok"):
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key, timeout=30, max_retries=1,
                                  base_url=XAI_BASE_URL if provider == "grok" else None)
        elif provider == "gemini":
            from google import genai
            self._client = genai.Client(api_key=api_key)
        else:
            raise ValueError(f"Không biết nhà cung cấp AI: {provider}")

    def _user_message(self, text: str) -> str:
        parts = []
        if self.history:
            ctx = "\n".join(f"- {s}  =>  {d}" for s, d in self.history)
            parts.append(f"Earlier lines and their translations (context only, do not repeat):\n{ctx}\n")
        parts.append(f"Translate this:\n{text}")
        return "\n".join(parts)

    def translate(self, text: str) -> str:
        msg = self._user_message(text)
        result = getattr(self, f"_call_{self.provider}")(msg).strip()
        if result:
            self.history.append((text, result))
        return result

    # --- tung nha cung cap ---
    def _call_claude(self, msg: str) -> str:
        import anthropic
        kwargs = dict(model=self.model, max_tokens=4096, system=self.system,
                      messages=[{"role": "user", "content": msg}])
        if self._use_effort:
            kwargs["output_config"] = {"effort": "low"}   # dich nhanh, it suy nghi
        try:
            if self.model in CLAUDE_FALLBACK_MODELS:
                resp = self._client.beta.messages.create(
                    betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
            else:
                resp = self._client.messages.create(**kwargs)
        except anthropic.BadRequestError as e:
            if self._use_effort and "effort" in str(e).lower():   # model cu khong ho tro effort
                self._use_effort = False
                return self._call_claude(msg)
            raise
        if resp.stop_reason == "refusal":
            return "[AI từ chối dịch đoạn này]"
        return "".join(b.text for b in resp.content if b.type == "text")

    def _call_openai(self, msg: str) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": self.system},
                      {"role": "user", "content": msg}],
        )
        return resp.choices[0].message.content or ""

    _call_grok = _call_openai

    def _call_gemini(self, msg: str) -> str:
        from google.genai import types
        resp = self._client.models.generate_content(
            model=self.model, contents=msg,
            config=types.GenerateContentConfig(system_instruction=self.system),
        )
        return resp.text or ""


def list_models(provider: str, api_key: str) -> list[str]:
    """Lay danh sach model tu nha cung cap bang key cua nguoi dung."""
    if provider == "claude":
        import anthropic
        return [m.id for m in anthropic.Anthropic(api_key=api_key, timeout=20).models.list()]
    if provider in ("openai", "grok"):
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=20,
                        base_url=XAI_BASE_URL if provider == "grok" else None)
        ids = sorted((m.id for m in client.models.list()), reverse=True)
        if provider == "openai":   # bo model khong phai chat (anh, giong noi, embedding...)
            skip = ("embedding", "whisper", "tts", "dall-e", "image", "audio", "realtime",
                    "moderation", "transcribe", "search", "davinci", "babbage", "sora")
            ids = [i for i in ids if not any(s in i for s in skip)]
        return ids
    if provider == "gemini":
        from google import genai
        out = []
        for m in genai.Client(api_key=api_key).models.list():
            actions = getattr(m, "supported_actions", None) or []
            if not actions or "generateContent" in actions:
                out.append(m.name.removeprefix("models/"))
        return out
    return []
