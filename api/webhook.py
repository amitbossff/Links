from telegram import Update
from telegram.ext import Application
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Application.builder().token(BOT_TOKEN).build()

async def handler(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return {
        "statusCode": 200,
        "body": json.dumps({"ok": True})
    }
