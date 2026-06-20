# Transfer Site Flask V1

Отдельный сайт на Python/Flask для сервиса трансферов.

## Страницы

- `/` — главная страница
- `/reviews` — публичные отзывы из Supabase
- `/pay?order_id=123456` — страница оплаты заказа
- `/health` — проверка сервиса

## Подключение к боту

Сайт ведёт пользователя в основного Telegram-бота:

`PUBLIC_BOT_URL=https://t.me/BatumiTransferBot`

Чтобы бот отправлял клиента на сайт для оплаты, в env бота поставь:

`PUBLIC_PAYMENT_URL=https://домен-сайта/pay`

Для отзывов:

`PUBLIC_REVIEWS_URL=https://домен-сайта/reviews`

## Запуск локально в VS Code

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Установка:

```bash
pip install -r requirements.txt
```

Создай `.env` по примеру `.env.example`.

Запуск:

```bash
python app.py
```

Открыть:

`http://127.0.0.1:10000`
