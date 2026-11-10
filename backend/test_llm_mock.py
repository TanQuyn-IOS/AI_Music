# -*- coding: utf-8 -*-
"""
Test LLM Parsing & Response Formatting (Unit Tests)
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.ai_engine.llm_service import (
    generate_lyrics_with_llm,
    chat_with_music_llm,
    get_active_provider,
)

class LLMServiceTestCase(unittest.TestCase):

    @patch("apps.ai_engine.llm_service.get_active_provider")
    @patch("apps.ai_engine.llm_service.call_llm")
    def test_generate_lyrics_success(self, mock_call_llm, mock_provider):
        mock_provider.return_value = ("gemini", "dummy_key")
        mock_call_llm.return_value = (
            """{
                "title": "Gió Lạnh Mùa Đông",
                "theme": "sad",
                "lyrics": "[Intro]\\nGió lạnh thổi qua hàng cây...\\n\\n[Verse 1]\\nPhố dài vắng bóng một người, bước chân lạc lõng giữa trời\\nGiọt sương rơi lạnh bờ mi, nhớ thương người đã xa xôi\\n\\n[Chorus]\\nVà cơn gió đông mang em đi thật xa, buốt giá con tim này\\nLời hứa ngày xưa tan thành khói mây, riêng anh nơi đây",
                "style_tags": "Vietnamese pop, sad ballad, acoustic piano, clear vocals"
            }""",
            "gemini"
        )

        res = generate_lyrics_with_llm(
            topic="Mùa đông cô đơn",
            genre="vpop",
            mood="sad",
            vocal_gender="male"
        )
        self.assertIsNotNone(res)
        self.assertEqual(res["title"], "Gió Lạnh Mùa Đông")
        self.assertEqual(res["provider"], "gemini")
        self.assertIn("[Chorus]", res["lyrics"])
        print("✓ Test generate_lyrics_with_llm: PASSED")

    @patch("apps.ai_engine.llm_service.get_active_provider")
    @patch("apps.ai_engine.llm_service.call_llm")
    def test_chatbot_llm_success(self, mock_call_llm, mock_provider):
        mock_provider.return_value = ("gemini", "dummy_key")
        mock_call_llm.return_value = (
            """{
                "message": "Tôi rất hiểu cảm giác cô đơn của bạn 🌧️ Hãy để những nốt nhạc nhẹ nhàng vỗ về nhé!",
                "mood": "sad",
                "recommended_genres": ["vpop", "ballad"],
                "recommended_song_ids": [101]
            }""",
            "gemini"
        )

        dummy_song = MagicMock()
        dummy_song.id = 101
        dummy_song.title = "Nỗi Buồn Gác Trọ"
        dummy_song.genre = "vpop"
        dummy_song.mood = "sad"
        dummy_song.artist = MagicMock(username="Ca Sĩ AI")

        res = chat_with_music_llm(
            message="Tôi buồn quá bạn ơi",
            songs_pool=[dummy_song]
        )
        self.assertIsNotNone(res)
        self.assertEqual(res["mood"], "sad")
        self.assertIn("vpop", res["recommended_genres"])
        self.assertEqual(len(res["songs"]), 1)
        self.assertEqual(res["songs"][0]["title"], "Nỗi Buồn Gác Trọ")
        print("✓ Test chat_with_music_llm: PASSED")


if __name__ == "__main__":
    unittest.main()
