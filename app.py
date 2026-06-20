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
PUBLIC_PHONE = os.getenv("PUBLIC_PHONE", "")

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
        response = requests.get(
            url,
            headers=supabase_headers(),
            timeout=12,
        )
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
  :root {
    --bg: #f5f5f5;
    --text: #111827;
    --muted: #6b7280;
    --dark: #111827;
    --green: #22c55e;
    --green-dark: #15803d;
    --card: #ffffff;
    --line: #e5e7eb;
    --amber-bg: #fff7ed;
    --amber-line: #fed7aa;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
  }
  a { color: inherit; }
  .wrap {
    max-width: 1120px;
    margin: 0 auto;
    padding: 24px 16px 56px;
  }
  .nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 18px;
  }
  .brand {
    font-weight: 900;
    font-size: 18px;
  }
  .nav-links {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    color: var(--muted);
    font-size: 14px;
  }
  .nav-links a {
    text-decoration: none;
  }
  .hero {
    background:
      radial-gradient(circle at 85% 20%, rgba(34,197,94,.23), transparent 28%),
      var(--dark);
    color: white;
    border-radius: 30px;
    padding: 36px;
    margin-bottom: 18px;
    overflow: hidden;
  }
  .hero h1 {
    margin: 0 0 14px;
    font-size: clamp(36px, 6vw, 64px);
    line-height: .95;
    letter-spacing: -0.05em;
    max-width: 900px;
  }
  .hero p {
    margin: 8px 0;
    color: #d1d5db;
    font-size: 18px;
    line-height: 1.55;
    max-width: 820px;
  }
  .hero .small {
    font-size: 15px;
    color: #cbd5e1;
  }
  .buttons {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 22px;
  }
  .button {
    display: inline-block;
    padding: 14px 17px;
    border-radius: 15px;
    background: var(--green);
    color: #052e16;
    font-weight: 900;
    text-decoration: none;
    border: 0;
  }
  .button:hover { background: #16a34a; }
  .button.secondary {
    background: rgba(255,255,255,.12);
    color: white;
    border: 1px solid rgba(255,255,255,.18);
  }
  .button.light {
    background: #111827;
    color: white;
  }
  .badges {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
  }
  .badge {
    background: rgba(255,255,255,.10);
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 999px;
    padding: 9px 12px;
    font-weight: 700;
    color: #f9fafb;
    font-size: 14px;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px;
  }
  .card {
    background: var(--card);
    border-radius: 24px;
    padding: 22px;
    box-shadow: 0 8px 28px rgba(0,0,0,.06);
  }
  .card h2, .card h3 {
    margin: 0 0 12px;
  }
  .muted {
    color: var(--muted);
    line-height: 1.55;
  }
  .price {
    font-size: 30px;
    font-weight: 900;
    margin-top: 12px;
  }
  .section {
    margin-top: 26px;
  }
  .section-title {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 16px;
    flex-wrap: wrap;
    margin: 0 0 14px;
  }
  .section-title h2 {
    margin: 0;
    font-size: 30px;
    letter-spacing: -0.03em;
  }
  .step {
    display: flex;
    gap: 14px;
    align-items: flex-start;
  }
  .step-num {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: var(--dark);
    color: white;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    flex: 0 0 auto;
  }
  .stars {
    font-size: 20px;
    margin-bottom: 10px;
  }
  .comment {
    line-height: 1.55;
    white-space: pre-wrap;
  }
  .meta {
    color: var(--muted);
    font-size: 14px;
    margin-top: 12px;
  }
  .mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    background: #f3f4f6;
    border-radius: 12px;
    padding: 11px;
    overflow-wrap: anywhere;
  }
  .warn {
    margin-top: 14px;
    background: var(--amber-bg);
    border: 1px solid var(--amber-line);
    color: #7c2d12;
    border-radius: 16px;
    padding: 14px;
    line-height: 1.45;
  }
  .summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
    gap: 12px;
    margin-top: 18px;
  }
  .sum-card {
    background: rgba(255,255,255,.1);
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 16px;
    padding: 14px;
  }
  .sum-card .label {
    color: #cbd5e1;
    font-size: 13px;
  }
  .sum-card .value {
    font-size: 20px;
    font-weight: 900;
    margin-top: 6px;
  }
  .faq details {
    background: white;
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 8px 28px rgba(0,0,0,.05);
  }
  .faq details + details { margin-top: 10px; }
  .faq summary {
    cursor: pointer;
    font-weight: 900;
  }
  .faq p {
    color: var(--muted);
    line-height: 1.55;
  }
  .cta {
    background: var(--dark);
    color: white;
    border-radius: 28px;
    padding: 30px;
  }
  .cta p { color: #d1d5db; line-height: 1.55; }
  .footer {
    text-align: center;
    color: var(--muted);
    margin-top: 28px;
    font-size: 14px;
  }
</style>
"""


LAYOUT = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  """ + BASE_CSS + """
</head>
<body>
  <main class="wrap">
    <nav class="nav">
      <div class="brand">{{ site_title }}</div>
      <div class="nav-links">
        <a href="/">Главная</a>
        <a href="/#routes">Маршруты</a>
        <a href="/#faq">FAQ</a>
        <a href="/reviews">Отзывы</a>
        <a href="{{ bot_url }}">Заказать</a>
      </div>
    </nav>
    {{ content|safe }}
    <div class="footer">© {{ site_title }} · Заказы принимаются через Telegram</div>
  </main>
</body>
</html>
"""


def page(title: str, content: str):
    return render_template_string(
        LAYOUT,
        title=title,
        content=content,
        site_title=PUBLIC_SITE_TITLE,
        bot_url=PUBLIC_BOT_URL,
    )


def render_review_cards(reviews):
    if not reviews:
        return """
        <article class="card">
          <div class="stars">⭐</div>
          <div class="comment">Отзывы скоро появятся после первых завершённых поездок.</div>
          <div class="meta">Трансферы из Батуми</div>
        </article>
        """

    cards = ""
    for review in reviews:
        rating = int(review.get("rating") or 5)
        stars = "⭐" * max(1, min(5, rating))
        cards += f"""
        <article class="card">
          <div class="stars">{stars}</div>
          <div class="comment">{safe(review.get("comment") or "Оценка без комментария")}</div>
          <div class="meta">{safe(public_client_name(review.get("client_name")))} · {safe(review.get("route") or "маршрут")}</div>
        </article>
        """
    return cards


@app.get("/")
def index():
    reviews = fetch_reviews(limit=3)
    review_cards = render_review_cards(reviews)

    content = f"""
    <section class="hero">
      <h1>Трансферы из Батуми без нервов</h1>
      <p>Поездки по Грузии и к границе с понятной ценой, подтверждением заказа, водителем заранее и поддержкой менеджера в Telegram.</p>
      <p class="small">Батуми ↔ Тбилиси · Батуми ↔ Владикавказ · Батуми ↔ Сарпи · индивидуальные маршруты · посылки</p>

      <div class="buttons">
        <a class="button" href="{safe(PUBLIC_BOT_URL)}">Заказать трансфер</a>
        <a class="button secondary" href="#routes">Смотреть маршруты</a>
      </div>

      <div class="badges">
        <div class="badge">🚗 Водитель заранее</div>
        <div class="badge">📡 Live-трекинг</div>
        <div class="badge">🔔 Напоминания</div>
        <div class="badge">💬 Поддержка менеджера</div>
      </div>
    </section>

    <section class="section grid">
      <article class="card">
        <h3>Почему не просто водитель из чата?</h3>
        <p class="muted">Когда поездка важная, мало просто найти номер водителя. Нужно понимать, кто едет, когда машина будет на месте и что делать, если что-то изменилось.</p>
      </article>
      <article class="card">
        <h3>Заявка проходит через бота</h3>
        <p class="muted">Маршрут, дата, количество мест, комментарий, подтверждение менеджером, оплата, данные водителя и статусы поездки.</p>
      </article>
      <article class="card">
        <h3>Больше контроля</h3>
        <p class="muted">Клиент получает уведомления по рейсу, может видеть live-геолокацию и быстро связаться с менеджером.</p>
      </article>
    </section>

    <section class="section">
      <div class="section-title">
        <h2>Что получает клиент</h2>
      </div>
      <div class="grid">
        <article class="card">
          <h3>🚗 Водитель заранее</h3>
          <p class="muted">После подтверждения заказа менеджер назначает водителя и отправляет данные машины.</p>
        </article>
        <article class="card">
          <h3>📍 Статусы поездки</h3>
          <p class="muted">Водитель выехал, на месте, клиент сел, поездка в пути, рейс завершён.</p>
        </article>
        <article class="card">
          <h3>📡 Live-трекинг</h3>
          <p class="muted">Если водитель делится геолокацией, клиент видит машину на карте в реальном времени.</p>
        </article>
        <article class="card">
          <h3>🔔 Напоминания</h3>
          <p class="muted">Бот заранее напоминает о поездке, дате и времени выезда.</p>
        </article>
      </div>
    </section>

    <section class="section" id="routes">
      <div class="section-title">
        <h2>Маршруты</h2>
        <a class="button light" href="{safe(PUBLIC_BOT_URL)}">Оставить заявку</a>
      </div>

      <div class="grid">
        <article class="card">
          <h3>Батуми ↔ Владикавказ</h3>
          <p class="muted">Маршрут к границе и через Верхний Ларс. Подходит для поездок с багажом, семьёй, документами и важной датой выезда.</p>
          <div class="price">350 GEL</div>
          <p class="muted">за 1 место</p>
        </article>
        <article class="card">
          <h3>Батуми ↔ Тбилиси</h3>
          <p class="muted">Поездки между городами, трансфер в аэропорт, встреча гостей, семейные поездки.</p>
          <div class="price">250 GEL</div>
          <p class="muted">за 1 место</p>
        </article>
        <article class="card">
          <h3>Батуми ↔ Сарпи</h3>
          <p class="muted">Короткий маршрут до границы, поездки туда-обратно, передача небольших посылок.</p>
          <div class="price">35 GEL</div>
          <p class="muted">за 1 место</p>
        </article>
        <article class="card">
          <h3>Свой маршрут</h3>
          <p class="muted">Другой город, нестандартное время, много багажа, отдельная машина или посылка. Менеджер уточнит детали и рассчитает стоимость.</p>
          <div class="price">по запросу</div>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="section-title">
        <h2>Как оформить заказ</h2>
      </div>
      <div class="grid">
        <article class="card step">
          <div class="step-num">1</div>
          <div>
            <h3>Оставьте заявку в Telegram</h3>
            <p class="muted">Выберите маршрут, количество мест, дату, точку посадки и комментарий.</p>
          </div>
        </article>
        <article class="card step">
          <div class="step-num">2</div>
          <div>
            <h3>Получите подтверждение</h3>
            <p class="muted">Менеджер проверит возможность поездки, подтвердит цену и отправит ссылку на оплату.</p>
          </div>
        </article>
        <article class="card step">
          <div class="step-num">3</div>
          <div>
            <h3>Оплатите предоплату</h3>
            <p class="muted">Доступны грузинский банк, RUB через СБП, USDT TRC20 и USDT TON.</p>
          </div>
        </article>
        <article class="card step">
          <div class="step-num">4</div>
          <div>
            <h3>Получите данные водителя</h3>
            <p class="muted">Перед поездкой клиент получает информацию о водителе, машине и статусах рейса.</p>
          </div>
        </article>
      </div>
    </section>

    <section class="section" id="faq">
      <div class="section-title">
        <h2>Частые вопросы</h2>
      </div>

      <div class="faq">
        <details>
          <summary>Когда возвращается предоплата?</summary>
          <p>Предоплата возвращается, если поездка не состоялась по нашей стороне: водитель не смог приехать, машина не была найдена или заказ отменён нами. Если клиент отменяет поездку заранее, не позднее чем за 24 часа до выезда, предоплата может быть возвращена или перенесена на другую дату.</p>
        </details>
        <details>
          <summary>Что если водитель опоздал?</summary>
          <p>Менеджер сообщает клиенту причину задержки и новое время прибытия. Если задержка значительная, стараемся найти замену или согласовать другое решение.</p>
        </details>
        <details>
          <summary>Что если клиент опоздал?</summary>
          <p>Водитель бесплатно ожидает до 15 минут после согласованного времени. Если клиент сильно опаздывает или не выходит на связь, водитель может уехать, а предоплата может быть удержана.</p>
        </details>
        <details>
          <summary>Что если граница закрыта?</summary>
          <p>Мы не можем гарантировать работу границы, погоду, очереди и решения пограничных служб. Если проблема возникла до начала поездки, заказ можно перенести или отменить. Если уже в пути, решение согласуется с менеджером и водителем.</p>
        </details>
        <details>
          <summary>Что если много багажа?</summary>
          <p>Багаж нужно указать заранее при оформлении заказа. Если есть крупные сумки, коробки, коляска, животное, спортивное снаряжение или посылки, это важно написать в комментарии.</p>
        </details>
      </div>
    </section>

    <section class="section">
      <div class="section-title">
        <h2>Отзывы клиентов</h2>
        <a href="/reviews">Все отзывы</a>
      </div>
      <div class="grid">{review_cards}</div>
    </section>

    <section class="section cta">
      <h2>Заказать трансфер</h2>
      <p>Оставьте заявку в Telegram-боте. Менеджер подтвердит маршрут, цену и условия поездки.</p>
      <div class="buttons">
        <a class="button" href="{safe(PUBLIC_BOT_URL)}">Перейти в Telegram</a>
        <a class="button secondary" href="/reviews">Отзывы клиентов</a>
      </div>
    </section>
    """

    return page(PUBLIC_SITE_TITLE, content)


@app.get("/reviews")
def reviews_page():
    reviews = fetch_reviews(limit=80)
    cards = render_review_cards(reviews)

    content = f"""
    <section class="hero">
      <h1>Отзывы клиентов</h1>
      <p>Отзывы оставляют клиенты после завершённых поездок. Они помогают новым пассажирам понять, как работает сервис и чего ожидать.</p>
      <div class="buttons">
        <a class="button" href="{safe(PUBLIC_BOT_URL)}">Заказать трансфер</a>
      </div>
    </section>
    <section class="grid">{cards}</section>
    """
    return page(f"Отзывы — {PUBLIC_SITE_TITLE}", content)


@app.get("/pay")
def pay_page():
    order_id = request.args.get("order_id", "").strip()
    order = get_order(order_id)

    if not order:
        content = """
        <section class="card">
          <h1>Заказ не найден</h1>
          <p class="muted">Проверьте ссылку или вернитесь в Telegram и запросите ссылку заново.</p>
        </section>
        """
        return page("Заказ не найден", content)

    deposit_gel = order.get("deposit_gel")

    try:
        deposit_gel = float(deposit_gel)
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
    <section class="hero">
      <h1>Оплата заказа №{safe(order_id)}</h1>
      <p>🛣 Маршрут: <strong>{safe(order.get("route") or "не указан")}</strong></p>
      <p>👥 Мест: <strong>{safe(order.get("seats") or "—")}</strong></p>
      <p>📅 Дата: <strong>{safe(order.get("trip_date") or "—")}</strong></p>
      <p>После оплаты вернитесь в Telegram и нажмите «💳 Я оплатил». Менеджер проверит оплату и закрепит место.</p>
      <div class="buttons">
        <a class="button" href="{safe(PUBLIC_BOT_URL)}">Вернуться в Telegram</a>
      </div>

      <div class="summary">
        <div class="sum-card"><div class="label">Предоплата GEL</div><div class="value">{money(deposit_gel, "GEL")}</div></div>
        <div class="sum-card"><div class="label">USD</div><div class="value">{money(deposit_usd, "USD")}</div></div>
        <div class="sum-card"><div class="label">EUR</div><div class="value">{money(deposit_eur, "EUR")}</div></div>
        <div class="sum-card"><div class="label">RUB</div><div class="value">{money(deposit_rub, "RUB")}</div></div>
      </div>
    </section>

    <section class="grid">
      <article class="card">
        <h2>🇬🇪 GEL / USD / EUR</h2>
        <p class="muted">Оплата на грузинский банк. Сейчас блок подготовлен под Credo Bank.</p>
        <div class="line"><strong>Банк:</strong> {payment_detail(PAYMENT_BANK_NAME, "Credo Bank")}</div>
        <div class="line"><strong>Получатель:</strong> {payment_detail(PAYMENT_BANK_RECEIVER, "будет указан менеджером")}</div>
        <div class="line"><strong>IBAN GEL:</strong><div class="mono">{payment_detail(PAYMENT_BANK_GEL_IBAN, "будет добавлен после открытия счёта")}</div></div>
        <div class="line"><strong>IBAN USD:</strong><div class="mono">{payment_detail(PAYMENT_BANK_USD_IBAN, "будет добавлен после открытия счёта")}</div></div>
        <div class="line"><strong>IBAN EUR:</strong><div class="mono">{payment_detail(PAYMENT_BANK_EUR_IBAN, "будет добавлен после открытия счёта")}</div></div>
        <div class="line"><strong>Назначение:</strong><div class="mono">Order {safe(order_id)}</div></div>
        <div class="warn">Если реквизиты ещё не указаны, запросите их у менеджера в Telegram.</div>
      </article>

      <article class="card">
        <h2>🇷🇺 RUB через СБП</h2>
        <div class="line"><strong>Сумма:</strong> {money(deposit_rub, "RUB")}</div>
        <div class="line"><strong>Получатель:</strong> {payment_detail(PAYMENT_RUB_RECEIVER)}</div>
        <div class="line"><strong>Банк:</strong> {payment_detail(PAYMENT_RUB_BANK)}</div>
        <div class="line"><strong>Телефон СБП:</strong><div class="mono">{payment_detail(PAYMENT_RUB_PHONE)}</div></div>
        <div class="line"><strong>Комментарий:</strong><div class="mono">Order {safe(order_id)}</div></div>
        <div class="warn">Обязательно укажите номер заказа в комментарии, иначе оплату придётся искать вручную.</div>
      </article>

      <article class="card">
        <h2>₿ Telegram / Crypto</h2>
        <div class="line"><strong>Связь по оплате:</strong><div class="mono">{payment_detail(tg_wallet)}</div></div>
        <div class="line"><strong>USDT TRC20:</strong><div class="mono">{payment_detail(PAYMENT_CRYPTO_USDT_TRC20)}</div></div>
        <div class="line"><strong>USDT TON:</strong><div class="mono">{payment_detail(PAYMENT_CRYPTO_USDT_TON)}</div></div>
        <div class="line"><strong>Комментарий / memo:</strong><div class="mono">Order {safe(order_id)}</div></div>
        <div class="warn">Внимательно выбирайте сеть. USDT TRC20 отправлять только в TRON/TRC20. USDT TON отправлять только в TON. При ошибке сети платёж может быть потерян.</div>
      </article>
    </section>
    """

    return page(f"Оплата заказа №{order_id}", content)


@app.get("/health")
def health():
    return "OK"


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
