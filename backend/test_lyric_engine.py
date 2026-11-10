# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from apps.ai_engine.prompt_analyzer import PromptAnalyzerService
from apps.ai_engine.lyric_engine import generate_multilingual_lyrics

TESTS = [
    "K-pop buon ve tinh yeu, nu hat",
    "Nhac Viet chill ve tuoi tre, guitar acoustic",
    "J-pop anime opening manh me, nam hat",
    "C-pop ballad buon, piano, giong nu",
    "English pop dance vui ve, female vocal",
]

print("=== TEST LYRIC ENGINE (5 LANGUAGES) ===\n")
for prompt in TESTS:
    c = PromptAnalyzerService.analyze(prompt)
    r = generate_multilingual_lyrics(
        language=c["language"],
        theme=c["theme"],
        genre=c["genre"],
        vocal_gender=c["vocal_gender"],
    )
    lang = c["language"]
    genre = c["genre"]
    theme = c["theme"]
    title = r["title"]
    snippet = r["lyrics"][:80].replace("\n", " | ")
    print(f"[{lang}] genre={genre:8} theme={theme:10} title={title}")
    print(f"       lyrics: {snippet}...")
    print()

print("=== ALL PASSED ===")
