import discord
from discord.ext import commands, tasks
from mood_detection import AIGameDetection
from apikeys import BOTTOKEN

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.mood_detection = AIGameDetection(bot=bot)
bot.silent_mode = False  # Tryb cichy wyłączony domyślnie

# Komenda do opuszczania kanału głosowego
@bot.command(name='leave')
async def leave_command(ctx):
    try:
        voice_client = ctx.voice_client

        # Zatrzymaj monitorowanie aktywności, jeśli działa
        if bot.mood_detection.is_monitoring:
            bot.mood_detection.is_monitoring = False
            bot.mood_detection.monitor_channel_activity.cancel()
            await ctx.send("Zatrzymano monitorowanie aktywności na kanale.")

        # Rozłącz bota z kanału głosowego
        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            await ctx.send("Opuszczam kanał głosowy.")
        else:
            await ctx.send("Nie jestem na żadnym kanale głosowym.")
    except Exception as e:
        print(f"[ERROR] Wystąpił błąd w leave_command: {e}")

# Komenda do wykrywania rodzaju gry i odtwarzania muzyki
@bot.command(name='start_context_music')
async def start_context_music(ctx):
    await bot.mood_detection.start_monitoring(ctx)

@bot.command(name='stop_context_music')
async def stop_context_music(ctx):
    await bot.mood_detection.stop_monitoring(ctx)

# Komenda do sprawdzenia statusu bota
@bot.command(name='status')
async def status(ctx):
    if bot.mood_detection.is_monitoring:
        await ctx.send("🔍 Bot monitoruje aktywność i odtwarza muzykę.")
    else:
        await ctx.send("🛑 Bot jest nieaktywny.")

# Komenda do przełączania trybu cichego
@bot.command(name='silent')
async def toggle_silent_mode(ctx):
    bot.silent_mode = not bot.silent_mode
    state = "włączony" if bot.silent_mode else "wyłączony"
    await ctx.send(f"🔕 Tryb cichy został {state}.")

# Obsługa błędów komend
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

# Informacja o uruchomieniu bota
@bot.event
async def on_ready():
    print(f'Bot jest gotowy. Zalogowano jako {bot.user.name}')

bot.run(BOTTOKEN)
