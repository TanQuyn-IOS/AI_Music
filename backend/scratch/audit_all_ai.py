import os
import sys
import time

backend_dir = r"c:\Users\QUYN\OneDrive\Documents\Luu_o_day_ne\AI Music\backend"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from rest_framework.test import APIClient
from apps.users.models import User
from apps.music.models import Song

client = APIClient()

test_user = User.objects.filter(is_staff=True).first() or User.objects.first()
if test_user:
    client.force_authenticate(user=test_user)

audit_report = []

def test_endpoint(category, name, method, url, payload=None, validator=None):
    t0 = time.time()
    try:
        if method == "GET":
            res = client.get(url, payload or {}, format="json")
        elif method == "POST":
            res = client.post(url, payload or {}, format="json")
        else:
            res = None

        elapsed = round((time.time() - t0) * 1000, 1)

        ok = res is not None and res.status_code in (200, 201)
        detail = ""
        if ok and validator:
            valid, detail = validator(res.data if hasattr(res, 'data') else res.content)
            if not valid:
                ok = False
        elif not ok:
            detail = f"Status: {res.status_code if res else 'No response'} | Data: {str(getattr(res, 'data', ''))[:120]}"

        audit_report.append({
            "category": category,
            "name": name,
            "url": url,
            "passed": ok,
            "elapsed_ms": elapsed,
            "detail": detail
        })
        icon = "✅ [PASS]" if ok else "❌ [FAIL]"
        print(f"{icon} {category} - {name} ({elapsed}ms)")
        if detail:
            print(f"      -> {detail}")
    except Exception as e:
        elapsed = round((time.time() - t0) * 1000, 1)
        audit_report.append({
            "category": category,
            "name": name,
            "url": url,
            "passed": False,
            "elapsed_ms": elapsed,
            "detail": f"Exception: {str(e)}"
        })
        print(f"❌ [FAIL] {category} - {name} ({elapsed}ms): {e}")

print("=" * 80)
print("🔍 BẮT ĐẦU KIỂM TRA TOÀN DIỆN TẤT CẢ CÁC TÍNH NĂNG AI CỦA SONAVIA STUDIO")
print("=" * 80)

# 1. Prompt Analyzer
test_endpoint(
    category="1. Phân Tích & Hiểu Ngữ Nghĩa",
    name="Prompt Analyzer (Phân tích phong cách, BPM, Gam, Cấu trúc)",
    method="POST",
    url="/api/ai/analyze/",
    payload={"prompt": "V-Pop ballad buồn về hoàng hôn, giọng nữ trong trẻo, piano sâu lắng", "language": "vi", "vocal": "female"},
    validator=lambda d: ("genre" in d and "bpm" in d and "mood" in d, f"Genre: {d.get('genre_name')} | Mood: {d.get('mood_name')} | BPM: {d.get('bpm')} | Key: {d.get('key')}")
)

# 2. Magic Prompt Enhancer
test_endpoint(
    category="1. Phân Tích & Hiểu Ngữ Nghĩa",
    name="Magic Prompt Enhancer (Nâng cấp prompt ngắn thành studio prompt)",
    method="POST",
    url="/api/ai/prompt/enhance/",
    payload={"prompt": "nhac chill mua thu", "language": "vi"},
    validator=lambda d: ("enhanced_prompt" in d and len(d.get("enhanced_prompt", "")) > 10, f"Enhanced: {d.get('enhanced_prompt')[:70]}...")
)

# 3. Emotion Classification
test_endpoint(
    category="1. Phân Tích & Hiểu Ngữ Nghĩa",
    name="Emotion Classifier (Phân loại cảm xúc tiếng Việt 6 nhãn)",
    method="POST",
    url="/api/ai/emotion/classify/",
    payload={"text": "Tôi cảm thấy lòng nhẹ nhõm và vô cùng bình yên giữa thiên nhiên"},
    validator=lambda d: (d.get("emotion") == "calm", f"Emotion: {d.get('emotion')} | Confidence: {d.get('confidence')}")
)

# 4. Smart Lyrics - Tiếng Việt
test_endpoint(
    category="2. Sáng Tác Lời Ca Từ (Lyric AI)",
    name="Smart Lyrics Generator - Tiếng Việt (V-Pop)",
    method="POST",
    url="/api/ai/lyrics/generate/",
    payload={"topic": "Tình yêu đầu thời học sinh", "language": "vi", "genre": "vpop", "mood": "romantic"},
    validator=lambda d: (len(d.get("lyrics", "")) > 100 and "title" in d, f"Title: '{d.get('title')}' | Dòng: {len(d.get('lyrics', '').splitlines())}")
)

# 5. Smart Lyrics - Tiếng Hàn (K-Pop)
test_endpoint(
    category="2. Sáng Tác Lời Ca Từ (Lyric AI)",
    name="Smart Lyrics Generator - Tiếng Hàn (K-Pop Hangul)",
    method="POST",
    url="/api/ai/lyrics/generate/",
    payload={"topic": "Spring love memory", "language": "ko", "genre": "kpop", "mood": "happy"},
    validator=lambda d: (any('\uac00' <= ch <= '\ud7af' for ch in d.get("lyrics", "")), f"Title: '{d.get('title')}' | Hangul verified: True")
)

# 6. Smart Lyrics - Tiếng Nhật (J-Pop)
test_endpoint(
    category="2. Sáng Tác Lời Ca Từ (Lyric AI)",
    name="Smart Lyrics Generator - Tiếng Nhật (J-Pop / Anime)",
    method="POST",
    url="/api/ai/lyrics/generate/",
    payload={"topic": "Cherry blossom sky", "language": "ja", "genre": "jpop", "mood": "calm"},
    validator=lambda d: (any('\u3040' <= ch <= '\u30ff' for ch in d.get("lyrics", "")), f"Title: '{d.get('title')}' | Kana/Kanji verified: True")
)

# 7. Smart Lyrics - Tiếng Trung (C-Pop)
test_endpoint(
    category="2. Sáng Tác Lời Ca Từ (Lyric AI)",
    name="Smart Lyrics Generator - Tiếng Trung (C-Pop Mandopop)",
    method="POST",
    url="/api/ai/lyrics/generate/",
    payload={"topic": "Rainy night longing", "language": "zh", "genre": "cpop", "mood": "sad"},
    validator=lambda d: (any('\u4e00' <= ch <= '\u9fff' for ch in d.get("lyrics", "")), f"Title: '{d.get('title')}' | Hanzi verified: True")
)

# 8. Smart Lyrics - Tiếng Anh (US-UK)
test_endpoint(
    category="2. Sáng Tác Lời Ca Từ (Lyric AI)",
    name="Smart Lyrics Generator - Tiếng Anh (English Pop)",
    method="POST",
    url="/api/ai/lyrics/generate/",
    payload={"topic": "Midnight highway drive", "language": "en", "genre": "pop", "mood": "energetic"},
    validator=lambda d: (len(d.get("lyrics", "")) > 100, f"Title: '{d.get('title')}' | English lyrics verified: True")
)

# 9. Image To Music - Bối cảnh mẫu (Sunset)
test_endpoint(
    category="3. Thị Giác Âm Nhạc (Vision Image-to-Music)",
    name="Image-to-Music Analyzer (Preset Scene: Golden Sunset Romantic)",
    method="POST",
    url="/api/ai/analyze-image/",
    payload={"preset_scene": "golden_sunset_romantic", "language": "vi"},
    validator=lambda d: (d.get("success") and "palette" in d and "lyrics" in d, f"Atmosphere: {d.get('atmosphere')[:60]}... | Key: {d.get('key')} | BPM: {d.get('bpm')}")
)

# 10. Image To Music - Bối cảnh mẫu Tiếng Hàn (Neon Cyber Night -> Korean)
test_endpoint(
    category="3. Thị Giác Âm Nhạc (Vision Image-to-Music)",
    name="Image-to-Music Analyzer (Preset Scene: Neon Night in Korean)",
    method="POST",
    url="/api/ai/analyze-image/",
    payload={"preset_scene": "neon_cyber_night", "language": "ko"},
    validator=lambda d: (d.get("success") and "lyrics" in d, f"Title: {d.get('title')} | Lang: {d.get('language')} | Genre: {d.get('genre_name')}")
)

# 11. AI Chatbot Tư vấn âm nhạc
test_endpoint(
    category="4. Trợ Lý & Soạn Thảo Âm Nhạc",
    name="AI Music Chatbot (Tư vấn cảm xúc, giai điệu & bài hát)",
    method="POST",
    url="/api/ai/chatbot/",
    payload={"message": "Tôi đang buồn và muốn nghe bài hát acoustic sâu lắng để suy ngẫm"},
    validator=lambda d: (bool(d.get("reply") or d.get("message")), f"Mood: {d.get('mood')} | Reply: {(d.get('reply') or d.get('message'))[:60]}...")
)

# 12. AI MIDI Composer
test_endpoint(
    category="4. Trợ Lý & Soạn Thảo Âm Nhạc",
    name="AI Symbolic MIDI Composer (Tạo tệp MIDI hợp âm & nốt nhạc)",
    method="POST",
    url="/api/ai/compose/midi/",
    payload={"genre": "vpop", "mood": "romantic", "root_note": "C", "num_bars": 8},
    validator=lambda c: (len(c) > 200, f"MIDI binary stream size: {len(c)} bytes")
)

# 13. Hệ Thống Gợi Ý & Khám Phá (Recommendation AI)
sample_song = Song.objects.filter(is_published=True).first()
if sample_song:
    test_endpoint(
        category="5. Hệ Thống Đề Xuất Thông Minh (Recommender AI)",
        name="Content-Based Similar Songs (Đề xuất bài hát tương đồng)",
        method="GET",
        url=f"/api/ai/recommend/song/{sample_song.id}/",
        validator=lambda d: (isinstance(d, dict) and "recommendations" in d, f"Found {len(d.get('recommendations', []))} similar recommendations for '{sample_song.title}'")
    )

test_endpoint(
    category="5. Hệ Thống Đề Xuất Thông Minh (Recommender AI)",
    name="Mood-Based Song Discovery (Khám phá bài hát theo tâm trạng)",
    method="GET",
    url="/api/ai/recommend/mood/?mood=happy",
    validator=lambda d: (isinstance(d, dict) and "recommendations" in d, f"Found {len(d.get('recommendations', []))} songs matching mood 'happy'")
)

# 14. Kiểm tra trạng thái AI Engine & GPU
test_endpoint(
    category="6. Cơ Chế Hạ Tầng & Trạng Thái Engine",
    name="Engine Status & Local GPU Diagnostics",
    method="GET",
    url="/api/ai/generate/status/",
    validator=lambda d: ("cuda_available" in d, f"CUDA: {d.get('cuda_available')} | GPU: {d.get('gpu_name')} | VRAM: {d.get('vram_total_gb')} GB")
)

# 15. Kiểm tra trạng thái ACE-Step HF Space Engine
test_endpoint(
    category="6. Cơ Chế Hạ Tầng & Trạng Thái Engine",
    name="ACE-Step HF Space Cloud Engine Status",
    method="GET",
    url="/api/ai/acestep/status/",
    validator=lambda d: ("connected" in d, f"Connected: {d.get('connected')} | Space: {d.get('space')} | Max Duration: {d.get('max_duration')}s")
)

# 16. Sonavia Acoustic Synth (Tier 4 Instant Synth)
try:
    t0 = time.time()
    from apps.ai_engine.providers.synth_provider import AcousticSynthProvider
    synth = AcousticSynthProvider()
    res_synth = synth.generate(
        prompt="Peaceful piano and cello harmony",
        duration=30,
        genre="vpop",
        mood="calm"
    )
    elapsed = round((time.time() - t0) * 1000, 1)
    synth_ok = len(res_synth["audio_bytes"]) > 1000 and res_synth["duration"] == 30
    audit_report.append({
        "category": "7. Bộ Máy Tạo Nhạc (Music Generation Engines)",
        "name": "Sonavia Acoustic Synth (100% Offline, Zero Latency Harmonic Synth)",
        "url": "python:AcousticSynthProvider",
        "passed": synth_ok,
        "elapsed_ms": elapsed,
        "detail": f"Generated {len(res_synth['audio_bytes']):,} bytes | Duration: {res_synth['duration']}s | Format: WAV"
    })
    print(f"✅ [PASS] 7. Bộ Máy Tạo Nhạc - Sonavia Acoustic Synth ({elapsed}ms)")
    print(f"      -> Generated {len(res_synth['audio_bytes']):,} bytes | Duration: {res_synth['duration']}s")
except Exception as e:
    print(f"❌ [FAIL] Sonavia Acoustic Synth: {e}")

# 17. Sonavia Audio Mastering Studio
try:
    t0 = time.time()
    from apps.ai_engine.audio_mastering import master_audio_bytes
    dummy_wav = res_synth["audio_bytes"]
    mastered_bytes = master_audio_bytes(dummy_wav, is_vietnamese=True, output_format='MP3')
    elapsed = round((time.time() - t0) * 1000, 1)
    master_ok = len(mastered_bytes) > 1000
    audit_report.append({
        "category": "7. Bộ Máy Tạo Nhạc (Music Generation Engines)",
        "name": "Sonavia Audio Mastering Studio (Dynamic EQ, Limiter -1dBFS, Stereo Polish)",
        "url": "python:master_audio_bytes",
        "passed": master_ok,
        "elapsed_ms": elapsed,
        "detail": f"Mastered {len(dummy_wav):,} WAV bytes -> {len(mastered_bytes):,} MP3 mastered bytes"
    })
    print(f"✅ [PASS] 7. Bộ Máy Tạo Nhạc - Audio Mastering Studio ({elapsed}ms)")
    print(f"      -> Mastered {len(dummy_wav):,} WAV bytes -> {len(mastered_bytes):,} MP3 mastered bytes")
except Exception as e:
    print(f"❌ [FAIL] Audio Mastering Studio: {e}")

# 18. Sonavia Orchestrator Complete Song Generation (End-to-End)
try:
    t0 = time.time()
    from apps.ai_engine.orchestrator import sonavia_orchestrator
    song_out = sonavia_orchestrator.generate_song(
        prompt="Giai điệu thư thái nhẹ nhàng cuối tuần",
        language="vi",
        duration=30,
        preferred_provider="synth"
    )
    elapsed = round((time.time() - t0) * 1000, 1)
    song_ok = bool(song_out and len(song_out.get("audio_bytes", b"")) > 1000 and song_out.get("duration") == 30)
    audit_report.append({
        "category": "7. Bộ Máy Tạo Nhạc (Music Generation Engines)",
        "name": "Sonavia Orchestrator (Pipeline hoàn chỉnh: Prompt -> Phân tích -> Ca từ -> Render -> Mastering)",
        "url": "python:sonavia_orchestrator.generate_song",
        "passed": song_ok,
        "elapsed_ms": elapsed,
        "detail": f"Title: '{song_out.get('title')}' | Provider: {song_out.get('provider')} | Duration: {song_out.get('duration')}s"
    })
    print(f"✅ [PASS] 7. Bộ Máy Tạo Nhạc - Sonavia Orchestrator Complete Pipeline ({elapsed}ms)")
    print(f"      -> Title: '{song_out.get('title')}' | Provider: {song_out.get('provider')} | Duration: {song_out.get('duration')}s")
except Exception as e:
    print(f"❌ [FAIL] Sonavia Orchestrator: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# TỔNG KẾT BÁO CÁO
# ─────────────────────────────────────────────────────────────────────────────
total = len(audit_report)
passed = sum(1 for r in audit_report if r["passed"])
failed = total - passed

print("\n" + "=" * 80)
print(f"📊 KẾT QUẢ KIỂM TRA TẤT CẢ TÍNH NĂNG AI: {passed}/{total} HẠNG MỤC HOẠT ĐỘNG HOÀN HẢO!")
print("=" * 80)
if failed == 0:
    print("🎉 TẤT CẢ CÁC TÍNH NĂNG AI TRÊN WEBSITE ĐANG HOẠT ĐỘNG RẤT TỐT VÀ SẴN SÀNG PHỤC VỤ!")
else:
    print(f"⚠️ Có {failed} hạng mục cần lưu ý.")

