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

async def ensure_voice_connection(source_ctx):
    """Reconnect to the voice channel if disconnected unexpectedly."""
    if isinstance(source_ctx, discord.Interaction):
        user = source_ctx.user
    else:
        user = source_ctx.author

    guild = source_ctx.guild
    channel = user.voice.channel if user.voice else None

    if channel:
        voice_client = guild.voice_client
        if not isinstance(voice_client, discord.VoiceClient) or not voice_client.is_connected():
            voice_client = await channel.connect()
        return voice_client
    else:
        if isinstance(source_ctx, discord.Interaction):
            await source_ctx.response.send_message("Musisz być na kanale głosowym, aby odtwarzać muzykę.")
        else:
            await source_ctx.send("Musisz być na kanale głosowym, aby odtwarzać muzykę.")
        return None

async def play_single_song(ctx_or_interaction, song_url):
    voice_client = await ensure_voice_connection(ctx_or_interaction)
    if not voice_client or not isinstance(voice_client, discord.VoiceClient):
        return  # Exit if no connection could be established

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

            if voice_client.is_playing():
                voice_client.stop()  # Stop any existing audio before playing new one

            voice_client.play(source)
            message = f"Odtwarzam: {song_title}"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(message)
            else:
                await ctx_or_interaction.send(message)
    except Exception as e:
        error_message = "Wystąpił błąd podczas odtwarzania utworu."
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(error_message)
        else:
            await ctx_or_interaction.send(error_message)
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

async def stop(ctx):
    voice_client = ctx.voice_client
    if isinstance(voice_client, discord.VoiceClient) and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Muzyka zatrzymana.")

async def pause(ctx):
    voice_client = ctx.voice_client
    if isinstance(voice_client, discord.VoiceClient) and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Muzyka wstrzymana.")

async def resume(ctx):
    voice_client = ctx.voice_client
    if isinstance(voice_client, discord.VoiceClient) and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Wznawiam muzykę.")
