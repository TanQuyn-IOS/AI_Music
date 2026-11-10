"""
Sonavia Studio — High-Fidelity Audio Mixer & Stem Combiner
===========================================================
Ghép nhạc nền (Instrumental) + giọng hát AI (Vocal) thành bài hát hoàn chỉnh chuẩn phòng thu.

Tính năng:
- Bảo tồn 100% STEREO (âm thanh nổi 2 kênh), tuyệt đối không ép về mono gây hẹp âm trường và triệt tiêu pha.
- Resample chính xác bằng polyphase filtering (scipy) chống méo aliasing.
- Căn chỉnh nhịp điệu (Timing & Intro Offset): chừa khoảng lặng intro 2.0s tự nhiên trước khi lời hát cất lên.
- TUYỆT ĐỐI KHÔNG lặp lại lời hát (vocal tiling) bừa bãi khi nhạc dài hơn; đệm khoảng lặng mượt mà ở outro.
- Vocal Pocket Ducking: Tự động hạ nhẹ âm lượng nhạc nền khi có tiếng hát để giọng tiếng Việt nổi bật, rõ chữ.
- Chống clipping và vỡ tiếng với True-Peak Limiting (-1.0 dBFS).
- Xuất WAV 16-bit PCM chuẩn quốc tế (tương thích 100% mọi trình phát media).
"""

import io
import logging
import numpy as np
import soundfile as sf
from typing import Tuple

logger = logging.getLogger(__name__)


def _to_stereo(audio: np.ndarray) -> np.ndarray:
    """Đảm bảo âm thanh ở định dạng Stereo (N, 2), bảo tồn không gian âm thanh nổi."""
    if audio is None or len(audio) == 0:
        return np.zeros((0, 2), dtype=np.float32)
    if audio.ndim == 1:
        return np.column_stack([audio, audio]).astype(np.float32)
    elif audio.ndim == 2:
        if audio.shape[1] == 1:
            return np.column_stack([audio[:, 0], audio[:, 0]]).astype(np.float32)
        elif audio.shape[0] == 2 and audio.shape[1] > 2:
            return audio.T.astype(np.float32)
        return audio[:, :2].astype(np.float32)
    return audio.astype(np.float32)


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio về target sample rate bằng scipy polyphase chống aliasing."""
    if orig_sr == target_sr or audio is None or len(audio) == 0:
        return audio
    try:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(orig_sr, target_sr)
        up   = target_sr // g
        down = orig_sr   // g
        axis = 0 if audio.ndim > 1 else -1
        resampled = resample_poly(audio.astype(np.float32), up, down, axis=axis)
        return resampled.astype(np.float32)
    except Exception as e:
        logger.warning(f"Resample poly failed: {e}, fallback to linear interpolation")
        ratio = target_sr / orig_sr
        new_len = int(len(audio) * ratio)
        if audio.ndim == 1:
            indices = np.linspace(0, len(audio) - 1, new_len)
            return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
        else:
            out = np.zeros((new_len, audio.shape[1]), dtype=np.float32)
            indices = np.linspace(0, len(audio) - 1, new_len)
            for c in range(audio.shape[1]):
                out[:, c] = np.interp(indices, np.arange(len(audio)), audio[:, c])
            return out


def normalize(audio: np.ndarray, peak: float = 0.9) -> np.ndarray:
    """Normalize audio về peak level an toàn, tránh chia cho 0."""
    if audio is None or len(audio) == 0:
        return audio
    mx = float(np.max(np.abs(audio)))
    if mx > 1e-6:
        return (audio / mx * peak).astype(np.float32)
    return audio.astype(np.float32)


def apply_fade(
    audio: np.ndarray,
    sr: int,
    fade_in_s: float = 0.8,
    fade_out_s: float = 2.0
) -> np.ndarray:
    """Thêm fade in / fade out êm ái, hỗ trợ cả 1D mono lẫn 2D stereo."""
    if audio is None or len(audio) == 0:
        return audio
    audio = audio.copy()
    n_samples = len(audio)
    fi = min(int(fade_in_s * sr), n_samples // 2)
    fo = min(int(fade_out_s * sr), n_samples // 2)

    if fi > 0:
        fade_in_curve = np.linspace(0.0, 1.0, fi, dtype=np.float32)
        if audio.ndim == 1:
            audio[:fi] *= fade_in_curve
        else:
            audio[:fi] *= fade_in_curve[:, None]

    if fo > 0:
        fade_out_curve = np.linspace(1.0, 0.0, fo, dtype=np.float32)
        if audio.ndim == 1:
            audio[-fo:] *= fade_out_curve
        else:
            audio[-fo:] *= fade_out_curve[:, None]

    return audio


def mix_music_and_vocal(
    music_audio:  np.ndarray,
    music_sr:     int,
    vocal_audio:  np.ndarray,
    vocal_sr:     int,
    music_volume: float = 0.46,   # Cân bằng âm lượng nhạc nền (không lấn át giọng hát)
    vocal_volume: float = 0.90,   # Vocal rõ nét, nổi bật trên beat
    target_sr:    int = 32000,
    intro_delay_s: float = 2.2,   # Intro 2.2s tự nhiên trước khi hát
) -> Tuple[np.ndarray, int]:
    """
    Ghép nhạc nền Stereo + giọng hát AI với độ cân bằng âm lượng và timing chuẩn phòng thu.
    """
    logger.info(f"[AudioMixer] Resampling: music {music_sr}Hz → {target_sr}Hz, vocal {vocal_sr}Hz → {target_sr}Hz")

    # 1. Đảm bảo cả hai đều là Stereo 2 kênh
    music = _to_stereo(music_audio)
    vocal = _to_stereo(vocal_audio)

    # 2. Resample về cùng target_sr
    music = resample_audio(music, music_sr, target_sr)
    vocal = resample_audio(vocal, vocal_sr, target_sr)

    # 3. Chuẩn hóa mức năng lượng ban đầu
    music = normalize(music, peak=music_volume)
    vocal = normalize(vocal, peak=vocal_volume)

    target_len = len(music)
    if target_len == 0:
        return vocal, target_sr

    # 4. Căn chỉnh Timing: Thêm khoảng lặng intro hợp lý nếu bài hát đủ dài
    intro_samples = int(intro_delay_s * target_sr) if (target_len > int(10 * target_sr) and intro_delay_s > 0) else 0
    if intro_samples > 0:
        silence_intro = np.zeros((intro_samples, vocal.shape[1]), dtype=np.float32)
        vocal = np.vstack([silence_intro, vocal])

    # 5. Căn chỉnh độ dài: TUYỆT ĐỐI KHÔNG lặp lại lời hát
    if len(vocal) < target_len:
        # Nếu lời hát ngắn hơn nhạc: chừa outro nhạc nền êm ái
        pad_len = target_len - len(vocal)
        silence_tail = np.zeros((pad_len, vocal.shape[1]), dtype=np.float32)
        vocal = np.vstack([vocal, silence_tail])
    else:
        # Nếu lời hát dài hơn nhạc nền: cắt vừa vặn và fade-out êm
        vocal = vocal[:target_len]
        vocal = apply_fade(vocal, target_sr, fade_in_s=0.05, fade_out_s=2.0)

    # 6. Dynamic Vocal Pocket Ducking:
    # Nhẹ nhàng hạ nhạc nền ~1.5dB khi ca sĩ cất giọng để tiếng hát không bị đè lấp
    vocal_rms = np.sqrt(np.mean(vocal ** 2, axis=1) + 1e-9)
    vocal_active = vocal_rms > 0.025
    if np.any(vocal_active):
        smooth_len = min(int(0.2 * target_sr), len(vocal_active))
        if smooth_len > 1:
            kernel = np.ones(smooth_len, dtype=np.float32) / float(smooth_len)
            duck_env = np.convolve(vocal_active.astype(np.float32), kernel, mode='same')
            duck_env = np.clip(duck_env * 1.4, 0.0, 1.0)
            duck_factor = 1.0 - (0.24 * duck_env[:, None])
            music = music * duck_factor

    # 7. Mix Stereo hai track
    mixed = music + vocal

    # 8. Chuẩn hóa headroom tổng thể
    mixed = normalize(mixed, peak=0.90)

    # 9. Fade in và Fade out tổng thể
    mixed = apply_fade(mixed, target_sr, fade_in_s=0.8, fade_out_s=2.5)

    logger.info(f"[AudioMixer] Hoàn tất mixing Stereo: {len(mixed)/target_sr:.1f}s tại {target_sr}Hz")
    return mixed, target_sr


def audio_to_wav_bytes(audio: np.ndarray, sr: int) -> bytes:
    """Chuyển numpy array thành WAV bytes 16-bit PCM chuẩn tương thích mọi thiết bị."""
    buf = io.BytesIO()
    clipped = np.clip(audio, -1.0, 1.0).astype(np.float32)
    sf.write(buf, clipped, sr, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()


def mix_to_wav_bytes(
    music_wav_bytes: bytes,
    vocal_wav_bytes: bytes,
    music_volume: float = 0.46,
    vocal_volume: float = 0.90,
) -> bytes:
    """
    Nhận WAV bytes của nhạc nền và giọng hát, trả về WAV bytes Stereo đã mix & master.
    """
    music_buf = io.BytesIO(music_wav_bytes)
    vocal_buf = io.BytesIO(vocal_wav_bytes)

    music_audio, music_sr = sf.read(music_buf, dtype='float32')
    vocal_audio, vocal_sr = sf.read(vocal_buf, dtype='float32')

    mixed, sr = mix_music_and_vocal(
        music_audio, music_sr,
        vocal_audio, vocal_sr,
        music_volume=music_volume,
        vocal_volume=vocal_volume,
    )

    # Áp dụng Vocal Clarity DSP Mastering chuyên sâu
    from .audio_mastering import master_audio_array
    mixed = master_audio_array(mixed, sr, is_vietnamese=True, target_peak=0.891)

    return audio_to_wav_bytes(mixed, sr)


def music_only_to_wav_bytes(music_wav_bytes: bytes) -> bytes:
    """Xử lý nhạc nền không lời: giữ trọn Stereo, fade in/out và mastering chuẩn."""
    buf = io.BytesIO(music_wav_bytes)
    audio, sr = sf.read(buf, dtype='float32')
    stereo = _to_stereo(audio)
    stereo = normalize(stereo, peak=0.90)
    stereo = apply_fade(stereo, sr, fade_in_s=0.8, fade_out_s=2.5)

    from .audio_mastering import master_audio_array
    mastered = master_audio_array(stereo, sr, is_vietnamese=False, target_peak=0.891)
    return audio_to_wav_bytes(mastered, sr)
