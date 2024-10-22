import discord
from apikeys import *
from discord.ext import commands
from googletrans import Translator

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# inicjalizacja tłumacza
translator = Translator()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    # synchronizuje komendy kontekstowe z serwerem
    try:
        synced = await bot.tree.sync()  # globalna synchronizacja komend
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# testowa komenda
@bot.command()
async def hello(ctx):
    await ctx.send('Hello! I am your AI bot.')

# komenda do tłumaczenia wiadomości
@bot.command()
async def translate(ctx, *, message):
    # wykrywanie języka
    detected_lang = translator.detect(message).lang
    # tłumaczenie wiadomości na polski
    translated = translator.translate(message, src=detected_lang, dest='pl').text
    await ctx.send(f'Translated from {detected_lang} to Polish: {translated}')

# Komenda kontekstowa (PPM na wiadomosc -> aplikacje -> translate message)
@bot.tree.context_menu(name="Translate message")
async def translate_message(interaction: discord.Interaction, message: discord.Message):
    try:
        # wykrywanie języka wiadomości
        detected_lang = translator.detect(message.content).lang
        # tłumaczenie wiadomości na polski
        translated = translator.translate(message.content, src=detected_lang, dest='pl').text
        # odpowiedź z przetłumaczonym tekstem
        await interaction.response.send_message(f'Translated from {detected_lang} to Polish: {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)


bot.run(BOTTOKEN)