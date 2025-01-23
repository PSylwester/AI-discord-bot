import os
import discord
from apikeys import *
from discord.ext import commands
from discord import app_commands
from gtts import gTTS
from google.cloud import translate_v2 as translate
import html
import json
from discord.ext import commands
from apikeys import CHATBOTTOKEN
import ollama
import requests
from discord.ext import commands
from youtube_transcript_api import YouTubeTranscriptApi
import tiktoken
from collections import deque
import spacy
import re

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"googlekey.json"

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

