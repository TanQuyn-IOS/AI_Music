"""
Test suite for Multi-Minute Audio Generation & Multilingual Lyrics Fix
1. Verifies MusicGenProvider supports duration > 30 (up to 180s = 3 minutes).
2. Verifies SonaviaOrchestrator automatically resolves language mismatch:
   When user selects Korean (ko), Japanese (ja), Chinese (zh), English (en),
   any stale Vietnamese custom_lyrics (from image analysis) is purged,
   generating authentic native lyrics in the target language.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase
import numpy as np

from apps.ai_engine.orchestrator import SonaviaOrchestrator
from apps.ai_engine.providers.musicgen_provider import MusicGenProvider


class TestDurationAndMultilingualFix(TestCase):

    def setUp(self):
        self.orchestrator = SonaviaOrchestrator()
        self.musicgen_provider = MusicGenProvider()

    def test_musicgen_provider_supports_duration_over_30s(self):
        """Kiểm tra MusicGenProvider gọi generate_long_music khi duration > 30 và trả về duration mục tiêu."""
        fake_sr = 32000
        target_duration = 180
        fake_audio = np.zeros(fake_sr * target_duration, dtype=np.float32)

        with patch("apps.ai_engine.music_generator.generate_long_music", return_value=(fake_audio, fake_sr)) as mock_long:
            res = self.musicgen_provider.generate(
                prompt="Epic cinematic ballad",
                duration=target_duration,
            )
            mock_long.assert_called_once()
            self.assertEqual(res["duration"], 180)
            self.assertGreater(len(res["audio_bytes"]), 1000)

    def test_orchestrator_passes_full_duration_to_fallback(self):
        """Kiểm tra Orchestrator chuyển duration=180 (3 phút) tới fallback provider thay vì bị giới hạn 30s."""
        fake_result = {
            "audio_bytes": b"RIFFtestaudioheaderwavdata",
            "duration": 180,
            "elapsed": 5.0,
            "prompt": "Test prompt",
            "seed": "12345",
            "lyrics": "",
            "format": "wav",
            "provider": "musicgen",
            "mastered": True,
            "vocal_type": "melodic_lead",
            "vocal_generated": False,
        }

        # Mock primary ACE-Step provider is_available=True, but generate fails with Space down
        with patch.object(self.orchestrator.primary_provider, "is_available", return_value=True):
            with patch.object(self.orchestrator.primary_provider, "generate", side_effect=Exception("Space down")):
                with patch.object(self.orchestrator.fallback_provider, "generate", return_value=fake_result) as mock_fallback:
                    res = self.orchestrator.generate_song(
                        prompt="Korean ballad in the sunset",
                        language="ko",
                        duration=180,
                    )
                    mock_fallback.assert_called_once()
                    call_kwargs = mock_fallback.call_args[1]
                    self.assertEqual(call_kwargs["duration"], 180)
                    self.assertEqual(res["duration"], 180)

    def test_korean_language_purges_stale_vietnamese_lyrics(self):
        """Kiểm tra khi chọn tiếng Hàn ('ko'), nếu có lời tiếng Việt cũ từ phân tích ảnh, hệ thống tự động sinh lời tiếng Hàn."""
        stale_vietnamese_lyrics = (
            "[Intro]\n"
            "Gió khẽ lay qua từng giọt nắng phai...\n"
            "[Verse 1]\n"
            "Ánh chiều buông xuống bên thềm hoa rơi..."
        )

        fake_result = {
            "audio_bytes": b"RIFFtestaudioheaderwavdata",
            "duration": 180,
            "elapsed": 4.0,
            "prompt": "Test Korean pop",
            "seed": "99999",
            "lyrics": "",
            "format": "wav",
            "provider": "synth",
            "mastered": True,
            "vocal_type": "melodic_lead",
            "vocal_generated": False,
        }

        # Primary down -> fallback to synth
        with patch.object(self.orchestrator.primary_provider, "generate", side_effect=Exception("Space down")):
            with patch.object(self.orchestrator.synth_provider, "generate", return_value=fake_result):
                res = self.orchestrator.generate_song(
                    prompt="Bức tranh tình yêu lãng mạn",
                    language="ko",
                    custom_lyrics=stale_vietnamese_lyrics,
                    duration=180,
                    preferred_provider="synth",
                )
                generated_lyrics = res["lyrics"]
                # Ca từ tạo ra PHẢI chứa ký tự tiếng Hàn (Hangul)
                has_hangul = any('\uac00' <= ch <= '\ud7af' for ch in generated_lyrics)
                self.assertTrue(has_hangul, f"Lyrics should contain Korean Hangul characters, got: {generated_lyrics[:100]}")
                # Không được còn là bài tiếng Việt cũ
                self.assertNotIn("Gió khẽ lay qua từng giọt nắng phai", generated_lyrics)
                self.assertEqual(res["config"]["language"], "ko")

    def test_japanese_language_purges_stale_vietnamese_lyrics(self):
        """Kiểm tra khi chọn tiếng Nhật ('ja'), hệ thống tự động sinh lời tiếng Nhật thay vì giữ lời tiếng Việt cũ."""
        stale_vietnamese_lyrics = "Từng hạt mưa rơi lạnh buốt tâm hồn"

        fake_result = {
            "audio_bytes": b"RIFFtestaudioheaderwavdata",
            "duration": 60,
            "elapsed": 2.0,
            "prompt": "Test J-Pop",
            "seed": "88888",
            "lyrics": "",
            "format": "wav",
            "provider": "synth",
            "mastered": True,
            "vocal_type": "melodic_lead",
            "vocal_generated": False,
        }

        with patch.object(self.orchestrator.primary_provider, "generate", side_effect=Exception("Space down")):
            with patch.object(self.orchestrator.synth_provider, "generate", return_value=fake_result):
                res = self.orchestrator.generate_song(
                    prompt="Anime sunset vibes",
                    language="ja",
                    custom_lyrics=stale_vietnamese_lyrics,
                    duration=60,
                    preferred_provider="synth",
                )
                generated_lyrics = res["lyrics"]
                has_kana = any('\u3040' <= ch <= '\u30ff' for ch in generated_lyrics)
                self.assertTrue(has_kana, f"Lyrics should contain Japanese characters, got: {generated_lyrics[:100]}")
                self.assertNotIn("Từng hạt mưa rơi", generated_lyrics)
                self.assertEqual(res["config"]["language"], "ja")
