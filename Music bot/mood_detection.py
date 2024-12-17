import discord
from discord.ext import tasks
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import yt_dlp as youtube_dl

class AIGameDetection:
    def __init__(self, bot):
        self.bot = bot
        self.is_monitoring = False
        self.voice_channel = None
        self.current_playlist = []

        # Ładowanie lokalnego modelu BERT
        model_path = "./models/bert"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.text_classifier = pipeline("text-classification", model=self.model, tokenizer=self.tokenizer, framework="pt")

    async def start_monitoring(self, ctx):
        """Rozpoczyna monitorowanie aktywności na kanale z automatycznym wykrywaniem gry."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Musisz być na kanale głosowym, aby rozpocząć monitorowanie.")
            return

        self.is_monitoring = True
        self.voice_channel = ctx.author.voice.channel
        await ctx.send(f"Rozpoczynam monitorowanie aktywności na kanale głosowym: {self.voice_channel.name}.")
        self.monitor_channel_activity.start(ctx)

    async def stop_monitoring(self, ctx):
        """Zatrzymuje monitorowanie aktywności."""
        self.is_monitoring = False
        self.monitor_channel_activity.stop()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        self.current_playlist.clear()
        await ctx.send("Zakończono monitorowanie i zatrzymano odtwarzanie muzyki.")

    def classify_game_type(self, text):
        """Klasyfikuje typ gry na podstawie analizy tekstu za pomocą lokalnego modelu BERT."""
        try:
            result = self.text_classifier(text, truncation=True, max_length=512)
            label = result[0]['label'].lower()
            print(f"Klasyfikacja tekstu: {label} z wynikiem {result[0]['score']}")
            return label
        except Exception as e:
            print(f"[ERROR] Błąd klasyfikacji tekstu: {e}")
            return "general"

    def select_music_for_game(self, game_type):
        """Dobiera muzykę na podstawie rodzaju gry."""
        game_music_map = {
            "shooter": "intense action music",
            "strategy": "calm strategy music",
            "rpg": "epic fantasy music",
            "horror": "horror suspense music",
        }
        return game_music_map.get(game_type, "general gaming music")

    def search_song(self, query):
        """Wyszukuje link do utworu na YouTube."""
        options = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }
        with youtube_dl.YoutubeDL(options) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
                return info['url']
            except Exception as e:
                print(f"[ERROR] Nie udało się znaleźć piosenki: {e}")
                return None

    async def play_song(self, ctx, url):
        """Odtwarza utwór na kanale głosowym."""
        try:
            if not ctx.voice_client:
                await self.voice_channel.connect()

            ctx.voice_client.stop()
            ctx.voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: print(f"Zakończono odtwarzanie: {e}"))
            print(f"Rozpoczynam odtwarzanie: {url}")
        except Exception as e:
            await ctx.send(f"Błąd podczas odtwarzania utworu: {e}")
            print(f"[ERROR] {e}")

    @tasks.loop(seconds=30)
    async def monitor_channel_activity(self, ctx):
        """Monitoruje aktywność na kanale głosowym i odtwarza muzykę w zależności od rodzaju gry."""
        if not self.is_monitoring:
            return

        try:
            messages = [message async for message in ctx.channel.history(limit=50)]
            messages_text = " ".join([message.content for message in messages])

            game_type = self.classify_game_type(messages_text)

            if self.current_playlist and self.current_playlist[0] == game_type:
                print(f"Typ gry ({game_type}) nie zmienił się. Nie zmieniam muzyki.")
                return

            song_query = self.select_music_for_game(game_type)
            song_url = self.search_song(song_query)

            if song_url:
                self.current_playlist = [song_url]
                await self.play_song(ctx, song_url)
                await ctx.send(f"Wykryto grę typu: {game_type}. Odtwarzam muzykę: {song_query}.")
            else:
                await ctx.send("Nie udało się znaleźć odpowiedniej muzyki.")
        except Exception as e:
            print(f"[ERROR] Wystąpił błąd podczas monitorowania: {e}")
            await ctx.send("Wystąpił błąd podczas monitorowania kanału.")
