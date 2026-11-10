"""
Sonavia Studio — Neural Symbolic Acoustic Synth Provider (Tier-3 Fallback Engine)
===================================================================================
Bộ phát sinh âm thanh thuần nhạc lý đa âm (Harmonic Additive Synthesizer) độc quyền của Sonavia:
- 100% tự chủ không phụ thuộc vào internet, GPU hay server đám mây.
- Sáng tác từ cấu trúc hợp âm (Chord Progression), giai điệu (Melody) và bè trầm (Bassline).
- Tổng hợp âm sắc phong phú (Grand Piano, Electric Bass, Acoustic Strings, Soft Lead) với ADSR envelope.
- Stereo field panning + Reverb spatial illusion + DSP Vocal Clarity Mastering.
"""

import io
import time
import logging
import numpy as np
import soundfile as sf
from typing import Dict, Any, Optional
from .base_provider import BaseMusicProvider
from ..music_composer import (
    build_progression, generate_melody, get_scale,
    NOTES, MOOD_TO_MODE, MOOD_TO_TEMPO
)
from ..audio_mastering import master_audio_array

logger = logging.getLogger(__name__)


def midi_to_freq(midi_num: int) -> float:
    """Chuyển nốt MIDI thành tần số Hz chuẩn (A4 = 69 = 440Hz)."""
    return 440.0 * (2.0 ** ((midi_num - 69.0) / 12.0))


def render_note_waveform(
    freq: float,
    duration_s: float,
    sr: int = 44100,
    instrument: str = 'piano',
    velocity: int = 80,
) -> np.ndarray:
    """Tạo dạng sóng âm thanh phong phú của 1 nốt nhạc theo loại nhạc cụ."""
    n_samples = int(sr * duration_s)
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float32)

    t = np.linspace(0, duration_s, n_samples, endpoint=False)
    vel_scale = max(0.2, min(1.0, velocity / 100.0))

    if instrument == 'bass':
        # Sub-bass ấm + 2nd harmonic
        wave = (
            np.sin(2.0 * np.pi * freq * t) +
            0.4 * np.sin(2.0 * np.pi * (freq * 2.0) * t) +
            0.15 * np.sin(2.0 * np.pi * (freq * 3.0) * t)
        )
        # ADSR nhanh
        env = np.exp(-t * 2.5)
        return (wave * env * vel_scale * 0.7).astype(np.float32)

    elif instrument == 'melody':
        # Lead mượt mà với vibrato tinh tế
        vibrato = 1.0 + 0.004 * np.sin(2.0 * np.pi * 5.0 * t)
        wave = (
            np.sin(2.0 * np.pi * freq * vibrato * t) +
            0.5 * np.sin(2.0 * np.pi * (freq * 2.0) * vibrato * t) +
            0.2 * np.sin(2.0 * np.pi * (freq * 3.0) * t) +
            0.08 * np.sin(2.0 * np.pi * (freq * 4.0) * t)
        )
        # Envelope tự nhiên
        attack = min(int(sr * 0.03), n_samples)
        env = np.ones(n_samples, dtype=np.float32)
        if attack > 0:
            env[:attack] = np.linspace(0, 1, attack)
        decay = np.exp(-t * 1.8)
        return (wave * env * decay * vel_scale * 0.65).astype(np.float32)

    else:
        # Piano / Chords: Tổng hợp hài âm piano với suy hao theo tần số
        wave = (
            np.sin(2.0 * np.pi * freq * t) +
            0.55 * np.sin(2.0 * np.pi * (freq * 2.0) * t) * np.exp(-t * 3.5) +
            0.30 * np.sin(2.0 * np.pi * (freq * 3.0) * t) * np.exp(-t * 5.0) +
            0.15 * np.sin(2.0 * np.pi * (freq * 4.0) * t) * np.exp(-t * 7.0) +
            0.08 * np.sin(2.0 * np.pi * (freq * 5.0) * t) * np.exp(-t * 9.0)
        )
        attack = min(int(sr * 0.015), n_samples)
        env = np.ones(n_samples, dtype=np.float32)
        if attack > 0:
            env[:attack] = np.linspace(0, 1, attack)
        decay = np.exp(-t * 1.6)
        return (wave * env * decay * vel_scale * 0.55).astype(np.float32)


class AcousticSynthProvider(BaseMusicProvider):
    """
    Tier-3 Standalone Synth Provider của Sonavia Studio.
    Đảm bảo 100% thời gian hoạt động của hệ thống ngay cả khi ngoại tuyến hoặc GPU quá tải.
    """
    name = "sonavia-synth"
    has_vocals = False
    supports_multilingual = True

    def generate(
        self,
        prompt: str,
        lyrics: str = "",
        duration: int = 30,
        genre: str = "vpop",
        mood: str = "happy",
        vocal_gender: str = "female",
        seed: Optional[str] = None,
        custom_prompt: str = "",
        guidance_scale: float = 8.5,
        infer_steps: int = 60,
        **kwargs: Any
    ) -> Dict[str, Any]:
        t0 = time.time()
        logger.info(f"[AcousticSynthProvider] Khởi tạo âm thanh nhạc lý đa âm: genre={genre}, mood={mood}, duration={duration}s")

        sr = 44100
        dur_target = max(15, min(int(duration), 120))  # 15s - 120s
        total_samples = int(sr * dur_target)

        # 1. Xác định gam, nhịp độ và nốt chủ
        root_note = 'C'
        root_idx = NOTES.index(root_note) if root_note in NOTES else 0
        root_midi = 48 + root_idx
        mode = MOOD_TO_MODE.get(mood, 'major')
        tempo = MOOD_TO_TEMPO.get(mood, 115)
        sec_per_beat = 60.0 / float(tempo)
        sec_per_bar = sec_per_beat * 4.0
        num_bars = max(4, int(dur_target / sec_per_bar) + 1)

        scale_notes = get_scale(root_midi, mode)
        chords = build_progression(genre, root_midi, mode)

        # 2. Tạo các kênh âm thanh stereo (Left, Right)
        audio_left = np.zeros(total_samples, dtype=np.float32)
        audio_right = np.zeros(total_samples, dtype=np.float32)

        # ── KÊNH 1: HỢP ÂM PIANO (CHORDS) ──
        bars_per_chord = 1
        current_time_s = 0.0
        while current_time_s < dur_target:
            for chord_idx, chord in enumerate(chords):
                chord_start_idx = int(current_time_s * sr)
                chord_dur = sec_per_bar * bars_per_chord
                chord_dur_s = min(chord_dur, dur_target - current_time_s)
                if chord_dur_s <= 0 or chord_start_idx >= total_samples:
                    break

                for note_midi in chord:
                    freq = midi_to_freq(note_midi)
                    note_wave = render_note_waveform(freq, chord_dur_s, sr, 'piano', velocity=72)
                    end_idx = min(total_samples, chord_start_idx + len(note_wave))
                    n_len = end_idx - chord_start_idx
                    if n_len > 0:
                        audio_left[chord_start_idx:end_idx] += note_wave[:n_len] * 0.45
                        audio_right[chord_start_idx:end_idx] += note_wave[:n_len] * 0.55

                current_time_s += chord_dur
                if current_time_s >= dur_target:
                    break

        # ── KÊNH 2: BÈ TRẦM (ELECTRIC BASS) ──
        current_time_s = 0.0
        while current_time_s < dur_target:
            for chord in chords:
                bass_midi = max(24, chord[0] - 12)
                bass_freq = midi_to_freq(bass_midi)
                for beat_offset in [0.0, 2.0]:
                    n_start_s = current_time_s + (beat_offset * sec_per_beat)
                    if n_start_s >= dur_target:
                        break
                    start_idx = int(n_start_s * sr)
                    note_dur_s = min(sec_per_beat * 1.8, dur_target - n_start_s)
                    if note_dur_s <= 0 or start_idx >= total_samples:
                        break

                    bass_wave = render_note_waveform(bass_freq, note_dur_s, sr, 'bass', velocity=85)
                    end_idx = min(total_samples, start_idx + len(bass_wave))
                    n_len = end_idx - start_idx
                    if n_len > 0:
                        audio_left[start_idx:end_idx] += bass_wave[:n_len] * 0.5
                        audio_right[start_idx:end_idx] += bass_wave[:n_len] * 0.5

                current_time_s += sec_per_bar
                if current_time_s >= dur_target:
                    break

        # ── KÊNH 3: GIAI ĐIỆU CHÍNH (MELODY LEAD) ──
        melody_style = 'smooth' if mood in ('sad', 'calm', 'romantic', 'melancholic') else 'rhythmic'
        melody_notes = generate_melody(scale_notes, num_bars=num_bars, tempo=tempo, style=melody_style)
        for m in melody_notes:
            n_start_s = m['beat'] * sec_per_beat
            if n_start_s >= dur_target:
                break
            start_idx = int(n_start_s * sr)
            n_dur_s = min(m['duration'] * sec_per_beat * 1.1, dur_target - n_start_s)
            if n_dur_s <= 0 or start_idx >= total_samples:
                continue

            m_freq = midi_to_freq(m['pitch'])
            m_wave = render_note_waveform(m_freq, n_dur_s, sr, 'melody', velocity=m.get('volume', 85))
            end_idx = min(total_samples, start_idx + len(m_wave))
            n_len = end_idx - start_idx
            if n_len > 0:
                audio_left[start_idx:end_idx] += m_wave[:n_len] * 0.55
                audio_right[start_idx:end_idx] += m_wave[:n_len] * 0.45

        # 3. Kết hợp stereo & Fade in / out
        stereo_audio = np.stack([audio_left, audio_right], axis=1)

        fade_in = int(sr * 1.2)
        if total_samples > fade_in:
            stereo_audio[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
        fade_out = int(sr * 2.5)
        if total_samples > fade_out:
            stereo_audio[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]

        # 4. Hậu kỳ âm thanh chuyên sâu qua Audiophile Mastering Engine
        is_vi = (genre == "vpop" or "vi" in str(lyrics).lower() or any(c in str(lyrics) for c in 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ'))
        mastered_audio = master_audio_array(stereo_audio, sr, is_vietnamese=is_vi, vocal_boost_db=1.5, target_peak=0.891)

        # 5. Xuất ra tệp WAV
        buf = io.BytesIO()
        sf.write(buf, mastered_audio, sr, format='WAV')
        audio_bytes = buf.getvalue()
        elapsed = round(time.time() - t0, 2)

        logger.info(f"[AcousticSynthProvider] Đã tạo xong bản hòa âm {dur_target}s trong {elapsed}s ({len(audio_bytes):,} bytes)")

        return {
            "audio_bytes": audio_bytes,
            "duration": dur_target,
            "elapsed": elapsed,
            "prompt": custom_prompt or prompt,
            "seed": str(seed or "synth_local"),
            "lyrics": lyrics or "",
            "format": "wav",
            "provider": self.name,
            "mastered": True,
        }

    def is_available(self) -> bool:
        return True
