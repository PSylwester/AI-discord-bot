import discord
from discord.ext import commands
from mood_detection import AIGameDetection

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

def setup_music(bot: commands.Bot, on_ready_callbacks: list, on_message_callbacks: list):
    bot.mood_detection = AIGameDetection(bot=bot)
    bot.silent_mode = False  # Tryb cichy wyłączony domyślnie

    # Komenda do wykrywania rodzaju gry i odtwarzania muzyki
    @bot.command(name='start')
    async def start_context_music(ctx):
        """
        Starts monitoring the voice channel activity and plays music based on the detected game type.

        Usage:
        !start
        """
        await bot.mood_detection.start_monitoring(ctx)

    @bot.command(name='stop')
    async def stop_context_music(ctx):
        """
        Stops monitoring the voice channel activity and stops music playback.

        Usage:
        !stop
        """
        await bot.mood_detection.stop_monitoring(ctx)

    @bot.command(name='pause')
    async def pause_music(ctx):
        """
        Pauses the currently playing music on the voice channel.

        Usage:
        !pause
        """
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Muzyka została wstrzymana.")
        else:
            await ctx.send("❌ Nie odtwarzam żadnej muzyki.")

    @bot.command(name='resume')
    async def resume_music(ctx):
        """
        Resumes the paused music on the voice channel.

        Usage:
        !resume
        """
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Wznawiam odtwarzanie muzyki.")
        else:
            await ctx.send("❌ Muzyka nie jest wstrzymana.")

    # Komenda do sprawdzenia statusu bota
    @bot.command(name='status')
    async def status(ctx):
        """
        Displays the current status of the bot: whether it is monitoring the channel and playing music.

        Usage:
        !status
        """
        if bot.mood_detection.is_monitoring:
            await ctx.send("🔍 Bot monitoruje aktywność i odtwarza muzykę.")
        else:
            await ctx.send("🛑 Bot jest nieaktywny.")

    # Komenda do przełączania trybu cichego
    @bot.command(name='silent')
    async def toggle_silent_mode(ctx):
        """
        Toggles the silent mode on or off. In silent mode, the bot will not send messages.

        Usage:
        !silent
        """
        bot.silent_mode = not bot.silent_mode
        state = "włączony" if bot.silent_mode else "wyłączony"
        await ctx.send(f"🔕 Tryb cichy został {state}.")

    @bot.command(name='volume')
    async def change_volume(ctx, volume: int):
        """
        Changes the volume of the currently playing music. The volume can be set between 0 and 100.

        Usage:
        !volume <0-100>
        Example:
        !volume 70  -> Sets the volume to 70%
        """
        if 0 <= volume <= 100:
            bot.mood_detection.volume = volume / 100  # Zamiana wartości na zakres 0.0 - 1.0

            # Sprawdzenie, czy bot odtwarza muzykę
            if ctx.voice_client and ctx.voice_client.source:
                # Sprawdzenie, czy źródło to PCMVolumeTransformer (czyli obsługuje głośność)
                if isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
                    ctx.voice_client.source.volume = bot.mood_detection.volume  # Dynamiczna zmiana głośności

            await ctx.send(f"🔊 Głośność ustawiona na {volume}%.")
        else:
            await ctx.send("❌ Podaj wartość z zakresu od 0 do 100.")

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

    @bot.event
    async def music_on_message(message):
        # Ignoruj wiadomości wysłane przez bota
        if message.author == bot.user:
            return

        # await bot.process_commands(message)
    # Rejestrujemy `translate_on_ready` w liście callbacków
    on_message_callbacks.append(music_on_message)

    # Informacja o uruchomieniu bota
    @bot.event
    async def music_on_ready():
        print(f'MusicBot module on ready is ready as {bot.user.name}')
    # Rejestrujemy `translate_on_ready` w liście callbacków
    on_ready_callbacks.append(music_on_ready)

print("[MUSICBOT] Functions loaded.")