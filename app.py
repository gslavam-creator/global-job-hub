import streamlit as st
import json
import os
import subprocess
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

CONFIG_FILE = "config.json"
PDF_FILE = "CV.pdf"

def load_existing_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def generate_pdf_cv(profile):
    """Створює професійний PDF-файл резюме на основі даних профілю"""
    doc = SimpleDocTemplate(PDF_FILE, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # Кастомні стилі
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=15,
        textColor=colors_hex := "#1a365d"
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors_hex
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leading=14
    )

    # Додаємо контент у PDF
    story.append(Paragraph(profile.get("name", "Candidate CV"), title_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>Дозвіл на роботу:</b> " + profile.get("work_permit", ""), body_style))
    story.append(Paragraph("<b>Мови:</b> " + profile.get("languages", ""), body_style))
    
    story.append(Paragraph("Професійний досвід та навички", heading_style))
    story.append(Paragraph(profile.get("experience", "").replace("\n", "<br/>"), body_style))
    
    doc.build(story)

st.set_page_config(
    page_title="Spain Job Agent - Onboarding",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 AI Job Search Agent (Spain)")
st.subheader("Налаштування профілю та запуск агента")

existing_config = load_existing_config()
default_profile = existing_config.get("candidate_profile", {}) if existing_config else {}
default_params = existing_config.get("search_parameters", {}) if existing_config else {}

with st.form("onboarding_form"):
    st.header("1. Профіль кандидата")
    candidate_name = st.text_input("Ваше повне ім'я", value=default_profile.get("name", ""))
    experience = st.text_area(
        "Досвід роботи (навички, стаж, спеціалізація)",
        value=default_profile.get("experience", "")
    )
    languages = st.text_input(
        "Мови (наприклад: Español (B2), Inglés (Intermedio))",
        value=default_profile.get("languages", "")
    )
    work_permit = st.text_input(
        "Дозвіл на роботу в Іспанії",
        value=default_profile.get("work_permit", "Permiso de trabajo en España")
    )

    st.header("2. Параметри пошуку")
    default_titles = ", ".join(default_params.get("job_titles", ["Instalador FTTH"]))
    job_titles_input = st.text_area("Посади (через кому)", value=default_titles)
    
    default_locations = ", ".join(default_params.get("locations", ["Spain", "Alicante"]))
    locations_input = st.text_input("Регіони / Міста (через кому)", value=default_locations)
    
    matching_threshold = st.slider(
        "Поріг відповідності ШІ (%)",
        min_value=50, max_value=95, value=existing_config.get("matching_threshold", 70)
    )

    st.header("3. Telegram (для сповіщень)")
    telegram_token = st.text_input("Telegram Bot Token", type="password", value=os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id = st.text_input("Telegram Chat ID", value=os.getenv("TELEGRAM_CHAT_ID", ""))

    submitted = st.form_submit_button("💾 Зберегти дані та згенерувати резюме")

if submitted:
    job_titles_list = [t.strip() for t in job_titles_input.split(",") if t.strip()]
    locations_list = [l.strip() for l in locations_input.split(",") if l.strip()]

    new_config = {
        "candidate_profile": {
            "name": candidate_name,
            "experience": experience,
            "languages": languages,
            "work_permit": work_permit
        },
        "search_parameters": {
            "job_titles": job_titles_list,
            "locations": locations_list,
            "results_wanted": 15
        },
        "matching_threshold": matching_threshold
    }

    # Зберігаємо конфіг
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_config, f, ensure_ascii=False, indent=4)
        
        # Генеруємо PDF
        generate_pdf_cv(new_config["candidate_profile"])
        
        st.success("✅ Налаштування збережено, а PDF-резюме успішно згенеровано!")
        st.balloons()
    except Exception as e:
        st.error(f"❌ Помилка: {e}")

# Додаткова секція: Ручний запуск пошуку вакансій прямо з сайту
st.divider()
st.subheader("⚡ Керування агентом")
st.markdown("Ви можете протестувати запуск пошуку вакансій просто зараз натисканням кнопки нижче:")

if st.button("🚀 Запустити сканування вакансій"):
    with st.spinner("Агент сканує ринок праці в Іспанії та аналізує збіги..."):
        try:
            # Запуск основного скрипта агента (main.py)
            result = subprocess.run(["python", "main.py"], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                st.success("✅ Сканування завершено! Звіт надіслано у ваш Telegram.")
                if result.stdout:
                    st.text(result.stdout[-500:]) # Показати останні рядки логу
            else:
                st.error(f"⚠️ Сталася помилка під час виконання: {result.stderr}")
        except Exception as e:
            st.error(f"❌ Не вдалося запустити агент: {e}")

# Кнопка завантаження згенерованого CV
if os.path.exists(PDF_FILE):
    st.divider()
    with open(PDF_FILE, "rb") as pdf_file:
        st.download_button(
            label="📄 Завантажити згенероване CV.pdf",
            data=pdf_file,
            file_name="CV.pdf",
            mime="application/octet-stream"
        )
