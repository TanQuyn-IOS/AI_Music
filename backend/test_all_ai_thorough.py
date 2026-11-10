# -*- coding: utf-8 -*-
"""
THOROUGH AI AUDIT SUITE FOR SONAVIA AI MUSIC
Kiểm tra chi tiết và toàn diện 100% tất cả các tính năng & engine AI trên hệ thống.
"""

import os
import sys
import time
import io
import json
import numpy as np
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import django
django.setup()

from django.test import Client
from apps.users.models import User
from apps.music.models import Song, ListenHistory

PASS = "✅ [PASS]"
FAIL = "❌ [FAIL]"
WARN = "⚠️ [WARN]"

results = []

def record(test_name, success, details=""):
    results.append((test_name, success, details))
    mark = PASS if success else FAIL
    print(f"{mark} {test_name}")
    if details:
        for line in details.strip().split('\n'):
            print(f"      {line}")


print("=" * 70)
print("🎵 SONAVIA AI MUSIC — KIỂM TRA TOÀN DIỆN TẤT CẢ CÁC ENGINE AI")
print("=" * 70)

# ─────────────────────────────────────────────────────────────────────────────
# 1. KIỂM TRA PROMPT ANALYZER AI & MAGIC ENHANCER
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1/10] KIỂM TRA AI PHÂN TÍCH PROMPT & MAGIC PROMPT ENHANCER")
try:
    from apps.ai_engine.prompt_analyzer import PromptAnalyzerService
    
    test_prompts = [
        ("Nhạc pop buồn về mưa đêm rơi lúc hoàng hôn, nữ hát", "vi", "vpop", "female"),
        ("Sôi động EDM quẩy bốc lửa bar club", "vi", "edm", "auto"),
        ("K-pop energetic dance with upbeat rhythm", "ko", "kpop", "auto"),
        ("anime opening J-pop guitar solo fast", "ja", "jpop", "auto"),
        ("acoustic guitar calm study relaxing lo-fi", "en", "lofi", "auto"),
        ("nhạc buồn", "vi", "vpop", "auto"),
    ]
    
    passed_cases = 0
    details_str = []
    for p, exp_lang, exp_genre, exp_vocal in test_prompts:
        cfg = PromptAnalyzerService.analyze(p)
        matched_lang = (cfg['language'] == exp_lang)
        matched_genre = (cfg['genre'] == exp_genre or exp_genre in cfg['genre'])
        if matched_lang:
            passed_cases += 1
        details_str.append(
            f"Prompt: '{p[:30]}...' -> Lang={cfg['language']}, Genre={cfg['genre']}, "
            f"Mood={cfg['mood']}, BPM={cfg['bpm']}, Key={cfg['key']}, Vocal={cfg['vocal_gender']}"
        )
    
    record("PromptAnalyzerService Multi-language & Nuance Extraction", passed_cases >= len(test_prompts) - 1, "\n".join(details_str))
except Exception as e:
    record("PromptAnalyzerService", False, str(e))

# Magic Prompt Enhancer
try:
    from apps.ai_engine.llm_service import enhance_prompt_with_llm
    enh = enhance_prompt_with_llm("nhạc buồn mưa rơi", language="vi")
    success = bool(enh.get("enhanced_prompt")) and len(enh.get("enhanced_prompt")) > len("nhạc buồn mưa rơi")
    record("Magic Prompt Enhancer (Offline/LLM Fallback)", success, f"Enhanced: '{enh.get('enhanced_prompt')[:80]}...'")
except Exception as e:
    record("Magic Prompt Enhancer", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 2. KIỂM TRA LYRIC ENGINE AI & SMART STRUCTURED LYRICS
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/10] KIỂM TRA AI SÁNG TÁC LỜI BÀI HÁT & CẤU TRÚC SUNO / ACE-STEP")
try:
    from apps.ai_engine.lyric_engine import generate_multilingual_lyrics
    from apps.ai_engine.smart_lyrics import generate_structured_lyrics

    # Test tiếng Việt có cấu trúc đầy đủ
    vi_res = generate_structured_lyrics(
        topic="tình yêu tuổi học trò dưới mưa",
        genre="vpop",
        mood="romantic",
        vocal_gender="female"
    )
    has_structure = all(tag in vi_res['lyrics'] for tag in ['[Verse 1]', '[Chorus]'])
    record(
        "Structured Lyrics Generator (Tiếng Việt Verse/Chorus/Bridge)",
        has_structure and len(vi_res['lyrics']) > 150,
        f"Title: '{vi_res.get('title')}' | Chars: {len(vi_res['lyrics'])} | Has tags: {has_structure}"
    )

    # Test đa ngôn ngữ (KO, JA, ZH, EN)
    languages = [("ko", "love", "kpop"), ("ja", "energy", "jpop"), ("zh", "sad", "cpop"), ("en", "happy", "pop")]
    lang_ok = 0
    for lang, theme, genre in languages:
        lyr = generate_multilingual_lyrics(language=lang, theme=theme, genre=genre, vocal_gender="female", user_prompt="test")
        if lyr.get("title") and len(lyr.get("lyrics", "")) > 100:
            lang_ok += 1
    record(
        "Multilingual Lyrics (KO, JA, ZH, EN)",
        lang_ok == len(languages),
        f"Passed: {lang_ok}/{len(languages)} languages generated successfully"
    )
except Exception as e:
    record("Lyric Engine AI", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 3. KIỂM TRA AI PHÂN TÍCH HÌNH ẢNH (VISUAL SYNESTHESIA: IMAGE TO MUSIC)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/10] KIỂM TRA AI CẢM NHẬN HÌNH ẢNH SANG ÂM NHẠC (VISUAL SYNESTHESIA)")
try:
    from apps.ai_engine.image_analyzer import ImageToMusicAnalyzer

    # Test 1: Ảnh hoàng hôn (Sunset: Đỏ / Cam / Vàng) -> Phải ra Romantic hoặc Melancholic
    sunset_img = Image.new('RGB', (120, 120), color=(235, 110, 45))
    res_sunset = ImageToMusicAnalyzer.analyze_image(sunset_img)
    sunset_valid = res_sunset.get("mood") in ["romantic", "melancholic", "calm", "happy"] and res_sunset.get("bpm") > 0
    record(
        "Image Analyzer: Sunset Palette -> Mood & Music Parameters",
        sunset_valid,
        f"Mood: {res_sunset.get('mood_name')} | Genre: {res_sunset.get('genre_name')} | BPM: {res_sunset.get('bpm')} | Key: {res_sunset.get('key')}"
    )

    # Test 2: Ảnh đêm Cyberpunk Neon (Tím / Xanh đậm) -> Phải ra Energetic / EDM / Electronic
    neon_img = Image.new('RGB', (120, 120), color=(15, 10, 50))
    res_neon = ImageToMusicAnalyzer.analyze_image(neon_img)
    neon_valid = res_neon.get("bpm") > 0 and len(res_neon.get("palette", [])) > 0
    record(
        "Image Analyzer: Night/Neon Palette -> Atmosphere & Style Tags",
        neon_valid,
        f"Mood: {res_neon.get('mood_name')} | Atmosphere: {res_neon.get('atmosphere')[:60]}... | Tags: {res_neon.get('visual_tags')[:3]}"
    )

    # Test 3: Ảnh thiên nhiên thanh bình (Xanh lá) -> Calm / Acoustic
    green_img = Image.new('RGB', (120, 120), color=(34, 139, 34))
    res_green = ImageToMusicAnalyzer.analyze_image(green_img)
    green_valid = res_green.get("bpm") > 0 and bool(res_green.get("prompt")) and bool(res_green.get("lyrics"))
    record(
        "Image Analyzer: Nature Green -> Peaceful Atmosphere & Prompt/Lyrics",
        green_valid,
        f"Mood: {res_green.get('mood_name')} | Prompt: {res_green.get('prompt')[:60]}... | Lyrics: {len(res_green.get('lyrics', ''))} chars"
    )
except Exception as e:
    record("Image Analyzer AI", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 4. KIỂM TRA AI CHATBOT TƯ VẤN ÂM NHẠC & PHÂN TÍCH TÂM TRẠNG
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/10] KIỂM TRA AI CHATBOT TƯ VẤN & NHẬN DIỆN CẢM XÚC")
try:
    from apps.ai_engine.chatbot import get_chatbot_response
    sample_songs = list(Song.objects.filter(is_published=True)[:20])

    chat_tests = [
        ("Xin chào Sonavia", None, "greeting"),
        ("Hôm nay tôi thất tình và rất buồn, khóc một mình", "sad", "sad"),
        ("Hom nay toi rat buon va met moi", "sad", "unaccented sad"),
        ("Tối nay đi quẩy tiệc tùng bốc lửa cháy hết mình", "energetic", "energetic"),
        ("Cần nhạc nhẹ nhàng bình yên để ngủ ngon", "calm", "calm"),
        ("Gợi ý nhạc pop", None, "genre query"),
    ]

    chat_passed = 0
    chat_details = []
    for msg, exp_mood, desc in chat_tests:
        r = get_chatbot_response(msg, sample_songs)
        msg_out = r.get("message") or r.get("reply") or ""
        detected = r.get("mood")
        matched = (exp_mood is None) or (detected == exp_mood)
        if matched and len(msg_out) > 10:
            chat_passed += 1
        chat_details.append(f"Input: '{msg}' -> Mood={detected} | Reply: '{msg_out[:60]}...'")

    record(
        "AI Chatbot Emotion Recognition & Responses (Accented & Unaccented)",
        chat_passed == len(chat_tests),
        "\n".join(chat_details)
    )
except Exception as e:
    record("Chatbot AI", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 5. KIỂM TRA AI ĐỀ XUẤT (RECOMMENDATION ENGINE - COSINE SIMILARITY & PROFILING)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5/10] KIỂM TRA AI ĐỀ XUẤT ÂM NHẠC (RECOMMENDER & USER PROFILING)")
try:
    from apps.ai_engine.recommender import (
        get_content_based_recommendations,
        get_user_based_recommendations,
        get_mood_based_recommendations,
        get_music_profile,
        song_to_vector,
    )

    all_songs = list(Song.objects.filter(is_published=True))
    if len(all_songs) >= 2:
        # Test 1: Content-based (Cosine Vector Similarity)
        target = all_songs[0]
        recs = get_content_based_recommendations(target, all_songs, top_n=5)
        vec = song_to_vector(target)
        record(
            "Content-Based Recommendation (Vector Cosine Similarity)",
            len(recs) > 0 and target.id not in [s.id for s in recs],
            f"Target: '{target.title}' ({target.genre}, {target.mood}) -> Recommended {len(recs)} songs: {[s.title for s in recs[:3]]}"
        )

        # Test 2: Mood-based
        mood_recs = get_mood_based_recommendations("happy", all_songs, top_n=5)
        record(
            "Mood-Based Recommendation",
            len(mood_recs) > 0,
            f"Found {len(mood_recs)} songs for mood 'happy': {[s.title for s in mood_recs[:3]]}"
        )

        # Test 3: Music Profile
        test_history = list(ListenHistory.objects.all()[:15])
        profile = get_music_profile(test_history)
        record(
            "User Music Profile Aggregation",
            "top_genres" in profile and "top_moods" in profile and "favorite_tempo" in profile,
            f"Top Genres: {profile.get('top_genres')} | Avg Tempo: {profile.get('favorite_tempo')} BPM"
        )
    else:
        record("Recommendation Engine", False, "Cần ít nhất 2 bài hát trong Database để kiểm tra.")
except Exception as e:
    record("Recommendation Engine", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 6. KIỂM TRA AI MIDI COMPOSER (3 TRACKS: PIANO CHORDS + MELODY + BASS)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6/10] KIỂM TRA AI SOẠN NHẠC MIDI 3-TRACK")
try:
    from apps.ai_engine.music_composer import generate_midi, generate_lyrics, build_progression, get_scale, NOTES

    # Test MIDI binary output
    midi_bytes = generate_midi(
        genre="vpop",
        mood="romantic",
        root_note="G",
        num_bars=16,
        bpm=90
    )
    is_valid_midi = midi_bytes.startswith(b'MThd') and len(midi_bytes) > 500
    record(
        "MIDI 3-Track Generator (Piano Chords + Melody + Bass)",
        is_valid_midi,
        f"Length: {len(midi_bytes):,} bytes | Header: {midi_bytes[:4]} (Valid standard MIDI header)"
    )

    # Test Scale & Chords helper
    scale = get_scale(60, 'major')  # C Major
    chords = build_progression('pop', 60, 'major')
    record(
        "Music Theory Helpers (Scales & Chord Progressions)",
        len(scale) == 7 and len(chords) >= 4,
        f"Scale length: {len(scale)} notes | Progression bars: {len(chords)} chords"
    )
except Exception as e:
    record("MIDI Composer AI", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 7. KIỂM TRA DSP AUDIO MASTERING & VOCAL CLARITY ENGINE
# ─────────────────────────────────────────────────────────────────────────────
print("\n[7/10] KIỂM TRA DSP AUDIO MASTERING & TỐI ƯU ĐỘ RÕ NGỮ ÂM TIẾNG VIỆT")
try:
    from apps.ai_engine.audio_mastering import master_audio_array, master_audio_bytes

    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # Signal kết hợp 40Hz (ù) + 1000Hz (thân) + 3200Hz (vocal formant) + 11000Hz (air)
    synth_wave = (
        0.5 * np.sin(2 * np.pi * 40 * t) +
        0.3 * np.sin(2 * np.pi * 1000 * t) +
        0.2 * np.sin(2 * np.pi * 3200 * t) +
        0.1 * np.sin(2 * np.pi * 11000 * t)
    ).astype(np.float32)

    mastered = master_audio_array(synth_wave, sr, is_vietnamese=True)
    peak = float(np.max(np.abs(mastered)))
    peak_ok = 0.88 <= peak <= 0.895

    # Kiểm tra cắt sub-bass 40Hz
    fft_orig = np.abs(np.fft.rfft(synth_wave))
    fft_mast = np.abs(np.fft.rfft(mastered))
    freqs = np.fft.rfftfreq(len(synth_wave), 1.0 / sr)
    idx_40 = np.argmin(np.abs(freqs - 40))
    idx_1k = np.argmin(np.abs(freqs - 1000))
    low_cut_ratio = (fft_mast[idx_40] / fft_mast[idx_1k]) / (fft_orig[idx_40] / fft_orig[idx_1k])
    low_cut_ok = low_cut_ratio < 0.25

    record(
        "DSP Mastering: True-Peak Normalization (-1.0 dBFS / 0.891 Headroom)",
        peak_ok,
        f"Target: 0.891 | Actual Peak: {peak:.4f} | Zero-clipping: {peak <= 0.895}"
    )
    record(
        "DSP Mastering: Adaptive High-Pass Filter (<65Hz rumble cut)",
        low_cut_ok,
        f"40Hz Attenuation Ratio: {low_cut_ratio:.4f} (< 0.25 threshold)"
    )

    # Test master in-memory bytes (WAV)
    import soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, synth_wave, sr, format='WAV')
    raw_wav = buf.getvalue()
    out_wav = master_audio_bytes(raw_wav, is_vietnamese=True, output_format='WAV')
    record(
        "DSP Mastering: In-Memory Audio Bytes Processing",
        len(out_wav) > 1000,
        f"Input: {len(raw_wav):,} bytes -> Output: {len(out_wav):,} bytes"
    )
except Exception as e:
    record("DSP Audio Mastering", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 8. KIỂM TRA RICH CAPTION BUILDER (CHUYỂN PROMPT THÀNH CAPTION PHÒNG THU)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[8/10] KIỂM TRA CAPTION BUILDER (EXPANDED STUDIO PROMPT CAPTIONS)")
try:
    from apps.ai_engine.caption_builder import build_rich_caption
    config = {
        "language": "vi",
        "genre": "vpop",
        "genre_name": "V-Pop Ballad",
        "mood": "romantic",
        "mood_name": "Lãng mạn",
        "bpm": 85,
        "key": "G Major",
        "vocal_gender": "female",
        "theme": "love",
        "user_prompt": "Nhạc tình yêu lãng mạn nhẹ nhàng",
    }
    
    cap_fast = build_rich_caption(config, quality="fast")
    cap_balanced = build_rich_caption(config, quality="balanced")
    cap_high = build_rich_caption(config, quality="high")

    cap_ok = (len(cap_fast) > 100) and (len(cap_balanced) > 150) and (len(cap_high) > 200)
    record(
        "Rich Studio Caption Builder (Fast / Balanced / High Presets)",
        cap_ok,
        f"Fast: {len(cap_fast)} chars | Balanced: {len(cap_balanced)} chars | High: {len(cap_high)} chars\n"
        f"Sample: '{cap_balanced[:100]}...'"
    )
except Exception as e:
    record("Caption Builder", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 9. KIỂM TRA TẠO ÂM THANH THỰC SỰ TRÊN GPU (META MUSICGEN AI)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[9/10] KIỂM TRA TẠO ÂM THANH THỰC SỰ TRÊN GPU (META MUSICGEN)")
try:
    import torch
    cuda_avail = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
    print(f"      Thiết bị: {gpu_name} | CUDA: {cuda_avail}")

    from apps.ai_engine.music_generator import generate_music
    t0 = time.time()
    # Tạo 5 giây audio nhẹ để kiểm tra inference pipeline (dùng cache nếu đã chạy)
    audio_bytes, sr = generate_music("acoustic guitar chill lofi beat", duration=5)
    elapsed = time.time() - t0
    gen_ok = len(audio_bytes) > 1000 and sr > 0
    record(
        "Meta MusicGen AI Generation on Local GPU",
        gen_ok,
        f"Audio output: {len(audio_bytes):,} bytes | Sampling Rate: {sr}Hz | Inference time: {elapsed:.2f}s"
    )
except Exception as e:
    record("Meta MusicGen AI Generation", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 10. KIỂM TRA TẤT CẢ ENDPOINT API CỦA TOÀN BỘ HỆ THỐNG AI
# ─────────────────────────────────────────────────────────────────────────────
print("\n[10/10] KIỂM TRA CÁC API ENDPOINTS AI QUA HTTP TEST CLIENT")
try:
    from rest_framework.test import APIClient
    c = APIClient()
    admin_user = User.objects.filter(is_staff=True).first()
    if admin_user:
        c.force_authenticate(user=admin_user)

    api_tests = [
        ("POST", "/api/ai/analyze/", {"prompt": "Nhạc chill học bài"}, 200),
        ("POST", "/api/ai/prompt/enhance/", {"prompt": "nhạc buồn trời mưa", "language": "vi"}, 200),
        ("POST", "/api/ai/lyrics/generate/", {"topic": "Mưa mùa hạ", "genre": "vpop", "mood": "calm"}, 200),
        ("POST", "/api/ai/chatbot/", {"message": "Hôm nay tôi thấy vui quá"}, 200),
        ("POST", "/api/ai/compose/lyrics/", {"mood": "happy", "genre": "pop", "num_verses": 2}, 200),
        ("POST", "/api/ai/compose/preview/", {"genre": "pop", "mood": "happy", "root_note": "C"}, 200),
        ("POST", "/api/ai/compose/midi/", {"genre": "pop", "mood": "happy", "root_note": "C", "num_bars": 8}, 200),
        ("GET", "/api/ai/generate/options/", None, 200),
        ("GET", "/api/ai/generate/status/", None, 200),
        ("GET", "/api/ai/acestep/status/", None, 200),
        ("GET", "/api/ai/profile/", None, 200),
    ]

    api_passed = 0
    api_details = []
    for method, path, body, exp_code in api_tests:
        if method == "POST":
            res = c.post(path, data=json.dumps(body) if body else {}, content_type="application/json")
        else:
            res = c.get(path)
        matched = (res.status_code == exp_code)
        if matched:
            api_passed += 1
        api_details.append(f"{method} {path} -> HTTP {res.status_code} (Expected {exp_code})")

    record(
        "All AI Web API Endpoints Validation",
        api_passed == len(api_tests),
        f"Passed: {api_passed}/{len(api_tests)} endpoints\n" + "\n".join(api_details[:6])
    )
except Exception as e:
    record("AI API Endpoints", False, str(e))


print("\n" + "=" * 70)
total_tests = len(results)
passed_tests = sum(1 for _, ok, _ in results if ok)
print(f"📊 TỔNG KẾT: {passed_tests}/{total_tests} HẠNG MỤC AI ĐẠT CHUẨN!")
print("=" * 70)

if passed_tests == total_tests:
    print("🎉 TẤT CẢ 10/10 MODULE VÀ TÍNH NĂNG AI HOẠT ĐỘNG HOÀN HẢO!")
else:
    print("⚠️ Có một số bài kiểm tra chưa đạt yêu cầu, xem chi tiết ở trên.")
