# Megano — интернет-магазин

Fullstack-проект: бэкенд на Django + Django REST Framework, фронтенд на Vue, фоновая обработка оплаты через Celery +
Redis.

## Возможности

- Каталог товаров с категориями, страница товара, отзывы
- Баннеры, популярные и лимитированные товары, распродажи
- Корзина и оформление заказа, история заказов
- Оплата в фоне через Celery (фиктивный платёжный сервис)
- Регистрация, вход, профиль с аватаром
- Админ-панель Django
- Валидация на трёх уровнях: фронтенд, формы Django, модели

## Стек

Python 3.11+, Django, DRF, Celery, Redis, SQLite, Vue, Docker (для Redis), mypy

## Требования

- Python 3.11+
- Docker (для Redis)
- Git

## Установка

```bash
git clone https://github.com/leniksergey/python-django-shop.git
cd python-django-shop

# Виртуальное окружение
python3 -m venv venv         # на Windows: python -m venv venv
source venv/bin/activate     # Linux/Mac
# venv\Scripts\activate      # Windows

# Зависимости
pip install -r requirements.txt

# Фронтенд (editable-режим)
cd vue-frontend
pip install -e .
cd ..
```

## Настройка окружения

Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

Переменные:

- `SECRET_KEY` — секретный ключ Django;
- `DEBUG` — режим отладки (`True` / `False`);
- `ALLOWED_HOSTS` — разрешённые хосты через запятую;
- `REDIS_URL` — адрес Redis для Celery.

## Redis

```bash
docker run -d --name shop-redis -p 6379:6379 redis:7
```

Если контейнер уже создан:

```bash
docker start shop-redis
```

## База данных и демо-данные

```bash
python manage.py migrate
python manage.py loaddata fixtures/demo.json
cp -r fixtures/demo_media/. media/
```

Фикстура `fixtures/demo.json` добавляет:

- категории, товары, картинки;
- администратора и покупателей;
- отзывы, заказы, настройки доставки.

## Запуск

**Терминал 1 — Celery:**

```bash
celery -A shop worker -l info
```

**Терминал 2 — Django:**

```bash
python manage.py runserver 8000
```

- Сайт: http://127.0.0.1:8000
- Админка: http://127.0.0.1:8000/admin/

## Тестовые учётные данные

| Роль          | Логин    | Пароль     |
|---------------|----------|------------|
| Администратор | `admin`  | `admin123` |
| Покупатель    | `buyer1` | `123456`   |
| Покупатель    | `buyer2` | `123456`   |
| Покупатель    | `buyer3` | `123456`   |
| Покупатель    | `vasya`  | `123456`   |

## Валидация

Все правила — в [docs/VALIDATION.md](docs/VALIDATION.md).

Три уровня:

- **Frontend (Vue)** — ошибки при вводе, под полями;
- **Backend (Django Forms)** — `OrderCreateForm`, `OrderUpdateForm`, `PaymentForm`;
- **Модель (validators)** — регулярки для телефона, минимальные значения.

## Очередь оплаты

Оплата обрабатывается в фоне через Celery + Redis.

**Логика фиктивного сервиса:**

- чётный и не заканчивается на 0 → оплата **подтверждается** (`PAID`);
- нечётный или заканчивается на 0 → **ошибка** (`FAILED`).

Без запущенного воркера оплата вернёт ошибку.

## Структура проекта

```
python-django-shop/
├── accounts/          # пользователи, профили
├── catalog/           # категории, товары, отзывы
├── orders/            # заказы, доставка, оплата (Celery)
├── shop/              # настройки Django, celery.py
├── vue-frontend/      # Vue-фронтенд (editable)
├── fixtures/          # демо-данные (demo.json, demo_media/)
├── docs/              # VALIDATION.md
├── media/             # загруженные файлы (создаётся локально, в Git не хранится)
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## Ветки

`main` ← `release/stage-N` ← `feature/<название>-api`

Примеры: `feature/catalog-api`, `feature/orders-api`, `feature/accounts-api`.
