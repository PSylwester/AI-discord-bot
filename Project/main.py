import os
import discord
from apikeys import *
from discord.ext import commands
from discord import app_commands
from gtts import gTTS
from google.cloud import translate_v2 as translate
import html
import json
from apikeys import CHATBOTTOKEN
import ollama
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import tiktoken
from collections import deque
import spacy
import re



from chatbot import setup_chatbot
from translatebot import setup_translate

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"googlekey.json"

# Tworzenie instancji bota
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

# Dodaj globalną listę do obsługi wielu `on_ready` i `on_message` funkcji
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

# Uruchomienie bota
bot.run(CHATBOTTOKEN)

