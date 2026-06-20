import os
import html
from urllib.parse import quote

from dotenv import load_dotenv
import requests
from flask import Flask, request, render_template_string

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ORDERS_TABLE = os.getenv("SUPABASE_TABLE_NAME", "orders")
SUPABASE_REVIEWS_TABLE = os.getenv("SUPABASE_REVIEWS_TABLE_NAME", "reviews")

PUBLIC_BOT_URL = os.getenv("PUBLIC_BOT_URL", "https://t.me/BatumiTransferBot")
PUBLIC_SITE_TITLE = os.getenv("PUBLIC_SITE_TITLE", "Трансферы из Батуми")

PAYMENT_BANK_RECEIVER = os.getenv("PAYMENT_BANK_RECEIVER", "")
PAYMENT_BANK_NAME = os.getenv("PAYMENT_BANK_NAME", "Credo Bank")
PAYMENT_BANK_GEL_IBAN = os.getenv("PAYMENT_BANK_GEL_IBAN", "")
PAYMENT_BANK_USD_IBAN = os.getenv("PAYMENT_BANK_USD_IBAN", "")
PAYMENT_BANK_EUR_IBAN = os.getenv("PAYMENT_BANK_EUR_IBAN", "")

PAYMENT_RUB_RECEIVER = os.getenv("PAYMENT_RUB_RECEIVER", "Яковлев Андрей Русланович")
PAYMENT_RUB_BANK = os.getenv("PAYMENT_RUB_BANK", "Яндекс Банк")
PAYMENT_RUB_PHONE = os.getenv("PAYMENT_RUB_PHONE", "+7(950)493-96-63")

PAYMENT_TG_WALLET = os.getenv("PAYMENT_TG_WALLET", "")
PAYMENT_CRYPTO_USDT_TRC20 = os.getenv("PAYMENT_CRYPTO_USDT_TRC20", "TH9BE3DhPCpoyGe93iQeMYhAbJWHptiH5y")
PAYMENT_CRYPTO_USDT_TON = os.getenv("PAYMENT_CRYPTO_USDT_TON", "UQC3VjQS0-5Vpgkf29C583OKaz1GBHXxtLnYIro0cuG4QTzv")

EXCHANGE_RATES = {
    "GEL": float(os.getenv("RATE_GEL", "1")),
    "USD": float(os.getenv("RATE_USD", "0.37")),
    "EUR": float(os.getenv("RATE_EUR", "0.32")),
    "RUB": float(os.getenv("RATE_RUB", "27.4")),
}


def supabase_headers():
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def supabase_get(table: str, params: str):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return []
    url = f"{SUPABASE_URL}/rest/v1/{table}{params}"
    try:
        response = requests.get(url, headers=supabase_headers(), timeout=12)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"SUPABASE GET ERROR: {exc}", flush=True)
        return []


def get_order(order_id: str):
    order_id = (order_id or "").strip()
    if not order_id:
        return None
    params = (
        f"?order_id=eq.{quote(order_id)}"
        "&select=order_id,telegram_id,client_name,route,seats,from_place,to_place,"
        "trip_date,pickup_datetime,status,price_gel,deposit_gel,price_usd,price_eur,price_rub"
        "&limit=1"
    )
    rows = supabase_get(SUPABASE_ORDERS_TABLE, params)
    return rows[0] if rows else None


def fetch_reviews(limit: int = 50):
    params = (
        "?is_public=eq.true"
        "&is_approved=eq.true"
        "&select=rating,comment,client_name,route,created_at"
        "&order=created_at.desc"
        f"&limit={limit}"
    )
    return supabase_get(SUPABASE_REVIEWS_TABLE, params)


def safe(value):
    return html.escape(str(value or ""))


def public_client_name(name: str):
    raw = (name or "").strip()
    if not raw:
        return "Клиент"
    raw = raw.split("(@")[0].strip()
    raw = raw.split("@")[0].strip()
    first = raw.split()[0] if raw.split() else "Клиент"
    return first[:24]


def convert_gel(amount_gel: float, currency: str):
    return round(float(amount_gel or 0) * EXCHANGE_RATES.get(currency, 1), 2)


def money(value, currency: str):
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0
    if currency == "RUB":
        return f"{round(amount):,.0f} RUB".replace(",", " ")
    return f"{amount:,.2f} {currency}".replace(",", " ")


def payment_detail(value: str, fallback: str = "уточнит менеджер"):
    value = (value or "").strip()
    return safe(value if value else fallback)


BASE_CSS = """
<style>
:root{--bg:#f5f5f5;--text:#111827;--muted:#6b7280;--dark:#111827;--green:#22c55e;--card:#fff;--line:#e5e7eb}*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--text)}a{color:inherit}.wrap{max-width:1060px;margin:0 auto;padding:24px 16px 52px}.nav{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px}.brand{font-weight:900;font-size:18px}.nav-links{display:flex;gap:12px;flex-wrap:wrap;color:var(--muted);font-size:14px}.hero{background:var(--dark);color:#fff;border-radius:28px;padding:34px;margin-bottom:18px;overflow:hidden}.hero h1{margin:0 0 14px;font-size:clamp(34px,6vw,60px);line-height:.95;letter-spacing:-.04em}.hero p{margin:8px 0;color:#d1d5db;font-size:18px;line-height:1.55;max-width:780px}.buttons{display:flex;gap:12px;flex-wrap:wrap;margin-top:22px}.button{display:inline-block;padding:14px 17px;border-radius:15px;background:var(--green);color:#052e16;font-weight:900;text-decoration:none}.button.secondary{background:rgba(255,255,255,.12);color:white;border:1px solid rgba(255,255,255,.18)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}.card{background:var(--card);border-radius:24px;padding:22px;box-shadow:0 8px 28px rgba(0,0,0,.06)}.card h2,.card h3{margin:0 0 12px}.muted{color:var(--muted);line-height:1.55}.price{font-size:30px;font-weight:900;margin-top:12px}.section{margin-top:18px}.steps{counter-reset:step}.step{display:flex;gap:14px;align-items:flex-start}.step:before{counter-increment:step;content:counter(step);width:34px;height:34px;border-radius:50%;background:var(--dark);color:white;display:inline-flex;align-items:center;justify-content:center;font-weight:900;flex:0 0 auto}.stars{font-size:20px;margin-bottom:10px}.comment{line-height:1.55;white-space:pre-wrap}.meta{color:var(--muted);font-size:14px;margin-top:12px}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;background:#f3f4f6;border-radius:12px;padding:11px;overflow-wrap:anywhere}.warn{margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;color:#7c2d12;border-radius:16px;padding:14px;line-height:1.45}.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:12px;margin-top:18px}.sum-card{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:14px}.sum-card .label{color:#cbd5e1;font-size:13px}.sum-card .value{font-size:20px;font-weight:900;margin-top:6px}.footer{text-align:center;color:var(--muted);margin-top:28px;font-size:14px}
</style>
"""

LAYOUT = """
<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }}</title>""" + BASE_CSS + """</head><body><main class="wrap"><nav class="nav"><div class="brand">{{ site_title }}</div><div class="nav-links"><a href="/">Главная</a><a href="/reviews">Отзывы</a><a href="{{ bot_url }}">Заказать в Telegram</a></div></nav>{{ content|safe }}<div class="footer">© {{ site_title }} · Заказы принимаются через Telegram</div></main></body></html>
"""


def page(title: str, content: str):
    return render_template_string(LAYOUT, title=title, content=content, site_title=PUBLIC_SITE_TITLE, bot_url=PUBLIC_BOT_URL)


@app.get("/")
def index():
    reviews = fetch_reviews(limit=3)
    review_cards = ""
    if reviews:
        for review in reviews:
            rating = int(review.get("rating") or 5)
            stars = "⭐" * max(1, min(5, rating))
            review_cards += f"""
            <article class="card"><div class="stars">{stars}</div><div class="comment">{safe(review.get('comment') or 'Оценка без комментария')}</div><div class="meta">{safe(public_client_name(review.get('client_name')))} · {safe(review.get('route') or 'маршрут')}</div></article>
            """
    else:
        review_cards = """<article class="card"><div class="stars">⭐</div><div class="comment">Отзывы появятся после первых завершённых поездок.</div><div class="meta">Трансферы из Батуми</div></article>"""

    content = f"""
    <section class="hero"><h1>Трансферы из Батуми без нервов</h1><p>Батуми ↔ Тбилиси, Батуми ↔ Владикавказ, Батуми ↔ Сарпи и посылки по маршрутам.</p><p>Водитель заранее, подтверждение заказа, напоминание о рейсе, live-трекинг и поддержка менеджера в Telegram.</p><div class="buttons"><a class="button" href="{safe(PUBLIC_BOT_URL)}">Заказать трансфер</a><a class="button secondary" href="/reviews">Посмотреть отзывы</a></div></section>
    <section class="grid"><article class="card"><h3>Батуми ↔ Владикавказ</h3><p class="muted">Дальний маршрут к границе. Важны связь, водитель заранее и понимание статуса поездки.</p><div class="price">350 GEL</div><p class="muted">за 1 место</p></article><article class="card"><h3>Батуми ↔ Тбилиси</h3><p class="muted">Для поездок между городами, аэропортов, отелей, семей и багажа.</p><div class="price">250 GEL</div><p class="muted">за 1 место</p></article><article class="card"><h3>Батуми ↔ Сарпи</h3><p class="muted">Короткий маршрут, быстрые поездки и передача посылок.</p><div class="price">35 GEL</div><p class="muted">за 1 место</p></article></section>
    <section class="section grid"><article class="card step"><div><h3>Оставляете заявку</h3><p class="muted">В Telegram-боте выбираете маршрут, дату, количество мест и комментарий.</p></div></article><article class="card step"><div><h3>Получаете подтверждение</h3><p class="muted">Менеджер подтверждает заказ, цену и отправляет ссылку на оплату.</p></div></article><article class="card step"><div><h3>Едете спокойно</h3><p class="muted">Водитель назначается заранее, клиент получает статусы и live-трекинг.</p></div></article></section>
    <section class="section"><h2>Отзывы клиентов</h2><div class="grid">{review_cards}</div><div class="buttons"><a class="button" href="/reviews">Все отзывы</a></div></section>
    """
    return page(PUBLIC_SITE_TITLE, content)


@app.get("/reviews")
def reviews_page():
    reviews = fetch_reviews(limit=80)
    cards = ""
    if reviews:
        for review in reviews:
            rating = int(review.get("rating") or 5)
            stars = "⭐" * max(1, min(5, rating))
            cards += f"""<article class="card"><div class="stars">{stars}</div><div class="comment">{safe(review.get('comment') or 'Оценка без комментария')}</div><div class="meta">{safe(public_client_name(review.get('client_name')))} · {safe(review.get('route') or 'маршрут')}</div></article>"""
    else:
        cards = """<article class="card"><div class="stars">⭐</div><div class="comment">Отзывы скоро появятся после первых завершённых поездок.</div><div class="meta">Трансферы из Батуми</div></article>"""
    content = f"""<section class="hero"><h1>Отзывы клиентов</h1><p>Отзывы оставляют клиенты после завершённых поездок.</p><div class="buttons"><a class="button" href="{safe(PUBLIC_BOT_URL)}">Заказать трансфер</a></div></section><section class="grid">{cards}</section>"""
    return page(f"Отзывы — {PUBLIC_SITE_TITLE}", content)


@app.get("/pay")
def pay_page():
    order_id = request.args.get("order_id", "").strip()
    order = get_order(order_id)
    if not order:
        return page("Заказ не найден", """<section class="card"><h1>Заказ не найден</h1><p class="muted">Проверьте ссылку или вернитесь в Telegram и запросите ссылку заново.</p></section>""")

    try:
        deposit_gel = float(order.get("deposit_gel"))
    except (TypeError, ValueError):
        try:
            deposit_gel = round(float(order.get("price_gel") or 0) * 0.5, 2)
        except (TypeError, ValueError):
            deposit_gel = 0

    deposit_usd = convert_gel(deposit_gel, "USD")
    deposit_eur = convert_gel(deposit_gel, "EUR")
    deposit_rub = convert_gel(deposit_gel, "RUB")
    tg_wallet = PAYMENT_TG_WALLET or PUBLIC_BOT_URL

    content = f"""
    <section class="hero"><h1>Оплата заказа №{safe(order_id)}</h1><p>🛣 Маршрут: <strong>{safe(order.get('route') or 'не указан')}</strong></p><p>👥 Мест: <strong>{safe(order.get('seats') or '—')}</strong></p><p>📅 Дата: <strong>{safe(order.get('trip_date') or '—')}</strong></p><p>После оплаты вернитесь в Telegram и нажмите «💳 Я оплатил». Менеджер проверит оплату и закрепит место.</p><div class="buttons"><a class="button" href="{safe(PUBLIC_BOT_URL)}">Вернуться в Telegram</a></div><div class="summary"><div class="sum-card"><div class="label">Предоплата GEL</div><div class="value">{money(deposit_gel,'GEL')}</div></div><div class="sum-card"><div class="label">USD</div><div class="value">{money(deposit_usd,'USD')}</div></div><div class="sum-card"><div class="label">EUR</div><div class="value">{money(deposit_eur,'EUR')}</div></div><div class="sum-card"><div class="label">RUB</div><div class="value">{money(deposit_rub,'RUB')}</div></div></div></section>
    <section class="grid"><article class="card"><h2>🇬🇪 GEL / USD / EUR</h2><p class="muted">Оплата на грузинский банк. Сейчас блок подготовлен под Credo Bank.</p><div><strong>Банк:</strong> {payment_detail(PAYMENT_BANK_NAME,'Credo Bank')}</div><div><strong>Получатель:</strong> {payment_detail(PAYMENT_BANK_RECEIVER,'будет указан менеджером')}</div><p><strong>IBAN GEL:</strong></p><div class="mono">{payment_detail(PAYMENT_BANK_GEL_IBAN,'будет добавлен после открытия счёта')}</div><p><strong>IBAN USD:</strong></p><div class="mono">{payment_detail(PAYMENT_BANK_USD_IBAN,'будет добавлен после открытия счёта')}</div><p><strong>IBAN EUR:</strong></p><div class="mono">{payment_detail(PAYMENT_BANK_EUR_IBAN,'будет добавлен после открытия счёта')}</div><p><strong>Назначение:</strong></p><div class="mono">Order {safe(order_id)}</div><div class="warn">Если реквизиты ещё не указаны, запросите их у менеджера в Telegram.</div></article>
    <article class="card"><h2>🇷🇺 RUB через СБП</h2><p><strong>Сумма:</strong> {money(deposit_rub,'RUB')}</p><p><strong>Получатель:</strong> {payment_detail(PAYMENT_RUB_RECEIVER)}</p><p><strong>Банк:</strong> {payment_detail(PAYMENT_RUB_BANK)}</p><p><strong>Телефон СБП:</strong></p><div class="mono">{payment_detail(PAYMENT_RUB_PHONE)}</div><p><strong>Комментарий:</strong></p><div class="mono">Order {safe(order_id)}</div><div class="warn">Обязательно укажите номер заказа в комментарии, иначе оплату придётся искать вручную.</div></article>
    <article class="card"><h2>₿ Telegram / Crypto</h2><p><strong>Связь по оплате:</strong></p><div class="mono">{payment_detail(tg_wallet)}</div><p><strong>USDT TRC20:</strong></p><div class="mono">{payment_detail(PAYMENT_CRYPTO_USDT_TRC20)}</div><p><strong>USDT TON:</strong></p><div class="mono">{payment_detail(PAYMENT_CRYPTO_USDT_TON)}</div><p><strong>Комментарий / memo:</strong></p><div class="mono">Order {safe(order_id)}</div><div class="warn">Внимательно выбирайте сеть. USDT TRC20 отправлять только в TRON/TRC20. USDT TON отправлять только в TON. При ошибке сети платёж может быть потерян.</div></article></section>
    """
    return page(f"Оплата заказа №{order_id}", content)


@app.get("/health")
def health():
    return "OK"


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
