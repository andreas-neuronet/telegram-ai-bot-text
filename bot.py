import os
import time
import requests
import json
from dotenv import load_dotenv

# Загрузка конфигурации
load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
    MODEL = os.getenv('MODEL')

def setup():
    """Проверка настроек"""
    required_vars = ['OPENROUTER_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID', 'MODEL']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Не задана переменная {var} в .env файле")

def clean_text(text):
    """Очистка текста от форматирования"""
    if not text:
        return ""
    for char in ['*', '_', '[', ']', '`']:
        text = text.replace(char, '')
    return text.strip()

def read_queries(file_path="input.txt"):
    """Чтение вопросов из файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return []

def is_russian(text):
    """Проверка русского языка"""
    russian_letters = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    text_lower = text.lower()
    return any(char in russian_letters for char in text_lower)

def get_ai_response(query):
    """Запрос к AI модели через OpenRouter API"""
    try:
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/yourusername/telegram-ai-bot-text",
            "X-Title": "Telegram AI Bot",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": Config.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты - русскоязычный помощник. Отвечай только на русском. Формат: чистый текст без разметки. Длина: 200-500 символов."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            answer = clean_text(answer)
            return answer if is_russian(answer) else None
        else:
            print(f"Ошибка API (код {response.status_code}): {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"Ошибка при запросе к API: {str(e)[:200]}")
        return None

def send_to_telegram(message):
    """Отправка сообщения в Telegram"""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": Config.TELEGRAM_CHANNEL_ID,
                "text": message,
                "disable_web_page_preview": True
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка Telegram: {e}")
        return False

def main():
    print("=== AI Telegram Bot ===")
    print(f"Модель: {Config.MODEL}")
    
    try:
        setup()
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
        return
    
    queries = read_queries()
    if not queries:
        print("❌ Нет вопросов в input.txt")
        return
    
    print(f"📋 Вопросов для обработки: {len(queries)}")
    
    success = 0
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 [{i}/{len(queries)}] Вопрос: {query[:50]}...")
        
        if not is_russian(query):
            print("⚠️ Пропуск: вопрос не на русском")
            continue
            
        answer = get_ai_response(query)
        if not answer:
            print("⚠️ Не удалось получить ответ")
            continue
            
        print(f"📝 Ответ ({len(answer)} символов): {answer[:50]}...")
        
        if send_to_telegram(answer):
            print("✅ Отправлено в Telegram")
            success += 1
        else:
            print("❌ Ошибка отправки")
            
        if i < len(queries):
            print("⏳ Ожидание 10 сек...")
            time.sleep(10)
    
    print(f"\n🎉 Результат: {success}/{len(queries)} отправлено")

if __name__ == "__main__":
    main()