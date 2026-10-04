# Валидация данных в проекте

Документ описывает все правила валидации, реализованные в проекте, на трёх уровнях:
**frontend** (Vue), **backend** (Django Forms) и **база данных** (validators).

---

## Принципы

- **Фронт** — для UX: показывает ошибки пользователю **сразу при вводе**, до отправки на сервер.
- **Бэк** — для безопасности: проверяет данные **при POST** и защищает от подделки запроса через DevTools или прямые API-вызовы.
- **БД** — последний рубеж: валидаторы на уровне модели.

**Ключевое правило:** данные из запроса **никогда не считаются доверенными**.

---

## 1. Оформление заказа

### Шаг 1 — Параметры пользователя

| Поле | Фронт | Бэк | Сообщение |
|---|---|---|---|
| ФИО | не пусто, ≥2 символа, только буквы/пробел/точка/дефис, **без цифр** | `CharField(max_length=200, min_length=1)` | «ФИО не должно содержать цифры» |
| Телефон | 10–15 цифр (без `+`, скобок, пробелов) | `RegexValidator(r"^\+?\d{10,15}$")` | «Телефон должен содержать 10–15 цифр» |
| Email | регулярка `^[^\s@]+@[^\s@]+\.[^\s@]+$` | `EmailField` | «Введите корректный email» |

### Шаг 2 — Способ доставки

| Поле | Фронт | Бэк | Сообщение |
|---|---|---|---|
| Тип доставки | не пусто (radio) | `ChoiceField([("ordinary"), ("express")])` | «Выберите способ доставки» |
| Город | не пусто, ≥2, только буквы/пробел/дефис, **без цифр** | `CharField(max_length=100, min_length=1)` | «Название города не должно содержать цифры» |
| Адрес | не пусто, ≥3 символа | `CharField(max_length=255, min_length=1)` | «Адрес слишком короткий» |

### Шаг 3 — Способ оплаты

| Поле | Фронт | Бэк |
|---|---|---|
| Способ оплаты | не пусто | `ChoiceField([("online"), ("someone")])` |

### Шаг 4 — Подтверждение

Перед отправкой выполняются проверки шагов 1–3. При успехе — POST `/api/order/<id>/`.

---

## 2. Оплата

| Поле | Фронт | Бэк | Сообщение |
|---|---|---|---|
| Номер карты | 13–19 цифр, алгоритм Луна | `CharField(min_length=13, max_length=25)` + `clean_number` (Luhn) | «Некорректный номер карты» |
| Имя владельца | ≥2, только буквы/пробел/точка/дефис | `CharField(min_length=2, max_length=100)` + `clean_name` | «Только буквы, пробел, точка и дефис» |
| Месяц | 1–12 | `IntegerField(min_value=1, max_value=12)` | «Месяц от 1 до 12» |
| Год | ≥ текущего, ≤ +15 лет, срок не истёк | `IntegerField` + `clean_year` + `clean` | «Год не может быть меньше текущего» |
| CVV | ровно 3 цифры | `CharField(min_length=3, max_length=3)` + `clean_cvv` | «CVV — ровно 3 цифры» |

**Особенность:** фронт отправляет поле `code`, форма ожидает `cvv`. В `PaymentForm.__init__` выполняется маппинг `code → cvv`.

**Сумма не принимается от клиента** — берётся из `order.total_cost` на бэке.

---

## 3. Создание заказа (корзина)

Валидация в `OrderCreateForm.clean_items`:

| Проверка | Сообщение |
|---|---|
| `items` — непустой список | «Корзина пуста» |
| Каждый элемент — объект | «Элемент #N должен быть объектом» |
| У элемента есть `id` и `count` (1–1000) | «Некорректный элемент #N» |
| Все товары существуют в БД | «Товары не найдены: [...]» |
| Цена товара > 0 | «Некорректная цена у товара X» |
| Дубликаты id схлопываются (суммируется `count`) | — |

---

## 4. Бизнес-проверки (не поля, а правила)

### Подтверждение заказа (`order_detail`)

| Проверка | HTTP-статус |
|---|---|
| Заказ — свой (или анонимный) | **403 forbidden** |
| Нельзя редактировать оплаченный/отменённый заказ | **409 order is locked** |
| Валидация формы `OrderUpdateForm` | **400 + errors** |

### Оплата (`payment`)

| Проверка | HTTP-статус |
|---|---|
| Заказ существует | **404** |
| Заказ — свой | **403 forbidden** |
| Не оплачен ранее | **409 already paid** |
| Статус `ACCEPTED` (или `FAILED`) | **409 order not accepted** |
| Валидация формы `PaymentForm` | **400 + errors** |
| `order.total_cost > 0` | **400 invalid amount** |
| Celery worker недоступен | **503 service unavailable** |
| `process_payment` вернул `False` | **500 payment failed** |
| Успех | **200 `{status: "ok", orderId}`** |

---

## 5. Где что лежит в коде

| Файл | Что там |
|---|---|
| `orders/forms.py` | `OrderCreateForm`, `OrderUpdateForm`, `PaymentForm` — вся валидация форм |
| `orders/views.py` | `create_order`, `order_detail`, `payment` — бизнес-проверки и HTTP-статусы |
| `orders/models.py` | Модели `Order`, `OrderItem` |
| `orders/validators.py` | `PHONE_RE` — регулярка для телефона |
| `orders/tasks.py` | `process_payment` — Celery-задача оплаты |
| `frontend/assets/js/order-detail.js` | `validateStep1/2/3`, `watch` — валидация шагов заказа |
| `frontend/assets/js/payment.js` | `validatePayment`, `luhnCheck`, `watch` — валидация карты |
| `frontend/templates/frontend/order.html` | `:class`, `v-if="errors.X"`, `.form-error` — отображение ошибок |
| `frontend/templates/frontend/payment.html` | То же для страницы оплаты |

---

## 6. Как это работает — механика

### Фронт-валидация «на лету»

В `order-detail.js` и `payment.js` есть блок `watch`:

```js
watch: {
    fullName() { this.validateStep1() },
    phone() { this.validateStep1() },
    email() { this.validateStep1() },
    ...
}
```

**При любом изменении поля** Vue автоматически вызывает валидацию, обновляет `errors`, и в HTML через `v-if="errors.fullName"` появляется сообщение.

### Отображение ошибок

В `order.html` и `payment.html`:

```html
<input :class="{'form-input_error': errors.fullName}" v-model="fullName">
<div v-if="errors.fullName" class="form-error">${ errors.fullName }$</div>
```

- `:class` — красная рамка при ошибке
- `v-if` — сообщение под полем

### Бэк-валидация

Каждая форма проверяется через `form.is_valid()`. При ошибке:

```python
return JsonResponse(
    {"error": "validation failed", "errors": form.errors}, status=400
)
```

Фронт в `.catch` читает `err.response.data.errors` и показывает пользователю.

---

## 7. Запуск для тестирования валидации

Нужно **3 терминала** одновременно:

**1. Redis (docker):**
```bash
docker start shop-redis
```

**2. Django:**
```bash
python manage.py runserver 8001
```

**3. Celery:**
```bash
celery -A shop worker -l info
```

**Сценарий теста:**
1. Корзина → товар → «Оформить»
2. Шаг 1 — невалидные данные → ошибки при вводе
3. Заполнить правильно → «Дальше»
4. Шаг 2 — город `123` → ошибка
5. Шаг 3 — выбрать оплату
6. Шаг 4 — «Оплатить»
7. Номер `1` → ошибка при вводе
8. Всё правильно → 200 → alert «Успешная оплата» → редирект

---

## 8. Технологии

- **Frontend:** Vue 3 (CDN), Axios
- **Backend:** Django 6.1, Django Forms
- **Асинхронные задачи:** Celery 5.6 + Redis 7 (Docker)
- **БД:** SQLite (dev)
