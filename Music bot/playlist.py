from single_play import play_single_song, search_single_song


class Playlist:
    def __init__(self):
        self.queue = []
        self.current_index = 0

    def add_songs(self, songs):
        self.queue = songs
        self.current_index = 0

    def get_current_song(self):
        return self.queue[self.current_index] if self.queue else None

    def next_song(self):
        if self.current_index < len(self.queue) - 1:
            self.current_index += 1
            return self.queue[self.current_index]
        return None

    def reset(self):
        self.queue = []
        self.current_index = 0


async def play_playlist_song(ctx, playlist):
    current_song = playlist.get_current_song()
    if current_song:
        voice_client = ctx.voice_client
        await play_single_song(ctx, current_song["url"])

        # Ustawienie automatycznego przejścia do kolejnego utworu
        def after_playback(error):
            if error:
                print(f"Błąd podczas odtwarzania: {error}")
            else:
                # Przejście do następnego utworu po zakończeniu
                ctx.bot.loop.create_task(play_next_in_playlist(ctx))

        # Sprawdzenie, czy voice_client istnieje i odtwarza
        if voice_client and not voice_client.is_playing():
            voice_client.play(voice_client.source, after=after_playback)



async def play_next_in_playlist(ctx):
    playlist = ctx.bot.playlist
    voice_client = ctx.voice_client

    if voice_client and voice_client.is_playing():
        voice_client.stop()

    next_track = playlist.next_song()
    if next_track:
        await play_playlist_song(ctx, playlist)
    else:
        await ctx.send("Playlista zakończona.")
        if voice_client:
            await voice_client.disconnect()


async def display_playlist(ctx, playlist):
    if playlist.queue:
        playlist_text = "\n".join([f"{idx + 1}. {song['title']}" for idx, song in enumerate(playlist.queue)])
        await ctx.send(f"**Playlista:**\n{playlist_text}")
    else:
        await ctx.send("Playlista jest pusta.")


async def create_playlist(ctx, query, playlist):
    search_results = search_single_song(query)
    if search_results:
        playlist.add_songs(search_results)
        await display_playlist(ctx, playlist)
        await ctx.send("Playlista została utworzona. Użyj komendy !play_list, aby rozpocząć odtwarzanie.")
    else:
        await ctx.send("Nie znaleziono wyników dla podanej frazy.")
