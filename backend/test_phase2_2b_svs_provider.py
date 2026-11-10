"""
Sonavia AI - Phase 2.2B Test Suite: Vietnamese SVS Provider Verification
========================================================================
Kiểm thử toàn diện Provider SVS tiếng Việt:
1. Kiểm tra Provider availability (báo False trung thực khi chưa có checkpoint).
2. Kiểm tra Missing checkpoint & giải thích rõ ràng.
3. Kiểm tra GPU/CPU reporting trong get_model_info().
4. Kiểm tra Input validation (chuỗi rỗng, quá ngắn, Unicode NFC).
5. Kiểm tra tích hợp Vietnamese Phonetic Layer (trích xuất 6 thanh điệu, trọng số âm học).
6. Khẳng định tuyệt đối KHÔNG tạo vocal giả khi chưa có checkpoint.
7. Khẳng định tuyệt đối KHÔNG gọi Bark trong bất kỳ trường hợp nào.
8. Kiểm tra cơ chế giải phóng bộ nhớ (unload_model).
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Thiết lập Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.ai_engine.providers.vietnamese_svs_provider import VietnameseSVSProvider
from apps.ai_engine.vietnamese_phonetics import ToneType, AcousticWeight


class TestPhase22BSVSProvider(unittest.TestCase):
    """Kiểm thử chuẩn hóa cho VietnameseSVSProvider."""

    def setUp(self):
        self.provider = VietnameseSVSProvider()
        self.benchmark_lyrics = (
            "Nắng nghiêng chiều buông trên dòng sông vắng\n"
            "Gió lạnh lùng ru từng nhánh bằng lăng\n"
            "Gợi nỗi nhớ người thương năm tháng cũ\n"
            "Khúc tình ca êm ái ngút ngàn xưa"
        )

    def test_provider_availability_false_without_checkpoint(self):
        """Khi chưa có checkpoint kiểm chứng, is_available() bắt buộc phải trả về False."""
        self.assertFalse(self.provider.is_available())
        self.assertIsNone(self.provider.checkpoint_path)

    def test_fake_checkpoint_path_returns_false_if_not_exists(self):
        """Nếu truyền đường dẫn checkpoint không tồn tại, is_available() vẫn trả về False."""
        non_existent_provider = VietnameseSVSProvider(checkpoint_path="/fake/path/model.ckpt")
        self.assertFalse(non_existent_provider.is_available())

    def test_get_model_info_structure(self):
        """get_model_info() phải báo cáo chi tiết về GPU, lý do chưa khả dụng và các kiến trúc SVS."""
        info = self.provider.get_model_info()
        self.assertEqual(info["provider_name"], "vietnamese_svs")
        self.assertFalse(info["is_available"])
        self.assertFalse(info["has_checkpoint"])
        self.assertIn("Chưa có checkpoint SVS tiếng Việt", info["status_reason"])
        self.assertIn("gpu_status", info)
        self.assertIn("device", info["gpu_status"])
        self.assertIn("supported_svs_architectures", info)

        arch_names = [a["name"] for a in info["supported_svs_architectures"]]
        self.assertIn("DiffSinger", arch_names)
        self.assertIn("ViSVS", arch_names)
        self.assertIn("OpenVPI", arch_names)

    def test_validate_input_empty_lyrics(self):
        """Xác thực đầu vào từ chối chuỗi rỗng hoặc chỉ có khoảng trắng."""
        valid, msg = self.provider.validate_input("prompt", "")
        self.assertFalse(valid)
        self.assertIn("không được để trống", msg)

        valid, msg = self.provider.validate_input("prompt", "   ")
        self.assertFalse(valid)

        valid, msg = self.provider.validate_input("prompt", "abc")
        self.assertFalse(valid)
        self.assertIn("quá ngắn", msg)

    def test_validate_input_valid_lyrics(self):
        """Ca từ hợp lệ phải vượt qua bước xác thực."""
        valid, msg = self.provider.validate_input("V-Pop ballad", self.benchmark_lyrics)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_phonetic_preprocessing_integration(self):
        """Tích hợp sâu với Vietnamese Phonetic Layer để phân tích âm tiết và thanh điệu."""
        analysis = self.provider.phonetic_preprocess(self.benchmark_lyrics)
        self.assertEqual(analysis.total_syllables, 32)
        self.assertEqual(analysis.vietnamese_syllable_count, 32)
        self.assertTrue(analysis.is_all_vietnamese)

        # Kiểm tra sự hiện diện của đủ các thanh điệu
        self.assertGreater(analysis.tone_distribution["sắc"], 0)
        self.assertGreater(analysis.tone_distribution["huyền"], 0)
        self.assertGreater(analysis.tone_distribution["ngang"], 0)
        self.assertGreater(analysis.tone_distribution["ngã"], 0)
        self.assertGreater(analysis.tone_distribution["nặng"], 0)

    @patch("apps.ai_engine.bark_singer.generate_vocal_bytes")
    @patch("apps.ai_engine.bark_singer.generate_vocal")
    def test_generate_raises_error_without_checkpoint_and_never_calls_bark(self, mock_bark_vocal, mock_bark_bytes):
        """Khi chưa có checkpoint, generate() phải ném lỗi giải thích rõ, KHÔNG tạo vocal giả và KHÔNG gọi Bark."""
        with self.assertRaises(RuntimeError) as ctx:
            self.provider.generate(
                prompt="Bài hát trữ tình",
                lyrics=self.benchmark_lyrics,
            )

        self.assertIn("VietnameseSVSProvider unavailable", str(ctx.exception))
        self.assertIn("không sử dụng Bark làm fallback", str(ctx.exception))

        # Khẳng định Bark tuyệt đối không bị gọi
        mock_bark_vocal.assert_not_called()
        mock_bark_bytes.assert_not_called()

    def test_unload_model_does_not_crash(self):
        """unload_model() giải phóng bộ nhớ GPU an toàn."""
        try:
            self.provider.unload_model()
            ok = True
        except Exception:
            ok = False
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
