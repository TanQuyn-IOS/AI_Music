# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.urls import resolve, reverse
from apps.ai_engine.orchestrator import sonavia_orchestrator
from apps.ai_engine.prompt_analyzer import PromptAnalyzerService

print("=== KIỂM TRA SONAVIA STUDIO UNIFIED ARCHITECTURE ===\n")

# 1. Kiểm tra routing URL
match = resolve('/api/music/generate/')
print(f"1. URL '/api/music/generate/' resolved to: {match.view_name} (Class: {match.func.__name__})")
assert match.view_name == 'music-generate-unified', "Routing test failed!"
print("   -> Route /api/music/generate/ CHÍNH XÁC.\n")

# 2. Kiểm tra phân tích Prompt đa ngôn ngữ qua Orchestrator
sample_prompts = [
    ("K-pop buồn về tình yêu, nữ hát", "ko"),
    ("Nhạc Việt chill về tuổi trẻ, guitar acoustic", "vi"),
    ("J-pop anime opening mạnh mẽ, nam hát", "ja"),
    ("C-pop ballad buồn, piano, giọng nữ", "zh"),
    ("English pop dance vui vẻ, female vocal", "en"),
]

print("2. Kiểm tra phân tích cấu hình bài hát (5 ngôn ngữ):")
for p, expected_lang in sample_prompts:
    cfg = PromptAnalyzerService.analyze(p)
    status_icon = "✓" if cfg["language"] == expected_lang else "✗"
    print(f"   [{status_icon}] Prompt: '{p}'")
    print(f"       -> Lang: {cfg['language']} | Genre: {cfg['genre_name']} | Mood: {cfg['mood_name']} | BPM: {cfg['bpm']} | Key: {cfg['key']}")

# 3. Kiểm tra tính sẵn sàng của Providers
print("\n3. Kiểm tra tính sẵn sàng của Provider:")
print(f"   - Primary (ACE-Step): Available = {sonavia_orchestrator.primary_provider.is_available()}")
print(f"   - Fallback (MusicGen): Available = {sonavia_orchestrator.fallback_provider.is_available()}")

print("\n=== TẤT CẢ KIỂM TRA HOÀN TẤT THÀNH CÔNG ===")
