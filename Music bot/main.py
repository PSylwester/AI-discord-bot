import discord
from discord.ext import commands
from single_play import send_song_selection, stop, pause, resume
from playlist import PlaylistManager
from mood_detection import MoodDetection  # Import MoodDetection
from apikeys import BOTTOKEN  # Import tokenu bota

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.playlist = PlaylistManager(bot)
bot.mood_detection = MoodDetection(bot, bot.playlist)  # Inicjalizacja MoodDetection

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

# Komenda do zatrzymania odtwarzania
@bot.command(name='stop')
async def stop_command(ctx):
    await stop(ctx)

# Komenda do wstrzymania odtwarzania
@bot.command(name='pause')
async def pause_command(ctx):
    await pause(ctx)

# Komenda do wznowienia odtwarzania
@bot.command(name='resume')
async def resume_command(ctx):
    await resume(ctx)

# Komendy do zarządzania playlistą
@bot.command(name='create_list')
async def create_playlist_command(ctx, *, query: str = None):
    if not query:
        await ctx.send("Nie podałeś zapytania do utworzenia playlisty. Użyj komendy w formacie: `!create_list <nazwa utworu lub artysty>`")
        return
    await bot.playlist.create_playlist(ctx, query)

@bot.command(name='play_list')
async def play_list_command(ctx):
    if not ctx.author.voice:
        await ctx.send("Musisz być na kanale głosowym, aby odtwarzać muzykę.")
        return

    if not bot.playlist.queue:
        await ctx.send("Playlista jest pusta. Użyj komendy `!create_list <zapytanie>`, aby utworzyć playlistę.")
        return

    await bot.playlist.play_song(ctx)

@bot.command(name='stop_list')
async def stop_list_command(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    bot.playlist.reset()
    await ctx.send("Odtwarzanie playlisty zostało zatrzymane i playlista została wyczyszczona.")

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

# Komendy do wykrywania emocji
@bot.command(name='start_context_music')
async def start_context_music(ctx):
    """Uruchamia monitorowanie aktywności na kanale."""
    await bot.mood_detection.start_monitoring(ctx)

@bot.command(name='stop_context_music')
async def stop_context_music(ctx):
    """Zatrzymuje monitorowanie aktywności na kanale."""
    await bot.mood_detection.stop_monitoring(ctx)

# Event informujący o błędnych komendach
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
