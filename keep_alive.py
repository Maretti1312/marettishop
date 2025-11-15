"""
Skrypt do utrzymywania bota przy życiu na Render.com
Render usypia darmowe serwisy po 15 min braku aktywności.
Ten skrypt tworzy prosty serwer HTTP, który można pingować.
"""
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Boty Telegram działają! 🤖"

@app.route('/health')
def health():
    return {"status": "ok", "bots": "running"}

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()