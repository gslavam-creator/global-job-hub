import streamlit as st
import sqlite3
import os
import subprocess
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB_FILE = "database.db"

def init_db():
    """Ініціалізація бази даних та створення таблиці користувачів"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            experience TEXT,
            languages TEXT,
            work_permit TEXT,
            job_titles TEXT,
            locations TEXT,
            matching_threshold INTEGER,
            telegram_token TEXT,
            telegram_chat_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user_data(email):
    """Отримання даних користувача за його email"""
    if not email:
        return None
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, experience, languages, work_permit, job_titles, locations, matching_threshold, telegram_token, telegram_chat_id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0],
            "experience": row[1],
            "languages": row[2],
            "work_permit": row[3],
            "job_titles": row[4],
            "locations": row[5],
            "matching_threshold": row[6],
            "telegram_token": row[7],
            "telegram_chat_id": row[8]
        }
    return None

def save_user_data(email, data):
    """Збереження або оновлення даних користувача в базі"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (email, name, experience, languages, work_permit, job_titles, locations, matching_threshold, telegram_token, telegram_chat_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        email,
        data["name"],
        data["experience"],
        data["languages"],
        data["work_permit"],
        data["job_titles"],
        data["locations"],
        data["matching_threshold"],
        data["telegram_token"],
        data["telegram_chat_id"]
    ))
    conn.commit()
    conn.close()

def generate_pdf_cv(profile, pdf_filename):
    """Генерує персональний PDF-файл резюме для конкретного користувача"""
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=15,
        textColor="#1a365d"
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=6,
        textColor="#1a365d"
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leading=14
    )

    story.append(Paragraph(profile.get("name", "Candidate CV"), title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Дозвіл на роботу:</b> " + profile.get("work_permit", ""), body_style))
    story.append(Paragraph("<b>Мови:</b> " + profile.get("languages", ""), body_style))
    story.append(Paragraph("Професійний досвід та навички", heading_style))
    story.append(Paragraph(profile.get("experience", "").replace("\n", "<br/>"), body_style))
    
    doc.build(story)

# Ініціалізуємо БД при запускi
init_db()

st.set_page_config(
    page_title="Spain Job Agent - SaaS Onboarding",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 AI Job Search Agent (Spain)")
st.subheader("Мультикористувацький портал налаштування агента")

# Поле для ідентифікації користувача за Email
user_email = st.text_input("Введіть ваш Email (для збереження та завантаження профілю)", value="")

# Завантажуємо дані існуючого користувача з бази, якщо email введено
user_data = get_user_data(user_email) if user_email else None

default_name = user_data["name"] if user_data else ""
default_exp = user_data["experience"] if user_data else ""
default_lang = user_data["languages"] if user_data else ""
default_permit = user_data["work_permit"] if user_data else "Permiso de trabajo en España"
default_titles = user_data["job_titles"] if user_data else "Instalador FTTH, Técnico de telecomunicaciones"
default_locs = user_data["locations"] if user_data else "Spain, Alicante, Murcia"
default_threshold = user_data["matching_threshold"] if user_data else 70
default_tg_token = user_data["telegram_token"] if user_data else ""
default_tg_chat = user_data["telegram_chat_id"] if user_data else ""

with st.form("onboarding_form"):
    st.header("1. Профіль кандидата")
    candidate_name = st.text_input("Ваше повне ім'я", value=default_name)
    experience = st.text_area("Досвід роботи (навички, стаж, спеціалізація)", value=default_exp)
    languages = st.text_input("Мови (наприклад: Español (B2), Inglés (Intermedio))", value=default_lang)
    work_permit = st.text_input("Дозвіл на роботу в Іспанії", value=default_permit)

    st.header("2. Параметри пошуку")
    job_titles_input = st.text_area("Посади (через кому)", value=default_titles)
    locations_input = st.text_input("Регіони / Міста (через кому)", value=default_locs)
    
    matching_threshold = st.slider("Поріг відповідності ШІ (%)", min_value=50, max_value=95, value=default_threshold)

    st.header("3. Telegram (для сповіщень)")
    telegram_token = st.text_input("Telegram Bot Token", type="password", value=default_tg_token)
    telegram_chat_id = st.text_input("Telegram Chat ID", value=default_tg_chat)

    submitted = st.form_submit_button("💾 Зберегти профіль у базі даних")

if submitted:
    if not user_email or "@" not in user_email:
        st.warning("⚠️ Будь ласка, введіть коректний Email на початку сторінки перед збереженням!")
    else:
        profile_data = {
            "name": candidate_name,
            "experience": experience,
            "languages": languages,
            "work_permit": work_permit,
            "job_titles": job_titles_input,
            "locations": locations_input,
            "matching_threshold": matching_threshold,
            "telegram_token": telegram_token,
            "telegram_chat_id": telegram_chat_id
        }

        # Зберігаємо у SQLite
        save_user_data(user_email, profile_data)
        
        # Генеруємо персональний PDF для цього користувача
        safe_email_name = user_email.replace("@", "_at_").replace(".", "_")
        pdf_filename = f"CV_{safe_email_name}.pdf"
        generate_pdf_cv(profile_data, pdf_filename)
        
        st.success(f"✅ Профіль для {user_email} успішно збережено в базі даних!")
        st.balloons()

        # Зберігаємо назву файлу у сесії, щоб кнопка скачування була доступна одразу
        st.session_state["last_pdf"] = pdf_filename

# Кнопка завантаження персонального CV
target_pdf = st.session_state.get("last_pdf")
if not target_pdf and user_email:
    safe_email_name = user_email.replace("@", "_at_").replace(".", "_")
    potential_pdf = f"CV_{safe_email_name}.pdf"
    if os.path.exists(potential_pdf):
        target_pdf = potential_pdf

if target_pdf and os.path.exists(target_pdf):
    st.divider()
    with open(target_pdf, "rb") as pdf_file:
        st.download_button(
            label="📄 Завантажити моє персональне CV.pdf",
            data=pdf_file,
            file_name="CV.pdf",
            mime="application/octet-stream"
        )

# Секція ручного запуску агента
st.divider()
st.subheader("⚡ Керування агентом")
if st.button("🚀 Запустити сканування вакансій"):
    with st.spinner("Агент виконує пошук та аналіз..."):
        try:
            result = subprocess.run(["python", "main.py"], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                st.success("✅ Сканування завершено!")
                if result.stdout:
                    st.text(result.stdout[-500:])
            else:
                st.error(f"⚠️ Помилка виконання: {result.stderr}")
        except Exception as e:
            st.error(f"❌ Не вдалося запустити агент: {e}")
