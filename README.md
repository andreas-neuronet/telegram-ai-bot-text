# Telegram AI Text Bot

Бот для автоматической генерации текстов с помощью Mistral AI и публикации в Telegram.


**Как использовать:**
1. Создайте бота через @BotFather и получите токен
2. Добавьте бота в канал как администратора
3. Получите API ключ на OpenRouter.ai
4. Заполните `.env` файл
5. Добавьте вопросы в `input.txt`
6. Запустите `python bot.py`

**Для публикации на GitHub:**

git config --global user.name "Andrey"
git config --global user.email "andreas.neuronet@gmail.com"

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/andreas-neuronet/telegram-ai-bot-text
git push -u origin main

## Настройка

1. Скопируйте проект:
```bash
git clone https://github.com/ваш_аккаунт/telegram-ai-bot-text.git
cd telegram-ai-bot-text

# Сначала получить изменения с сервера
git pull origin main

# Разрешить конфликты вручную, затем:
git add .
git commit -m "Разрешение конфликтов"
git push origin main