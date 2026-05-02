import os
import threading
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Discord bot is running"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web_server, daemon=True).start()

with open("bot.py", "r", encoding="utf-8") as f:
    source = f.read()

source = source.replace("bot.run('')", "bot.run(os.getenv('DISCORD_TOKEN'))")

exec(compile(source, "bot.py", "exec"))
