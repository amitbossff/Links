from fastapi import FastAPI

app = FastAPI()

@app.post("/webhook")
async def webhook():
    return {"ok": True}
