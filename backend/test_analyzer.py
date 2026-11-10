# -*- coding: utf-8 -*-
import sys
import os

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from apps.ai_engine.prompt_analyzer import PromptAnalyzerService

test_prompts = [
    "K-pop buồn về tình yêu, nữ hát",
    "Nhạc Việt chill về tuổi trẻ, guitar acoustic",
    "J-pop anime opening mạnh mẽ, nam hát",
    "C-pop ballad buồn, piano, giọng nữ",
    "English pop dance vui vẻ, female vocal",
    "사랑을 잃은 슬픈 노래",
    "夏の恋についての曲",
    "一首关于青春的流行歌曲",
    "Sad song about losing someone",
    "Buồn",
    "Kpop",
    "anime opening",
    "nhạc chill để học",
]

print("=== TEST PROMPT ANALYZER (5 LANGUAGES & SHORT PROMPTS) ===")
for p in test_prompts:
    res = PromptAnalyzerService.analyze(p)
    print(f"{p:<45} | Lang: {res['language']:<2} | Genre: {res['genre_name']:<12} | Vocal: {res['vocal_gender']:<10} | {res['bpm']} BPM | Key: {res['key']}")
