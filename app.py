import streamlit as st
import sqlite3
import os
import subprocess
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB_FILE = "database.db"

# Словник локалізації (7 мов)
TRANSLATIONS = {
    "uk": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Автономна платформа глобального пошуку вакансій, генерації резюме та розумних сповіщень.",
        "sidebar_auth": "🔑 Ідентифікація",
        "email_label": "Ваш Email",
        "email_help": "Ключ до вашого профілю у системі.",
        "sidebar_lang": "🌐 Мова інтерфейсу",
        "sidebar_info": "ℹ️ Про систему",
        "sidebar_desc": "Цей сервіс автоматично сканує світовий ринок праці за вашими критеріями та надсилає персональні звіти.",
        "welcome_warning": "👋 Будь ласка, введіть свій **Email** у бічній панелі ліворуч, щоб розпочати.",
        "tab1": "👤 Профіль та Пошук",
        "tab2": "🤖 Telegram-сповіщення",
        "tab3": "⚡ Керування та CV",
        "profile_header": "Налаштування профілю кандидата",
        "name_label": "Повне ім'я",
        "permit_label": "Дозвіл на роботу / Віза",
        "lang_label": "Мови",
        "lang_placeholder": "English (Fluent), Spanish (B2)",
        "titles_label": "Бажані посади (через кому)",
        "locs_label": "Регіони / Міста / Remote",
        "threshold_label": "Поріг релевантності ШІ (%)",
        "exp_label": "Детальний досвід роботи та навички",
        "save_profile_btn": "💾 Зберегти профіль та оновити CV",
        "tg_header": "Налаштування Telegram-бота",
        "tg_desc": "Введіть дані вашого бота для отримання миттєвих сповіщень про нові вакансії.",
        "tg_token": "Telegram Bot Token",
        "tg_chat": "Telegram Chat ID",
        "save_tg_btn": "💾 Зберегти налаштування Telegram",
        "docs_header": "Робота з документами та запуск агента",
        "cv_header": "📄 Ваше персональне CV",
        "download_cv": "📥 Завантажити CV.pdf",
        "cv_info": "Спочатку збережіть профіль на першій вкладці, щоб згенерувати документ.",
        "scan_header": "🚀 Запуск глобального сканування",
        "scan_btn": "⚡ Запустити пошук вакансій зараз",
        "scan_spinner": "Агент сканує глобальний ринок праці...",
        "scan_success": "✅ Сканування завершено успішно!",
        "log_exp": "Лог виконання",
        "save_success": "✨ Зміни успішно збережено в базі даних та резюме оновлено!"
    },
    "en": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Autonomous platform for global job hunting, resume generation, and smart notifications.",
        "sidebar_auth": "🔑 Identification",
        "email_label": "Your Email",
        "email_help": "Unique key for your profile in the system.",
        "sidebar_lang": "🌐 Interface Language",
        "sidebar_info": "ℹ️ About System",
        "sidebar_desc": "This service automatically scans the global job market based on your criteria and sends personal reports.",
        "welcome_warning": "👋 Please enter your **Email** in the sidebar on the left to get started.",
        "tab1": "👤 Profile & Search",
        "tab2": "🤖 Telegram Alerts",
        "tab3": "⚡ Management & CV",
        "profile_header": "Candidate Profile Settings",
        "name_label": "Full Name",
        "permit_label": "Work Authorization / Visa",
        "lang_label": "Languages",
        "lang_placeholder": "English (Fluent), Spanish (B2)",
        "titles_label": "Target Job Titles (comma separated)",
        "locs_label": "Regions / Cities / Remote",
        "threshold_label": "AI Matching Threshold (%)",
        "exp_label": "Detailed Work Experience & Skills",
        "save_profile_btn": "💾 Save Profile & Update CV",
        "tg_header": "Telegram Bot Settings",
        "tg_desc": "Enter your bot details to receive instant notifications about new job openings.",
        "tg_token": "Telegram Bot Token",
        "tg_chat": "Telegram Chat ID",
        "save_tg_btn": "💾 Save Telegram Settings",
        "docs_header": "Documents & Agent Runner",
        "cv_header": "📄 Your Personal CV",
        "download_cv": "📥 Download CV.pdf",
        "cv_info": "Save your profile on the first tab first to generate the document.",
        "scan_header": "🚀 Run Global Scan",
        "scan_btn": "⚡ Run Job Search Now",
        "scan_spinner": "Agent is scanning the global job market...",
        "scan_success": "✅ Scan completed successfully!",
        "log_exp": "Execution Log",
        "save_success": "✨ Changes successfully saved to database and CV updated!"
    },
    "es": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Plataforma autónoma para la búsqueda global de empleo, generación de CV y notificaciones inteligentes.",
        "sidebar_auth": "🔑 Identificación",
        "email_label": "Tu Correo Electrónico",
        "email_help": "Clave única para tu perfil en el sistema.",
        "sidebar_lang": "🌐 Idioma de la Interfaz",
        "sidebar_info": "ℹ️ Sobre el Sistema",
        "sidebar_desc": "Este servicio escanea automáticamente el mercado laboral global según tus criterios y envía informes personales.",
        "welcome_warning": "👋 Por favor, introduce tu **Correo Electrónico** en la barra lateral izquierda para empezar.",
        "tab1": "👤 Perfil y Búsqueda",
        "tab2": "🤖 Alertas de Telegram",
        "tab3": "⚡ Gestión y CV",
        "profile_header": "Configuración del Perfil",
        "name_label": "Nombre Completo",
        "permit_label": "Permiso de Trabajo / Visa",
        "lang_label": "Idiomas",
        "lang_placeholder": "English (Fluent), Spanish (B2)",
        "titles_label": "Puestos Deseados (separados por comas)",
        "locs_label": "Regiones / Ciudades / Remoto",
        "threshold_label": "Umbral de Coincidencia de IA (%)",
        "exp_label": "Experiencia Laboral Detallada y Habilidades",
        "save_profile_btn": "💾 Guardar Perfil y Actualizar CV",
        "tg_header": "Configuración del Bot de Telegram",
        "tg_desc": "Introduce los datos de tu bot para recibir notificaciones instantáneas de nuevas ofertas.",
        "tg_token": "Token del Bot de Telegram",
        "tg_chat": "ID de Chat de Telegram",
        "save_tg_btn": "💾 Guardar Configuración de Telegram",
        "docs_header": "Documentos y Ejecución del Agente",
        "cv_header": "📄 Tu CV Personal",
        "download_cv": "📥 Descargar CV.pdf",
        "cv_info": "Guarda tu perfil en la primera pestaña para generar el documento.",
        "scan_header": "🚀 Ejecutar Análisis Global",
        "scan_btn": "⚡ Buscar Empleo Ahora",
        "scan_spinner": "El agente está escaneando el mercado laboral global...",
        "scan_success": "✅ ¡Análisis completado con éxito!",
        "log_exp": "Registro de Ejecución",
        "save_success": "✨ ¡Cambios guardados en la base de datos y CV actualizado!"
    },
    "fr": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Plateforme autonome pour la recherche mondiale d'emploi, la génération de CV et les notifications intelligentes.",
        "sidebar_auth": "🔑 Identification",
        "email_label": "Votre e-mail",
        "email_help": "Clé unique de votre profil dans le système.",
        "sidebar_lang": "🌐 Langue de l'interface",
        "sidebar_info": "ℹ️ À propos du système",
        "sidebar_desc": "Ce service analyse automatiquement le marché mondial de l'emploi selon vos critères et envoie des rapports personnalisés.",
        "welcome_warning": "👋 Veuillez entrer votre **e-mail** dans la barre latérale à gauche pour commencer.",
        "tab1": "👤 Profil et Recherche",
        "tab2": "🤖 Alertes Telegram",
        "tab3": "⚡ Gestion et CV",
        "profile_header": "Paramètres du profil candidat",
        "name_label": "Nom complet",
        "permit_label": "Autorisation de travail / Visa",
        "lang_label": "Langues",
        "lang_placeholder": "Anglais (Courant), Espagnol (B2)",
        "titles_label": "Postes recherchés (séparés par des virgules)",
        "locs_label": "Régions / Villes / Télétravail",
        "threshold_label": "Seuil de correspondance IA (%)",
        "exp_label": "Expérience professionnelle détaillée et compétences",
        "save_profile_btn": "💾 Enregistrer le profil et mettre à jour le CV",
        "tg_header": "Paramètres du bot Telegram",
        "tg_desc": "Entrez les détails de votre bot pour recevoir des notifications instantanées sur les nouvelles offres.",
        "tg_token": "Jeton du bot Telegram",
        "tg_chat": "ID de chat Telegram",
        "save_tg_btn": "💾 Enregistrer les paramètres Telegram",
        "docs_header": "Documents et exécution de l'agent",
        "cv_header": "📄 Votre CV personnel",
        "download_cv": "📥 Télécharger le CV.pdf",
        "cv_info": "Enregistrez d'abord votre profil dans le premier onglet pour générer le document.",
        "scan_header": "🚀 Lancer l'analyse globale",
        "scan_btn": "⚡ Rechercher un emploi maintenant",
        "scan_spinner": "L'agent analyse le marché mondial de l'emploi...",
        "scan_success": "✅ Analyse terminée avec succès !",
        "log_exp": "Journal d'exécution",
        "save_success": "✨ Modifications enregistrées dans la base de données et CV mis à jour !"
    },
    "de": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Autonome Plattform für die globale Jobsuche, Lebenslauf-Generierung und intelligente Benachrichtigungen.",
        "sidebar_auth": "🔑 Identifikation",
        "email_label": "Ihre E-Mail-Adresse",
        "email_help": "Eindeutiger Schlüssel für Ihr Profil im System.",
        "sidebar_lang": "🌐 Oberflächensprache",
        "sidebar_info": "ℹ️ Über das System",
        "sidebar_desc": "Dieser Dienst scannt automatisch den globalen Arbeitsmarkt nach Ihren Kriterien und sendet persönliche Berichte.",
        "welcome_warning": "👋 Bitte geben Sie Ihre **E-Mail-Adresse** in der Seitenleiste links ein, um zu beginnen.",
        "tab1": "👤 Profil & Suche",
        "tab2": "🤖 Telegram-Benachrichtigungen",
        "tab3": "⚡ Verwaltung & Lebenslauf",
        "profile_header": "Kandidatenprofil-Einstellungen",
        "name_label": "Vollständiger Name",
        "permit_label": "Arbeitserlaubnis / Visum",
        "lang_label": "Sprachen",
        "lang_placeholder": "Englisch (Fließend), Spanisch (B2)",
        "titles_label": "Gewünschte Berufsbezeichnungen (durch Komma getrennt)",
        "locs_label": "Regionen / Städte / Remote",
        "threshold_label": "KI-Übereinstimmungsschwellenwert (%)",
        "exp_label": "Detaillierte Berufserfahrung & Fähigkeiten",
        "save_profile_btn": "💾 Profil speichern & Lebenslauf aktualisieren",
        "tg_header": "Telegram-Bot-Einstellungen",
        "tg_desc": "Geben Sie Ihre Bot-Daten ein, um sofortige Benachrichtigungen über neue Stellenangebote zu erhalten.",
        "tg_token": "Telegram Bot Token",
        "tg_chat": "Telegram Chat ID",
        "save_tg_btn": "💾 Telegram-Einstellungen speichern",
        "docs_header": "Dokumente & Agenten-Ausführung",
        "cv_header": "📄 Ihr persönlicher Lebenslauf",
        "download_cv": "📥 Lebenslauf herunterladen (PDF)",
        "cv_info": "Speichern Sie zuerst Ihr Profil im ersten Tab, um das Dokument zu generieren.",
        "scan_header": "🚀 Globalen Scan starten",
        "scan_btn": "⚡ Jetzt nach Jobs suchen",
        "scan_spinner": "Der Agent scannt den globalen Arbeitsmarkt...",
        "scan_success": "✅ Scan erfolgreich abgeschlossen!",
        "log_exp": "Ausführungsprotokoll",
        "save_success": "✨ Änderungen erfolgreich in der Datenbank gespeichert und Lebenslauf aktualisiert!"
    },
    "pt": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Plataforma autônoma para busca global de empregos, geração de currículos e notificações inteligentes.",
        "sidebar_auth": "🔑 Identificação",
        "email_label": "Seu E-mail",
        "email_help": "Chave exclusiva para o seu perfil no sistema.",
        "sidebar_lang": "🌐 Idioma da Interface",
        "sidebar_info": "ℹ️ Sobre o Sistema",
        "sidebar_desc": "Este serviço analisa automaticamente o mercado de trabalho global com base nos seus critérios e envia relatórios pessoais.",
        "welcome_warning": "👋 Por favor, insira seu **E-mail** na barra lateral à esquerda para começar.",
        "tab1": "👤 Perfil e Busca",
        "tab2": "🤖 Alertas do Telegram",
        "tab3": "⚡ Gestão e CV",
        "profile_header": "Configurações do Perfil do Candidato",
        "name_label": "Nome Completo",
        "permit_label": "Autorização de Trabalho / Visto",
        "lang_label": "Idiomas",
        "lang_placeholder": "Inglês Fluente, Espanhol B2",
        "titles_label": "Cargos Desejados (separados por vírgula)",
        "locs_label": "Regiões / Cidades / Remoto",
        "threshold_label": "Limiar de Correspondência de IA (%)",
        "exp_label": "Experiência Profissional Detalhada e Habilidades",
        "save_profile_btn": "💾 Salvar Perfil e Atualizar CV",
        "tg_header": "Configurações do Bot do Telegram",
        "tg_desc": "Insira os dados do seu bot para receber notificações instantâneas sobre novas vagas.",
        "tg_token": "Token do Bot do Telegram",
        "tg_chat": "ID de Chat do Telegram",
        "save_tg_btn": "💾 Salvar Configurações do Telegram",
        "docs_header": "Documentos e Execução do Agente",
        "cv_header": "📄 Seu CV Pessoal",
        "download_cv": "📥 Baixar CV.pdf",
        "cv_info": "Salve seu perfil na primeira aba para gerar o documento.",
        "scan_header": "🚀 Executar Varredura Global",
        "scan_btn": "⚡ Buscar Empregos Agora",
        "scan_spinner": "O agente está escaneando o mercado de trabalho global...",
        "scan_success": "✅ Varredura concluída com sucesso!",
        "log_exp": "Log de Execução",
        "save_success": "✨ Alterações salvas com sucesso no banco de dados e CV atualizado!"
    },
    "ru": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Автономная платформа глобального поиска вакансий, генерации резюме и умных уведомлений.",
        "sidebar_auth": "🔑 Идентификация",
        "email_label": "Ваш Email",
        "email_help": "Уникальный ключ вашего профиля в системе.",
        "sidebar_lang": "🌐 Язык интерфейса",
        "sidebar_info": "ℹ️ О системе",
        "sidebar_desc": "Этот сервис автоматически сканирует мировой рынок труда по вашим критериям и отправляет персональные отчеты.",
        "welcome_warning": "👋 Пожалуйста, введите свой **Email** в боковой панели слева, чтобы начать.",
        "tab1": "👤 Профиль и Поиск",
        "tab2": "🤖 Telegram-уведомления",
        "tab3": "⚡ Управление и CV",
        "profile_header": "Настройки профиля кандидата",
        "name_label": "Полное имя",
        "permit_label": "Разрешение на работу / Виза",
        "lang_label": "Языки",
        "lang_placeholder": "English (Fluent), Spanish (B2)",
        "titles_label": "Желаемые должности (через запятую)",
        "locs_label": "Регионы / Города / Remote",
        "threshold_label": "Порог релевантности ИИ (%)",
        "exp_label": "Подробный опыт работы и навыки",
        "save_profile_btn": "💾 Сохранить профиль и обновить CV",
        "tg_header": "Настройки Telegram-бота",
        "tg_desc": "Введите данные вашего бота для получения мгновенных уведомлений о новых вакансиях.",
        "tg_token": "Telegram Bot Token",
        "tg_chat": "Telegram Chat ID",
        "save_tg_btn": "💾 Сохранить настройки Telegram",
        "docs_header": "Работа с документами и запуск агента",
        "cv_header": "📄 Ваше персональное CV",
        "download_cv": "📥 Скачать CV.pdf",
        "cv_info": "Сначала сохраните профиль на первой вкладке, чтобы сгенерировать документ.",
        "scan_header": "🚀 Запуск глобального сканирования",
        "scan_btn": "⚡ Запустить поиск вакансий сейчас",
        "scan_spinner": "Агент сканирует глобальный рынок труда...",
        "scan_success": "✅ Сканирование успешно завершено!",
        "log_exp": "Лог выполнения",
        "save_success": "✨ Изменения успешно сохранены в базе данных и резюме обновлено!"
    }
}

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
    story.append(Paragraph("<b>Work Authorization / Visa:</b> " + profile.get("work_permit", ""), body_style))
    story.append(Paragraph("<b>Languages:</b> " + profile.get("languages", ""), body_style))
    story.append(Paragraph("Professional Experience & Skills", heading_style))
    story.append(Paragraph(profile.get("experience", "").replace("\n", "<br/>"), body_style))
    
    doc.build(story)

init_db()

# Конфігурація сторінки
st.set_page_config(
    page_title="Global Job Hub | SaaS",
    page_icon="🌍",
    layout="wide"
)

# Вибір мови у сайдбарі
with st.sidebar:
    st.markdown("### 🌐 Language / Мова / Idioma")
    selected_lang = st.selectbox(
        "Виберіть мову",
        options=["uk", "en", "es", "fr", "de", "pt", "ru"],
        format_func=lambda x: {
            "en": "🇬🇧 English",
            "es": "🇪🇸 Español",
            "fr": "🇫🇷 Français",
            "de": "🇩🇪 Deutsch",
            "pt": "🇵🇹 Português",
            "ru": "🇷🇺 Русский",
            "uk": "🇺🇦 Українська"
        }[x],
        label_visibility="collapsed"
    )
    st.session_state["lang"] = selected_lang

# Отримуємо переклади для поточної мови
lang = st.session_state.get("lang", "uk")
t = TRANSLATIONS[lang]

# Шапка додатка
st.title(t["app_title"])
st.caption(t["app_caption"])

# Авторизація у сайдбарі
with st.sidebar:
    st.divider()
    st.markdown(f"### {t['sidebar_auth']}")
    user_email = st.text_input(t["email_label"], placeholder="candidate@example.com", help=t["email_help"])
    st.divider()
    st.markdown(f"### {t['sidebar_info']}")
    st.info(t["sidebar_desc"])

if not user_email or "@" not in user_email:
    st.warning(t["welcome_warning"])
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

    # Вкладки з перекладами
    tab1, tab2, tab3 = st.tabs([t["tab1"], t["tab2"], t["tab3"]])

    with tab1:
        st.markdown(f"#### {t['profile_header']}")
        with st.form("profile_form"):
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                candidate_name = st.text_input(t["name_label"], value=default_name)
                work_permit = st.text_input(t["permit_label"], value=default_permit)
                languages = st.text_input(t["lang_label"], value=default_lang, placeholder=t["lang_placeholder"])
                
            with col2:
                job_titles_input = st.text_area(t["titles_label"], value=default_titles, height=80)
                locations_input = st.text_input(t["locs_label"], value=default_locs)
                matching_threshold = st.slider(t["threshold_label"], min_value=50, max_value=95, value=default_threshold)
            
            experience = st.text_area(t["exp_label"], value=default_exp, height=120)
            
            submitted = st.form_submit_button(t["save_profile_btn"], use_container_width=True)

    with tab2:
        st.markdown(f"#### {t['tg_header']}")
        st.markdown(t["tg_desc"])
        
        with st.form("telegram_form"):
            telegram_token = st.text_input(t["tg_token"], type="password", value=default_tg_token)
            telegram_chat_id = st.text_input(t["tg_chat"], value=default_tg_chat)
            
            tg_submitted = st.form_submit_button(t["save_tg_btn"], use_container_width=True)

    with tab3:
        st.markdown(f"#### {t['docs_header']}")
        
        col_cv, col_agent = st.columns(2, gap="large")
        
        with col_cv:
            st.markdown(f"##### {t['cv_header']}")
            target_pdf = f"CV_{user_email.replace('@', '_at_').replace('.', '_')}.pdf"
            
            if os.path.exists(target_pdf):
                with open(target_pdf, "rb") as pdf_file:
                    st.download_button(
                        label=t["download_cv"],
                        data=pdf_file,
                        file_name="CV.pdf",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
            else:
                st.info(t["cv_info"])

        with col_agent:
            st.markdown(f"##### {t['scan_header']}")
            if st.button(t["scan_btn"], use_container_width=True):
                with st.spinner(t["scan_spinner"]):
                    try:
                        result = subprocess.run(["python", "main.py"], capture_output=True, text=True, timeout=120)
                        if result.returncode == 0:
                            st.success(t["scan_success"])
                            if result.stdout:
                                with st.expander(t["log_exp"]):
                                    st.text(result.stdout[-600:])
                        else:
                            st.error(f"⚠️ Error: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Failed to run: {e}")

    # Обробка збереження форм
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
        
        st.success(t["save_success"])
