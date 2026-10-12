import streamlit as st
import json
import os

CONFIG_FILE = "config.json"

def load_existing_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

st.set_page_config(
    page_title="Spain Job Agent - Onboarding",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 AI Job Search Agent (Spain)")
st.subheader("Налаштування вашого персонального агента з працевлаштування в Іспанії")

st.markdown("""
Цей сервіс щодня сканує провідні портали роботи в Іспанії, фільтрує вакансії за допомогою штучного інтелекту, 
генерує персоналізовані супровідні листи (*Carta de presentación*) та надсилає звіт прямо у ваш Telegram.
""")

existing_config = load_existing_config()
default_profile = existing_config.get("candidate_profile", {}) if existing_config else {}
default_params = existing_config.get("search_parameters", {}) if existing_config else {}

with st.form("onboarding_form"):
    st.header("1. Профіль кандидата (для ШІ та резюме)")
    
    candidate_name = st.text_input("Ваше повне ім'я", value=default_profile.get("name", ""))
    experience = st.text_area(
        "Короткий опис досвіду роботи (наприклад, технічні навички, стаж, спеціалізація)",
        value=default_profile.get("experience", "")
    )
    languages = st.text_input(
        "Мови, якими володієте (наприклад: Español (B2), Inglés (Intermedio), Ucraniano (Nativo))",
        value=default_profile.get("languages", "")
    )
    work_permit = st.text_input(
        "Дозвіл на роботу в Іспанії",
        value=default_profile.get("work_permit", "Permiso de trabajo en España / TIE")
    )

    st.header("2. Параметри пошуку вакансій")
    
    # Конвертуємо список посад у текст через кому для зручності введення
    default_titles = ", ".join(default_params.get("job_titles", ["Instalador FTTH", "Técnico de telecomunicaciones"]))
    job_titles_input = st.text_area(
        "Посади для пошуку (розділяйте комами)",
        value=default_titles
    )
    
    default_locations = ", ".join(default_params.get("locations", ["Spain", "Alicante", "Murcia"]))
    locations_input = st.text_input(
        "Регіони / Міста в Іспанії (розділяйте комами)",
        value=default_locations
    )
    
    matching_threshold = st.slider(
        "Мінімальний відсоток відповідності ШІ для сповіщення",
        min_value=50, max_value=95, value=existing_config.get("matching_threshold", 70)
    )

    st.header("3. Інтеграція з Telegram (Куди надсилати звіти)")
    telegram_token = st.text_input("Telegram Bot Token", type="password", value=os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id = st.text_input("Telegram Chat ID", value=os.getenv("TELEGRAM_CHAT_ID", ""))

    submitted = st.form_submit_button("💾 Зберегти налаштування")

if submitted:
    # Обробка введених даних
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

    # Зберігаємо у файл config.json
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_config, f, ensure_ascii=False, indent=4)
        st.success("✅ Налаштування успішно збережено у файл конфігурації!")
        st.balloons()
    except Exception as e:
        st.error(f"❌ Помилка збереження конфігурації: {e}")
