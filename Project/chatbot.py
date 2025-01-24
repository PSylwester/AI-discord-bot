import os
import discord
from apikeys import *

from discord import app_commands
from gtts import gTTS
from google.cloud import translate_v2 as translate
import html
import json

import ollama
import requests
from discord.ext import commands
from youtube_transcript_api import YouTubeTranscriptApi
import tiktoken
from collections import deque
import spacy
import re

# Globalna zmienna do przechowywania historii rozmów
conversation_history = {}
def setup_chatbot(bot: commands.Bot, on_ready_callbacks: list, on_message_callbacks: list):
    """Rejestruje komendy ChatBota."""
    # Event: kiedy bot się uruchomi
    @bot.event
    async def chatbot_on_ready():
        print(f'ChatBot module on ready is ready as {bot.user.name}')
        print(f'Bot is ready as {bot.user.name}')
    # Rejestrujemy `chatbot_on_ready` w liście callbacków
    on_ready_callbacks.append(chatbot_on_ready)
    # Lista dozwolonych kanałów
    allowed_channel_ids = [1332129837326012447, 1332128831460605993]  # Wstaw ID dozwolonych kanałów
    # Komenda testowa
    @bot.command(name="hello")
    async def hello(ctx):
        await ctx.send("Hello, I'm a bot!")


    # Ładowanie modelu spaCy dla języka polskiego
    nlp = spacy.load("pl_core_news_sm")

    # Funkcja do konwersji miasta na mianownik
    def get_city_in_nominative(city_name):
        doc = nlp(city_name)
        for token in doc:
            if token.pos_ == "PROPN":  # Sprawdzamy, czy to jest nazwa własna (miasto)
                return token.lemma_  # Lemmatyzacja, zwróci formę mianownika
        return city_name  # Jeśli nie uda się rozpoznać miasta, zwróć oryginalne słowo

    async def detect_intent(message_content):

        # Sprawdzenie, czy wiadomość zawiera link do YouTube
        youtube_link_pattern = r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^\s]+)"
        youtube_match = re.search(youtube_link_pattern, message_content)

        if youtube_match:
            youtube_url = youtube_match.group(0)  # Pobierz pierwszy pasujący link
            print(f"[DETECT INTENT] YouTube link detected: {youtube_url}")
            return {"intent": "summarise_youtube", "data": {"url": youtube_url}}

        print(f"[DETECT INTENT] Processing message: {message_content}")

        # Rozpoznanie intencji za pomocą modelu AI
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'system',
                'content': '''
                You are an AI assistant that classifies user messages into intents such as:
                - "ask_question" for general questions.
                - "summarise_youtube" for summarization requests of YouTube videos.
                - "weather" for weather-related queries.
                
                When detecting a "weather" intent, also extract the city if mentioned.
                Respond in the following JSON format and no other:
                {"intent": "<intent_name>", "data": {"city": "<city_name>"}}
                If no city is mentioned, set "city" to null.
                ''',
            },
            {
                'role': 'user',
                'content': f"Message: {message_content}",
            },
        ])
        
        try:
            result = response['message']['content'].strip()
            print(f"[DETECT INTENT] Raw response: {result}")
            return json.loads(result)  # Oczekujemy formatu JSON od modelu
        except (KeyError, json.JSONDecodeError) as e:
            print(f"[DETECT INTENT] Error: {e}")
            return {"intent": "unknown", "data": None}



    async def ask(channel, question):
        # Sprawdź, czy wiadomość pochodzi z jednego z dozwolonych kanałów
        if channel.id not in allowed_channel_ids:
            allowed_channels_links = [f"<#{ch_id}>" for ch_id in allowed_channel_ids]
            channels_message = ", ".join(allowed_channels_links)
            await channel.send(f"This command can only be used in the following channels: {channels_message}.")
            return

        # Uzyskanie odpowiedzi z ollama
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'system',
                'content': 'You are a helpful assistant who provides answers to questions concisely in no more than 1000 words.',
            },
            {
                'role': 'user',
                'content': question,
            },
        ])

        # Sprawdzenie, czy odpowiedź jest poprawna i pobranie tekstu
        try:
            full_response = response['message']['content']
        except KeyError:
            await channel.send("There was an error retrieving the response.")
            return

        # Podział odpowiedzi na fragmenty
        if len(full_response) > 2000:
            for i in range(0, len(full_response), 2000):
                await channel.send(full_response[i:i + 2000])
        else:
            await channel.send(full_response)

    # Komenda `ask` wywołująca funkcję obsługującą
    @bot.command(name="ask")
    async def ask_command(ctx, *, question):
        await ask(ctx.channel, question)

    # @bot.command(name="summarise")
    async def summarise(channel):
        # Sprawdź, czy wiadomość pochodzi z jednego z dozwolonych kanałów
        if channel.channel.id not in allowed_channel_ids:
            # Tworzenie klikalnych odnośników do kanałów
            allowed_channels_links = [f"<#{ch_id}>" for ch_id in allowed_channel_ids]
            channels_message = ", ".join(allowed_channels_links)
            await channel.send(f"This command can only be used in the following channels: {channels_message}.")
            return

        msgs = [ message.content async for message in channel.history(limit=10)]

        summarise_prompt = f"""
            Summarise the following messages delimited by 3 backticks:
            ```
            {msgs}
            ```
            """
        
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'system',
                'content': 'You are a helpful assistant who summarises the provided messages in bullet points concisely in no more than 1000 words.',
            },
            {
                'role': 'user',
                'content': summarise_prompt,
            },
        ])
        await channel.send(response['message']['content'])

    # @bot.command(name="summarise_youtube")
    async def summarise_youtube(channel, url):
        if channel.id not in allowed_channel_ids:
            allowed_channels_links = [f"<#{ch_id}>" for ch_id in allowed_channel_ids]
            channels_message = ", ".join(allowed_channels_links)
            await channel.send(f"This command can only be used in the following channels: {channels_message}.")
            return

        await channel.send("Fetching and summarising YouTube video...")

        video_id = url.split("v=")[1]
        try:
            # Fetch the transcript in Polish
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'pl', 'de', 'fr'])
            full_transcript = " ".join([item['text'] for item in transcript_list])

            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            tokens = encoding.encode(full_transcript)
            num_tokens = len(tokens)

            print(num_tokens)

            chunk_size = 7000

            if num_tokens > chunk_size:
                num_chunks = (num_tokens + chunk_size - 1) // chunk_size
                chunks = [full_transcript[i * chunk_size: (i + 1) * chunk_size] for i in range(num_chunks)]

                async def process_chunk(chunk, chunk_num):
                    await channel.send(f"Extracting summary of chunk {chunk_num} of {num_chunks} ...")
                    response = ollama.chat(model='llama3.2', messages=[
                        {
                            'role': 'system',
                            'content': 'You are a helpful assistant who summarises the transcript of a YouTube video in bullet points concisely in no more than 1000 words.',
                        },
                        {
                            'role': 'user',
                            'content': f'''
                            Please provide a summary for the following chunk of the Youtube video transcript:
                            1. Start with a high-level title for this chunk.
                            2. Provide 6-8 bullet points summarizing the key points in this chunk.
                            3. Start with the title of the chunk and then provide the summary in bullet points instead of using "here's the summary of the transcript".
                            4. No need to use concluding remarks at the end.
                            5. Return the response in markdown format.
                            6. Add a divider at the end in markdown format.

                            Chunk:
                            {chunk}
                            ''',
                        },
                    ])
                    return response['message']['content']

                for i, chunk in enumerate(chunks, start=1):
                    summary = await process_chunk(chunk, i)
                    await channel.send(summary)

            else:
                response = ollama.chat(model='llama3.2', messages=[
                    {
                        'role': 'system',
                        'content': '''
                            You are a helpful assistant who provides
                            a concise summary of the provided YouTube video transcript in bullet points concisely.
                        ''',
                    },
                    {
                        'role': 'user',
                        'content': full_transcript,
                    },
                ])
                final_summary = response['message']['content']
                await channel.send(final_summary)

        except Exception as e:
            await channel.send(f"Error: {str(e)}")


    @bot.command(name="summarise_youtube")
    async def summarise_youtube_command(ctx, url):
        await summarise_youtube(ctx.channel, url)


    async def weather(channel, city: str):
        """
        Sprawdza pogodę w podanym mieście i wysyła odpowiedź na kanał.
        """
        print(f"[WEATHER] Fetching weather for city: {city}")
        try:
            # Endpoint API OpenWeatherMap
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            # Sprawdzenie statusu odpowiedzi
            if response.status_code == 200:
                print(f"[WEATHER] API Response: {data}")
                # Pobranie danych pogodowych
                weather_description = data["weather"][0]["description"]
                temperature = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]

                # Przygotowanie wiadomości
                message = (
                    f"**Pogoda w {city.title()}:**\n"
                    f"- Opis: {weather_description.capitalize()}\n"
                    f"- Temperatura: {temperature}°C (odczuwalna: {feels_like}°C)\n"
                    f"- Wilgotność: {humidity}%\n"
                    f"- Prędkość wiatru: {wind_speed} m/s"
                )
            else:
                print(f"[WEATHER] Failed to fetch weather. Status code: {response.status_code}, Response: {data}")
                # Obsługa błędu (np. nie znaleziono miasta)
                message = f"Nie udało się znaleźć pogody dla miasta **{city}**. Sprawdź, czy nazwa jest poprawna."

        except Exception as e:
            # Obsługa błędów
            print(f"[WEATHER] Error: {e}")
            message = f"Wystąpił błąd podczas sprawdzania pogody: {e}"

        # Wysyłanie odpowiedzi na Discordzie
        await channel.send(message)
        
    @bot.event
    async def chatbot_on_message(message):
        print(f'ChatBot module on message is ready as {bot.user.name}')
        # Ignoruj wiadomości wysłane przez bota
        if message.author.bot:
            return
        
        print(f"[DEBUG] Received message: {message.content} from {message.author.name} in channel {message.channel.name}")

        # **1. Moderacja wiadomości**
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'system',
                'content': '''
                You are a content moderator. Your task is to analyze messages for compliance with the following rules:

                **Moderation Rules:**
                1. **Offensive or vulgar language**: The message must not contain profanity, insults, or vulgar expressions.
                2. **Hate speech**: The message must not include discriminatory, hateful, or offensive content directed at any group of people (e.g., based on race, religion, sexual orientation, etc.).
                3. **Harmful content**: The message must not promote violence, self-harm, misinformation, or other harmful activities.

                **Response Instructions:**
                - If the message **complies with all the rules**, respond with the single digit: `1`.
                - If the message **violates any of the rules**, respond with the single digit: `0`.
                - Do not add any additional comments or explanations. You mustn't response with any other comments. Your response must be strictly `1` or `0`.

                Important: Consider each rule individually and evaluate the message objectively based on the above criteria.
                ''',
            },
            {
                'role': 'user',
                'content': f"Message: {message.content}",
            },
        ])


        try:
            moderation_result = response['message']['content'].strip()
            if moderation_result == "0":  # Jeśli wiadomość została oznaczona jako naruszająca zasady
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, your message was removed due to policy violations."
                )
                return
            elif moderation_result == "1":  # Jeśli wiadomość jest akceptowalna
                print(f"Message from {message.author.name} is acceptable.")
            else:
                print("Unexpected moderation response:", moderation_result)
        except KeyError:
            print("AI moderation failed: Response missing or improperly formatted.")


        # Kanał dedykowany dla rozmów z AI
        ai_conversation_channel_id = 1332151862136275067  # id kanału dla rozmowy ai <-> users

        if message.channel.id == ai_conversation_channel_id:
            await handle_ai_conversation(message.channel, message.content)
            return

        # Sprawdź, czy wiadomość pochodzi z dozwolonego kanału
        if message.channel.id not in allowed_channel_ids:
            return  # Ignoruj wiadomości spoza dozwolonych kanałów

        # Skip command-prefixed messages
        if message.content.startswith(bot.command_prefix):
            await bot.process_commands(message)
            return

        # **2. Rozpoznawanie intencji**
        # Rozpoznaj intencję użytkownika
        if message.channel.id in allowed_channel_ids:
            intent_result  = await detect_intent(message.content)
            intent = intent_result.get("intent", "unknown")
            city = intent_result.get("data", {}).get("city", None)

            print(f"[INTENT HANDLER] Detected intent: {intent}, City: {city}")

            # Obsługa intencji
            if intent == "ask_question":
                await message.channel.send("Wykryto pytanie! Odpowiadam...")
                await ask(message.channel, message.content)

            elif intent == "summarise_youtube":
                await message.channel.send("Wykryto link do filmu na YouTube! Próbuję pobrać i streścić zawartość...")
                await summarise_youtube(message.channel, message.content)

            elif intent == "weather":
                await message.channel.send("Wykryto zapytanie o pogodę!")
                if city:
                    city = get_city_in_nominative(city)
                    print(f"[INTENT HANDLER] Extracted city: {city}")
                    await message.channel.send(f"Fetching weather information for {city}...")
                    await weather(message.channel, city)
                else:
                    await message.channel.send("I detected a weather query, but you need to specify a city. For example: 'What is the weather in London?'")
                    print("[INTENT HANDLER] No city extracted from the message.")
            
            else:
                await message.channel.send("Nie rozpoznano intencji, ale możesz użyć komendy `/ask`, aby uzyskać odpowiedź.")

            # Przetwarzanie standardowych komend
            await bot.process_commands(message)
    on_message_callbacks.append(chatbot_on_message)
    async def handle_ai_conversation(channel, message_content):
        """
        Funkcja obsługująca wspólną rozmowę z AI na dedykowanym kanale.

        Args:
            channel: Kanał, na którym odbywa się rozmowa.
            message_content: Treść wiadomości od użytkownika.
        """
        global conversation_history  # Użycie zmiennej globalnej

        # Pobierz historię rozmowy dla kanału lub zainicjalizuj nową
        if channel.id not in conversation_history:
            conversation_history[channel.id] = deque(maxlen=20)

        channel_history = conversation_history[channel.id]

        # Dodaj wiadomość użytkownika do historii
        channel_history.append({"role": "user", "content": message_content})

        # Przygotowanie kontekstu dla modelu AI
        context = list(channel_history)

        # Wygenerowanie odpowiedzi modelu AI
        response = ollama.chat(
            model='llama3.2',
            messages=context
        )

        # Przechwycenie odpowiedzi
        bot_response = response['message']['content']
        await channel.send(bot_response)

        # Dodaj odpowiedź bota do historii
        channel_history.append({"role": "bot", "content": bot_response})

    async def reset_conversation_history(channel_id):
        """Resetuje historię rozmowy dla danego kanału."""
        global conversation_history
        if channel_id in conversation_history:
            conversation_history[channel_id].clear()

    print("[CHATBOT] Functions loaded.")