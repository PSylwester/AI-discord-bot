import os
import discord
from discord.ext import commands
from apikeys import CHATBOTTOKEN
import ollama

# Ustawienie intents
intents = discord.Intents.default()
intents.message_content = True  # Dodaj tę linię, aby bot mógł odczytywać treści wiadomości

# Tworzenie instancji bota
bot = commands.Bot(command_prefix='/', intents=intents)

# Event: kiedy bot się uruchomi
@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user.name}')

# Komenda testowa
@bot.command(name="hello")
async def hello(ctx):
    await ctx.send("Hello, I'm a bot!")

@bot.command(name="ask")
async def ask(ctx, *, message):
    # Uzyskanie odpowiedzi z ollama
    response = ollama.chat(model='llama3.2', messages=[
        {
            'role': 'system',
            'content': 'You are a helpful assistant who provides answers to questions concisely in no more than 1000 words.',
        },
        {
            'role': 'user',
            'content': message,
        },
    ])

    # Sprawdzenie, czy odpowiedź jest poprawna i pobranie tekstu
    try:
        full_response = response['message']['content']  # Upewnij się, że 'content' to właściwe pole
    except KeyError:
        await ctx.send("There was an error retrieving the response.")
        return

    # Podział odpowiedzi, jeśli jest dłuższa niż 2000 znaków
    if len(full_response) > 2000:
        for i in range(0, len(full_response), 2000):
            await ctx.send(full_response[i:i + 2000])
    else:
        await ctx.send(full_response)


@bot.command(name="summarise")
async def summarise(ctx):

    msgs = [ message.content async for message in ctx.channel.history(limit=10)]

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
    await ctx.send(response['message']['content'])

# Uruchomienie bota z tokenem
bot.run(CHATBOTTOKEN)
