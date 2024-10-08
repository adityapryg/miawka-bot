import os
from discord.ext import commands
from dotenv import load_dotenv
from core.globals import DISCORD_TOKEN, intents
from core.events import setup_event_handlers
from commands.miaw import setup_miaw_command
from commands.sensei import setup_sensei_command

load_dotenv()

# Inisialisasi bot dengan prefix dan intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Setup event handlers (on_message, on_ready, etc)
setup_event_handlers(bot)

# Setup command handlers
setup_miaw_command(bot)
setup_sensei_command(bot)

# Jalankan bot
bot.run(DISCORD_TOKEN)