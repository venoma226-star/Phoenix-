import os
import discord
from discord.ext import commands
from flask import Flask
import threading
import random

# -------------------- Flask Server --------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Phoenix is alive..."

threading.Thread(target=lambda: app.run(
    host="0.0.0.0", port=int(os.environ.get("PORT", 8080))
)).start()

# -------------------- Discord Bot ---------------------
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_CHANNEL = 1441813949220782181
GOODBYE_CHANNEL = 1442369914265534596

WELCOME_GIF = "https://cdn.discordapp.com/attachments/1418573231698214982/1442699662426636329/image0.gif?ex=69266243&is=692510c3&hm=a1ed6041f67f553e464498183863848c6e572d9dfd000afa214776ad8f0fbf3e&"
GOODBYE_GIF = "https://cdn.discordapp.com/attachments/1418573231698214982/1442699366778404926/image0.gif?ex=692661fd&is=6925107d&hm=0e03964485afd6bfdf6be27e123da8decd814b95520a888d4374a67d0bd4f617&"

WELCOME_LINES = [
    "✨ A new spark rises… the Phoenix acknowledges your arrival.",
    "🔥 Destiny shifts as you enter our realm, warrior.",
    "🌅 A radiant soul ascends into our skies — welcome.",
    "🕊️ The Phoenix spreads its wings in your honor."
]

GOODBYE_LINES = [
    "🌑 A flame dims… yet legends never truly fade.",
    "🍂 The winds carry your name onward — until we meet again.",
    "🔥 Even departing embers glow with purpose. Farewell.",
    "💫 The Phoenix bows — your journey continues elsewhere."
]

@bot.event
async def on_ready():
    print("Phoenix has awakened.")

# -------------------- WELCOME --------------------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL)
    if channel:
        line = random.choice(WELCOME_LINES)
        embed = discord.Embed(
            title="🔥 The Phoenix Welcomes You 🔥",
            description=line,
            color=discord.Color.red()
        )
        embed.set_image(url=WELCOME_GIF)
        embed.set_footer(text="May your fire burn brighter within our realm.")

        await channel.send(f"Hello {member.mention} ✨", embed=embed)

        try:
            await member.send(f"🌟 Welcome, {member.name}. {line}")
        except:
            pass

# -------------------- GOODBYE --------------------
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL)
    if channel:
        line = random.choice(GOODBYE_LINES)
        embed = discord.Embed(
            title="🌑 The Phoenix Watches You Depart 🌑",
            description=line,
            color=discord.Color.dark_red()
        )
        embed.set_image(url=GOODBYE_GIF)
        embed.set_footer(text="Your flame may travel, but it is never forgotten.")

        await channel.send(f"{member.name} has left the realm…", embed=embed)

# -------------------- Run Bot --------------------
bot.run(os.environ.get("DISCORD_TOKEN"))
