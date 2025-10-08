#!/usr/bin/env python3
# Telegram quest bot "Андрей, ты в игре!" (русский, с фото, уведомление администратору)

import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

# База данных
conn = sqlite3.connect("game.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS sessions (
    tg_id INTEGER PRIMARY KEY,
    payload TEXT,
    state INTEGER,
    photo_received INTEGER DEFAULT 0,
    wish TEXT DEFAULT ''
)""")
conn.commit()

def get_session(tg_id):
    cur.execute("SELECT payload, state, photo_received, wish FROM sessions WHERE tg_id=?", (tg_id,))
    r = cur.fetchone()
    if r:
        return {"payload": r[0], "state": r[1], "photo_received": bool(r[2]), "wish": r[3] or ""}
    return None

def create_session(tg_id, payload):
    cur.execute("INSERT OR REPLACE INTO sessions(tg_id,payload,state,photo_received,wish) VALUES(?,?,?,?,?)",
                (tg_id, payload, 0, 0, ""))
    conn.commit()

def set_state(tg_id, state):
    cur.execute("UPDATE sessions SET state=? WHERE tg_id=?", (state, tg_id))
    conn.commit()

def mark_photo(tg_id):
    cur.execute("UPDATE sessions SET photo_received=1 WHERE tg_id=?", (tg_id,))
    conn.commit()

def save_wish(tg_id, wish):
    cur.execute("UPDATE sessions SET wish=? WHERE tg_id=?", (wish, tg_id))
    conn.commit()

# Кнопки
def kb_start():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Начать игру", callback_data="start_game")]])
def kb_done():
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Задание выполнено", callback_data="done")]])
def kb_next(label="Дальше"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data="next")]])
def kb_better():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Ближе", callback_data="closer")]])
def kb_final():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎉 Все задания выполнены", callback_data="all_done")]])

# Обработчики
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    payload = args[0] if args else ""
    tg_id = update.effective_user.id
    create_session(tg_id, payload)
    text = "🎮 *Андрей, ты в игре!*\n\nКвест начнётся прямо сейчас. Готов?"
    await update.message.reply_text(text, reply_markup=kb_start(), parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = query.from_user.id
    session = get_session(tg_id)
    if not session:
        create_session(tg_id, "")
        session = get_session(tg_id)
    data = query.data
    if data == "start_game":
        set_state(tg_id, 0)
        await query.message.reply_text("📸 *Задание 1:*\nСделай селфи, стоя на голове, с максимально ржачным идиотским лицом и отправь сюда.", parse_mode='Markdown')
    elif data == "done":
        state = session["state"]
        if state == 0:
            if session["photo_received"]:
                set_state(tg_id,1)
                await query.message.reply_text("👍 Отлично! Задание 1 принято.\n\n💬 *Задание 2:*\nОтправь сообщение пятерым друзьям с текстом:\n\"Я по серьезному отмечаю свой ДР. Это вам не хиханьки хаханьки.\"\nПрикрепи селфи, где ты стоишь на голове.\nПосле этого нажми кнопку 'Задание выполнено'.", reply_markup=kb_done(), parse_mode='Markdown')
            else:
                await query.message.reply_text("⚠️ Похоже, мы ещё не получили селфи. Пришли фото.")
        elif state == 1:
            set_state(tg_id,2)
            await query.message.reply_text("📍 Далее тебя ждет подсказка, чтобы найти свой подарок. Она находится во дворе под лавкой.\nПосле этого нажми 'Задание выполнено'.", reply_markup=kb_done())
        elif state == 2:
            set_state(tg_id,3)
            await query.message.reply_text("🤣 Ха-ха, это была шутка — никаких подсказок нет.\nЕсли хочешь получить супер приз — жми 'Ближе'.", reply_markup=kb_better())
    elif data=="next" or data=="closer":
        set_state(tg_id,4)
        await query.message.reply_text("🎉 Поздравляю! Твой подарок почти в твоих руках!\n\n*Последнее задание:*\nПожелай себе всего того, чего бы ты хотел достичь, всего того, что делает тебя счастливым и наблюдай, как всё это начнёт происходить в течение трёх месяцев!\n\nИ жми далее.", reply_markup=kb_final(), parse_mode='Markdown')
    elif data=="all_done":
        set_state(tg_id,99)
        await query.message.reply_text("🎊 Поздравляю! Ты прошёл квест. Спасибо за участие — ожидай подарок!")
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(int(ADMIN_CHAT_ID), f"🎉 Андрей прошёл квест и нажал кнопку 'Все задания выполнены'! (id={tg_id})")
            except: pass

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    session = get_session(tg_id)
    if not session:
        await update.message.reply_text("Отправь /start чтобы начать игру.")
        return
    photos = update.message.photo
    if photos:
        file = photos[-1].get_file()
        path = f"photos/{tg_id}"
        import os as _os
        _os.makedirs(path, exist_ok=True)
        filename = f"{path}/{file.file_id}.jpg"
        await file.download_to_drive(filename)
        mark_photo(tg_id)
        await update.message.reply_text("📸 Фото принято! Нажми 'Задание выполнено'.", reply_markup=kb_done())
    else:
        await update.message.reply_text("⚠️ Пожалуйста, пришли фото (не стикер).")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    session = get_session(tg_id)
    if not session:
        await update.message.reply_text("Отправь /start чтобы начать игру.")
        return
    state = session["state"]
    text = (update.message.text or "").strip()
    if state==4:
        save_wish(tg_id,text)
        await update.message.reply_text("✅ Пожелание сохранено. Нажми 'Все задания выполнены'.", reply_markup=kb_final())
    else:
        await update.message.reply_text("Используй кнопки или пришли фото, если просят.")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Инструкции:\n/start - начать игру")

def ensure_dirs():
    import os
    os.makedirs("photos", exist_ok=True)

def main():
    ensure_dirs()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))
    app.add_handler(CommandHandler("help", cmd_help))
    print("Bot is running...")
    app.run_polling()

if __name__=="__main__":
    main()
