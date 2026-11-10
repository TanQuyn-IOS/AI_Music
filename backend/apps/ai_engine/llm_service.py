"""
Sonavia Studio — LLM Service (Phase 4: True AI Brain)
======================================================
Tích hợp mô hình ngôn ngữ lớn (Google Gemini / OpenAI) cho:
1. Sáng tác lời bài hát (Lyrics Generation) giàu cảm xúc, vần điệu chuẩn nhạc lý.
2. AI Chatbot tư vấn âm nhạc và phân tích tâm trạng thông minh, tự nhiên.

Hỗ trợ:
- Google Gemini: gemini-2.5-flash / gemini-2.0-flash / gemini-1.5-flash (Có gói miễn phí cực rộng)
- OpenAI: gpt-4o-mini / gpt-4o
- Tự động fallback mượt mà nếu chưa có API Key hoặc gặp sự cố mạng (không crash app).
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Danh sách model Gemini ưu tiên (sử dụng các model đang hoạt động ổn định nhất)
GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
]

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _get_env(key: str, default: str = "") -> str:
    """Lấy biến môi trường từ os hoặc settings Django hoặc file .env."""
    val = os.environ.get(key, "").strip()
    if not val:
        try:
            from django.conf import settings
            val = getattr(settings, key, "").strip()
        except Exception:
            pass
    if not val:
        try:
            from dotenv import dotenv_values
            base_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env_path = os.path.join(base_backend, ".env")
            if os.path.exists(env_path):
                vals = dotenv_values(env_path)
                val = vals.get(key, "").strip()
        except Exception:
            pass
    return val or default


def get_active_provider() -> Tuple[Optional[str], str]:
    """
    Xác định provider LLM đang khả dụng.
    Returns: (provider_name: 'gemini' | 'openai' | None, api_key: str)
    """
    provider_pref = _get_env("LLM_PROVIDER", "auto").lower()
    gemini_key = _get_env("GEMINI_API_KEY", "")
    openai_key = _get_env("OPENAI_API_KEY", "")

    if provider_pref == "gemini" and gemini_key:
        return "gemini", gemini_key
    if provider_pref == "openai" and openai_key:
        return "openai", openai_key

    # Chế độ 'auto': ưu tiên Gemini (vì có free tier rất lớn), sau đó đến OpenAI
    if gemini_key:
        return "gemini", gemini_key
    if openai_key:
        return "openai", openai_key

    return None, ""


def is_llm_available() -> bool:
    provider, key = get_active_provider()
    return provider is not None and bool(key)


# ─── GỌI GEMINI REST API ────────────────────────────────────────────────────────

def _call_gemini_api(
    prompt: str,
    system_instruction: str = "",
    api_key: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    Gọi Google Gemini API qua REST interface tiêu chuẩn bằng httpx/requests.
    Không cần cài đặt thư viện ngoài cồng kềnh, hoạt động 100% ổn định.
    """
    import httpx

    preferred_model = _get_env("GEMINI_MODEL", "")
    models_to_try = [preferred_model] if preferred_model else []
    for m in GEMINI_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }

    if system_instruction:
        payload["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    last_error = None
    # Fast check: Validate Gemini API key structure early to avoid wasting network timeouts
    if not (api_key.startswith("AIzaSy") or api_key.startswith("ya29.")):
        logger.debug("[Gemini] API Key format is not standard Google API key ('AIzaSy...' or 'ya29...'). Falling back.")
        return None

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            headers = {"Content-Type": "application/json"}
            if api_key.startswith("ya29."):
                headers["Authorization"] = f"Bearer {api_key}"
            else:
                headers["x-goog-api-key"] = api_key
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                else:
                    err_msg = f"Gemini HTTP {res.status_code}: {res.text[:200]}"
                    logger.warning(f"[Gemini] Model {model_name} thất bại ({err_msg}), thử model kế tiếp...")
                    last_error = err_msg
                    # Nếu lỗi xác thực API Key hoặc Quota, ngắt lặp ngay để kích hoạt fallback quang học
                    if res.status_code in (401, 403) or (res.status_code == 400 and ("API_KEY" in res.text or "key not valid" in res.text)):
                        break
                    continue
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[Gemini] Lỗi kết nối model {model_name}: {e}")
            # Nếu là sự cố kết nối mạng/DNS, dừng lặp để fallback tức thì
            err_str = str(e).lower()
            if any(k in err_str for k in ["getaddrinfo", "connecterror", "network", "connection", "nodename"]):
                break

    logger.error(f"[Gemini] Tất cả model thất bại: {last_error}")
    return None


# ─── GỌI OPENAI REST API ────────────────────────────────────────────────────────

def _call_openai_api(
    prompt: str,
    system_instruction: str = "",
    api_key: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Optional[str]:
    """Gọi OpenAI Chat Completions API qua REST interface."""
    import httpx

    model_name = _get_env("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    url = "https://api.openai.com/v1/chat/completions"

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            res = client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
            )
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
            else:
                logger.error(f"[OpenAI] Lỗi HTTP {res.status_code}: {res.text[:300]}")
                return None
    except Exception as e:
        logger.error(f"[OpenAI] Ngoại lệ kết nối: {e}")
        return None


# ─── UNIFIED LLM COMPLETION ───────────────────────────────────────────────────

def call_llm(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Gửi prompt đến LLM khả dụng (Gemini hoặc OpenAI).
    Returns: (response_text, provider_name_used)
    """
    provider, api_key = get_active_provider()
    if not provider or not api_key:
        return None, None

    logger.info(f"[LLMService] Đang gọi {provider.upper()} API...")

    if provider == "gemini":
        text = _call_gemini_api(prompt, system_instruction, api_key, temperature, max_tokens)
    elif provider == "openai":
        text = _call_openai_api(prompt, system_instruction, api_key, temperature, max_tokens)
    else:
        text = None

    if text:
        return text, provider
    return None, None


# ─── BỘ SÁNG TÁC LỜI BÀI HÁT CAO CẤP (TRUE AI LYRICIST) ────────────────────────

def generate_lyrics_with_llm(
    topic: str,
    genre: str = "vpop",
    mood: str = "happy",
    vocal_gender: str = "female",
    language: str = "vi",
    structure_labels: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Sáng tác lời bài hát chuyên nghiệp bằng LLM:
    - Đúng cấu trúc âm nhạc: [Intro], [Verse 1], [Chorus], [Verse 2], [Bridge], [Outro]
    - Tối ưu cho AI hát rõ lời: câu ngắn 5-8 từ, có dấu phẩy ngắt hơi, vần điệu mượt mà
    - Nội dung mới lạ, giàu cảm xúc, không trùng lặp khuôn mẫu cũ.
    """
    provider, _ = get_active_provider()
    if not provider:
        return None

    system_instruction = (
        "Bạn là một Nhạc sĩ & Nhà sản xuất âm nhạc chuyên nghiệp (Master Songwriter & Lyricist) hàng đầu. "
        "Nhiệm vụ của bạn là sáng tác lời bài hát hoàn toàn mới, đầy cảm xúc, có chiều sâu nghệ thuật và hình ảnh thơ mộng. "
        "QUY TẮC BẮT BUỘC ĐỂ BÀI HÁT KHI ĐƯA VÀO AI HÁT ĐƯỢC RÕ LỜI VÀ TRÒN VÀNH RÕ CHỮ:\n"
        "1. Mỗi dòng hát chỉ dài từ 5 đến 8 từ (tối đa 40 ký tự), ngắt câu dứt khoát.\n"
        "2. Sử dụng dấu phẩy (,) ở giữa câu để ca sĩ AI lấy hơi và nhả chữ tự nhiên.\n"
        "3. Lời hát tiếng Việt phải tuân theo vần điệu (vần chân, vần lưng) và thanh điệu bằng trắc hài hòa.\n"
        "4. Bắt buộc sử dụng các thẻ phân đoạn chuẩn trong ngoặc vuông: [Intro], [Verse 1], [Chorus], [Verse 2], [Bridge], [Outro].\n"
        "5. Đầu ra BẮT BUỘC trả về đúng định dạng JSON chuẩn (không bọc trong markdown dư thừa nếu có thể): "
        "{\"title\": \"Tên bài hát\", \"theme\": \"chủ đề\", \"lyrics\": \"nội dung bài hát đầy đủ\", \"style_tags\": \"gợi ý phong cách nhạc tiếng Anh\"}"
    )

    lang_desc = {
        "vi": "Tiếng Việt (V-Pop trữ tình hoặc hiện đại)",
        "en": "English (Pop/Ballad)",
        "ko": "Korean (K-Pop)",
        "ja": "Japanese (J-Pop/Anime OST)",
        "zh": "Chinese Mandarin (C-Pop)",
    }.get(language, "Tiếng Việt")

    vocal_desc = {
        "female": "Giọng Nữ trong trẻo, truyền cảm",
        "male": "Giọng Nam trầm ấm, da diết",
        "duet": "Song ca Nam Nữ hòa quyện",
    }.get(vocal_gender, "Giọng hát biểu cảm")

    prompt = f"""Hãy sáng tác một bài hát hoàn toàn mới theo yêu cầu sau:
- Chủ đề / Câu chuyện: "{topic}"
- Thể loại âm nhạc: {genre.upper()}
- Tâm trạng / Cảm xúc: {mood}
- Ngôn ngữ: {lang_desc}
- Đối tượng thể hiện: {vocal_desc}

Yêu cầu chi tiết cấu trúc:
[Intro] (khoảng 1-2 dòng gợi mở tâm trạng)
[Verse 1] (4 dòng ngắn, kể câu chuyện)
[Chorus] (4 dòng điệp khúc đắt giá, giai điệu bắt tai, dễ nhớ)
[Verse 2] (4 dòng phát triển cảm xúc)
[Chorus] (lặp lại điệp khúc)
[Bridge] (2-3 dòng cao trào, chuyển đổi cảm xúc)
[Chorus] (điệp khúc bùng nổ lần cuối)
[Outro] (1-2 dòng kết bài êm dịu)

Hãy trả về định dạng JSON thuần túy:
{{
  "title": "Tiêu đề bài hát thật hay và ý nghĩa",
  "theme": "{mood}",
  "lyrics": "Toàn bộ lời bài hát với các tag [Verse], [Chorus]...",
  "style_tags": "Vietnamese pop ballad, acoustic piano, clear vocals, studio recording"
}}"""

    raw_response, used_provider = call_llm(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.75,
        max_tokens=2048,
    )

    if not raw_response:
        return None

    # Parse JSON từ response của LLM
    try:
        clean_text = raw_response.strip()
        # Loại bỏ markdown code blocks nếu model trả về ```json ... ```
        if "```" in clean_text:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
            if match:
                clean_text = match.group(1)
            else:
                clean_text = clean_text.replace("```json", "").replace("```", "").strip()

        data = json.loads(clean_text)
        title = data.get("title", topic[:40].title())
        lyrics = data.get("lyrics", "")
        style_tags = data.get("style_tags", f"{genre}, emotional, melodic, studio quality")
        theme = data.get("theme", mood)

        if lyrics and len(lyrics.strip()) > 50:
            logger.info(f"[LLMService] Đã tạo lời thành công bằng {used_provider.upper()}: '{title}'")
            return {
                "title": title,
                "lyrics": lyrics.strip(),
                "style_tags": style_tags,
                "theme": theme,
                "provider": used_provider,
            }
    except Exception as e:
        logger.warning(f"[LLMService] Không parse được JSON trực tiếp từ LLM ({e}), trích xuất text...")
        # Nếu model trả về plain text thay vì JSON
        lines = raw_response.strip().split("\n")
        title = topic[:40].title()
        lyrics_lines = []
        for line in lines:
            if line.lower().startswith("tiêu đề:") or line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip("'")
            else:
                lyrics_lines.append(line)
        lyrics = "\n".join(lyrics_lines).strip()
        if len(lyrics) > 50:
            return {
                "title": title,
                "lyrics": lyrics,
                "style_tags": f"{genre}, emotional, studio quality",
                "theme": mood,
                "provider": used_provider,
            }

    return None


# ─── BỘ CHATBOT TƯ VẤN ÂM NHẠC THẬT SỰ (TRUE AI MUSIC PRODUCER) ────────────────

def chat_with_music_llm(
    message: str,
    songs_pool: Optional[List[Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Trò chuyện với AI Chatbot âm nhạc chuyên nghiệp:
    - Thấu hiểu tâm tư, cảm xúc của người nghe nhạc
    - Tư vấn kiến thức hòa âm, phối khí, ca từ, thể loại bài hát
    - Gợi ý bài hát thực tế có trong thư viện của hệ thống
    - Trích xuất Mood và Thể loại để kích hoạt nút 'Áp dụng gợi ý' trên giao diện.
    """
    provider, _ = get_active_provider()
    if not provider:
        return None

    # Rút trích danh sách bài hát trong DB để LLM biết đường giới thiệu
    catalog_context = ""
    song_map = {}
    if songs_pool:
        sample_songs = songs_pool[:25]
        song_lines = []
        for s in sample_songs:
            artist_name = getattr(s, "artist", None)
            artist_str = getattr(artist_name, "username", "Sonavia AI") if artist_name else "Sonavia AI"
            song_lines.append(f"- ID:{s.id} | \"{s.title}\" | Nghệ sĩ: {artist_str} | Thể loại: {s.genre} | Mood: {s.mood}")
            song_map[s.id] = {
                "id": s.id,
                "title": s.title,
                "artist": artist_str,
            }
        catalog_context = "DANH SÁCH BÀI HÁT HIỆN CÓ TRONG HỆ THỐNG:\n" + "\n".join(song_lines)

    system_instruction = (
        "Bạn là Sonavia AI — Chuyên gia tư vấn âm nhạc và Nhà sản xuất âm nhạc thông minh của nền tảng AI Music Social.\n"
        "Phong cách của bạn: Thân thiện, ấm áp, am hiểu sâu sắc về cảm xúc con người và mọi thể loại âm nhạc "
        "(V-Pop, Indie Việt, Ballad, Rap Việt, EDM, Lo-fi, K-Pop, Jazz...). Bạn sử dụng ngôn ngữ tiếng Việt tự nhiên, trẻ trung.\n\n"
        "NHIỆM VỤ:\n"
        "1. Trò chuyện, đồng cảm hoặc giải đáp câu hỏi của người dùng về âm nhạc hoặc cảm xúc.\n"
        "2. Nếu người dùng bộc lộ cảm xúc hoặc muốn nghe/tạo nhạc: Hãy xác định rõ Tâm trạng (mood) và Thể loại (genres) phù hợp.\n"
        "3. Nếu có bài hát trong danh sách hệ thống phù hợp, hãy đề xuất 1-3 bài hát đó (ghi rõ ID bài hát).\n"
        "4. BẮT BUỘC trả về kết quả theo cấu trúc JSON sau:\n"
        "{\n"
        "  \"message\": \"Nội dung phản hồi trò chuyện thân thiện và giàu cảm xúc với người dùng (dùng emoji sinh động)\",\n"
        "  \"mood\": \"sad | happy | romantic | calm | energetic | melancholic | angry | null\",\n"
        "  \"recommended_genres\": [\"vpop\", \"ballad\"...],\n"
        "  \"recommended_song_ids\": [1, 2...]\n"
        "}"
    )

    user_prompt = f"Người dùng nhắn: \"{message}\"\n\n{catalog_context}"

    raw_response, used_provider = call_llm(
        prompt=user_prompt,
        system_instruction=system_instruction,
        temperature=0.7,
        max_tokens=1024,
    )

    if not raw_response:
        return None

    try:
        clean_text = raw_response.strip()
        if "```" in clean_text:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
            if match:
                clean_text = match.group(1)
            else:
                clean_text = clean_text.replace("```json", "").replace("```", "").strip()

        data = json.loads(clean_text)
        reply_message = data.get("message", "").strip()
        detected_mood = data.get("mood")
        if detected_mood and str(detected_mood).lower() in ("null", "none"):
            detected_mood = None

        genres = data.get("recommended_genres", [])
        if not isinstance(genres, list):
            genres = [str(genres)]

        rec_ids = data.get("recommended_song_ids", [])
        matched_songs = []
        for sid in rec_ids:
            try:
                sid_int = int(sid)
                if sid_int in song_map:
                    matched_songs.append(song_map[sid_int])
            except (ValueError, TypeError):
                pass

        # Nếu không match được ID nào nhưng có mood, lọc nhẹ từ pool
        if not matched_songs and detected_mood and songs_pool:
            mood_matches = [s for s in songs_pool if getattr(s, "mood", None) == detected_mood][:3]
            for s in mood_matches:
                artist_name = getattr(s, "artist", None)
                artist_str = getattr(artist_name, "username", "Sonavia AI") if artist_name else "Sonavia AI"
                matched_songs.append({"id": s.id, "title": s.title, "artist": artist_str})

        return {
            "message": reply_message,
            "reply": reply_message,
            "mood": detected_mood,
            "recommended_genres": genres,
            "songs": matched_songs,
            "provider": used_provider,
        }
    except Exception as e:
        logger.warning(f"[LLMService] Chatbot JSON parse error: {e}")
        return {
            "message": raw_response.strip(),
            "reply": raw_response.strip(),
            "mood": None,
            "recommended_genres": [],
            "songs": [],
            "provider": used_provider,
        }


# ─── BỘ TỐI ƯU HÓA PROMPT BẰNG AI (MAGIC PROMPT ENHANCER) ─────────────────────

def enhance_prompt_with_llm(
    user_prompt: str,
    language: str = "auto",
) -> Dict[str, Any]:
    """
    Tối ưu hóa và làm giàu prompt ngắn của người dùng thành Prompt âm nhạc chuyên nghiệp:
    - Bổ sung nhạc cụ, không gian âm thanh, phong cách giọng hát, nhịp điệu
    - Trả về: enhanced_prompt, style_tags, suggested_title, genre, mood
    - Tự động fallback thông minh nếu chưa có API key.
    """
    clean_p = user_prompt.strip()
    if not clean_p:
        clean_p = "bài hát về tình yêu cuộc sống"

    provider, _ = get_active_provider()
    if provider:
        system_instruction = (
            "Bạn là Master Music Prompt Engineer cho các mô hình AI âm nhạc đỉnh cao (như Suno AI, Udio, ACE-Step).\n"
            "Nhiệm vụ: Người dùng nhập vào một ý tưởng hoặc mô tả bài hát ngắn. Hãy phân tích và làm giàu nó thành một "
            "Prompt âm nhạc chuyên nghiệp, giàu hình ảnh, hoàn hảo để AI sinh ra tác phẩm xuất sắc nhất.\n\n"
            "YÊU CẦU BẮT BUỘC:\n"
            "1. Giữ trọn vẹn chủ đề và cảm xúc gốc mà người dùng muốn truyền tải.\n"
            "2. Bổ sung cụ thể: Thể loại (genre/subgenre), Nhạc cụ chủ đạo (piano, acoustic guitar, strings, 808 bass...), "
            "Tâm trạng & không khí (mood, atmosphere), Phong cách thanh nhạc (vocal tone, warm, emotional, crisp...), "
            "Không gian phối khí (studio recording, clean mix, radio-friendly).\n"
            "3. BẮT BUỘC trả về đúng định dạng JSON chuẩn:\n"
            "{\n"
            "  \"enhanced_prompt\": \"Đoạn mô tả chi tiết, mượt mà và truyền cảm hứng (bằng tiếng Việt)\",\n"
            "  \"style_tags\": \"Các thẻ từ khóa tiếng Anh chuẩn cho AI sinh nhạc, ví dụ: 'vpop ballad, grand piano, warm acoustic guitar, sweet clear female vocals, emotional, studio master'\",\n"
            "  \"suggested_title\": \"Tiêu đề bài hát gợi ý hấp dẫn\",\n"
            "  \"genre\": \"vpop | pop | ballad | lofi | rock | edm | rnb | jazz | indie\",\n"
            "  \"mood\": \"sad | romantic | happy | calm | energetic | melancholic\"\n"
            "}"
        )

        user_input = f"Hãy tối ưu và làm giàu prompt âm nhạc sau: \"{clean_p}\""
        raw_res, used_provider = call_llm(
            prompt=user_input,
            system_instruction=system_instruction,
            temperature=0.75,
            max_tokens=1024,
        )

        if raw_res:
            try:
                txt = raw_res.strip()
                if "```" in txt:
                    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, re.DOTALL)
                    if m:
                        txt = m.group(1)
                    else:
                        txt = txt.replace("```json", "").replace("```", "").strip()

                data = json.loads(txt)
                enhanced = data.get("enhanced_prompt", "").strip()
                style_tags = data.get("style_tags", "").strip()
                title = data.get("suggested_title", clean_p[:40].title()).strip()
                genre = data.get("genre", "vpop").strip().lower()
                mood = data.get("mood", "happy").strip().lower()

                if enhanced:
                    logger.info(f"[LLMService] Đã tối ưu hóa prompt thành công bằng {used_provider.upper()}")
                    return {
                        "success": True,
                        "original_prompt": clean_p,
                        "enhanced_prompt": enhanced,
                        "style_tags": style_tags,
                        "suggested_title": title,
                        "genre": genre,
                        "mood": mood,
                        "provider": used_provider,
                    }
            except Exception as parse_err:
                logger.warning(f"[LLMService] Parse enhanced prompt JSON error: {parse_err}")

    # Fallback thông minh nếu không có LLM
    from .prompt_analyzer import PromptAnalyzerService
    config = PromptAnalyzerService.analyze(prompt=clean_p)
    g = config.get("genre", "pop")
    m = config.get("mood", "happy")
    suggested = f"{clean_p.capitalize()}, giai điệu truyền cảm, hòa âm piano và guitar mộc mạc, giọng hát ấm áp rõ chữ, chất lượng phòng thu chuẩn."
    tags = f"{g}, {m}, acoustic guitar, melodic piano, clean vocal, studio master, 320kbps"

    return {
        "success": True,
        "original_prompt": clean_p,
        "enhanced_prompt": suggested,
        "style_tags": tags,
        "suggested_title": clean_p[:35].title(),
        "genre": g,
        "mood": m,
        "provider": "fallback",
    }


def _parse_json_from_llm(raw_text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON an toàn từ phản hồi LLM, cho phép ký tự điều khiển/xuống dòng bên trong chuỗi."""
    if not raw_text:
        return None
    clean_text = raw_text.strip()
    if "```" in clean_text:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
        if m:
            clean_text = m.group(1).strip()
        else:
            clean_text = clean_text.replace("```json", "").replace("```", "").strip()

    # Thử json.loads tiêu chuẩn với strict=False
    try:
        return json.loads(clean_text, strict=False)
    except Exception:
        pass

    # Thử sửa trường hợp chuỗi bị cắt cụt do giới hạn token
    try:
        if clean_text.startswith("{") and not clean_text.rstrip().endswith("}"):
            repaired = clean_text + '"}'
            return json.loads(repaired, strict=False)
    except Exception:
        pass

    # Thử trích xuất các trường cơ bản bằng regex nếu JSON bị lỗi cú pháp
    try:
        data = {}
        for key in ["title", "atmosphere", "genre", "genre_name", "mood", "mood_name", "bpm", "key", "vocal", "prompt", "lyrics"]:
            m_val = re.search(rf'"{key}"\s*:\s*"([^"]+)"', clean_text, re.DOTALL)
            if m_val:
                data[key] = m_val.group(1).strip()
        if not data.get("lyrics"):
            m_lyr = re.search(r'"lyrics"\s*:\s*"(.*)', clean_text, re.DOTALL)
            if m_lyr:
                data["lyrics"] = m_lyr.group(1).rsplit('"', 1)[0].strip()
        if data.get("title") or data.get("lyrics"):
            return data
    except Exception:
        pass

    return None


# ─── BỘ PHÂN TÍCH THỊ GIÁC ĐA PHƯƠNG THỨC (TRUE MULTIMODAL VISION AI) ─────────

def analyze_image_with_vision_llm(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    language: str = "auto",
) -> Optional[Dict[str, Any]]:
    """
    Phân tích trực tiếp hình ảnh bằng Multimodal Vision AI (Google Gemini):
    - 'Nhìn' thấu các chi tiết thật trong ảnh (cảnh sắc, con người, cảm xúc, ánh sáng, màu sắc).
    - Chuyển hóa thị giác thành ý tưởng âm nhạc độc bản: Title, Atmosphere, Genre, Mood, BPM, Key, Prompt.
    - Sáng tác lời bài hát (hỗ trợ đa ngôn ngữ: vi, ko, ja, zh, en) chuẩn phòng thu gắn liền với linh hồn bức ảnh.
    """
    import base64
    import httpx

    provider, api_key = get_active_provider()
    if not provider or not api_key:
        return None

    b64_image = base64.b64encode(image_bytes).decode("ascii")

    lang_choice = (language or "auto").strip().lower()
    if lang_choice == "ko":
        title_guide = "Tên bài hát thật nghệ thuật bằng tiếng Hàn (Hangul 한국어, ví dụ: 별빛 아래서, 너의 계절)"
        lyrics_guide = "Lời bài hát viết 100% bằng tiếng Hàn (Hangul 한국어 - chuẩn K-Pop) có cấu trúc [Intro], [Verse 1], [Chorus], [Verse 2], [Bridge], [Outro]. Câu từ ngắn gọn, giàu hình ảnh ăn khớp với bức ảnh."
        prompt_guide = "Mô tả tiếng Anh phối khí K-Pop chi tiết cho AI sinh nhạc (ví dụ: Modern K-pop melodic dance ballad, catchy synth, warm piano, Korean female lead vocal, crisp diction, studio master)"
    elif lang_choice == "ja":
        title_guide = "Tên bài hát thật nghệ thuật bằng tiếng Nhật (Kanji/Kana 日本語, ví dụ: 桜の記憶, 青い空の彼方)"
        lyrics_guide = "Lời bài hát viết 100% bằng tiếng Nhật (Kanji & Kana 日本語 - chuẩn J-Pop/Anime) có cấu trúc [Intro], [Verse 1], [Chorus], [Verse 2], [Bridge], [Outro]. Mang đậm phong cách J-Pop/Anime ăn khớp với bức ảnh."
        prompt_guide = "Mô tả tiếng Anh phối khí J-Pop chi tiết cho AI sinh nhạc (ví dụ: Emotional J-pop anime ballad, strings, grand piano, Japanese female lead vocal, clear pronunciation, studio recording)"
    elif lang_choice == "zh":
        title_guide = "Tên bài hát thật nghệ thuật bằng tiếng Trung (Chữ Hán 中文, ví dụ: 晴天下的微风, 遥远的星河)"
        lyrics_guide = "Lời bài hát viết 100% bằng tiếng Trung (Chữ Hán 中文 - chuẩn C-Pop) có cấu trúc [Intro], [Verse 1], [Chorus], [Verse 2], [Bridge], [Outro]. Lời ca trữ tình, thanh thoát phù hợp với hình ảnh."
        prompt_guide = "Mô tả tiếng Anh phối khí C-Pop chi tiết cho AI sinh nhạc (ví dụ: Chinese pop ballad, erhu touches, grand piano, emotional Mandarin female lead vocal, studio recording)"
    elif lang_choice == "en":
        title_guide = "Artistic and expressive song title in English (e.g. Starlight Whispers, Ocean Horizon)"
        lyrics_guide = "Full song lyrics written in English (clean Pop / Indie / R&B lyrics) with [Intro], [Verse 1], [Chorus], [Verse 2], [Bridge], [Outro]. Poetic and deeply inspired by the visual elements of the image."
        prompt_guide = "Studio production prompt in English (e.g. Modern pop ballad, ambient synthesizer, warm acoustic guitar, emotional female vocals, upfront mix)"
    else:
        title_guide = "Tên bài hát thật nghệ thuật và giàu cảm xúc (tiếng Việt)"
        lyrics_guide = "Lời bài hát tiếng Việt hoàn chỉnh có [Intro], [Verse 1], [Chorus], [Verse 2], [Bridge], [Outro]. Câu hát ngắn 5-8 từ, có dấu phẩy ngắt hơi, mang nội dung gắn liền trực tiếp với những gì bạn thấy trong ảnh."
        prompt_guide = "Mô tả tiếng Anh phối khí phòng thu chi tiết cho AI sinh nhạc (ví dụ: Vietnamese acoustic pop ballad, grand piano, warm guitar, clear female vocals, emotional, studio recording)"

    prompt = (
        "Bạn là Nhà sản xuất âm nhạc & Thi sĩ tài hoa hàng đầu của Sonavia AI Studio.\n"
        "Hãy quan sát kỹ lưỡng bức ảnh này (đối tượng, con người, cảnh quan, ánh sáng, tông màu, cảm xúc toát ra).\n"
        "Hãy chuyển hóa linh hồn bức ảnh thành một tác phẩm âm nhạc hoàn chỉnh và trả về đúng định dạng JSON chuẩn sau:\n"
        "{\n"
        f"  \"title\": \"{title_guide}\",\n"
        "  \"atmosphere\": \"1-2 câu miêu tả không gian, cảm xúc và linh hồn bức ảnh bằng tiếng Việt sinh động\",\n"
        "  \"genre\": \"vpop | pop | lofi | ballad | acoustic | rnb | rock | electronic | jazz | folk | kpop\",\n"
        "  \"genre_name\": \"Tên thể loại hiển thị (ví dụ: V-Pop Ballad, Lo-fi Chill, Acoustic Folk...)\",\n"
        "  \"mood\": \"happy | sad | calm | energetic | romantic | melancholic | uplifting\",\n"
        "  \"mood_name\": \"Tên tâm trạng (ví dụ: Lãng mạn & Ấm áp, Bình yên & Thư thái...)\",\n"
        "  \"bpm\": 85,\n"
        "  \"key\": \"C Major\",\n"
        "  \"vocal\": \"female | male | duet | instrumental\",\n"
        "  \"visual_tags\": [\"#Tag1\", \"#Tag2\", \"#Tag3\", \"#Tag4\"],\n"
        f"  \"prompt\": \"{prompt_guide}\",\n"
        f"  \"lyrics\": \"{lyrics_guide}\"\n"
        "}"
    )

    if provider == "gemini":
        preferred_model = _get_env("GEMINI_MODEL", "")
        models_to_try = [preferred_model] if preferred_model else []
        for m in GEMINI_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_image,
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.75,
                "maxOutputTokens": 4096,
            }
        }

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            try:
                headers = {"Content-Type": "application/json"}
                if api_key.startswith("ya29."):
                    headers["Authorization"] = f"Bearer {api_key}"
                else:
                    headers["x-goog-api-key"] = api_key
                with httpx.Client(timeout=20.0) as client:
                    res = client.post(url, headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                raw_text = parts[0].get("text", "").strip()
                                result = _parse_json_from_llm(raw_text)
                                if result and (result.get("title") or result.get("lyrics")):
                                    logger.info(f"[VisionLLM] Đã phân tích ảnh thành công bằng Gemini ({model_name}): '{result.get('title')}'")
                                    return result
                    else:
                        logger.warning(f"[VisionLLM] Gemini {model_name} trả về HTTP {res.status_code}: {res.text[:150]}, thử model khác...")
                        if res.status_code in (401, 403) or (res.status_code == 400 and ("API_KEY" in res.text or "key not valid" in res.text)):
                            break
                        continue
            except Exception as e:
                logger.warning(f"[VisionLLM] Lỗi gọi Gemini {model_name}: {e}")
                err_str = str(e).lower()
                if any(k in err_str for k in ["getaddrinfo", "connecterror", "network", "connection", "nodename"]):
                    break

    elif provider == "openai":
        openai_model = _get_env("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        target_model = openai_model if "gpt-4" in openai_model else "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": target_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.75,
            "max_tokens": 4096,
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                    },
                    json=payload,
                )
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        raw_text = choices[0].get("message", {}).get("content", "").strip()
                        result = _parse_json_from_llm(raw_text)
                        if result and (result.get("title") or result.get("lyrics")):
                            logger.info(f"[VisionLLM] Đã phân tích ảnh thành công bằng OpenAI: '{result.get('title')}'")
                            return result
                else:
                    logger.warning(f"[VisionLLM] OpenAI Vision lỗi HTTP {res.status_code}: {res.text[:150]}")
        except Exception as e:
            logger.warning(f"[VisionLLM] Lỗi gọi OpenAI Vision: {e}")

    return None


# ─── NEURAL PROMPT REASONING (TRUE AI PROMPT ANALYZER) ──────────────────────────

def analyze_prompt_with_llm(
    prompt: str,
    user_language: str = "auto",
    user_vocal: str = "auto",
    is_instrumental: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Phân tích ngữ nghĩa prompt âm nhạc chuyên sâu bằng Neural LLM Reasoning:
    - Hiểu sâu sắc ẩn dụ, cảm xúc, không gian, bối cảnh văn hóa.
    - Suy luận chuẩn xác BPM, Key, Genre, Mood, Instruments và xây dựng studio caption.
    """
    if not prompt or not prompt.strip():
        return None

    system_instruction = (
        "Bạn là Chuyên gia Âm nhạc & Nhà sản xuất Âm thanh AI cấp cao (Senior AI Music Producer). "
        "Nhiệm vụ của bạn là phân tích prompt của người dùng để suy luận toàn bộ thông số âm nhạc tối ưu. "
        "Trả về DUY NHẤT một khối JSON hợp lệ (không kèm markdown thừa) với các trường:\n"
        "{\n"
        '  "language": "vi"|"ko"|"ja"|"zh"|"en",\n'
        '  "genre": "vpop"|"ballad"|"rnb"|"pop"|"kpop"|"jpop"|"cpop"|"lofi"|"rock"|"edm"|"acoustic"|"jazz",\n'
        '  "genre_name": "Tên thể loại hiển thị (ví dụ: V-Pop Ballad, K-Pop R&B)",\n'
        '  "subgenre": "Tiểu thể loại (ví dụ: Acoustic Ballad)",\n'
        '  "mood": "happy"|"sad"|"romantic"|"energetic"|"calm"|"melancholic"|"uplifting",\n'
        '  "mood_name": "Tên cảm xúc tiếng Việt (ví dụ: Da diết & Lãng mạn)",\n'
        '  "vocal_gender": "female"|"male"|"duet"|"instrumental",\n'
        '  "vocal_desc": "Mô tả giọng hát chi tiết bằng tiếng Anh",\n'
        '  "bpm": Số nguyên từ 60 đến 175,\n'
        '  "key": "Tông nhạc (ví dụ: C Major, A Minor, E Minor, F# Major)",\n'
        '  "instruments": ["nhạc cụ 1", "nhạc cụ 2", "nhạc cụ 3", "nhạc cụ 4"],\n'
        '  "theme": "love"|"sad"|"chill"|"energy"|"nostalgia"|"summer"|"breakup"|"youth",\n'
        '  "production_style": "Mô tả chất lượng sản xuất phòng thu (ví dụ: warm intimate acoustic, pristine modern pop mix)",\n'
        '  "model_prompt": "Caption tiếng Anh studio chuẩn cho mô hình sinh nhạc ACE-Step"\n'
        "}"
    )

    user_req = (
        f"Prompt người dùng: \"{prompt.strip()}\"\n"
        f"Tùy chọn ngôn ngữ người dùng: {user_language}\n"
        f"Tùy chọn giọng hát người dùng: {user_vocal}\n"
        f"Yêu cầu không lời (Instrumental): {is_instrumental}\n"
    )

    try:
        raw_output, _ = call_llm(
            prompt=user_req,
            system_instruction=system_instruction,
            temperature=0.3,
            max_tokens=1024,
        )
        if not raw_output:
            return None

        clean_text = raw_output.strip()
        if "```" in clean_text:
            m_json = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
            if m_json:
                clean_text = m_json.group(1)
            else:
                clean_text = clean_text.replace("```json", "").replace("```", "").strip()

        data = json.loads(clean_text)
        if data.get("genre") and data.get("bpm"):
            logger.info(f"[PromptAnalyzer AI] Đã phân tích prompt thành công qua Neural LLM: {data.get('genre_name')} | {data.get('bpm')} BPM | {data.get('key')}")
            return data
    except Exception as e:
        logger.warning(f"[PromptAnalyzer AI] Phân tích bằng LLM gián đoạn ({e}), tự động fallback sang Rule-based.")

    return None


# ─── NEURAL SEMANTIC EMBEDDING ENGINE (TRUE AI VECTOR RECOMMENDER) ──────────────

_EMBEDDING_CACHE: Dict[str, Any] = {}
_LAST_EMBED_NETWORK_FAIL: float = 0.0

def get_neural_embedding(text: str) -> Optional[Any]:
    """
    Sinh vector nhúng ngữ nghĩa chiều cao (Dense Neural Latent Vector 3072-dim)
    từ mô hình Gemini Neural Embedding để đo lường độ tương đồng ngữ âm & ý niệm giữa các bài hát.
    """
    import numpy as np
    import time
    global _LAST_EMBED_NETWORK_FAIL

    if not text or not text.strip():
        return None

    clean_text = text.strip()[:1000]
    if clean_text in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[clean_text]

    provider, api_key = get_active_provider()
    # Circuit breaker: chỉ gọi Gemini embedding nếu api_key hợp lệ và không bị network failure gần đây
    is_valid_gemini_key = bool(api_key and (api_key.startswith("AIzaSy") or api_key.startswith("ya29.")))
    if provider == "gemini" and is_valid_gemini_key and (time.time() - _LAST_EMBED_NETWORK_FAIL > 60.0):
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
        payload = {
            "model": "models/gemini-embedding-001",
            "content": {
                "parts": [{"text": clean_text}]
            }
        }
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    vals = res.json().get("embedding", {}).get("values", [])
                    if vals:
                        raw = np.array(vals, dtype=np.float32)
                        # Uniform 3072-dimension normalization across all embedding pipelines
                        if len(raw) == 3072:
                            vec = raw
                        elif len(raw) == 768:
                            expanded = np.zeros(3072, dtype=np.float32)
                            expanded[0:768] = raw
                            expanded[768:1536] = np.roll(raw, 192)
                            expanded[1536:2304] = np.roll(raw, 384)
                            expanded[2304:3072] = np.roll(raw, 576)
                            vec = expanded
                        else:
                            vec = np.pad(raw, (0, max(0, 3072 - len(raw))))[:3072]
                        norm = np.linalg.norm(vec)
                        if norm > 1e-6:
                            vec = vec / norm
                        _EMBEDDING_CACHE[clean_text] = vec
                        return vec
        except Exception as e:
            _LAST_EMBED_NETWORK_FAIL = time.time()
            logger.debug(f"[NeuralEmbedding] Gemini embed API call warning: {e}")

    # Fallback nội bộ: High-dimensional semantic projection hashing (3072-dim)
    import hashlib
    vec = np.zeros(3072, dtype=np.float32)
    words = clean_text.lower().split()
    for w in words:
        h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
        idx = h % 3072
        sign = 1.0 if (h % 2 == 0) else -1.0
        vec[idx] += sign

    norm = np.linalg.norm(vec)
    if norm > 1e-6:
        vec = vec / norm
    _EMBEDDING_CACHE[clean_text] = vec
    return vec


# ─── NEURAL SYMBOLIC MUSIC COMPOSER (GENERATIVE AI COMPOSER) ───────────────────

def compose_symbolic_music_with_llm(
    genre: str = "pop",
    mood: str = "happy",
    prompt: str = "",
    num_bars: int = 16,
) -> Optional[Dict[str, Any]]:
    """
    Sáng tác cấu trúc hợp âm và giai điệu đa bè (Polyphonic Chords, Melody, Bass)
    bằng Generative AI Neural Symbolic Music reasoning.
    """
    system_instruction = (
        "Bạn là Bậc thầy Nhạc sĩ AI (Master Generative Music Composer). "
        "Nhiệm vụ của bạn là sáng tác một bản hòa âm đa bè hoàn chỉnh (Chords, Melody, Bass) "
        "với nhạc lý tinh tế (hợp âm mở rộng 7th, 9th, sus4, voice leading dẫn nốt mượt mà). "
        "Trả về DUY NHẤT một khối JSON (không markdown thừa) theo cấu trúc:\n"
        "{\n"
        '  "title": "Tên khúc nhạc",\n'
        '  "bpm": 80-140,\n'
        '  "key": "Tông nhạc (ví dụ: C Major, A Minor)",\n'
        '  "chords": [\n'
        '    {"root": "C", "notes": [48, 52, 55, 59], "beat": 0.0, "duration": 4.0},\n'
        '    {"root": "Am", "notes": [45, 48, 52, 55], "beat": 4.0, "duration": 4.0}\n'
        '  ],\n'
        '  "melody": [\n'
        '    {"pitch": 72, "beat": 0.0, "duration": 1.0, "velocity": 90},\n'
        '    {"pitch": 74, "beat": 1.0, "duration": 1.0, "velocity": 85}\n'
        '  ],\n'
        '  "bass": [\n'
        '    {"pitch": 36, "beat": 0.0, "duration": 4.0, "velocity": 95},\n'
        '    {"pitch": 33, "beat": 4.0, "duration": 4.0, "velocity": 95}\n'
        '  ]\n'
        "}\n"
        "Lưu ý: pitch và notes là số nguyên MIDI note (48=C3, 60=C4, 72=C5). duration và beat tính theo nhịp phách (beat)."
    )

    user_req = f"Sáng tác tác phẩm nhạc thể loại {genre}, tâm trạng {mood}, chủ đề: \"{prompt or 'Giai điệu cảm xúc'}\", độ dài {num_bars} ô nhịp."

    try:
        raw_output, _ = call_llm(
            prompt=user_req,
            system_instruction=system_instruction,
            temperature=0.6,
            max_tokens=2048,
        )
        if not raw_output:
            return None

        clean_text = raw_output.strip()
        if "```" in clean_text:
            m_json = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
            if m_json:
                clean_text = m_json.group(1)
            else:
                clean_text = clean_text.replace("```json", "").replace("```", "").strip()

        data = json.loads(clean_text)
        if data.get("chords") and data.get("melody"):
            logger.info(f"[NeuralComposer AI] Đã sáng tác nhạc thành công qua LLM: {data.get('title')} ({len(data['chords'])} chords, {len(data['melody'])} melody notes)")
            return data
    except Exception as e:
        logger.warning(f"[NeuralComposer AI] Sáng tác LLM gián đoạn ({e}), fallback sang thuật toán nhạc lý.")

    return None



