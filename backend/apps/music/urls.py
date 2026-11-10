from django.urls import path
from . import views

urlpatterns = [
    path('songs/', views.SongListCreateView.as_view(), name='song-list'),
    path('generate/', views.MusicGenerateUnifiedView.as_view(), name='music-generate-unified'),
    # QUAN TRỌNG: các path tĩnh phải đứng TRƯỚC '<int:pk>/' để tránh bị shadow
    path('songs/trending/', views.TrendingSongsView.as_view(), name='trending'),
    path('songs/semantic-search/', views.SemanticSongSearchView.as_view(), name='semantic-song-search'),
    path('songs/save-ai/', views.SaveAiSongView.as_view(), name='save-ai-song'),
    path('songs/<int:pk>/', views.SongDetailView.as_view(), name='song-detail'),
    path('songs/<int:pk>/extend/', views.SongExtendView.as_view(), name='song-extend'),
    path('songs/<int:pk>/play/', views.IncrementPlayCountView.as_view(), name='song-play'),
    path('playlists/', views.PlaylistListCreateView.as_view(), name='playlist-list'),
    path('playlists/<int:pk>/', views.PlaylistDetailView.as_view(), name='playlist-detail'),
    path('playlists/<int:pk>/songs/', views.PlaylistAddSongView.as_view(), name='playlist-songs'),
    path('history/', views.ListenHistoryView.as_view(), name='listen-history'),
]
