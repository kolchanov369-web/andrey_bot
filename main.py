import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # твой Telegram ID

# Храним состояния пользователей
user_states = {}

# Возможные состояния
STATE_START = "start"
STATE_PHOTO = "photo"
STATE_DONE = "done"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение"""
    keyboard = [[InlineKeyboardButton("ПОЕХАЛИ 🚀", callback_data="go")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Андрей, ты в игре😎 Жми «ПОЕХАЛИ» и поехали🚀", reply_markup=reply_markup
    )
    user_states[update.effective_user.id] = STATE_START


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "go":
        user_states[user_id] = STATE_PHOTO
        await query.message.reply_text(
            "Сделай селфи, стоя на голове, с максимально ржачным и идиотским лицом 🤳 "
            "Это нужно, чтобы мы убедились, что это ты 🤣"
        )

    elif query.data == "next":
        await query.message.reply_text(
            "Молодцом, ты уверенно двигаешься🚀\n\n"
            "Отправь сообщение пятерым своим друзьям с текстом:\n"
            "\"Я по серьезному отмечаю свой ДР! Это вам не хиханьки хаханьки🔥\"\n\n"
            "и прикрепи селфи, где ты стоишь на голове. Потом жми «ЕХАЛИ ДАЛЬШЕ» 🤪"
        )
        keyboard = [[InlineKeyboardButton("ЕХАЛИ ДАЛЬШЕ 🤪", callback_data="next2")]]
        await query.message.reply_text(
            "Когда сделаешь — жми кнопку👇", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "next2":
        await query.message.reply_text(
            "Далее тебя ждет подсказка, чтобы найти свой подарок💰\n"
            "Эта подсказка находится во дворе под лавкой. Найди её🕵️‍♂️\n"
            "Только после того, как найдешь, жми кнопку «НАШЁЛ»."
        )
        keyboard = [[InlineKeyboardButton("НАШЁЛ 🕵️‍♂️", callback_data="found")]]
        await query.message.reply_text(
            "Когда найдёшь — жми👇", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "found":
        keyboard = [[InlineKeyboardButton("НАШЁЛ 🕵️‍♂️", callback_data="found2")]]
        await query.message.reply_text(
            "Ты нажал кнопку «НАШЁЛ», но это не так, я слежу за тобой😎\n"
            "Иди ищи снова! После того, как найдёшь, жми «НАШЁЛ» 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "found2":
        keyboard = [[InlineKeyboardButton("ХОЧУ ПОДАРОК 🎁", callback_data="gift")]]
        await query.message.reply_text(
            "Это была шутка, никаких подсказок нет 🤣.\n"
            "Жми «ХОЧУ ПОДАРОК», если всё ещё хочешь получить подарок!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "gift":
        keyboard = [[InlineKeyboardButton("Я СЧАСТЛИВЫЙ ЧЕЛ 😎", callback_data="finish")]]
        await query.message.reply_text(
            "Последнее задание и супер приз твой 🎁\n\n"
            "Отправь номер карты и три цифры на обороте карты! Шутка 🤪 Пожелай себе всего того, чего бы ты хотел достичь, "
            "всего того, что делает тебя счастливым, и наблюдай, "
            "как всё это начнёт происходить в течение трёх месяцев ✨ И жми «Я СЧАСТЛИВЫЙ ЧЕЛ»",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "finish":
        await query.message.reply_text(
            "Поздравляем! Ты прошёл игру👍 Ожидай подарок 🎁"
        )
        if ADMIN_ID:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"{query.from_user.first_name} прошёл игру! 🎉"
            )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото от пользователя"""
    user_id = update.effective_user.id

    if user_states.get(user_id) == STATE_PHOTO:
        await update.message.reply_text("Отлично, фото получено! 🤣")
        keyboard = [[InlineKeyboardButton("ЕХАЛИ ДАЛЬШЕ 🤪", callback_data="next")]]
        await update.message.reply_text(
            "Теперь жми кнопку👇", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        user_states[user_id] = STATE_DONE
    else:
        await update.message.reply_text(
            "Это фото не к месту 😅 Жми /start, чтобы начать игру заново."
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running via webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://andrey-bot.onrender.com/{BOT_TOKEN}"
    )
