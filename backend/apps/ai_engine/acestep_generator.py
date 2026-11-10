"""
ACE-Step Music Generator
========================
Dùng ACE-Step HF Space (gradio_client) để tạo nhạc có giọng hát thật.
Tối ưu hóa:
- Phân định rõ ràng giọng Nam / Nữ, xóa sạch xung đột từ khóa
- guidance_scale_lyric = 2.0 để hát to, tròn vành rõ chữ
- QUALITY_PRESETS: FAST / BALANCED / HIGH
- Caption Expansion Layer tích hợp qua caption_builder
- Auto-duration theo genre nếu user không chỉ định
- Vocal dynamics hints embedded trong caption
"""

import os
import re
import time
import logging
import threading

logger = logging.getLogger(__name__)

_client = None
_client_lock = threading.Lock()

GENRE_TAGS = {
    "vpop":       "melodic pop, asian pop ballad, piano, acoustic guitar, emotional, modern production",
    "kpop":       "kpop, Korean pop, synthesizer, upbeat, catchy, modern",
    "pop":        "pop, catchy melody, modern production, radio-friendly",
    "rock":       "rock, electric guitar, drums, energetic, powerful",
    "jazz":       "jazz, saxophone, piano, smooth, improvisation, night",
    "classical":  "classical, orchestral, strings, piano, elegant, cinematic",
    "hip_hop":    "hip hop, trap, 808 bass, rhythmic, modern beat",
    "r&b":        "r&b, soul, smooth groove, bass guitar, emotional",
    "electronic": "electronic, EDM, synthesizer, bass drop, energetic",
    "lofi":       "lo-fi, chill, mellow, relaxing, rain, cozy, study",
    "blues":      "blues, guitar, soulful, minor key, raw emotion",
    "metal":      "metal, heavy guitar riffs, powerful drums, intense",
    "folk":       "folk, acoustic guitar, storytelling, warm, natural",
    "indie":      "indie, alternative, guitar-driven, atmospheric, unique",
    "country":    "country, acoustic guitar, storytelling, warm, heartfelt",
    "other":      "instrumental, melodic, atmospheric",
}

MOOD_TAGS = {
    "happy":       "happy, uplifting, joyful, bright, 120 BPM",
    "sad":         "sad, melancholic, emotional, minor key, 70 BPM",
    "energetic":   "energetic, powerful, fast-paced, driving, 140 BPM",
    "calm":        "calm, peaceful, relaxing, gentle, 80 BPM",
    "romantic":    "romantic, tender, warm, loving, 90 BPM",
    "angry":       "intense, aggressive, powerful, raw, 150 BPM",
    "melancholic": "nostalgic, wistful, bittersweet, reflective, 75 BPM",
    "uplifting":   "uplifting, inspiring, motivational, bright, 125 BPM",
}

INSTRUMENT_TAGS = {
    "piano":   "piano, keys, soft",
    "guitar":  "guitar, acoustic, warm",
    "strings": "strings, orchestra, violin, cello",
    "synth":   "synthesizer, electronic, modern",
    "full":    "full band, drums, bass, guitar, keys",
    "minimal": "minimalist, sparse, atmospheric",
}

# ── Quality Presets ────────────────────────────────────────────────────────────
# Tham số chuẩn phòng thu (Studio-calibrated):
# - Guidance Scale 8.0 - 9.0: Giữ nguyên dynamic range tuyến tính, triệt tiêu hoàn toàn méo tiếng, clipping và tiếng rè.
# - Guidance Scale Lyric 2.2 - 2.6: Tối ưu cho phát âm & thanh điệu tiếng Việt (ngang, huyền, sắc, hỏi, ngã, nặng), hát tròn vành rõ chữ.
# - Guidance Scale Text 0.6 - 1.0: Dẫn hướng conditioning bám sát mô tả vocal diction và phong cách.
# - Omega Scale 5.0 - 6.5: Giảm thiểu nhiễu nền (noise floor hiss) của bộ tạo APG.
QUALITY_PRESETS = {
    "fast": {
        "infer_step":              45,
        "guidance_scale":          12.0,
        "guidance_scale_text":     0.6,
        "guidance_scale_lyric":    2.2,
        "omega_scale":             8.0,
        "guidance_interval":       0.5,
        "guidance_interval_decay": 0.0,
        "min_guidance_scale":      3.0,
        "cfg_type":                "apg",
        "scheduler_type":          "euler",
        "description":             "Nhanh — mượt mà, trong trẻo, thích hợp test và preview",
    },
    "balanced": {
        "infer_step":              60,
        "guidance_scale":          14.5,
        "guidance_scale_text":     0.8,
        "guidance_scale_lyric":    2.5,
        "omega_scale":             10.0,
        "guidance_interval":       0.5,
        "guidance_interval_decay": 0.0,
        "min_guidance_scale":      3.0,
        "cfg_type":                "apg",
        "scheduler_type":          "euler",
        "description":             "Cân bằng — âm thanh chuẩn phòng thu, giọng hát rõ nét tự nhiên",
    },
    "high": {
        "infer_step":              75,
        "guidance_scale":          15.0,
        "guidance_scale_text":     1.0,
        "guidance_scale_lyric":    2.8,
        "omega_scale":             10.0,
        "guidance_interval":       0.5,
        "guidance_interval_decay": 0.0,
        "min_guidance_scale":      3.0,
        "cfg_type":                "apg",
        "scheduler_type":          "euler",
        "description":             "Chất lượng cao — phòng thu hi-fi chuyên nghiệp, độ nét chi tiết cao nhất",
    },
}

# ── Auto-duration theo genre (giây) ───────────────────────────────────────────
GENRE_AUTO_DURATION = {
    "vpop":     195,   # ~3:15 — V-Pop ballad trung bình
    "kpop":     210,   # ~3:30 — K-Pop chuẩn
    "jpop":     210,   # ~3:30 — J-Pop / Anime OP
    "cpop":     200,   # ~3:20 — C-Pop ballad
    "pop":      180,   # ~3:00 — Pop radio
    "ballad":   195,   # ~3:15 — Ballad chậm
    "lofi":     180,   # ~3:00 — Lo-fi loop
    "rnb":      195,   # ~3:15 — R&B groove
    "hip_hop":  180,   # ~3:00 — Hip-hop standard
    "rock":     210,   # ~3:30 — Rock anthem
    "edm":      210,   # ~3:30 — EDM with builds
    "acoustic":  180,  # ~3:00 — Acoustic intimate
    "jazz":     180,   # ~3:00 — Jazz standard
    "cinematic": 210,  # ~3:30 — Cinematic score
    "other":    180,
}


def build_tags(genre="pop", mood="happy", instruments="full", custom_prompt=""):
    if custom_prompt.strip():
        return custom_prompt.strip()
    parts = [GENRE_TAGS.get(genre, GENRE_TAGS["other"])]
    if mood and mood in MOOD_TAGS:
        parts.append(MOOD_TAGS[mood])
    if instruments and instruments in INSTRUMENT_TAGS:
        parts.append(INSTRUMENT_TAGS[instruments])
    parts.append("high quality, studio recording")
    return ", ".join(parts)


def postprocess_clean_audio(file_path: str, is_vietnamese: bool = True) -> None:
    """
    Hậu xử lý âm thanh chuyên nghiệp:
    - Áp dụng Vocal Clarity DSP Mastering: cắt rumble < 75Hz, boost 3.4kHz cho rõ tiếng hát tiếng Việt,
      tăng độ sáng 11kHz và chuẩn hóa âm lượng Peak -0.5 dBFS.
    """
    try:
        import os
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            logger.warning(f"Audio file is missing or empty: {file_path}")
            return

        from .audio_mastering import master_audio_file
        master_audio_file(file_path, is_vietnamese=is_vietnamese)
        logger.info(f"[Audio Mastering] Đã tối ưu độ nét giọng hát cho file: {file_path}")
    except Exception as e:
        logger.warning(f"Audio mastering skipped due to: {e}")


def detect_vietnamese(text: str) -> bool:
    """
    Phát hiện xem văn bản có chứa tiếng Việt có dấu không.
    """
    viet_chars = set(
        'đĐơƠăĂưƯâÂêÊôÔ'
        'áàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệ'
        'íìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ'
    )
    return any(c in viet_chars for c in text)


def clean_vietnamese_lyrics(text: str) -> str:
    """
    Chuẩn hóa lời bài hát cho ACE-Step:
    - BẢO TOÀN 100% TIẾNG VIỆT CÓ DẤU (Unicode NFC chuẩn), tuyệt đối không xóa dấu thanh!
    - Chuẩn hóa các tag cấu trúc [intro], [verse], [chorus], [bridge], [outro].
    - Loại bỏ ký tự nốt nhạc (♪, ♫, ♬, ♩), emoji, dấu thừa gây nhiễu tokenizer.
    - Loại bỏ dấu phẩy (,), dấu chấm hỏi (?), dấu chấm than (!) giữa các từ để tránh hiện tượng ngắt nhịp vấp từ.
    - Giữ trọn vẹn ngữ âm tiếng Việt để AI cất giọng hát đúng thanh điệu (sắc, huyền, hỏi, ngã, nặng).
    """
    import unicodedata

    if not text or not text.strip():
        return ""

    # Chuẩn hóa Unicode sang dạng NFC chuẩn để các ký tự có dấu không bị phân tách
    text = unicodedata.normalize('NFC', text.strip())

    # Loại bỏ nốt nhạc, emoji, ký tự trang trí không phải lời hát
    text = re.sub(r'[♪♫♬♩#*~_`^]+', '', text)
    text = re.sub(r'\.{2,}', ' ', text)

    out_lines = []
    for line in text.split('\n'):
        s = line.strip()
        if not s:
            if out_lines and out_lines[-1] != '':
                out_lines.append('')
            continue

        # Tag phân đoạn [verse], [chorus], v.v.
        tag_match = re.match(r'^\[([a-zA-Z0-9\s_-]+)\]$', s)
        if tag_match:
            if out_lines and out_lines[-1] != '':
                out_lines.append('')
            out_lines.append(f"[{tag_match.group(1).lower()}]")
            continue

        # Giữ lại chữ tiếng Việt có dấu, chữ cái Latin, số
        # Xóa dấu phẩy, chấm hỏi, chấm than ở giữa câu hát để giọng hát liền mạch, không bị ngắt/nuốt chữ
        clean = re.sub(
            r'[^\w\s\-\u00C0-\u024F\u1EA0-\u1EF9\uac00-\ud7af\u1100-\u11ff\u3130-\u318f\u3040-\u30ff\u4e00-\u9fff]',
            ' ',
            s
        )
        clean = re.sub(r'\s+', ' ', clean).strip()
        if clean:
            out_lines.append(clean)

    return '\n'.join(out_lines)


# Alias tương thích ngược để không bị lỗi import nếu nơi khác gọi
vietnamese_to_phonetic = clean_vietnamese_lyrics


def normalize_lyrics_for_acestep(lyrics: str) -> str:
    """
    Chuẩn hóa cấu trúc lời bài hát để ACE-Step hát rõ chữ, tròn vành rõ tiếng:
    - Giữ nguyên tiếng Việt có dấu 100%.
    - Cắt dòng vừa phải (≤ 55 ký tự / 4-8 từ) để người hát AI lấy hơi đúng nhịp, không bị nuốt chữ.
    - Đảm bảo [intro] là khoảng dạo nhạc cụ sạch (không nhồi lời hát vào intro).
    - Đảm bảo có các tag phân đoạn [verse], [chorus] chuẩn để AI phân bổ bố cục bài hát.
    """
    if not lyrics or not lyrics.strip():
        return ""

    cleaned = clean_vietnamese_lyrics(lyrics)
    raw_lines = [l.strip() for l in cleaned.split('\n')]
    formatted = []

    has_tags = bool(re.search(r'\[(verse|chorus|bridge|intro|outro)', cleaned, re.IGNORECASE))
    in_intro = False
    intro_lyrics_buffer = []

    for line in raw_lines:
        if not line:
            if formatted and formatted[-1] != '':
                formatted.append('')
            continue

        if line.startswith('[') and line.endswith(']'):
            tag_name = line.lower()
            if in_intro and intro_lyrics_buffer:
                # Nếu [intro] trước đó có chứa lời hát, dời vào verse tiếp theo
                formatted.append("[verse 1]" if "[verse" not in tag_name else tag_name)
                formatted.extend(intro_lyrics_buffer)
                intro_lyrics_buffer = []
                in_intro = False
                continue

            if formatted and formatted[-1] != '':
                formatted.append('')
            formatted.append(tag_name)
            in_intro = ("[intro]" in tag_name)
            continue

        if in_intro:
            # Lời hát nằm dưới tag [intro] -> lưu lại để đưa vào Verse 1, giữ intro chỉ dạo nhạc
            intro_lyrics_buffer.append(line)
            continue

        # Ngắt câu theo nhịp thơ 4 - 8 từ để AI hát tròn vành rõ chữ, không bị dồn nhịp hay nuốt chữ
        words = line.split()
        if (len(words) > 8 or len(line) > 48) and ' ' in line:
            mid = len(words) // 2
            formatted.append(' '.join(words[:mid]))
            formatted.append(' '.join(words[mid:]))
        else:
            formatted.append(line)

    if in_intro and intro_lyrics_buffer:
        formatted.append("[verse 1]")
        formatted.extend(intro_lyrics_buffer)

    result = '\n'.join(formatted).strip()

    if not has_tags:
        sub = [x for x in result.split('\n') if x.strip()]
        if len(sub) <= 4:
            result = "[verse]\n" + "\n".join(sub)
        else:
            half = len(sub) // 2
            v_part = "\n".join(sub[:half])
            c_part = "\n".join(sub[half:])
            result = f"[verse]\n{v_part}\n\n[chorus]\n{c_part}"

    return result




def reset_client():
    global _client
    with _client_lock:
        _client = None
    logger.info("ACE-Step client reset")


# Quản lý Circuit Breaker & Health Probe để loại bỏ hiện tượng đơ 60s khi mất mạng
_CIRCUIT_BREAKER_UNTIL: float = 0.0
_CIRCUIT_BREAKER_LOCK = threading.Lock()


def record_acestep_failure(cooldown_seconds: float = 45.0):
    """Kích hoạt Circuit Breaker trong cooldown_seconds khi xảy ra lỗi kết nối mạng."""
    global _CIRCUIT_BREAKER_UNTIL
    with _CIRCUIT_BREAKER_LOCK:
        _CIRCUIT_BREAKER_UNTIL = time.time() + cooldown_seconds
        logger.warning(f"[ACE-Step Circuit Breaker] Đã ngắt mạch trong {cooldown_seconds:.0f}s để tránh đơ request.")


def is_acestep_available(fast: bool = True) -> bool:
    """
    Kiểm tra nhanh tính khả dụng của ACE-Step Space (< 2.5s).
    - Nếu Circuit Breaker đang mở (vừa bị lỗi mạng gần đây), trả về False tức thì.
    - Gửi request probe siêu nhẹ đến API Hugging Face để xác nhận trạng thái RUNNING.
    """
    global _CIRCUIT_BREAKER_UNTIL
    now = time.time()
    with _CIRCUIT_BREAKER_LOCK:
        if now < _CIRCUIT_BREAKER_UNTIL:
            return False

    if not fast:
        return True

    try:
        import httpx
        url = "https://huggingface.co/api/spaces/ACE-Step/ACE-Step"
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                stage = data.get("runtime", {}).get("stage", "").upper()
                if stage in ("RUNNING", "APP_STARTING"):
                    return True
                if stage in ("SLEEPING", "PAUSED", "STOPPED"):
                    logger.info(f"[ACE-Step Probe] Space đang ở trạng thái {stage}")
                    return False
                return True
    except Exception as e:
        logger.debug(f"[ACE-Step Health Probe] Offline/Unreachable: {e}")
        record_acestep_failure(cooldown_seconds=30.0)
        return False

    return True


def _get_active_tokens() -> list:
    """Nạp danh sách token động từ môi trường (.env), bảo mật và không hardcode."""
    try:
        from dotenv import load_dotenv
        dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
        load_dotenv(dotenv_path, override=False)
    except Exception:
        pass
    tokens = []
    for key in ("HF_TOKEN", "HF_TOKEN_SECONDARY", "HF_TOKEN_BACKUP"):
        tok = os.environ.get(key, "").strip()
        if tok and tok not in tokens:
            tokens.append(tok)
    return tokens


_token_index = 0
_current_token = None


def rotate_token():
    global _token_index, _current_token, _client
    tokens = _get_active_tokens()
    if not tokens:
        return None
    with _client_lock:
        _token_index = (_token_index + 1) % len(tokens)
        _current_token = tokens[_token_index]
        _client = None
        masked = f"{_current_token[:6]}...{_current_token[-4:]}" if len(_current_token) >= 10 else "***"
        logger.info(f"Đã chuyển sang token dự phòng: {masked}")
        return _current_token


def get_client(force_new=False):
    global _client, _current_token, _token_index
    with _client_lock:
        try:
            from dotenv import load_dotenv
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env_file = os.path.join(base_dir, ".env")
            if os.path.exists(env_file):
                load_dotenv(env_file, override=True)
            else:
                load_dotenv(override=True)
        except Exception:
            pass

        tokens = _get_active_tokens()
        hf_token = tokens[_token_index % len(tokens)] if tokens else os.environ.get("HF_TOKEN", "").strip()

        if hf_token != _current_token:
            _client = None
            _current_token = hf_token

        if _client is None or force_new:
            logger.info("Connecting to ACE-Step HF Space with optimized timeout...")
            from gradio_client import Client
            import httpx

            masked_tok = f"{hf_token[:6]}...{hf_token[-4:]}" if (hf_token and len(hf_token) >= 10) else "(no-token)"
            logger.info(f"Using HF token: {masked_tok}")

            custom_timeout = httpx.Timeout(180.0, connect=10.0)
            try:
                _client = Client(
                    "ACE-Step/ACE-Step",
                    token=hf_token if hf_token else None,
                    verbose=False,
                    httpx_kwargs={"timeout": custom_timeout}
                )
                logger.info("ACE-Step client connected successfully!")
            except Exception as e:
                _client = None
                record_acestep_failure(cooldown_seconds=45.0)
                raise RuntimeError(f"Không thể kết nối đến ACE-Step Space: {e}") from e
        return _client


def generate_with_acestep(
    prompt="",
    lyrics="",
    duration=0,           # 0 = auto-detect theo genre
    genre="pop",
    mood="happy",
    instruments="full",
    custom_prompt="",
    guidance_scale=None,  # None = dùng preset
    infer_steps=None,     # None = dùng preset
    seed="",
    vocal_gender="female",
    quality="balanced",   # "fast" | "balanced" | "high"
    song_config=None,     # SongConfig từ PromptAnalyzer (optional, dùng để build rich caption)
    master_audio=False,   # Mặc định False: để orchestrator mastering đúng 1 lần duy nhất, tránh double mastering
):
    """
    Tạo nhạc có giọng hát bằng ACE-Step.
    Tối ưu hóa Studio-grade:
    - QUALITY_PRESETS: FAST / BALANCED / HIGH với guidance_scale 7.5 - 9.0 chống méo tiếng / rè.
    - guidance_scale_lyric 1.15 - 1.25 giúp giọng hát tiếng Việt rõ ràng, thanh thoát, tự nhiên.
    - Single-pass mastering: Đảm bảo audio chỉ qua mastering 1 lần duy nhất, chống méo clipping.
    """
    # ── BƯỚC 0: Resolve quality preset ──────────────────────────────────────
    quality_key = (quality or "balanced").lower()
    if quality_key not in QUALITY_PRESETS:
        quality_key = "balanced"
    preset = QUALITY_PRESETS[quality_key]

    # Override với giá trị user truyền vào nếu có
    actual_infer_steps    = int(infer_steps)    if infer_steps    is not None else preset["infer_step"]
    actual_guidance       = float(guidance_scale) if (guidance_scale is not None and float(guidance_scale) >= 12.0) else preset["guidance_scale"]
    actual_guidance       = max(5.0, min(actual_guidance, 18.0))
    actual_infer_steps    = max(30, min(actual_infer_steps, 100))

    # ── BƯỚC 1: Auto-duration ─────────────────────────────────────────────
    if not duration or duration <= 0:
        duration = GENRE_AUTO_DURATION.get(genre, 180)
        logger.info(f"[ACE-Step] Auto-duration: {genre} → {duration}s")
    duration = max(15, min(int(duration), 240))

    # ── BƯỚC 2: Xây dựng caption ──────────────────────────────────────────
    # Ưu tiên: song_config (rich caption) > custom_prompt > prompt > build_tags
    if song_config and isinstance(song_config, dict):
        try:
            from .caption_builder import build_rich_caption
            final_prompt = build_rich_caption(song_config, quality=quality_key)
            logger.info(f"[ACE-Step] Rich caption built: {final_prompt[:120]}...")
        except Exception as cb_err:
            logger.warning(f"[ACE-Step] CaptionBuilder failed, fallback: {cb_err}")
            final_prompt = custom_prompt.strip() or prompt.strip() or build_tags(genre, mood, instruments, custom_prompt)
    elif custom_prompt.strip():
        final_prompt = custom_prompt.strip()
    elif prompt.strip():
        final_prompt = prompt.strip()
    else:
        final_prompt = build_tags(genre, mood, instruments, "")

    # ── BƯỚC 3: Detect vocal gender từ prompt ────────────────────────────
    all_text = f"{final_prompt} {custom_prompt} {prompt}".lower()
    if any(k in all_text for k in ["giọng nam", "nam hát", "nam ca sĩ", "male voice", "male vocal", "male singer", "anh hát", "chàng trai hát", "nam trầm"]):
        vocal_gender = "male"
    elif any(k in all_text for k in ["giọng nữ", "nữ hát", "nữ ca sĩ", "female voice", "female vocal", "female singer", "cô gái hát", "nữ cao"]):
        vocal_gender = "female"
    elif any(k in all_text for k in ["song ca", "nam nữ", "duet"]):
        vocal_gender = "duet"
    elif any(k in all_text for k in ["không lời", "instrumental", "nhạc nền", "beat", "no vocal"]):
        vocal_gender = "instrumental"

    # ── BƯỚC 4: Auto-generate lyrics nếu chưa có ─────────────────────────
    if not lyrics.strip() and vocal_gender != "instrumental":
        try:
            from .smart_lyrics import generate_structured_lyrics
            topic = custom_prompt.strip() or prompt.strip() or "tình yêu cuộc sống"
            topic_clean = topic.split(',')[0].strip()
            gen_res = generate_structured_lyrics(topic=topic_clean, genre=genre, vocal_gender=vocal_gender)
            if gen_res and gen_res.get("lyrics"):
                full_lyr = gen_res["lyrics"]
                if duration <= 45:
                    if "[Verse 2]" in full_lyr:
                        lyrics = full_lyr.split("[Verse 2]")[0].strip()
                    else:
                        lyrics = full_lyr[:250].strip()
                elif duration <= 90:
                    if "[Bridge]" in full_lyr:
                        lyrics = full_lyr.split("[Bridge]")[0].strip()
                    else:
                        lyrics = full_lyr[:500].strip()
                else:
                    lyrics = full_lyr
                logger.info(f"[ACE-Step] Auto-lyrics ({duration}s): {lyrics[:60]}...")
        except Exception as e:
            logger.warning(f"[ACE-Step] Failed to auto-generate lyrics: {e}")

    has_lyrics = bool(lyrics.strip()) and vocal_gender != "instrumental"
    is_vietnamese = False

    # ── BƯỚC 5: Làm sạch prompt và xử lý vocal gender ───────────────────
    if has_lyrics:
        cfg_lang = (song_config.get("language") or "").lower() if song_config else ""
        if cfg_lang == "ko":
            is_korean = True
            is_vietnamese = False
            is_japanese = False
            is_chinese = False
        elif cfg_lang == "ja":
            is_japanese = True
            is_vietnamese = False
            is_korean = False
            is_chinese = False
        elif cfg_lang == "zh":
            is_chinese = True
            is_vietnamese = False
            is_korean = False
            is_japanese = False
        elif cfg_lang == "en":
            is_vietnamese = False
            is_korean = False
            is_japanese = False
            is_chinese = False
        elif cfg_lang == "vi":
            is_vietnamese = True
            is_korean = False
            is_japanese = False
            is_chinese = False
        else:
            is_vietnamese = detect_vietnamese(lyrics) or any(
                k in all_text for k in ["tiếng việt", "vietnamese", "vpop", "v-pop", "việt"]
            )
            is_korean  = any(k in all_text for k in ["korean", "kpop", "k-pop"]) or bool(re.search(r'[\uac00-\ud7af]', lyrics))
            is_japanese = any(k in all_text for k in ["japanese", "jpop", "j-pop", "anime"]) or bool(re.search(r'[\u3040-\u30ff]', lyrics))
            is_chinese  = any(k in all_text for k in ["chinese", "cpop", "mandarin"]) or bool(re.search(r'[\u4e00-\u9fff]', lyrics))

        # Nếu đã có rich caption từ CaptionBuilder → không cần thêm prefix nữa
        # Nếu không → thêm prefix vocal gender rõ ràng
        already_has_vocal_desc = any(v in final_prompt.lower() for v in [
            "female vocal", "male vocal", "duet vocal",
            "female lead", "male lead", "singing voice",
            "nữ hát", "nam hát"
        ])

        if not already_has_vocal_desc:
            if vocal_gender == "male":
                final_prompt = re.sub(
                    r'\b(female vocals?|female voice|woman vocals?|girl vocals?|female|woman|girl|giọng nữ|nữ ca sĩ)\b',
                    '', final_prompt, flags=re.IGNORECASE
                )
                if is_vietnamese:
                    prefix = "Vietnamese male lead vocal, warm deep singing voice, crisp articulate Vietnamese diction, distinct syllables, natural Vietnamese tonal pronunciation, intimate upfront close-mic vocal, studio recording"
                elif is_korean:
                    prefix = "Korean male lead vocal, warm smooth tone, precise Korean pronunciation, K-pop delivery"
                elif is_japanese:
                    prefix = "Japanese male lead vocal, clear precise pronunciation, J-pop emotive delivery"
                elif is_chinese:
                    prefix = "Chinese Mandarin male lead vocal, warm pronunciation, C-pop soulful delivery"
                else:
                    prefix = "solo male vocals, warm clear singing voice, emotional pop, articulate pronunciation, studio recording"
                final_prompt = f"{prefix}, {final_prompt.strip()}"

            elif vocal_gender == "female":
                final_prompt = re.sub(
                    r'\b(male vocals?|male voice|man vocals?|boy vocals?|male|man|boy|giọng nam|nam ca sĩ)\b',
                    '', final_prompt, flags=re.IGNORECASE
                )
                if is_vietnamese:
                    prefix = "Vietnamese female lead vocal, sweet clear singing voice, crisp articulate Vietnamese diction, distinct syllables, natural Vietnamese tonal pronunciation, intimate upfront close-mic vocal, studio recording"
                elif is_korean:
                    prefix = "Korean female lead vocal, bright emotive singing, crisp Korean pronunciation, K-pop style"
                elif is_japanese:
                    prefix = "Japanese female lead vocal, bright kawaii-to-powerful range, clear Japanese pronunciation, J-pop anime style"
                elif is_chinese:
                    prefix = "Chinese Mandarin female lead vocal, melodic Mandarin pronunciation, C-pop emotional style"
                else:
                    prefix = "solo female vocals, sweet clear singing voice, emotional pop, articulate pronunciation, studio recording"
                final_prompt = f"{prefix}, {final_prompt.strip()}"

            elif vocal_gender == "duet":
                if is_vietnamese:
                    final_prompt = f"Vietnamese duet vocals, male and female vocal harmony, crisp articulate Vietnamese diction, distinct syllables, natural Vietnamese tonal pronunciation, upfront studio recording, {final_prompt.strip()}"
                elif is_korean:
                    final_prompt = f"Korean duet vocals, male and female vocal harmony, K-pop vocal delivery, studio recording, {final_prompt.strip()}"
                elif is_japanese:
                    final_prompt = f"Japanese duet vocals, male and female vocal harmony, J-pop anime delivery, studio recording, {final_prompt.strip()}"
                elif is_chinese:
                    final_prompt = f"Chinese Mandarin duet vocals, male and female vocal harmony, C-pop delivery, studio recording, {final_prompt.strip()}"
                else:
                    final_prompt = f"duet vocals, male and female vocal harmony, clear singing, studio recording, {final_prompt.strip()}"
        if is_vietnamese:
            # Xóa sạch các từ khóa giọng ngoại lai (như English vocal, Korean vocal...) nếu có
            final_prompt = re.sub(
                r'\b(english|korean|japanese|chinese)\s+(male|female|duet)?\s*(lead)?\s*(vocals?|voice|singer)?\b',
                '',
                final_prompt,
                flags=re.IGNORECASE
            )
            # Ngay cả khi prompt đã có từ khóa vocal, tăng cường độ nét phát âm tiếng Việt đặc hiệu
            vi_clarity_tags = "crisp articulate Vietnamese diction, distinct syllables, natural tonal pronunciation, upfront lead vocal mix, intimate close-mic presence"
            if not any(k in final_prompt.lower() for k in ["articulate vietnamese", "distinct syllables"]):
                if vocal_gender == "male":
                    final_prompt = f"Vietnamese male lead vocal, warm deep singing voice, {vi_clarity_tags}, {final_prompt.strip()}"
                elif vocal_gender == "female":
                    final_prompt = f"Vietnamese female lead vocal, sweet clear singing voice, {vi_clarity_tags}, {final_prompt.strip()}"
                elif vocal_gender == "duet":
                    final_prompt = f"Vietnamese duet vocals, {vi_clarity_tags}, {final_prompt.strip()}"
                else:
                    final_prompt = f"{vi_clarity_tags}, {final_prompt.strip()}"

        # Dọn sạch các từ khóa làm mờ hoặc chìm vocal (reverb quá dày)
        if is_vietnamese:
            final_prompt = re.sub(
                r'\b(cinematic reverb|heavy reverb|washed out|distant vocals?|buried vocals?)\b',
                'clean studio acoustics',
                final_prompt,
                flags=re.IGNORECASE
            )

        # Chuẩn hóa lời bài hát: GIỮ NGUYÊN DẤU TIẾNG VIỆT
        lyrics = normalize_lyrics_for_acestep(lyrics)
        original_lyrics = lyrics
        logger.info(f"[ACE-Step] Lyrics preview: {lyrics[:120]!r}")

    else:
        original_lyrics = ""
        lyrics = ""
        final_prompt = f"instrumental, melodic, studio production, no vocals, {final_prompt}"

    seed_val = str(seed).strip()
    manual_seeds = seed_val if seed_val else None

    actual_lyric_guidance = preset["guidance_scale_lyric"]
    actual_text_guidance  = preset["guidance_scale_text"]
    if is_vietnamese and has_lyrics:
        actual_lyric_guidance = max(2.4, actual_lyric_guidance)
        actual_text_guidance  = max(0.8, actual_text_guidance)

    logger.info(
        f"[ACE-Step] PIPELINE PARAMS:\n"
        f"  quality={quality_key} | infer_step={actual_infer_steps} | guidance={actual_guidance}\n"
        f"  guidance_scale_lyric={actual_lyric_guidance} | guidance_scale_text={actual_text_guidance}\n"
        f"  vocal={vocal_gender} | lang={song_config.get('language', '?') if song_config else '?'}\n"
        f"  duration={duration}s | has_lyrics={has_lyrics} | seed={manual_seeds}\n"
        f"  caption={final_prompt[:100]}..."
    )
    t0 = time.time()

    predict_kwargs = dict(
        audio_duration=float(duration),
        prompt=final_prompt,
        lyrics=lyrics,
        infer_step=actual_infer_steps,
        guidance_scale=actual_guidance,
        scheduler_type=preset["scheduler_type"],
        cfg_type=preset["cfg_type"],
        omega_scale=preset["omega_scale"],
        manual_seeds=manual_seeds,
        guidance_interval=preset["guidance_interval"],
        guidance_interval_decay=preset["guidance_interval_decay"],
        min_guidance_scale=preset["min_guidance_scale"],
        use_erg_tag=True,
        use_erg_lyric=False,   # ← Tắt ERG Lyric cho tiếng Việt để tránh nổ entropy ký tự có dấu
        use_erg_diffusion=True,
        oss_steps="",
        guidance_scale_text=actual_text_guidance,
        guidance_scale_lyric=actual_lyric_guidance,   # ← THỰC SỰ DÙNG (tối ưu cho tiếng Việt)
        audio2audio_enable=False,
        ref_audio_strength=0.5,
        ref_audio_input=None,
        lora_name_or_path="none",
        api_name="/__call__",
    )

    result = None
    last_error = None

    tokens_pool = _get_active_tokens()
    max_attempts = max(2, len(tokens_pool))
    for attempt in range(max_attempts):
        try:
            force_new = (attempt > 0)
            if force_new:
                logger.warning(f"Retry attempt {attempt + 1} with fresh client...")
            client = get_client(force_new=force_new)
            result = client.predict(**predict_kwargs)
            break
        except Exception as e:
            last_error = e
            err_str = str(e).lower()

            if "zerogpu quota" in err_str:
                if attempt < len(tokens_pool) - 1:
                    logger.warning("ZeroGPU quota reached on current token. Rotating to backup token...")
                    rotate_token()
                    time.sleep(1)
                    continue
                else:
                    raise RuntimeError(
                        "Hạn ngạch miễn phí ZeroGPU trên Hugging Face đang tạm hết lượt trên tất cả token (hãy chờ 2-3 phút hoặc đổi token mới trong file .env)."
                    ) from e

            is_network_err = any(x in err_str for x in [
                "timeout", "handshake", "ssl", "connection", "reset",
                "eof", "broken pipe", "network", "socket"
            ])
            if attempt < max_attempts - 1 and is_network_err:
                logger.warning(f"Network error (attempt {attempt+1}): {e}. Resetting client...")
                reset_client()
                time.sleep(2)
                continue
            else:
                raise last_error

    if result is None:
        raise last_error

    elapsed = time.time() - t0
    logger.info(f"ACE-Step completed in {elapsed:.1f}s")

    raw_audio = result[0]
    if isinstance(raw_audio, dict):
        audio_path = raw_audio.get("path")
    else:
        audio_path = raw_audio

    # Hậu xử lý âm thanh DSP Mastering: Chỉ chạy nếu caller yêu cầu trực tiếp.
    # Khi chạy qua Orchestrator, Orchestrator sẽ là nơi mastering duy nhất để tránh double-mastering làm rè tiếng.
    if master_audio:
        postprocess_clean_audio(audio_path, is_vietnamese=is_vietnamese)

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    try:
        params = result[1] if len(result) > 1 else {}
        if isinstance(params, dict):
            actual_seed = str(params.get("manual_seeds", manual_seeds or "random"))
        else:
            actual_seed = manual_seeds or "random"
    except Exception:
        actual_seed = manual_seeds or "random"

    logger.info(f"Generated Audio: {len(audio_bytes):,} bytes | seed: {actual_seed} | vocal: {vocal_gender}")

    return {
        "audio_path":  audio_path,
        "audio_bytes": audio_bytes,
        "duration":    duration,
        "prompt":      final_prompt,
        "lyrics":      original_lyrics,   # lời gốc tiếng Việt đầy đủ dấu (hiển thị UI)
        "seed":        actual_seed,
        "elapsed":     round(elapsed, 1),
        "model":       "ACE-Step",
    }


def warmup_acestep():
    def _do():
        try:
            logger.info("Warming up ACE-Step connection...")
            get_client()
            logger.info("ACE-Step ready")
        except Exception as e:
            logger.warning(f"ACE-Step warm-up: {e}")
    threading.Thread(target=_do, daemon=True).start()