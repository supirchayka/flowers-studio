# API Spec

## Auth

- `POST /api/v1/auth/session` — логин через `initData`
- `POST /api/v1/auth/dev-session` — dev-only логин
- `GET /api/v1/auth/me` — текущий пользователь

## Public

- `GET /api/v1/services`
- `GET /api/v1/services/{service_id}`
- `GET /api/v1/services/{service_id}/availability?day=YYYY-MM-DD`

## User bookings

- `POST /api/v1/bookings`
- `GET /api/v1/bookings/me`
- `POST /api/v1/bookings/{booking_id}/cancel`

## Admin

- `GET/POST/PATCH/DELETE /api/v1/admin/services`
- `GET/POST/PATCH/DELETE /api/v1/admin/schedule/rules`
- `GET/POST/PATCH/DELETE /api/v1/admin/schedule/blocked-intervals`
- `GET /api/v1/admin/bookings`
- `PATCH /api/v1/admin/bookings/{booking_id}/status`
- `GET /api/v1/admin/bookings/dashboard`

