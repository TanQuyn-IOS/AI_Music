import os
import io
import uuid
import logging
import torch
import torchaudio
from django.conf import settings

logger = logging.getLogger(__name__)


def crossfade_audio_tensors(audio1: torch.Tensor, audio2: torch.Tensor, sr: int, crossfade_sec: float = 1.5) -> torch.Tensor:
    """
    Nối và hòa quyện (crossfade) 2 đoạn âm thanh liền mạch, loại bỏ click/pop.
    audio1: tensor [channels, samples]
    audio2: tensor [channels, samples]
    """
    # Đồng bộ số kênh (mono <-> stereo)
    if audio1.dim() == 1:
        audio1 = audio1.unsqueeze(0)
    if audio2.dim() == 1:
        audio2 = audio2.unsqueeze(0)

    if audio1.shape[0] == 1 and audio2.shape[0] == 2:
        audio1 = audio1.repeat(2, 1)
    elif audio1.shape[0] == 2 and audio2.shape[0] == 1:
        audio2 = audio2.repeat(2, 1)

    fade_len = int(crossfade_sec * sr)
    min_len = min(audio1.shape[1], audio2.shape[1])
    if fade_len > min_len // 2:
        fade_len = max(100, min_len // 2)

    device = audio1.device
    fade_out = torch.linspace(1.0, 0.0, fade_len, device=device)
    fade_in = torch.linspace(0.0, 1.0, fade_len, device=device)

    # Hòa quyện đoạn giao nhau
    overlap = audio1[:, -fade_len:] * fade_out + audio2[:, :fade_len] * fade_in

    # Ghép 3 phần: [audio1 trước giao] + [đoạn hòa quyện] + [audio2 sau giao]
    combined = torch.cat([audio1[:, :-fade_len], overlap, audio2[:, fade_len:]], dim=1)
    return combined


def resolve_song_audio_path(song) -> str:
    """Tìm đường dẫn file audio thực tế của bài hát trên ổ đĩa"""
    if song.audio_file:
        try:
            path = song.audio_file.path
            if os.path.isfile(path):
                return path
        except Exception:
            pass

    if song.audio_url:
        clean_url = song.audio_url.replace(settings.MEDIA_URL, '').lstrip('/\\')
        full_path = os.path.join(str(settings.MEDIA_ROOT), clean_url)
        if os.path.isfile(full_path):
            return full_path

    # Thử tìm trong generated
    gen_dir = os.path.join(str(settings.MEDIA_ROOT), 'generated')
    if os.path.isdir(gen_dir) and song.audio_url:
        base_name = os.path.basename(song.audio_url)
        candidate = os.path.join(gen_dir, base_name)
        if os.path.isfile(candidate):
            return candidate

    return ""


def generate_extension_segment(parent_song, duration_sec: int = 60, continuation_prompt: str = ""):
    """
    Sinh đoạn nhạc nối tiếp (extension chunk) đồng điệu về thể loại, mood, tempo.
    Ưu tiên gọi ACE-Step / MusicGen nếu khả dụng, fallback qua Harmonic Audio Engine.
    """
    prompt = continuation_prompt or f"{parent_song.title}, continuing melody in {parent_song.genre} style, {parent_song.mood} atmosphere"
    genre = parent_song.genre or 'pop'
    mood = parent_song.mood or 'happy'

    # Thử ACE-Step nếu có
    try:
        from apps.ai_engine.acestep_generator import is_acestep_available, generate_with_acestep
        if is_acestep_available(fast=True):
            res = generate_with_acestep(
                prompt=prompt,
                lyrics="",
                duration=duration_sec,
                genre=genre,
                mood=mood,
                instruments="full",
                quality="fast"
            )
            audio_bytes = res.get('audio_bytes')
            if audio_bytes and len(audio_bytes) > 2000:
                return audio_bytes
    except Exception as e:
        logger.warning(f"[Extend] ACE-Step không phản hồi: {e}")

    # Thử MusicGen nếu có
    try:
        from apps.ai_engine.music_generator import generate_music_full
        res = generate_music_full(
            genre=genre,
            mood=mood,
            duration=min(duration_sec, 30),
            custom_prompt=prompt,
        )
        audio_bytes = res.get('audio')
        if audio_bytes and len(audio_bytes) > 2000:
            return audio_bytes
    except Exception as e:
        logger.warning(f"[Extend] MusicGen fallback: {e}")

    # Fallback Tier 3: Tạo âm thanh hòa âm acoustic chất lượng cao
    try:
        from apps.ai_engine.synth_provider import AcousticHarmonicSynth
        synth = AcousticHarmonicSynth()
        return synth.generate_harmonic_audio(duration=duration_sec, genre=genre, mood=mood)
    except Exception as e:
        logger.error(f"[Extend] Tier 3 Synth lỗi: {e}")
        # Tạo sóng sin dự phòng
        import numpy as np
        sr = 44100
        t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
        wave_data = (0.3 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        buf = io.BytesIO()
        import scipy.io.wavfile as wavfile
        wavfile.write(buf, sr, wave_data)
        return buf.getvalue()


def extend_song(parent_song, user, duration_sec: int = 60, continuation_prompt: str = "", additional_lyrics: str = ""):
    """
    Thực hiện mở rộng bài hát:
    1. Lấy audio bài gốc
    2. Sinh audio nối tiếp
    3. Crossfade mượt mà 2 đoạn
    4. Lưu file và tạo bản ghi Song mới
    """
    duration_sec = max(15, min(duration_sec, 120))
    orig_path = resolve_song_audio_path(parent_song)

    extension_bytes = generate_extension_segment(
        parent_song,
        duration_sec=duration_sec,
        continuation_prompt=continuation_prompt
    )

    songs_dir = os.path.join(str(settings.MEDIA_ROOT), 'songs')
    os.makedirs(songs_dir, exist_ok=True)
    ext_filename = f"extended_{parent_song.id}_{uuid.uuid4().hex[:8]}.wav"
    output_path = os.path.join(songs_dir, ext_filename)

    final_duration = parent_song.duration + duration_sec

    if orig_path and os.path.isfile(orig_path):
        try:
            orig_tensor, sr1 = torchaudio.load(orig_path)
            cont_tensor, sr2 = torchaudio.load(io.BytesIO(extension_bytes))

            # Resample nếu sample rate khác nhau
            if sr2 != sr1:
                resampler = torchaudio.transforms.Resample(sr2, sr1)
                cont_tensor = resampler(cont_tensor)

            combined_tensor = crossfade_audio_tensors(orig_tensor, cont_tensor, sr=sr1, crossfade_sec=1.5)
            torchaudio.save(output_path, combined_tensor, sr1)
            final_duration = int(combined_tensor.shape[1] / sr1)
        except Exception as mix_err:
            logger.warning(f"[Extend] Lỗi crossfade với torchaudio: {mix_err}, lưu audio nối tiếp...")
            with open(output_path, 'wb') as f:
                f.write(extension_bytes)
    else:
        # Nếu bài gốc không có file cục bộ, lưu trực tiếp extension
        with open(output_path, 'wb') as f:
            f.write(extension_bytes)

    # Tạo Song mới kế thừa metadata
    from apps.music.models import Song
    extended_lyrics = (parent_song.lyrics or '').strip()
    if additional_lyrics.strip():
        extended_lyrics += f"\n\n[Mở rộng +{duration_sec}s]\n{additional_lyrics.strip()}"

    new_title = f"{parent_song.title} (Extended)"
    if len(new_title) > 195:
        new_title = new_title[:195] + "..."

    extended_song = Song.objects.create(
        title=new_title,
        artist=user,
        genre=parent_song.genre,
        mood=parent_song.mood,
        tempo=parent_song.tempo,
        duration=final_duration,
        lyrics=extended_lyrics,
        description=f"Phiên bản mở rộng (+{duration_sec}s) kế thừa từ bản gốc '{parent_song.title}'.",
        cover_image=parent_song.cover_image,
        audio_file=f"songs/{ext_filename}",
        audio_url=f"{settings.MEDIA_URL}songs/{ext_filename}",
        is_published=True
    )

    return extended_song
