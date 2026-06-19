"""Analyze a raw interview transcript and extract structured blocks."""

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
    # Remove "Speaker 1:" labels
    text = re.sub(r"(?i)(speaker\s*\d+|я|анна|саша)\s*[:\-]", "", text)
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
        messages=[
            {"role": "user", "content": _build_prompt(transcript, name)},
        ],
    )

    content = response.content[0].text  # type: ignore
    # Sometimes Claude wraps JSON in markdown fences
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"\s*```", "", content)
    data = json.loads(content)
    return _dict_to_dataclass(data)


def analyze_fallback(transcript: str, name: str) -> InterviewData:
    """Lightweight rule-based fallback when API is unavailable."""
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

    # Extract likely role from first sentence
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        result.role = lines[0][:80]

    # Quotes: lines that sound like statements
    for line in lines[:30]:
        if len(line) > 30 and len(line) < 200 and line[-1] in ".!?":
            result.quotes.append(line)
            if len(result.quotes) >= 5:
                break

    result.audience = ["[требует уточнения — данные из интервью]"]
    result.services = [{"name": "[основная услуга]", "price": result.price_low, "format": "[уточнить]", "description": "[заполнить по интервью]"}]
    result.barriers = ["[требует уточнения — возможно, барьер 'продвижение = продажа себя']"]
    return result


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


def analyze(transcript: str, name: str = "", use_api: bool = True) -> InterviewData:
    """Analyze transcript using Claude API if available, otherwise fall back to rule-based extraction."""
    try:
        if use_api and anthropic is not None and os.environ.get("ANTHROPIC_API_KEY"):
            return analyze_with_claude(transcript, name)
    except Exception as exc:
        print(f"[WARN] Claude API analysis failed: {exc}. Falling back to local parser.")
    return analyze_fallback(transcript, name)
