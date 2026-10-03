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

## Ветки

`master` ← `release/stage-N` ← `feature/<название>-api`

Примеры: `feature/catalog-api`, `feature/orders-api`, `feature/accounts-api`.
