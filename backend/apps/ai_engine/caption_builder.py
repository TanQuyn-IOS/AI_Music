"""
Sonavia Studio — Caption Builder (Prompt Expansion Layer)
==========================================================
Biến SongConfig dict thành rich caption chi tiết cho ACE-Step.

Input:  SongConfig từ PromptAnalyzerService.analyze()
Output: Chuỗi caption mô tả đầy đủ:
        - Genre / subgenre
        - Vocal (language, gender, style, dynamics)
        - Mood / energy / theme
        - Instrumentation chi tiết
        - Arrangement progression
        - Production style
        - BPM / key context
"""

from typing import Dict, Any

# ── Language → vocal description ──────────────────────────────────────────────
LANG_VOCAL_STYLE = {
    "vi": {
        "female": (
            "Vietnamese female lead vocal, sweet crystal clear singing voice, "
            "crisp articulate Vietnamese diction, distinct syllables, "
            "flawless natural Vietnamese tonal pronunciation, intimate upfront close-mic vocal, "
            "authentic V-Pop delivery, expressive emotional phrasing, clean vowels, resonant presence"
        ),
        "male": (
            "Vietnamese male lead vocal, warm deep singing voice, "
            "crisp articulate Vietnamese diction, distinct syllables, "
            "flawless natural Vietnamese tonal pronunciation, intimate upfront close-mic vocal, "
            "authentic V-Pop delivery, soulful emotional phrasing, clear consonants, resonant presence"
        ),
        "duet": (
            "Vietnamese duet vocals, male and female vocal harmony, "
            "crisp articulate Vietnamese diction, distinct syllables, "
            "flawless natural Vietnamese tonal pronunciation, call-and-response phrasing, "
            "upfront balanced blend, emotional interplay"
        ),
    },
    "ko": {
        "female": (
            "Korean female lead vocal, bright emotive singing, "
            "crisp Korean pronunciation, K-pop style vocal runs, "
            "intimate verse delivery, powerful chorus peak"
        ),
        "male": (
            "Korean male lead vocal, warm smooth tone, "
            "precise Korean pronunciation, expressive K-pop delivery, "
            "controlled falsetto, emotional depth"
        ),
        "duet": (
            "Korean duet vocals, male and female vocal harmony, "
            "crisp Korean pronunciation, K-pop style call-and-response, "
            "emotional interplay, layered harmonies"
        ),
    },
    "ja": {
        "female": (
            "Japanese female lead vocal, bright kawaii-to-powerful range, "
            "clear Japanese pronunciation, J-pop anime vocal style, "
            "energetic delivery, soaring chorus"
        ),
        "male": (
            "Japanese male lead vocal, clear precise pronunciation, "
            "J-pop emotive delivery, dynamic range from soft verse to powerful chorus"
        ),
        "duet": (
            "Japanese duet vocals, male and female vocal blend, "
            "clear Japanese pronunciation, anime OST style, "
            "harmonized chorus, interweaving vocal lines"
        ),
    },
    "zh": {
        "female": (
            "Chinese Mandarin female lead vocal, melodic Mandarin pronunciation, "
            "C-pop emotional ballad style, expressive phrasing, "
            "delicate verses, soaring chorus"
        ),
        "male": (
            "Chinese Mandarin male lead vocal, warm Mandarin pronunciation, "
            "C-pop soulful delivery, lyrical phrasing, resonant tone"
        ),
        "duet": (
            "Chinese Mandarin duet vocals, male and female vocal blend, "
            "melodic Mandarin pronunciation, C-pop romantic style, "
            "intertwined vocal melodies"
        ),
    },
    "en": {
        "female": (
            "English female lead vocal, clear articulate pronunciation, "
            "contemporary pop singing style, expressive dynamics, "
            "intimate verses, powerful chorus"
        ),
        "male": (
            "English male lead vocal, clear articulate pronunciation, "
            "contemporary pop singing style, warm tone, expressive phrasing"
        ),
        "duet": (
            "English duet vocals, male and female vocal harmony, "
            "clear pronunciation, contemporary pop style, "
            "call-and-response sections, blended chorus harmonies"
        ),
    },
}

# ── Genre → arrangement description ───────────────────────────────────────────
GENRE_ARRANGEMENT = {
    "vpop": (
        "warm piano intro, gentle acoustic guitar, soft synth pads, "
        "emotional string swells, restrained kick and hi-hat, deep sub bass, "
        "intimate verse arrangement, rising pre-chorus tension, "
        "fuller layered chorus with strings and synths"
    ),
    "kpop": (
        "catchy synth hook intro, modern 808 bass, tight electronic drums, "
        "polished synth leads, bright layered production, "
        "intimate rap-style verse, snappy pre-chorus build, "
        "explosive wide chorus with layered synths, "
        "optional dance-break with minimal percussion"
    ),
    "jpop": (
        "energetic electric guitar intro, fast driving drums, "
        "melodic bass guitar, bright piano chords, soaring synth lead, "
        "dynamic verse-chorus contrast, guitar solo interlude, "
        "anthemic chorus with full band arrangement"
    ),
    "cpop": (
        "atmospheric erhu or guzheng intro, cinematic string swell, "
        "piano accompaniment, soft traditional percussion, "
        "poetic verse with sparse arrangement, "
        "emotional chorus with full string orchestra, "
        "cultural fusion production"
    ),
    "pop": (
        "catchy melodic intro, acoustic guitar and piano, "
        "four-on-the-floor drums, punchy bass, "
        "bright synth pads in chorus, layered backing vocals, "
        "radio-friendly production"
    ),
    "ballad": (
        "solo grand piano intro, gradual string orchestra entry, "
        "sparse verse with piano only, warm bass enters pre-chorus, "
        "full orchestral chorus, intimate bridge with solo piano return, "
        "powerful final chorus with full arrangement"
    ),
    "lofi": (
        "vinyl crackle texture, rhodes electric piano, "
        "mellow jazz guitar, dusty lo-fi drums, "
        "rain ambient sounds, warm tape saturation, "
        "cozy lo-pass filtered production, relaxing loop-based structure"
    ),
    "rnb": (
        "smooth groove intro, deep 808 bass, "
        "rhodes piano, finger snaps, "
        "silky synth chords, spacious reverb, "
        "soulful chord stabs, contemporary R&B production"
    ),
    "hip_hop": (
        "hard-hitting 808 bass intro, hi-hat rolls, "
        "punchy snare, dark synth lead, bell melody, "
        "trap-style production, rhythmic flow arrangement, "
        "punchy low-end, crisp percussion"
    ),
    "rock": (
        "overdriven electric guitar intro, crash cymbals, "
        "driving rhythm section, bass guitar, "
        "power chord verse, anthemic chorus with full band, "
        "guitar solo breakdown, raw live energy"
    ),
    "edm": (
        "atmospheric intro build, rising synth arpeggio, "
        "kick drum four-on-floor, punchy saw lead, "
        "massive bass drop, sidechain pump compression, "
        "wide stereo production, breakdown with chords, "
        "second drop with variation, euphoric outro"
    ),
    "acoustic": (
        "fingerpicked acoustic guitar intro, "
        "warm room acoustics, cajon or shaker, "
        "upright bass, natural intimate production, "
        "stripped-back arrangement throughout"
    ),
    "jazz": (
        "saxophone or piano jazz intro, walking upright bass, "
        "brushed snare drums, warm chord voicings, "
        "improvised feel, vintage studio warmth"
    ),
    "cinematic": (
        "orchestral string swell intro, French horns, "
        "choir pads, timpani, piano lead, "
        "epic dynamic build, dramatic brass stabs in chorus, "
        "grand orchestral production"
    ),
}

# ── Mood → emotional production description ────────────────────────────────────
MOOD_PRODUCTION = {
    "sad": (
        "melancholic atmosphere, minor key emotional color, "
        "delicate reverb on vocals, subtle underscore tension, "
        "gradually building emotional intensity toward chorus"
    ),
    "happy": (
        "bright uplifting energy, major key warm color, "
        "sparkling high-frequency production, feel-good momentum, "
        "joyful arrangement"
    ),
    "chill": (
        "relaxed laid-back groove, warm low-pass textures, "
        "smooth unhurried flow, cozy intimate atmosphere, "
        "soft dynamic range"
    ),
    "energetic": (
        "high energy driving production, punchy transients, "
        "wide dynamic contrast, explosive peak moments, "
        "powerful momentum throughout"
    ),
    "romantic": (
        "warm intimate atmosphere, gentle romantic color, "
        "lush reverb on vocals, tender emotional phrasing, "
        "sweeping melodic lines"
    ),
    "nostalgic": (
        "bittersweet nostalgic atmosphere, warm vintage color, "
        "soft glow production, reflective emotional tone, "
        "gentle dynamic swells"
    ),
}

# ── Vocal dynamics per structure section ──────────────────────────────────────
VOCAL_DYNAMICS_DESCRIPTION = (
    "intimate controlled vocal in verses, increasing tension in pre-chorus, "
    "stronger wider emotional delivery in chorus, "
    "dynamic variation in bridge, strongest emotional peak in final chorus"
)

# ── Quality preset → production suffix ────────────────────────────────────────
QUALITY_PRODUCTION_TAG = {
    "fast":    "clean studio recording",
    "balanced": "polished studio production, balanced mix",
    "high":    "professional studio master, pristine stereo mix, "
               "full frequency range, natural dynamic range",
}


def build_rich_caption(config: Dict[str, Any], quality: str = "balanced") -> str:
    """
    Tạo rich caption chi tiết cho ACE-Step từ SongConfig.

    Args:
        config:  Output của PromptAnalyzerService.analyze()
        quality: 'fast' | 'balanced' | 'high'

    Returns:
        Caption string đầy đủ cho ACE-Step prompt field.
    """
    lang          = config.get("language", "vi")
    genre_key     = config.get("genre", "pop")
    mood_key      = config.get("mood", "happy")
    vocal_gender  = config.get("vocal_gender", "female")
    bpm           = config.get("bpm", 100)
    key           = config.get("key", "C Major")
    genre_name    = config.get("genre_name", "Pop")
    subgenre      = config.get("subgenre", "")
    production    = config.get("production_style", "")
    energy        = config.get("energy", "medium")

    parts = []

    # 1. Genre / subgenre
    if subgenre:
        parts.append(f"{genre_name}, {subgenre}")
    else:
        parts.append(genre_name)

    # 2. Vocal (language + gender + style)
    if vocal_gender != "instrumental":
        lang_vocals = LANG_VOCAL_STYLE.get(lang, LANG_VOCAL_STYLE["en"])
        vocal_desc = lang_vocals.get(vocal_gender, lang_vocals.get("female", ""))
        parts.append(vocal_desc)
    else:
        parts.append("instrumental, no vocals, expressive melodic lead instruments")

    # 3. Mood / atmosphere
    mood_prod = MOOD_PRODUCTION.get(mood_key, "")
    if mood_prod:
        parts.append(mood_prod)

    # 4. Arrangement
    arrangement = GENRE_ARRANGEMENT.get(genre_key, GENRE_ARRANGEMENT.get("pop", ""))
    if arrangement:
        parts.append(arrangement)

    # 5. BPM hint (helps model set pace)
    parts.append(f"{bpm} BPM, {key}")

    # 6. Vocal dynamics (for singing songs)
    if vocal_gender != "instrumental":
        parts.append(VOCAL_DYNAMICS_DESCRIPTION)

    # 7. Production style from genre DB
    if production:
        parts.append(production)

    # 8. Quality tag
    quality_lower = quality.lower() if quality else "balanced"
    quality_tag = QUALITY_PRODUCTION_TAG.get(quality_lower, QUALITY_PRODUCTION_TAG["balanced"])
    parts.append(quality_tag)

    # 9. Clarity & articulation reinforcement
    parts.append(build_negative_hints(genre_key))

    return ", ".join(p.strip() for p in parts if p.strip())


def build_negative_hints(genre_key: str = "pop") -> str:
    """
    Tạo các quality hints (ACE-Step không có explicit negative prompt,
    nhưng ta có thể dùng positive quality reinforcement).
    """
    return (
        "clear vocal articulation, no distortion, no clipping, "
        "no abrupt ending, complete song structure, "
        "no robotic vocal artifacts, natural breathing phrasing"
    )
