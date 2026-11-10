# -*- coding: utf-8 -*-
import os
import sys
import time

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import django
django.setup()

print("=" * 60)
print("🧪 KIỂM TRA TOÀN DIỆN CÁC TÍNH NĂNG AI TRONG HỆ THỐNG")
print("=" * 60)

# 1. Prompt Analyzer AI
print("\n[1/7] Kiểm tra AI Phân Tích Prompt (Prompt Analyzer):")
try:
    from apps.ai_engine.prompt_analyzer import PromptAnalyzerService
    res = PromptAnalyzerService.analyze("Nhạc pop buồn về mưa rơi lúc hoàng hôn, nữ hát")
    print(f"  ✅ Hoạt động tốt! Kết quả:")
    print(f"     - Ngôn ngữ: {res['language']}")
    print(f"     - Thể loại: {res['genre']} ({res['genre_name']})")
    print(f"     - Tâm trạng: {res['mood']} ({res['mood_name']})")
    print(f"     - Giọng hát: {res['vocal_gender']}")
    print(f"     - BPM: {res['bpm']} | Key: {res['key']}")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

# 2. Lyric Engine AI
print("\n[2/7] Kiểm tra AI Sáng Tác Lời Bài Hát (Lyric Engine):")
try:
    from apps.ai_engine.lyric_engine import generate_multilingual_lyrics
    res = generate_multilingual_lyrics(
        language="vi", theme="sad", genre="vpop", vocal_gender="female",
        user_prompt="Nhạc pop buồn về mưa rơi lúc hoàng hôn"
    )
    print(f"  ✅ Hoạt động tốt! Tiêu đề: '{res['title']}' ({len(res['lyrics'])} ký tự)")
    preview = res['lyrics'].split('\n')[:4]
    for line in preview:
        print(f"     | {line}")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

# 3. Image Synesthesia AI (Image to Music)
print("\n[3/7] Kiểm tra AI Phân Tích Hình Ảnh Sang Âm Nhạc (Image Analyzer):")
try:
    from apps.ai_engine.image_analyzer import ImageToMusicAnalyzer
    from PIL import Image
    # Tạo một ảnh test màu hoàng hôn (cam/đỏ)
    test_img = Image.new('RGB', (100, 100), color=(220, 100, 50))
    res = ImageToMusicAnalyzer.analyze_image(test_img)
    print(f"  ✅ Hoạt động tốt! Kết quả phân tích ảnh:")
    print(f"     - Mood nhận diện: {res.get('mood_name')} ({res.get('mood')})")
    print(f"     - Thể loại gợi ý: {res.get('genre_name')} ({res.get('genre')})")
    print(f"     - BPM gợi ý: {res.get('bpm')} | Key: {res.get('key')}")
    print(f"     - Không gian (Atmosphere): {res.get('atmosphere')}")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

# 4. Chatbot AI
print("\n[4/7] Kiểm tra AI Chatbot Tư Vấn Âm Nhạc (Chatbot):")
try:
    from apps.ai_engine.chatbot import get_chatbot_response
    res = get_chatbot_response("Hôm nay tôi thấy hơi buồn và mệt mỏi, gợi ý bài hát cho tôi với")
    print(f"  ✅ Hoạt động tốt! Phản hồi Chatbot:")
    print(f"     - Mood nhận diện: {res.get('mood')}")
    print(f"     - Câu trả lời: {res.get('message')}")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

# 5. Recommendation AI
print("\n[5/7] Kiểm tra AI Đề Xuất (Recommender - Cosine Similarity):")
try:
    from apps.music.models import Song
    from apps.ai_engine.recommender import get_content_based_recommendations, get_mood_based_recommendations
    all_songs = list(Song.objects.filter(is_published=True))
    if all_songs:
        target = all_songs[0]
        recs = get_content_based_recommendations(target, all_songs, top_n=3)
        print(f"  ✅ Hoạt động tốt! Tìm thấy {len(all_songs)} bài trong DB.")
        print(f"     - Đề xuất tương tự cho '{target.title}': {[s.title for s in recs]}")
    else:
        print("  ⚠️ DB chưa có bài hát, cần seed_data.")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

# 6. MIDI Composer AI
print("\n[6/7] Kiểm tra AI Soạn Nhạc MIDI 3 Track (Music Composer):")
try:
    from apps.ai_engine.music_composer import generate_midi
    midi_bytes = generate_midi(
        genre="pop", mood="happy", root_note="C", num_bars=8
    )
    print(f"  ✅ Hoạt động tốt! Đã tạo file MIDI {len(midi_bytes):,} bytes (3 tracks: piano chords, melody, bass)")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

# 7. Local Deep Learning MusicGen AI (Meta AudioCraft/Transformers trên GPU)
print("\n[7/7] Kiểm tra Mô hình AI Sinh Âm Thanh (Meta MusicGen trên GPU):")
try:
    import torch
    print(f"     - PyTorch: {torch.__version__} | CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"     - GPU: {torch.cuda.get_device_name(0)}")
    from apps.ai_engine.music_generator import generate_music
    t0 = time.time()
    audio_bytes, dur = generate_music("lofi acoustic guitar chill beat", duration=5)
    print(f"  ✅ Hoạt động thực sự! Đã tạo ra file âm thanh {len(audio_bytes):,} bytes ({dur}s) trong {time.time()-t0:.1f}s.")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")

print("\n" + "=" * 60)
print("🎉 KIỂM TRA HOÀN TẤT!")
print("=" * 60)
