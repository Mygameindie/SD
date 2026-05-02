import os

with open("bot.py", "r", encoding="utf-8") as f:
    source = f.read()

source = source.replace("bot.run('')", "bot.run(os.getenv('DISCORD_TOKEN'))")

exec(compile(source, "bot.py", "exec"))
