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

    if not sender_email or not sender_password:
        print("ℹ️ Налаштування SENDER_EMAIL/SENDER_PASSWORD відсутні. Пропускаємо відправку поштою.", flush=True)
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                msg.attach(part)

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"📧 Лист із резюме успішно відправлено на {target_email}!", flush=True)
        return True
    except Exception as e:
        print(f"⚠️ Помилка відправки Email на {target_email}: {e}", flush=True)
        return False

def send_telegram_notification(bot_token, chat_id, title, company, location, url, score, reason, cover_letter, site_source="", email_sent=False):
    safe_title = html.escape(str(title if title else "Без назви"))
    safe_company = html.escape(str(company if company else "Не вказано"))
    safe_location = html.escape(str(location if location else "Spain"))
    safe_reason = html.escape(str(reason if reason else ""))
    safe_cover_letter = html.escape(str(cover_letter if cover_letter else ""))
    safe_site = html.escape(str(site_source if site_source else "Веб-сайт"))

    clean_url = str(url).strip() if url else ""
    if clean_url.startswith("http://") or clean_url.startswith("https://"):
        link_html = f"🔗 <a href=\"{clean_url}\">Переглянути вакансію та відгукнутися</a>"
    else:
        link_html = "🔗 Посилання відсутнє"

    status_tag = "📩 <b>АВТО-ВІДГУК НАДІСЛАНО НА EMAIL HR!</b>\n\n" if email_sent else ""

    text = (
        f"{status_tag}"
        f"🎯 <b>Нова вакансія ({score}% відповідності)</b>\n\n"
        f"<b>Посада:</b> {safe_title}\n"
        f"<b>Компанія:</b> {safe_company}\n"
        f"<b>Локація:</b> {safe_location}\n"
        f"<b>Джерело:</b> {safe_site}\n\n"
        f"💡 <b>Аналіз штучного інтелекту:</b>\n{safe_reason}\n\n"
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
        res = requests.post(api_url, json=
