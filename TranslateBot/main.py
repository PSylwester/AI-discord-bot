import os
import discord
import json
import html
import ollama
from apikeys import *
from discord.ext import commands
from discord import app_commands
from gtts import gTTS
from google.cloud import translate_v2 as translate


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"googlekey.json"

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# inicjalizacja tłumacza
translator = translate.Client()

server_language = 'en'

# mapowanie języków dla kanałów
channel_languages = {
    'main': 'pl',
    'english': 'en',
    'polish': 'pl'
}

# słownik z pełnymi nazwami języków
language_map = {
    "pl": "Polish",
    "en": "English",
    "es": "Spanish",
    "de": "German",
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()  # globalna synchronizacja komend
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# ogólna funkcja autocomplete dla języków pl - Polish itd.
async def language_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=language_map[lang], value=lang)
        for lang in language_map if current.lower() in language_map[lang].lower()
    ]


                            # KOMENDY /TRANSLATE_TO_....


# tłumaczenie wiadomości na polski
async def translate_to_polish_logic(text: str) -> str:
    try:
        translation = translator.translate(text, target_language="pl")
        translated_text = html.unescape(translation["translatedText"])

        return f'**Translated to Polish:** {translated_text}'
    except Exception as e:
        return f"An error occurred: {str(e)}"

# komenda do tłumaczenia wiadomości na polski /translate_to_polish
@bot.tree.command(name="translate_to_polish", description="Translate text to Polish")
async def translate_to_polish(interaction: discord.Interaction, message: str):
    result = await translate_to_polish_logic(message)
    await interaction.response.send_message(result, ephemeral=True)



# tłumaczenie wiadomości na angielski
async def translate_to_english_logic(text: str) -> str:
    try:
        translation = translator.translate(text, target_language="en")
        translated_text = html.unescape(translation["translatedText"])

        return f'**Translated to English:** {translated_text}'
    except Exception as e:
        return f"An error occurred: {str(e)}"

# komenda do tłumaczenia wiadomości na angielski /translate_to_english
@bot.tree.command(name="translate_to_english", description="Translate text to English")
async def translate_to_english(interaction: discord.Interaction, message: str):
    result = await translate_to_english_logic(message)
    await interaction.response.send_message(result, ephemeral=True)



# tłumaczenie wiadomości na niemiecki
async def translate_to_german_logic(text: str) -> str:
    try:
        translation = translator.translate(text, target_language="de")
        translated_text = html.unescape(translation["translatedText"])

        return f'**Translated to German:** {translated_text}'
    except Exception as e:
        return f"An error occurred: {str(e)}"

# komenda do tłumaczenia wiadomości na niemiecki /translate_to_german
@bot.tree.command(name="translate_to_german", description="Translate text to German")
async def translate_to_german(interaction: discord.Interaction, message: str):
    result = await translate_to_german_logic(message)
    await interaction.response.send_message(result, ephemeral=True)



# tłumaczenie wiadomości na hiszpanski
async def translate_to_spanish_logic(text: str) -> str:
    try:
        translation = translator.translate(text, target_language="es")
        translated_text = html.unescape(translation["translatedText"])

        return f'**Translated to Spanish:** {translated_text}'
    except Exception as e:
        return f"An error occurred: {str(e)}"

# komenda do tłumaczenia wiadomości na hiszpanski /translate_to_spanish
@bot.tree.command(name="translate_to_spanish", description="Translate text to Spanish")
async def translate_to_spain(interaction: discord.Interaction, message: str):
    result = await translate_to_spanish_logic(message)
    await interaction.response.send_message(result, ephemeral=True)



# komenda /translate_from_x_to_y z autocomplete dla języków
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
    if src_language.lower() == dest_language.lower():
        await interaction.response.send_message(
            "Source and target languages cannot be the same. Please choose different languages.",
            ephemeral=True
        )
        return

    try:
        response = translator.translate(message, source_language=src_language, target_language=dest_language)
        translated_text = html.unescape(response["translatedText"])
        await interaction.response.send_message(f'**Translated from {language_map[src_language]} '
                                                f'to {language_map[dest_language]}:** {translated_text}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)


                                # KOMENDY KONTEKSTOWE


# komenda kontekstowa translate to polish
@bot.tree.context_menu(name="Translate to Polish")
async def translate_to_polish(interaction: discord.Interaction, message: discord.Message):
    if message.author == bot.user:
        await interaction.response.send_message("You cannot use this command on bot messages.", ephemeral=True)
        return
    try:
        response = translator.translate(message.content, target_language='pl')
        translated_text = html.unescape(response["translatedText"])
        await interaction.response.send_message(f'**Translated to Polish:** {translated_text}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# komenda kontekstowa translate to english
@bot.tree.context_menu(name="Translate to English")
async def translate_to_english(interaction: discord.Interaction, message: discord.Message):
    if message.author == bot.user:
        await interaction.response.send_message("You cannot use this command on bot messages.", ephemeral=True)
        return
    try:
        response = translator.translate(message.content, target_language='en')
        translated_text = html.unescape(response["translatedText"])
        await interaction.response.send_message(f'**Translated to English:** {translated_text}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# komenda kontekstowa translate to spanish
@bot.tree.context_menu(name="Translate to Spanish")
async def translate_to_spanish(interaction: discord.Interaction, message: discord.Message):
    if message.author == bot.user:
        await interaction.response.send_message("You cannot use this command on bot messages.", ephemeral=True)
        return
    try:
        response = translator.translate(message.content, target_language='es')
        translated_text = html.unescape(response["translatedText"])
        await interaction.response.send_message(f'**Translated to Spanish:** {translated_text}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# komenda kontekstowa translate to german
@bot.tree.context_menu(name="Translate to German")
async def translate_to_german(interaction: discord.Interaction, message: discord.Message):
    if message.author == bot.user:
        await interaction.response.send_message("You cannot use this command on bot messages.", ephemeral=True)
        return
    try:
        response = translator.translate(message.content, target_language='de')
        translated_text = html.unescape(response["translatedText"])
        await interaction.response.send_message(f'**Translated to German:** {translated_text}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)



# automatyczne tłumaczenie w zależności od ustawionego języka na kanale, globalnie jest pl
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # ignoruje wiadomości od botów

    channel_name = message.channel.name

    # jeśli kanału nie ma w słowniku, to ustawia domyślnie globalny język
    target_language = channel_languages.get(channel_name, server_language)

    try:
        detected_lang = translator.detect_language(message.content)["language"]
        if detected_lang != target_language:
            response = translator.translate(message.content, source_language=detected_lang, target_language=target_language)
            translated_text = html.unescape(response["translatedText"])
            await message.reply(f'**Translation:** {translated_text}')
    except Exception as e:
        print(f"An error occured during translation: {e}")

    await bot.process_commands(message)  # umożliwia działanie innych komend



@bot.tree.command(name="ask", description="Ask the bot to analyze your message and respond accordingly.")
@app_commands.describe(query="Your message to analyze")
async def ask_command(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system',
             'content': 'You are an assistant integrated with a Discord bot. '
                        'Your task is to analyze the user message and identify its intent. '
                        'If the intent is to translate text to a specific language (English, Polish, German or Spanish), '
                        'extract only the text that should be translated and the specified target language. '
                        'For all supported languages (English, Polish, German, Spanish), '
                        'ensure the response uses proper capitalization (e.g., "Polish" not "polish"). '
                        'Input language names may be in lowercase or uppercase, but always normalize '
                        'them to have the first letter capitalized. \n'
                        'For example:\n'
                        '"Translate klawiatura to English" => '
                        '{"intent": "translate_to_english", "details": {"text": "klawiatura"}}\n'
                        '"Przetłumacz mi słowo komputer na angielski" => '
                        '{"intent": "translate_to_english", "details": {"text": "komputer"}}\n'
                        '"Can you translate the word computer into German?" => '
                        '{"intent": "translate_to_german", "details": {"text": "computer"}}\n\n'
                        'If the user specifies a target language that is not supported, '
                        'and clearly mentions the unsupported language, respond with '
                        '{"intent": "unsupported_language", "details": '
                        '{"language": "specified language", "text": "example text"}}.\n\n'
                        'If the user does not explicitly specify the target language '
                        'in their message, respond with {"intent": "unknown"}. '
                        'For example:\n'
                        '"Przetłumacz mi tekst Today the weather is nice" => {"intent": "unknown"}\n\n'
                        'If the input contains only emoji, symbols, '
                        'or non-meaningful content (e.g., "#$%^&", "😃🎉🌟"), respond with '
                        '{"intent": "invalid_input", "details": {"reason": "non-meaningful content"}}.\n\n'
                        'Do not infer the target language from context or the message content. '
                        'Do not treat supported languages (English, Polish, German, Spanish) as unsupported in any scenario. '
                        'If the user requests to convert a text message to a voice message, '
                        'respond with {"intent": "text_to_speech", "details": {"text": "example text"}}.\n'
                        'For example:\n'
                        '"Convert this message to voice: Hello world!" => '
                        '{"intent": "text_to_speech", "details": {"text": "Hello world!"}}\n'
                        '"Zamień hello world na głosówkę" => '
                        '{"intent": "text_to_speech", "details": {"text": "hello world"}}\n'
                        '"Change how are you to voice" => '
                        '{"intent": "text_to_speech", "details": {"text": "how are you"}}\n'
                        '"Zamień to na wiadomość głosową: Cześć!" => '
                        '{"intent": "text_to_speech", "details": {"text": "Cześć!"}}\n\n'
                        'Always respond with a JSON object in this exact format.'},
            {'role': 'user', 'content': query}
        ])

        print("Response from Ollama:", response)

        # pobieranie treści odpowiedzi od modelu
        response_content = response['message']['content']

        # parsowanie odpowiedzi jako JSON
        parsed_response = json.loads(response_content)
        intent = parsed_response.get("intent", "unknown")
        details = parsed_response.get("details", {})

        # INTENCJE
        if intent == "translate_to_polish":
            text_to_translate = details.get("text", "")
            if text_to_translate:
                result = await translate_to_polish_logic(text_to_translate)
                await interaction.followup.send(result)
            else:
                await interaction.followup.send("I couldn't find any text to translate.")

        elif intent == "translate_to_english":
            text_to_translate = details.get("text", "")
            if text_to_translate:
                result = await translate_to_english_logic(text_to_translate)
                await interaction.followup.send(result)
            else:
                await interaction.followup.send("I couldn't find any text to translate.")

        elif intent == "translate_to_german":
            text_to_translate = details.get("text", "")
            if text_to_translate:
                result = await translate_to_german_logic(text_to_translate)
                await interaction.followup.send(result)
            else:
                await interaction.followup.send("I couldn't find any text to translate.")

        elif intent == "translate_to_spanish":
            text_to_translate = details.get("text", "")
            if text_to_translate:
                result = await translate_to_spanish_logic(text_to_translate)
                await interaction.followup.send(result)
            else:
                await interaction.followup.send("I couldn't find any text to translate.")

        elif intent == "text_to_speech":
            text_to_convert = details.get("text", "")
            if text_to_convert:
                try:
                    tts_file = await text_to_speech_logic(text_to_convert)
                    await interaction.followup.send("Here is the voice message:", file=discord.File(tts_file))
                except Exception as e:
                    await interaction.followup.send(
                        f"An error occurred while generating the voice message: {str(e)}")
            else:
                await interaction.followup.send("I couldn't find any text to convert to a voice message.")

        elif intent == "unsupported_language":
            unsupported_language = details.get("language", "unknown")
            await interaction.followup.send(
                f"The specified language '{unsupported_language}' is not supported. "
                "Supported languages are: English, Polish, German, and Spanish.")

        elif intent == "invalid_input":
            await interaction.followup.send(
                "Your input contains only non-meaningful content like symbols or emojis. "
                "Please provide valid text for processing.")

        else:
            await interaction.followup.send(
                "I couldn't determine the intent of your message. Please try again.")

    except json.JSONDecodeError:
        await interaction.followup.send("Failed to parse the response. Please try again.")
    except Exception as e:
        print(f"Error processing command: {e}")
        await interaction.followup.send("An error occurred while processing your request.")

# komenda /set_server_language
@bot.tree.command(name="set_server_language", description="Change server language")
@app_commands.autocomplete(language=language_autocomplete)
async def set_server_language(interaction: discord.Interaction, language: str):
    global server_language
    try:
        server_language = language
        await interaction.response.send_message(f"Server language has been set to {language_map[language]}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)


# text_to_speech
async def text_to_speech_logic(message_content: str, interaction: discord.Interaction = None):
    try:
        detected_lang = translator.detect_language(message_content)["language"]

        # tworzenie pliku audio
        tts = gTTS(text=message_content, lang=detected_lang)
        tts.save("message.mp3")

        if interaction:
            await interaction.response.send_message(
                "Here is the voice message:", file=discord.File("message.mp3"), ephemeral=True)
        return "message.mp3"
    except Exception as e:
        if interaction:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
        raise e

# komenda kontekstowa text_to_speech
@bot.tree.context_menu(name="Text to speech")
async def text_to_speech(interaction: discord.Interaction, message: discord.Message):
    await text_to_speech_logic(message.content, interaction=interaction)


bot.run(BOTTOKEN)