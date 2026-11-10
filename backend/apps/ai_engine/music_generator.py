"""
AI Music Generator — Optimized
================================
Tối ưu tốc độ cho RTX 3050 6GB:
  1. float16 + cudnn benchmark mode  → ~30-40% nhanh hơn
  2. torch.inference_mode()          → nhanh hơn no_grad
  3. Warm-up model khi Django start  → loại bỏ độ trễ lần đầu
  4. Prompt/audio cache (LRU)        → cùng prompt không cần tạo lại
  5. Giảm default duration 30s→15s  → 1500 tokens → 750 tokens
  6. Bật autocast float16            → giảm VRAM + tăng tốc
"""

import os
import io
import time
import logging
import hashlib
import threading
import numpy as np
from functools import lru_cache
from collections import OrderedDict

logger = logging.getLogger(__name__)

# ─── Model singleton ──────────────────────────────────────────────────────────

_model     = None
_processor = None
_device    = None
_model_name = None
_model_lock = threading.Lock()

# ─── Audio cache (LRU, tối đa 20 bài, ~200MB RAM) ────────────────────────────

_audio_cache: OrderedDict = OrderedDict()
_cache_lock = threading.Lock()
MAX_CACHE = 20


def _cache_key(prompt: str, duration: int, guidance: float, temp: float) -> str:
    s = f"{prompt}|{duration}|{guidance:.1f}|{temp:.1f}"
    return hashlib.md5(s.encode()).hexdigest()[:16]


def _cache_get(key: str):
    with _cache_lock:
        if key in _audio_cache:
            _audio_cache.move_to_end(key)
            return _audio_cache[key]
        return None


def _cache_set(key: str, value):
    with _cache_lock:
        _audio_cache[key] = value
        if len(_audio_cache) > MAX_CACHE:
            _audio_cache.popitem(last=False)


# ─── Device setup ─────────────────────────────────────────────────────────────

def _get_device() -> str:
    import torch
    if torch.cuda.is_available():
        # Bật cudnn benchmark — tự chọn kernel tối ưu cho shape cố định
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True   # Tensor Core acceleration
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"GPU: {torch.cuda.get_device_name(0)} ({vram:.1f}GB) — cudnn.benchmark=True")
        return "cuda"
    logger.warning("CUDA not available, using CPU (slower)")
    return "cpu"


# ─── Model load ───────────────────────────────────────────────────────────────

def load_model(model_name: str = "facebook/musicgen-small"):
    """Load model vào VRAM với tất cả tối ưu."""
    global _model, _processor, _device, _model_name

    if _model is not None and _model_name == model_name:
        return _model, _processor, _device

    logger.info(f"Loading {model_name}...")
    t0 = time.time()

    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    _device = _get_device()

    try:
        _processor = AutoProcessor.from_pretrained(model_name, local_files_only=True)
    except Exception:
        _processor = AutoProcessor.from_pretrained(model_name)

    # Load với float16 nếu CUDA (tiết kiệm ~50% VRAM, nhanh hơn ~30%)
    # Dùng device_map thay vì low_cpu_mem_usage+.to() để tránh lỗi meta tensor
    dtype = torch.float16 if _device == "cuda" else torch.float32
    try:
        _model = MusicgenForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map=_device,
            local_files_only=True,
        )
    except Exception:
        _model = MusicgenForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map=_device,
        )
    _model.eval()

    # Tắt gradient hoàn toàn (không cần cho inference)
    for p in _model.parameters():
        p.requires_grad_(False)

    _model_name = model_name
    logger.info(f"Model ready in {time.time()-t0:.1f}s on {_device} ({dtype})")

    # Warm-up: chạy 1 lần ngắn để CUDA kernel được compile sẵn
    _warmup_model()

    return _model, _processor, _device


# Backward-compatible alias
get_model = load_model


def _warmup_model():
    """Chạy inference ngắn để warm-up CUDA kernels → lần thật sẽ nhanh hơn."""
    if _device != "cuda":
        return
    try:
        import torch
        logger.info("Warming up CUDA kernels...")
        t0 = time.time()
        with torch.inference_mode():
            with torch.autocast("cuda", dtype=torch.float16):
                inp = _processor(text=["warm up"], padding=True, return_tensors="pt")
                inp = {k: v.to(_device) for k, v in inp.items()}
                _ = _model.generate(**inp, max_new_tokens=50, do_sample=False)
        torch.cuda.empty_cache()
        logger.info(f"Warm-up done in {time.time()-t0:.1f}s")
    except Exception as e:
        logger.warning(f"Warm-up failed (non-critical): {e}")


def unload_model():
    global _model, _processor, _device, _model_name
    if _model is not None:
        import torch
        del _model, _processor
        _model = _processor = _model_name = None
        if _device == "cuda":
            torch.cuda.empty_cache()
        logger.info("Model unloaded")


# ─── Prompt builder ───────────────────────────────────────────────────────────

GENRE_PROMPTS = {
    "vpop":      "Vietnamese pop music, melodic, emotional, piano and strings",
    "kpop":      "K-pop music, catchy beat, synthesizer, upbeat",
    "pop":       "pop music, catchy melody, modern production, radio-friendly",
    "rock":      "rock music, electric guitar, drums, energetic",
    "jazz":      "jazz music, saxophone, piano, smooth, improvisation",
    "classical": "classical orchestral music, strings, piano, elegant",
    "hip_hop":   "hip hop music, trap beat, 808 bass, rhythmic",
    "r&b":       "R&B music, soulful, smooth groove, bass guitar",
    "electronic":"electronic music, synthesizer, EDM, bass drop",
    "lofi":      "lo-fi hip hop, relaxing, mellow, rain sounds, chill",
    "blues":     "blues music, guitar, soulful, minor key",
    "metal":     "metal music, heavy guitar riffs, powerful drums",
    "folk":      "folk music, acoustic guitar, storytelling, warm",
    "indie":     "indie music, alternative, guitar-driven, atmospheric",
    "latin":     "latin music, guitar, percussion, rhythmic, festive",
    "country":   "country music, acoustic guitar, storytelling, warm vocals",
    "other":     "instrumental music, melodic",
}

MOOD_PROMPTS = {
    "happy":       "happy, uplifting, joyful, bright",
    "sad":         "sad, melancholic, emotional, minor key",
    "energetic":   "energetic, powerful, fast-paced, driving",
    "calm":        "calm, peaceful, relaxing, gentle",
    "romantic":    "romantic, tender, warm, loving",
    "angry":       "intense, aggressive, powerful, raw",
    "melancholic": "nostalgic, wistful, bittersweet, reflective",
    "uplifting":   "uplifting, inspiring, motivational, bright",
}

TEMPO_PROMPTS = {
    "slow":   "slow tempo, 60-80 BPM",
    "medium": "medium tempo, 90-120 BPM",
    "fast":   "fast tempo, 130-160 BPM",
}

INSTRUMENT_PROMPTS = {
    "piano":   "featuring piano",
    "guitar":  "featuring guitar",
    "strings": "featuring strings and orchestra",
    "synth":   "featuring synthesizers",
    "full":    "full band arrangement",
    "minimal": "minimalist arrangement",
}


def build_prompt(
    genre: str = "pop",
    mood: str = "happy",
    tempo: str = "medium",
    instruments: str = "full",
    custom_prompt: str = "",
) -> str:
    parts = []
    if custom_prompt.strip():
        parts.append(custom_prompt.strip())
    else:
        parts.append(GENRE_PROMPTS.get(genre, GENRE_PROMPTS["other"]))
    if mood in MOOD_PROMPTS:
        parts.append(MOOD_PROMPTS[mood])
    if tempo in TEMPO_PROMPTS:
        parts.append(TEMPO_PROMPTS[tempo])
    if instruments in INSTRUMENT_PROMPTS:
        parts.append(INSTRUMENT_PROMPTS[instruments])
    parts.append("smooth melodic contour, warm timbre, natural legato phrasing, expressive vocal-like lead, soft dynamics, polished mix, high quality, studio recording")
    return ", ".join(parts)


# ─── Core generate (tối ưu) ───────────────────────────────────────────────────

def generate_music(
    prompt: str,
    duration: int = 15,            # Default 15s (nhanh hơn 30s gấp đôi)
    model_name: str = "facebook/musicgen-small",
    guidance_scale: float = 3.0,
    temperature: float = 1.0,
    use_cache: bool = True,
) -> tuple[bytes, int]:
    """
    Tạo nhạc tối ưu tốc độ.
    - float16 + autocast
    - torch.inference_mode (nhanh hơn no_grad 5-10%)
    - LRU cache: cùng prompt trả về ngay lập tức
    """
    import torch
    import soundfile as sf

    duration = max(5, min(duration, 30))

    # Kiểm tra cache
    if use_cache:
        key = _cache_key(prompt, duration, guidance_scale, temperature)
        cached = _cache_get(key)
        if cached:
            logger.info(f"Cache hit for prompt: {prompt[:40]}...")
            return cached

    model, processor, device = load_model(model_name)
    sr = model.config.audio_encoder.sampling_rate

    logger.info(f"Generate: '{prompt[:50]}...' | {duration}s | {device}")
    t0 = time.time()

    # Tính tokens: MusicGen tạo 50 tokens/giây
    max_tokens = int(duration * 50)

    with torch.inference_mode():
        inp = processor(text=[prompt], padding=True, return_tensors="pt")
        inp = {k: v.to(device) for k, v in inp.items()}

        # autocast: tự dùng float16 nơi an toàn → nhanh hơn ~20-30%
        if device == "cuda":
            with torch.autocast("cuda", dtype=torch.float16):
                out = model.generate(
                    **inp,
                    max_new_tokens=max_tokens,
                    guidance_scale=guidance_scale,
                    temperature=temperature,
                    do_sample=True,
                )
        else:
            out = model.generate(
                **inp,
                max_new_tokens=max_tokens,
                guidance_scale=guidance_scale,
                temperature=temperature,
                do_sample=True,
            )

    audio = out[0, 0].cpu().float().numpy()
    elapsed = time.time() - t0
    logger.info(f"Generated {duration}s in {elapsed:.1f}s ({duration/elapsed:.1f}x realtime)")

    # Audiophile DSP Mastering Chain (Bass Punch, Vocal Presence, Silky Air, Tape Warmth & Peak Limiting)
    try:
        from .audio_mastering import master_audio_array
        audio = master_audio_array(audio, sr, is_vietnamese=True, target_peak=0.891)
    except Exception as m_err:
        logger.warning(f"Mastering fallback: {m_err}")
        if np.abs(audio).max() > 0:
            audio = audio / np.abs(audio).max() * 0.9

    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    wav_bytes = buf.getvalue()

    if device == "cuda":
        torch.cuda.empty_cache()

    # Lưu cache
    if use_cache:
        _cache_set(key, (wav_bytes, sr))

    return wav_bytes, sr


def generate_music_full(
    genre: str = "pop",
    mood: str = "happy",
    tempo: str = "medium",
    instruments: str = "full",
    custom_prompt: str = "",
    duration: int = 15,
    guidance_scale: float = 3.0,
    temperature: float = 1.0,
    model_name: str = "facebook/musicgen-small",
) -> dict:
    prompt = build_prompt(genre, mood, tempo, instruments, custom_prompt)
    audio_bytes, sr = generate_music(
        prompt=prompt,
        duration=duration,
        model_name=model_name,
        guidance_scale=guidance_scale,
        temperature=temperature,
    )
    return {"audio": audio_bytes, "sample_rate": sr, "prompt": prompt,
            "duration": duration, "model": model_name}


# ─── Long Music Generator (ghép đoạn) ────────────────────────────────────────

SEGMENT_DURATION = 20   # Giảm 25→20s: ít tokens hơn, nhanh hơn mỗi đoạn
OVERLAP_DURATION  = 1   # Giảm overlap


def generate_long_music(
    prompt: str,
    total_duration: int = 180,
    model_name: str = "facebook/musicgen-small",
    guidance_scale: float = 3.0,
    temperature: float = 1.0,
    progress_callback=None,
) -> tuple[np.ndarray, int]:
    """Tạo nhạc dài bằng cách ghép đoạn với continuation mode."""
    import torch
    import soundfile as sf

    total_duration = max(10, min(total_duration, 300))
    n_segments = max(1, int(np.ceil(total_duration / SEGMENT_DURATION)))
    seg_dur = int(np.ceil(total_duration / n_segments))

    logger.info(f"Long music: {total_duration}s = {n_segments} × {seg_dur}s")

    model, processor, device = load_model(model_name)
    sr = model.config.audio_encoder.sampling_rate
    all_audio = []
    prev_audio = None

    for i in range(n_segments):
        if progress_callback:
            progress_callback(i, n_segments, f"Đoạn {i+1}/{n_segments} ({seg_dur}s)...")

        t0 = time.time()
        max_tokens = int(seg_dur * 50)

        with torch.inference_mode():
            if i == 0 or prev_audio is None:
                inp = processor(text=[prompt], padding=True, return_tensors="pt")
            else:
                tail = prev_audio[-int(2 * sr):]   # 2s tail
                inp = processor(text=[prompt], audio=tail,
                                sampling_rate=sr, padding=True, return_tensors="pt")
            inp = {k: v.to(device) for k, v in inp.items()}

            if device == "cuda":
                with torch.autocast("cuda", dtype=torch.float16):
                    out = model.generate(**inp, max_new_tokens=max_tokens,
                                         guidance_scale=guidance_scale,
                                         temperature=temperature, do_sample=True)
            else:
                out = model.generate(**inp, max_new_tokens=max_tokens,
                                      guidance_scale=guidance_scale,
                                      temperature=temperature, do_sample=True)

        seg = out[0, 0].cpu().float().numpy()
        prev_audio = seg

        # Crossfade
        if all_audio and OVERLAP_DURATION > 0:
            ov = int(OVERLAP_DURATION * sr)
            if len(all_audio[-1]) >= ov and len(seg) >= ov:
                all_audio[-1][-ov:] *= np.linspace(1, 0, ov)
                seg[:ov] *= np.linspace(0, 1, ov)
                blend = all_audio[-1][-ov:] + seg[:ov]
                all_audio[-1] = all_audio[-1][:-ov]
                seg = np.concatenate([blend, seg[ov:]])
        all_audio.append(seg)

        logger.info(f"  Segment {i+1} done in {time.time()-t0:.1f}s")
        if device == "cuda":
            torch.cuda.empty_cache()

    if progress_callback:
        progress_callback(n_segments, n_segments, "Nhạc nền xong!")

    final = np.concatenate(all_audio).astype(np.float32)
    target = int(total_duration * sr)
    if len(final) > target:
        fade = int(3 * sr)
        final[target-fade:target] *= np.linspace(1, 0, fade)
        final = final[:target]

    return final, sr


def generate_long_music_bytes(
    genre="vpop", mood="romantic", tempo="medium", instruments="full",
    custom_prompt="", total_duration=180, guidance_scale=3.0,
    temperature=1.0, model_name="facebook/musicgen-small",
    progress_callback=None,
) -> tuple[bytes, int, str]:
    import soundfile as sf
    prompt = build_prompt(genre, mood, tempo, instruments, custom_prompt)
    audio, sr = generate_long_music(
        prompt=prompt, total_duration=total_duration,
        model_name=model_name, guidance_scale=guidance_scale,
        temperature=temperature, progress_callback=progress_callback,
    )
    try:
        from .audio_mastering import master_audio_array
        audio = master_audio_array(audio, sr, is_vietnamese=True, target_peak=0.891)
    except Exception as m_err:
        if np.abs(audio).max() > 0:
            audio = audio / np.abs(audio).max() * 0.9
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    buf.seek(0)
    return buf.read(), sr, prompt


# ─── Warm-up khi Django start ─────────────────────────────────────────────────

def warmup_on_startup():
    """
    Gọi hàm này trong apps.py ready() để model được load sẵn khi server khởi động.
    Người dùng sẽ không phải chờ lần đầu.
    """
    import threading
    def _do():
        try:
            logger.info("Background warm-up: loading MusicGen...")
            load_model("facebook/musicgen-small")
            logger.info("Background warm-up complete ✓")
        except Exception as e:
            logger.warning(f"Background warm-up failed: {e}")
    t = threading.Thread(target=_do, daemon=True)
    t.start()
