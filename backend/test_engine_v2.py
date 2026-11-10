# -*- coding: utf-8 -*-
import sys
import os

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

DIVIDER = "=" * 65

def test_section(title):
    print()
    print(DIVIDER)
    print(f"  {title}")
    print(DIVIDER)


# ── TEST 1: PROMPT ANALYZER ────────────────────────────────────────────────────
test_section("TEST 1: PROMPT ANALYZER — 5 NGON NGU")
from apps.ai_engine.prompt_analyzer import PromptAnalyzerService

test_cases = [
    {
        "prompt": "K-pop buon ve tinh yeu, nu hat",
        "expect_lang": "ko",
        "expect_vocal": "female",
        "label": "Korean K-pop",
    },
    {
        "prompt": "Nhac Viet chill ve tuoi tre",
        "expect_lang": "vi",
        "expect_vocal": "female",
        "label": "Vietnamese Chill",
    },
    {
        "prompt": "Japanese anime opening manh me",
        "expect_lang": "ja",
        "expect_vocal": "female",
        "label": "Japanese Anime",
    },
    {
        "prompt": "Chinese emotional ballad",
        "expect_lang": "zh",
        "expect_vocal": "female",
        "label": "Chinese Ballad",
    },
    {
        "prompt": "English summer dance pop",
        "expect_lang": "en",
        "expect_vocal": "female",
        "label": "English Pop",
    },
]

all_pass = True
for tc in test_cases:
    cfg = PromptAnalyzerService.analyze(prompt=tc["prompt"])
    lang_ok  = cfg["language"]     == tc["expect_lang"]
    vocal_ok = cfg["vocal_gender"] == tc["expect_vocal"]
    status   = "PASS" if lang_ok and vocal_ok else "FAIL"
    if not (lang_ok and vocal_ok):
        all_pass = False
    print(f"  [{status}] {tc['label']}")
    print(f"         Prompt: {tc['prompt']}")
    print(f"         Lang: {cfg['language']} ({'OK' if lang_ok else 'FAIL - expected ' + tc['expect_lang']})")
    print(f"         Vocal: {cfg['vocal_gender']} ({'OK' if vocal_ok else 'FAIL'})")
    print(f"         Genre: {cfg['genre']} | BPM: {cfg['bpm']} | Mood: {cfg['mood']}")
    print(f"         Key: {cfg['key']}")
    print()

print(f"  Prompt Analyzer: {'ALL PASS' if all_pass else 'SOME FAIL'}")


# ── TEST 2: CAPTION BUILDER ────────────────────────────────────────────────────
test_section("TEST 2: CAPTION BUILDER — PROMPT EXPANSION")
from apps.ai_engine.caption_builder import build_rich_caption

cfg_ko = PromptAnalyzerService.analyze("K-pop buon ve tinh yeu, nu hat")
print("  Input: 'K-pop buon ve tinh yeu, nu hat'")
print()
for quality in ("fast", "balanced", "high"):
    cap = build_rich_caption(cfg_ko, quality=quality)
    print(f"  [{quality.upper()}] Caption length: {len(cap)} chars")
    print(f"  Preview: {cap[:200]}")
    print()


# ── TEST 3: LYRIC ENGINE ───────────────────────────────────────────────────────
test_section("TEST 3: LYRIC ENGINE — 5 NGON NGU")
from apps.ai_engine.lyric_engine import generate_multilingual_lyrics

lang_tests = [
    ("vi", "sad",      "vpop", "female", "Vietnamese Sad"),
    ("ko", "sad",      "kpop", "female", "Korean Sad"),
    ("ja", "energy",   "jpop", "female", "Japanese Energy"),
    ("zh", "romantic", "cpop", "female", "Chinese Romantic"),
    ("en", "happy",    "pop",  "female", "English Happy"),
]
for lang, theme, genre, vocal, label in lang_tests:
    result = generate_multilingual_lyrics(
        language=lang, theme=theme, genre=genre, vocal_gender=vocal
    )
    has_chorus = "[Chorus]" in result["lyrics"] or "[chorus]" in result["lyrics"]
    has_verse  = "[Verse" in result["lyrics"]
    has_bridge = "[Bridge]" in result["lyrics"] or "[bridge]" in result["lyrics"]
    print(f"  [{lang.upper()}] {label}")
    print(f"         Title: {result['title']}")
    print(f"         Chorus: {'YES' if has_chorus else 'NO'} | Verse: {'YES' if has_verse else 'NO'} | Bridge: {'YES' if has_bridge else 'NO'}")
    print(f"         Length: {len(result['lyrics'])} chars")
    # Show first few lines
    preview_lines = result["lyrics"].split("\n")[:5]
    for line in preview_lines:
        if line.strip():
            print(f"         | {line}")
    print()


# ── TEST 4: QUALITY PRESETS ────────────────────────────────────────────────────
test_section("TEST 4: QUALITY PRESETS")
from apps.ai_engine.acestep_generator import QUALITY_PRESETS, GENRE_AUTO_DURATION

print("  PRESETS:")
for name, preset in QUALITY_PRESETS.items():
    print(f"  [{name.upper()}]")
    print(f"    infer_step={preset['infer_step']}")
    print(f"    guidance_scale={preset['guidance_scale']}")
    print(f"    guidance_scale_lyric={preset['guidance_scale_lyric']}")
    print(f"    guidance_scale_text={preset['guidance_scale_text']}")
    print(f"    Description: {preset['description']}")

print()
print("  AUTO DURATION PER GENRE:")
for genre, dur in GENRE_AUTO_DURATION.items():
    mins = dur // 60
    secs = dur % 60
    print(f"    {genre:12s}: {dur}s ({mins}:{secs:02d})")


# ── SUMMARY ────────────────────────────────────────────────────────────────────
test_section("SUMMARY")
print("  MODEL:           ACE-Step (HF Space: ACE-Step/ACE-Step)")
print("  LM:              ACE-Step built-in ERG (tag/lyric/diffusion)")
print("  DIFFUSION MODEL: ACE-Step DiT")
print()
print("  QUALITY PRESETS:")
print("    FAST    — infer=40, guidance=12.0, lyric_guidance=1.5")
print("    BALANCED— infer=60, guidance=14.0, lyric_guidance=2.0")
print("    HIGH    — infer=75, guidance=16.0, lyric_guidance=2.5, text_guidance=1.0")
print()
print("  PROMPT PIPELINE:")
print("    User Prompt → PromptAnalyzerService.analyze() → SongConfig")
print("    SongConfig  → CaptionBuilder.build_rich_caption() → Rich Caption")
print("    SongConfig  → LyricEngine.generate_multilingual_lyrics() → Lyrics")
print()
print("  LYRIC PIPELINE:")
print("    Language: vi/ko/ja/zh/en auto-detected")
print("    Theme: love/sad/chill/energy/nostalgia/breakup")
print("    Structure: Intro→Verse1→PreChorus→Chorus→Verse2→Bridge→FinalChorus→Outro")
print()
print("  VOCAL PIPELINE:")
print("    Vocal gender: female/male/duet/instrumental")
print("    Language-specific vocal style embedded in caption")
print("    No TTS — vocal generated inside ACE-Step DiT")
print()
print("  AUDIO PIPELINE:")
print("    ACE-Step → MP3 48kHz → Audio validation → Save to media/generated/")
print()
print("  FILES CHANGED:")
print("    + caption_builder.py (NEW)")
print("    ~ acestep_generator.py (QUALITY_PRESETS, auto-duration, rich caption)")
print("    ~ providers/acestep_provider.py (quality, song_config params)")
print("    ~ views.py (SmartGenerateView: quality param, pipeline logging)")
print("    ~ lyric_engine.py (Pre-chorus content, Final Chorus)")
print()
print("  NOTE: ACE-Step server test requires network connection to HF Space.")
print("        Run backend server và POST to /api/ai/generate/smart/ to test end-to-end.")
