from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
import numpy as np
import unicodedata

from apps.ai_engine.vietnamese_phonetics import normalize_nfc, analyze_lyrics
from apps.ai_engine.emotion_classifier import classify_vietnamese_emotion, EMOTION_LABELS
from apps.ai_engine.llm_service import get_neural_embedding


class AIEngineUnitTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_vietnamese_phonetic_preservation(self):
        text = "Ánh trăng rạng rỡ, đêm nay ta ngồi nhớ nhung kỷ niệm xưa"
        norm = normalize_nfc(text)
        self.assertEqual(norm, unicodedata.normalize('NFC', text))
        # Ensure tones are preserved
        self.assertIn("Ánh", norm)
        self.assertIn("rỡ", norm)
        self.assertIn("nhớ", norm)

        analysis = analyze_lyrics(norm)
        self.assertGreater(analysis.total_syllables, 0)
        self.assertGreater(analysis.vietnamese_syllable_count, 0)
        self.assertTrue(analysis.is_all_vietnamese)

    def test_vietnamese_emotion_classification_6_labels(self):
        # 1. Happy
        res_happy = classify_vietnamese_emotion("Hôm nay tôi rất vui và hạnh phúc, rạng rỡ yêu đời")
        self.assertEqual(res_happy['emotion'], 'happy')
        self.assertGreaterEqual(res_happy['confidence'], 0.5)

        # 2. Sad
        res_sad = classify_vietnamese_emotion("Nước mắt rơi, lòng đau đớn cô đơn và u sầu tuyệt vọng")
        self.assertEqual(res_sad['emotion'], 'sad')

        # 3. Nostalgic
        res_nostalgic = classify_vietnamese_emotion("Kỷ niệm xưa chốn cũ, năm tháng tuổi thơ bâng khuâng da diết")
        self.assertEqual(res_nostalgic['emotion'], 'nostalgic')

        # 4. Calm
        res_calm = classify_vietnamese_emotion("Bình yên tĩnh lặng, thảnh thơi an yên êm đềm")
        self.assertEqual(res_calm['emotion'], 'calm')

        # 5. Energetic
        res_energetic = classify_vietnamese_emotion("Quẩy lên nào anh em ơi, bùng nổ năng lượng sôi động")
        self.assertEqual(res_energetic['emotion'], 'energetic')

        # 6. Angry
        res_angry = classify_vietnamese_emotion("Tức giận phẫn nộ, oán hận gào thét")
        self.assertEqual(res_angry['emotion'], 'angry')

        # Softmax sum assertion across all 6 labels
        scores = res_happy['scores']
        for lbl in EMOTION_LABELS:
            self.assertIn(lbl, scores)
        self.assertAlmostEqual(sum(scores.values()), 1.0, places=2)

    def test_neural_embedding_strictly_3072_dimensions(self):
        text = "Nhạc V-Pop trữ tình, giai điệu piano êm dịu, ca từ sâu sắc"
        vec = get_neural_embedding(text)
        self.assertIsNotNone(vec)
        self.assertEqual(vec.shape, (3072,))
        norm = float(np.linalg.norm(vec))
        self.assertAlmostEqual(norm, 1.0, places=3)

    def test_full_song_options_api(self):
        res = self.client.get('/api/ai/generate/full/options/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('genres', res.data)
        self.assertIn('moods', res.data)
        self.assertIn('voice_profiles', res.data)
        voices = res.data['voices']
        self.assertIn('female_vi', voices)
        self.assertIn('male_vi', voices)

    def test_emotion_classify_api_endpoint(self):
        res = self.client.post('/api/ai/emotion/classify/', {
            'text': 'Khúc nhạc thanh bình êm đềm'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['emotion'], 'calm')
        self.assertIn('confidence', res.data)
        self.assertIn('scores', res.data)
