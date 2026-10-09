import os
import json
import sqlite3
import asyncio
from dotenv import load_dotenv
from jobspy import scrape_jobs
from openai import OpenAI
from telegram import Bot

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
telegram_bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")
db_path = os.path.join(script_dir, "jobs_history.db")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_jobs (
            job_url TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_job_processed(job_url):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_jobs WHERE job_url = ?", (job_url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_job_as_processed(job_url, title, company):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO processed_jobs (job_url, title, company) VALUES (?, ?, ?)",
        (job_url, title, company)
    )
    conn.commit()
    conn.close()

def evaluate_job(job_title, job_description):
    prompt = f"""
    Ти — HR-експерт ринку праці Іспанії. Оціни відповідність вакансії кандидату від 0 до 100%.

    ПРОФІЛЬ КАНДИДАТА:
    {config['candidate_profile']['experience']}
    Мови: {config['candidate_profile']['languages']}
    Право на роботу: {config['candidate_profile']['work_permit']}

    ВАКАНСІЯ:
    Назва: {job_title}
    Опис: {job_description[:2500]}

    Поверни відповідь СУВОРО у форматі JSON:
    {{
      "score": number,
      "reason": "коротке пояснення українською мовою (2 речення)",
      "cover_letter": "короткий супровідний лист іспанською мовою (Carta de presentación, до 100 слів)"
    }}
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Помилка аналізу OpenAI: {e}")
        return None

async def main():
    init_db()
    print("🚀 Запуск моніторингу вакансій в Іспанії...")

    try:
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "glassdoor"],
            search_term=" OR ".join(config["search_parameters"]["job_titles"]),
            location=config["search_parameters"]["location"],
            results_wanted=config["search_parameters"]["results_wanted"],
            country_indeed='spain'
        )
    except Exception as e:
        print(f"Помилка при зборі вакансій: {e}")
        return

    print(f"Знайдено вакансій: {len(jobs)}")

    for idx, row in jobs.iterrows():
        job_url = row.get('job_url', '')
        title = str(row.get('title', 'Без назви'))
        company = str(row.get('company', 'Невідома компанія'))
        location = str(row.get('location', 'Іспанія'))
        description = str(row.get('description', ''))

        if not job_url or is_job_processed(job_url):
            continue

        if not description or len(description) < 100:
            mark_job_as_processed(job_url, title, company)
            continue

        evaluation = evaluate_job(title, description)
        mark_job_as_processed(job_url, title, company)

        if not evaluation:
            continue

        score = evaluation.get("score", 0)
        print(f"Оцінка [{score}%]: {title} у {company}")

        if score >= config["matching_threshold"]:
            message = (
                f"🎯 **Нова відповідна вакансія ({score}%)**\n\n"
                f"📌 **Посада:** {title}\n"
                f"🏢 **Компанія:** {company}\n"
                f"📍 **Локація:** {location}\n\n"
                f"💡 **Обґрунтування:**\n{evaluation.get('reason')}\n\n"
                f"📝 **Carta de Presentación:**\n`{evaluation.get('cover_letter')}`\n\n"
                f"🔗 [Переглянути вакансію]({job_url})"
            )
            try:
                await telegram_bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Помилка відправки в Telegram: {e}")

if __name__ == "__main__":
    asyncio.run(main())