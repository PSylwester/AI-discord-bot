import discord
from discord.ext import tasks
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import yt_dlp as youtube_dl
import asyncio

class AIGameDetection:
    def __init__(self, bot):
        self.bot = bot
        self.is_monitoring = False
        self.voice_channel = None
        self.current_playlist = []
        self.last_checked = None  # Znacznik czasu

        # Ładowanie lokalnego modelu BERT
        model_path = "./models/bert_custom_final"  # Upewnij się, że ścieżka jest poprawna
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
        self.last_checked = ctx.message.created_at  # Ustaw czas rozpoczęcia monitorowania
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
        """Klasyfikuje typ gry za pomocą modelu BERT."""
        # Mapowanie etykiet zwracanych przez model
        label_mapping = {
            "LABEL_0": "rpg",
            "LABEL_1": "shooter",
            "LABEL_2": "strategy",
            "LABEL_3": "general"
        }
        try:
            result = self.text_classifier(text, truncation=True, max_length=512)
            raw_label = result[0]['label']  # np. LABEL_1
            confidence = result[0]['score']
            label = label_mapping.get(raw_label.upper(), "general")

            print(f"Klasyfikacja tekstu: {label} z wynikiem {confidence:.4f}")
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
            "general": "relaxing gaming music"
        }
        return game_music_map.get(game_type, "general gaming music")

    def search_song_with_title(self, query):
        """Wyszukuje link i tytuł utworu na YouTube."""
        options = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'extractor-args': 'youtube:player_client=android',  # Zapewnia kompatybilność
        }
        with youtube_dl.YoutubeDL(options) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
                return info['url'], info.get('title', 'Unknown')
            except Exception as e:
                print(f"[ERROR] Nie udało się znaleźć piosenki: {e}")
                return None, None

    async def play_song(self, ctx, url, retries=3):
        """Odtwarza utwór na kanale głosowym z ponowną próbą w razie błędu."""
        try:
            if not ctx.voice_client:
                await self.voice_channel.connect()

            for attempt in range(retries):
                try:
                    if ctx.voice_client.is_playing():
                        ctx.voice_client.stop()

                    ffmpeg_options = {
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn'
                    }
                    audio_source = discord.FFmpegPCMAudio(url, **ffmpeg_options)
                    ctx.voice_client.play(audio_source)
                    print(f"Rozpoczynam odtwarzanie: {url}")
                    return  # Sukces

                except Exception as e:
                    print(f"[ERROR] Próba {attempt + 1}/{retries} nie powiodła się: {e}")
                    await asyncio.sleep(2)

            await ctx.send("❌ Nie udało się odtworzyć utworu po kilku próbach.")
        except Exception as e:
            print(f"[ERROR] Nie udało się odtworzyć utworu: {e}")
            await ctx.send(f"❌ Błąd podczas odtwarzania: {e}")

    @tasks.loop(seconds=30)
    async def monitor_channel_activity(self, ctx):
        """Monitoruje aktywność na kanale głosowym i odtwarza muzykę w zależności od rodzaju gry."""
        if not self.is_monitoring:
            return

        try:
            # Pobierz wiadomości wysłane po ostatnim sprawdzonym czasie
            messages = [message async for message in ctx.channel.history(after=self.last_checked)]
            self.last_checked = discord.utils.utcnow()  # Aktualizuj znacznik czasu

            # Łącz tekst z wiadomości
            messages_text = " ".join([message.content for message in messages])

            # Klasyfikacja gry
            game_type = self.classify_game_type(messages_text)
            print(f"Wykryty gatunek gry: {game_type}")

            if self.current_playlist and self.current_playlist[0] == game_type:
                print(f"Typ gry ({game_type}) nie zmienił się. Nie zmieniam muzyki.")
                return

            # Znalezienie muzyki
            song_query = self.select_music_for_game(game_type)
            song_url, song_title = self.search_song_with_title(song_query)

            if song_url:
                self.current_playlist = [game_type]
                await self.play_song(ctx, song_url)
                await ctx.send(f"🎮 Wykryto grę typu: **{game_type}**. Odtwarzam muzykę: **{song_title}**.")
            else:
                await ctx.send("❌ Nie udało się znaleźć odpowiedniej muzyki.")
        except Exception as e:
            print(f"[ERROR] Wystąpił błąd podczas monitorowania: {e}")
            await ctx.send("❌ Wystąpił błąd podczas monitorowania kanału.")
