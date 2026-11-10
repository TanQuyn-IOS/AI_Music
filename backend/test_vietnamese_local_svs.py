import os
import sys
import unittest
import numpy as np

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.ai_engine.vietnamese_vocal_synth import (
    generate_syllable_f0_contour,
    synthesize_syllable_audio,
    VietnameseAcousticSVSEngine,
    SAMPLE_RATE,
)
from apps.ai_engine.vietnamese_phonetics import analyze_syllable, ToneType
from apps.ai_engine.providers.vietnamese_svs_provider import VietnameseSVSProvider
from apps.ai_engine.orchestrator import sonavia_orchestrator


class TestVietnameseLocalSVS(unittest.TestCase):
    """Bộ kiểm thử cho Vietnamese Acoustic SVS Synthesizer (Offline SVS)."""

    def setUp(self):
        self.lyrics = (
            "Nắng nghiêng chiều buông trên dòng sông vắng\n"
            "Gió lạnh lùng ru từng nhánh bằng lăng\n"
            "Gợi nỗi nhớ người thương năm tháng cũ\n"
            "Khúc tình ca êm ái ngút ngàn xưa"
        )
        self.provider = VietnameseSVSProvider()

    def test_tone_f0_pitch_contours_all_six_tones(self):
        """Kiểm tra đường cong cao độ F0 phản ánh chính xác 6 thanh điệu tiếng Việt."""
        n_samples = 4410
        base_f0 = 220.0

        # Tone 1: Ngang (phẳng)
        c1 = generate_syllable_f0_contour(base_f0, ToneType.NGANG, n_samples)
        self.assertAlmostEqual(c1[0], base_f0, delta=5.0)
        self.assertAlmostEqual(c1[n_samples // 2], base_f0, delta=10.0)

        # Tone 2: Huyền (hạ dần)
        c2 = generate_syllable_f0_contour(base_f0, ToneType.HUYEN, n_samples)
        self.assertGreater(c2[100], c2[-100])

        # Tone 3: Sắc (vút lên)
        c3 = generate_syllable_f0_contour(base_f0, ToneType.SAC, n_samples)
        self.assertLess(c3[100], c3[-100])

        # Tone 4: Hỏi (võng sâu rồi bật)
        c4 = generate_syllable_f0_contour(base_f0, ToneType.HOI, n_samples)
        mid_idx = n_samples // 2
        self.assertLess(c4[mid_idx], c4[50])

        # Tone 5: Ngã (lượn sóng đi lên)
        c5 = generate_syllable_f0_contour(base_f0, ToneType.NGA, n_samples)
        self.assertGreater(c5[-50], c5[50])

        # Tone 6: Nặng (rơi dốc)
        c6 = generate_syllable_f0_contour(base_f0, ToneType.NANG, n_samples)
        self.assertGreater(c6[50], c6[-50])

    def test_synthesize_syllable_audio(self):
        """Tổng hợp âm tiết đơn có bao biên độ chuẩn và không méo tiếng."""
        syl = analyze_syllable("nắng")
        wave = synthesize_syllable_audio(syl, base_f0=261.63, duration_sec=0.5, vocal_gender="female")
        self.assertTrue(len(wave) > 0)
        self.assertIsInstance(wave, np.ndarray)
        peak = float(np.max(np.abs(wave)))
        self.assertLessEqual(peak, 0.90)

    def test_full_song_vocal_synthesis(self):
        """Tổng hợp bè vocal toàn bài hát Stereo 44.1kHz."""
        stereo_vocal, sr = VietnameseAcousticSVSEngine.synthesize_vietnamese_song_vocal(
            lyrics=self.lyrics,
            total_duration=8,
            genre="vpop",
            mood="romantic",
            vocal_gender="female",
            bpm=90,
        )
        self.assertEqual(sr, SAMPLE_RATE)
        self.assertEqual(stereo_vocal.shape, (8 * SAMPLE_RATE, 2))
        max_peak = float(np.max(np.abs(stereo_vocal)))
        self.assertLessEqual(max_peak, 0.895)
        self.assertGreater(max_peak, 0.1)

    def test_provider_acoustic_synthesis_integration(self):
        """Kiểm tra tích hợp phương thức synthesize_acoustic_vocal trên VietnameseSVSProvider."""
        res = self.provider.synthesize_acoustic_vocal(
            lyrics="Anh yêu em nhiều lắm",
            duration=6,
            genre="vpop",
            vocal_gender="female",
        )
        self.assertEqual(res["provider"], "vietnamese_svs")
        self.assertEqual(res["engine"], "vietnamese_acoustic_svs")
        self.assertEqual(res["vocal_type"], "vocal")
        self.assertTrue(res["vocal_generated"])
        self.assertIsInstance(res["audio_bytes"], bytes)
        self.assertTrue(len(res["audio_bytes"]) > 1000)
        self.assertEqual(res["audio_bytes"][:4], b"RIFF")

    def test_synthesize_acoustic_vocal_with_instrumental_mix(self):
        """Kiểm tra hòa âm tự động bè vocal tiếng Việt và hòa tấu acoustic synth."""
        wav_bytes = VietnameseAcousticSVSEngine.synthesize_to_wav_bytes(
            lyrics="Gió mùa thu xôn xao từng hàng cây",
            total_duration=15,
            genre="vpop",
            mood="romantic",
            vocal_gender="female",
            mix_with_instrumental=True,
        )
        self.assertIsInstance(wav_bytes, bytes)
        self.assertTrue(len(wav_bytes) > 10000)
        self.assertEqual(wav_bytes[:4], b"RIFF")

    def test_orchestrator_routing_to_acoustic_svs(self):
        """Kiểm tra orchestrator định tuyến trực tiếp sang Acoustic SVS khi preferred_provider='acoustic_svs'."""
        res = sonavia_orchestrator.generate_song(
            prompt="Tình ca mùa thu",
            language="vi",
            custom_lyrics=self.lyrics,
            vocal="female",
            duration=15,
            preferred_provider="acoustic_svs",
        )
        self.assertEqual(res["provider"], "vietnamese_svs")
        self.assertEqual(res["vocal_type"], "vocal")
        self.assertTrue(res["vocal_generated"])
        self.assertIsNone(res["fallback_reason"])
        self.assertIsInstance(res["audio_bytes"], bytes)
        self.assertTrue(len(res["audio_bytes"]) > 10000)


if __name__ == "__main__":
    unittest.main()
