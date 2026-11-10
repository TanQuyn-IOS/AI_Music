from django.db import models
from apps.users.models import User


GENRE_CHOICES = [
    ('pop', 'Pop'), ('rock', 'Rock'), ('jazz', 'Jazz'), ('classical', 'Classical'),
    ('hip_hop', 'Hip Hop'), ('r&b', 'R&B'), ('rnb', 'R&B'), ('electronic', 'Electronic'),
    ('edm', 'EDM'), ('country', 'Country'), ('folk', 'Folk'), ('metal', 'Metal'),
    ('indie', 'Indie'), ('blues', 'Blues'), ('latin', 'Latin'), ('kpop', 'K-Pop'),
    ('vpop', 'V-Pop'), ('jpop', 'J-Pop'), ('cpop', 'C-Pop'), ('ballad', 'Ballad'),
    ('lofi', 'Lo-Fi'), ('acoustic', 'Acoustic'), ('bolero', 'Bolero'), ('other', 'Khác'),
]


MOOD_CHOICES = [
    ('happy', 'Vui vẻ'), ('sad', 'Buồn'), ('energetic', 'Năng động'),
    ('calm', 'Bình yên'), ('romantic', 'Lãng mạn'), ('angry', 'Mạnh mẽ'),
    ('melancholic', 'Hoài niệm'), ('uplifting', 'Phấn khởi'),
]


class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(User, related_name='songs', on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='songs/', null=True, blank=True)
    audio_url = models.CharField(max_length=500, blank=True, default='')
    cover_image = models.ImageField(upload_to='song_covers/', null=True, blank=True)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='other', db_index=True)
    mood = models.CharField(max_length=50, choices=MOOD_CHOICES, blank=True, default='', db_index=True)
    tempo = models.FloatField(null=True, blank=True)
    duration = models.IntegerField(default=0, help_text='Giây')
    lyrics = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    play_count = models.IntegerField(default=0, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'songs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist.username}"

    @property
    def likes_count(self):
        return self.likes.count()


class Playlist(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(User, related_name='playlists', on_delete=models.CASCADE)
    songs = models.ManyToManyField(Song, through='PlaylistSong', related_name='playlists', blank=True)
    cover_image = models.ImageField(upload_to='playlist_covers/', null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'playlists'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} by {self.owner.username}"

    @property
    def songs_count(self):
        return self.songs.count()


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('playlist', 'song')
        ordering = ['order']


class ListenHistory(models.Model):
    user = models.ForeignKey(User, related_name='listen_history', on_delete=models.CASCADE)
    song = models.ForeignKey(Song, related_name='history', on_delete=models.CASCADE)
    listened_at = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_listened = models.IntegerField(default=0)

    class Meta:
        db_table = 'listen_history'
        ordering = ['-listened_at']

    def __str__(self):
        return f"{self.user.username} nghe {self.song.title}"
