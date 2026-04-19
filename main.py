import sqlite3
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Состояния для ConversationHandler
REAL_NAME, NICKNAME, TROPHIES = range(3)

# Создание базы данных
def init_db():
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            real_name TEXT,
            nickname TEXT,
            trophies INTEGER,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Сохранение игрока в БД
def save_player(user_id, username, real_name, nickname, trophies):
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO players (user_id, username, real_name, nickname, trophies)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, real_name, nickname, trophies))
    conn.commit()
    conn.close()

# Проверка, зарегистрирован ли игрок
def is_registered(user_id):
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Получение данных игрока
def get_player(user_id):
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    cursor.execute('SELECT real_name, nickname, trophies FROM players WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_registered(user_id):
        player_data = get_player(user_id)
        await update.message.reply_text(
            f"✅ Вы уже зарегистрированы!\n\n"
            f"👤 Реальное имя: {player_data[0]}\n"
            f"🎮 Ник в игре: {player_data[1]}\n"
            f"🏆 Кубки: {player_data[2]}\n\n"
            f"Используйте /profile для просмотра профиля\n"
            f"Используйте /update для обновления данных"
        )
    else:
        await update.message.reply_text(
            "🌟 Добро пожаловать в игру! 🌟\n\n"
            "Для регистрации нужно указать:\n"
            "1️⃣ Фио\n"
            "2️⃣ Ваш ник в игре\n"
            "3️⃣ Количество кубков\n\n"
            "Нажмите /register чтобы начать регистрацию"
        )

# Начало регистрации
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_registered(user_id):
        await update.message.reply_text("Вы уже зарегистрированы! Используйте /update для обновления данных")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 Давайте познакомимся!\n\n"
        "Введите ваше ФИО:"
    )
    return REAL_NAME

# Получение реального имени
async def get_real_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    real_name = update.message.text
    context.user_data['real_name'] = real_name
    
    await update.message.reply_text(
        f"Приятно познакомиться, {real_name}! 🤝\n\n"
        f"Теперь введите ваш ник в игре:"
    )
    return NICKNAME

# Получение ника
async def get_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nickname = update.message.text
    context.user_data['nickname'] = nickname
    
    await update.message.reply_text(
        f"Отлично! Ник: {nickname}\n\n"
        f"Теперь введите количество кубков (только число):"
    )
    return TROPHIES

# Получение кубков и сохранение
async def get_trophies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        trophies = int(update.message.text)
        if trophies < 0:
            await update.message.reply_text("❌ Кубки не могут быть отрицательными! Введите корректное число:")
            return TROPHIES
            
        user_id = update.effective_user.id
        username = update.effective_user.username or "Не указан"
        real_name = context.user_data['real_name']
        nickname = context.user_data['nickname']
        
        # Сохраняем в БД
        save_player(user_id, username, real_name, nickname, trophies)
        
        await update.message.reply_text(
            f"✅ Регистрация успешно завершена!\n\n"
            f"📊 Ваши данные:\n"
            f"👤 Реальное имя: {real_name}\n"
            f"🎮 Ник в игре: {nickname}\n"
            f"🏆 Кубки: {trophies}\n\n"
            f"Используйте /profile для просмотра профиля"
        )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите число! Количество кубков должно быть числом:")
        return TROPHIES

# Просмотр профиля
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text("❌ Вы не зарегистрированы! Используйте /register")
        return
    
    player_data = get_player(user_id)
    await update.message.reply_text(
        f"👤 Ваш профиль:\n\n"
        f"📝 Реальное имя: {player_data[0]}\n"
        f"🎮 Ник в игре: {player_data[1]}\n"
        f"🏆 Кубки: {player_data[2]}\n"
        f"🆔 ID Telegram: {user_id}"
    )

# Обновление данных
async def update_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text("❌ Вы не зарегистрированы! Используйте /register")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🔄 Обновление данных.\n\n"
        "Введите ваше реальное имя:"
    )
    return REAL_NAME

# Отмена регистрации
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Операция отменена.")
    return ConversationHandler.END

# Команда для топ игроков
async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT real_name, nickname, trophies 
        FROM players 
        ORDER BY trophies DESC 
        LIMIT 10
    ''')
    top = cursor.fetchall()
    conn.close()
    
    if not top:
        await update.message.reply_text("📭 Пока нет зарегистрированных игроков")
        return
    
    message = "🏆 ТОП-10 игроков по кубкам:\n\n"
    for i, (real_name, nickname, trophies) in enumerate(top, 1):
        message += f"{i}. {real_name} (@{nickname}) - {trophies} 🏆\n"
    
    await update.message.reply_text(message)

# Команда для просмотра всех игроков
async def list_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('players.db')
    cursor = conn.cursor()
    cursor.execute('SELECT real_name, nickname, trophies FROM players ORDER BY registered_at')
    players = cursor.fetchall()
    conn.close()
    
    if not players:
        await update.message.reply_text("📭 Нет зарегистрированных игроков")
        return
    
    message = "📋 Список всех игроков:\n\n"
    for real_name, nickname, trophies in players:
        message += f"👤 {real_name} | Ник: {nickname} | 🏆 {trophies}\n"
    
    await update.message.reply_text(message)

# Команда помощи
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/register - Зарегистрироваться\n"
        "/profile - Посмотреть свой профиль\n"
        "/update - Обновить свои данные\n"
        "/top - Топ-10 игроков по кубкам\n"
        "/list - Список всех игроков\n"
        "/help - Показать эту справку\n"
        "/cancel - Отменить текущую операцию"
    )

def main():
    # Инициализация БД
    init_db()
    
    # Замени 'YOUR_BOT_TOKEN' на токен твоего бота
    TOKEN = '8640024264:AAFCTzQnQvSQQK3lFdyGgrmLTaeHPIK1A9Y'
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler для регистрации
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register)],
        states={
            REAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_real_name)],
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nickname)],
            TROPHIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_trophies)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Conversation handler для обновления
    update_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('update', update_data)],
        states={
            REAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_real_name)],
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nickname)],
            TROPHIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_trophies)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(conv_handler)
    application.add_handler(update_conv_handler)
    application.add_handler(CommandHandler('profile', profile))
    application.add_handler(CommandHandler('top', top_players))
    application.add_handler(CommandHandler('list', list_players))
    
    # Запускаем бота
    print("🤖 Бот запущен и готов к работе...")
    print("Нажми Ctrl+C для остановки")
    application.run_polling()

if __name__ == '__main__':
    main()