from flask import Flask, request
from dotenv import load_dotenv
from groq import Groq
import requests
import os

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "myverify123")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


@app.route("/")
def home():
    return "WhatsApp AI Bot Running ✅"


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


def get_ai_reply(user_message):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful WhatsApp AI assistant. Reply short and simple."
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content


def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("Send Status:", response.status_code)
    print(response.text)

    return response


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Incoming:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" in value:
            message = value["messages"][0]

            sender = message["from"]
            text = message.get("text", {}).get("body", "")

            print("From:", sender)
            print("Message:", text)

            if text:
                ai_reply = get_ai_reply(text)
            else:
                ai_reply = "Sorry, abhi main sirf text messages samajh sakta hoon."

            print("AI Reply:", ai_reply)

            send_whatsapp_message(sender, ai_reply)

    except Exception as e:
        print("Webhook Error:", e)

    return "EVENT_RECEIVED", 200
