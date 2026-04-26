from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from dotenv import load_dotenv
import os
import httpx
from claude_agent import generate_reply
from database import init_db, add_client, get_client, get_all_clients, delete_client

load_dotenv()
app = FastAPI()
init_db()

conversation_store: dict[str, list] = {}

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return PlainTextResponse(content=params.get("hub.challenge"))
    return {"error": "invalid verify token"}

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print(f"Incoming: {data}")

    try:
        for entry in data.get("entry", []):
            page_id = str(entry.get("id", ""))
            client = get_client(page_id)

            if not client:
                print(f"Unknown page_id: {page_id}")
                continue

            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                message_text = messaging.get("message", {}).get("text", "")

                if not message_text:
                    continue

                conv_key = f"{page_id}_{sender_id}"
                history = conversation_store.get(conv_key, [])
                reply = generate_reply(message_text, history, client["sheet_id"])

                history.append({"role": "user", "content": message_text})
                history.append({"role": "assistant", "content": reply})
                conversation_store[conv_key] = history[-10:]

                async with httpx.AsyncClient() as http:
                    response = await http.post(
                        "https://graph.facebook.com/v19.0/me/messages",
                        params={"access_token": client["page_token"]},
                        json={
                            "recipient": {"id": sender_id},
                            "message": {"text": reply}
                        }
                    )
                    print(f"FB response: {response.status_code} {response.text}")

    except Exception as e:
        print(f"შეცდომა: {e}")

    return {"status": "ok"}

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(password: str = ""):
    if password != ADMIN_PASSWORD:
        return """
        <html><body style="font-family:Arial;padding:20px">
        <h2>Admin Panel</h2>
        <form>
            Password: <input name="password" type="password">
            <button type="submit">Login</button>
        </form>
        </body></html>
        """

    clients = get_all_clients()
    rows = ""
    for c in clients:
        status = "✅ Active" if c[4] else "❌ Inactive"
        rows += f"<tr><td>{c[0]}</td><td>{c[2]}</td><td>{c[1]}</td><td>{status}</td><td>{c[4]}</td></tr>"

    return f"""
    <html><body style="font-family:Arial;padding:20px">
    <h2>🏠 Samaklero Agent — Admin Panel</h2>
    <h3>კლიენტების დამატება</h3>
    <form method="post" action="/admin/add?password={password}">
        კომპანია: <input name="company_name" placeholder="Dream Home Batumi"><br><br>
        Page ID: <input name="page_id" placeholder="1146672688530304"><br><br>
        Page Token: <input name="page_token" style="width:400px" placeholder="EAAU..."><br><br>
        Sheet ID: <input name="sheet_id" placeholder="10FCM5cR..."><br><br>
        <button type="submit" style="background:#1a73e8;color:white;padding:10px 20px;border:none;cursor:pointer">
            ➕ კლიენტის დამატება
        </button>
    </form>
    <br>
    <h3>კლიენტების სია</h3>
    <table border="1" cellpadding="8" style="border-collapse:collapse">
        <tr style="background:#1a73e8;color:white">
            <th>ID</th><th>კომპანია</th><th>Page ID</th><th>სტატუსი</th><th>თარიღი</th>
        </tr>
        {rows}
    </table>
    </body></html>
    """

@app.post("/admin/add")
async def add_client_endpoint(request: Request, password: str = ""):
    if password != ADMIN_PASSWORD:
        return {"error": "unauthorized"}
    form = await request.form()
    add_client(
        page_id=form.get("page_id"),
        page_token=form.get("page_token"),
        sheet_id=form.get("sheet_id"),
        company_name=form.get("company_name")
    )
    return PlainTextResponse(f"""
        <html><body style="font-family:Arial;padding:20px">
        <h2>✅ კლიენტი დაემატა!</h2>
        <a href="/admin?password={password}">← უკან</a>
        </body></html>
    """, media_type="text/html")

@app.get("/")
async def health():
    return {"status": "samaklero multi-tenant agent v2 running 🏠"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
