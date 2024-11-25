from discord.ext import tasks
from transformers import pipeline


class MoodDetection:
    def __init__(self, bot, playlist_manager):
        self.bot = bot
        self.playlist_manager = playlist_manager
        self.is_monitoring = False

        # Inicjalizacja modelu do analizy sentymentu
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )

    async def start_monitoring(self, ctx):
        """Rozpoczyna monitorowanie aktywności na kanale."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Musisz być na kanale głosowym, aby rozpocząć monitorowanie.")
            return

        self.is_monitoring = True
        self.voice_channel = ctx.author.voice.channel
        await ctx.send("Rozpoczynam monitorowanie aktywności na kanale głosowym.")
        self.monitor_channel_activity.start(ctx)

    async def stop_monitoring(self, ctx):
        """Zatrzymuje monitorowanie aktywności."""
        self.is_monitoring = False
        self.monitor_channel_activity.stop()
        await ctx.send("Zakończono monitorowanie aktywności i zatrzymano muzykę.")

    def analyze_emotions(self, text):
        """Analizuje emocje w wiadomościach tekstowych za pomocą angielskiego modelu."""
        try:
            # Podział tekstu na fragmenty mieszczące się w limicie modelu
            max_length = 512
            chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]

            # Analiza każdego fragmentu osobno
            sentiments = []
            for chunk in chunks:
                result = self.sentiment_analyzer(chunk)
                sentiments.append(result[0]['label'])

            # Agregowanie wyników
            if sentiments.count("POSITIVE") > sentiments.count("NEGATIVE"):
                return "joy"
            elif sentiments.count("NEGATIVE") > sentiments.count("POSITIVE"):
                return "sadness"
            else:
                return "neutral"

        except Exception as e:
            print(f"[ERROR] Błąd analizy emocji: {e}")
            return None

    @tasks.loop(seconds=30)
    async def monitor_channel_activity(self, ctx):
        """Monitoruje aktywność na kanale tekstowym i dostosowuje muzykę."""
        if not self.is_monitoring:
            return

        try:
            # Pobieranie historii wiadomości
            messages = [message async for message in ctx.channel.history(limit=50)]
            messages_text = " ".join([message.content for message in messages])
            emotion = self.analyze_emotions(messages_text)
            if emotion is None:
                await ctx.send("Nie udało się rozpoznać emocji. Spróbuj ponownie później.")
                return

            # Dobieranie muzyki na podstawie emocji
            if emotion == "joy":
                mood = "happy"
                playlist = ["upbeat song 1", "upbeat song 2", "upbeat song 3"]
            elif emotion == "sadness":
                mood = "calm"
                playlist = ["calm song 1", "calm song 2", "calm song 3"]
            else:
                mood = "neutral"
                playlist = ["neutral song 1", "neutral song 2", "neutral song 3"]

            await ctx.send(f"Rozpoznany nastrój: {mood}. Odtwarzam muzykę odpowiednią do {mood}.")

            # Sprawdzanie playlist_manager
            if self.playlist_manager is None:
                await ctx.send("Błąd: Playlist manager nie został zainicjalizowany.")
                print("[ERROR] Playlist manager is None.")
                return

            await self.playlist_manager.reset()
            self.playlist_manager.add_songs(playlist)
            await self.playlist_manager.play_song(ctx)

        except Exception as e:
            await ctx.send("Wystąpił błąd podczas monitorowania kanału.")
            print(f"[ERROR] Unexpected error: {e}")

