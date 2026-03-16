# SERVER.md

## Назначение

Этот документ описывает **полный разворот проекта на Ubuntu Server** в production-режиме.
Инструкция написана под текущую структуру репозитория и текущий код:

- frontend: React + TypeScript, собирается в статические файлы
- backend: FastAPI + Uvicorn
- БД: PostgreSQL
- Nginx: reverse proxy + раздача frontend
- Telegram-уведомления: через Bot API из backend, отдельный bot-worker для текущего MVP не нужен

Документ ориентирован на **один сервер Ubuntu**. Для первого production этого достаточно.

---

## 1. Что будет в итоге

После выполнения гайда у вас будет:

- Ubuntu-сервер с базовым hardening
- PostgreSQL, доступный только локально
- backend, работающий как `systemd`-сервис на `127.0.0.1:8000`
- frontend, собранный в статику и отдаваемый Nginx
- HTTPS через Let's Encrypt
- Telegram Mini App, открывающийся по домену вида `https://booking.example.com`

Схема трафика:

```text
Telegram Mini App / Browser
          |
          v
       Nginx :443
      /           \
     /             \
static frontend   proxy /api and /health
                       |
                       v
              Uvicorn/FastAPI :8000
                       |
                       v
               PostgreSQL :5432 (localhost only)
```

---

## 2. Что подготовить заранее

До начала у вас должны быть:

1. Ubuntu Server 22.04 LTS или 24.04 LTS.
2. Домен, который указывает на ваш сервер.
   Пример: `booking.example.com`.
3. Telegram-бот и его token.
4. Telegram ID администратора.
5. Доступ по SSH по ключу.
6. Репозиторий проекта на сервере или возможность скопировать его через `git clone`.

Нужные значения, которые пригодятся дальше:

- домен: `booking.example.com`
- backend env file: `/etc/studio/backend.env`
- код проекта: `/opt/studio/app`
- frontend build: `/var/www/studio-mini-app/current`
- systemd unit backend: `/etc/systemd/system/studio-backend.service`

---

## 3. Базовая подготовка Ubuntu

Подключитесь к серверу:

```bash
ssh ubuntu@YOUR_SERVER_IP
```

Обновите систему:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

Установите базовые пакеты:

```bash
sudo apt install -y \
  git curl unzip wget \
  build-essential pkg-config \
  ca-certificates software-properties-common \
  ufw fail2ban \
  nginx \
  certbot python3-certbot-nginx \
  postgresql postgresql-contrib \
  python3 python3-venv python3-pip
```

### 3.1. Установить Node.js LTS

Frontend собирается через Node.js. Берите LTS.
В примере ниже используется Node 22.

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

### 3.2. Базовый hardening SSH

Если вы уже настроили SSH по ключу, хорошо. Проверьте:

```bash
sudo nano /etc/ssh/sshd_config
```

Рекомендуемые значения:

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes
```

После изменений:

```bash
sudo systemctl restart ssh
```

### 3.3. Firewall

Откройте только то, что реально нужно:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Важно:

- **не открывайте `5432` наружу**
- backend тоже не должен слушать внешний интерфейс, только `127.0.0.1`

### 3.4. Fail2ban

Обычно хватает дефолтной установки:

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo systemctl status fail2ban
```

---

## 4. Создать системного пользователя приложения

Создаём отдельного пользователя, от которого будут крутиться процессы приложения:

```bash
sudo adduser --system --group --home /opt/studio studio
```

Создайте рабочие каталоги:

```bash
sudo mkdir -p /opt/studio
sudo mkdir -p /var/www/studio-mini-app/current
sudo mkdir -p /etc/studio
sudo chown -R studio:studio /opt/studio
sudo chown -R studio:studio /var/www/studio-mini-app
```

---

## 5. Безопасная настройка PostgreSQL

Это один из самых важных блоков. Цели:

- отдельная БД под приложение
- отдельный пользователь БД без суперправ
- PostgreSQL не торчит наружу
- пароли через `scram-sha-256`

### 5.1. Проверить версию и статус

```bash
psql --version
sudo systemctl status postgresql
```

### 5.2. Найти конфиги PostgreSQL

```bash
sudo -u postgres psql -c "SHOW config_file;"
sudo -u postgres psql -c "SHOW hba_file;"
```

Обычно пути примерно такие:

- `postgresql.conf`: `/etc/postgresql/16/main/postgresql.conf`
- `pg_hba.conf`: `/etc/postgresql/16/main/pg_hba.conf`

### 5.3. Включить SCRAM и оставить только local/loopback

Откройте `postgresql.conf`:

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Проверьте или выставьте:

```text
listen_addresses = '127.0.0.1'
password_encryption = scram-sha-256
```

Комментарий:

- `listen_addresses = '127.0.0.1'` означает, что PostgreSQL не слушает внешний интерфейс
- этого достаточно для текущего one-server deployment

Теперь откройте `pg_hba.conf`:

```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Нормальный безопасный минимальный вариант:

```text
local   all             postgres                                peer
local   all             all                                     scram-sha-256
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
```

Если хотите жёстче и точнее:

```text
local   all             postgres                                peer
local   studio_prod     studio_app                              scram-sha-256
host    studio_prod     studio_app      127.0.0.1/32            scram-sha-256
host    studio_prod     studio_app      ::1/128                 scram-sha-256
```

После изменений:

```bash
sudo systemctl restart postgresql
sudo systemctl status postgresql
```

### 5.4. Создать роль и базу данных

Зайдите под `postgres`:

```bash
sudo -u postgres psql
```

Выполните:

```sql
CREATE ROLE studio_app
  LOGIN
  PASSWORD 'CHANGE_THIS_TO_A_LONG_RANDOM_PASSWORD'
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  NOINHERIT;

CREATE DATABASE studio_prod
  OWNER studio_app
  ENCODING 'UTF8'
  TEMPLATE template0;

\c studio_prod

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO studio_app;

\q
```

Почему так:

- `studio_app` не суперпользователь
- `studio_app` не может создавать роли и базы
- у приложения есть доступ только к своей БД и своей схеме

### 5.5. Проверить логин приложения

Проверьте, что логин работает:

```bash
psql "postgresql://studio_app:CHANGE_THIS_TO_A_LONG_RANDOM_PASSWORD@127.0.0.1:5432/studio_prod" -c "SELECT 1;"
```

Если команда вернула `1`, базовая настройка готова.

### 5.6. Что нельзя делать

Не делайте в production следующее:

- не используйте пользователя `postgres` в `DATABASE_URL`
- не открывайте `5432` наружу
- не храните пароль БД в world-readable файлах
- не включайте `trust` в `pg_hba.conf`

---

## 6. Получить код проекта на сервер

Перейдите в каталог приложения:

```bash
cd /opt/studio
```

Клонируйте репозиторий:

```bash
sudo -u studio -H git clone YOUR_REPOSITORY_URL /opt/studio/app
```

Проверьте:

```bash
sudo -u studio -H ls -la /opt/studio/app
```

---

## 7. Развернуть backend

### 7.1. Создать virtualenv и установить зависимости

```bash
sudo -u studio -H bash -lc '
cd /opt/studio/app/backend
python3 -m venv /opt/studio/venv
/opt/studio/venv/bin/pip install --upgrade pip
/opt/studio/venv/bin/pip install -e .
'
```

### 7.2. Создать production env для backend

Создайте файл:

```bash
sudo nano /etc/studio/backend.env
```

Пример production-конфига:

```env
APP_NAME=Studio Booking MVP
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://studio_app:CHANGE_THIS_TO_A_LONG_RANDOM_PASSWORD@127.0.0.1:5432/studio_prod
TELEGRAM_BOT_TOKEN=123456:replace_with_real_token
AUTH_SECRET=PUT_A_LONG_RANDOM_SECRET_HERE
SESSION_TTL_MINUTES=720
STUDIO_TIMEZONE=Europe/Moscow
SLOT_STEP_MINUTES=30
ALLOW_DEV_LOGIN=false
ALLOW_SCHEMA_CREATE=false
CORS_ORIGINS=https://booking.example.com
ADMIN_TELEGRAM_IDS=5000,123456789
TELEGRAM_ADMIN_CHAT_IDS=5000,123456789
```

Сгенерировать длинный `AUTH_SECRET` можно так:

```bash
openssl rand -hex 32
```

Права на файл:

```bash
sudo chown root:studio /etc/studio/backend.env
sudo chmod 640 /etc/studio/backend.env
```

### 7.3. Первый bootstrap схемы БД

Важно: в текущем MVP **нет Alembic/migrations**.
Значит для первого разворота таблицы нужно создать один раз вручную.

Есть безопасный вариант:

1. временно запустить инициализацию схемы
2. после создания таблиц оставить `ALLOW_SCHEMA_CREATE=false`

Выполните:

```bash
sudo -u studio -H bash -lc '
set -a
source /etc/studio/backend.env
export ALLOW_SCHEMA_CREATE=true
cd /opt/studio/app/backend
/opt/studio/venv/bin/python -c "import asyncio; from app.db.session import init_db; asyncio.run(init_db())"
'
```

После этого:

- не меняйте `ALLOW_SCHEMA_CREATE=false` в production env
- авто-создание схемы в runtime лучше не держать включённым

### 7.4. systemd unit для backend

Создайте unit:

```bash
sudo nano /etc/systemd/system/studio-backend.service
```

Содержимое:

```ini
[Unit]
Description=Studio Booking FastAPI Backend
After=network.target postgresql.service
Wants=postgresql.service

[Service]
User=studio
Group=studio
WorkingDirectory=/opt/studio/app/backend
EnvironmentFile=/etc/studio/backend.env
ExecStart=/opt/studio/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
TimeoutStopSec=30
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
```

Примените:

```bash
sudo systemctl daemon-reload
sudo systemctl enable studio-backend
sudo systemctl start studio-backend
sudo systemctl status studio-backend
```

Проверка health:

```bash
curl http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

Логи:

```bash
journalctl -u studio-backend -f
```

---

## 8. Развернуть frontend

Важно: frontend env нужен **только на этапе сборки**.
После `npm run build` значения уже вшиты в статику.

### 8.1. Создать production env для frontend

```bash
sudo -u studio -H nano /opt/studio/app/frontend/.env.production
```

Содержимое:

```env
VITE_API_URL=https://booking.example.com/api/v1
VITE_DEV_LOGIN=false
```

### 8.2. Установить зависимости и собрать frontend

```bash
sudo -u studio -H bash -lc '
cd /opt/studio/app/frontend
npm ci
npm run build
'
```

### 8.3. Положить build в web-root

```bash
sudo rsync -av --delete /opt/studio/app/frontend/dist/ /var/www/studio-mini-app/current/
sudo chown -R studio:studio /var/www/studio-mini-app/current
```

---

## 9. Настроить Nginx

### 9.1. Конфиг сайта

Создайте файл:

```bash
sudo nano /etc/nginx/sites-available/studio-mini-app
```

Содержимое:

```nginx
server {
    listen 80;
    server_name booking.example.com;

    root /var/www/studio-mini-app/current;
    index index.html;

    client_max_body_size 10m;

    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    location /assets/ {
        try_files $uri =404;
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri /index.html;
    }
}
```

Включите сайт:

```bash
sudo ln -s /etc/nginx/sites-available/studio-mini-app /etc/nginx/sites-enabled/studio-mini-app
sudo nginx -t
sudo systemctl reload nginx
```

Проверьте:

```bash
curl http://booking.example.com/health
```

---

## 10. Включить HTTPS

Получите сертификат:

```bash
sudo certbot --nginx -d booking.example.com
```

Проверьте автопродление:

```bash
systemctl list-timers | grep certbot
sudo certbot renew --dry-run
```

После этого сайт и Mini App должны открываться по:

```text
https://booking.example.com
```

Это обязательно, потому что Telegram Mini Apps требуют HTTPS.

---

## 11. Настроить Telegram Mini App

### 11.1. Bot token

В `/etc/studio/backend.env` должен быть **реальный** `TELEGRAM_BOT_TOKEN`.

### 11.2. Mini App URL

В настройках вашего Telegram-бота задайте Web App URL:

```text
https://booking.example.com
```

### 11.3. Админы

Список админов определяется по:

```env
ADMIN_TELEGRAM_IDS=5000,123456789
```

Важно:

- пользователь становится админом после авторизации через приложение
- если поменяли `ADMIN_TELEGRAM_IDS`, перезапустите backend

### 11.4. Уведомления

Backend отправляет уведомления в:

```env
TELEGRAM_ADMIN_CHAT_IDS=5000,123456789
```

Для личных уведомлений пользователю backend использует его `telegram_id`.

---

## 12. Первая проверка после запуска

Проверьте последовательно:

### 12.1. Backend

```bash
curl https://booking.example.com/health
```

### 12.2. Frontend

Откройте:

```text
https://booking.example.com
```

### 12.3. Авторизация

Откройте Mini App из Telegram и убедитесь, что `POST /api/v1/auth/session` проходит успешно.

### 12.4. Админка

Зайдите в приложение своим Telegram-аккаунтом из `ADMIN_TELEGRAM_IDS`.

Проверьте, что можете:

- создать услугу
- создать рабочее правило
- создать блокировку
- изменить статус записи

### 12.5. Пользовательский flow

Проверьте:

1. выбрать услугу
2. выбрать дату
3. выбрать свободный слот
4. создать запись
5. увидеть запись в `Мои записи`
6. отменить запись

---

## 13. Безопасный update в будущем

Обновление кода делайте так:

```bash
sudo -u studio -H bash -lc '
cd /opt/studio/app
git pull
cd /opt/studio/app/backend
/opt/studio/venv/bin/pip install -e .
cd /opt/studio/app/frontend
npm ci
npm run build
'

sudo rsync -av --delete /opt/studio/app/frontend/dist/ /var/www/studio-mini-app/current/
sudo systemctl restart studio-backend
sudo systemctl reload nginx
```

После обновления обязательно:

```bash
curl https://booking.example.com/health
journalctl -u studio-backend -n 100 --no-pager
```

---

## 14. Резервные копии PostgreSQL

Минимум, который нужно сделать сразу: nightly dump.

Создайте каталог:

```bash
sudo mkdir -p /var/backups/studio-postgres
sudo chown postgres:postgres /var/backups/studio-postgres
```

Создайте скрипт:

```bash
sudo nano /usr/local/bin/studio_pg_backup.sh
```

Содержимое:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/var/backups/studio-postgres"
STAMP="$(date +%F_%H-%M-%S)"

sudo -u postgres pg_dump -Fc studio_prod > "${BACKUP_DIR}/studio_prod_${STAMP}.dump"
find "${BACKUP_DIR}" -type f -name "*.dump" -mtime +14 -delete
```

Сделайте исполняемым:

```bash
sudo chmod +x /usr/local/bin/studio_pg_backup.sh
```

Добавьте в cron:

```bash
sudo crontab -e
```

Например:

```cron
30 2 * * * /usr/local/bin/studio_pg_backup.sh
```

Периодически проверяйте, что backup реально восстанавливается.

Проверка списка backup-файлов:

```bash
ls -lh /var/backups/studio-postgres
```

---

## 15. Полезные команды эксплуатации

### Backend

```bash
sudo systemctl restart studio-backend
sudo systemctl status studio-backend
journalctl -u studio-backend -f
```

### Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status nginx
```

### PostgreSQL

```bash
sudo systemctl status postgresql
sudo -u postgres psql
```

### Firewall

```bash
sudo ufw status numbered
```

---

## 16. Troubleshooting

### 16.1. `502 Bad Gateway`

Причина обычно одна из двух:

- backend не поднялся
- Nginx проксирует не туда

Проверка:

```bash
sudo systemctl status studio-backend
curl http://127.0.0.1:8000/health
sudo nginx -t
```

### 16.2. Telegram auth не проходит

Проверьте:

- `TELEGRAM_BOT_TOKEN` в `/etc/studio/backend.env`
- что Mini App открывается именно через того же бота
- что backend после изменения токена был перезапущен

### 16.3. Уведомления не приходят

Проверьте:

- правильный `TELEGRAM_BOT_TOKEN`
- правильные `TELEGRAM_ADMIN_CHAT_IDS`
- что пользователь хотя бы раз открыл бота/приложение и доступен для сообщений
- логи backend:

```bash
journalctl -u studio-backend -f
```

### 16.4. Не подключается PostgreSQL

Проверьте:

```bash
sudo systemctl status postgresql
psql "postgresql://studio_app:YOUR_PASSWORD@127.0.0.1:5432/studio_prod" -c "SELECT 1;"
```

Если не работает:

- смотрите `pg_hba.conf`
- смотрите `listen_addresses`
- проверьте пароль пользователя `studio_app`

### 16.5. CORS ошибки

Если frontend и backend живут на одном домене, ставьте:

```env
CORS_ORIGINS=https://booking.example.com
```

После изменения env:

```bash
sudo systemctl restart studio-backend
```

---

## 17. Production checklist

Перед запуском обязательно проверьте:

- `DEBUG=false`
- `ALLOW_DEV_LOGIN=false`
- `ALLOW_SCHEMA_CREATE=false`
- `AUTH_SECRET` длинный и случайный
- `DATABASE_URL` использует **не** `postgres`, а `studio_app`
- `5432` не открыт наружу
- backend слушает только `127.0.0.1:8000`
- сайт работает по HTTPS
- certbot renewal проверен
- backup PostgreSQL настроен
- env-файлы не лежат в репозитории
- права на `/etc/studio/backend.env` ограничены

---

## 18. Что стоит улучшить следующим шагом

Для первого production этого гайда достаточно, но следующим этапом желательно добавить:

1. Alembic/migrations вместо `ALLOW_SCHEMA_CREATE`
2. CI/CD pipeline
3. отдельный staging server
4. мониторинг и алерты
5. ротацию логов
6. внешнее хранилище backup
7. systemd health/restart policy с более жёсткими лимитами

---

## 19. Краткий план разворота в правильном порядке

Если нужен очень короткий порядок действий:

1. Подготовить Ubuntu, SSH, firewall.
2. Установить Python, Node, Nginx, PostgreSQL.
3. Настроить PostgreSQL локально и безопасно.
4. Создать пользователя `studio` и каталоги.
5. Склонировать проект в `/opt/studio/app`.
6. Установить backend зависимости и создать `/etc/studio/backend.env`.
7. Один раз создать schema bootstrap.
8. Поднять backend через `systemd`.
9. Собрать frontend и положить статику в `/var/www/studio-mini-app/current`.
10. Настроить Nginx.
11. Выпустить TLS через certbot.
12. Прописать Mini App URL в Telegram.
13. Проверить auth, booking flow и admin flow.

