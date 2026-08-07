from flask import Flask, jsonify
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "bot": "Telegram Music Bot",
        "version": "2.0.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
