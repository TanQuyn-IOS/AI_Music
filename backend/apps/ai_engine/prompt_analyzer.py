"""
Sonavia Studio — Prompt Analyzer Engine
========================================
Phân tích thông minh prompt ngắn của người dùng để suy luận đầy đủ:
- Language (vi, ko, ja, zh, en) với tính năng phát hiện tự động AUTO
- Genre & Sub-genre (30+ thể loại âm nhạc)
- Mood (cảm xúc)
- Vocal Gender & Style
- Tempo / BPM
- Musical Key
- Instruments
- Song Structure
- Production Style
- Lyric Theme & Energy
"""

import re
import unicodedata

# ─── Bảng nhận diện ngôn ngữ bằng ký tự đặc trưng ────────────────────────────

def detect_language(text: str) -> str:
    """
    Phát hiện ngôn ngữ đích cho bài hát từ văn bản prompt:
    1. Native scripts:
       - Hangul -> ko (한국어)
       - Hiragana / Katakana -> ja (日本語)
       - Hanzi -> zh (中文)
    2. Từ khóa thể loại / ngôn ngữ đích được yêu cầu:
       - "k-pop", "kpop", "tiếng hàn", "hàn quốc", "korean" -> ko
       - "j-pop", "jpop", "tiếng nhật", "nhật bản", "anime", "japanese" -> ja
       - "c-pop", "cpop", "tiếng trung", "hoa ngữ", "chinese", "mandarin" -> zh
       - "english", "tiếng anh", "us-uk", "us uk" -> en
       - "v-pop", "vpop", "nhạc việt", "tiếng việt", "vietnamese" -> vi
    3. Ngôn ngữ nhập nếu không ghi rõ thể loại:
       - Tiếng Việt có dấu -> vi
       - Mặc định -> en (hoặc vi nếu có từ vựng tiếng Việt)
    """
    if not text or not text.strip():
        return "vi"

    text_lower = text.lower()

    # 1. Native scripts (chữ viết bản địa)
    # Tiếng Hàn (Hangul)
    if re.search(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]', text):
        return "ko"

    # Tiếng Nhật (Hiragana / Katakana)
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
        return "ja"

    # 2. Từ khóa thể loại / ngôn ngữ đích được yêu cầu trong prompt
    # Cho dù người dùng mô tả bằng tiếng Việt (ví dụ: "K-pop buồn về tình yêu, nữ hát")
    # thì AI hiểu ngôn ngữ bài hát phải là Tiếng Hàn (ko)!
    if any(k in text_lower for k in ["k-pop", "kpop", "tiếng hàn", "hàn quốc", "korean", "tieng han", "han quoc"]):
        return "ko"
    if any(k in text_lower for k in ["j-pop", "jpop", "tiếng nhật", "nhật bản", "anime", "japanese", "tieng nhat", "nhat ban", "anime opening"]):
        return "ja"
    if any(k in text_lower for k in ["c-pop", "cpop", "tiếng trung", "hoa ngữ", "chinese", "mandarin", "tieng trung"]):
        return "zh"
    if any(k in text_lower for k in ["english", "tiếng anh", "us-uk", "us uk", "pop dance", "tieng anh"]):
        return "en"
    if any(k in text_lower for k in ["v-pop", "vpop", "nhạc việt", "tiếng việt", "vietnamese", "nhac viet", "viet nam", "nhac viet nam"]):
        return "vi"

    # Tiếng Trung nếu có chữ Hán (và không có Hiragana/Katakana)
    if re.search(r'[\u4e00-\u9fff]', text):
        return "zh"

    # 3. Tiếng Việt có dấu đặc trưng
    viet_chars = set(
        'đĐơƠăĂưƯâÂêÊôÔ'
        'áàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệ'
        'íìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ'
    )
    if any(c in viet_chars for c in text):
        return "vi"

    # 4. Từ vựng tiếng Việt không dấu phổ biến
    vi_common_words = {"buon", "vui", "tinh yeu", "nhe nhang", "nam hat", "nu hat", "mua he", "tuoi tre", "tam trang"}
    words = set(text_lower.split())
    if words.intersection(vi_common_words):
        return "vi"

    return "en"


# ─── Bảng thể loại phong phú (30+ Genres) ────────────────────────────────────

GENRE_DATABASE = {
    "vpop": {
        "name": "V-Pop",
        "subgenres": ["V-Pop Ballad", "Nhạc Trẻ", "V-Indie", "Acoustic Pop"],
        "default_bpm": 85,
        "default_key": "C Major",
        "instruments": ["acoustic guitar", "piano", "strings", "soft drums", "bass"],
        "production": "warm, intimate, emotional, clean studio mix",
        "keywords": ["vpop", "v-pop", "nhạc việt", "việt nam", "vietnamese pop", "nhạc trẻ", "ballad việt"],
        "structure": "standard_pop",
    },
    "kpop": {
        "name": "K-Pop",
        "subgenres": ["K-Pop Dance", "Emotional K-Pop", "K-R&B", "K-Ballad"],
        "default_bpm": 118,
        "default_key": "A Minor",
        "instruments": ["synthesizer", "catchy synth lead", "808 bass", "modern electronic drums", "polished keys"],
        "production": "high energy, modern compressed beat, catchy hook, polished production",
        "keywords": ["kpop", "k-pop", "korean pop", "nhạc hàn", "hallyu", "idol pop"],
        "structure": "kpop_dance",
    },
    "jpop": {
        "name": "J-Pop",
        "subgenres": ["J-Rock", "Anime Opening", "City Pop", "J-Ballad"],
        "default_bpm": 138,
        "default_key": "E Major",
        "instruments": ["electric guitar", "fast driving drums", "bass guitar", "piano", "synth lead"],
        "production": "dynamic, bright, complex chord progression, anime soundtrack style",
        "keywords": ["jpop", "j-pop", "japanese pop", "anime", "anime opening", "ost", "j-rock"],
        "structure": "anime_ost",
    },
    "cpop": {
        "name": "C-Pop",
        "subgenres": ["Mandopop", "Chinese Ballad", "Guofeng Pop", "Cantopop"],
        "default_bpm": 76,
        "default_key": "D Minor",
        "instruments": ["erhu", "guzheng", "piano", "cinematic strings", "soft percussion"],
        "production": "poetic, atmospheric, emotional crescendo, traditional fusion",
        "keywords": ["cpop", "c-pop", "chinese pop", "mandopop", "nhạc hoa", "hoa ngữ", "guofeng"],
        "structure": "ballad",
    },
    "pop": {
        "name": "Pop",
        "subgenres": ["Dance Pop", "Synthpop", "Radio Pop", "Acoustic Pop"],
        "default_bpm": 120,
        "default_key": "G Major",
        "instruments": ["drums", "bass", "piano", "synth pad", "acoustic guitar"],
        "production": "catchy melody, radio-friendly, commercial stereo mix",
        "keywords": ["pop", "dance pop", "radio", "catchy", "mainstream"],
        "structure": "standard_pop",
    },
    "ballad": {
        "name": "Ballad",
        "subgenres": ["Piano Ballad", "Orchestral Ballad", "Power Ballad"],
        "default_bpm": 70,
        "default_key": "C Major",
        "instruments": ["grand piano", "orchestral strings", "warm bass", "gentle cymbal swells"],
        "production": "heartfelt, wide dynamic range, upfront emotional vocal",
        "keywords": ["ballad", "nhẹ nhàng", "sâu lắng", "power ballad", "slow"],
        "structure": "ballad",
    },
    "lofi": {
        "name": "Lo-Fi",
        "subgenres": ["Lo-Fi Chill", "Chillhop", "Study Beats", "Cozy Lo-Fi"],
        "default_bpm": 78,
        "default_key": "F Major",
        "instruments": ["vinyl crackle", "rhodes electric piano", "mellow jazz guitar", "dusty drums", "rain ambient"],
        "production": "warm tape saturation, relaxing, low-pass filter, cozy",
        "keywords": ["lo-fi", "lofi", "chill", "học bài", "thư giãn", "relax", "rain", "cozy", "study"],
        "structure": "lofi_loop",
    },
    "rnb": {
        "name": "R&B / Soul",
        "subgenres": ["Contemporary R&B", "Neo-Soul", "Trap Soul"],
        "default_bpm": 92,
        "default_key": "E Minor",
        "instruments": ["deep 808 bass", "rhodes piano", "finger snaps", "smooth synth chords", "silky vocal pads"],
        "production": "smooth groove, sensual, spacious reverb, expressive phrasing",
        "keywords": ["r&b", "rnb", "soul", "smooth", "quyến rũ", "groove"],
        "structure": "standard_pop",
    },
    "hip_hop": {
        "name": "Hip-Hop / Rap",
        "subgenres": ["Trap", "Boom Bap", "Melodic Rap", "Phonk"],
        "default_bpm": 135,
        "default_key": "F# Minor",
        "instruments": ["hard-hitting 808 bass", "hi-hat rolls", "snare", "dark synth lead", "bell melody"],
        "production": "punchy low-end, crisp percussion, rhythmic flow, aggressive compression",
        "keywords": ["hip-hop", "hip hop", "rap", "trap", "phonk", "beat", "flow"],
        "structure": "hiphop_rap",
    },
    "rock": {
        "name": "Rock",
        "subgenres": ["Alternative Rock", "Hard Rock", "Indie Rock", "Pop Punk"],
        "default_bpm": 130,
        "default_key": "D Major",
        "instruments": ["overdriven electric guitar", "bass guitar", "acoustic drum kit", "crash cymbals"],
        "production": "raw energy, driving rhythm, live band sound",
        "keywords": ["rock", "guitar điện", "mạnh mẽ", "alternative", "punk", "distortion"],
        "structure": "standard_pop",
    },
    "edm": {
        "name": "EDM / Dance",
        "subgenres": ["House", "Slap House", "Progressive EDM", "Festival Trap"],
        "default_bpm": 128,
        "default_key": "F Minor",
        "instruments": ["punchy kick drum", "saw synth lead", "sub bass", "risers", "vocal chops"],
        "production": "huge build-up, massive bass drop, wide stereo width, sidechain pump",
        "keywords": ["edm", "dance", "house", "sôi động", "quẩy", "drop", "synthwave"],
        "structure": "edm_drop",
    },
    "acoustic": {
        "name": "Acoustic / Folk",
        "subgenres": ["Folk Ballad", "Fingerstyle", "Campfire Acoustic", "Indie Folk"],
        "default_bpm": 88,
        "default_key": "G Major",
        "instruments": ["fingerpicked acoustic guitar", "shaker", "cajon", "warm upright bass"],
        "production": "intimate, natural room acoustics, unpolished raw emotion",
        "keywords": ["acoustic", "guitar mộc", "mộc mạc", "folk", "guitar gỗ"],
        "structure": "standard_pop",
    },
    "jazz": {
        "name": "Jazz & Blues",
        "subgenres": ["Smooth Jazz", "Bossa Nova", "Slow Blues", "Midnight Jazz"],
        "default_bpm": 95,
        "default_key": "Bb Major",
        "instruments": ["saxophone", "jazz piano", "walking upright bass", "brushed drums"],
        "production": "warm, vintage, rich harmonic texture, improvised feel",
        "keywords": ["jazz", "blues", "saxophone", "ngẫu hứng", "bossa nova"],
        "structure": "standard_pop",
    },
    "cinematic": {
        "name": "Cinematic / Classical",
        "subgenres": ["Film Score", "Epic Orchestral", "Piano Solo", "Emotional Ambient"],
        "default_bpm": 75,
        "default_key": "D Minor",
        "instruments": ["symphonic orchestra", "cello", "timpani", "choir", "french horn"],
        "production": "grand orchestral depth, epic build-up, dramatic dynamic contrast",
        "keywords": ["cinematic", "nhạc phim", "orchestra", "giao hưởng", "epic", "classical"],
        "structure": "ballad",
    },
}

# ─── Bảng phân tích tâm trạng (Mood & Energy) ────────────────────────────────

MOOD_DATABASE = {
    "sad": {
        "name": "Sad & Melancholic",
        "energy": "low",
        "tempo_modifier": 0.85,
        "mode": "Minor",
        "tags": ["sad", "heartbroken", "melancholic", "tearful", "emotional", "deep pain"],
        "keywords": ["buồn", "khóc", "chia tay", "cô đơn", "đau", "mất", "vỡ", "sad", "tear", "cry", "lonely", "heartbreak", "슬픈", "이별", "悲しい", "伤感"],
    },
    "happy": {
        "name": "Happy & Joyful",
        "energy": "high",
        "tempo_modifier": 1.15,
        "mode": "Major",
        "tags": ["happy", "cheerful", "uplifting", "bright", "sunny", "celebration"],
        "keywords": ["vui", "hạnh phúc", "yêu đời", "rực rỡ", "nắng", "happy", "joy", "cheerful", "fun", "bright", "기쁜", "행복", "楽しい", "快乐"],
    },
    "chill": {
        "name": "Calm & Relaxing",
        "energy": "medium-low",
        "tempo_modifier": 0.95,
        "mode": "Major",
        "tags": ["chill", "peaceful", "relaxing", "calm", "smooth", "soothing"],
        "keywords": ["chill", "bình yên", "thư giãn", "nhẹ nhàng", "mưa", "cà phê", "relax", "calm", "peaceful", "편안한", "穏やか", "放松"],
    },
    "energetic": {
        "name": "Energetic & Powerful",
        "energy": "very-high",
        "tempo_modifier": 1.25,
        "mode": "Major",
        "tags": ["energetic", "powerful", "driving", "hype", "explosive", "fast-paced"],
        "keywords": ["sôi động", "cháy", "bùng nổ", "mạnh mẽ", "nhiệt huyết", "energetic", "power", "hype", "fast", "신나는", "熱い", "燃", "热血"],
    },
    "romantic": {
        "name": "Romantic & Tender",
        "energy": "medium",
        "tempo_modifier": 1.0,
        "mode": "Major",
        "tags": ["romantic", "sweet", "loving", "tender", "heartfelt", "warm"],
        "keywords": ["lãng mạn", "tình yêu", "ngọt ngào", "say đắm", "hẹn hò", "romantic", "love", "sweet", "tender", "사랑", "ロマンチック", "浪漫"],
    },
    "nostalgic": {
        "name": "Nostalgic & Bittersweet",
        "energy": "medium-low",
        "tempo_modifier": 0.92,
        "mode": "Minor",
        "tags": ["nostalgic", "memories", "bittersweet", "longing", "retro", "youth"],
        "keywords": ["thanh xuân", "hoài niệm", "tuổi trẻ", "kỷ niệm", "nhớ", "xưa", "nostalgia", "memories", "youth", "추억", "懐かしい", "回忆"],
    },
}

# ─── Bảng cấu trúc bài hát theo thể loại ─────────────────────────────────────

SONG_STRUCTURES = {
    "standard_pop": [
        {"type": "intro", "label": "[Intro]", "duration_weight": 0.08},
        {"type": "verse_1", "label": "[Verse 1]", "duration_weight": 0.20},
        {"type": "pre_chorus", "label": "[Pre-Chorus]", "duration_weight": 0.10},
        {"type": "chorus", "label": "[Chorus]", "duration_weight": 0.22},
        {"type": "verse_2", "label": "[Verse 2]", "duration_weight": 0.16},
        {"type": "bridge", "label": "[Bridge]", "duration_weight": 0.10},
        {"type": "final_chorus", "label": "[Final Chorus]", "duration_weight": 0.22},
        {"type": "outro", "label": "[Outro]", "duration_weight": 0.08},
    ],
    "ballad": [
        {"type": "intro", "label": "[Intro]", "duration_weight": 0.10},
        {"type": "verse_1", "label": "[Verse 1]", "duration_weight": 0.22},
        {"type": "chorus", "label": "[Chorus]", "duration_weight": 0.24},
        {"type": "verse_2", "label": "[Verse 2]", "duration_weight": 0.18},
        {"type": "bridge", "label": "[Bridge]", "duration_weight": 0.12},
        {"type": "final_chorus", "label": "[Final Chorus]", "duration_weight": 0.26},
        {"type": "outro", "label": "[Outro]", "duration_weight": 0.10},
    ],
    "kpop_dance": [
        {"type": "intro", "label": "[Intro]", "duration_weight": 0.08},
        {"type": "verse_1", "label": "[Verse 1]", "duration_weight": 0.18},
        {"type": "pre_chorus", "label": "[Pre-Chorus]", "duration_weight": 0.10},
        {"type": "chorus", "label": "[Chorus]", "duration_weight": 0.24},
        {"type": "verse_2", "label": "[Verse 2]", "duration_weight": 0.15},
        {"type": "rap_verse", "label": "[Rap Verse]", "duration_weight": 0.12},
        {"type": "bridge", "label": "[Bridge]", "duration_weight": 0.08},
        {"type": "dance_break", "label": "[Dance Break]", "duration_weight": 0.10},
        {"type": "final_chorus", "label": "[Final Chorus]", "duration_weight": 0.22},
        {"type": "outro", "label": "[Outro]", "duration_weight": 0.08},
    ],
    "anime_ost": [
        {"type": "intro", "label": "[Intro]", "duration_weight": 0.10},
        {"type": "verse_1", "label": "[Verse 1]", "duration_weight": 0.18},
        {"type": "pre_chorus", "label": "[Pre-Chorus]", "duration_weight": 0.12},
        {"type": "chorus", "label": "[Chorus]", "duration_weight": 0.25},
        {"type": "verse_2", "label": "[Verse 2]", "duration_weight": 0.16},
        {"type": "guitar_solo", "label": "[Guitar Solo]", "duration_weight": 0.12},
        {"type": "bridge", "label": "[Bridge]", "duration_weight": 0.10},
        {"type": "final_chorus", "label": "[Final Chorus]", "duration_weight": 0.25},
        {"type": "outro", "label": "[Outro]", "duration_weight": 0.08},
    ],
    "lofi_loop": [
        {"type": "intro", "label": "[Intro]", "duration_weight": 0.15},
        {"type": "theme_a", "label": "[Theme A]", "duration_weight": 0.35},
        {"type": "variation", "label": "[Variation]", "duration_weight": 0.35},
        {"type": "outro", "label": "[Outro]", "duration_weight": 0.15},
    ],
    "hiphop_rap": [
        {"type": "intro", "label": "[Intro]", "duration_weight": 0.08},
        {"type": "hook", "label": "[Hook]", "duration_weight": 0.20},
        {"type": "verse_1", "label": "[Verse 1]", "duration_weight": 0.26},
        {"type": "hook", "label": "[Hook]", "duration_weight": 0.20},
        {"type": "verse_2", "label": "[Verse 2]", "duration_weight": 0.26},
        {"type": "outro", "label": "[Outro]", "duration_weight": 0.08},
    ],
    "edm_drop": [
        {"type": "intro", "label": "[Intro]", "duration_weight": 0.10},
        {"type": "verse", "label": "[Verse]", "duration_weight": 0.15},
        {"type": "build_up", "label": "[Build Up]", "duration_weight": 0.12},
        {"type": "drop", "label": "[Drop]", "duration_weight": 0.25},
        {"type": "break", "label": "[Break]", "duration_weight": 0.10},
        {"type": "build_up", "label": "[Build Up]", "duration_weight": 0.12},
        {"type": "final_drop", "label": "[Final Drop]", "duration_weight": 0.25},
        {"type": "outro", "label": "[Outro]", "duration_weight": 0.08},
    ],
}


def match_keyword_in_text(kw: str, text: str, text_unaccented: str) -> bool:
    """Kiểm tra keyword xuất hiện trong text với word boundary để tránh va chạm chuỗi con."""
    kw_lower = kw.lower()
    # Với tiếng Hàn / Trung / Nhật: không dùng space phân cách nên kiểm tra trực tiếp
    if re.search(r'[\u3040-\u9fff\uac00-\ud7af]', kw):
        return kw_lower in text

    # Khớp chính xác với word boundary
    pattern = rf'(?:^|[^\w]){re.escape(kw_lower)}(?:$|[^\w])'
    if re.search(pattern, text, re.IGNORECASE):
        return True

    # Khớp không dấu nếu keyword >= 3 ký tự (tránh các từ ngắn như 'vỡ' -> 'vo' va chạm 'vocal')
    import unicodedata
    kw_unacc = ''.join(c for c in unicodedata.normalize('NFD', kw_lower) if unicodedata.category(c) != 'Mn').replace('đ', 'd').replace('Đ', 'D')
    if len(kw_unacc) >= 3:
        pattern_unacc = rf'(?:^|[^\w]){re.escape(kw_unacc)}(?:$|[^\w])'
        if re.search(pattern_unacc, text_unaccented, re.IGNORECASE):
            return True

    return False


class PromptAnalyzerService:
    """
    Phân tích toàn diện prompt tự nhiên của người dùng để trả về cấu hình bài hát chi tiết.
    """

    @classmethod
    def analyze(cls, prompt: str, user_language: str = "auto", user_vocal: str = "auto", is_instrumental: bool = False) -> dict:
        """
        Phân tích prompt và trả về SongConfiguration dictionary chuẩn.
        - Ưu tiên: Sử dụng Neural LLM Zero-Shot Reasoning (Google Gemini) để thấu cảm ngữ cảnh,
          cảm xúc ẩn dụ, phong cách âm nhạc đa chiều.
        - Dự phòng: Tự động fallback sang Rule-based NLP nếu mất mạng hoặc offline.
        """
        clean_prompt = prompt.strip() if prompt else "Bài hát về tình yêu cuộc sống"

        # ── 0. THỬ PHÂN TÍCH BẰNG NEURAL LLM REASONING THỰC SỰ ──
        try:
            from .llm_service import is_llm_available, analyze_prompt_with_llm
            if is_llm_available():
                llm_config = analyze_prompt_with_llm(
                    prompt=clean_prompt,
                    user_language=user_language,
                    user_vocal=user_vocal,
                    is_instrumental=is_instrumental,
                )
                if llm_config and llm_config.get("genre") and llm_config.get("bpm"):
                    if user_language and user_language.lower() != "auto":
                        llm_config["language"] = user_language.lower()
                    genre_k = llm_config.get("genre", "vpop")
                    g_info = GENRE_DATABASE.get(genre_k, GENRE_DATABASE.get("pop", {}))
                    struct_k = g_info.get("structure", "standard_pop")
                    llm_config["structure_name"] = struct_k
                    llm_config["structure"] = SONG_STRUCTURES.get(struct_k, SONG_STRUCTURES["standard_pop"])
                    llm_config["prompt"] = clean_prompt
                    llm_config["is_real_ai"] = True
                    llm_config["analyzer_engine"] = "Neural LLM Zero-Shot Reasoning"
                    return llm_config
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"[PromptAnalyzer] LLM analysis fallback: {e}")

        prompt_lower = clean_prompt.lower()
        import unicodedata
        prompt_unaccented = ''.join(c for c in unicodedata.normalize('NFD', prompt_lower) if unicodedata.category(c) != 'Mn').replace('đ', 'd').replace('Đ', 'D')

        # 1. Xác định Language
        if user_language and user_language.lower() != "auto":
            lang = user_language.lower()
        else:
            lang = detect_language(clean_prompt)

        # 2. Xác định Thể loại (Genre)
        detected_genre_key = "vpop" if lang == "vi" else ("kpop" if lang == "ko" else ("jpop" if lang == "ja" else ("cpop" if lang == "zh" else "pop")))
        for g_key, g_info in GENRE_DATABASE.items():
            if any(match_keyword_in_text(kw, prompt_lower, prompt_unaccented) for kw in g_info["keywords"]):
                detected_genre_key = g_key
                break

        genre_info = GENRE_DATABASE.get(detected_genre_key, GENRE_DATABASE["pop"])

        # 3. Xác định Tâm trạng (Mood & Energy)
        detected_mood_key = "happy"
        for m_key, m_info in MOOD_DATABASE.items():
            if any(match_keyword_in_text(kw, prompt_lower, prompt_unaccented) for kw in m_info["keywords"]):
                detected_mood_key = m_key
                break

        mood_info = MOOD_DATABASE.get(detected_mood_key, MOOD_DATABASE["happy"])

        # 4. Xác định Giọng hát (Vocal Gender & Style)
        if is_instrumental or any(k in prompt_lower or k in prompt_unaccented for k in ["không lời", "khong loi", "instrumental", "nhạc nền", "nhac nen", "beat", "no vocals", "no vocal"]):
            vocal_gender = "instrumental"
            vocal_desc = "Không lời (Thuần nhạc cụ)"
        elif user_vocal and user_vocal != "auto":
            vocal_gender = user_vocal
            vocal_desc = "Giọng Nữ" if vocal_gender == "female" else ("Giọng Nam" if vocal_gender == "male" else "Song ca Nam Nữ")
        else:
            # Tự động trích xuất từ prompt - Ưu tiên Song ca (Duet) trước
            is_duet = any(k in prompt_lower or k in prompt_unaccented for k in ["song ca", "duet", "nam nữ", "nam nu", "nam và nữ", "nam va nu", "hòa giọng", "hoa giong"])

            # Kiểm tra giọng Nữ
            is_female = any(k in prompt_lower or k in prompt_unaccented for k in [
                "giọng nữ", "giong nu", "nữ hát", "nu hat", "nữ ca sĩ", "nu ca si",
                "cô gái hát", "co gai hat", "female vocal", "female singer", "female voice",
                "woman vocal", "girl vocal"
            ]) or bool(re.search(r'\b(female|woman|girl|nữ)\b', prompt_lower)) or bool(re.search(r'\bnu\b', prompt_unaccented) and any(w in prompt_unaccented for w in ["hat", "ca si", "giong", "nu"]))

            # Kiểm tra giọng Nam (tránh match 'man' trong 'manh me', 'romance' và 'nam' trong 'viet nam')
            is_male = any(k in prompt_lower or k in prompt_unaccented for k in [
                "giọng nam", "giong nam", "nam hát", "nam hat", "nam ca sĩ", "nam ca si",
                "chàng trai hát", "chang trai hat", "male vocal", "male singer", "male voice",
                "man vocal", "boy vocal"
            ]) or bool(re.search(r'\b(male|boy)\b', prompt_lower)) or bool(re.search(r'\bman\b', prompt_lower) and not re.search(r'\bmanh\b', prompt_unaccented)) or bool(re.search(r'(?<!việt\s)(?<!viet\s)\bnam\b(?!\s*tiến)', prompt_unaccented) and any(w in prompt_unaccented for w in ["hat", "ca si", "giong"]))

            if is_duet:
                vocal_gender = "duet"
                vocal_desc = "Song ca Nam & Nữ"
            elif is_female:
                vocal_gender = "female"
                vocal_desc = "Giọng Nữ truyền cảm"
            elif is_male:
                vocal_gender = "male"
                vocal_desc = "Giọng Nam trầm ấm"
            else:
                # Default vocal theo genre
                if detected_genre_key in ["kpop", "vpop", "ballad", "jpop", "cpop"]:
                    vocal_gender = "female"
                    vocal_desc = "Giọng Nữ trong trẻo"
                elif detected_genre_key in ["rock", "hip_hop"]:
                    vocal_gender = "male"
                    vocal_desc = "Giọng Nam mạnh mẽ"
                else:
                    vocal_gender = "female"
                    vocal_desc = "Giọng Nữ tự nhiên"

        # 5. Xác định Tempo / BPM
        # Trích xuất số BPM nếu người dùng ghi rõ (ví dụ: "120 bpm" hoặc "khoảng 115 bpm")
        bpm_match = re.search(r'(\d{2,3})\s*(?:bpm|nhịp)', prompt_lower)
        if bpm_match:
            bpm = int(bpm_match.group(1))
            bpm = max(60, min(bpm, 180))
        else:
            base_bpm = genre_info["default_bpm"]
            modifier = mood_info["tempo_modifier"]
            bpm = int(round(base_bpm * modifier))

        # 6. Xác định Musical Key
        key = f"{genre_info['default_key'].split()[0]} {mood_info['mode']}"

        # 7. Nhạc cụ (Instruments)
        instruments = list(genre_info["instruments"])
        # Nếu prompt có nhắc nhạc cụ riêng, đưa lên đầu
        extra_inst_map = {
            "piano": "grand piano",
            "guitar": "acoustic guitar",
            "guitar điện": "electric guitar",
            "trống": "drums",
            "violin": "violin strings",
            "đàn tranh": "guzheng",
            "sáo": "bamboo flute",
            "synth": "analog synthesizer",
            "bass": "808 bass",
        }
        for kw, inst in extra_inst_map.items():
            if kw in prompt_lower and inst not in instruments:
                instruments.insert(0, inst)

        # 8. Cấu trúc bài hát (Structure)
        struct_key = genre_info.get("structure", "standard_pop")
        structure = SONG_STRUCTURES.get(struct_key, SONG_STRUCTURES["standard_pop"])

        # 9. Chủ đề ca từ (Lyric Theme)
        theme = "love"
        if any(k in prompt_lower for k in ["chia tay", "mất", "đau", "breakup", "sad", "rời xa"]):
            theme = "breakup"
        elif any(k in prompt_lower for k in ["mùa hè", "summer", "biển", "nắng"]):
            theme = "summer"
        elif any(k in prompt_lower for k in ["thanh xuân", "tuổi trẻ", "học trò", "youth", "school"]):
            theme = "youth"
        elif any(k in prompt_lower for k in ["chill", "thư giãn", "mưa", "đêm"]):
            theme = "relax"
        elif any(k in prompt_lower for k in ["đam mê", "chiến đấu", "ước mơ", "tiến lên"]):
            theme = "motivation"

        # 10. Tạo Prompt hoàn chỉnh cho Music Generator
        prompt_tags = [
            f"{genre_info['name']}",
            f"{genre_info['subgenres'][0]}",
            f"{mood_info['name']}",
            f"{bpm} BPM",
            f"key of {key}",
            f"{', '.join(instruments[:4])}",
            f"{genre_info['production']}",
            "studio quality master",
        ]

        if vocal_gender != "instrumental":
            lang_name_map = {"vi": "Vietnamese", "ko": "Korean", "ja": "Japanese", "zh": "Chinese", "en": "English"}
            lang_label = lang_name_map.get(lang, "Vietnamese")
            if vocal_gender == "female":
                prompt_tags.insert(0, f"solo {lang_label} female vocals, clear articulate singing, expressive natural phrasing")
            elif vocal_gender == "male":
                prompt_tags.insert(0, f"solo {lang_label} male vocals, warm deep singing, articulate pronunciation")
            elif vocal_gender == "duet":
                prompt_tags.insert(0, f"{lang_label} duet vocals, male and female vocal harmony, clear singing")
        else:
            prompt_tags.insert(0, "instrumental, no vocals, melodic lead instruments")

        final_model_prompt = ", ".join(prompt_tags)

        return {
            "prompt": clean_prompt,
            "language": lang,
            "genre": detected_genre_key,
            "genre_name": genre_info["name"],
            "subgenre": genre_info["subgenres"][0],
            "mood": detected_mood_key,
            "mood_name": mood_info["name"],
            "energy": mood_info["energy"],
            "vocal_gender": vocal_gender,
            "vocal_desc": vocal_desc,
            "bpm": bpm,
            "key": key,
            "instruments": instruments,
            "theme": theme,
            "structure_name": struct_key,
            "structure": structure,
            "production_style": genre_info["production"],
            "model_prompt": final_model_prompt,
        }
