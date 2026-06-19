"""Render extracted interview data into the final strategy Markdown document."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from .analyzer import InterviewData


def _esc(text: str) -> str:
    return str(text).strip()


def _as_list(items: list[str]) -> str:
    if not items:
        return "- _нет данных_"
    return "\n".join(f"- {_esc(item)}" for item in items)


def _as_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header_line = "| " + " | ".join(headers) + " |"
    separator = "|" + "|".join([" --- " for _ in headers]) + "|"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join([header_line, separator, body])


def _service_rows(services: list[dict]) -> list[list[str]]:
    rows = []
    for s in services:
        name = _esc(s.get("name", ""))
        price = _esc(s.get("price", ""))
        fmt = _esc(s.get("format", ""))
        desc = _esc(s.get("description", ""))
        rows.append([name, price, fmt, desc])
    if not rows:
        rows.append(["[основная услуга]", "[цена]", "[формат]", "[описание]"])
    return rows


def _case_rows(cases: list[dict]) -> list[list[str]]:
    rows = []
    for i, c in enumerate(cases, 1):
        before = _esc(c.get("before", ""))
        work = _esc(c.get("work", ""))
        after = _esc(c.get("after", ""))
        rows.append([f"Кейс {i}", before, work, after])
    return rows


def _first_quote(quotes: list[str]) -> str:
    for q in quotes:
        cleaned = re.sub(r"^[\s\-•]+", "", q).strip()
        if 20 < len(cleaned) < 200:
            return cleaned
    return ""


def _signature_block(producer: Optional[dict]) -> str:
    if not producer:
        return ""
    lines = []
    if producer.get("name"):
        lines.append(f"**Подготовил:** {producer['name']}")
    for key in ["phone", "telegram", "site", "vk", "email"]:
        if producer.get(key):
            label = {"phone": "Телефон", "telegram": "Telegram", "site": "Сайт", "vk": "VK", "email": "Email"}[key]
            lines.append(f"**{label}:** {producer[key]}")
    return "\n".join(lines)


def render(data: InterviewData, producer: Optional[dict] = None) -> str:
    today = datetime.now().strftime("%d.%m.%Y")
    name = data.name or "[Имя специалиста]"
    role = data.role or "[роль специалиста]"

    offer = data.offer or "[УТП — сформулировать после уточнения]"
    difference = data.difference or "[отличие — уточнить]"
    audience = data.audience or ["[аудитория — уточнить]"]

    first_steps = []
    if data.cases:
        first_steps.append("Собрать и опубликовать 3–5 кейсов из интервью.")
    if data.channels:
        first_steps.append("Оформить или обновить профили на ключевых площадках.")
    if data.barriers:
        first_steps.append("Проработать главный барьер: " + data.barriers[0].lower())
    if not first_steps:
        first_steps.append("Согласовать позиционирование и УТП.")
        first_steps.append("Собрать первые отзывы и кейсы.")
        first_steps.append("Заполнить один канал продвижения.")

    # Asset table rows
    asset_rows = []
    if data.years_experience:
        asset_rows.append([f"{data.years_experience} лет опыта", "Экспертность и доверие", "Позиционирование через опыт"])
    if data.role:
        asset_rows.append([data.role, "Понятная роль на рынке", "Заголовки профилей"])
    if difference and difference.startswith("[") is False:
        asset_rows.append(["Отличие", difference, "УТП и ключевые сообщения"])
    if data.cases:
        asset_rows.append([f"{len(data.cases)} кейса", "Социальное доказательство", "Тексты для площадок и постов"])
    if not asset_rows:
        asset_rows.append(["[актив 1]", "[что даёт]", "[как использовать]"])

    # Gap table rows
    gap_rows = []
    if not data.cases:
        gap_rows.append(["Нет собранных кейсов", "Высокий", "Переписать 3–5 историй в формате «было — работа — стало»"])
    if not data.channels:
        gap_rows.append(["Нет оформленных каналов продвижения", "Высокий", "Заполнить 1–2 площадки или профиля"])
    if data.barriers:
        gap_rows.append([data.barriers[0], "Критический", "Перефрейм: не «продавать себя», а «рассказывать о помощи»"])
    if not gap_rows:
        gap_rows.append(["[пробел]", "[приоритет]", "[действие]"])

    # Audience bullets
    audience_bullets = "\n".join(f"- {a}" for a in audience)

    services_table = _as_table(["Услуга", "Цена", "Формат", "Описание"], _service_rows(data.services))
    case_table = _as_table(["Кейс", "Было", "Работа", "Стало"], _case_rows(data.cases))

    content_plan = """| Неделя | Тема | Формат | Цель |
| --- | --- | --- | --- |
| 1 | «Как понять, что [проблема клиента] — это не только про [поверхность]» | Пост | Привлечение ЦА |
| 2 | Кейс: [реальный случай из интервью] | Пост / карусель | Социальное доказательство |
| 3 | «Чем мой подход отличается от [типичного способа]» | Пост | Объяснение метода |
| 4 | Вопросы аудитории: ответ на частый вопрос | Пост / stories | Вовлечение |"""

    metrics_table = """| Метрика | Цель на 1 месяц | Цель на квартал | Как мерить |
| --- | --- | --- | --- |
| Заполненные площадки / профили | 1–2 | 4 | Проверка профилей |
| Посты / публикации | 4 | 12 | Публикации |
| Новые отзывы / кейсы | 2–3 | 10+ | Публикации на площадках |
| Новые обращения | 2–3 | 30+ | Сообщения, звонки, заявки |
| Конверсия в покупку | 30% | 50% | Продажи / обращения |"""

    signature = _signature_block(producer)

    doc = f"""# Результат стратегического интервью: {name}

**Дата:** {today}
**Составлено по итогам:** стратегического интервью
**Статус:** готовый рабочий материал

---

## Как пользоваться этим документом

Этот файл — результат интервьюирования и база для дальнейших действий. Всё, что здесь написано, можно использовать как черновики для профилей, площадок, постов и разговоров с клиентами.

- [Разделы 3.1–3.4](#основа-для-оформления-площадок-и-контента) — тексты, готовые к копированию.
- [Раздел 1](#документ-с-аналитикой-ваших-активов) — аналитика активов и пробелов.
- [Раздел 2](#понимание-как-вас-правильно-показывать-рынку) — позиционирование и аудитория.
- [Раздел 4](#база-для-дальнейшего-продвижения) — пошаговый план. Начинайте с подраздела [4.2 «Первые 3 шага»](#первые-3-шага--начните-отсюда).

Где стоит пометка **[требует проверки]** — прочитайте и подтвердите, что формулировка отражает вашу реальность. Где **[готово к публикации]** — текст можно использовать почти без правок.

---

## Ваша сводка за 2 минуты

**Главный оффер (УТП):** {offer}

**В чём отличие:** {difference}

**Главный барьер:** {data.barriers[0] if data.barriers else "[барьер — уточнить]"}

**Три первых действия:**
1. {first_steps[0]}
2. {first_steps[1] if len(first_steps) > 1 else "Согласовать позиционирование и тексты для каналов."}
3. {first_steps[2] if len(first_steps) > 2 else "Заполнить один канал продвижения и начать собирать отзывы."}

---

## 1. Документ с аналитикой ваших активов {{#документ-с-аналитикой-ваших-активов}}

**[этот раздел для понимания, не для публикации]**

### 1.1. Кто вы сейчас

{_as_table(["Актив", "Что это даёт", "Как использовать"], asset_rows)}

### 1.2. Ваши сильные стороны как специалиста

{_as_list(data.audience[:5] if data.audience else ["[сильные стороны — уточнить]"])}

### 1.3. Ваши текущие активы в интернете

{_as_list(data.channels if data.channels else ["[каналы — уточнить]"])}

### 1.4. Что пока не актив, а задача

{_as_table(["Пробел", "Приоритет", "Что делать"], gap_rows)}

---

## 2. Понимание, как вас правильно показывать рынку {{#понимание-как-вас-правильно-показывать-рынку}}

**[этот раздел для понимания, не для публикации]**

### 2.1. Позиционирование

**Главный оффер (УТП):**

> {offer}

**Расшифровка:**

> {name} — {role}. {difference}

**Типичный сценарий входа:**

> {audience[0] if audience else "[сценарий — уточнить]"}

### 2.2. Кого вы ловите

**Основная аудитория — предварительная, требует уточнения.**

{audience_bullets}

### 2.3. Чем вы отличаетесь от других

**Отличие в трёх словах:**

> [требует проверки]

### 2.4. Голос и тон

- [требует проверки]

### 2.5. Как правильно себя показывать (что работает)

**Работает:**
- Тихое присутствие через отзывы и рекомендации.
- Честные короткие посты с одной мыслью.
- Кейсы в формате «было — работа — стало».
- Акцент на главном отличии.

**Не работает:**
- Агрессивные продажи и марафоны.
- Позиционирование «я лучше других».
- Долгие абстрактные посты.

---

## 3. Основа для оформления площадок и контента {{#основа-для-оформления-площадок-и-контента}}

**[здесь собраны тексты для копирования]**

### 3.1. Био для профилей

**[готово к публикации — проверьте личные данные и форматы площадок]**

**Вариант 1. Короткий (для карточек площадок)**

> {name} — {role}. {offer}

**Вариант 2. Средний (для сайта / Telegram)**

> {name} — {role}. {difference} {offer}

### 3.2. Тексты для карточек услуг

{services_table}

### 3.3. Готовые кейсы для площадок и сайта

**[требует проверки — уточните у клиентов, можно ли публиковать, и скорректируйте детали]**

{case_table if data.cases else "_Кейсы не найдены в транскрипции — нужно добавить вручную._"}

### 3.4. Контент-план на первый месяц

{content_plan}

### 3.5. Скрипт первой беседы

**Шаг 1. Приветствие**

> Здравствуйте. Меня зовут {name}. Расскажите, что привело к нам?

**Шаг 2. Сбор запроса**

> Что сейчас беспокоит больше всего? Что вы уже пробовали?

**Шаг 3. Мини-консультация**

> Я слушаю, что вы говорите, и сразу вижу, где основной запрос. Потом мы идём туда, где он начался.

**Шаг 4. Мягкое предложение**

> Когда вам удобно? Онлайн или офлайн?

---

## 4. База для дальнейшего продвижения {{#база-для-дальнейшего-продвижения}}

### 4.1. Понимание вашего барьера

{data.barriers[0] if data.barriers else "[барьер — уточнить]"}

**Что помогает:**

- Не позиционировать продвижение как «продажу себя», а как «рассказ о помощи, которую я умею давать».
- Публиковать не «чтобы продать», а «чтобы те, кто ищет, нашли».

### 4.2. Первые 3 шага — начните отсюда {{#первые-3-шага--начните-отсюда}}

1. {first_steps[0]}
2. {first_steps[1] if len(first_steps) > 1 else "Согласовать позиционирование."}
3. {first_steps[2] if len(first_steps) > 2 else "Заполнить один канал продвижения."}

### 4.3. Ключевые метрики

{metrics_table}

### 4.4. Резюме

{name} — {role}. {offer} Главная задача — не агрессивно «продать», а спокойно показать: вот помощь, вот результат, вот как со мной связаться.

---

{signature}
"""
    return doc


def write_output(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
