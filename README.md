# MebelExpress — MVP платформа заказа мебели

Лёгкий MVP: мгновенный расчёт цены, заявка в Telegram, AI-распознавание эскиза, публичный трекинг заказа.

## Стек

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy Async, SQLite
- **Frontend:** HTML5, Tailwind CDN, Vanilla JS
- **Интеграции:** Telegram Bot API, OpenAI Vision (опционально)
- **Deploy:** Docker Compose + Nginx

## Быстрый старт (локально)

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # или cp .env.example .env

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Swagger: http://localhost:8000/docs  
- Health: http://localhost:8000/health  
- Демо-заказ: `GET /api/v1/tracking/TEST1234`

### 2. Frontend

В другом терминале:

```bash
cd frontend
python -m http.server 5500
```

Откройте http://localhost:5500 — JS по умолчанию ходит на `http://localhost:8000/api/v1`.

## Docker

В корне `06-furniture-platform/`:

```bash
# опционально: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OPENAI_API_KEY
docker compose up --build
```

Сайт: http://localhost:8080  
API (через Nginx): http://localhost:8080/api/v1/…  
Docs: http://localhost:8080/docs

## Переменные окружения

| Переменная | Описание |
|---|---|
| `DATABASE_URL` | По умолчанию `sqlite+aiosqlite:///./furniture.db` |
| `TELEGRAM_BOT_TOKEN` | Токен бота (без него заявка всё равно сохраняется) |
| `TELEGRAM_CHAT_ID` | Chat ID для уведомлений |
| `OPENAI_API_KEY` | GPT-4o Vision; без ключа — эвристический fallback |
| `CORS_ORIGINS` | `*` или список через запятую |

## API

| Метод | Путь | Назначение |
|---|---|---|
| `POST` | `/api/v1/calculator/calculate` | Вилка цен + разбивка |
| `POST` | `/api/v1/leads/create` | Заявка + Telegram |
| `POST` | `/api/v1/vision/estimate-sketch` | Распознать эскиз (multipart) |
| `GET` | `/api/v1/tracking/{order_number}` | Статус заказа |

Телефон заявки: `+77XXXXXXXXX` или `87XXXXXXXXX`.

## Формула цены

```
Cost = (Width × Height × Depth × MaterialFactor) + HardwareCost + AssemblyCost (+ extras)
Price_min = Cost × 0.95
Price_max = Cost × 1.15
```

Размеры в мм. Валюта: KZT.

## Миграции (Alembic)

При старте API таблицы также создаются через `create_all` + нормализация enum.
Для явных миграций:

```bash
cd backend
alembic upgrade head
```

## Структура

См. каталог `06-furniture-platform/` — backend (`app/`), frontend, `nginx/`, `docker-compose.yml`.
