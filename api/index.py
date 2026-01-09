import os
import re
import json
import asyncio
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002822914255

# ⚠️ Own use ke liye simple global state
saved_text = ""
waiting_for_links = False
link_dict = {}

# ========== .l ==========
async def save_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_text, waiting_for_links

    msg = update.message
    if not msg or msg.chat_id != GROUP_ID:
        return

    if not msg.reply_to_message or not msg.reply_to_message.text:
        await msg.reply_text("❌ Reply to a message with `.l`")
        return

    saved_text = msg.reply_to_message.text.strip()
    waiting_for_links = True
    await msg.reply_text("📎 Send links (digit + link)")

# ========== LINKS ==========
async def process_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_links, saved_text, link_dict

    if not waiting_for_links:
        return

    msg = update.message
    if not msg or msg.chat_id != GROUP_ID:
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

    out = []
    lines = saved_text.splitlines()
    i = 0

    while i < len(lines) - 1:
        name = lines[i].strip()
        num = lines[i + 1].strip()

        if num.isdigit():
            name = name.replace("✅", "☑️")
            out.append(f"*{name}*")

            link = link_dict.get(num)
            if not link:
                out.append(num)
            elif link.lower() == "deleted":
                out.append("❌")
            else:
                out.append(link)

            out.append("")
            i += 2
        else:
            i += 1

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text="\n".join(out),
        parse_mode="Markdown"
    )

    waiting_for_links = False

# ========== .p ==========
async def list_formatter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.reply_to_message or not msg.reply_to_message.text:
        await msg.reply_text("❌ Kisi list ko reply karke .p use karo")
        return

    res = []
    for line in msg.reply_to_message.text.splitlines():
        line = re.sub(r"^0?(\d+)\.", r"\1", line)
        res.append(line.strip())

    await msg.reply_text("\n".join(res))

# ========== APP ==========
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.Regex(r'^\.l$'), save_post))
app.add_handler(MessageHandler(filters.Regex(r'^\.p$'), list_formatter))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_links))

# ========== VERCEL HANDLER ==========
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length)

        update = Update.de_json(json.loads(body), app.bot)
        asyncio.run(app.process_update(update))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
