# -*- coding: utf-8 -*-
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_backend not in sys.path:
    sys.path.insert(0, base_backend)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import SimpleTestCase
from apps.ai_engine.acestep_generator import clean_vietnamese_lyrics, normalize_lyrics_for_acestep


class PhoneticTestCase(SimpleTestCase):
    def test_normalize_lyrics_preserves_vietnamese(self):
        test_lyrics = """[Verse 1]
Từng giọt nắng khẽ rơi bên hiên nhà xưa
Ánh mắt em cười như ngàn vì sao sáng ♪
[Chorus]
Hãy nắm lấy tay anh đi qua ngày giông bão...
Đêm nay ngân nga khúc ca tình yêu đôi ta!"""
        normalized = normalize_lyrics_for_acestep(test_lyrics)
        viet_chars = 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ'
        found_viet = [c for c in normalized if c in viet_chars]
        self.assertTrue(len(found_viet) > 0, "Bị mất dấu tiếng Việt")
        self.assertNotIn('♪', normalized, "Chưa lọc nốt nhạc ♪")
        self.assertIn('[verse 1]', normalized, "Mất tag [verse 1]")
        self.assertIn('[chorus]', normalized, "Mất tag [chorus]")


if __name__ == '__main__':
    import unittest
    unittest.main()
