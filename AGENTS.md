# AGENTS.md

## Архитектура

- Соблюдаем структуру из `START.md`, пункт `42. Приложение B`
- Домен бронирования живёт в `backend/app/modules/bookings`
- Telegram Mini App интеграции фронтенда живут в `frontend/src/shared/hooks` и `frontend/src/shared/lib`

## Backend

- Не выносить критическую проверку доступности слота на frontend
- Любая логика антидублей должна оставаться внутри backend-транзакции
- Для новых функций стараться держать маршруты тонкими, а бизнес-логику в `service.py`

## Frontend

- Telegram theme params должны прокидывать цвета в CSS variables
- На каждом экране держать одно главное действие
- Для destructive действий использовать confirm flow

## Тесты

- Минимум: slot generation, auth validation, booking create/cancel, admin status change

