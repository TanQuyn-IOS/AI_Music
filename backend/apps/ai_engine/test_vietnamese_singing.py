# -*- coding: utf-8 -*-
"""
Sonavia Studio — Vietnamese AI Singing Voice Mandatory Test Suite (Part 6.4)
============================================================================
Kiểm thử 4 kịch bản bắt buộc theo Master Prompt:
1. Nữ ballad chậm (70 BPM): "Từng hạt mưa rơi rớt bên thềm vắng xưa..."
2. Nam ballad chậm (72 BPM): "Gió đông về lạnh lùng góc phố thân quen..."
3. Nữ V-Pop sôi động (105 BPM): "Nụ cười rạng rỡ như ánh bình minh lung linh..."
4. Nam V-Pop sôi động (108 BPM): "Bùng cháy lên ngọn lửa đam mê thanh xuân..."

Tiêu chí đánh giá bắt buộc:
- Chuẩn hóa Unicode NFC 100%
- Bảo tồn toàn vẹn 6 thanh điệu (Ngang, Huyền, Sắc, Hỏi, Ngã, Nặng)
- Đầy đủ âm tiết, không nuốt chữ
- Kiểm tra tính lặp dị thường (No repetition anomalies)
- Tuyệt đối cấm sử dụng Bark cho tiếng Việt có lời
- Xử lý biên an toàn (Graceful timeout fallback)
"""

import unicodedata
from django.test import TestCase
from unittest.mock import patch, MagicMock

from apps.ai_engine.vietnamese_phonetics import (
    normalize_nfc,
    analyze_lyrics,
    detect_repetition_anomalies,
)
from apps.ai_engine.providers.vietnamese_svs_provider import VietnameseSVSProvider
from apps.ai_engine.orchestrator import sonavia_orchestrator


class VietnameseSingingVoiceTests(TestCase):
    """Bộ kiểm thử SVS 4 kịch bản bắt buộc của Sonavia AI."""

    def test_scenario_1_female_slow_ballad_70_bpm(self):
        """Kịch bản 1: Nữ ballad chậm (70 BPM)"""
        lyrics = "Từng hạt mưa rơi rớt bên thềm vắng xưa mang theo nỗi nhớ khôn nguôi"
        bpm = 70
        gender = 'female'

        # 1. Unicode NFC Normalization
        norm = normalize_nfc(lyrics)
        self.assertTrue(unicodedata.is_normalized('NFC', norm))

        # 2. 6 Tones & Syllable Completeness
        analysis = analyze_lyrics(norm)
        self.assertEqual(analysis.total_syllables, len(lyrics.split()))
        self.assertTrue(analysis.is_all_vietnamese)
        self.assertGreater(analysis.tone_distribution['nặng'], 0)  # "hạt", "rớt"
        self.assertGreater(analysis.tone_distribution['huyền'], 0) # "Từng", "thềm"
        self.assertGreater(analysis.tone_distribution['sắc'], 0)   # "vắng", "nhớ"
        self.assertGreater(analysis.tone_distribution['ngang'], 0) # "mưa", "rơi", "xưa"

        # 3. No repetition anomalies
        has_anom, _ = detect_repetition_anomalies(norm)
        self.assertFalse(has_anom)

        # 4. Local SVS Acoustic Engine Vocal Synthesis
        provider = VietnameseSVSProvider()
        res = provider.synthesize_acoustic_vocal(
            lyrics=norm,
            duration=4,
            genre="ballad",
            mood="sad",
            vocal_gender=gender,
            bpm=bpm,
        )
        self.assertIsNotNone(res.get('audio_bytes'))
        self.assertGreater(len(res['audio_bytes']), 1000)
        self.assertEqual(res['vocal_type'], 'vocal')
        self.assertTrue(res['vocal_generated'])

    def test_scenario_2_male_slow_ballad_72_bpm(self):
        """Kịch bản 2: Nam ballad chậm (72 BPM)"""
        lyrics = "Gió đông về lạnh lùng góc phố thân quen tìm lại bước chân người xưa"
        bpm = 72
        gender = 'male'

        norm = normalize_nfc(lyrics)
        self.assertTrue(unicodedata.is_normalized('NFC', norm))

        analysis = analyze_lyrics(norm)
        self.assertEqual(analysis.total_syllables, len(lyrics.split()))
        self.assertTrue(analysis.is_all_vietnamese)
        self.assertGreater(analysis.tone_distribution['sắc'], 0)   # "Gió", "góc", "phố"
        self.assertGreater(analysis.tone_distribution['huyền'], 0) # "về", "lùng", "người"
        self.assertGreater(analysis.tone_distribution['nặng'], 0)  # "lạnh", "lại"

        has_anom, _ = detect_repetition_anomalies(norm)
        self.assertFalse(has_anom)

        provider = VietnameseSVSProvider()
        res = provider.synthesize_acoustic_vocal(
            lyrics=norm,
            duration=4,
            genre="ballad",
            mood="melancholic",
            vocal_gender=gender,
            bpm=bpm,
        )
        self.assertIsNotNone(res.get('audio_bytes'))
        self.assertGreater(len(res['audio_bytes']), 1000)
        self.assertEqual(res['vocal_type'], 'vocal')
        self.assertTrue(res['vocal_generated'])

    def test_scenario_3_female_vpop_105_bpm(self):
        """Kịch bản 3: Nữ V-Pop sôi động (105 BPM)"""
        lyrics = "Nụ cười rạng rỡ như ánh bình minh lung linh thắp sáng tình yêu"
        bpm = 105
        gender = 'female'

        norm = normalize_nfc(lyrics)
        self.assertTrue(unicodedata.is_normalized('NFC', norm))

        analysis = analyze_lyrics(norm)
        self.assertEqual(analysis.total_syllables, len(lyrics.split()))
        self.assertTrue(analysis.is_all_vietnamese)
        # Kiểm tra dấu Ngã ("rỡ")
        self.assertGreater(analysis.tone_distribution['ngã'], 0)
        # Kiểm tra dấu Nặng ("Nụ", "rạng")
        self.assertGreater(analysis.tone_distribution['nặng'], 0)

        has_anom, _ = detect_repetition_anomalies(norm)
        self.assertFalse(has_anom)

        provider = VietnameseSVSProvider()
        res = provider.synthesize_acoustic_vocal(
            lyrics=norm,
            duration=4,
            genre="vpop",
            mood="happy",
            vocal_gender=gender,
            bpm=bpm,
        )
        self.assertIsNotNone(res.get('audio_bytes'))
        self.assertGreater(len(res['audio_bytes']), 1000)
        self.assertEqual(res['vocal_type'], 'vocal')
        self.assertTrue(res['vocal_generated'])

    def test_scenario_4_male_vpop_108_bpm(self):
        """Kịch bản 4: Nam V-Pop sôi động (108 BPM)"""
        lyrics = "Bùng cháy lên ngọn lửa đam mê thanh xuân cùng nhau bước tới tương lai"
        bpm = 108
        gender = 'male'

        norm = normalize_nfc(lyrics)
        self.assertTrue(unicodedata.is_normalized('NFC', norm))

        analysis = analyze_lyrics(norm)
        self.assertEqual(analysis.total_syllables, len(lyrics.split()))
        self.assertTrue(analysis.is_all_vietnamese)
        # Kiểm tra dấu Hỏi ("lửa")
        self.assertGreater(analysis.tone_distribution['hỏi'], 0)
        # Kiểm tra dấu Nặng ("ngọn")
        self.assertGreater(analysis.tone_distribution['nặng'], 0)
        # Kiểm tra dấu Sắc ("cháy", "tới")
        self.assertGreater(analysis.tone_distribution['sắc'], 0)

        has_anom, _ = detect_repetition_anomalies(norm)
        self.assertFalse(has_anom)

        provider = VietnameseSVSProvider()
        res = provider.synthesize_acoustic_vocal(
            lyrics=norm,
            duration=4,
            genre="vpop",
            mood="energetic",
            vocal_gender=gender,
            bpm=bpm,
        )
        self.assertIsNotNone(res.get('audio_bytes'))
        self.assertGreater(len(res['audio_bytes']), 1000)
        self.assertEqual(res['vocal_type'], 'vocal')
        self.assertTrue(res['vocal_generated'])

    @patch("apps.ai_engine.bark_singer.generate_vocal_bytes")
    @patch("apps.ai_engine.bark_singer.generate_vocal")
    def test_strict_bark_prohibition_for_vietnamese_singing(self, mock_bark_vocal, mock_bark_bytes):
        """Cấm tuyệt đối sử dụng Bark cho tiếng Việt có lời."""
        provider = VietnameseSVSProvider()
        # When deep learning weights are missing, generate() refuses fake vocals and explains no bark
        with self.assertRaises(RuntimeError) as ctx:
            provider.generate(prompt="Ballad nữ buồn", lyrics="Ánh trăng vàng dịu dàng soi bóng em")
        self.assertIn("không sử dụng Bark làm fallback", str(ctx.exception))

        mock_bark_vocal.assert_not_called()
        mock_bark_bytes.assert_not_called()

    @patch("apps.ai_engine.bark_singer.generate_vocal_bytes")
    def test_edge_case_and_timeout_resilience(self, mock_bark_bytes):
        """Xử lý biên an toàn nếu provider bị timeout."""
        # Khi ACE-Step bị timeout, Orchestrator fallback mượt mà sang Melodic Lead mà không crash
        with patch.object(sonavia_orchestrator.primary_provider, "generate", side_effect=TimeoutError("Request timed out")):
            with patch("apps.ai_engine.music_generator.generate_music", return_value=(b"RIFFdummywavdata", 32000)):
                res = sonavia_orchestrator.generate_song(
                    prompt="Bài hát thử nghiệm timeout",
                    language="vi",
                    custom_lyrics="Khúc nhạc êm đềm trong chiều vắng",
                    vocal="female",
                )
                self.assertIsNotNone(res)
                self.assertEqual(res["provider"], "musicgen")
                self.assertEqual(res["vocal_type"], "melodic_lead")
                self.assertFalse(res["vocal_generated"])
                self.assertEqual(res["fallback_reason"], "no_compatible_vietnamese_svs")
                mock_bark_bytes.assert_not_called()
