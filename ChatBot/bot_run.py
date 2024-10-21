import discord
from discord.ext import commands
from apikeys import CHATBOTTOKEN

# Ustawienie intents
intents = discord.Intents.default()
intents.message_content = True  # Dodaj tę linię, aby bot mógł odczytywać treści wiadomości

# Tworzenie instancji bota
bot = commands.Bot(command_prefix='!', intents=intents)

# Event: kiedy bot się uruchomi
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Komenda testowa
@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

# Uruchomienie bota z tokenem
bot.run(CHATBOTTOKEN)
