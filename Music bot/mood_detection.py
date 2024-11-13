import discord
from discord.ext import tasks
from transformers import pipeline


class MoodDetection:
    def __init__(self, bot, playlist_manager):
        self.bot = bot
        self.playlist_manager = playlist_manager
        self.is_monitoring = False

        # Inicjalizacja modelu do analizy emocji
        self.emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base",
                                           return_all_scores=True)

    async def start_monitoring(self, ctx):
        """Rozpoczyna monitorowanie aktywności na kanale z AI do analizy emocji."""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("Musisz być na kanale głosowym, aby rozpocząć monitorowanie.")
                return

            self.is_monitoring = True
            self.voice_channel = ctx.author.voice.channel
            await ctx.send("Rozpoczynam monitorowanie emocji na kanale i dostosowywanie muzyki.")
            self.monitor_channel_activity.start(ctx)

        except discord.DiscordException as e:
            await ctx.send("Wystąpił błąd podczas uruchamiania monitorowania.")
            print(f"[ERROR] DiscordException: {e}")

        except Exception as e:
            await ctx.send("Wystąpił niespodziewany błąd. Spróbuj ponownie.")
            print(f"[ERROR] Unexpected error: {e}")

    async def stop_monitoring(self, ctx):
        """Zatrzymuje monitorowanie aktywności na kanale z kontrolą błędów."""
        try:
            self.is_monitoring = False
            self.monitor_channel_activity.stop()
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            await ctx.send("Zakończono monitorowanie emocji na kanale i zatrzymano muzykę.")

        except discord.DiscordException as e:
            await ctx.send("Wystąpił błąd podczas zatrzymywania monitorowania.")
            print(f"[ERROR] DiscordException: {e}")

        except Exception as e:
            await ctx.send("Wystąpił niespodziewany błąd. Spróbuj ponownie.")
            print(f"[ERROR] Unexpected error: {e}")

    async def analyze_emotions(self, text):
        """Analizuje emocje na podstawie tekstu przy użyciu modelu AI."""
        try:
            # Używamy modelu do analizy emocji w tekście
            emotions = self.emotion_classifier(text)
            # Sortowanie wyników i wybór emocji z najwyższym prawdopodobieństwem
            dominant_emotion = max(emotions[0], key=lambda x: x['score'])['label']
            return dominant_emotion
        except Exception as e:
            print(f"[ERROR] Błąd analizy emocji: {e}")
            return None

    @tasks.loop(seconds=30)
    async def monitor_channel_activity(self, ctx):
        """Monitoruje aktywność na kanale co 30 sekund i dostosowuje muzykę na podstawie analizy emocji."""
        if not self.is_monitoring:
            return

        try:
            # Pobieramy ostatnie wiadomości z kanału
            messages = await ctx.channel.history(limit=50).flatten()
            messages_text = " ".join([message.content for message in messages])

            # Analizujemy emocje w zebranych wiadomościach
            emotion = await self.analyze_emotions(messages_text)

            # Dostosowanie playlisty na podstawie emocji
            if emotion == "joy":
                mood = "happy"
                playlist = ["upbeat song 1", "upbeat song 2", "upbeat song 3"]
            elif emotion == "sadness":
                mood = "calm"
                playlist = ["calm song 1", "calm song 2", "calm song 3"]
            elif emotion == "anger":
                mood = "intense"
                playlist = ["intense song 1", "intense song 2", "intense song 3"]
            else:
                mood = "neutral"
                playlist = ["neutral song 1", "neutral song 2", "neutral song 3"]

            await ctx.send(f"Rozpoznany nastrój: {mood}. Odtwarzam muzykę odpowiednią do {mood}.")

            # Reset playlisty i odtworzenie dostosowanej muzyki
            await self.playlist_manager.reset()
            self.playlist_manager.add_songs(playlist)
            await self.playlist_manager.play_song(ctx)

        except discord.DiscordException as e:
            await ctx.send("Wystąpił błąd podczas monitorowania kanału.")
            print(f"[ERROR] DiscordException: {e}")

        except Exception as e:
            await ctx.send("Wystąpił niespodziewany błąd podczas monitorowania kanału.")
            print(f"[ERROR] Unexpected error: {e}")
