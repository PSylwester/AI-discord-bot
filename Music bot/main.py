import discord
from discord.ext import commands
from single_play import send_song_selection, stop, pause, resume
from playlist import Playlist, play_playlist_song, create_playlist
from apikeys import *

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.playlist = Playlist()

# Komenda do odtwarzania pojedynczego utworu
@bot.command(name='play')
async def play_command(ctx, *, query: str = None):
    if not ctx.author.voice:
        await ctx.send("Musisz być na kanale głosowym, aby odtwarzać muzykę.")
        return
    if not query:
        await ctx.send("Nie podałeś zapytania. Użyj komendy w formacie: `!play <nazwa utworu lub część tekstu>`")
        return

    await send_song_selection(ctx, query)

# Komenda do tworzenia playlisty
@bot.command(name='create_list')
async def create_playlist_command(ctx, *, query: str = None):
    if not query:
        await ctx.send("Nie podałeś zapytania do utworzenia playlisty. Użyj komendy w formacie: `!create_list <nazwa utworu lub artysty>`")
        return

    await create_playlist(ctx, query, bot.playlist)

# Komenda do odtwarzania playlisty
@bot.command(name='play_list')
async def play_list_command(ctx):
    if not ctx.author.voice:
        await ctx.send("Musisz być na kanale głosowym, aby odtwarzać muzykę.")
        return

    if not bot.playlist.queue:
        await ctx.send("Playlista jest pusta. Użyj komendy `!create_list <zapytanie>`, aby utworzyć playlistę.")
        return

    await play_playlist_song(ctx, bot.playlist)

# Komendy sterujące odtwarzaniem pojedynczego utworu
@bot.command(name='stop')
async def stop_command(ctx):
    await stop(ctx)

@bot.command(name='pause')
async def pause_command(ctx):
    await pause(ctx)

@bot.command(name='resume')
async def resume_command(ctx):
    await resume(ctx)

# Komenda do opuszczania kanału głosowego
@bot.command(name='leave')
async def leave_command(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        bot.playlist.reset()  # Wyczyść playlistę po opuszczeniu kanału
        await ctx.send("Opuszczam kanał głosowy i czyszczę pamięć playlisty.")
    else:
        await ctx.send("Nie jestem na żadnym kanale głosowym.")

# Event informujący użytkownika o błędnej komendzie
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Nieznana komenda. Sprawdź dostępne komendy i spróbuj ponownie.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Brakuje wymaganego argumentu. Sprawdź format komendy.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Podano nieprawidłowy argument. Sprawdź, czy używasz właściwego formatu.")
    else:
        await ctx.send(f"Wystąpił błąd podczas wykonywania komendy: {str(error)}")

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user.name}')

bot.run(BOTTOKEN)
