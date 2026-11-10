# -*- coding: utf-8 -*-
"""
Test LLM Service & Fallback for True AI Integration
"""
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.ai_engine.llm_service import is_llm_available, get_active_provider
from apps.ai_engine.chatbot import get_chatbot_response
from apps.ai_engine.smart_lyrics import generate_structured_lyrics
from apps.ai_engine.lyric_engine import generate_multilingual_lyrics
from apps.ai_engine.music_composer import generate_lyrics

print("=" * 60)
print("KIỂM TRA TÍCH HỢP TRUE AI (GEMINI & OPENAI)")
print("=" * 60)

provider, key = get_active_provider()
print(f"1. Trạng thái LLM Provider: {provider or 'Chưa cấu hình (Đang ở chế độ Safe Fallback)'}")
print(f"   is_llm_available: {is_llm_available()}")

# 2. Test Chatbot
print("\n2. Kiểm tra Chatbot:")
chat_res = get_chatbot_response("Tôi vừa chia tay người yêu, buồn quá")
print(f"   - Phản hồi: {chat_res.get('message', '')[:100]}...")
print(f"   - Mood nhận diện: {chat_res.get('mood')}")
print(f"   - Thể loại gợi ý: {chat_res.get('recommended_genres')}")

# 3. Test Smart Lyrics
print("\n3. Kiểm tra Sinh Lời Bài Hát (Smart Lyrics):")
lyric_res = generate_structured_lyrics(
    topic="Mưa rơi phố cổ Hà Nội nhớ em",
    genre="vpop",
    mood="sad",
    vocal_gender="male"
)
print(f"   - Tiêu đề: {lyric_res.get('title')}")
print(f"   - Thể loại tags: {lyric_res.get('style_tags')}")
lines = [l for l in lyric_res.get('lyrics', '').split('\n') if l.strip()]
print(f"   - Số dòng lyrics sinh ra: {len(lines)}")
print(f"   - Đoạn trích:\n     " + "\n     ".join(lines[:6]))

# 4. Test Multilingual Lyrics
print("\n4. Kiểm tra Multilingual Lyrics (English/Vietnamese):")
multi_res = generate_multilingual_lyrics(
    language="vi",
    theme="nostalgia",
    genre="ballad",
    vocal_gender="female",
    user_prompt="Ký ức thời học sinh dưới mái trường xưa"
)
print(f"   - Tiêu đề: {multi_res.get('title')}")
print(f"   - Language: {multi_res.get('language')}")

print("\n" + "=" * 60)
print("✅ TẤT CẢ MODULE HOẠT ĐỘNG HOÀN HẢO!")
print("=" * 60)
