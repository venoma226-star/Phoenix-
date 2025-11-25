import os
import discord
from discord.ext import commands
from flask import Flask
import threading
import random

# ---------------- Flask Server ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()

# ---------------- Discord Bot ----------------
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_CHANNEL_ID = 1441813949220782181
QUOTES = [
    "Rise like a phoenix, mighty and unbroken!",
    "Glory awaits those who dare to enter!",
    "May your journey be legendary!",
    "Strength and honor guide your path!"
]

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        quote = random.choice(QUOTES)
        embed = discord.Embed(title="Welcome to the Realm!", description=quote, color=discord.Color.red())
        embed.set_image(url="https://cdn.discordapp.com/attachments/1441276578440155216/1442556258589610158/image0.gif?ex=6925dcb5&is=69248b35&hm=44eb3adbe52ae1640567fab37325b130c892784ddf4faeb1c2de89bc123c13b3&")
        embed.set_footer(text="Prepare for glory!")

        await channel.send(f"Hello {member.mention}!", embed=embed)
        try:
            await member.send(f"Welcome {member.name}! {quote}")
        except:
            pass

bot.run(os.environ.get("DISCORD_TOKEN"))
