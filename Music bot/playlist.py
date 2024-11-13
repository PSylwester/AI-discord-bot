import discord
import yt_dlp as youtube_dl
from single_play import search_single_song  # Zakładam, że funkcja wyszukiwania jest w pliku single_play

ydl_opts = {
    'format': 'bestaudio[ext=webm]/bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch'
}

class PlaylistManager:
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current_index = 0
        self.is_playing = False

    def add_songs(self, songs):
        """Dodaje utwory do kolejki playlisty."""
        self.queue.extend(songs)
        if len(self.queue) == len(songs):
            self.current_index = 0
        print(f"[DEBUG] Dodano utwory do kolejki. Liczba utworów: {len(self.queue)}")

    def get_current_song(self):
        """Zwraca bieżący utwór."""
        song = self.queue[self.current_index] if self.queue else None
        print(f"[DEBUG] Bieżący utwór: {song['title'] if song else 'Brak'} na pozycji {self.current_index}")
        return song

    def next_song(self):
        """Przechodzi do następnego utworu i aktualizuje wskaźnik."""
        if self.current_index < len(self.queue) - 1:
            self.current_index += 1
            print(f"[DEBUG] Przejście do następnego utworu. Nowy indeks: {self.current_index}")
            return self.queue[self.current_index]
        else:
            print("[DEBUG] Koniec kolejki, brak kolejnego utworu.")
        return None

    def reset(self):
        """Czyści playlistę i zatrzymuje odtwarzanie."""
        self.queue = []
        self.current_index = 0
        self.is_playing = False
        print("[DEBUG] Playlista została wyczyszczona.")

    async def play_next(self, ctx):
        """Przechodzi do następnego utworu w kolejce, jeśli istnieje."""
        self.next_song()  # Przesuń wskaźnik do następnego utworu
        if not self.queue or self.current_index >= len(self.queue):  # Sprawdź, czy nadal są utwory
            self.is_playing = False
            await ctx.send("Playlista zakończona.")
            print("[DEBUG] Playlista zakończona.")
            return

        await self.play_song(ctx)

    async def play_song(self, ctx):
        """Rozpoczyna odtwarzanie bieżącego utworu."""
        current_song = self.get_current_song()
        if not current_song:
            await ctx.send("Playlista jest pusta.")
            return

        voice_client = ctx.voice_client
        if not voice_client:
            if ctx.author.voice:
                voice_client = await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Musisz być na kanale głosowym, aby odtwarzać muzykę.")
                return

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(current_song['url'], download=False)
                url = info['url']
            except Exception as e:
                await ctx.send(f"Błąd podczas pobierania utworu: {e}")
                print(f"[DEBUG] Błąd pobierania: {e}")
                return

        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -user_agent "Mozilla/5.0"',
            'options': '-vn'
        }

        def after_callback(error):
            """Callback `after` wywołujący `play_next` tylko, jeśli playlista nie jest zatrzymana i nie została zresetowana."""
            if self.is_playing and self.queue and self.current_index < len(self.queue):
                print("[DEBUG] Wywołanie after_callback i przejście do następnego utworu.")
                self.bot.loop.create_task(self.play_next(ctx))
            else:
                print("[DEBUG] Callback after zatrzymany - playlista zatrzymana lub wyczyszczona.")

        self.is_playing = True
        voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options), after=after_callback)
        await ctx.send(f"Odtwarzam: {current_song['title']}")
        print(f"[DEBUG] Rozpoczęto odtwarzanie utworu: {current_song['title']}")

    async def create_playlist(self, ctx, query):
        """Tworzy nową playlistę na podstawie wyszukiwania utworów, zatrzymuje aktualne odtwarzanie i czyści poprzednią kolejkę."""

        # Sprawdzenie i zatrzymanie odtwarzania, jeśli bot odtwarza muzykę
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            self.is_playing = False  # Wyłącz automatyczne odtwarzanie dla bieżącego callbacku
            voice_client.stop()
            await ctx.send("Odtwarzanie zostało zatrzymane, aby utworzyć nową playlistę.")

        # Wyczyść poprzednią playlistę i zresetuj wszystkie wskaźniki
        self.reset()

        # Wyszukaj i dodaj nowe utwory do playlisty
        search_results = search_single_song(query)
        if search_results:
            self.add_songs(search_results)
            song_list = "\n".join([f"{idx + 1}. {song['title']}" for idx, song in enumerate(search_results)])
            await ctx.send(f"Playlista została utworzona z następującymi utworami:\n{song_list}")
            await ctx.send("Użyj komendy !play_list, aby rozpocząć odtwarzanie.")
            print(f"[DEBUG] Playlista utworzona z {len(search_results)} utworów.")
        else:
            await ctx.send("Nie znaleziono wyników dla podanej frazy.")
            print("[DEBUG] Brak wyników wyszukiwania.")





