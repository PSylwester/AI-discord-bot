import os
import discord
from dotenv import load_dotenv
from apikeys import *
from discord.ext import commands
from discord import app_commands
from chatbot import setup_chatbot
from translatebot import setup_translate
from musicbot import setup_music

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"googlekey.json"

# Tworzenie instancji bota
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

# globalna lista do obsługi wielu `on_ready` i `on_message` funkcji
on_ready_callbacks = []
on_message_callbacks = []

# Główne on_message, które wywołuje wszystkie callbacki
@bot.event
async def on_message(message: discord.Message):
    # Wywołanie wszystkich zarejestrowanych callbacków
    for callback in on_message_callbacks:
        await callback(message)
    # Zapewniamy, że bot przetworzy również swoje komendy
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user.name}')
    for callback in on_ready_callbacks:
        await callback()  # Wywołanie każdego zarejestrowanego callbacka
        
# Dodawanie funkcjonalności z innych modułów
setup_translate(bot, on_ready_callbacks, on_message_callbacks)
setup_chatbot(bot, on_ready_callbacks, on_message_callbacks)
setup_music(bot, on_ready_callbacks, on_message_callbacks)

# Uruchomienie bota
bot.run(BOT_TOKEN)

