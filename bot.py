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
    """Безопасное форматирование текста для Telegram MarkdownV2"""
    if not text:
        return ""
    
    # Экранируем все спецсимволы MarkdownV2
    text = re.escape_markdown(text)
    
    # Восстанавливаем нужное нам форматирование
    text = text.replace(r'\*', '*').replace(r'\_', '_')
    
    # Форматируем заголовки и списки
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Заголовки (строка заканчивается на :)
        if line.endswith(':'):
            line = f"*{line}*"
        # Нумерованные списки (1., 2. и т.д.)
        elif re.match(r'^\d+\.', line):
            line = f"▪️ {line}"
        # Маркированные списки
        elif line.startswith(('-', '•', '→')):
            line = f"• {line[1:].strip()}"
        
        lines.append(line)
    
    # Добавляем разделение между абзацами
    formatted_text = '\n\n'.join(lines)
    
    # Добавляем эмодзи-префикс
    return f"📌 *Сообщение от бота:*\n\n{formatted_text}"

def read_queries(file_path="input.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"📄 File read error: {e}")
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
5. Используй форматирование:
   *Заголовки:*
   - Списки
   • Альтернативные пункты
   ▪️ Нумерованные

Пример:
*Преимущества солнечной энергии:*
✅ Экологичность
• Без вредных выбросов
▪️ 1. Долговечность
▪️ 2. Экономичность"""
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 650,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=40
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
            if is_russian(answer):
                return answer
            print("⚠️ Ответ не на русском языке")
            return None
        print(f"⚠️ API Error: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"⚠️ Request Error: {str(e)[:200]}")
        return None

def send_to_telegram(message):
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
        if response.status_code != 200:
            print(f"⚠️ Telegram API Error: {response.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")
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
        # Удаляем обработанный вопрос
        with open("input.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open("input.txt", "w", encoding="utf-8") as f:
            f.writelines(lines[1:])
    else:
        print("❌ Ошибка при отправке сообщения")

if __name__ == "__main__":
    main()