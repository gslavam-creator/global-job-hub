import os
import json
import html
import sqlite3
import requests
import pandas as pd
from jobspy import scrape_jobs
from openai import OpenAI

CONFIG_FILE = "config.json"
DB_FILE = "jobs.db"

# 1. Завантаження конфігурації
def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Файл {CONFIG_FILE} не знайдено!")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 2. Робота з базою даних (Захист від дублікатів)
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            id TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def is_job_seen(job_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM seen_jobs WHERE id = ?", (str(job_id),))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def mark_job_seen(job_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO seen_jobs (id) VALUES (?)", (str(job_id),))
    conn.commit()
    conn.close()

# 3. Безпечна відправка сповіщень у Telegram
def send_telegram_notification(bot_token, chat_id, title, company, location, url, score, reason, cover_letter):
    # Екрануємо спеціальні символи HTML (<, >, &, ")
    safe_title = html.escape(str(title if title else "Без назви"))
    safe_company = html.escape(str(company if company else "Не вказано"))
    safe_location = html.escape(str(location if location else "Spain"))
    safe_reason = html.escape(str(reason if reason else ""))
    safe_cover_letter = html.escape(str(cover_letter if cover_letter else ""))

    clean_url = str(url).strip() if url else ""
    if clean_url.startswith("http://") or clean_url.startswith("https://"):
        link_html = f"🔗 <a href=\"{clean_url}\">Переглянути та відгукнутися</a>"
    else:
        link_html = "🔗 Посилання відсутнє"

    text = (
        f"🎯 <b>Нова вакансія ({score}% відповідності)</b>\n\n"
        f"<b>Посада:</b> {safe_title}\n"
        f"<b>Компанія:</b> {safe_company}\n"
        f"<b>Локація:</b> {safe_location}\n\n"
        f"💡 <b>Оцінка штучного інтелекту:</b>\n{safe_reason}\n\n"
        f"✉️ <b>Carta de presentación:</b>\n<i>{safe_cover_letter}</i>\n\n"
        f"{link_html}"
    )

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        res = requests.post(api_url, json=payload, timeout=10)
        if not res.ok:
            print(f"⚠️ Помилка Telegram ({res.status_code}): {res.text}", flush=True)
    except Exception as e:
        print(f"⚠️ Помилка відправки в Telegram: {e}", flush=True)

# 4. Оцінка вакансії через OpenAI
def evaluate_job(client, job_title, company, description, candidate_profile):
    prompt = f"""
    Ви — професійний IT/Telecom рекрутер в Іспанії.
    Проаналізуйте вакансію та порівняйте її з профілем кандидата.

    Профіль кандидата:
    - Досвід: {candidate_profile.get('experience')}
    - Мови: {candidate_profile.get('languages')}
    - Дозвіл на роботу: {candidate_profile.get('work_permit')}

    Вакансія:
    - Посада: {job_title}
    - Компанія: {company}
    - Опис: {str(description)[:2500]}

    Поверніть відповідь строго у формі JSON із 3 полями:
    {{
        "score": ціле число від 0 до 100 (ступінь відповідності),
        "reason": "1-2 речення українською мовою з поясненням чому вакансія підходить або ні",
        "cover_letter": "Професійний супровідний лист (Carta de presentación) іспанською мовою (3-4 речення), який кандидат може використати для відгуку"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ти помічник з оцінки вакансій. Відповідай строго у JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        data = json.loads(response.choices[0].message.content)
        return int(data.get("score", 0)), str(data.get("reason", "")), str(data.get("cover_letter", ""))
    except Exception as e:
        print(f"⚠️ Помилка OpenAI API: {e}", flush=True)
        return 0, "Помилка аналізу через OpenAI", ""

# 5. Головний алгоритм
def main():
    print("🚀 Запуск моніторингу вакансій в Іспанії...", flush=True)

    openai_key = os.getenv("OPENAI_API_KEY")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not all([openai_key, telegram_token, telegram_chat_id]):
        print("❌ Помилка: Не всі секретні ключі додані в GitHub Secrets!", flush=True)
        return

    config = load_config()
    init_db()

    client = OpenAI(api_key=openai_key)
    search_params = config["search_parameters"]
    threshold = config.get("matching_threshold", 70)

    # Збір вакансій
    all_jobs = []
    for title in search_params["job_titles"]:
        print(f"🔎 Шукаємо: '{title}'...", flush=True)
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed"],
                search_term=title,
                location=search_params["location"],
                results_wanted=search_params.get("results_wanted", 10),
                country_indeed='spain'
            )
            if jobs is not None and not jobs.empty:
                all_jobs.append(jobs)
        except Exception as e:
            print(f"⚠️ Помилка скрапінгу для '{title}': {e}", flush=True)

    if not all_jobs:
        print("ℹ️ Вакансій на сайтах не знайдено.", flush=True)
        return

    combined_jobs = pd.concat(all_jobs, ignore_index=True).drop_duplicates(subset=['id'])
    print(f"\n📊 Всього знайдено унікальних вакансій: {len(combined_jobs)}\n", flush=True)

    matched_count = 0
    for idx, row in combined_jobs.iterrows():
        job_id = str(row.get('id', ''))
        title = str(row.get('title', 'Без назви'))
        company = str(row.get('company', 'Не вказано'))
        location = str(row.get('location', 'Spain'))
        job_url = str(row.get('job_url', ''))
        description = str(row.get('description', 'Немає опису'))

        if not job_id or is_job_seen(job_id):
            continue

        mark_job_seen(job_id)

        # Оцінка через AI
        score, reason, cover_letter = evaluate_job(
            client, title, company, description, config["candidate_profile"]
        )

        print(f"🔍 [{score}%] {title} в '{company}' -> {reason}", flush=True)

        if score >= threshold:
            print(f"   👉 Відповідність >= {threshold}%! Надсилаємо в Telegram...", flush=True)
            send_telegram_notification(
                telegram_token, telegram_chat_id,
                title, company, location, job_url,
                score, reason, cover_letter
            )
            matched_count += 1

    print(f"\n✅ Запуск завершено. Нових підхожих вакансій у Telegram: {matched_count}", flush=True)

if __name__ == "__main__":
    main()
