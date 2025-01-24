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



from ChatBot.ChatBot import setup_chatbot_commands
from TranslateBot.TranslateBot import setup_translate_commands

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"googlekey.json"

# Tworzenie instancji bota
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

# Dodawanie funkcjonalności z innych modułów
setup_chatbot_commands(bot)
setup_translate_commands(bot)
# Event: uruchomienie bota
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user.name}")

# Uruchomienie bota
bot.run(CHATBOTTOKEN)

