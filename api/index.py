import os
import json
import re
import requests
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

saved_text = ""
waiting_for_links = False
link_dict = {}

def send_message(chat_id, text):
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        global saved_text, waiting_for_links, link_dict

        length = int(self.headers.get("content-length", 0))
        body = json.loads(self.rfile.read(length))

        message = body.get("message")
        if not message:
            self.send_response(200)
            self.end_headers()
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        # .l command
        if text == ".l":
            reply = message.get("reply_to_message")
            if not reply or not reply.get("text"):
                send_message(chat_id, "❌ Reply to a message with `.l`")
            else:
                saved_text = reply["text"]
                waiting_for_links = True
                send_message(chat_id, "📎 Send links (digit + link)")

        # links
        elif waiting_for_links and re.search(r"https?://|deleted", text):
            link_dict.clear()
            for line in text.splitlines():
                try:
                    d, l = line.split(maxsplit=1)
                    if d.isdigit():
                        link_dict[d] = l
                except:
                    pass

            out = []
            lines = saved_text.splitlines()
            i = 0

            while i < len(lines) - 1:
                name = lines[i].replace("✅", "☑️")
                num = lines[i + 1].strip()

                if num.isdigit():
                    out.append(f"*{name}*")
                    link = link_dict.get(num, num)
                    out.append("❌" if link == "deleted" else link)
                    out.append("")
                    i += 2
                else:
                    i += 1

            send_message(chat_id, "\n".join(out))
            waiting_for_links = False

        # .p command
        elif text == ".p":
            reply = message.get("reply_to_message")
            if reply and reply.get("text"):
                res = []
                for line in reply["text"].splitlines():
                    line = re.sub(r"^0?(\d+)\.", r"\1", line)
                    res.append(line.strip())
                send_message(chat_id, "\n".join(res))

        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot running")
