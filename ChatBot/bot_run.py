import os
import discord
from discord.ext import commands
from apikeys import CHATBOTTOKEN
import ollama

from youtube_transcript_api import YouTubeTranscriptApi
import tiktoken

# Ustawienie intents
intents = discord.Intents.default()
intents.message_content = True  # Dodaj tę linię, aby bot mógł odczytywać treści wiadomości

# Tworzenie instancji bota
bot = commands.Bot(command_prefix='/', intents=intents)

# Event: kiedy bot się uruchomi
@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user.name}')

# Lista dozwolonych kanałów
allowed_channel_ids = [1297985734376165437, 1309723026283171891]  # Wstaw ID dozwolonych kanałów

# Komenda testowa
@bot.command(name="hello")
async def hello(ctx):
    await ctx.send("Hello, I'm a bot!")

async def detect_intent(message_content):
    # Sprawdzenie, czy wiadomość zawiera link do YouTube
    if "youtube.com/watch?v=" in message_content or "youtu.be/" in message_content:
        return "summarise_youtube"
    
    # Rozpoznanie innych typów wiadomości
    response = ollama.chat(model='llama3.2', messages=[
        {
            'role': 'system',
            'content': '''
            You are an AI assistant that classifies user messages into intents such as:
            - "ask_question" for questions.
            - "translate" for translation requests.
            - "summarise" for summarization requests.
            - "weather" for weather-related queries.
            Respond with just the intent name.
            ''',
        },
        {
            'role': 'user',
            'content': f"Message: {message_content}",
        },
    ])
    try:
        return response['message']['content'].strip().lower()
    except KeyError:
        return "unknown"

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
    # Sprawdź, czy wiadomość pochodzi z jednego z dozwolonych kanałów
    if channel.id not in allowed_channel_ids:
        # Tworzenie klikalnych odnośników do kanałów
        allowed_channels_links = [f"<#{ch_id}>" for ch_id in allowed_channel_ids]
        channels_message = ", ".join(allowed_channels_links)
        await channel.send(f"This command can only be used in the following channels: {channels_message}.")
        return

    await channel.send("Fetching and summarising YouTube video...") # Send message indicating the start of the process

    # Extract video transcript using youtube_transcript_api
    video_id = url.split("v=")[1] # Extract the video ID from the URL
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id) # Fetch the transcript using the video ID
    full_transcript = " ".join([item['text'] for item in transcript_list]) # Join the transcript text into a single string

    # Check the length of the transcript in tokens using tiktoken
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo") # Get the encoding for the specified model
    tokens = encoding.encode(full_transcript) # Encode the transcript into tokens
    num_tokens = len(tokens) # Get the number of tokens

    print(num_tokens) # Print the number of tokens
    # Define the chunk size
    chunk_size = 7000 # Set the chunk size to 7000 tokens

    # If the number of tokens exceeds the chunk size, split into chunks
    if num_tokens > chunk_size:
        num_chunks = (num_tokens + chunk_size - 1) // chunk_size # Calculate the number of chunks
        chunks = [full_transcript[i * chunk_size : (i + 1) * chunk_size] for i in range(num_chunks)] # Split the transcript in the chunks

        async def process_chunk(chunk, chunk_num):
            await channel.send(f"Extracting summary of chunk {chunk_num} of {num_chunks} ...") # Send message indicating the current chunk

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
                    6. Add a devider at the end in markdown format.

                    Chunk:
                    {chunk}
                    ''',
                },
            ])
            return response['message']['content'] # Return the summary content from the response
        for i, chunk in enumerate(chunks, start=1): # Iterate over each chunk
            summary = await process_chunk(chunk, i) # Process the chunk and get the summary
            await channel.send(summary) # Send the summary as a message

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
        final_summary = response['message']['content'] # Get the final summary as a message
        await channel.send(final_summary) # Send the final summary as a message

@bot.command(name="summarise_youtube")
async def summarise_youtube_command(ctx, url):
    await summarise_youtube(ctx.channel, url)

@bot.event
async def on_message(message):
    # Ignoruj wiadomości wysłane przez bota
    if message.author.bot:
        return

    # **1. Moderacja wiadomości**
    response = ollama.chat(model='llama3.2', messages=[
        {
            'role': 'system',
            'content': '''
            You are a content moderator. Evaluate the following message for:
            1. Offensive language.
            2. Hate speech.
            3. Spam or unwanted advertising.
            4. Links to malicious websites.
            Classify the message as:
            - "acceptable" if the message meets all guidelines.
            - "unacceptable" if the message violates any policy.
            ''',
        },
        {
            'role': 'user',
            'content': f"Message: {message.content}",
        },
    ])

    try:
        moderation_result = response['message']['content'].strip().lower()
        if "unacceptable" in moderation_result:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, your message was removed due to policy violations."
            )
            return
    except KeyError:
        print("AI moderation failed.")

    # Sprawdź, czy wiadomość pochodzi z dozwolonego kanału
    if message.channel.id not in allowed_channel_ids:
        return  # Ignoruj wiadomości spoza dozwolonych kanałów

    # Skip command-prefixed messages
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # **2. Rozpoznawanie intencji**
    # Rozpoznaj intencję użytkownika
    intent = await detect_intent(message.content)

    # Obsługa intencji
    if intent == "ask_question":
        await message.channel.send("Wykryto pytanie! Odpowiadam...")
        await ask(message.channel, message.content)

    elif intent == "translate":
        await message.channel.send("Wykryto zapytanie o tłumaczenie! Funkcja tłumaczenia wkrótce zostanie zaimplementowana.")

    elif intent == "summarise":
        await message.channel.send("Wykryto prośbę o streszczenie! Próbuję podsumować ostatnie wiadomości...")
        await summarise(message.channel)

    elif intent == "summarise_youtube":
        await message.channel.send("Wykryto link do filmu na YouTube! Próbuję pobrać i streścić zawartość...")
        await summarise_youtube(message.channel, message.content)

    elif intent == "weather":
        await message.channel.send("Wykryto zapytanie o pogodę! Niestety, funkcja pogody nie jest jeszcze dodana.")

    else:
        await message.channel.send("Nie rozpoznano intencji, ale możesz użyć komendy `/ask`, aby uzyskać odpowiedź.")

    # Przetwarzanie standardowych komend
    await bot.process_commands(message)


# Uruchomienie bota z tokenem
bot.run(CHATBOTTOKEN)
