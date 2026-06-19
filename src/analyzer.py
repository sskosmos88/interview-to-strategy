"""Analyze a raw interview transcript and extract structured blocks.

Supports multiple LLM providers:
- Anthropic Claude (ANTHROPIC_API_KEY)
- Ollama local models (OLLAMA_URL, OLLAMA_MODEL)
- Perplexity (PERPLEXITY_API_KEY, PERPLEXITY_MODEL)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore

try:
    import requests
except ImportError:  # type: ignore
    requests = None  # type: ignore


try:
    import openai
except ImportError:  # type: ignore
    openai = None  # type: ignore


SECTIONS = [
    "expert_info",
    "services",
    "audience",
    "competitors",
    "cases",
    "resources",
    "goals",
    "fears",
    "quotes",
]


@dataclass
class InterviewData:
    name: str = ""
    role: str = ""
    offer: str = ""
    difference: str = ""
    audience: list[str] = field(default_factory=list)
    services: list[dict] = field(default_factory=list)
    cases: list[dict] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    barriers: list[str] = field(default_factory=list)
    quotes: list[str] = field(default_factory=list)
    price_low: str = ""
    price_high: str = ""
    format_notes: str = ""
    geography: str = ""
    contacts: dict = field(default_factory=dict)
    years_experience: str = ""


def clean_transcript(text: str) -> str:
    """Remove timestamps and speaker labels commonly found in transcripts."""
    # Remove [00:01:23] style timestamps
    text = re.sub(r"\[?\d{1,2}:\d{2}:\d{2}\]?", "", text)
    # Remove "Speaker 1:" and generic interviewer/expert labels
    text = re.sub(r"(?i)(speaker\s*\d+|я|саша|продюсер|интервьюер|эксперт)\s*[:\-]", "", text)
    # Remove "Интервью с ..." header line so it is not mistaken for role
    text = re.sub(r"(?i)^интервью\s+с\s+[^.\n]+\.?\s*\d{1,2}\s+[а-я]+\s+\d{4}\.?\n?", "", text, count=1)
    # Collapse multiple whitespace
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _build_prompt(transcript: str, name: str) -> str:
    return f"""Ты — опытный продюсер и маркетолог. Тебе дали сырую расшифровку стратегического интервью со специалистом.

Извлеки из текста структурированные данные в формате JSON со следующими ключами:
- name: имя специалиста (если не указано, используй "{name}")
- role: роль / профессия
- offer: главное УТП в 1 предложении
- difference: чем отличается от других
- audience: список строк с описанием аудиторий/сценариев
- services: список объектов {{"name": ..., "price": ..., "format": ..., "description": ...}}
- cases: список объектов {{"before": ..., "work": ..., "after": ...}} — обезличенные кейсы
- channels: список строк — текущие каналы продвижения
- goals: список строк — цели на ближайшие 3–6 месяцев
- barriers: список строк — препятствия, страхи, возражения
- quotes: список строк — точные цитаты специалиста, которые можно использовать в текстах
- price_low: цена самой доступной услуги
- price_high: цена самой дорогой услуги
- format_notes: форматы работы (онлайн, офлайн, длительность)
- geography: город / география
- contacts: объект с любыми контактами {{"telegram": ..., "phone": ..., "vk": ..., "site": ...}}
- years_experience: сколько лет опыта / обучения

Правила:
1. Не домысливай. Если данных нет — ставь пустую строку или пустой список.
2. Используй язык клиента verbatim там, где это уместно.
3. Цифры и цены бери из текста.
4. Результат — только валидный JSON, без Markdown-форматирования, без пояснений.

РАСШИФРОВКА:
---
{transcript}
---
"""


def _safe_json_parse(content: str) -> dict:
    """Clean common LLM formatting and parse JSON."""
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"\s*```", "", content)
    content = content.strip()
    return json.loads(content)


def _dict_to_dataclass(data: dict) -> InterviewData:
    def service_items(raw):
        out = []
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
            elif isinstance(item, str):
                out.append({"name": item, "price": "", "format": "", "description": ""})
        return out

    def case_items(raw):
        out = []
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
            elif isinstance(item, str):
                out.append({"before": item, "work": "", "after": ""})
        return out

    return InterviewData(
        name=data.get("name", ""),
        role=data.get("role", ""),
        offer=data.get("offer", ""),
        difference=data.get("difference", ""),
        audience=data.get("audience", []),
        services=service_items(data.get("services", [])),
        cases=case_items(data.get("cases", [])),
        channels=data.get("channels", []),
        goals=data.get("goals", []),
        barriers=data.get("barriers", []),
        quotes=data.get("quotes", []),
        price_low=data.get("price_low", ""),
        price_high=data.get("price_high", ""),
        format_notes=data.get("format_notes", ""),
        geography=data.get("geography", ""),
        contacts=data.get("contacts", {}),
        years_experience=data.get("years_experience", ""),
    )


def _detect_provider() -> tuple[str, Optional[str]]:
    """Detect which LLM provider is configured. Returns (provider, model_or_url)."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", "claude-3-5-sonnet-20241022"
    if os.environ.get("PERPLEXITY_API_KEY"):
        return "perplexity", os.environ.get("PERPLEXITY_MODEL", "llama-3-sonar-large-32k-online")
    if os.environ.get("OLLAMA_URL") or os.environ.get("OLLAMA_MODEL"):
        url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "")
        return "ollama", f"{url}|{model}"
    return "none", None


def analyze_with_claude(
    transcript: str,
    name: str,
    api_key: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022",
) -> InterviewData:
    """Use Claude API to extract structured interview data."""
    if anthropic is None:
        raise RuntimeError("anthropic package is not installed")

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0.2,
        messages=[{"role": "user", "content": _build_prompt(transcript, name)}],
    )
    content = response.content[0].text  # type: ignore
    data = _safe_json_parse(content)
    return _dict_to_dataclass(data)


def analyze_with_ollama(
    transcript: str,
    name: str,
    url: str = "http://localhost:11434",
    model: Optional[str] = None,
) -> InterviewData:
    """Use a local Ollama model to extract structured interview data."""
    if requests is None:
        raise RuntimeError("requests package is not installed")

    model = model or os.environ.get("OLLAMA_MODEL")
    if not model:
        raise RuntimeError("OLLAMA_MODEL is not set")

    url = url.rstrip("/")
    payload = {
        "model": model,
        "prompt": _build_prompt(transcript, name),
        "stream": False,
        "options": {"temperature": 0.2},
    }
    response = requests.post(f"{url}/api/generate", json=payload, timeout=300)
    response.raise_for_status()
    result = response.json()
    content = result.get("response", "")
    data = _safe_json_parse(content)
    return _dict_to_dataclass(data)


def analyze_with_perplexity(
    transcript: str,
    name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> InterviewData:
    """Use Perplexity API (OpenAI-compatible) to extract structured interview data."""
    if openai is None:
        raise RuntimeError("openai package is not installed")

    key = api_key or os.environ.get("PERPLEXITY_API_KEY")
    if not key:
        raise RuntimeError("PERPLEXITY_API_KEY is not set")

    model = model or os.environ.get("PERPLEXITY_MODEL", "llama-3-sonar-large-32k-online")
    client = openai.OpenAI(api_key=key, base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[{"role": "user", "content": _build_prompt(transcript, name)}],
    )
    content = response.choices[0].message.content  # type: ignore
    data = _safe_json_parse(content)
    return _dict_to_dataclass(data)


def analyze_with_llm(transcript: str, name: str = "") -> InterviewData:
    """Analyze transcript using whichever LLM provider is configured."""
    provider, value = _detect_provider()

    if provider == "anthropic":
        return analyze_with_claude(transcript, name)
    if provider == "perplexity":
        return analyze_with_perplexity(transcript, name)
    if provider == "ollama":
        url, model = value.split("|", 1) if value and "|" in value else ("http://localhost:11434", "")
        return analyze_with_ollama(transcript, name, url=url, model=model)

    raise RuntimeError("No LLM provider configured. Set ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, or OLLAMA_MODEL.")


def analyze_fallback(transcript: str, name: str) -> InterviewData:
    """Lightweight rule-based fallback when no LLM is available."""
    text = clean_transcript(transcript)
    result = InterviewData(name=name or "Специалист")

    # Try to find prices like 5 000, 5000, 7 000 ₽
    prices = re.findall(r"(\d[\d\s]{2,})(?:\s*₽|руб|р\\.)?", text)
    if prices:
        nums = sorted({int(p.replace(" ", "")) for p in prices})
        result.price_low = f"{nums[0]:,}".replace(",", " ") + " ₽"
        result.price_high = f"{nums[-1]:,}".replace(",", " ") + " ₽"

    # Experience years
    m = re.search(r"(\d{1,2})\s*(?:лет|года?)\s*(?:обучения|опыта|практики)", text, re.I)
    if m:
        result.years_experience = m.group(1)

    # Geography
    cities = re.findall(r"(?:в|из)\s+([А-Я][а-я]+(?:\s[А-Я][а-я]+)?)", text)
    if cities:
        result.geography = cities[0]

    # Contacts
    phones = re.findall(r"\+7\s?[\(]?\d{3}[\)]?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}", text)
    if phones:
        result.contacts["phone"] = phones[0]

    raw_lines = [line.strip() for line in transcript.splitlines() if line.strip()]
    role_keywords = [
        "тренер", "коуч", "консультант", "психолог", "маркетолог", "дизайнер",
        "разработчик", "юрист", "бухгалтер", "врач", "наставник", "эксперт",
        "специалист", "руководитель", "предприниматель", "фотограф", "ведущий",
        "помогаю", "работаю", "занимаюсь", "внедряю", "провожу", "обучаю",
    ]
    for line in raw_lines[:25]:
        if line.endswith("?") or line.startswith("Интервью"):
            continue
        clean = re.sub(r"^(?:[А-ЯA-Z][а-яa-z]+)[:\-]?\s*", "", line).strip()
        lower = clean.lower()
        if any(kw in lower for kw in role_keywords) and 20 < len(clean) < 250:
            result.role = clean
            break
    if not result.role and raw_lines:
        result.role = raw_lines[0][:120]

    # Quotes
    for line in raw_lines[:30]:
        if len(line) > 30 and len(line) < 200 and line[-1] in ".!?":
            result.quotes.append(line)
            if len(result.quotes) >= 5:
                break

    # Structured cases
    case_paragraphs = re.findall(
        r"(?is)(?:^|\n)(?:[А-ЯA-Z][а-яa-z]+[:\-]?\s*)?было[:\-]?\s*(.*?)\n(?:[А-ЯA-Z][а-яa-z]+[:\-]?\s*)?работа[:\-]?\s*(.*?)\n(?:[А-ЯA-Z][а-яa-z]+[:\-]?\s*)?стало[:\-]?\s*(.*?)(?=\n\n|$)",
        text,
    )
    for before, work, after in case_paragraphs[:3]:
        result.cases.append({"before": before.strip(), "work": work.strip(), "after": after.strip()})

    # Services from explicit price lines
    service_candidates = re.findall(
        r"(?m)^[^\n]*?([А-ЯA-Z][^.\n]{2,40}?)\s*[—\-]\s*(\d[\d\s]{2,}(?:\s*₽)?)[^.\n]*$",
        text,
    )
    if service_candidates:
        result.services = []
        for svc, price in service_candidates[:5]:
            result.services.append({
                "name": svc.strip(),
                "price": price.strip() + (" ₽" if "₽" not in price else ""),
                "format": "[уточнить]",
                "description": "[заполнить по интервью]",
            })
    else:
        result.services = [{"name": "[основная услуга]", "price": result.price_low, "format": "[уточнить]", "description": "[заполнить по интервью]"}]

    result.audience = ["[аудитория — уточнить]"]
    result.channels = ["[каналы — уточнить]"]
    result.barriers = ["[барьер — уточнить]"]
    return result


def analyze(transcript: str, name: str = "", use_llm: bool = True) -> InterviewData:
    """Analyze transcript using configured LLM if available, otherwise fall back to rule-based extraction."""
    if use_llm:
        try:
            return analyze_with_llm(transcript, name)
        except Exception as exc:
            print(f"[WARN] LLM analysis failed: {exc}. Falling back to local parser.")
    return analyze_fallback(transcript, name)
