import sqlite3
import os
import requests
# Тут імпортуйте ваші інші модулі для парсингу вакансій та роботи з AI (наприклад, OpenAI / Gemini)

DB_FILE = "database.db"

def get_all_users():
    """Отримує список усіх зареєстрованих користувачів із бази даних"""
    if not os.path.exists(DB_FILE):
        return []
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT email, name, experience, languages, work_permit, 
               job_titles, locations, matching_threshold, 
               telegram_token, telegram_chat_id 
        FROM users
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    users = []
    for row in rows:
        users.append({
            "email": row[0],
            "name": row[1],
            "experience": row[2],
            "languages": row[3],
            "work_permit": row[4],
            # Перетворюємо рядки назад у списки (розділені комами)
            "job_titles": [t.strip() for t in row[5].split(",") if t.strip()],
            "locations": [l.strip() for l in row[6].split(",") if l.strip()],
            "matching_threshold": row[7],
            "telegram_token": row[8],
            "telegram_chat_id": row[9]
        })
    return users

def send_telegram_message(token, chat_id, message):
    """Функція надсилання звіту в Telegram конкретного користувача"""
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Помилка відправки в Telegram: {e}")

def run_job_agent_for_user(user):
    """Виконує пошук вакансій та аналіз для конкретного користувача"""
    print(f"🔄 Запуск агента для користувача: {user['email']}")
    print(f"   Посади: {user['job_titles']}")
    print(f"   Регіони: {user['locations']}")
    
    # 1. ТУТ ВАШ КОД СКАНУВАННЯ ВАКАНСІЙ (парсери Infojobs, LinkedIn тощо)
    # Використовуйте user['job_titles'] та user['locations'] замість конфігу.
    
    # 2. ТУТ АНАЛІЗ ЧЕРЕЗ ШІ (враховуючи досвід користувача: user['experience'])
    
    # 3. Формування персонального звіту
    report_text = f"🤖 *Щоденний звіт для {user['name']}*\n\nАгент перевірив ринок за вашими параметрами. Знайдено нові вакансії!"
    
    # 4. Надсилання в Telegram цього користувача
    if user["telegram_token"] and user["telegram_chat_id"]:
        send_telegram_message(user["telegram_token"], user["telegram_chat_id"], report_text)
        print(f"✅ Звіт надіслано в Telegram для {user['email']}")
    else:
        print(f"⚠️ У користувача {user['email']} не налаштовано Telegram-токен.")

def main():
    print("🚀 Старт масового сканування для всіх користувачів SaaS...")
    users = get_all_users()
    
    if not users:
        print("❌ У базі даних немає жодного користувача.")
        return
        
    for user in users:
        try:
            run_job_agent_for_user(user)
        except Exception as e:
            print(f"❌ Помилка при обробці користувача {user['email']}: {e}")

    print("🏁 Усі завдання завершено успішно.")

if __name__ == "__main__":
    main()
