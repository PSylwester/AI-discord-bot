import discord
from youtube_search import YoutubeSearch
import yt_dlp
from discord.ui import View, Button
from functools import partial


def search_single_song(query):
    results = YoutubeSearch(query, max_results=10).to_dict()
    return [
        {"title": result["title"], "url": f"https://www.youtube.com/watch?v={result['id']}"}
        for result in results
    ] if results else None


async def play_single_song(ctx, song_url):
    guild = ctx.guild
    user = ctx.author  # Zmieniono z ctx.user na ctx.author

    if not user.voice:
        await ctx.send("Musisz być na kanale głosowym, aby odtwarzać muzykę.")
        return

    channel = user.voice.channel
    voice_client = guild.voice_client

    if not voice_client or not voice_client.is_connected():
        voice_client = await channel.connect()
    else:
        if voice_client.is_playing():
            voice_client.stop()

    ydl_opts = {'format': 'bestaudio', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_url, download=False)
            audio_url = info['url']
            song_title = info.get('title', 'Nieznany tytuł')
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)

            voice_client.play(source)
            await ctx.send(f"Odtwarzam: {song_title}")
    except Exception as e:
        await ctx.send("Wystąpił błąd podczas odtwarzania utworu.")
        print(f"Błąd: {e}")


async def button_callback(interaction: discord.Interaction, url):
    await play_single_song(interaction, url)


async def send_song_selection(ctx, query):
    search_results = search_single_song(query)
    if search_results:
        view = View(timeout=600)
        for result in search_results:
            button = Button(label=result["title"][:80], style=discord.ButtonStyle.primary)
            button.callback = partial(button_callback, url=result["url"])
            view.add_item(button)

        await ctx.send("Wybierz utwór z listy:", view=view)


async def leave_channel(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("Opuszczam kanał głosowy.")


async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Muzyka zatrzymana.")


async def pause(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Muzyka wstrzymana.")


async def resume(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Wznawiam muzykę.")
