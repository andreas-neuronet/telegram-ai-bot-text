import os
import time
import re
import requests
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
    MODEL = os.getenv('MODEL')

def setup():
    required_vars = ['OPENROUTER_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID', 'MODEL']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing {var} in .env file")

def format_for_telegram(text):
    """Форматирует текст для Telegram с учётом MarkdownV2"""
    if not text:
        return ""

    # Шаг 1: Экранируем все специальные символы MarkdownV2
    escaped_text = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

    # Шаг 2: Разбиваем на строки
    lines = escaped_text.split('\n')
    formatted_lines = []

    for line in lines:
        stripped = line.strip()

        # Пропускаем пустые строки
        if not stripped:
            continue

        # Форматируем заголовки (строки, заканчивающиеся на ":")
        if stripped.endswith(':'):
            line = f"*{stripped}*"
        
        # Форматируем маркированные списки
        elif stripped.startswith(('-', '•', '→')):
            bullet = stripped[0]
            content = stripped[1:].strip()
            line = f"• {content}"

        # Форматируем нумерованные списки вроде "1. Что-то", "2. Другое"
        elif re.match(r'^\d+\.', stripped):
            parts = stripped.split('.', 1)
            if len(parts) == 2:
                number, content = parts
                line = f"{number}\\. {content.strip()}"

        # Добавляем к строке эмодзи в начало по желанию
        formatted_lines.append(line)

    # Соединяем абзацы двойным переносом строки
    result = "📌 " + '\n\n'.join(formatted_lines)
    return result

def read_queries(file_path="input.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"File read error: {e}")
        return []

def is_russian(text):
    russian_letters = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    return any(char in russian_letters for char in text.lower())

def get_ai_response(query):
    try:
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": Config.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": """Ты - русскоязычный помощник. Форматируй ответы для Telegram:
1. Используй MarkdownV2 (*жирный*, _курсив_)
2. Разделяй на абзацы (двойной перенос строки)
3. Добавляй эмодзи для наглядности
4. Выделяй основные пункты
Пример:
*Преимущества:*
✅ Надежность
✅ Простота
➡️ Подробнее..."""
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 600
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions ",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            return answer if is_russian(answer) else None
        else:
            print(f"API Error: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"Request Error: {str(e)[:200]}")
        return None

def send_to_telegram(message):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot {Config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": Config.TELEGRAM_CHANNEL_ID,
                "text": format_for_telegram(message),
                "parse_mode": "MarkdownV2",
                "disable_web_page_preview": True
            },
            timeout=15
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram Error: {e}")
        return False

def main():
    print("=== 🌟 Telegram AI Bot ===")
    print(f"🔧 Model: {Config.MODEL}")
    
    try:
        setup()
    except ValueError as e:
        print(f"❌ Config Error: {e}")
        return
    
    queries = read_queries()
    if not queries:
        print("📭 No questions in input.txt")
        return
    
    query = queries[0]
    print(f"🔍 Processing: {query[:50]}...")
    
    answer = get_ai_response(query)
    if not answer:
        print("⚠️ Failed to get answer")
        return
    
    print(f"📝 Answer preview:\n{answer[:100]}...")
    
    if send_to_telegram(answer):
        print("✅ Successfully posted to Telegram")
        # Remove processed question
        with open("input.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open("input.txt", "w", encoding="utf-8") as f:
            f.writelines(lines[1:])
    else:
        print("❌ Failed to post")

if __name__ == "__main__":
    main()