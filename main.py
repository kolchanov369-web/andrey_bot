#!/usr/bin/env python3
# Telegram quest bot "Андрей, ты в игре!" (русский, с фото, уведомление администратору)

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")  # Вставь свой токен
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "YOUR_TELEGRAM_ID")  # Вставь свой Telegram ID

# Задания
TASKS = [
    {"text": "Сделай селфи, стоя на голове с максимально ржачным и идиотским лицом и отправь сюда🤳 Это для того, чтобы мы убедились, что это ты🤣", "button": None},
    {"text": 'Молодцом, ты уверенно двигаешься🚀 Отправь сообщение пятерым своим друзьям с текстом "Я по серьезному отмечаю свой ДР! Это вам не хиханьки хаханьки🔥" и прикрепи селфи, где ты стоишь на голове и жми кнопку «ЕХАЛИ ДАЛЬШЕ»🤪', "button": "ЕХАЛИ ДАЛЬШЕ"},
    {"text": 'Далее тебя ждет подсказка, чтобы найти свой подарок💰 Эта подсказка находится во дворе под лавкой. Найди её🕵️‍♂️ Только после того, как найдешь, жми кнопку "НАШЁЛ"', "button": "НАШЁЛ"},
    {"text": 'Это была шутка, никаких подсказок нет 🤣. Жми "ХОЧУ ПОДАРОК", если всё еще хочешь получить подарок!', "button": "ХОЧУ ПОДАРОК"},
    {"text": 'Последнее задание и супер приз твой 🎁 Скинь номер карты и три цифры на обороте! Шутка🤣 Пожелай себе всего того, чего бы ты хотел достичь, всего того, что делает тебя счастливым и наблюдай как всё это начнет происходить в течении трех месяцев✨ И жми «Я СЧАСТЛИВЫЙ ЧЕЛ».', "button": "Я СЧАСТЛИВЫЙ ЧЕЛ"},
]

# Сессии пользователей
SESSIONS = {}  # tg_id: task_index

def get_keyboard(button_text):
    if not button_text:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton(button_text, callback_data=button_text)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    SESSIONS[tg_id] = 0
    keyboard = get_keyboard("ПОЕХАЛИ")
    await update.message.reply_text("Андрей, ты в игре😎 Жми «ПОЕХАЛИ» и поехали🚀", reply_markup=keyboard)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = query.from_user.id
    idx = SESSIONS.get(tg_id, 0)

    # Проверка какой кнопки нажали
    if idx < len(TASKS):
        expected_button = TASKS[idx]["button"]
        if expected_button is None or query.data == expected_button or query.data == "ПОЕХАЛИ":
            idx += 1
            SESSIONS[tg_id] = idx
            if idx < len(TASKS):
                next_task = TASKS[idx]
                await query.message.reply_text(next_task["text"], reply_markup=get_keyboard(next_task["button"]))
            else:
                # Последнее сообщение
                await query.message.reply_text("Поздравляем! Ты прошел игру👍 Ожидай подарок 🎁")
                # Уведомление админу
                if ADMIN_CHAT_ID:
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Пользователь {tg_id} прошел игру!")
        else:
            await query.message.reply_text("Пожалуйста, нажми правильную кнопку, чтобы продолжить.")
    else:
        await query.message.reply_text("Игра завершена. Спасибо за участие!")

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    idx = SESSIONS.get(tg_id, 0)
    # Если это первое задание, засчитываем фото сразу
    if idx == 0:
        SESSIONS[tg_id] = 1
        next_task = TASKS[1]
        await update.message.reply_text(next_task["text"], reply_markup=get_keyboard(next_task["button"]))
    else:
        await update.message.reply_text("Фото принято!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, photo))

    print("Bot is running...")
    app.run_polling()
