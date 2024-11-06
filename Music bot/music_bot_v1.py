import discord
from discord.ext import commands
from discord.ui import View, Button
from youtube_search import YoutubeSearch
from apikeys import *
import yt_dlp

# Definiowanie intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

# Stworzenie instancji bota
bot = commands.Bot(command_prefix='!', intents=intents)

# Funkcja wyszukiwania video na YouTube, zwracająca 5 wyników
def search_youtube(query):
    results = YoutubeSearch(query, max_results=5).to_dict()
    return [
        {"title": result["title"], "url": f"https://www.youtube.com/watch?v={result['id']}"}
        for result in results
    ] if results else None

# Funkcja do odtwarzania utworu z podanego URL
async def play_song(ctx, song_url):
    voice_client = ctx.voice_client
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song_url, download=False)
        audio_url = info['url']
        song_title = info.get('title', 'Nieznany tytuł')

        # Użycie poprawnych opcji FFmpeg
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)

        # Odtwarzanie źródła i informowanie o końcu utworu
        voice_client.play(source, after=lambda e: bot.loop.create_task(on_song_end(ctx, song_title)))

        # Wyświetlenie odtwarzanej piosenki
        await ctx.send(f"Odtwarzam: {song_title}")

# Funkcja informująca o zakończeniu utworu
async def on_song_end(ctx, song_title):
    await ctx.send(f"Zakończono odtwarzanie: {song_title}")

# Oddzielna funkcja do obsługi przycisków
async def button_callback(interaction, ctx, url):
    if not ctx.author.voice:
        await interaction.response.send_message("Musisz być na kanale głosowym, aby odtwarzać muzykę.", ephemeral=True)
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

    # Natychmiastowa odpowiedź na interakcję
    await interaction.response.send_message("Rozpoczęto odtwarzanie", ephemeral=True)

    # Uruchom odtwarzanie w osobnym zadaniu
    await play_song(ctx, url)

# Polecenie do wyszukiwania i wyświetlania 5 wyników z przyciskami
@bot.command(name='search')
async def search(ctx, *, query: str):
    search_results = search_youtube(query)
    if search_results:
        view = View()
        for result in search_results:
            # Tworzenie przycisków dla każdego wyniku wyszukiwania
            button = Button(label=result["title"][:80], style=discord.ButtonStyle.primary)
            button.callback = lambda interaction, url=result["url"]: button_callback(interaction, ctx, url)
            view.add_item(button)

        await ctx.send("Wybierz utwór z listy:", view=view)
    else:
        await ctx.send("Nie znaleziono wyników dla podanej frazy.")

# Komendy do zarządzania odtwarzaniem
@bot.command(name='stop')
async def stop(ctx):
    voice_client = ctx.voice_client
    if not voice_client or not voice_client.is_connected():
        await ctx.send("Nie jestem na kanale głosowym.")
        return
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Muzyka zatrzymana.")

@bot.command(name='pause')
async def pause(ctx):
    voice_client = ctx.voice_client
    if not voice_client or not voice_client.is_connected():
        await ctx.send("Nie jestem na kanale głosowym.")
        return
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Muzyka wstrzymana.")

@bot.command(name='resume')
async def resume(ctx):
    voice_client = ctx.voice_client
    if not voice_client or not voice_client.is_connected():
        await ctx.send("Nie jestem na kanale głosowym.")
        return
    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Wznawiam muzykę.")

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

