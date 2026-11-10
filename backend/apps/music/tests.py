from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.music.models import Song, Playlist, PlaylistSong

User = get_user_model()


class MusicSystemTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='producer', password='password123')
        self.song = Song.objects.create(
            title='Mùa Thu Hà Nội',
            artist=self.user,
            genre='ballad',
            mood='sad',
            audio_url='https://example.com/audio/muathuhanoi.mp3',
            duration=180,
            play_count=10,
            is_published=True,
            tags='hanoi, mua thu, ballad, vietnamese'
        )

    def test_song_list_and_filter(self):
        res = self.client.get('/api/music/songs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Mùa Thu Hà Nội')

    def test_atomic_play_count_increment(self):
        initial_plays = self.song.play_count
        # Request with ?play=1 triggers atomic F('play_count') + 1 increment
        res = self.client.get(f'/api/music/songs/{self.song.id}/?play=1')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.song.refresh_from_db()
        self.assertEqual(self.song.play_count, initial_plays + 1)

    def test_playlist_creation_and_song_addition(self):
        self.client.force_authenticate(user=self.user)
        # Create playlist
        res = self.client.post('/api/music/playlists/', {
            'title': 'My Chill Playlist',
            'is_public': True
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        playlist_id = res.data['id']

        # Add song to playlist
        add_res = self.client.post(f'/api/music/playlists/{playlist_id}/songs/', {
            'song_id': self.song.id
        }, format='json')
        self.assertEqual(add_res.status_code, status.HTTP_200_OK)
        self.assertEqual(PlaylistSong.objects.filter(playlist_id=playlist_id, song=self.song).count(), 1)

    def test_semantic_song_search_3072_dims(self):
        res = self.client.get('/api/music/songs/semantic-search/?q=mùa thu buồn')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['type'], 'neural_semantic_3072')
        self.assertIn('results', res.data)
        # Found matches should include our ballad song
        results = res.data['results']
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Mùa Thu Hà Nội')
        self.assertIn('similarity_score', results[0])

