import discord
from apikeys import *
from discord.ext import commands
from discord import app_commands
from googletrans import Translator
from gtts import gTTS

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# inicjalizacja tłumacza
translator = Translator()

server_language = 'pl'

# mapowanie języków dla kanałów;
channel_languages = {
    'main': 'pl',
    'english': 'en',
    'polish': 'pl'
}

# Słownik z pełnymi nazwami języków
language_map = {
    "pl": "Polish",
    "en": "English",
    "es": "Spanish",
    "de": "German",
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

# komenda do tłumaczenia wiadomości na polski /translate
@bot.tree.command(name="translate", description="Translate text to Polish")
async def translate(interaction: discord.Interaction, message: str):
    try:
        # Wykrywanie języka wiadomości
        detected_lang = translator.detect(message).lang
        detected_lang_full = language_map.get(detected_lang, detected_lang)
        # tłumaczenie wiadomości na polski
        translated = translator.translate(message, src='auto', dest='pl').text
        await interaction.response.send_message(f'**Translated from {detected_lang_full} to Polish:** {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# ogólna funkcja autocomplete dla języków pl - Polish itd.
async def language_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=language_map[lang], value=lang)
        for lang in language_map if current.lower() in language_map[lang].lower()
    ]

# Komenda /translate_from_x_to_y z autocomplete dla języków
@bot.tree.command(name="translate_from_x_to_y", description="Translate from any language to any other language")
@app_commands.describe(
    src_language="Source language (e.g., en, es, de, pl)",
    dest_language="Target language (e.g., en, es, de, pl)",
    message="The message to translate"
)
@app_commands.autocomplete(src_language=language_autocomplete)
@app_commands.autocomplete(dest_language=language_autocomplete)
async def translate_from_x_to_y(interaction: discord.Interaction,
                                src_language: str,
                                dest_language: str,
                                message: str):
    try:
        translated = translator.translate(message, src=src_language, dest=dest_language).text
        await interaction.response.send_message(f'**Translated from {language_map[src_language]} to {language_map[dest_language]}:** {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)


# Komenda kontekstowa (PPM na wiadomosc -> aplikacje -> translate message)
@bot.tree.context_menu(name="Translate message")
async def translate_message(interaction: discord.Interaction, message: discord.Message):
    try:
        detected_lang = translator.detect(message.content).lang
        detected_lang_full = language_map.get(detected_lang, detected_lang)
        translated = translator.translate(message.content, src=detected_lang, dest='pl').text
        # odpowiedź z przetłumaczonym tekstem
        await interaction.response.send_message(f'**Translated from {detected_lang_full} to Polish:** {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# komendy kontekstowe tłumaczące na inne języki
@bot.tree.context_menu(name="Translate to English")
async def translate_to_english(interaction: discord.Interaction, message: discord.Message):
    try:
        translated = translator.translate(message.content, dest='en', src='auto').text
        await interaction.response.send_message(f'**Translated to English:** {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

@bot.tree.context_menu(name="Translate to Spanish")
async def translate_to_spanish(interaction: discord.Interaction, message: discord.Message):
    try:
        translated = translator.translate(message.content, dest='es', src='auto').text
        await interaction.response.send_message(f'**Translated to Spanish:** {translated}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

@bot.tree.context_menu(name="Translate to German")
async def translate_to_german(interaction: discord.Interaction, message: discord.Message):
    try:
        translated = translator.translate(message.content, dest='de', src='auto').text
        await interaction.response.send_message(f'**Translated to German:** {translated}', ephemeral=True)
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
        await message.reply(f'**Translation:** {translated_text}')

    await bot.process_commands(message)  # Umożliwia działanie innych komend

# Komenda /set_server_language z podpowiedziami nazw języków
@bot.tree.command(name="set_server_language", description="Change server language")
@app_commands.autocomplete(language=language_autocomplete)
async def set_server_language(interaction: discord.Interaction, language: str):
    global server_language
    try:
        server_language = language
        await interaction.response.send_message(f"Server language has been set to {language_map[language]}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)


# komenda kontekstowa text_to_speech
@bot.tree.context_menu(name="Text to speech")
async def text_to_speech(interaction: discord.Interaction, message: discord.Message):
    try:
        # Tworzenie pliku audio z treści wiadomości
        tts = gTTS(text=message.content, lang=server_language)
        tts.save("message.mp3")

        # Wysyłanie pliku audio jako odpowiedź
        await interaction.response.send_message("Here is the voice message:", file=discord.File("message.mp3"), ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

bot.run(BOTTOKEN)