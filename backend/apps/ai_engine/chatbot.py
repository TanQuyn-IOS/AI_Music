"""
AI Chatbot tư vấn âm nhạc
"""
import random
import re
import unicodedata

def remove_vietnamese_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt để đối sánh linh hoạt cả có dấu lẫn không dấu."""
    nfkd = unicodedata.normalize('NFD', text)
    unaccented = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    return unaccented.replace('đ', 'd').replace('Đ', 'D')

# Từ điển ánh xạ mood → genre đề xuất (hỗ trợ cả tiếng Việt có dấu, không dấu và tiếng Anh)
MOOD_KEYWORDS = {
    'sad': [
        'buồn', 'buon', 'thất tình', 'that tinh', 'cô đơn', 'co don', 'khóc', 'khoc',
        'đau lòng', 'dau long', 'đau', 'dau', 'tan vỡ', 'tan vo', 'mệt mỏi', 'met moi',
        'áp lực', 'ap luc', 'bế tắc', 'be tac', 'tâm trạng', 'tam trang', 'chán', 'chan',
        'nản', 'nan', 'chia tay', 'roi xa', 'rời xa', 'sad', 'cry', 'lonely', 'breakup'
    ],
    'happy': [
        'vui', 'vui vẻ', 'vui ve', 'hạnh phúc', 'hanh phuc', 'yêu đời', 'yeu doi',
        'tươi vui', 'tuoi vui', 'cười', 'cuoi', 'tuyệt vời', 'tuyet voi', 'phấn chấn',
        'phan chan', 'happy', 'joy', 'smile', 'cheerful'
    ],
    'energetic': [
        'sôi động', 'soi dong', 'năng động', 'nang dong', 'quẩy', 'quay', 'cháy', 'chay',
        'bốc', 'boc', 'nhiệt huyết', 'nhiet huyet', 'tập gym', 'tap gym', 'thể thao', 'the thao',
        'chạy bộ', 'chay bo', 'mạnh mẽ', 'manh me', 'bùng nổ', 'bung no', 'energetic', 'party',
        'workout', 'power'
    ],
    'calm': [
        'thư giãn', 'thu gian', 'nhẹ nhàng', 'nhe nhang', 'bình yên', 'binh yen', 'chill',
        'ngủ ngon', 'ngu ngon', 'dễ ngủ', 'de ngu', 'tĩnh tâm', 'tinh tam', 'học bài', 'hoc bai',
        'đọc sách', 'doc sach', 'tập trung', 'tap trung', 'làm việc', 'lam viec', 'calm',
        'relax', 'peaceful', 'sleep', 'study'
    ],
    'romantic': [
        'lãng mạn', 'lang man', 'tình yêu', 'tinh yeu', 'ngọt ngào', 'ngot ngao', 'hẹn hò',
        'hen ho', 'tỏ tình', 'to tinh', 'nhớ người yêu', 'nho nguoi yeu', 'crush', 'thương',
        'thuong', 'yêu', 'yeu', 'romantic', 'love', 'date', 'sweet'
    ],
    'melancholic': [
        'hoài niệm', 'hoai niem', 'xưa', 'xua', 'kỷ niệm', 'ky niem', 'thanh xuân', 'thanh xuan',
        'tuổi thơ', 'tuoi tho', 'nhớ nhà', 'nho nha', 'quá khứ', 'qua khu', 'nhớ', 'nho',
        'melancholic', 'nostalgia', 'memories', 'retro'
    ],
    'uplifting': [
        'phấn khởi', 'phan khoi', 'động lực', 'dong luc', 'truyền cảm hứng', 'truyen cam hung',
        'hy vọng', 'hy vong', 'vươn lên', 'vuon len', 'tự tin', 'tu tin', 'cố lên', 'co len',
        'chiến thắng', 'chien thang', 'uplifting', 'inspired', 'hope', 'motivation'
    ],
    'angry': [
        'tức giận', 'tuc gian', 'giận', 'gian', 'bực bội', 'buc boi', 'cáu gắt', 'cau gat',
        'bực mình', 'buc minh', 'tức', 'tuc', 'ức chế', 'uc che', 'angry', 'mad', 'rage'
    ],
}

MOOD_TO_MUSIC_GENRE = {
    'sad': ['vpop', 'ballad', 'indie', 'folk', 'blues'],
    'melancholic': ['vpop', 'acoustic', 'classical', 'jazz', 'indie'],
    'happy': ['pop', 'vpop', 'kpop', 'edm'],
    'uplifting': ['pop', 'r&b', 'electronic', 'rock'],
    'energetic': ['rock', 'electronic', 'edm', 'hip_hop'],
    'calm': ['lofi', 'acoustic', 'classical', 'jazz', 'folk'],
    'romantic': ['vpop', 'ballad', 'r&b', 'pop', 'jazz'],
    'angry': ['rock', 'metal', 'hip_hop'],
}

CHATBOT_RESPONSES = {
    'greeting': [
        "Xin chào! Tôi là AI Music Assistant của Sonavia 🎵 Tôi có thể giúp bạn tìm nhạc, gợi ý playlist hoặc chọn phong cách sáng tác phù hợp với tâm trạng của bạn hôm nay.",
        "Chào bạn! 👋 Hãy cho tôi biết cảm xúc hoặc hoạt động hiện tại của bạn (học bài, tập gym, thư giãn, buồn...), tôi sẽ gợi ý những giai điệu tuyệt nhất nhé!",
    ],
    'unknown': [
        "Tôi chưa hiểu rõ ý bạn lắm. Bạn có thể cho tôi biết cảm xúc hoặc thể loại bạn muốn nghe không? Ví dụ: 'Tôi đang buồn', 'Cần nhạc tập gym', 'Gợi ý nhạc V-Pop chill'",
        "Hmm, bạn đang cảm thấy thế nào hôm nay? Hãy chia sẻ với tôi để tôi tìm những bản nhạc đồng điệu nhất với bạn nhé!",
    ],
}


def detect_mood_from_text(text: str) -> str:
    """Phát hiện tâm trạng từ văn bản (hỗ trợ cả có dấu và không dấu)."""
    text_lower = text.lower().strip()
    text_unaccented = remove_vietnamese_accents(text_lower)

    for mood, keywords in MOOD_KEYWORDS.items():
        for kw in keywords:
            kw_clean = kw.lower()
            if kw_clean in text_lower or kw_clean in text_unaccented:
                return mood

    return None


def get_chatbot_response(message, songs=None):
    """
    Xử lý tin nhắn và trả lời:
    - Ưu tiên: Sử dụng LLM (Google Gemini / OpenAI) để hiểu tâm lý, phân tích cảm xúc
      và gợi ý âm nhạc chân thực, linh hoạt.
    - Dự phòng: Tự động fallback về thuật toán rule-based nếu chưa cấu hình API key.
    """
    # ── 1. Thử gọi LLM Service thông minh thực thụ ──
    try:
        from .llm_service import is_llm_available, chat_with_music_llm
        if is_llm_available():
            llm_result = chat_with_music_llm(message=message, songs_pool=songs)
            if llm_result and llm_result.get("message"):
                return llm_result
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[Chatbot] Fallback từ LLM sang Rule-based: {e}")

    text = message.lower().strip()
    text_unaccented = remove_vietnamese_accents(text)

    # Chào hỏi
    if any(w in text or w in text_unaccented for w in ['xin chào', 'xin chao', 'hello', 'hi', 'chào', 'chao', 'hey', 'alo']):
        msg = random.choice(CHATBOT_RESPONSES['greeting'])
        return {
            'message': msg,
            'reply': msg,
            'mood': None,
            'recommended_genres': [],
            'songs': [],
        }

    # Phát hiện mood
    detected_mood = detect_mood_from_text(text)

    if detected_mood:
        genres = MOOD_TO_MUSIC_GENRE.get(detected_mood, [])

        # Lọc bài hát theo mood và genre
        recommended_songs = []
        if songs:
            mood_songs = [s for s in songs if getattr(s, 'mood', '') == detected_mood]
            if not mood_songs:
                mood_songs = [s for s in songs if getattr(s, 'genre', '') in genres]
            recommended_songs = mood_songs[:5]

        mood_messages = {
            'sad': "Tôi hiểu bạn đang có những tâm sự hoặc nỗi buồn 💙 Hãy để những giai điệu sâu lắng này vỗ về cảm xúc của bạn:",
            'melancholic': "Những phút giây hoài niệm về kỷ niệm xưa 🌙 Dưới đây là những bản nhạc đưa bạn về với những tháng ngày êm đềm:",
            'happy': "Thật tuyệt vời khi thấy bạn đang ngập tràn niềm vui! 🌟 Cùng đón nhận nguồn năng lượng tích cực này nhé:",
            'uplifting': "Hãy để âm nhạc tiếp thêm sức mạnh và niềm tin cho bạn hôm nay! ⚡",
            'energetic': "Năng lượng bùng cháy! 🔥 Dưới đây là những bản nhạc beat căng tràn đầy nhiệt huyết cho bạn:",
            'calm': "Tạm gác lại những bộn bề, cùng thư giãn trong không gian bình yên này nhé 🌿",
            'romantic': "Không gian thật ngọt ngào và lãng mạn 💕 Những giai điệu tình yêu này sinh ra là dành riêng cho bạn:",
            'angry': "Hãy để âm nhạc mạnh mẽ giúp bạn giải tỏa hết những bực bội và căng thẳng nhé! 💪",
        }

        response_msg = mood_messages.get(detected_mood, "Dưới đây là những giai điệu phù hợp nhất dành cho bạn:")

        if genres:
            genre_names = [g.upper() for g in genres[:3]]
            response_msg += f"\n\n🎵 Thể loại gợi ý: {', '.join(genre_names)}"

        return {
            'message': response_msg,
            'reply': response_msg,
            'mood': detected_mood,
            'recommended_genres': genres,
            'songs': [{'id': s.id, 'title': s.title, 'artist': (s.artist.username if s.artist else 'Sonavia AI')} for s in recommended_songs],
        }

    # Xử lý các câu hỏi xin gợi ý chung
    if any(w in text or w in text_unaccented for w in ['nhạc gì', 'nhac gi', 'nghe gì', 'nghe gi', 'gợi ý', 'goi y', 'đề xuất', 'de xuat', 'recommend']):
        msg = "Hãy cho tôi biết cảm xúc hoặc hoàn cảnh của bạn nhé! Ví dụ:\n• 'Tôi đang buồn, muốn nghe bài gì sâu lắng'\n• 'Cần nhạc nhẹ nhàng để học bài'\n• 'Gợi ý nhạc tập gym sôi động'\n• 'Tôi muốn nghe V-Pop lãng mạn'"
        return {
            'message': msg,
            'reply': msg,
            'mood': None,
            'recommended_genres': [],
            'songs': [],
        }

    # Hỏi về thể loại cụ thể
    genre_keywords = {
        'pop': 'pop', 'rock': 'rock', 'jazz': 'jazz', 'v-pop': 'vpop',
        'vpop': 'vpop', 'k-pop': 'kpop', 'kpop': 'kpop', 'j-pop': 'jpop',
        'jpop': 'jpop', 'c-pop': 'cpop', 'cpop': 'cpop', 'ballad': 'ballad',
        'lofi': 'lofi', 'lo-fi': 'lofi', 'acoustic': 'acoustic',
        'indie': 'indie', 'rap': 'hip_hop', 'hip hop': 'hip_hop',
        'edm': 'electronic', 'electronic': 'electronic', 'r&b': 'r&b',
    }
    for keyword, genre in genre_keywords.items():
        if keyword in text:
            song_list = []
            if songs:
                song_list = [s for s in songs if getattr(s, 'genre', '') == genre][:5]
            msg = f"🎵 Đây là những bản nhạc {keyword.upper()} tuyển chọn dành cho bạn:"
            return {
                'message': msg,
                'reply': msg,
                'mood': None,
                'recommended_genres': [genre],
                'songs': [{'id': s.id, 'title': s.title, 'artist': (s.artist.username if s.artist else 'Sonavia AI')} for s in song_list],
            }

    fallback_msg = random.choice(CHATBOT_RESPONSES['unknown'])
    return {
        'message': fallback_msg,
        'reply': fallback_msg,
        'mood': None,
        'recommended_genres': [],
        'songs': [],
    }
