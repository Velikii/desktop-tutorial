import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv("/Users/macbookair/config/.env")

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ['/start', '/help'],
            ['🌤 Москва', '🌤 СПб'],
            ['📍 Хотьковский пр.9', '🌤 Нью-Йорк']
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите локацию"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    user_info = [
        f"👋 Привет, {user.first_name}!" if user.first_name else "👋 Привет!",
        f"🆔 ID: {user.id}",
        f"👤 Имя: {user.first_name} {user.last_name}" if user.last_name else f"👤 Имя: {user.first_name}",
        f"🔹 Username: @{user.username}" if user.username else "🔹 Username: не указан",
        f"📅 Сегодня: {current_date}",
        "",
        "🌍 Я ваш персональный погодный бот. Выберите локацию:"
    ]
    
    await update.message.reply_text(
        "\n".join(filter(None, user_info)),
        reply_markup=get_main_keyboard()
    )

async def handle_weather(location: str, display_name: str = None) -> str:
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={location}&lang=ru"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'error' in data:
            return f"🚫 Ошибка: {data['error']['message']}"
            
        loc = data['location']
        curr = data['current']
        
        name = display_name if display_name else f"{loc['name']}, {loc['country']}"
        
        return (
            f"🌍 {name}\n"
            f"📍 Координаты: {loc['lat']:.4f}°N, {loc['lon']:.4f}°E\n"
            f"🕒 Местное время: {loc['localtime'].split()[1]}\n\n"
            f"🌡 Температура: {curr['temp_c']}°C\n"
            f"☁️ Состояние: {curr['condition']['text']}\n"
            f"💨 Ветер: {curr['wind_kph']} км/ч\n"
            f"💧 Влажность: {curr['humidity']}%"
        )
        
    except Exception as e:
        logger.error(f"Ошибка API: {e}")
        return "⚠ Сервис временно недоступен"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if text.startswith('погода'):
        query = text[6:].strip()
        if query:
            weather = await handle_weather(query)
        else:
            weather = "Укажите город/адрес после 'погода'"
    elif text in ['москва', '🌤 москва']:
        weather = await handle_weather("Москва")
    elif text in ['спб', '🌤 спб', 'санкт-петербург']:
        weather = await handle_weather("Санкт-Петербург")
    elif text in ['хотьковский пр.9', '📍 хотьковский пр.9']:
        weather = await handle_weather("Сергиев Посад", "Хотьковский проезд, 9")
    elif text in ['нью-йорк', '🌤 нью-йорк']:
        weather = await handle_weather("Нью-Йорк")
    else:
        weather = "Используйте меню или напишите 'погода [место]'"
    
    await update.message.reply_text(
        weather,
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напишите 'погода' и название города или выберите из меню",
        reply_markup=get_main_keyboard()
    )

def main():
    if not TOKEN or not WEATHER_API_KEY:
        logger.error("Не заданы TOKEN или WEATHER_API_KEY в .env!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    logger.info("Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()