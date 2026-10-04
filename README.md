# Интернет-магазин

## Установка

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Подключение фронтенда

```bash
cd diploma-frontend
python setup.py sdist
cd ..
pip install diploma-frontend/dist/*.tar.gz
```

## Запуск

```bash
python manage.py migrate
python manage.py loaddata catalog/fixtures/catalog.json
python manage.py createsuperuser
python manage.py runserver
```

Сайт: http://127.0.0.1:8000, админка: http://127.0.0.1:8000/admin/


## Валидация

Все правила — в [docs/VALIDATION.md](docs/VALIDATION.md).

Три уровня:
- **Frontend (Vue)** — ошибки при вводе, под полями
- **Backend (Django Forms)** — `OrderCreateForm`, `OrderUpdateForm`, `PaymentForm`
- **Модель (validators)** — регулярки для телефона, минимальные значения

Тестовые карты (Luhn-валидные):
- `4242424242424242`
- `4111111111111111`
- `5555555555554444`

Срок действия: `12/2027`, CVV: `123`.

## Очередь оплаты

Оплата обрабатывается в фоне через Celery + Redis. Redis запускается в Docker:

```bash
docker run -d --name shop-redis -p 6379:6379 redis:7
```

Если контейнер уже создан, достаточно `docker start shop-redis`.

Воркер Celery запускается в отдельном терминале (при активированном venv):

```bash
celery -A shop worker -l info
```

Без запущенного воркера оплата вернёт ошибку.

## Ветки

`master` ← `release/stage-N` ← `feature/<название>-api`

Примеры: `feature/catalog-api`, `feature/orders-api`, `feature/accounts-api`.
