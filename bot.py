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

def escape_markdown(text):
    """Альтернативная функция экранирования Markdown"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def format_for_telegram(text):
    """Безопасное форматирование текста для Telegram MarkdownV2"""
    if not text:
        return ""
    
    # Экранируем все спецсимволы MarkdownV2
    text = escape_markdown(text)
    
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

# ... (остальные функции остаются без изменений) ...

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