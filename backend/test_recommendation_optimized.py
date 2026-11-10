import os
import sys
import time
import unittest

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.ai_engine.recommender import (
    get_content_based_recommendations,
    get_user_based_recommendations,
    get_mood_based_recommendations,
    get_music_profile,
    get_song_neural_vector,
    build_hybrid_song_vector,
)
from apps.music.models import Song, ListenHistory
from apps.users.models import User


class TestOptimizedRecommender(unittest.TestCase):
    """Kiểm thử hiệu năng và độ chính xác của Recommender tối ưu hóa."""

    def setUp(self):
        # Lấy hoặc mock danh sách bài hát
        self.songs = list(Song.objects.filter(is_published=True)[:100])
        if not self.songs:
            # Tạo dummy objects nếu DB trống
            class DummySong:
                def __init__(self, id, title, genre, mood, tempo=120, play_count=10):
                    self.id = id
                    self.title = title
                    self.genre = genre
                    self.mood = mood
                    self.tempo = tempo
                    self.play_count = play_count
                    self.likes_count = 5
                    self.duration = 180
                    self.lyrics = f"Lời bài hát cho {title}"
                    self.tags = ["vpop", "chill"]
            self.songs = [
                DummySong(i, f"Song {i}", "vpop" if i % 2 == 0 else "ballad", "happy" if i % 3 == 0 else "sad")
                for i in range(1, 60)
            ]

    def test_vector_shape_and_normalization(self):
        target = self.songs[0]
        vec = build_hybrid_song_vector(target)
        self.assertEqual(vec.shape, (64,))
        norm = float(sum(x*x for x in vec)**0.5)
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_content_based_recommendation_speed(self):
        target = self.songs[0]
        # Chạy thử và đo thời gian
        t0 = time.perf_counter()
        results = get_content_based_recommendations(target, self.songs, top_n=10)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertTrue(len(results) > 0)
        self.assertNotIn(target, results)
        print(f"\n[PASS] Recommender Content-based: {len(self.songs)} bài hát xử lý trong {elapsed_ms:.2f} ms")
        # Phải chạy dưới 50ms (mục tiêu thực tế là < 5ms)
        self.assertLess(elapsed_ms, 50.0)

    def test_caching_speedup(self):
        target = self.songs[0]
        # Lần 1 nạp cache
        get_content_based_recommendations(target, self.songs, top_n=10)

        # Lần 2 lấy từ cache
        t0 = time.perf_counter()
        results = get_content_based_recommendations(target, self.songs, top_n=10)
        cached_elapsed_ms = (time.perf_counter() - t0) * 1000.0
        print(f"[PASS] Recommender Cached Call: {cached_elapsed_ms:.2f} ms")
        self.assertLess(cached_elapsed_ms, 15.0)

    def test_mood_based_recommendations(self):
        res = get_mood_based_recommendations("happy", self.songs, top_n=5)
        self.assertTrue(len(res) > 0)

    def test_music_profile(self):
        profile = get_music_profile([])
        self.assertEqual(profile["total_listened"], 0)


if __name__ == "__main__":
    unittest.main()
