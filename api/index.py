import os
import re
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002822914255

app = FastAPI()
telegram_app = Application.builder().token(BOT_TOKEN).build()

saved_text = ""
waiting_for_links = False
link_dict = {}

# ========== .l ==========
async def save_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_text, waiting_for_links
    msg = update.message

    if msg.chat_id != GROUP_ID:
        return

    if not msg.reply_to_message or not msg.reply_to_message.text:
        await msg.reply_text("❌ Reply to a message with `.l`")
        return

    saved_text = msg.reply_to_message.text.strip()
    waiting_for_links = True
    await msg.reply_text("📎 Send links (digit + link)")

# ========== LINK PROCESS ==========
async def process_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_links, saved_text, link_dict

    if not waiting_for_links:
        return

    msg = update.message
    if msg.chat_id != GROUP_ID:
        return

    if not re.search(r'https?://|deleted', msg.text or ''):
        return

    link_dict.clear()
    for line in msg.text.splitlines():
        try:
            d, l = line.split(maxsplit=1)
            if d.isdigit():
                link_dict[d] = l.strip()
        except:
            pass

    final = []
    lines = saved_text.splitlines()
    i = 0

    while i < len(lines):
        name = lines[i].strip()
        if not name:
            i += 1
            continue

        digit = lines[i+1].strip() if i+1 < len(lines) else ""
        if digit.isdigit():
            name = name.replace("✅", "☑️")
            final.append(f"*{name}*")

            link = link_dict.get(digit)
            if not link:
                final.append(digit)
            elif link.lower() == "deleted":
                final.append("❌")
            else:
                final.append(link)

            final.append("")
            i += 2
        else:
            i += 1

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text="\n".join(final),
        parse_mode="Markdown"
    )

    waiting_for_links = False

telegram_app.add_handler(MessageHandler(filters.Regex(r'^\.l$'), save_post))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_links))

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
