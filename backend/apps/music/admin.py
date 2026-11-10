from django.contrib import admin
from .models import Song, Playlist, PlaylistSong, ListenHistory


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'genre', 'mood', 'play_count', 'is_published', 'created_at']
    list_filter = ['genre', 'mood', 'is_published']
    search_fields = ['title', 'artist__username']
    list_editable = ['is_published']
    ordering = ['-created_at']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'songs_count', 'is_public', 'created_at']
    list_filter = ['is_public']
    search_fields = ['name', 'owner__username']


@admin.register(PlaylistSong)
class PlaylistSongAdmin(admin.ModelAdmin):
    list_display = ['playlist', 'song', 'order', 'added_at']
    ordering = ['playlist', 'order']


@admin.register(ListenHistory)
class ListenHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'song', 'listened_at', 'duration_listened']
    list_filter = ['listened_at']
    search_fields = ['user__username', 'song__title']
    ordering = ['-listened_at']
