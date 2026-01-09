import os
import re
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters
)
from http.server import BaseHTTPRequestHandler
import json
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002822914255

saved_text = ""
waiting_for_links = False
link_dict = {}

# ========== .l ==========
async def save_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_text, waiting_for_links

    message = update.message
    if message.chat_id != GROUP_ID:
        return

    if not message.reply_to_message or not message.reply_to_message.text:
        await message.reply_text("❌ Reply to a message with `.l`")
        return

    saved_text = message.reply_to_message.text.strip()
    waiting_for_links = True
    await message.reply_text("📎 Send links (digit + link)")

# ========== LINK PROCESS ==========
async def process_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_links, saved_text, link_dict

    if not waiting_for_links:
        return

    message = update.message
    if message.chat_id != GROUP_ID:
        return

    if not re.search(r'https?://|deleted', message.text or ''):
        return

    link_dict.clear()

    for line in message.text.splitlines():
        try:
            digit, link = line.split(maxsplit=1)
            if digit.isdigit():
                link_dict[digit] = link.strip()
        except:
            pass

    final_lines = []
    lines = saved_text.splitlines()
    i = 0

    while i < len(lines):
        name_line = lines[i].strip()
        if not name_line:
            i += 1
            continue

        digit_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

        if digit_line.isdigit():
            name_line = name_line.replace("✅", "☑️")
            final_lines.append(f"*{name_line}*")

            link = link_dict.get(digit_line)
            if not link:
                final_lines.append(digit_line)
            elif link.lower() == "deleted":
                final_lines.append("❌")
            else:
                final_lines.append(link)

            final_lines.append("")
            i += 2
        else:
            i += 1

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text="\n".join(final_lines),
        parse_mode="Markdown"
    )

    waiting_for_links = False

# ========== .p ==========
async def list_formatter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message.reply_to_message or not message.reply_to_message.text:
        await message.reply_text("❌ Kisi list ko reply karke .p use karo")
        return

    output = []
    for line in message.reply_to_message.text.splitlines():
        line = re.sub(r"^0([1-9])\.", r"\1", line)
        line = re.sub(r"^(\d+)\.", r"\1", line)
        output.append(line.strip())

    await message.reply_text("\n".join(output))


# ========== TELEGRAM APP ==========
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.Regex(r'^\.l$'), save_post))
app.add_handler(MessageHandler(filters.Regex(r'^\.p$'), list_formatter))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_links))


# ========== VERCEL HANDLER ==========
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)

        update = Update.de_json(json.loads(body), app.bot)

        asyncio.run(app.process_update(update))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
