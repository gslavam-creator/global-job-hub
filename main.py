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
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, spaceAfter=15, textColor="#1a365d")
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6, textColor="#1a365d")
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=11, spaceAfter=8, leading=14)

    story.append(Paragraph(profile.get("name", "Candidate CV"), title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Дозвіл на роботу:</b> " + profile.get("work_permit", ""), body_style))
    story.append(Paragraph("<b>Мови:</b> " + profile.get("languages", ""), body_style))
    story.append(Paragraph("Професійний досвід та навички", heading_style))
    story.append(Paragraph(profile.get("experience", "").replace("\n", "<br/>"), body_style))
    
    doc.build(story)

# Ініціалізація БД
init_db()

# Налаштування сторінки
st.set_page_config(
    page_title="Spain Job Agent | SaaS Portal",
    page_icon="💼",
    layout="wide"
)

# Стильний кастомний CSS для покращення вигляду кнопок та карток
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        color: #1e3a8a;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-text {
        color: #4b5563;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }
    .stButton button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Головний заголовок
st.markdown('<p class="main-header">💼 Spain Job Agent SaaS</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Автоматизована платформа пошуку вакансій та генерації супровідних документів в Іспанії.</p>', unsafe_allow_html=True)

# Бічна панель (Sidebar) для ідентифікації та налаштувань Telegram
with st.sidebar:
    st.header("🔑 Авторизація")
    user_email = st.text_input("Введіть ваш Email", placeholder="candidate@example.com", help="Використовується як унікальний ID вашого профілю.")
    
    st.divider()
    st.header("🤖 Telegram Bot")
    st.markdown("Налаштуйте сповіщення, щоб отримувати знайдені вакансії прямо в месенджер.")
    
    # Підтягуємо існуючі дані для сайдбару, якщо email є
    user_data = get_user_data(user_email) if user_email else None
    
    default_tg_token = user_data["telegram_token"] if user_data else ""
    default_tg_chat = user_data["telegram_chat_id"] if user_data else ""
    
    telegram_token = st.text_input("Bot Token", type="password", value=default_tg_token)
    telegram_chat_id = st.text_input("Chat ID", value=default_tg_chat)

    st.info("💡 Підказка: після збереження профілю ви зможете керувати агентом нижче.")

# Основна робоча зона (розбита на колонки для естетики)
if not user_email or "@" not in user_email:
    st.warning("⚠️ Будь ласка, введіть ваш дійсний **Email** у бічній панелі ліворуч, щоб завантажити або створити профіль.")
else:
    # Завантажуємо решту даних користувача
    default_name = user_data["name"] if user_data else ""
    default_exp = user_data["experience"] if user_data else ""
    default_lang = user_data["languages"] if user_data else ""
    default_permit = user_data["work_permit"] if user_data else "Permiso de trabajo en España"
    default_titles = user_data["job_titles"] if user_data else "Instalador FTTH, Técnico de telecomunicaciones"
    default_locs = user_data["locations"] if user_data else "Spain, Alicante, Murcia"
    default_threshold = user_data["matching_threshold"] if user_data else 70

    with st.form("onboarding_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Профіль кандидата")
            candidate_name = st.text_input("Повне ім'я", value=default_name, placeholder="Іван Петренко")
            work_permit = st.text_input("Дозвіл на роботу", value=default_permit)
            languages = st.text_input("Мови", value=default_lang, placeholder="Español (B2), Inglés (Intermedio)")
            experience = st.text_area("Досвід роботи та навички", value=default_exp, height=150, placeholder="Опишіть ваш досвід у телекомунікаціях, володіння інструментами тощо...")

        with col2:
            st.subheader("🎯 Параметри пошуку")
            job_titles_input = st.text_area("Бажані посади (через кому)", value=default_titles, height=80)
            locations_input = st.text_input("Регіони / Міста", value=default_locs, placeholder="Alicante, Valencia, Madrid")
            matching_threshold = st.slider("Мінімальний поріг релевантності ШІ (%)", min_value=50, max_value=95, value=default_threshold)
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("💾 Зберегти профіль та оновити CV", use_container_width=True)

    if submitted:
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

        save_user_data(user_email, profile_data)
        
        safe_email_name = user_email.replace("@", "_at_").replace(".", "_")
        pdf_filename = f"CV_{safe_email_name}.pdf"
        generate_pdf_cv(profile_data, pdf_filename)
        
        st.success(f"✨ Успішно! Профіль та персональне резюме для **{user_email}** оновлено.")
        st.session_state["last_pdf"] = pdf_filename

    # Секція дій (Скачування CV та запуск агента)
    st.divider()
    st.subheader("🚀 Керування та результати")
    
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        # Логіка кнопок скачування
        target_pdf = st.session_state.get("last_pdf")
        if not target_pdf:
            safe_email_name = user_email.replace("@", "_at_").replace(".", "_")
            potential_pdf = f"CV_{safe_email_name}.pdf"
            if os.path.exists(potential_pdf):
                target_pdf = potential_pdf

        if target_pdf and os.path.exists(target_pdf):
            with open(target_pdf, "rb") as pdf_file:
                st.download_button(
                    label="📄 Завантажити моє CV.pdf",
                    data=pdf_file,
                    file_name="CV.pdf",
                    mime="application/octet-stream",
                    use_container_width=True
                )
        else:
            st.info("ℹ️ Збережіть профіль вище, щоб згенерувати своє перше резюме.")

    with action_col2:
        if st.button("⚡ Запустити сканування ринку", use_container_width=True):
            with st.spinner("Агент сканує ринок та готує звіт..."):
                try:
                    result = subprocess.run(["python", "main.py"], capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        st.success("✅ Сканування завершено! Звіт надіслано в Telegram.")
                        if result.stdout:
                            with st.expander("Переглянути лог виконання"):
                                st.text(result.stdout[-600:])
                    else:
                        st.error(f"⚠️ Помилка виконання: {result.stderr}")
                except Exception as e:
                    st.error(f>хтакий стан: Не вдалося запустити агент: {e}")

<FollowUp label="Хочете, щоб ми додали вкладки (Tabs) для розділення налаштувань профілю та історії знайдених вакансій?" query="Як додати вкладки у Streamlit для розділення налаштувань профілю та історії результатів пошуку?"/>
