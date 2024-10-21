import discord
from discord.ext import commands
from youtube_search import YoutubeSearch
from apikeys import *
import yt_dlp

# Definiowanie intents
# Definiowanie intents
intents = discord.Intents.default()
intents.messages = True              # Włącza dostęp do wiadomości
intents.message_content = True       # Włącza dostęp do treści wiadomości
intents.guilds = True                # Włącza dostęp do informacji o serwerach
intents.voice_states = True          # Włącza dostęp do stanów głosowych

# Stworzenie instancji bota
bot = commands.Bot(command_prefix='!', intents=intents)


# Funkcja wyszukiwania video na YouTube
def search_youtube(query):
    results = YoutubeSearch(query, max_results=1).to_dict()
    if results:
        return f"https://www.youtube.com/watch?v={results[0]['id']}"
    else:
        return None


# Polecenie dołączenia do kanału głosowego i odtwarzania muzyki
@bot.command(name='play')
async def play(ctx, *, query: str):
    if not ctx.author.voice:
        await ctx.send("Musisz być na kanale głosowym, aby użyć tej komendy.")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        voice_client = await channel.connect()
    else:
        voice_client = ctx.voice_client
        if voice_client.channel != channel:
            await voice_client.move_to(channel)

    if voice_client.is_playing():
        voice_client.stop()

    song_url = search_youtube(query)
    if song_url:
        ydl_opts = {
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_url, download=False)
            audio_url = info['url']
            source = discord.FFmpegPCMAudio(audio_url)
            voice_client.play(source)
            await ctx.send(f"Odtwarzam: {info.get('title', 'Nieznany tytuł')}")
    else:
        await ctx.send("Nie znaleziono piosenki o podanej nazwie.")

# Komenda do zatrzymania muzyki
@bot.command(name='stop')
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Muzyka zatrzymana.")

# Polecenie opuszczenia kanału głosowego
@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Opuszczam kanał głosowy.")
    else:
        await ctx.send("Nie jestem na żadnym kanale głosowym.")


# Event informujący o gotowości bota
@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user.name}')


# Uruchomienie bota
bot.run(BOTTOKEN)
