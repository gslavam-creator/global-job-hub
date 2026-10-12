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
    story.append(Paragraph("<b>Дозвіл на роботу:</b> " + profile.get("work_permit", ""), body_style))
    story.append(Paragraph("<b>Мови:</b> " + profile.get("languages", ""), body_style))
    story.append(Paragraph("Професійний досвід та навички", heading_style))
    story.append(Paragraph(profile.get("experience", "").replace("\n", "<br/>"), body_style))
    
    doc.build(story)

init_db()

# Налаштування сторінки
st.set_page_config(
    page_title="Spain Job Agent | SaaS Platform",
    page_icon="⚡",
    layout="wide"
)

# ПРОФЕСІЙНИЙ CSS-ДИЗАЙН (Стиль SaaS / Clean Dashboard)
st.markdown("""
    <style>
    /* Загальний фон та шрифти */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Головний заголовок */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.025em;
        margin-bottom: 0px;
    }
    .main-subtitle {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 2rem;
    }

    /* Картки-контейнери */
    div.stForm {
        background: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    
    /* Стиль заголовків всередині форми */
    h3 {
        color: #1e293b !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        margin-top: 1rem !important;
    }

    /* Поля вводу */
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        color: #0f172a;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
    }

    /* Кнопки */
    .stButton button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }
    
    /* Сайдбар */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# Шапка сайту
st.markdown('<p class="main-title">⚡ Spain Job Agent SaaS</p>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Автономна система моніторингу ринку праці, генерації резюме та сповіщень в Іспанії.</p>', unsafe_allow_html=True)

# Сайдбар для ідентифікації
with st.sidebar:
    st.markdown("### 🔐 Авторизація користувача")
    user_email = st.text_input("Email-ідентифікатор", placeholder="vash.email@gmail.com", help="Введіть свій email, щоб завантажити персональні налаштування.")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🤖 Telegram-бот")
    st.markdown("<p style='font-size: 0.85rem; color: #64748b;'>Налаштуйте для отримання миттєвих звітів про вакансії.</p>", unsafe_allow_html=True)
    
    user_data = get_user_data(user_email) if user_email else None
    
    telegram_token = st.text_input("Bot Token", type="password", value=user_data["telegram_token"] if user_data else "")
    telegram_chat_id = st.text_input("Chat ID", value=user_data["telegram_chat_id"] if user_data else "")

# Основна логіка
if not user_email or "@" not in user_email:
    # Красивий бейдж-застереження замість сухого тексту
    st.info("👋 **Вітаємо!** Будь ласка, введіть свій **Email** у бічній панелі ліворуч, щоб розпочати роботу з платформою.")
else:
    default_name = user_data["name"] if user_data else ""
    default_exp = user_data["experience"] if user_data else ""
    default_lang = user_data["languages"] if user_data else ""
    default_permit = user_data["work_permit"] if user_data else "Permiso de trabajo en España"
    default_titles = user_data["job_titles"] if user_data else "Instalador FTTH, Técnico de redes"
    default_locs = user_data["locations"] if user_data else "Alicante, Valencia, Murcia"
    default_threshold = user_data["matching_threshold"] if user_data else 70

    with st.form("onboarding_form"):
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("### 👤 Профіль кандидата")
            candidate_name = st.text_input("Повне ім'я", value=default_name)
            work_permit = st.text_input("Дозвіл на роботу", value=default_permit)
            languages = st.text_input("Мови", value=default_lang)
            experience = st.text_area("Професійний досвід та навички", value=default_exp, height=140)

        with col2:
            st.markdown("### 🎯 Цілі та параметри пошуку")
            job_titles_input = st.text_area("Бажані посади (через кому)", value=default_titles, height=85)
            locations_input = st.text_input("Міста / Регіони", value=default_locs)
            matching_threshold = st.slider("Мінімальний поріг релевантності ШІ (%)", min_value=50, max_value=95, value=default_threshold)
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("💾 Зберегти профіль та згенерувати CV", use_container_width=True)

    if submitted:
        profile_data = {
            "name": candidate_name, "experience": experience, "languages": languages,
            "work_permit": work_permit, "job_titles": job_titles_input, "locations": locations_input,
            "matching_threshold": matching_threshold, "telegram_token": telegram_token, "telegram_chat_id": telegram_chat_id
        }

        save_user_data(user_email, profile_data)
        
        safe_email_name = user_email.replace("@", "_at_").replace(".", "_")
        pdf_filename = f"CV_{safe_email_name}.pdf"
        generate_pdf_cv(profile_data, pdf_filename)
        
        st.success(f"✨ Дані успішно збережено в базі даних для **{user_email}**!")
        st.session_state["last_pdf"] = pdf_filename

    # Панель управління та дій під формою
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⚡ Керування агентом та документи")
    
    act_col1, act_col2 = st.columns(2, gap="medium")
    
    with act_col1:
        target_pdf = st.session_state.get("last_pdf")
        if not target_pdf:
            safe_email_name = user_email.replace("@", "_at_").replace(".", "_")
            potential_pdf = f"CV_{safe_email_name}.pdf"
            if os.path.exists(potential_pdf):
                target_pdf = potential_pdf

        if target_pdf and os.path.exists(target_pdf):
            with open(target_pdf, "rb") as pdf_file:
                st.download_button(
                    label="📄 Завантажити моє CV (PDF)",
                    data=pdf_file,
                    file_name="CV.pdf",
                    mime="application/octet-stream",
                    use_container_width=True
                )
        else:
            st.markdown("<p style='color: #64748b; font-size: 0.9rem;'>Збережіть профіль вище, щоб сформувати персональний документ.</p>", unsafe_allow_html=True)

    with act_col2:
        if st.button("🚀 Запустити сканування ринку праці", use_container_width=True):
            with st.spinner("Агент сканує ринок та обробляє вакансії..."):
                try:
                    result = subprocess.run(["python", "main.py"], capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        st.success("✅ Сканування успішно завершено! Звіт надіслано в Telegram.")
                        if result.stdout:
                            with st.expander("Переглянути деталі логу"):
                                st.text(result.stdout[-600:])
                    else:
                        st.error(f"⚠️ Помилка виконання: {result.stderr}")
                except Exception as e:
                    st.error(f"❌ Не вдалося запустити агент: {e}")
