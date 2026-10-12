import streamlit as st
import sqlite3
import os
import subprocess
from cv_generator import generate_pdf_cv

DB_FILE = "database.db"

# Словник локалізації (7 мов)
TRANSLATIONS = {
    "uk": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Автономна платформа пошуку вакансій, підрядів і субпідрядів, генерації резюме та комерційних пропозицій.",
        "sidebar_auth": "🔑 Ідентифікація",
        "email_label": "Ваш Email (Логін)",
        "email_help": "Ключ до вашого профілю у системі.",
        "sidebar_lang": "🌐 Мова інтерфейсу",
        "sidebar_info": "ℹ️ Про сервіс",
        "sidebar_desc": "Автоматичний моніторинг ринку праці з інтелектуальним підбором та миттєвими сповіщеннями.",
        "welcome_warning": "👋 Будь ласка, введіть свій **Email** у бічній панелі ліворуч, щоб розпочати.",
        "tab1": "👤 Профіль та Пошук",
        "tab2": "Керування та CV",
        "tab3": "🤖 Telegram-сповіщення",
        "profile_header": "Контакти, профіль та налаштування кандидата",
        "name_label": "Повне ім'я",
        "phone_label": "Номер телефону",
        "address_label": "Адреса (Місто, Країна)",
        "profile_summary_label": "Професійний профіль (Summary)",
        "lang_label": "Мови",
        "lang_placeholder": "English (Fluent), Spanish (B2)",
        "titles_label": "Бажані посади (через кому)",
        "locs_label": "Регіони / Міста / Remote",
        "threshold_label": "Поріг релевантності ШІ (%)",
        "exp_label": "Досвід роботи (попередні компанії, посади, дати, досягнення)",
        "edu_label": "Освіта",
        "cert_label": "Сертифікати та ліцензії",
        "other_label": "Інші дані (дозвіл на роботу, водійські права, власне авто, переїзд тощо)",
        "add_label": "Додаткова інформація",
        "save_profile_btn": "💾 Зберегти профіль та оновити професійне CV",
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
        "save_success": "✨ Зміни успішно збережено в базі даних та розширене резюме оновлено!"
    },
    "en": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Autonomous platform for searching jobs, contracts, subcontracts, resume generation, and commercial proposals.",
        "sidebar_auth": "🔑 Identification",
        "email_label": "Your Email",
        "email_help": "Unique key for your profile in the system.",
        "sidebar_lang": "🌐 Interface Language",
        "sidebar_info": "ℹ️ About the Service",
        "sidebar_desc": "Automated monitoring of the job market with intelligent matching and instant alerts.",
        "welcome_warning": "👋 Please enter your **Email** in the sidebar on the left to get started.",
        "tab1": "👤 Profile & Search",
        "tab2": "🤖 Telegram Alerts",
        "tab3": "⚡ Management & CV",
        "profile_header": "Contacts, Profile & Candidate Settings",
        "name_label": "Full Name",
        "phone_label": "Phone Number",
        "address_label": "Address (City, Country)",
        "profile_summary_label": "Professional Profile (Summary)",
        "lang_label": "Languages",
        "lang_placeholder": "English (Fluent), Spanish (B2)",
        "titles_label": "Target Job Titles (comma separated)",
        "locs_label": "Regions / Cities / Remote",
        "threshold_label": "AI Matching Threshold (%)",
        "exp_label": "Work Experience (previous companies, roles, dates, achievements)",
        "edu_label": "Education",
        "cert_label": "Certifications & Licenses",
        "other_label": "Other Data (work permit, driver's license, own car, relocation, etc.)",
        "add_label": "Additional Information",
        "save_profile_btn": "💾 Save Profile & Update Professional CV",
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
        "save_success": "✨ Changes successfully saved to database and professional CV updated!"
    },
    "es": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Plataforma autónoma para la búsqueda de empleo, contratos, subcontratos, generación de CV y propuestas comerciales.",
        "sidebar_auth": "🔑 Identificación",
        "email_label": "Tu Correo Electrónico",
        "email_help": "Clave única para tu perfil en el sistema.",
        "sidebar_lang": "🌐 Idioma de la Interfaz",
        "sidebar_info": "ℹ️ Sobre el servicio",
        "sidebar_desc": "Monitoreo automatizado del mercado laboral con selección inteligente y alertas al instante.",
        "welcome_warning": "👋 Por favor, introduce tu **Correo Electrónico** en la barra lateral izquierda para empezar.",
        "tab1": "👤 Perfil y Búsqueda",
        "tab2": "🤖 Alertas de Telegram",
        "tab3": "⚡ Gestión y CV",
        "profile_header": "Contactos, Perfil y Configuración",
        "name_label": "Nombre Completo",
        "phone_label": "Número de Teléfono",
        "address_label": "Dirección (Ciudad, País)",
        "profile_summary_label": "Perfil Profesional (Summary)",
        "lang_label": "Idiomas",
        "lang_placeholder": "English (Fluent), Spanish (B2)",
        "titles_label": "Puestos Deseados (separados por comas)",
        "locs_label": "Regiones / Ciudades / Remoto",
        "threshold_label": "Umbral de Coincidencia de IA (%)",
        "exp_label": "Experiencia Laboral (empresas anteriores, puestos, fechas, logros)",
        "edu_label": "Educación",
        "cert_label": "Certificaciones y Licencias",
        "other_label": "Otros Datos (permiso de trabajo, carné de conducir, coche propio, etc.)",
        "add_label": "Información Adicional",
        "save_profile_btn": "💾 Guardar Perfil y Actualizar CV Profesional",
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
        "save_success": "✨ ¡Cambios guardados en la base de datos y CV profesional actualizado!"
    },
    "fr": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Plateforme autonome de recherche d'emplois, contrats, sous-traitances, génération de CV et propositions commerciales.",
        "sidebar_auth": "🔑 Identification",
        "email_label": "Votre e-mail",
        "email_help": "Clé unique de votre profil dans le système.",
        "sidebar_lang": "🌐 Langue de l'interface",
        "sidebar_info": "ℹ️ À propos du service",
        "sidebar_desc": "Surveillance automatisée du marché de l'emploi avec sélection intelligente et alertes instantanées.",
        "welcome_warning": "👋 Veuillez entrer votre **e-mail** dans la barre latérale à gauche pour commencer.",
        "tab1": "👤 Profil et Recherche",
        "tab2": "🤖 Alertes Telegram",
        "tab3": "⚡ Gestión et CV",
        "profile_header": "Contacts, profil et paramètres",
        "name_label": "Nom complet",
        "phone_label": "Numéro de téléphone",
        "address_label": "Adresse (Ville, Pays)",
        "profile_summary_label": "Profil professionnel (Summary)",
        "lang_label": "Langues",
        "lang_placeholder": "Anglais (Courant), Espagnol (B2)",
        "titles_label": "Postes recherchés (séparés par des virgules)",
        "locs_label": "Régions / Villes / Télétravail",
        "threshold_label": "Seuil de correspondance IA (%)",
        "exp_label": "Expérience professionnelle (postes, entreprises, dates, réalisations)",
        "edu_label": "Formation",
        "cert_label": "Certifications & Licences",
        "other_label": "Autres données (permis de travail, permis de conduire, véhicule, etc.)",
        "add_label": "Informations complémentaires",
        "save_profile_btn": "💾 Enregistrer et mettre à jour le CV professionnel",
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
        "save_success": "✨ Modifications enregistrées et CV professionnel mis à jour !"
    },
    "de": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Autonome Plattform für die Suche nach Jobs, Aufträgen, Subaufträgen, Lebenslauferstellung und kommerziellen Angeboten.",
        "sidebar_auth": "🔑 Identifikation",
        "email_label": "Ihre E-Mail-Adresse",
        "email_help": "Eindeutiger Schlüssel für Ihr Profil im System.",
        "sidebar_lang": "🌐 Oberflächensprache",
        "sidebar_info": "ℹ️ Über den Service",
        "sidebar_desc": "Automatisierte Überwachung des Arbeitsmarktes mit intelligenter Zuordnung und Sofortbenachrichtigungen.",
        "welcome_warning": "👋 Bitte geben Sie Ihre **E-Mail-Adresse** in der Seitenleiste links ein, um zu beginnen.",
        "tab1": "👤 Profil & Suche",
        "tab2": "🤖 Telegram-Benachrichtigungen",
        "tab3": "⚡ Verwaltung & Lebenslauf",
        "profile_header": "Kontakte, Profil & Einstellungen",
        "name_label": "Vollständiger Name",
        "phone_label": "Telefonnummer",
        "address_label": "Adresse (Stadt, Land)",
        "profile_summary_label": "Berufliches Profil (Summary)",
        "lang_label": "Sprachen",
        "lang_placeholder": "Englisch (Fließend), Spanisch (B2)",
        "titles_label": "Gewünschte Berufsbezeichnungen (durch Komma getrennt)",
        "locs_label": "Regionen / Städte / Remote",
        "threshold_label": "KI-Übereinstimmungsschwellenwert (%)",
        "exp_label": "Berufserfahrung (vorherige Unternehmen, Rollen, Daten, Erfolge)",
        "edu_label": "Ausbildung",
        "cert_label": "Zertifikate & Lizenzen",
        "other_label": "Sonstige Daten (Arbeitserlaubnis, Führerschein, eigenes Auto usw.)",
        "add_label": "Zusätzliche Informationen",
        "save_profile_btn": "💾 Profil speichern & professionellen Lebenslauf aktualisieren",
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
        "save_success": "✨ Änderungen erfolgreich gespeichert und professioneller Lebenslauf aktualisiert!"
    },
    "pt": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Plataforma autônoma para busca de empregos, contratos, subcontratos, geração de currículos e propostas comerciais.",
        "sidebar_auth": "🔑 Identificação",
        "email_label": "Seu E-mail",
        "email_help": "Chave exclusiva para o seu perfil no sistema.",
        "sidebar_lang": "🌐 Idioma da Interface",
        "sidebar_info": "ℹ️ Sobre o Sistema",
        "sidebar_desc": "Monitoramento automatizado do mercado de trabalho com seleção inteligente e alertas instantâneos.",
        "welcome_warning": "👋 Por favor, insira seu **E-mail** na barra lateral à esquerda para começar.",
        "tab1": "👤 Perfil e Busca",
        "tab2": "🤖 Alertas do Telegram",
        "tab3": "⚡ Gestão e CV",
        "profile_header": "Contatos, Perfil e Configurações",
        "name_label": "Nome Completo",
        "phone_label": "Número de Telefone",
        "address_label": "Endereço (Cidade, País)",
        "profile_summary_label": "Perfil Profissional (Summary)",
        "lang_label": "Idiomas",
        "lang_placeholder": "Inglês Fluente, Espanhol B2",
        "titles_label": "Cargos Desejados (separados por vírgula)",
        "locs_label": "Regiões / Cidades / Remoto",
        "threshold_label": "Limiar de Correspondência de IA (%)",
        "exp_label": "Experiência Profissional (empresas anteriores, cargos, datas, conquistas)",
        "edu_label": "Educação",
        "cert_label": "Certificações e Licenças",
        "other_label": "Outros Dados (autorização de trabalho, carta de condução, carro próprio, etc.)",
        "add_label": "Informações Adicionais",
        "save_profile_btn": "💾 Salvar Perfil e Atualizar CV Profissional",
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
        "save_success": "✨ Alterações salvas com sucesso e CV profissional atualizado!"
    },
    "ru": {
        "page_title": "Global Job Hub | SaaS",
        "app_title": "🌍 Global Job Hub",
        "app_caption": "Автономная платформа поиска вакансий, подрядов и субподрядов, генерации резюме и коммерческих предложений.",
        "sidebar_auth": "🔑 Идентификация",
        "email_label": "Ваш Email",
        "email_help": "Уникальный ключ вашего профиля в системе.",
        "sidebar_lang": "🌐 Язык интерфейса",
        "sidebar_info": "ℹ️ О сервисе",
        "sidebar_desc": "Автоматический мониторинг рынка труда с интеллектуальным подбором и мгновенными уведомлениями.",
        "welcome_warning": "👋 Пожалуйста, введите свой **Email** в боковой панели слева, чтобы начать.",
        "tab1": "👤 Профиль и Поиск",
        "tab2": "🤖 Telegram-уведомления",
        "tab3": "⚡ Управление и CV",
        "profile_header": "Контакты, профиль и настройки кандидата",
        "name_label": "Полное имя",
        "phone_label": "Номер телефона",
        "address_label": "Адрес (Город, Страна)",
        "profile_summary_label": "Профессиональный профиль (Summary)",
        "lang_label": "Языки",
        "lang_placeholder": "English (Fluent), Spanish (B2)",
        "titles_label": "Желаемые должности (через запятую)",
        "locs_label": "Регионы / Города / Remote",
        "threshold_label": "Порог релевантности ИИ (%)",
        "exp_label": "Опыт работы (предыдущие компании, роли, даты, достижения)",
        "edu_label": "Образование",
        "cert_label": "Сертификаты и лицензии",
        "other_label": "Прочие данные (разрешение на работу, права, личный авто, переезд и т.д.)",
        "add_label": "Дополнительная информация",
        "save_profile_btn": "💾 Сохранить профиль и обновить профессиональное CV",
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
        "scan_btn": "⚡ Запустить поиск вакансий зараз",
        "scan_spinner": "Агент сканирует глобальный рынок труда...",
        "scan_success": "✅ Сканирование успешно завершено!",
        "log_exp": "Лог выполнения",
        "save_success": "✨ Изменения успешно сохранены в базе данных и профессиональное резюме обновлено!"
    }
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            address TEXT,
            professional_profile TEXT,
            experience TEXT,
            languages TEXT,
            job_titles TEXT,
            locations TEXT,
            matching_threshold INTEGER,
            telegram_token TEXT,
            telegram_chat_id TEXT,
            education TEXT,
            certifications TEXT,
            other_data TEXT,
            additional_info TEXT
        )
    ''')
    for col in ["phone", "address", "professional_profile", "other_data"]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

def get_user_data(email):
    if not email:
        return None
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, phone, address, professional_profile, experience, languages, 
               job_titles, locations, matching_threshold, 
               telegram_token, telegram_chat_id, education, certifications, 
               other_data, additional_info 
        FROM users WHERE email = ?
    """, (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0], "phone": row[1] or "", "address": row[2] or "", 
            "professional_profile": row[3] or "", "experience": row[4] or "", 
            "languages": row[5] or "", "job_titles": row[6] or "", 
            "locations": row[7] or "", "matching_threshold": row[8] or 70, 
            "telegram_token": row[9] or "", "telegram_chat_id": row[10] or "", 
            "education": row[11] or "", "certifications": row[12] or "", 
            "other_data": row[13] or "", "additional_info": row[14] or ""
        }
    return None

def save_user_data(email, data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (
            email, name, phone, address, professional_profile, experience, 
            languages, job_titles, locations, matching_threshold, 
            telegram_token, telegram_chat_id, education, certifications, 
            other_data, additional_info
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        email, data["name"], data["phone"], data["address"], data["professional_profile"],
        data["experience"], data["languages"], data["job_titles"],
        data["locations"], data["matching_threshold"], data["telegram_token"],
        data["telegram_chat_id"], data["education"], data["certifications"],
        data["other_data"], data["additional_info"]
    ))
    conn.commit()
    conn.close()

init_db()

st.set_page_config(
    page_title="Global Job Hub | SaaS",
    page_icon="🌍",
    layout="wide"
)

with st.sidebar:
    st.markdown("### 🌐 Language")
    selected_lang = st.selectbox(
        "Виберіть мову",
        options=["uk", "en", "es", "fr", "de", "pt", "ru"],
        format_func=lambda x: {
            "uk": "🇺🇦 Українська",
            "en": "🇬🇧 English",
            "es": "🇪🇸 Español",
            "fr": "🇫🇷 Français",
            "de": "🇩🇪 Deutsch",
            "pt": "🇵🇹 Português",
            "ru": "🇷🇺 Русский"
        }[x],
        label_visibility="collapsed"
    )
    st.session_state["lang"] = selected_lang

lang = st.session_state.get("lang", "uk")
t = TRANSLATIONS[lang]

st.title(t["app_title"])
st.caption(t["app_caption"])

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
    default_phone = user_data["phone"] if user_data else ""
    default_address = user_data["address"] if user_data else ""
    default_profile = user_data["professional_profile"] if user_data else ""
    default_exp = user_data["experience"] if user_data else ""
    default_edu = user_data["education"] if user_data else ""
    default_certs = user_data["certifications"] if user_data else ""
    default_other = user_data["other_data"] if user_data else ""
    default_add = user_data["additional_info"] if user_data else ""
    default_lang = user_data["languages"] if user_data else ""
    default_titles = user_data["job_titles"] if user_data else "Telecom Specialist, FTTH Technician, Remote"
    default_locs = user_data["locations"] if user_data else "Remote, Europe, Spain"
    default_threshold = user_data["matching_threshold"] if user_data else 70
    default_tg_token = user_data["telegram_token"] if user_data else ""
    default_tg_chat = user_data["telegram_chat_id"] if user_data else ""

    tab1, tab2, tab3 = st.tabs([t["tab1"], t["tab2"], t["tab3"]])

    with tab1:
        st.markdown(f"#### {t['profile_header']}")
        with st.form("profile_form"):
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                candidate_name = st.text_input(t["name_label"], value=default_name)
                candidate_phone = st.text_input(t["phone_label"], value=default_phone, placeholder="+34 ... / +380 ...")
                candidate_address = st.text_input(t["address_label"], value=default_address, placeholder="Alicante, Spain / Mukachevo, Ukraine")
                languages = st.text_input(t["lang_label"], value=default_lang, placeholder=t["lang_placeholder"])
                
            with col2:
                job_titles_input = st.text_area(t["titles_label"], value=default_titles, height=80)
                locations_input = st.text_input(t["locs_label"], value=default_locs)
                matching_threshold = st.slider(t["threshold_label"], min_value=50, max_value=95, value=default_threshold)
            
            professional_profile = st.text_area(t["profile_summary_label"], value=default_profile, height=90, placeholder="Короткий огляд вашого досвіду та сильних сторін...")
            experience = st.text_area(t["exp_label"], value=default_exp, height=140, placeholder="Company A | Role | Dates\n- Achievement 1\n\nCompany B | Role | Dates\n- Achievement 2")
            education = st.text_area(t["edu_label"], value=default_edu, height=80)
            certifications = st.text_area(t["cert_label"], value=default_certs, height=80)
            other_data = st.text_area(t["other_label"], value=default_other, height=80, placeholder="EU Work Permit, водійські права (B), власний автомобіль, готовність до релокації...")
            additional_info = st.text_area(t["add_label"], value=default_add, height=80)
            
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

    if submitted or ('tg_submitted' in locals() and tg_submitted):
        current_data = get_user_data(user_email) or {}
        
        profile_data = {
            "name": candidate_name if 'candidate_name' in locals() else current_data.get("name", ""),
            "phone": candidate_phone if 'candidate_phone' in locals() else current_data.get("phone", ""),
            "address": candidate_address if 'candidate_address' in locals() else current_data.get("address", ""),
            "professional_profile": professional_profile if 'professional_profile' in locals() else current_data.get("professional_profile", ""),
            "experience": experience if 'experience' in locals() else current_data.get("experience", ""),
            "education": education if 'education' in locals() else current_data.get("education", ""),
            "certifications": certifications if 'certifications' in locals() else current_data.get("certifications", ""),
            "other_data": other_data if 'other_data' in locals() else current_data.get("other_data", ""),
            "additional_info": additional_info if 'additional_info' in locals() else current_data.get("additional_info", ""),
            "languages": languages if 'languages' in locals() else current_data.get("languages", ""),
            "job_titles": job_titles_input if 'job_titles_input' in locals() else current_data.get("job_titles", ""),
            "locations": locations_input if 'locations_input' in locals() else current_data.get("locations", ""),
            "matching_threshold": matching_threshold if 'matching_threshold' in locals() else current_data.get("matching_threshold", 70),
            "telegram_token": telegram_token if 'telegram_token' in locals() else current_data.get("telegram_token", ""),
            "telegram_chat_id": telegram_chat_id if 'telegram_chat_id' in locals() else current_data.get("telegram_chat_id", "")
        }

        save_user_data(user_email, profile_data)
        pdf_filename = f"CV_{user_email.replace('@', '_at_').replace('.', '_')}.pdf"
        generate_pdf_cv(profile_data, user_email, pdf_filename)
        
        st.success(t["save_success"])
