import discord
import yt_dlp as youtube_dl
import asyncio
from single_play import search_single_song
from discord.ui import View, Button

ydl_opts = {
    'format': 'bestaudio[ext=webm]/bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch'
}

class Playlist:
    def __init__(self):
        self.queue = []
        self.current_index = 0

    def add_songs(self, songs):
        self.queue.extend(songs)
        if len(self.queue) == len(songs):
            self.current_index = 0

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

async def play_playlist_song(ctx, playlist):
    voice_client = ctx.voice_client
    if not voice_client:
        if ctx.author.voice:
            voice_client = await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Musisz być na kanale głosowym, aby odtworzyć muzykę.")
            return

    current_song = playlist.get_current_song()
    if not current_song:
        await ctx.send("Playlista jest pusta.")
        return

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(current_song['url'], download=False)
            url = info['url']
        except Exception as e:
            await ctx.send(f"Błąd podczas pobierania utworu: {e}")
            return

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -user_agent "Mozilla/5.0"',
        'options': '-vn'
    }

    def after_playback(error):
        if error:
            print(f"Błąd podczas odtwarzania: {error}")
        loop = ctx.bot.loop
        fut = asyncio.run_coroutine_threadsafe(play_next_in_playlist(ctx), loop)
        try:
            fut.result()
        except Exception as e:
            print(f"Błąd podczas przechodzenia do kolejnego utworu: {e}")

    if voice_client.is_playing():
        voice_client.stop()

    voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options), after=after_playback)
    await ctx.send(f"Odtwarzam: {current_song['title']}")

async def play_next_in_playlist(ctx):
    playlist = ctx.bot.playlist
    voice_client = ctx.voice_client

    next_track = playlist.next_song()
    if next_track:
        await play_playlist_song(ctx, playlist)
    else:
        await ctx.send("Playlista zakończona.")
        if voice_client:
            await asyncio.sleep(60)
            if not voice_client.is_playing():
                await voice_client.disconnect()


async def create_playlist(ctx, query, playlist):
    search_results = search_single_song(query)
    if search_results:
        playlist.add_songs(search_results)

        # Tworzymy listę tytułów utworów
        song_list = "\n".join([f"{idx + 1}. {song['title']}" for idx, song in enumerate(search_results)])

        # Wysyłamy listę piosenek do kanału
        await ctx.send("Playlista została utworzona z następującymi utworami:\n" + song_list)

        await ctx.send("Użyj komendy !play_list, aby rozpocząć odtwarzanie.")
    else:
        await ctx.send("Nie znaleziono wyników dla podanej frazy.")
