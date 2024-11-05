import discord
from apikeys import *
from discord.ext import commands
from googletrans import Translator

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# inicjalizacja tłumacza
translator = Translator()

server_language = 'pl'

# Przykładowe mapowanie języków dla kanałów; można rozszerzyć lub zapisać w bazie danych
channel_languages = {
    'main': 'pl',
    'english': 'en',  # Kanał English będzie miał język docelowy angielski
    'polish': 'pl'    # Można dodać więcej kanałów i języków docelowych
}

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

# testowo /translate
@bot.tree.command(name="translate", description="Translate text to Polish")
async def translate2(interaction: discord.Interaction, message: str):
    try:
        # Wykrywanie języka wiadomości
        detected_lang = translator.detect(message).lang
        # tłumaczenie wiadomości na polski
        translated = translator.translate(message, src='auto', dest='pl').text
        await interaction.response.send_message(f'Translated from {detected_lang} to Polish: {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)


# komenda /translate_from_x_to_y
@bot.tree.command(name="translate_from_x_to_y", description="Translate from any language to any other language")
async def translate_from_x_to_y(interaction: discord.Interaction,
                                src_language: str,
                                dest_language: str,
                                message: str):
    try:
        translated = translator.translate(message, src=src_language, dest=dest_language).text
        await interaction.response.send_message(f'Translated from {src_language} to {dest_language}: {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# Komenda kontekstowa (PPM na wiadomosc -> aplikacje -> translate message)
@bot.tree.context_menu(name="Translate message")
async def translate_message(interaction: discord.Interaction, message: discord.Message):
    try:
        detected_lang = translator.detect(message.content).lang
        translated = translator.translate(message.content, src=detected_lang, dest='pl').text
        # odpowiedź z przetłumaczonym tekstem
        await interaction.response.send_message(f'Translated from {detected_lang} to Polish: {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# komendy kontekstowe tłumaczące na inne języki
@bot.tree.context_menu(name="Translate to English")
async def translate_to_english(interaction: discord.Interaction, message: discord.Message):
    try:
        translated = translator.translate(message.content, dest='en', src='auto').text
        await interaction.response.send_message(f'Translated to English: {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

@bot.tree.context_menu(name="Translate to Spanish")
async def translate_to_spanish(interaction: discord.Interaction, message: discord.Message):
    try:
        translated = translator.translate(message.content, dest='es', src='auto').text
        await interaction.response.send_message(f'Translated to Spanish: {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

@bot.tree.context_menu(name="Translate to German")
async def translate_to_german(interaction: discord.Interaction, message: discord.Message):
    try:
        translated = translator.translate(message.content, dest='de', src='auto').text
        await interaction.response.send_message(f'Translated to German: {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# automatyczne tłumaczenie w zależności od ustawionego języka na kanale, globalnie jest pl
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # ignoruje wiadomości od botów

    # pobiera nazwę kanału
    channel_name = message.channel.name

    # jeśli kanału nie ma w słowniku, to ustawia domyślnie 'pl'
    target_language = channel_languages.get(channel_name, server_language)

    # wykrywa język wiadomości
    detected_lang = translator.detect(message.content).lang
    if detected_lang != target_language:
        # tłumaczy wiadomość na język docelowy kanału
        translated_text = translator.translate(message.content, src=detected_lang, dest=target_language).text
        await message.channel.send(f'**Tłumaczenie:** {translated_text}')

    await bot.process_commands(message)  # Umożliwia działanie innych komend

# komenda /set_server_language ustawia język serwera na jakiś wybrany
@bot.tree.command(name="set_server_language", description="Change server language")
async def translate_from_x_to_y(interaction: discord.Interaction, language: str):
    global server_language
    try:
        server_language = language
        await interaction.response.send_message(f"Server language has been set to {language}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

bot.run(BOTTOKEN)