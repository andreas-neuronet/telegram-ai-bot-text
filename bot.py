import os
import time
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

def clean_text(text):
    if not text:
        return ""
    for char in ['*', '_', '[', ']', '`']:
        text = text.replace(char, '')
    return text.strip()

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
                    "content": "Ты - русскоязычный помощник. Отвечай только на русском. Ответ должен быть 200-500 символов."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            answer = clean_text(response.json()['choices'][0]['message']['content'])
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
        print(f"Telegram Error: {e}")
        return False

def main():
    print("=== Telegram AI Bot ===")
    print(f"Model: {Config.MODEL}")
    
    try:
        setup()
    except ValueError as e:
        print(f"Config Error: {e}")
        return
    
    queries = read_queries()
    if not queries:
        print("❌ No questions in input.txt")
        return
    
    query = queries[0]
    print(f"🔍 Processing: {query[:50]}...")
    
    answer = get_ai_response(query)
    if not answer:
        print("⚠️ Failed to get answer")
        return
    
    print(f"📝 Answer ({len(answer)} chars): {answer[:50]}...")
    
    if send_to_telegram(answer):
        print("✅ Posted to Telegram")
        # Remove processed question
        with open("input.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open("input.txt", "w", encoding="utf-8") as f:
            f.writelines(lines[1:])
    else:
        print("❌ Failed to post")

if __name__ == "__main__":
    main()