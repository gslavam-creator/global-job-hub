import streamlit as st
import sqlite3
import os
import subprocess
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB_FILE = "database.db"

def init_db():
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
    if not email:
        return None
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, experience, languages, work_permit, job_titles, locations, matching_threshold, telegram_token, telegram_chat_id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0], "experience": row[1], "languages": row[2],
            "work_permit": row[3], "job_titles": row[4], "locations": row[5],
            "matching_threshold": row[6], "telegram_token": row[7], "telegram_chat_id": row[8]
        }
    return None

def save_user_data(email, data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (email, name, experience, languages, work_permit, job_titles, locations, matching_threshold, telegram_token, telegram_chat_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        email, data["name"], data["experience"], data["languages"], data["work_permit"],
        data["job_titles"], data["locations"], data["matching_threshold"],
        data["telegram_token"], data["telegram_chat_id"]
    ))
    conn.commit()
    conn.close()

def generate_pdf_cv(profile, pdf_filename):
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, spaceAfter=15, textColor="#0f172a")
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6, textColor="#1e293b")
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=11, spaceAfter=8, leading=14)

    story.append(Paragraph(profile.get("name", "Candidate CV"), title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Дозвіл на роботу / Віза:</b> " + profile.get("work_permit", ""), body_style))
    story.append(Paragraph("<b>Мови:</b> " + profile.get("languages", ""), body_style))
    story.append(Paragraph("Професійний досвід та навички", heading_style))
    story.append(Paragraph(profile.get("experience", "").replace("\n", "<br/>"), body_style))
    
    doc.build(story)

init_db()

# Конфігурація сторінки
st.set_page_config(
    page_title="Global Job Hub | SaaS",
    page_icon="🌍",
    layout="wide"
)

# Шапка додатка
st.title("🌍 Global Job Hub")
st.caption("Автономна платформа глобального пошуку вакансій, генерації резюме та розумних сповіщень.")

# Авторизація у сайдбарі
with st.sidebar:
    st.markdown("### 🔑 Ідентифікація")
    user_email = st.text_input("Ваш Email", placeholder="candidate@example.com", help="Ключ до вашого профілю у системі.")
    st.divider()
    st.markdown("### ℹ️ Про систему")
    st.info("Цей сервіс автоматично сканує світовий ринок праці за вашими критеріями та надсилає персональні звіти.")

if not user_email or "@" not in user_email:
    st.warning("👋 Будь ласка, введіть свій **Email** у бічній панелі ліворуч, щоб розпочати.")
else:
    user_data = get_user_data(user_email)
    
    default_name = user_data["name"] if user_data else ""
    default_exp = user_data["experience"] if user_data else ""
    default_lang = user_data["languages"] if user_data else ""
    default_permit = user_data["work_permit"] if user_data else "Work Authorization / Visa Status"
    default_titles = user_data["job_titles"] if user_data else "Software Engineer, Telecom Specialist, Remote"
    default_locs = user_data["locations"] if user_data else "Remote, Europe, USA"
    default_threshold = user_data["matching_threshold"] if user_data else 70
    default_tg_token = user_data["telegram_token"] if user_data else ""
    default_tg_chat = user_data["telegram_chat_id"] if user_data else ""

    # Сучасні вкладки
    tab1, tab2, tab3 = st.tabs(["👤 Профіль та Пошук", "🤖 Telegram-сповіщення", "⚡ Керування та CV"])

    with tab1:
        st.markdown("#### Налаштування профілю кандидата")
        with st.form("profile_form"):
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                candidate_name = st.text_input("Повне ім'я", value=default_name)
                work_permit = st.text_input("Дозвіл на роботу / Віза", value=default_permit)
                languages = st.text_input("Мови", value=default_lang, placeholder="English (Fluent), Spanish (B2)")
                
            with col2:
                job_titles_input = st.text_area("Бажані посади (через кому)", value=default_titles, height=80)
                locations_input = st.text_input("Регіони / Міста / Remote", value=default_locs)
                matching_threshold = st.slider("Поріг релевантності ШІ (%)", min_value=50, max_value=95, value=default_threshold)
            
            experience = st.text_area("Детальний досвід роботи та навички", value=default_exp, height=120)
            
            submitted = st.form_submit_button("💾 Зберегти профіль та оновити CV", use_container_width=True)

    with tab2:
        st.markdown("#### Налаштування Telegram-бота")
        st.markdown("Введіть дані вашого бота для отримання миттєвих сповіщень про нові вакансії.")
        
        with st.form("telegram_form"):
            telegram_token = st.text_input("Telegram Bot Token", type="password", value=default_tg_token)
            telegram_chat_id = st.text_input("Telegram Chat ID", value=default_tg_chat)
            
            tg_submitted = st.form_submit_button("💾 Зберегти налаштування Telegram", use_container_width=True)

    with tab3:
        st.markdown("#### Робота з документами та запуск агента")
        
        col_cv, col_agent = st.columns(2, gap="large")
        
        with col_cv:
            st.markdown("##### 📄 Ваше персональне CV")
            target_pdf = f"CV_{user_email.replace('@', '_at_').replace('.', '_')}.pdf"
            
            if os.path.exists(target_pdf):
                with open(target_pdf, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Завантажити CV.pdf",
                        data=pdf_file,
                        file_name="CV.pdf",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
            else:
                st.info("Спочатку збережіть профіль на першій вкладці, щоб згенерувати документ.")

        with col_agent:
            st.markdown("##### 🚀 Запуск глобального сканування")
            if st.button("⚡ Запустити пошук вакансій зараз", use_container_width=True):
                with st.spinner("Агент сканує глобальний ринок праці..."):
                    try:
                        result = subprocess.run(["python", "main.py"], capture_output=True, text=True, timeout=120)
                        if result.returncode == 0:
                            st.success("✅ Сканування завершено успішно!")
                            if result.stdout:
                                with st.expander("Лог виконання"):
                                    st.text(result.stdout[-600:])
                        else:
                            st.error(f"⚠️ Помилка: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Не вдалося запустити: {e}")

    # Обробка збереження
    if submitted or ('tg_submitted' in locals() and tg_submitted):
        current_data = get_user_data(user_email) or {}
        
        profile_data = {
            "name": candidate_name if 'candidate_name' in locals() else current_data.get("name", ""),
            "experience": experience if 'experience' in locals() else current_data.get("experience", ""),
            "languages": languages if 'languages' in locals() else current_data.get("languages", ""),
            "work_permit": work_permit if 'work_permit' in locals() else current_data.get("work_permit", ""),
            "job_titles": job_titles_input if 'job_titles_input' in locals() else current_data.get("job_titles", ""),
            "locations": locations_input if 'locations_input' in locals() else current_data.get("locations", ""),
            "matching_threshold": matching_threshold if 'matching_threshold' in locals() else current_data.get("matching_threshold", 70),
            "telegram_token": telegram_token if 'telegram_token' in locals() else current_data.get("telegram_token", ""),
            "telegram_chat_id": telegram_chat_id if 'telegram_chat_id' in locals() else current_data.get("telegram_chat_id", "")
        }

        save_user_data(user_email, profile_data)
        pdf_filename = f"CV_{user_email.replace('@', '_at_').replace('.', '_')}.pdf"
        generate_pdf_cv(profile_data, pdf_filename)
        
        st.success("✨ Зміни успішно збережено в базі даних та резюме оновлено!")
