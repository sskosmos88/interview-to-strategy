# interview-to-strategy

CLI-инструмент для продюсеров и маркетологов: превращает сырую текстовую расшифровку стратегического интервью со специалистом в структурированный Markdown-документ с позиционированием, услугами, кейсами и планом продвижения.

## Что делает

1. Читает `.txt` файл с расшифровкой интервью.
2. Извлекает ключевые блоки: кто специалист, что продаёт, кому, за сколько, какие кейсы, какие каналы, какие барьеры.
3. Генерирует готовый `.md` файл по шаблону финального документа для клиента.

## Быстрый старт

```bash
# 1. Склонировать репозиторий
git clone https://github.com/sskosmos88/interview-to-strategy.git
cd interview-to-strategy

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить на примере (локальный анализ без API)
python main.py --input data/sample-transcript.txt --name "Анна Ковалёва" --output output/strategy.md --no-api
```

Результат появится в `output/strategy.md`.

## Использование с Claude API

Для полноценного анализа нужен ключ Anthropic:

1. Скопируй `.env.example` в `.env`:
   ```bash
   cp .env.example .env
   ```
2. Пропиши свой `ANTHROPIC_API_KEY`.
3. Запусти без флага `--no-api`:
   ```bash
   python main.py --input data/sample-transcript.txt --name "Анна Ковалёва" --output output/strategy.md
   ```

## Аргументы CLI

| Аргумент | Описание |
| --- | --- |
| `--input`, `-i` | Путь к файлу с расшифровкой интервью |
| `--name`, `-n` | Имя специалиста (fallback, если не определилось автоматически) |
| `--output`, `-o` | Путь для сохранения итогового `.md` |
| `--no-api` | Использовать локальный rule-based анализ вместо Claude API |
| `--producer` | Имя продюсера для подписи в документе |

## Пример

```bash
python main.py \
  --input data/ivanova-interview.txt \
  --name "Мария Иванова" \
  --output output/ivanova-strategy.md \
  --producer "Саша Космос"
```

## Структура выходного документа

- Сводка за 2 минуты
- Аналитика активов и пробелов
- Позиционирование и аудитория
- Готовые тексты для площадок и контента
- План первых шагов и метрики
- Подпись продюсера

## Структура проекта

```
interview-to-strategy/
├── .claude/skills/          # Claude skill с описанием инструмента
├── data/                    # Примеры входных транскрипций
├── src/
│   ├── analyzer.py          # Извлечение данных из текста
│   └── formatter.py         # Генерация Markdown-документа
├── main.py                  # CLI-точка входа
├── requirements.txt
├── .env.example
└── README.md
```

## Скриншоты

### Терминал: запуск генератора
![terminal](docs/screenshots/terminal-run.png)

### Результат: стратегический документ
![output](docs/screenshots/output-preview.png)

> Скриншоты будут добавлены после локального тестирования. Пример результата уже доступен в `output/strategy.md`.

## Требования

- Python 3.10+
- `anthropic` (для API-режима)
- `python-dotenv`

## Лицензия

MIT — используйте свободно для своих проектов.
