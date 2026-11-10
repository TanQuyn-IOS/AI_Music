"""
AI Music Composer
=================
Tự động sáng tác nhạc gồm:
  1. Tạo chord progression (lý thuyết nhạc lý)
  2. Tạo giai điệu melody
  3. Tạo lời bài hát (Markov Chain + template)
  4. Xuất file MIDI
"""
import random
import io
import re
from collections import defaultdict
from midiutil import MIDIFile

# ─── Nhạc lý cơ bản ─────────────────────────────────────────────────────────

# Tên các nốt nhạc
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Khoảng cách bán cung của từng bậc trong gamme
SCALE_INTERVALS = {
    'major':      [0, 2, 4, 5, 7, 9, 11],
    'minor':      [0, 2, 3, 5, 7, 8, 10],
    'pentatonic': [0, 2, 4, 7, 9],
    'blues':      [0, 3, 5, 6, 7, 10],
    'dorian':     [0, 2, 3, 5, 7, 9, 10],
}

# Chord intervals (root, third, fifth)
CHORD_TYPES = {
    'major': [0, 4, 7],
    'minor': [0, 3, 7],
    'dim':   [0, 3, 6],
    'aug':   [0, 4, 8],
    'sus2':  [0, 2, 7],
    'sus4':  [0, 5, 7],
    '7':     [0, 4, 7, 10],
    'maj7':  [0, 4, 7, 11],
    'min7':  [0, 3, 7, 10],
}

# Chord progression templates theo thể loại
PROGRESSIONS = {
    'pop':       [[0,5,6,4], [1,4,6,5], [0,4,5,4], [6,4,1,5]],
    'rock':      [[0,6,7,5], [0,3,4,0], [0,7,6,7], [1,6,3,7]],
    'jazz':      [[1,4,0,5], [2,5,1,4], [0,6,2,5], [1,5,0,4]],
    'sad':       [[0,5,3,4], [6,3,4,5], [0,6,4,5], [1,5,6,4]],
    'happy':     [[0,4,5,4], [0,5,4,0], [0,2,5,4], [4,5,3,0]],
    'calm':      [[0,5,3,6], [0,2,4,5], [0,3,5,4], [3,6,2,5]],
    'energetic': [[0,7,6,7], [0,3,5,7], [0,5,6,7], [4,5,6,7]],
    'romantic':  [[0,5,6,4], [0,3,4,5], [1,4,0,5], [6,5,4,3]],
    'blues':     [[0,0,0,0, 4,4,0,0, 5,4,0,5]],
    'kpop':      [[0,5,3,4], [4,5,6,5], [0,4,5,3], [6,5,4,3]],
    'vpop':      [[0,5,6,4], [0,3,4,0], [6,3,4,5], [0,5,4,3]],
    'classical': [[0,4,5,0], [0,3,4,5], [5,4,3,0], [0,2,5,0]],
}

# Mapping mood → key (major/minor)
MOOD_TO_MODE = {
    'happy':      'major',
    'uplifting':  'major',
    'energetic':  'major',
    'romantic':   'major',
    'calm':       'major',
    'sad':        'minor',
    'melancholic':'minor',
    'angry':      'minor',
}

# Tempo theo mood
MOOD_TO_TEMPO = {
    'happy':      128, 'uplifting': 140, 'energetic': 160,
    'romantic':   80,  'calm':       70,  'sad':        65,
    'melancholic': 60,  'angry':     150,
}


def get_scale(root_midi: int, mode: str = 'major') -> list[int]:
    """Trả về danh sách MIDI notes của gamme từ root."""
    intervals = SCALE_INTERVALS.get(mode, SCALE_INTERVALS['major'])
    return [root_midi + i for i in intervals]


def get_chord_notes(root_midi: int, chord_type: str = 'major') -> list[int]:
    """Trả về các nốt của 1 hợp âm."""
    intervals = CHORD_TYPES.get(chord_type, CHORD_TYPES['major'])
    return [root_midi + i for i in intervals]


def build_progression(genre: str, root_midi: int, mode: str = 'major') -> list[list[int]]:
    """Tạo chord progression hoàn chỉnh."""
    templates = PROGRESSIONS.get(genre, PROGRESSIONS['pop'])
    template = random.choice(templates)
    scale = get_scale(root_midi, mode)

    chords = []
    for degree in template:
        if degree >= len(scale):
            degree = degree % len(scale)
        chord_root = scale[degree]
        # Chọn loại chord dựa trên bậc trong gamme
        if mode == 'major':
            chord_types_by_degree = ['major','minor','minor','major','major','minor','dim']
        else:
            chord_types_by_degree = ['minor','dim','major','minor','minor','major','major']
        ctype = chord_types_by_degree[degree % len(chord_types_by_degree)]
        chords.append(get_chord_notes(chord_root, ctype))
    return chords


def generate_melody(scale_notes: list[int], num_bars: int = 8,
                    tempo: int = 120, style: str = 'smooth') -> list[dict]:
    """Tạo giai điệu melody."""
    melody = []
    beat = 0

    # Thêm octave cao hơn cho melody
    melody_scale = scale_notes + [n + 12 for n in scale_notes]
    melody_scale = [n for n in melody_scale if 60 <= n <= 84]  # C4 → C6

    tonic_note = melody_scale[0]
    total_beats = num_bars * 4.0
    note_idx = len(melody_scale) // 2

    while beat < total_beats:
        remaining_beats = total_beats - beat
        if style == 'rhythmic':
            dur_choices = [0.5, 0.5, 1.0, 1.0, 0.25]
        elif style == 'smooth':
            dur_choices = [0.5, 1.0, 1.0, 1.5, 2.0]
        else:
            dur_choices = [0.5, 0.5, 1.0]

        valid_dur = [d for d in dur_choices if d <= remaining_beats]
        duration = random.choice(valid_dur if valid_dur else [remaining_beats])

        step = random.choice([-2, -1, -1, 0, 1, 1, 2, -3, 3])
        note_idx = max(0, min(len(melody_scale) - 1, note_idx + step))
        pitch = melody_scale[note_idx]

        if remaining_beats <= 2.0:
            pitch = tonic_note

        beat_in_bar = beat % 4.0
        if beat_in_bar in (0.0, 2.0):
            base_vol = 95
        elif beat_in_bar in (1.0, 3.0):
            base_vol = 85
        else:
            base_vol = 78

        human_jitter = int(random.gauss(0, 3.5))
        volume = max(60, min(115, base_vol + human_jitter))

        melody.append({
            'pitch': pitch,
            'beat': round(beat, 3),
            'duration': round(duration, 3),
            'volume': volume
        })
        beat += duration

    return melody


def generate_midi(
    genre: str = 'pop',
    mood: str = 'happy',
    root_note: str = 'C',
    num_bars: int = 16,
    bpm: int = None,
    custom_prompt: str = '',
) -> bytes:
    """
    Tạo file MIDI hoàn chỉnh.
    - Ưu tiên: Sử dụng Generative AI Neural Symbolic Music reasoning (Google Gemini)
      để sáng tác hợp âm phức hợp (7th, 9th, sus4), bè dẫn nốt giai điệu polyphonic và bassline sống động.
    - Dự phòng: Tự động fallback sang thuật toán nhạc lý truyền thống.
    """
    # ── 0. THỬ SÁNG TÁC BẰNG GENERATIVE AI NEURAL SYMBOLIC COMPOSER ──
    try:
        from .llm_service import is_llm_available, compose_symbolic_music_with_llm
        if is_llm_available():
            ai_comp = compose_symbolic_music_with_llm(
                genre=genre,
                mood=mood,
                prompt=custom_prompt or f"Bản nhạc {genre} mang sắc thái {mood}",
                num_bars=num_bars
            )
            if ai_comp and ai_comp.get('chords') and ai_comp.get('melody'):
                ai_tempo = ai_comp.get('bpm') or bpm or 110
                midi_ai = MIDIFile(3)
                midi_ai.addTempo(0, 0, ai_tempo)
                midi_ai.addTrackName(0, 0, f"AI Neural - {ai_comp.get('title', genre)} ({mood})")

                # Track 1: AI Polyphonic Chords
                midi_ai.addProgramChange(0, 0, 0, 0)
                for c in ai_comp['chords']:
                    b = float(c.get('beat', 0.0))
                    d = float(c.get('duration', 4.0))
                    for n in c.get('notes', []):
                        midi_ai.addNote(0, 0, int(n), b, d, 75)

                # Track 2: AI Expressive Melody
                midi_ai.addProgramChange(1, 1, 0, 0)
                for m in ai_comp['melody']:
                    p = int(m.get('pitch', 60))
                    b = float(m.get('beat', 0.0))
                    d = float(m.get('duration', 1.0))
                    v = int(m.get('velocity', 90))
                    midi_ai.addNote(1, 1, p, b, d, v)

                # Track 3: AI Counter-Melody Bass
                midi_ai.addProgramChange(2, 2, 0, 33)
                for bs in ai_comp.get('bass', []):
                    p = int(bs.get('pitch', 36))
                    b = float(bs.get('beat', 0.0))
                    d = float(bs.get('duration', 2.0))
                    v = int(bs.get('velocity', 95))
                    midi_ai.addNote(2, 2, p, b, d, v)

                buf_ai = io.BytesIO()
                midi_ai.writeFile(buf_ai)
                return buf_ai.getvalue()
    except Exception:
        pass
    """
    Tạo file MIDI hoàn chỉnh.
    Trả về bytes của file MIDI.
    """
    # Xác định root MIDI number
    root_idx = NOTES.index(root_note) if root_note in NOTES else 0
    root_midi = 48 + root_idx  # C3 = 48

    # Xác định mode và tempo
    mode = MOOD_TO_MODE.get(mood, 'major')
    tempo = bpm or MOOD_TO_TEMPO.get(mood, 120)

    # Tạo scale và chord progression
    scale_notes = get_scale(root_midi, mode)
    chords = build_progression(genre, root_midi, mode)

    # Tạo MIDI file với 3 tracks: chords, melody, bass
    midi = MIDIFile(3)

    # Track 0: Metadata
    midi.addTempo(0, 0, tempo)
    midi.addTrackName(0, 0, f"AI Composed - {genre.title()} ({mood})")

    # Track 1: Chord (Piano - channel 0)
    midi.addProgramChange(0, 0, 0, 0)   # Piano
    chord_beat = 0
    bars_per_chord = max(1, num_bars // len(chords))
    for chord_notes in chords:
        for _ in range(bars_per_chord):
            for note in chord_notes:
                midi.addNote(0, 0, note, chord_beat, 4, 70)
            chord_beat += 4
        if chord_beat >= num_bars * 4:
            break

    # Track 2: Melody (Piano sáng - channel 1)
    midi.addProgramChange(1, 1, 0, 0)   # Piano
    melody_style = 'smooth' if mood in ('sad', 'calm', 'romantic', 'melancholic') else 'rhythmic'
    melody_notes = generate_melody(scale_notes, num_bars, tempo, melody_style)
    for note in melody_notes:
        try:
            midi.addNote(1, 1, note['pitch'], note['beat'], note['duration'], note['volume'])
        except Exception:
            pass

    # Track 3: Bass (Bass Guitar - channel 2)
    midi.addProgramChange(2, 2, 0, 33)  # Electric Bass
    bass_beat = 0
    for chord_notes in chords:
        bass_note = chord_notes[0] - 12  # 1 octave thấp hơn
        bass_note = max(24, bass_note)
        for beat_offset in [0, 2]:
            midi.addNote(2, 2, bass_note, bass_beat + beat_offset, 1.5, 80)
        bass_beat += 4
        if bass_beat >= num_bars * 4:
            break

    # Xuất ra bytes
    buf = io.BytesIO()
    midi.writeFile(buf)
    return buf.getvalue()


# ─── Lyric Generator (Markov Chain + Templates) ──────────────────────────────

# Corpus mẫu theo mood
LYRIC_CORPUS = {
    'happy': [
        "ánh nắng chiếu sáng ngày hôm nay", "nụ cười rạng rỡ trên môi em",
        "trái tim vui hát những giai điệu", "bước chân nhẹ nhàng theo nhịp nhạc",
        "thế giới này thật tươi đẹp biết bao", "yêu cuộc sống từng giây phút này",
        "niềm vui lan tỏa khắp mọi nơi", "hãy cùng nhau ca hát vui vẻ nào",
        "sắc màu rực rỡ đầy trời xanh", "ta cùng nhau vẽ nên ước mơ",
    ],
    'sad': [
        "mưa rơi nhẹ trong đêm khuya vắng", "nỗi nhớ dâng lên trong lòng ta",
        "em đã đi rồi còn lại gì đây", "một mình đứng giữa bóng tối thênh thang",
        "những kỷ niệm cứ về trong giấc mơ", "nước mắt rơi không biết vì đâu",
        "tim vỡ tan theo từng nhịp thở dài", "ngày ta gặp nhau giờ xa cách rồi",
        "tiếng thở dài vang trong đêm tối", "cô đơn ngồi đếm từng giọt mưa rơi",
    ],
    'romantic': [
        "em là ánh sáng trong cuộc đời anh", "tình yêu mình dệt nên từ những giấc mơ",
        "đôi mắt em sâu như đại dương xanh", "bên em anh quên đi tất cả lo âu",
        "hãy để trái tim ta hoà làm một", "mãi mãi bên nhau dù trăm năm sau",
        "tình ta như hoa nở dưới trăng thanh", "anh muốn nắm tay em đi hết cuộc đời",
        "nụ hôn đầu tiên ngọt ngào mãi còn", "yêu em là hạnh phúc lớn nhất đời anh",
    ],
    'energetic': [
        "đứng lên và hãy cất cao giọng ca", "không gì có thể ngăn ta tiến lên",
        "lửa nhiệt huyết cháy trong huyết mạch", "ta chinh phục mọi đỉnh cao nhất",
        "hét to lên nào không ai dừng được", "nhịp tim đập mạnh theo từng tiếng nhạc",
        "bay cao vút lên tới tận chân trời", "không bao giờ bỏ cuộc dù khó khăn",
        "mạnh mẽ tiến lên không bao giờ ngã", "cháy hết mình trong từng khoảnh khắc",
    ],
    'calm': [
        "gió nhẹ thổi qua cánh đồng xanh mướt", "thư thái ngồi ngắm mây trời trôi qua",
        "bình yên trong từng hơi thở nhẹ nhàng", "lòng ta như mặt hồ không gợn sóng",
        "thiên nhiên ôm ta vào lòng dịu dàng", "chậm lại để cảm nhận cuộc sống này",
        "tiếng chim hót giữa buổi sáng bình yên", "ánh sáng dịu dàng xuyên qua tán lá",
        "nhẹ nhàng như sương mai tan dần đi", "lắng nghe tiếng lòng trong giây phút tĩnh",
    ],
    'melancholic': [
        "hoài niệm về những ngày tháng đã qua", "ký ức xưa cứ về trong tâm trí",
        "ngày ấy ta trẻ và đầy ước mơ", "thời gian trôi đi không thể nào níu",
        "nhớ con đường ta từng sánh vai nhau", "những tháng năm xưa giờ chỉ còn trong mơ",
        "mùa thu đến lá vàng rơi đầy sân", "hương xưa còn đây mà người đã xa",
        "giữa dòng đời ta tìm về quá khứ", "nỗi hoài niệm ngọt ngào và đau thương",
    ],
}

def build_markov_chain(corpus: list[str], order: int = 2) -> dict:
    """Xây dựng Markov Chain từ corpus."""
    chain = defaultdict(list)
    for sentence in corpus:
        words = sentence.split()
        for i in range(len(words) - order):
            key = tuple(words[i:i+order])
            chain[key].append(words[i+order])
    return dict(chain)


def generate_lyric_line(chain: dict, seed_words: list[str], max_words: int = 8) -> str:
    """Sinh 1 câu lời nhạc từ Markov Chain."""
    if not chain:
        return random.choice(list(LYRIC_CORPUS.get('happy', ['không có lời nhạc'])))

    # Chọn seed ngẫu nhiên từ chain
    if seed_words and len(seed_words) >= 2:
        current = tuple(seed_words[:2])
    else:
        current = random.choice(list(chain.keys()))

    result = list(current)
    for _ in range(max_words - len(current)):
        next_words = chain.get(current)
        if not next_words:
            # Restart từ điểm ngẫu nhiên
            current = random.choice(list(chain.keys()))
            continue
        next_word = random.choice(next_words)
        result.append(next_word)
        current = tuple(result[-2:])

    return ' '.join(result)


def generate_lyrics(
    mood: str = 'happy',
    genre: str = 'pop',
    title: str = '',
    num_verses: int = 2,
    has_chorus: bool = True,
) -> dict:
    """
    Tạo lời bài hát đầy đủ với verse, chorus, bridge.
    - Ưu tiên: Sử dụng LLM (Google Gemini / OpenAI) để sáng tác lời bài hát mới mẻ.
    - Dự phòng: Dùng Markov Chain nếu chưa cấu hình API key.
    """
    try:
        from .llm_service import is_llm_available, generate_lyrics_with_llm
        if is_llm_available():
            topic_str = title.strip() or f"bài hát phong cách {genre} tâm trạng {mood}"
            llm_res = generate_lyrics_with_llm(
                topic=topic_str,
                genre=genre,
                mood=mood,
                vocal_gender="female",
                language="vi",
            )
            if llm_res and llm_res.get("lyrics"):
                return {
                    'title': llm_res.get('title', title or _suggest_title(mood, genre)),
                    'lyrics': llm_res['lyrics'],
                    'structure': ['intro', 'verse_1', 'chorus', 'verse_2', 'bridge', 'outro'],
                    'mood': mood,
                    'genre': genre,
                    'provider': llm_res.get('provider', 'llm'),
                }
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[Composer] LLM fallback sang Markov: {e}")
    corpus = LYRIC_CORPUS.get(mood, LYRIC_CORPUS['happy'])
    # Bổ sung corpus từ genre nếu có
    if genre in LYRIC_CORPUS:
        corpus = corpus + LYRIC_CORPUS[genre]

    chain = build_markov_chain(corpus, order=2)

    def make_stanza(num_lines: int = 4) -> list[str]:
        lines = []
        seed = random.choice(corpus).split()[:2]
        for i in range(num_lines):
            line = generate_lyric_line(chain, seed if i == 0 else [], max_words=random.randint(6, 10))
            lines.append(line.capitalize())
            seed = line.split()[-2:] if len(line.split()) >= 2 else seed
        return lines

    # Tạo cấu trúc bài
    structure = {}

    for v in range(1, num_verses + 1):
        structure[f'verse_{v}'] = make_stanza(4)

    if has_chorus:
        chorus_lines = make_stanza(4)
        # Chorus thường có 1 câu lặp lại
        chorus_lines[2] = chorus_lines[0]
        structure['chorus'] = chorus_lines

    if num_verses >= 2:
        structure['bridge'] = make_stanza(2)

    # Format thành text
    formatted = []
    section_labels = {
        'verse_1': '[Verse 1]', 'verse_2': '[Verse 2]', 'verse_3': '[Verse 3]',
        'chorus': '[Chorus]', 'bridge': '[Bridge]',
    }

    for key, lines in structure.items():
        formatted.append(section_labels.get(key, f'[{key}]'))
        formatted.extend(lines)
        formatted.append('')

    return {
        'title': title or _suggest_title(mood, genre),
        'lyrics': '\n'.join(formatted).strip(),
        'structure': list(structure.keys()),
        'mood': mood,
        'genre': genre,
    }


def _suggest_title(mood: str, genre: str) -> str:
    """Tự động gợi ý tên bài hát."""
    titles = {
        'happy': ['Ánh Nắng', 'Ngày Vui', 'Nụ Cười', 'Hạnh Phúc', 'Sắc Màu'],
        'sad': ['Mưa Đêm', 'Nỗi Nhớ', 'Xa Cách', 'Bóng Tối', 'Cô Đơn'],
        'romantic': ['Tình Yêu', 'Ánh Mắt Em', 'Mãi Bên Nhau', 'Giấc Mơ Đôi', 'Hơi Ấm'],
        'energetic': ['Bốc Lửa', 'Không Dừng Lại', 'Tiến Lên', 'Chinh Phục', 'Sức Mạnh'],
        'calm': ['Bình Yên', 'Lặng Yên', 'Thiên Nhiên', 'Nhẹ Nhàng', 'Gió Mát'],
        'melancholic': ['Hoài Niệm', 'Ký Ức', 'Thời Gian', 'Mùa Thu', 'Xa Xưa'],
        'uplifting': ['Bay Cao', 'Hy Vọng', 'Ánh Bình Minh', 'Tương Lai', 'Vươn Lên'],
        'angry': ['Lửa', 'Phá Vỡ', 'Giải Phóng', 'Không Sợ', 'Bùng Cháy'],
    }
    base = random.choice(titles.get(mood, ['Giai Điệu']))
    suffix = random.choice(['', ' (AI Composed)', f' - {genre.upper()}', ''])
    return base + suffix
