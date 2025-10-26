---

# ТЗ / «Мониторинг релизов, предзаказов и скидок настольных игр» (RU, однопользовательский)

## 0) Контекст и цели

* **Задача:** локальное однопользовательское приложение на русском, которое по расписанию мониторит источники (магазины, публикации, каталоги), извлекает события (*announce / preorder / release / discount / price*), нормализует данные по играм, хранит историю цен, и шлёт уведомления (Web-Push; Telegram опционально).
* **Ограничения:** до **100 источников**, до **1000 страниц/сутки**, хранение данных **2 года**. Разрешён разумный скрейпинг, приоритет официальным API и уважение robots.txt.
* **Деплой:** локально через **Docker Compose** + автоматический скрипт PowerShell Deploy OneClick для выкачивания репозитория и запуска проекта в Docker.
* **LLM:** через отдельный **Ollama** сервер host.docker.internal:11434, на том же хосте, список моделей: http://host.docker.internal:11434/api/tags (адрес задаётся в конфиге и через UI).
* **Документация** На русском языке, основной функционал и быстрый старт

---

# 1) Архитектура и сервисы (Docker)

## 1.1 Сервисы

* `api` — **FastAPI** (Python 3.11+), бизнес-логика и REST API.
* `worker` — **Celery** воркер.
* `beat` — планировщик задач (Celery beat).
* `postgres` — PostgreSQL 15 + **TimescaleDB** (расширение) для истории цен.
* `redis` — брокер для Celery + кэш/квоты.
* `minio` — S3-совместимое хранилище сырья (HTML/JSON/скриншоты).
* `frontend` — **React** (RU UI), сборка либо dev-сервер.
* `nginx` — reverse proxy (фронт + api).
* `backup` (job/cron) — ежедневный автодамп ZIP.
* (вне compose) `ollama` — отдельный сервис (адрес задаётся в UI или `OLLAMA_URL`).

## 1.2 Переменные окружения (`.env` пример)

```
TZ=Europe/Moscow
DATABASE_URL=postgresql+psycopg2://app:app@postgres:5432/app
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=raw
S3_SECURE=false
OLLAMA_URL=http://host.docker.internal:11434
```

## 1.3 Compose-скелет (сокращённо)

```yaml
services:
  api:
    build: ./backend
    env_file: .env
    depends_on: [postgres, redis, minio]
  worker:
    build: ./backend
    command: celery -A app.celery_app worker -l INFO
    env_file: .env
    depends_on: [api, redis, postgres]
  beat:
    build: ./backend
    command: celery -A app.celery_app beat -l INFO
    env_file: .env
    depends_on: [worker]
  frontend:
    build: ./frontend
    env_file: .env
    depends_on: [api]
  nginx:
    image: nginx:stable
    volumes: [./deploy/nginx.conf:/etc/nginx/nginx.conf:ro]
    ports: ["80:80"]
    depends_on: [frontend, api]
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment: [POSTGRES_USER=app, POSTGRES_PASSWORD=app, POSTGRES_DB=app]
    volumes: [pgdata:/var/lib/postgresql/data]
  redis:
    image: redis:7
  minio:
    image: minio/minio
    command: server /data
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports: ["9000:9000"]
    volumes: [minio:/data]
  backup:
    build: ./backend
    command: python -m app.jobs.backup_daily
    env_file: .env
    depends_on: [postgres, minio]
volumes: { pgdata: {}, minio: {} }
```

---

# 2) Модель данных (PostgreSQL + Timescale)

## 2.1 Таблицы (DDL, упрощённо)

```sql
create table game (
  id uuid primary key,
  title text not null,
  synonyms text[] default '{}',
  bgg_id text,
  publisher text,
  tags text[] default '{}',
  created_at timestamptz default now()
);

create table store (
  id text primary key,
  name text not null,
  site_url text,
  region text default 'RU',
  currency text default 'RUB'
);

create table source_agent (
  id text primary key,
  name text not null,
  type text not null check (type in ('api','html','headless','telegram_public')),
  schedule jsonb not null,
  rate_limit jsonb not null,
  config jsonb not null,
  enabled boolean default true,
  created_at timestamptz default now()
);

create table raw_item (
  id uuid primary key,
  source_id text references source_agent(id),
  url text,
  fetched_at timestamptz not null,
  hash text not null,
  content_ref text not null  -- s3 key
);
create index on raw_item (source_id, fetched_at desc);
create unique index on raw_item (hash);

create type event_kind as enum ('announce','preorder','release','discount','price');

create table listing_event (
  id uuid primary key,
  game_id uuid references game(id),
  store_id text references store(id),
  kind event_kind not null,
  title text,
  edition text,
  price numeric(12,2),
  currency text default 'RUB',
  discount_pct numeric(5,2),
  in_stock boolean,
  start_at timestamptz,
  end_at timestamptz,
  url text,
  source_id text references source_agent(id),
  signature_hash text not null,
  created_at timestamptz default now()
);
create index on listing_event (game_id, created_at desc);
create unique index on listing_event (signature_hash);

-- Timescale для истории цен
create table price_history (
  game_id uuid references game(id),
  store_id text references store(id),
  observed_at timestamptz not null,
  price numeric(12,2) not null,
  currency text default 'RUB',
  primary key (game_id, store_id, observed_at)
);
-- преобразовать в hypertable в init миграции
-- select create_hypertable('price_history','observed_at');

create table alert_rule (
  id uuid primary key,
  name text not null,
  logic text not null check (logic in ('AND','OR')),
  conditions jsonb not null,
  channels text[] not null, -- ['webpush','telegram']
  cooldown_hours int default 12,
  enabled boolean default true,
  created_at timestamptz default now()
);

create table notification (
  id uuid primary key,
  rule_id uuid references alert_rule(id),
  event_id uuid references listing_event(id),
  status text not null, -- 'sent'|'error'|'deferred'
  sent_at timestamptz,
  meta jsonb default '{}'
);
```

---

# 3) Агентная платформа

## 3.1 Интерфейс SDK

```python
class BaseAgent:
    TYPE = "html"  # 'api' | 'html' | 'headless' | 'telegram_public'
    CONFIG_SCHEMA: dict = {...}  # JSON Schema валидация в UI

    def __init__(self, config: dict, secrets: dict, ctx: "RuntimeContext"): ...

    def fetch(self) -> "Iterable[Fetched]":
        """
        Вернуть итератор Fetched{url, status, body, headers, fetched_at}
        Учитывать rate_limit, retries, daily_pages_cap, robots.txt.
        """

    def parse(self, fetched: "Fetched") -> "Iterable[ListingEventDraft]":
        """
        Извлечь черновые события: {title, url, store_id?, kind?, price?, discount_pct?, edition?, in_stock?}
        без game_id; нормализация названия в отдельном шаге пайплайна.
        """
```

## 3.2 Манифест агента (импорт/экспорт)

* Файл `manifest.json` в ZIP. **Секреты пустые**; вводятся через UI и сохраняются в локальном `.secrets.json`.

```json
{
  "version": "1.0",
  "id": "hobbygames_coming_soon",
  "name": "Hobby Games — Coming Soon",
  "type": "html",
  "entrypoint": "agent.py",
  "schedule": { "cron": "0 */2 * * *", "timezone": "Europe/Moscow" },
  "rate_limit": { "rps": 0.3, "burst": 1, "daily_pages_cap": 50 },
  "config": {
    "start_urls": ["https://hobbygames.ru/coming-soon"],
    "mode": "search_watch",
    "selectors": {
      "item": ".product-item",
      "title": ".product-item__title",
      "price": ".product-item__price",
      "url": "a.product-item__link::attr(href)",
      "badge": ".product-item__label"
    },
    "price_regex": "([0-9][0-9\\s]+)\\s*₽"
  },
  "secrets": {}
}
```

## 3.3 Примеры агентов (скелеты)

### a) Nastol.io — публикации (search-watch)

* URL: `https://nastol.io/publications` (и конкретная статья для watch: `.../8739_...`)
* Извлекаем карточки постов: заголовок, ссылка, дата; в тексте ищем названия из watchlist, маркеры `предзаказ|релиз|в продаже`.

### b) Лавка Игр — магазин (search/sku)

* URL: `https://www.lavkaigr.ru/shop/`
* Парсить карточки, цена/наличие/метки «новинка/предзаказ/акция».

### c) HobbyGames — coming soon / catalog-new

* URL: `https://hobbygames.ru/coming-soon`, `https://hobbygames.ru/catalog-new`
* Возможно частично **headless** (Playwright) при динамической выдаче.

### d) Telegram публичный канал `t.me/s/nastole`

* Тип `telegram_public`: HTML выдача архива постов; заголовок/текст/ссылки/дата.

> **Режимы:**
> **SKU-watch** — мониторим конкретные товарные URL (экономит квоту, выше точность цен и скидок).
> **Search-watch** — «поиск по каталогу» с фильтром на watchlist (названия игр/синонимы).

---

# 4) Пайплайн обработки

## 4.1 Последовательность

1. Планировщик запускает `agent.fetch()` с учётом квот (`daily_pages_cap`) и `rps`.
2. HTML/JSON сохраняется в MinIO (`raw_item`), сохраняем `hash(url|body)`.
3. `agent.parse()` → черновые события `ListingEventDraft`.
4. **Нормализация**:

   * очистка текста (lower, удаление мусора, RU-токенизация),
   * маппинг к `game` через title/синонимы + fuzzy score (>= threshold),
   * при low-confidence (например, `0.6–0.75`) — опциональный вызов **LLM (Ollama)**: извлечь `game`, `kind`, `edition`, `price`, `discount`, `in_stock` из текста/HTML-фрагментов.
     Промпт (пример, RU):

     ```
     Задача: извлечь из фрагмента карточки настольной игры поля: game_title, kind (announce|preorder|release|discount|price), price_rub, discount_pct, in_stock (true/false), edition.
     Ответ в JSON. Если неизвестно — null. Текст:
     ---
     {{TEXT}}
     ```
5. Обогащение: `store_id`, валюта (RUB), флаги `in_stock`, период скидки (если виден).
6. **Дедупликация**: `signature_hash = sha256(normalize(title)|store_id|edition|round_price|date_bucket(24h))`.

   * Если подпись встречалась за последние 24–72 ч — обновить/слить; иначе — новый `listing_event`.
7. История цен: запись в `price_history` при наличии `price`.
8. Оповещения: см. ниже.

## 4.2 Нормализация названия

* Удалить слова: «настольная игра», «издание», «база», «делюкс», «эксклюзив», «набор» и т.п.
* Приводить латиницу/кириллицу (напр. «Dune: Империум» ↔ «Dune: Imperium»).
* Fuzzy-сравнение с `game.title` и `synonyms[]`.
* Опционально уточнение через LLM, если score ниже порога.

---

# 5) Правила и уведомления

## 5.1 Условия (конструктор)

* Поля: `game`, `title`, `kind`, `price`, `discount_pct`, `store_id`, `region` (RU).
* Операторы: `in`, `contains`, `contains_any`, `>=`, `<=`, `=`.
* `logic`: `AND` / `OR`.
* **Cooldown**: часы подавления повторов.
* Повтор определяется по `signature_hash` последнего срабатывания.

### Пример 1 — искомая игра + предзаказ/релиз

```json
{"logic":"OR","conditions":[
  {"field":"game","op":"in","value":["Громкое дело","Gromkoe Delo"]},
  {"field":"title","op":"contains_any","value":["предзаказ","в продаже","release","preorder"]}
],"channels":["webpush", "telegram"],"cooldown_hours":12,"enabled":true}
```

### Пример 2 — скидка ≥ 20% в Лавке/Хобби

```json
{"logic":"AND","conditions":[
  {"field":"discount_pct","op":">=","value":20},
  {"field":"store_id","op":"in","value":["lavkaigr_shop","hobbygames_coming_soon"]}
],"channels":["webpush", "telegram"],"cooldown_hours":12,"enabled":true}
```

## 5.2 Каналы

* **Web-Push** (генерация VAPID в UI; подписка браузера; тест-пуш).
* **Telegram** (опционально): `bot_token`, `chat_id` в UI.

## 5.3 Шаблоны уведомлений

* Заголовок: `{{game_title}} — {{kind}}`
* Тело: `Магазин: {{store_name}} | Цена: {{price}} ₽ (скидка {{discount_pct}}%) | {{in_stock ? "в наличии" : "нет"}} | {{url}}`
* Footer: «Настройки уведомлений — в приложении».

---

# 6) API (FastAPI, ключевые эндпоинты)

* `GET /healthz`
* **Auth (локальная, один пользователь)**: `POST /auth/login`
* **Игры (watchlist)**:

  * `GET /games`, `POST /games`, `PUT /games/{id}`, `DELETE /games/{id}`
* **Магазины**:

  * `GET /stores`, `POST /stores`
* **Агенты**:

  * `GET /agents`, `POST /agents` (создать), `PUT /agents/{id}`, `DELETE /agents/{id}`
  * `POST /agents/{id}/run` (ручной прогон)
  * `POST /agents/import` (ZIP), `GET /agents/{id}/export` (ZIP)
* **События/лента**:

  * `GET /events?game_id=&store_id=&kind=&from=&to=&min_discount=&max_price=`
  * `GET /events/{id}`
* **История цен**:

  * `GET /prices?game_id=&store_id=&from=&to=` — для графиков
* **Правила**:

  * `GET /rules`, `POST /rules`, `PUT /rules/{id}`, `DELETE /rules/{id}`
  * `POST /rules/{id}/test` (превью сработок на последнем батче)
* **Экспорт/импорт БД**:

  * `GET /export/full` (ZIP)
  * `POST /import/full` (ZIP; `dry_run=true|false`)
* **Настройки уведомлений**:

  * `GET /settings/notifications`, `PUT /settings/notifications`
  * `POST /notifications/test/webpush`, `POST /notifications/test/telegram`

---

# 7) Импорт/экспорт данных

## 7.1 Ежедневный автодамп (ZIP)

```
export-YYYY-MM-DD.zip
  games.ndjson
  stores.ndjson
  listing_events.ndjson
  price_history.ndjson
  alert_rules.json
  sources.json
  version.json    # {"schema":"1.0","created_at":"..."}
  checksums.txt
```

* Формат: **JSON/NDJSON**, без шифрования (по требованию).
* Импорт: `dry_run` отчёт (added/updated/skipped), затем применение.

---

# 8) UI (React, RU)

## 8.1 Разделы

* **Источники**: список (статус, частота, квоты, использовано сегодня), создать/редактировать, импорт/экспорт, ручной прогон, логи.
* **Игры (watchlist)**: добавить игру, синонимы, сопоставление с событиями, привязка BGG-ID (опц.).
* **Лента событий**: фильтры (игра/магазин/тип/даты/цена/скидка), переход на исходный URL, предпросмотр сырья.
* **Графики цен**: линейные графики по выбранной игре, выбор магазинов, период, экспорт CSV.
* **Правила**: конструктор условий, каналы, cooldown, превью.
* **Экспорт/импорт**: мастера с dry-run отчётом.
* **Настройки**: SMTP Yandex (по умолчанию), Web-Push VAPID, Telegram (опц.), «тихие часы» (глобально).
* **Мониторинг**: дашборд — успешность агентов, ретраи, квоты/сутки.

---

# 9) Планировщик, квоты и ретраи

* **Celery beat** — расписания per-agent (cron/interval, `timezone: Europe/Moscow`).
* Квоты:

  * глобально: **≤ 1000 страниц/сутки** (счётчик в Redis),
  * на агент: `daily_pages_cap` + `rps`/`burst` (токен-бакет).
* Ретраи: экспоненциальный backoff, например `1m, 5m, 15m, 1h` (max 5).
* **Политика частот (по умолчанию для стартовых):**

  * `hobbygames / lavkaigr`: 1–2 ч (search-watch), кап 50–80.
  * `nastol.io/publications`: 1 ч, кап 50; конкретная статья — 6 ч, кап 5.
  * Остальные (evrikus, crowdgames, gaga, zvezda, choochoogames): 2–4 ч, кап 30–50.
* Headless (Playwright) включать только если HTML-агент не даёт данные.

---

# 10) Набор стартовых источников (инициализация)

Создать в системе агенты для:

```
https://nastol.io/publications/8739_predzakaz_na_gromkoe_delo_startoval   (html, SKU-watch)
https://hobbygames.ru/coming-soon                                         (html/headless, search)
https://hobbygames.ru/catalog-new                                         (html/headless, search)
https://nastol.io/publications                                            (html, search)
https://evrikus.ru/catalog/                                               (html, search)
https://www.lavkaigr.ru/shop/                                             (html, search/sku)
https://www.lavkaigr.ru/projects/                                         (html, search)
https://www.crowdgames.ru/collection/igry-crowd-games                     (html, search)
https://gaga.ru/                                                          (html, search)
https://zvezda.org.ru/catalog/nastolnye_igry/                             (html, search)
https://choochoogames.ru/shop                                            (html, search)
```

---

# 11) Наблюдаемость и качество

## 11.1 Метрики (Prometheus)

* `agent_runs_total{agent_id,status}`
* `agent_pages_fetched_total{agent_id}`
* `daily_pages_used` / `daily_pages_cap`
* `events_created_total{kind}`
* `notifications_sent_total{channel,status}`
* `llm_calls_total{result=ok|fail, reason}`
* `event_dedup_ratio`

## 11.2 Тестирование

* **Record/Replay** для HTML (VCR.py).
* Набор эталонных страниц (минимум по 1 на источник) с ожидаемыми полями.
* Тесты нормализации (синонимы, fuzzy).
* Тест правил (AND/OR, cooldown).
* E2E: от `fetch` до Web-Push (с mocked Web-Push).

---

# 12) Безопасность и приватность

* Локальное однопользовательское приложение.
* Секреты в `.secrets.json` (локально), в `manifest.json` — пустые, ввод через UI.
* HTTPS на усмотрение (локальная среда — необязательно).
* Соблюдение robots.txt, бережные лимиты.
* Авто-очистка данных старше **2 лет** (nightly job).

---

# 13) Графики и экспорт

* **Линейные графики** цены по времени (по игре, с выбором магазинов и интервалов).
* Экспорт графичных данных в **CSV** (колонки: `observed_at, store, price, currency`).

---

# 14) Приёмка (Definition of Done)

1. Поднимается через `docker compose up`, UI доступен на `http://localhost`, язык — русский.
2. Созданы 11 стартовых агентов, выполняются по расписанию, суммарно ≤ 455 стр./сутки.
3. События типов `announce|preorder|release|discount|price` создаются, дубли подавляются; история цен пишется.
4. Работают правила AND/OR; Web-Push доставляют уведомления; Telegram включается после ввода токена.
5. График цены строится для выбранной игры по ≥2 магазинам; CSV выгружается.
6. Импорт/экспорт агентов (ZIP) и полный экспорт БД (ежедневно) работают; импорт — с dry-run.
7. Авто-очистка данных старше 2 лет работает по ночному расписанию.
8. Метрики доступны (простейший /metrics), логи информативны.

---

# 15) Дополнения: алгоритмы и псевдокод

## 15.1 Вычисление `signature_hash`

```
round_price = price is None ? "null" : str(int(round(price)))
bucket = floor(created_at to 24h)
base = f"{normalize(title)}|{store_id}|{normalize(edition)}|{round_price}|{bucket}"
signature_hash = sha256(base.encode()).hexdigest()
```

## 15.2 Оценка правила (упрощённо)

```python
def matches(event, rule):
    def test(cond):
        v = getattr_or_lookup(event, cond['field'])
        op = cond['op']; val = cond['value']
        if op == 'in': return v in val
        if op == 'contains': return isinstance(v, str) and val in v
        if op == 'contains_any': return any(x in (v or '') for x in val)
        if op == '>=': return v is not None and v >= val
        if op == '<=': return v is not None and v <= val
        if op == '=':  return v == val
        return False
    results = [test(c) for c in rule['conditions']]
    return all(results) if rule['logic']=='AND' else any(results)
```

## 15.3 LLM-вызов (если нужно)

* Вызывать **только** при низкой уверенности сопоставления игры или для классификации `kind` по тексту.
* Ограничить частоту LLM-вызовов (метрика `llm_calls_total`).

---

# 16) Готовые пресеты агентов (селекторы — как заглушки)

> При генерации кода — заполнить корректными селекторами под текущую разметку, добавить unit-тесты на образцах HTML.

* **HobbyGames /coming-soon**: `item:.product-item`, `title:.product-item__title`, `price:.product-item__price`, `url:a.product-item__link@href`.
* **ЛавкаИгр /shop**: `item:.product-card`, `title:.product-card__title`, `price:.price`, `badge:.badge`, `url:a.product-card__link@href`.
* **Nastol.io /publications**: `item:.post-card`, `title:.post-card__title`, `date:time[datetime]`, `url:a@href`.
