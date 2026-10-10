import os
import re
import json
import html
import sqlite3
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import pandas as pd
from jobspy import scrape_jobs
from openai import OpenAI

CONFIG_FILE = "config.json"
DB_FILE = "jobs.db"
CV_FILE = "CV.pdf"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Файл {CONFIG_FILE} не знайдено!")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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

def send_email_application(target_email, subject, body_text, pdf_path):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    backup_email = os.getenv("BACKUP_EMAIL")

    if not sender_email or not sender_password:
        print("ℹ️ Налаштування SENDER_EMAIL/SENDER_PASSWORD відсутні. Пропускаємо відправку поштою.", flush=True)
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = subject

        recipients = [target_email]
        if backup_email:
            msg['Bcc'] = backup_email
            recipients.append(backup_email)

        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                msg.attach(part)

        with smtplib.SMTP('smtp.mail.me.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())

        print(f"📧 Лист із резюме успішно відправлено на {target_email} (BCC: {backup_email})!", flush=True)
        return True
    except Exception as e:
        print(f"⚠️ Помилка відправки Email на {target_email}: {e}", flush=True)
        return False

def send_telegram_message(bot_token, chat_id, text):
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

    Поверніть відповідь строго у формі JSON із 4 полями:
    {{
        "score": ціле число від 0 до 100 (ступінь відповідності),
        "reason": "1-2 речення українською мовою з поясненням чому вакансія підходить або ні",
        "cover_letter": "Професійний супровідний лист (Carta de presentación) іспанською мовою (3-4 речення), який кандидат може використати для відгуку",
        "hr_email": "знайдена електронна пошта HR або компанії з опису вакансії, або null якщо пошти немає"
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
        return int(data.get("score", 0)), str(data.get("reason", "")), str(data.get("cover_letter", "")), data.get("hr_email")
    except Exception as e:
        print(f"⚠️ Помилка OpenAI API: {e}", flush=True)
        return 0, "Помилка аналізу через OpenAI", "", None

def main():
    print("🚀 Запуск агента моніторингу вакансій в Іспанії...", flush=True)

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

    target_sites = ["linkedin", "indeed", "glassdoor", "zip_recruiter", "google"]

    locations = search_params.get("locations", [search_params.get("location", "Spain")])
    job_titles = search_params["job_titles"]

    all_jobs = []
    for location in locations:
        for title in job_titles:
            print(f"🔎 Шукаємо: '{title}' у місті '{location}'...", flush=True)
            try:
                jobs = scrape_jobs(
                    site_name=target_sites,
                    search_term=title,
                    location=location,
                    results_wanted=search_params.get("results_wanted", 10),
                    country_indeed='spain'
                )
                if jobs is not None and not jobs.empty:
                    all_jobs.append(jobs)
            except Exception as e:
                print(f"⚠️ Помилка скрапінгу для '{title}' у '{location}': {e}", flush=True)

    if not all_jobs:
        print("ℹ️ Вакансій на сайтах не знайдено взагалі.", flush=True)
        send_telegram_message(
            telegram_token, telegram_chat_id,
            "📊 <b>Щоденний звіт агента</b>\n\n"
            "ℹ️ За останню добу нових вакансій за вашими критеріями на порталах не виявлено.\n"
            "<i>Агент продовжує моніторинг і перевірить знову завтра о 11:00.</i>"
        )
        return

    combined_jobs = pd.concat(all_jobs, ignore_index=True).drop_duplicates(subset=['id'])
    total_scanned = len(combined_jobs)
    print(f"\n📊 Всього зібрано унікальних вакансій у скануванні: {total_scanned}\n", flush=True)

    new_matched_count = 0
    emails_sent_count = 0

    for idx, row in combined_jobs.iterrows():
        job_id = str(row.get('id', ''))
        title = str(row.get('title', 'Без назви'))
        company = str(row.get('company', 'Не вказано'))
        location = str(row.get('location', 'Spain'))
        job_url = str(row.get('job_url', ''))
        description = str(row.get('description', 'Немає опису'))
        site_source = str(row.get('site', 'Веб-сайт'))

        if not job_id:
            continue

        # Перевірка чи вакансія вже була оброблена раніше
        if is_job_seen(job_id):
            continue

        # Позначаємо вакансію як опрацьовану в базі даних
        mark_job_seen(job_id)

        # Аналіз через OpenAI
        score, reason, cover_letter, hr_email = evaluate_job(
            client, title, company, description, config["candidate_profile"]
        )

        print(f"🔍 [Нова] [{score}%] [{site_source}] {title} в '{company}' -> {reason}", flush=True)

        if score >= threshold:
            new_matched_count += 1
            email_sent = False
            
            if hr_email and str(hr_email).strip() and "@" in str(hr_email):
                subject = f"Candidatura: {title} - {config['candidate_profile'].get('name', 'Candidato')}"
                email_sent = send_email_application(hr_email, subject, cover_letter, CV_FILE)
                if email_sent:
                    emails_sent_count += 1

            # Формування повідомлення для Telegram
            safe_title = html.escape(title)
            safe_company = html.escape(company)
            safe_location = html.escape(location)
            safe_reason = html.escape(reason)
            safe_cover_letter = html.escape(cover_letter)
            safe_site = html.escape(site_source)

            clean_url = str(url).strip() if url else ""
            if job_url.startswith("http://") or job_url.startswith("https://"):
                link_html = f"🔗 <a href=\"{job_url}\">Переглянути вакансію та відгукнутися самостійно</a>"
            else:
                link_html = "🔗 Посилання відсутнє"

            if email_sent and hr_email:
                status_tag = f"📩 <b>АВТО-ВІДГУК НАДІСЛАНО НА ПОШТУ:</b> <code>{hr_email}</code>\n\n"
            else:
                status_tag = "⚠️ <b>Прямий мейл відсутній.</b> Відгукуйтеся за посиланням нижче:\n\n"

            text = (
                f"{status_tag}"
                f"🎯 <b>Нова вакансія ({score}% відповідності)</b>\n\n"
                f"<b>Посада:</b> {safe_title}\n"
                f"<b>Компанія:</b> {safe_company}\n"
                f"<b>Локація:</b> {safe_location}\n"
                f"<b>Джерело:</b> {safe_site}\n\n"
                f"💡 <b>Аналіз ШІ:</b>\n{safe_reason}\n\n"
                f"✉️ <b>Carta de presentación:</b>\n<i>{safe_cover_letter}</i>\n\n"
                f"{link_html}"
            )
            send_telegram_message(telegram_token, telegram_chat_id, text)

    # Підсумковий щоденний звіт (надсилається завжди після завершення циклу)
    summary_text = (
        f"📊 <b>Щоденний звіт агента з працевлаштування</b>\n\n"
        f"🔍 Проскановано унікальних вакансій: <b>{total_scanned}</b>\n"
        f"✨ Нових підходящих вакансій (≥ {threshold}%): <b>{new_matched_count}</b>\n"
        f"📩 Автоматично надіслано резюме на пошту: <b>{emails_sent_count}</b>\n\n"
        f"<i>Агент виконав планову перевірку. Наступний запуск — завтра о 11:00.</i>"
    )
    send_telegram_message(telegram_token, telegram_chat_id, summary_text)

    print(f"\n✅ Запуск завершено. Нових підходящих вакансій опрацьовано: {new_matched_count}", flush=True)

if __name__ == "__main__":
    main()
