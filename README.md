# interview-to-strategy

Универсальный CLI-инструмент для продюсеров, маркетологов и специалистов: превращает сырую текстовую расшифровку стратегического интервью в структурированный Markdown-документ с позиционированием, услугами, кейсами и планом продвижения.

Подходит для любой ниши: психологи, коучи, тренеры, юристы, дизайнеры, разработчики, фотографы, наставники — кто угодно.

## Что делает

1. Читает `.txt` файл с расшифровкой интервью.
2. Извлекает ключевые блоки: кто специалист, что продаёт, кому, за сколько, какие кейсы, какие каналы, какие барьеры.
3. Генерирует готовый `.md` файл по шаблону финального документа для клиента.

## LLM-провайдеры

Инструмент может работать с несколькими источниками анализа:

| Провайдер | Требуется | Плюсы |
| --- | --- | --- |
| **Ollama** | Установленная модель | Бесплатно, локально, приватно |
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | Высокое качество извлечения |
| **Perplexity** | `PERPLEXITY_API_KEY` | OpenAI-совместимый API |
| **Rule-based fallback** | Ничего | Работает без интернета, но результат слабее |

## Быстрый старт (Ollama)

```bash
# 1. Склонировать репозиторий
git clone https://github.com/sskosmos88/interview-to-strategy.git
cd interview-to-strategy

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Указать Ollama-модель (пример для Windows PowerShell)
$env:OLLAMA_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "llama3:latest"

# 4. Запустить на примере
python main.py --input data/sample-transcript.txt --name "Иван Петров" --output output/strategy.md
```

Результат появится в `output/strategy.md`.

## Настройка провайдеров

Скопируй `.env.example` в `.env` и заполни нужный раздел:

```bash
cp .env.example .env
```

### Ollama

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest
```

[Установить Ollama](https://ollama.com/) и скачать модель:

```bash
ollama pull llama3
```

### Anthropic Claude

```env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Perplexity

```env
PERPLEXITY_API_KEY=pplx-your-key-here
PERPLEXITY_MODEL=llama-3-sonar-large-32k-online
```

## Аргументы CLI

| Аргумент | Описание |
| --- | --- |
| `--input`, `-i` | Путь к файлу с расшифровкой интервью |
| `--name`, `-n` | Имя специалиста (fallback, если не определилось автоматически) |
| `--output`, `-o` | Путь для сохранения итогового `.md` |
| `--fallback` | Использовать локальный rule-based анализ без LLM |
| `--producer-name` | Имя продюсера / автора документа |
| `--producer-phone` | Телефон продюсера |
| `--producer-telegram` | Telegram продюсера |
| `--producer-site` | Сайт продюсера |
| `--producer-vk` | VK продюсера |
| `--producer-email` | Email продюсера |

## Пример

```bash
python main.py \
  --input data/ivanova-interview.txt \
  --name "Мария Иванова" \
  --output output/ivanova-strategy.md \
  --producer-name "Алёна Орлова" \
  --producer-telegram "@alena_prod"
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
│   ├── analyzer.py          # Извлечение данных из текста (multi-provider)
│   └── formatter.py         # Генерация Markdown-документа
├── main.py                  # CLI-точка входа
├── requirements.txt
├── .env.example
└── README.md
```

## Скриншоты

### Терминал: запуск с Ollama
![terminal](docs/screenshots/terminal-run.png)

### Результат: стратегический документ
![output](docs/screenshots/output-preview.png)


## Требования

- Python 3.10+
- Один из провайдеров или флаг `--fallback`
- Для Ollama: запущенный `ollama serve` и скачанная модель

## Лицензия

MIT — используйте свободно для своих проектов.
