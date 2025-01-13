import discord
from discord.ext import tasks
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import yt_dlp as youtube_dl
import asyncio
import random

class AIGameDetection:
    def __init__(self, bot):
        self.bot = bot
        self.is_monitoring = False
        self.voice_channel = None
        self.current_playlist = []
        self.last_checked = None  # Znacznik czasu
        self.last_analyzed_text = ""  # Przechowuje ostatnio analizowany tekst

        # Ładowanie lokalnego modelu BERT
        model_path = "./models/bert_custom_final"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.text_classifier = pipeline("text-classification", model=self.model, tokenizer=self.tokenizer, framework="pt")

    async def start_monitoring(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Musisz być na kanale głosowym, aby rozpocząć monitorowanie.")
            return

        self.is_monitoring = True
        self.voice_channel = ctx.author.voice.channel
        self.last_checked = discord.utils.utcnow()
        await ctx.send(f"Rozpoczynam monitorowanie aktywności na kanale głosowym: {self.voice_channel.name}.")
        self.monitor_channel_activity.start(ctx)

    async def stop_monitoring(self, ctx):
        self.is_monitoring = False
        self.monitor_channel_activity.stop()

        # Zatrzymanie odtwarzania muzyki
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await asyncio.sleep(1)  # Dodanie opóźnienia dla bezpiecznego zatrzymania
            print("🛑 Zatrzymano odtwarzanie muzyki.")

        # Wymuszenie zakończenia procesu ffmpeg
        if ctx.voice_client and ctx.voice_client.is_connected():
            await ctx.voice_client.disconnect()
            print("🔌 Bot został rozłączony z kanału głosowego.")

        self.current_playlist.clear()
        await ctx.send("Zakończono monitorowanie i zatrzymano odtwarzanie muzyki.")

    def classify_game_type(self, text):
        label_mapping = {
            "LABEL_0": "rpg",
            "LABEL_1": "shooter",
            "LABEL_2": "strategy",
            "LABEL_3": "general"
        }
        try:
            result = self.text_classifier(text, truncation=True, max_length=512)
            raw_label = result[0]['label']
            confidence = result[0]['score']
            label = label_mapping.get(raw_label.upper(), "general")

            print(f"Klasyfikacja tekstu: {label} z wynikiem {confidence:.4f}")
            return label
        except Exception as e:
            print(f"[ERROR] Błąd klasyfikacji tekstu: {e}")
            return "general"

    def select_music_for_game(self, game_type):
        game_music_map = {
            "shooter": [
                "intense action game soundtrack",
                "fast-paced FPS music",
                "adrenaline pumping shooter music"
            ],
            "strategy": [
                "calm strategy game music",
                "orchestral strategy soundtrack",
                "relaxing strategy background music"
            ],
            "rpg": [
                "epic fantasy RPG music",
                "orchestral RPG soundtrack",
                "adventurous role-playing game music"
            ],
            "general": [
                "gaming background music",
                "relaxing gaming playlist",
                "chill game soundtrack"
            ]
        }
        return random.choice(game_music_map.get(game_type, ["gaming music"]))

    def search_song_with_title(self, query):
        options = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'extractor-args': 'youtube:player_client=android',
        }
        with youtube_dl.YoutubeDL(options) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
                return info['url'], info.get('title', 'Unknown')
            except Exception as e:
                print(f"[ERROR] Nie udało się znaleźć piosenki: {e}")
                return None, None

    async def safe_play_song(self, ctx, url, retries=3):
        for attempt in range(retries):
            try:
                await self.play_song(ctx, url)
                return
            except Exception as e:
                print(f"[ERROR] Próba {attempt + 1}/{retries} nie powiodła się: {e}")
                await asyncio.sleep(2)
        await ctx.send("❌ Nie udało się odtworzyć muzyki po kilku próbach.")

    async def play_song(self, ctx, url):
        if not ctx.voice_client:
            await self.voice_channel.connect()

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        audio_source = discord.FFmpegPCMAudio(url, **ffmpeg_options)
        ctx.voice_client.play(audio_source)
        print(f"Rozpoczynam odtwarzanie: {url}")

    @tasks.loop(seconds=60)
    async def monitor_channel_activity(self, ctx):
        if not self.is_monitoring:
            return

        try:
            messages = [
                message async for message in ctx.channel.history(after=self.last_checked)
                if message.author != self.bot.user and message.content.strip()
            ]
            messages_text = " ".join([message.content for message in messages])

            if not messages_text or messages_text == self.last_analyzed_text:
                print("Brak nowych wiadomości lub tekst się nie zmienił. Pomijam klasyfikację.")
                return

            self.last_analyzed_text = messages_text
            game_type = self.classify_game_type(messages_text)
            print(f"Wykryty gatunek gry: {game_type}")

            if self.current_playlist and self.current_playlist[0] == game_type and ctx.voice_client.is_playing():
                print(f"Typ gry ({game_type}) nie zmienił się. Nie zmieniam muzyki.")
                return

            song_query = self.select_music_for_game(game_type)
            song_url, song_title = self.search_song_with_title(song_query)

            if song_url:
                self.current_playlist = [game_type]
                await self.safe_play_song(ctx, song_url)
                await ctx.send(f"🎮 Wykryto grę typu: **{game_type}**. Odtwarzam muzykę: **{song_title}**.")
            else:
                await ctx.send("❌ Nie udało się znaleźć odpowiedniej muzyki.")
            self.last_checked = discord.utils.utcnow()
        except Exception as e:
            print(f"[ERROR] Wystąpił błąd podczas monitorowania: {e}")
            await ctx.send("❌ Wystąpił błąd podczas monitorowania kanału.")
