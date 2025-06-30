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
    """Проверка наличия всех необходимых переменных окружения"""
    required_vars = ['OPENROUTER_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID', 'MODEL']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Не задана переменная {var} в .env файле")

def escape_markdown(text):
    """Экранирование специальных символов MarkdownV2"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def format_for_telegram(text):
    """Форматирование текста для отправки в Telegram"""
    if not text:
        return ""
    
    text = escape_markdown(text)
    text = text.replace(r'\*', '*').replace(r'\_', '_')
    
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.endswith(':'):
            line = f"*{line}*"
        elif re.match(r'^\d+\.', line):
            line = f"▪️ {line}"
        elif line.startswith(('-', '•', '→')):
            line = f"• {line[1:].strip()}"
        
        lines.append(line)
    
    return '\n\n'.join(lines)

def read_queries(file_path="input.txt"):
    """Чтение вопросов из файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"📄 Ошибка чтения файла: {e}")
        return []

def is_russian(text):
    """Проверка, содержит ли текст русские буквы"""
    russian_letters = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    return any(char in russian_letters for char in text.lower())

def get_ai_response(query):
    """Получение ответа от ИИ через OpenRouter API"""
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
                    "content": "Ты - русскоязычный помощник. Форматируй ответы для Telegram с использованием MarkdownV2 (*жирный*, _курсив_)."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 600
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            return answer if is_russian(answer) else None
        print(f"⚠️ Ошибка API: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"⚠️ Ошибка запроса: {str(e)[:200]}")
        return None

def send_to_telegram(message):
    """Отправка сообщения в Telegram"""
    try:
        formatted_message = format_for_telegram(message)
        response = requests.post(
            f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": Config.TELEGRAM_CHANNEL_ID,
                "text": formatted_message,
                "parse_mode": "MarkdownV2",
                "disable_web_page_preview": True
            },
            timeout=20
        )
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ Ошибка Telegram: {e}")
        return False

def main():
    print("=== 🌟 Умный Telegram Бот ===")
    print(f"🔧 Используемая модель: {Config.MODEL}")
    
    try:
        setup()
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return
    
    queries = read_queries()
    if not queries:
        print("📭 В файле input.txt нет вопросов")
        return
    
    query = queries[0]
    print(f"🔍 Обрабатываю вопрос: {query[:50]}...")
    
    answer = get_ai_response(query)
    if not answer:
        print("⚠️ Не удалось получить ответ от ИИ")
        return
    
    print(f"📝 Предпросмотр ответа ({len(answer)} символов):\n{answer[:100]}...")
    
    if send_to_telegram(answer):
        print("✅ Сообщение успешно отправлено в Telegram")
        with open("input.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open("input.txt", "w", encoding="utf-8") as f:
            f.writelines(lines[1:])
    else:
        print("❌ Ошибка при отправке сообщения")

if __name__ == "__main__":
    main()