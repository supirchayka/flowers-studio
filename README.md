# Studio Booking Mini App MVP

MVP Telegram Mini App для записи в студию звукозаписи. Репозиторий собран по файловой структуре из `START.md`, пункт `42. Приложение B`.

## Что внутри

- `frontend/` — React + TypeScript Mini App с Telegram theming, Back Button и Main Button
- `backend/` — FastAPI API с серверной валидацией `initData`, расчётом слотов и транзакционным бронированием
- `docs/` — выжимка по продукту, API и UX-текстам
- `tests/` — unit/integration/e2e-каталоги для критических сценариев

## Быстрый старт

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .[test]
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

## Ключевые решения

- Telegram auth валидируется на backend через проверку `initData hash`
- итоговая проверка доступности и создание брони выполняются на backend в транзакции
- для PostgreSQL предусмотрен `pg_advisory_xact_lock` на день бронирования, чтобы снизить риск гонок
- доступные слоты считаются из рабочих часов, блокировок, активных записей и длительности услуги
- удаление услуг в MVP заменено архивированием
- новые записи получают статус `new`

## Переменные окружения

- backend: см. [backend/.env.example](/d:/prj/studio/backend/.env.example)
- frontend: см. [frontend/.env.example](/d:/prj/studio/frontend/.env.example)

## Тесты

```powershell
python -m pytest
```

