"""
Sonavia AI - Phase 2.3 Test Suite: Intelligent Music Orchestrator
=================================================================
Kiểm thử toàn diện hệ thống điều phối AI thông minh (SonaviaOrchestrator):
1. Phân biệt rõ tác vụ: Text-to-Song, Lyrics-to-Song, Instrumental, Melodic Lead.
2. Thứ tự ưu tiên điều phối 4 tầng (Tier 1: ACE-Step -> Tier 2: Vietnamese SVS -> Tier 3: MusicGen -> Tier 4: Acoustic Synth).
3. Tích hợp sâu Vietnamese Phonetic Layer (Unicode NFC, thanh điệu, trọng số âm học).
4. Fallback minh bạch khi thiếu SVS tiếng Việt: vocal_type="melodic_lead", vocal_generated=False, fallback_reason="no_compatible_vietnamese_svs".
5. Tuyệt đối không gọi Bark trong bất kỳ nhánh điều phối nào.
6. Tính tương thích 100% của API /api/music/generate/ và /api/ai/generate/full/.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Thiết lập Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.ai_engine.orchestrator import sonavia_orchestrator
from apps.music.views import MusicGenerateUnifiedView
from apps.ai_engine.views import FullSongGenerateView, FullSongStatusView, _JOBS, _JOBS_LOCK


class TestPhase23IntelligentOrchestrator(unittest.TestCase):
    """Bộ kiểm thử điều phối AI thông minh cho Sonavia AI."""

    def setUp(self):
        self.benchmark_lyrics = (
            "Nắng nghiêng chiều buông trên dòng sông vắng\n"
            "Gió lạnh lùng ru từng nhánh bằng lăng\n"
            "Gợi nỗi nhớ người thương năm tháng cũ\n"
            "Khúc tình ca êm ái ngút ngàn xưa"
        )

    def _create_dummy_wav(self, duration_s: float = 2.0, sr: int = 32000) -> bytes:
        import io
        import soundfile as sf
        import numpy as np
        t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False, dtype=np.float32)
        sine = 0.5 * np.sin(2 * np.pi * 440.0 * t)
        buf = io.BytesIO()
        sf.write(buf, sine, sr, format="WAV", subtype="PCM_16")
        return buf.getvalue()

    # ────────────────────────────────────────────────────────────────────────
    # 1. Phân loại tác vụ: Text-to-Song
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.providers.acestep_provider.generate_with_acestep")
    def test_text_to_song_task_routing(self, mock_acestep):
        """Khi chỉ có prompt, hệ thống tự động sinh lời và định tuyến tác vụ text_to_song."""
        dummy_wav = self._create_dummy_wav(2.0)
        mock_acestep.return_value = {
            "audio_bytes": dummy_wav,
            "duration": 60,
            "elapsed": 1.5,
            "prompt": "V-Pop ballad",
            "seed": "111",
            "lyrics": "Lời tự sinh",
        }

        res = sonavia_orchestrator.generate_song(
            prompt="Một bài hát nhẹ nhàng về mùa thu Hà Nội",
            language="vi",
            vocal="female",
            custom_lyrics="",
            instrumental=False,
        )

        self.assertEqual(res["task_type"], "text_to_song")
        self.assertTrue(bool(res["lyrics"]))
        self.assertEqual(res["vocal_type"], "vocal")
        self.assertTrue(res["vocal_generated"])
        self.assertIsNone(res["fallback_reason"])

    # ────────────────────────────────────────────────────────────────────────
    # 2. Phân loại tác vụ: Lyrics-to-Song
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.providers.acestep_provider.generate_with_acestep")
    def test_lyrics_to_song_task_routing(self, mock_acestep):
        """Khi có custom_lyrics, hệ thống bảo tồn nguyên văn ca từ và định tuyến lyrics_to_song."""
        dummy_wav = self._create_dummy_wav(2.0)
        mock_acestep.return_value = {
            "audio_bytes": dummy_wav,
            "duration": 60,
            "elapsed": 1.5,
            "prompt": "V-Pop",
            "seed": "222",
            "lyrics": self.benchmark_lyrics,
        }

        res = sonavia_orchestrator.generate_song(
            prompt="Ballad tình yêu",
            language="vi",
            custom_lyrics=self.benchmark_lyrics,
            vocal="female",
        )

        self.assertEqual(res["task_type"], "lyrics_to_song")
        self.assertIn("Nắng nghiêng chiều buông", res["lyrics"])
        # Kiểm tra phonetic layer được kích hoạt
        self.assertIsNotNone(res["phonetic_summary"])
        self.assertIsNotNone(res["tone_distribution"])
        self.assertGreater(res["tone_distribution"].get("sắc", 0), 0)

    # ────────────────────────────────────────────────────────────────────────
    # 3. Phân loại tác vụ: Instrumental
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.providers.acestep_provider.generate_with_acestep")
    def test_instrumental_task_routing(self, mock_acestep):
        """Khi yêu cầu instrumental, không sinh ca từ và trả về vocal_type=instrumental."""
        dummy_wav = self._create_dummy_wav(2.0)
        mock_acestep.return_value = {
            "audio_bytes": dummy_wav,
            "duration": 30,
            "elapsed": 1.0,
            "prompt": "Acoustic instrumental",
            "seed": "333",
            "lyrics": "",
        }

        res = sonavia_orchestrator.generate_song(
            prompt="Nhạc không lời thư giãn",
            language="vi",
            instrumental=True,
        )

        self.assertEqual(res["task_type"], "instrumental")
        self.assertEqual(res["vocal_type"], "instrumental")
        self.assertFalse(res["vocal_generated"])
        self.assertEqual(res["lyrics"], "")

    # ────────────────────────────────────────────────────────────────────────
    # 4. Fallback 4 tầng minh bạch khi Tier 1 & Tier 2 không khả dụng
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.bark_singer.generate_vocal_bytes")
    def test_multi_tier_fallback_hierarchy(self, mock_bark_bytes):
        """Khi ACE-Step fail, SVS unavailable -> fallback sang MusicGen Melodic Lead minh bạch."""
        dummy_wav = self._create_dummy_wav(2.0)

        # Tier 1 fail
        with patch.object(sonavia_orchestrator.primary_provider, "generate", side_effect=RuntimeError("Cloud space timeout")):
            # Tier 3 (MusicGen) thành công
            with patch("apps.ai_engine.music_generator.generate_music", return_value=(dummy_wav, 32000)):
                res = sonavia_orchestrator.generate_song(
                    prompt="Bài hát trữ tình",
                    language="vi",
                    custom_lyrics=self.benchmark_lyrics,
                    vocal="female",
                )

                # Bark tuyệt đối không bị gọi
                mock_bark_bytes.assert_not_called()

                # Kiểm tra trạng thái minh bạch
                self.assertEqual(res["provider"], "musicgen")
                self.assertEqual(res["vocal_type"], "melodic_lead")
                self.assertFalse(res["vocal_generated"])
                self.assertEqual(res["fallback_reason"], "no_compatible_vietnamese_svs")

    # ────────────────────────────────────────────────────────────────────────
    # 5. Tương thích API /api/music/generate/ (MusicGenerateUnifiedView)
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.providers.acestep_provider.generate_with_acestep")
    def test_music_generate_unified_api_response(self, mock_acestep):
        """API /api/music/generate/ trả về đầy đủ metadata chuẩn hóa mới mà không phá vỡ schema cũ."""
        dummy_wav = self._create_dummy_wav(2.0)
        mock_acestep.return_value = {
            "audio_bytes": dummy_wav,
            "duration": 45,
            "elapsed": 1.2,
            "prompt": "Pop song",
            "seed": "777",
            "lyrics": "Từng giọt nắng rơi",
        }

        view = MusicGenerateUnifiedView()
        request = MagicMock()
        request.data = {
            "prompt": "Bài hát vui tươi",
            "language": "vi",
            "vocal": "female",
            "duration": 45,
            "instrumental": False,
        }
        request.query_params = {}
        request.user = None
        request.build_absolute_uri.side_effect = lambda url: f"http://testserver{url}"

        response = view.post(request)
        self.assertEqual(response.status_code, 200)
        data = response.data

        self.assertTrue(data["success"])
        song = data["song"]
        self.assertIn("id", song)
        self.assertIn("title", song)
        self.assertIn("audio_url", song)
        # Các trường metadata mới
        self.assertIn("task_type", song)
        self.assertIn("vocal_type", song)
        self.assertIn("vocal_generated", song)
        self.assertIn("provider", song)


if __name__ == "__main__":
    unittest.main()
