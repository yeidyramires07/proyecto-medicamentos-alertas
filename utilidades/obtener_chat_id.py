import os
import requests

token = os.environ["TELEGRAM_TOKEN"]
r = requests.get("https://api.telegram.org/bot" + token + "/getUpdates", timeout=20)
datos = r.json()
print("ok:", datos.get("ok"))
for u in datos.get("result", []):
    m = u.get("message")
    if m:
        print("chat_id:", m["chat"]["id"], "| nombre:", m["chat"].get("first_name"))