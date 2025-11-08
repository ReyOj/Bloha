import os
from flask import Flask, request, jsonify
import hashlib
import hmac
import json
import requests
import random
import time
import git
from commands import get_reply

app = Flask(__name__)

VK_CONFIRMATION = os.environ.get("VK_CONFIRMATION", "50effcd8")
#VK_SECRET = os.environ.get("VK_SECRET")
VK_GROUP_TOKEN = os.environ.get("VK_GROUP_TOKEN", "")
VK_API = "https://api.vk.com/method/"
VK_VERSION = os.environ.get("VK_VERSION", "5.131")

def secure_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())

def vk_send(peer_id: int, text: str):
    """Отправка сообщения: peer_id работает и для ЛС, и для бесед."""
    if not VK_GROUP_TOKEN:
        app.logger.error("VK_GROUP_TOKEN is not set in environment - cannot send messages")
        raise RuntimeError("VK_GROUP_TOKEN not configured")

    payload = {
        "access_token": VK_GROUP_TOKEN,
        "v": VK_VERSION,
        "peer_id": peer_id,
        "random_id": int(time.time() * 1000) + random.randint(1, 999),
        "message": text,
    }
    r = requests.post(VK_API + "messages.send", data=payload, timeout=10)
    try:
        r.raise_for_status()
    except Exception as e:
        app.logger.error(f"[send] HTTP error: {e}; body={r.text}")
        raise
    data = r.json()
    if "error" in data:
        app.logger.error(f"[send] VK error: {data}")
        raise RuntimeError(data)

@app.route("/")
def index():
    return "ok"

#лютый вебхук для обновления кода из гита
@app.route("/update_server", methods=["POST"])
def webhook():
    if request.method == "POST":
        repo = git.Repo(os.getcwd())
        origin = repo.remotes.origin
        origin.pull()
        print("[update] repository updated")
        return "ok"
    else:
        return "method not allowed", 400

# Быстрый тест исходящего интернета к VK API
@app.route("/ping_vk")
def ping_vk():
    try:
        r = requests.get(
            VK_API + "utils.getServerTime",
            params={"v": VK_VERSION},
            timeout=10
        )
        return r.text, r.status_code, {"Content-Type": "application/json; charset=utf-8"}
    except Exception as e:
        return json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json; charset=utf-8"}

@app.route("/vk", methods=["GET", "POST"])
def vk_callback():
    if request.method == "GET":
        return "ok"

    raw_body = request.get_data()  # bytes
    # Логируем входящее (без секретов)
    app.logger.warning(f"[in] headers={ {k:v for k,v in request.headers.items() if k != 'X-VK-Signature'} }")
    app.logger.warning(f"[in] body={raw_body.decode('utf-8', 'ignore')}")

    # Парсим JSON
    try:
        data = request.get_json(force=True, silent=False) or {}
    except Exception as e:
        app.logger.error(f"[json] parse error: {e}")
        return "ok"

    # Подтверждение сервера
    if data.get("type") == "confirmation":
        app.logger.warning("[confirmation] return token")
        return VK_CONFIRMATION

    # Проверка подписи (если Secret key настроен в ВК)
#    if VK_SECRET:
#        vk_signature = request.headers.get("X-VK-Signature")
#        calc = hmac.new(VK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
#        if not vk_signature or not secure_compare(vk_signature, calc):
#            app.logger.error(f"[sig] mismatch: header={vk_signature}, calc={calc}")
#            return "signature mismatch", 403

    # Обработка сообщений
    if data.get("type") == "message_new":
        obj = data.get("object") or {}
        msg = obj.get("message") or {}
        text = msg.get("text", "")
        peer_id = msg.get("peer_id")
        from_id = msg.get("from_id")

        app.logger.warning(f"[msg] peer_id={peer_id} from_id={from_id} text={text!r}")

        if isinstance(text, str) and isinstance(peer_id, int):
            try:
                reply = get_reply(text)  # Optional[str]
                if reply is not None:
                    app.logger.warning(f"[reply] -> {reply!r}")
                    vk_send(peer_id, reply)
                else:
                    app.logger.warning("[reply] no command detected -> ignore")
            except Exception as e:
                app.logger.error(f"[send] failed: {e}")
        else:
            app.logger.error("[msg] invalid payload structure")


    # Всегда подтверждаем обработку
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))