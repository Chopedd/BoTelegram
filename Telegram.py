import requests
import time

TOKEN = "8744407519:AAFPzWheBRkBOMqToRZ1IcfvE5zaLxadUVo"
URL = f"https://api.telegram.org/bot{TOKEN}/"
offset = 0

def recibir_mensaje(): 
    global offset
    try:
        response = requests.get(f"{URL}getUpdates", params={"offset": offset, "timeout": 10})
        data = response.json()
        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                offset = update["update_id"] + 1
                
                # Clic en botón (Callback Query)
                if "callback_query" in update:
                    chat_id = update["callback_query"]["message"]["chat"]["id"]
                    texto = update["callback_query"]["data"]
                    msg_id = update["callback_query"]["message"]["message_id"]
                    # Retornamos texto, chat_id, msg_id y TRUE (es un callback)
                    return texto, chat_id, msg_id, True
                
                # Texto escrito manualmente por el usuario
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    texto = update["message"]["text"]
                    msg_id = update["message"]["message_id"]
                    # Retornamos texto, chat_id, msg_id y FALSE (no es un callback)
                    return texto, chat_id, msg_id, False
                    
        return None
    except Exception as e:
        print(f"Error en Telegram: {e}")
        return None

def borrar_mensaje(chat_id, message_id):
    requests.post(f"{URL}deleteMessage", json={"chat_id": chat_id, "message_id": message_id})

def enviar_mensaje_botones(chat_id, texto, botones):
    # Convertimos el diccionario a formato de botones de Telegram
    keyboard = []
    fila = []
    for k, v in botones.items():
        fila.append({"text": k, "callback_data": v})
    keyboard.append(fila)
    
    payload = {
        "chat_id": chat_id, 
        "text": texto, 
        "parse_mode": "HTML", 
        "reply_markup": {"inline_keyboard": keyboard}
    }
    res = requests.post(f"{URL}sendMessage", json=payload).json()
    return res['result']['message_id'] if 'result' in res else None

def editar_mensaje_botones(chat_id, message_id, texto, botones):
    keyboard = []
    fila = []
    for k, v in botones.items():
        fila.append({"text": k, "callback_data": v})
    keyboard.append(fila)
    
    payload = {
        "chat_id": chat_id, 
        "message_id": message_id, 
        "text": texto, 
        "parse_mode": "HTML", 
        "reply_markup": {"inline_keyboard": keyboard}
    }
    requests.post(f"{URL}editMessageText", json=payload)

def editar_progreso(chat_id, message_id, texto):
    """Edita el texto y elimina los botones (uso durante el procesamiento)"""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": texto,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": []} 
    }
    requests.post(f"{URL}editMessageText", json=payload)