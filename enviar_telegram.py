import os
import requests

def enviar_telegram(chat_id, texto):
    token = os.environ["TELEGRAM_TOKEN"]
    r = requests.post("https://api.telegram.org/bot" + token + "/sendMessage", data={"chat_id": chat_id, "text": texto}, timeout=20)
    return r.json()

if __name__ == "__main__":
    resp = enviar_telegram(os.environ["TELEGRAM_CHAT_ID"], "ALERTA Alta: prueba del sistema de alertas de medicamentos.")
    print("ok:", resp.get("ok"))