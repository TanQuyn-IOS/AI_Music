"""
Sonavia AI - Phase 2.2A Test Suite: Remove Bark Fallback Safely
================================================================
Kiểm thử toàn diện việc loại bỏ Bark khỏi toàn bộ tuyến tạo vocal tiếng Việt:
1. Yêu cầu tạo bài hát tiếng Việt không gọi Bark.
2. ACE-Step thất bại không chuyển sang Bark.
3. MusicGen vẫn tạo được instrumental / melodic lead chất lượng cao.
4. Background job không gọi Bark khi fallback.
5. API response phản ánh trung thực vocal_type, vocal_generated, fallback_reason.
6. Giao diện VietnameseSVSProvider báo unavailable minh bạch, không tạo vocal giả.
7. Tuyến gọi trực tiếp Bark bị chặn hoàn toàn (Hard Guard).
8. Không phá vỡ các API hiện có (FullSongOptionsView, FullSongGenerateView, FullSongStatusView).
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Thiết lập Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.ai_engine.orchestrator import sonavia_orchestrator, SonaviaOrchestrator
from apps.ai_engine.providers.musicgen_provider import MusicGenProvider
from apps.ai_engine.providers.vietnamese_svs_provider import VietnameseSVSProvider
from apps.ai_engine.views import (
    _run_full_generation_job,
    _JOBS,
    _JOBS_LOCK,
    FullSongOptionsView,
    FullSongStatusView,
)
from apps.ai_engine.bark_singer import (
    generate_vocal_bytes,
    _clean_vietnamese_lyrics_for_bark,
    _apply_chunk_fade,
    VOICE_PRESETS,
)


class TestPhase22ARemoveBark(unittest.TestCase):
    """Bộ kiểm thử xác nhận loại bỏ Bark an toàn và bảo toàn hệ thống."""

    def setUp(self):
        self.benchmark_lyrics = (
            "Nắng nghiêng chiều buông trên dòng sông vắng\n"
            "Gió lạnh lùng ru từng nhánh bằng lăng\n"
            "Gợi nỗi nhớ người thương năm tháng cũ\n"
            "Khúc tình ca êm ái ngút ngàn xưa"
        )

    def _create_dummy_wav(self, duration_s: float = 2.0, sr: int = 32000) -> bytes:
        """Tạo chuỗi byte WAV hợp lệ để soundfile đọc được trong test."""
        import io
        import soundfile as sf
        import numpy as np
        t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False, dtype=np.float32)
        sine = 0.5 * np.sin(2 * np.pi * 440.0 * t)
        buf = io.BytesIO()
        sf.write(buf, sine, sr, format="WAV", subtype="PCM_16")
        return buf.getvalue()

    # ────────────────────────────────────────────────────────────────────────
    # 1. Yêu cầu tạo bài hát tiếng Việt không gọi Bark
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.bark_singer.generate_vocal_bytes")
    @patch("apps.ai_engine.bark_singer.generate_vocal")
    def test_orchestrator_vietnamese_song_does_not_call_bark(self, mock_gen_vocal, mock_gen_vocal_bytes):
        """Khi tạo bài hát tiếng Việt qua Orchestrator, tuyệt đối không được gọi Bark."""
        dummy_wav = self._create_dummy_wav(2.0)

        with patch.object(sonavia_orchestrator.primary_provider, "is_available", return_value=True):
            with patch("apps.ai_engine.providers.acestep_provider.generate_with_acestep") as mock_acestep:
                mock_acestep.return_value = {
                    "audio_bytes": dummy_wav,
                    "duration": 60,
                    "elapsed": 2.0,
                    "prompt": "V-Pop ballad",
                    "seed": "12345",
                    "lyrics": self.benchmark_lyrics,
                }

                res = sonavia_orchestrator.generate_song(
                    prompt="Bài hát V-Pop ballad về hoàng hôn",
                    language="vi",
                    custom_lyrics=self.benchmark_lyrics,
                    vocal="female",
                    duration=60,
                )

            # Khẳng định Bark hoàn toàn không bị gọi
            mock_gen_vocal.assert_not_called()
            mock_gen_vocal_bytes.assert_not_called()

            # Khẳng định kết quả hợp lệ
            self.assertIn("audio_bytes", res)
            self.assertEqual(res["vocal_type"], "vocal")
            self.assertTrue(res["vocal_generated"])
            self.assertIsNone(res["fallback_reason"])

    # ────────────────────────────────────────────────────────────────────────
    # 2. ACE-Step thất bại không chuyển sang Bark
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.bark_singer.generate_vocal_bytes")
    @patch("apps.ai_engine.bark_singer.generate_vocal")
    def test_acestep_failure_falls_back_without_bark(self, mock_gen_vocal, mock_gen_vocal_bytes):
        """Khi ACE-Step gặp sự cố, hệ thống fallback sang MusicGen/Synth và KHÔNG gọi Bark."""
        dummy_music_wav = self._create_dummy_wav(2.0)

        # Giả lập ACE-Step bị lỗi mạng/quá tải
        with patch.object(sonavia_orchestrator.primary_provider, "generate", side_effect=RuntimeError("ACE-Step timeout")):
            with patch.object(sonavia_orchestrator.fallback_provider, "generate") as mock_musicgen:
                mock_musicgen.return_value = {
                    "audio_bytes": dummy_music_wav,
                    "duration": 30,
                    "elapsed": 1.5,
                    "prompt": "V-Pop acoustic, melodic lead",
                    "seed": "999",
                    "lyrics": self.benchmark_lyrics,
                    "format": "wav",
                    "provider": "musicgen",
                    "mastered": True,
                    "vocal_type": "melodic_lead",
                    "vocal_generated": False,
                    "fallback_reason": "no_compatible_vietnamese_svs",
                }

                res = sonavia_orchestrator.generate_song(
                    prompt="Ballad ngọt ngào",
                    language="vi",
                    custom_lyrics=self.benchmark_lyrics,
                    vocal="female",
                    duration=30,
                )

                # Bark tuyệt đối không bị gọi
                mock_gen_vocal.assert_not_called()
                mock_gen_vocal_bytes.assert_not_called()

                # Kiểm tra tính minh bạch của metadata
                self.assertEqual(res["vocal_type"], "melodic_lead")
                self.assertFalse(res["vocal_generated"])
                self.assertEqual(res["fallback_reason"], "no_compatible_vietnamese_svs")
                self.assertIsNotNone(res["audio_bytes"])

    # ────────────────────────────────────────────────────────────────────────
    # 3. MusicGen vẫn tạo được instrumental mà không phụ thuộc Bark
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.bark_singer.generate_vocal_bytes")
    def test_musicgen_provider_generates_instrumental_cleanly(self, mock_gen_vocal_bytes):
        """MusicGen tạo nhạc nền với melodic lead, không bao giờ gọi Bark."""
        provider = MusicGenProvider()
        dummy_wav = self._create_dummy_wav(2.0)

        with patch("apps.ai_engine.music_generator.generate_music", return_value=(dummy_wav, 32000)):
            res = provider.generate(
                prompt="Acoustic guitar gentle ballad",
                lyrics=self.benchmark_lyrics,
                duration=15,
                genre="vpop",
                mood="sad",
                vocal_gender="female",
            )

            # Bark không bị gọi
            mock_gen_vocal_bytes.assert_not_called()

            # Metadata trung thực
            self.assertEqual(res["vocal_type"], "melodic_lead")
            self.assertFalse(res["vocal_generated"])
            self.assertEqual(res["fallback_reason"], "no_compatible_vietnamese_svs")
            self.assertEqual(res["audio_bytes"], dummy_wav)

    # ────────────────────────────────────────────────────────────────────────
    # 4. Background Job không gọi Bark khi fallback
    # ────────────────────────────────────────────────────────────────────────
    @patch("apps.ai_engine.bark_singer.generate_vocal_bytes")
    def test_background_job_fallback_does_not_call_bark(self, mock_gen_vocal_bytes):
        """Background thread full generation job không gọi Bark khi fallback."""
        job_id = "test_phase2_job"
        dummy_music_bytes = self._create_dummy_wav(3.0)

        with _JOBS_LOCK:
            _JOBS[job_id] = {
                "status": "running",
                "pct": 0,
                "step": 0,
                "total": 1,
                "message": "Đang chạy test...",
            }

        # Giả lập orchestrator thất bại bên trong background thread để kích hoạt fallback
        with patch("apps.ai_engine.orchestrator.sonavia_orchestrator.generate_song", side_effect=RuntimeError("Space down")):
            with patch("apps.ai_engine.music_generator.generate_long_music_bytes", return_value=(dummy_music_bytes, 32000, "V-Pop")):
                with patch("apps.ai_engine.music_generator.unload_model"):
                    _run_full_generation_job(
                        job_id=job_id,
                        genre="vpop",
                        mood="romantic",
                        tempo="medium",
                        instruments="full",
                        custom_prompt="Tình ca mùa thu",
                        total_duration=60,
                        lyrics=self.benchmark_lyrics,
                        voice="female_vi",
                        with_vocal=True,
                        guidance_scale=3.0,
                        temperature=1.0,
                        model_name="facebook/musicgen-small",
                    )

        # Bark tuyệt đối không được gọi
        mock_gen_vocal_bytes.assert_not_called()

        with _JOBS_LOCK:
            job_state = _JOBS.get(job_id)

        self.assertIsNotNone(job_state)
        self.assertEqual(job_state["status"], "done")
        self.assertEqual(job_state["pct"], 100)
        # Metadata phản ánh trung thực
        self.assertEqual(job_state["vocal_type"], "melodic_lead")
        self.assertFalse(job_state["vocal_generated"])
        self.assertEqual(job_state["fallback_reason"], "no_compatible_vietnamese_svs")
        self.assertIsNotNone(job_state["audio"])

    # ────────────────────────────────────────────────────────────────────────
    # 5. FullSongStatusView phản ánh trung thực vocal_type & fallback_reason
    # ────────────────────────────────────────────────────────────────────────
    def test_full_song_status_view_reflects_vocal_metadata(self):
        """API FullSongStatusView trả về đầy đủ metadata minh bạch."""
        job_id = "test_status_job"
        with _JOBS_LOCK:
            _JOBS[job_id] = {
                "status": "done",
                "pct": 100,
                "message": "Hoàn thành test",
                "audio": b"RIFF123",
                "vocal_type": "melodic_lead",
                "vocal_generated": False,
                "fallback_reason": "no_compatible_vietnamese_svs",
            }

        view = FullSongStatusView()
        request = MagicMock()
        response = view.get(request, job_id=job_id)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["job_id"], job_id)
        self.assertEqual(data["status"], "done")
        self.assertEqual(data["vocal_type"], "melodic_lead")
        self.assertFalse(data["vocal_generated"])
        self.assertEqual(data["fallback_reason"], "no_compatible_vietnamese_svs")

    # ────────────────────────────────────────────────────────────────────────
    # 6. Giao diện VietnameseSVSProvider
    # ────────────────────────────────────────────────────────────────────────
    def test_vietnamese_svs_provider_interface(self):
        """VietnameseSVSProvider báo unavailable và không tạo vocal giả."""
        provider = VietnameseSVSProvider()
        # Không có checkpoint -> Báo False
        self.assertFalse(provider.is_available())

        # Gọi generate() phải ném lỗi giải thích rõ ràng, KHÔNG tạo vocal giả
        with self.assertRaises(RuntimeError) as ctx:
            provider.generate(
                prompt="V-Pop song",
                lyrics=self.benchmark_lyrics,
            )
        self.assertIn("VietnameseSVSProvider unavailable", str(ctx.exception))
        self.assertIn("không sử dụng Bark", str(ctx.exception))

    # ────────────────────────────────────────────────────────────────────────
    # 7. Tuyến gọi trực tiếp Bark bị chặn bởi Hard Guard
    # ────────────────────────────────────────────────────────────────────────
    def test_bark_generate_vocal_bytes_hard_guard(self):
        """Gọi trực tiếp generate_vocal_bytes phải bị chặn bởi hard guard."""
        with self.assertRaises(RuntimeError) as ctx:
            generate_vocal_bytes("Lời bài hát bất kỳ")
        self.assertIn("Bark vocal generation is disabled for Vietnamese lyrics", str(ctx.exception))

    # ────────────────────────────────────────────────────────────────────────
    # 8. Bảo toàn các chức năng và options hiện có
    # ────────────────────────────────────────────────────────────────────────
    def test_full_song_options_view_preserved(self):
        """API options cho full generator vẫn hoạt động trơn tru không lỗi."""
        view = FullSongOptionsView()
        request = MagicMock()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("genres", response.data)
        self.assertIn("moods", response.data)
        self.assertIn("voices", response.data)
        self.assertIn("models", response.data)
        self.assertIn("duration_options", response.data)
        # Các voice preset vẫn hiển thị cho giao diện lựa chọn
        self.assertIn("female_vi", response.data["voices"])
        self.assertIn("male_vi", response.data["voices"])


if __name__ == "__main__":
    unittest.main()
