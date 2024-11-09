import discord
from discord.ext import commands
import asyncio
from youtube_search import YoutubeSearch
import yt_dlp as youtube_dl  # Użycie yt_dlp zamiast youtube_dl

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'extract_flat': True,  # Unikaj przerywania playlisty
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

class Playlist:
    def __init__(self):
        self.queue = []          # Lista utworów w playliście
        self.current_index = 0   # Aktualny indeks odtwarzanego utworu

    def add_song(self, title, url):
        self.queue.append({'title': title, 'url': url})

    def get_current_song(self):
        return self.queue[self.current_index] if self.queue else None

    def next_song(self):
        if self.current_index < len(self.queue) - 1:
            self.current_index += 1
            return self.queue[self.current_index]
        return None

    def reset(self):
        self.queue = []
        self.current_index = 0

playlist = Playlist()

@bot.command(name='create_playlist')
async def create_playlist(ctx, *, query):
    results = YoutubeSearch(query, max_results=5).to_dict()
    if not results:
        await ctx.send("Nie znaleziono wyników dla podanej frazy.")
        return

    playlist.reset()
    for result in results:
        title = result['title']
        url_suffix = result['url_suffix']
        url = f"https://www.youtube.com{url_suffix}"
        playlist.add_song(title, url)

    await ctx.send("Playlista została utworzona. Użyj komendy !play, aby rozpocząć odtwarzanie.")

@bot.command(name='play')
async def play(ctx):
    if not ctx.author.voice:
        await ctx.send("Musisz być na kanale głosowym, aby odtworzyć muzykę.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if not voice_client or not voice_client.is_connected():
        voice_client = await channel.connect()

    if voice_client.is_playing():
        await ctx.send("Muzyka jest już odtwarzana.")
        return

    current_song = playlist.get_current_song()
    if not current_song:
        await ctx.send("Playlista jest pusta.")
        return

    await play_song(ctx, current_song)

async def play_song(ctx, song):
    voice_client = ctx.voice_client
    if not voice_client:
        await ctx.send("Bot nie jest połączony z żadnym kanałem głosowym.")
        return

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(song['url'], download=False)
            url = info['url']
        except Exception as e:
            await ctx.send(f"Błąd podczas pobierania utworu: {e}")
            return

    def after_playback(error):
        if error:
            print(f"Błąd podczas odtwarzania: {error}")
        next_song = playlist.next_song()
        if next_song:
            fut = asyncio.run_coroutine_threadsafe(play_song(ctx, next_song), bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"Błąd podczas przechodzenia do kolejnego utworu: {e}")
        else:
            fut = asyncio.run_coroutine_threadsafe(voice_client.disconnect(), bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"Błąd podczas rozłączania: {e}")

    voice_client.play(discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'), after=after_playback)
    await ctx.send(f"Odtwarzam: {song['title']}")

@bot.command(name='stop')
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Odtwarzanie zostało zatrzymane.")
    else:
        await ctx.send("Aktualnie nie jest odtwarzana żadna muzyka.")

bot.run('MTI5NzkxMTA3ODI0MzY2Mzk2NQ.Gtfg65.Ltl0IyxWyF1pFl63uur7OBhuyLSZgYnHx8bgEA')
