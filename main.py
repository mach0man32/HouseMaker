import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

# --- КОНФИГУРАЦИЯ WEBHOOK ---
TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_ДЛЯ_ТЕСТА") 
PORT = int(os.environ.get('PORT', '8080'))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# ---- ПАРСЕР ----
def parse_immowelt(city, min_price, max_price):
    url = f"https://www.immowelt.de/liste/{city}/wohnungen/mieten?price={min_price}-{max_price}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status() 

        soup = BeautifulSoup(r.text, "lxml")

        flats = []
        for item in soup.select(".EstateItem"): 
            title = item.select_one(".EstateTitle").text.strip()
            price = item.select_one(".EstatePrice").text.strip()
            link = item.select_one("a")["href"]
            flats.append(f"{title}\n{price}\nhttps://www.immowelt.de{link}")
        return flats
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе или парсинге: {e}")
        return []

# ---- ТЕЛЕГРАМ-БОТ (с гибкими фильтрами) ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /filter Город МинЦена МаксЦена (например: /filter berlin 400 800) для поиска.")

async def filter_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # 1. Проверяем, что пользователь ввел все аргументы
    if len(context.args) != 3:
        await update.message.reply_text(
            "Ошибка. Используйте формат: /filter Город МинЦена МаксЦена\nНапример: /filter berlin 400 800"
        )
        return
    
    try:
        city = context.args[0]
        min_price = int(context.args[1])
        max_price = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Цена должна быть числом!")
        return

    await update.message.reply_text(f"Ищу квартиры в {city} от {min_price}€ до {max_price}€... подожди ⏳")

    # 2. Вызываем парсер с новыми фильтрами
    flats = parse_immowelt(city, min_price, max_price)

    # 3. Отправляем результат
    if not flats:
        await update.message.reply_text("Ничего не найдено 😕")
    else:
        for flat in flats[:5]: 
            await update.message.reply_text(flat)
            
# ---- ЗАПУСК ----
def main():
    if not WEBHOOK_URL:
        # Если переменная WEBHOOK_URL не установлена (как у нас сейчас),
        # мы все равно запускаем код в режиме Webhook.
        # Render позаботится об этом. Главное, чтобы не было SyntaxError.
        pass

    # 1. Строим приложение
    # Обратите внимание: код внизу не будет выполняться, пока не будет исправлена
    # команда запуска (Start Command) в настройках Render.
    app = ApplicationBuilder().token(TOKEN).build()

    # 2. Регистрируем хэндлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("filter", filter_search))

    # 3. Запускаем в режиме Webhook для мгновенной реакции
    print(f"Запуск Webhook на порту {PORT} с URL: {WEBHOOK_URL}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN, 
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == '__main__':
    main()
    
