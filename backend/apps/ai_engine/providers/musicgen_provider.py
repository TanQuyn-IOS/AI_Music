"""
Sonavia Studio — MusicGen Provider (Local Fallback)
===================================================
Wrapper cho Meta MusicGen (chạy local GPU/CPU):
- Dùng làm fallback khi mất kết nối mạng hoặc hết hạn ngạch cloud
- Tạo nhạc không lời chất lượng cao
"""

import io
import re
import time
import logging
from typing import Dict, Any, Optional
from .base_provider import BaseMusicProvider

logger = logging.getLogger(__name__)


def _clean_lyrics_hint(lyrics: str) -> str:
    if not lyrics:
        return ""
    text = re.sub(r"\[[^\]]*\]", " ", lyrics)
    text = re.sub(r"[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐA-Za-z0-9]", " ", text)
    words = [w for w in text.split() if len(w) > 2][:18]
    return ", ".join(words)


class MusicGenProvider(BaseMusicProvider):
    name = "musicgen"
    has_vocals = False
    supports_multilingual = False

    def generate(
        self,
        prompt: str,
        lyrics: str = "",
        duration: int = 30,
        genre: str = "pop",
        mood: str = "happy",
        vocal_gender: str = "female",
        seed: Optional[str] = None,
        custom_prompt: str = "",
        guidance_scale: float = 3.5,
        infer_steps: int = 60,
        **kwargs: Any
    ) -> Dict[str, Any]:
        from ..music_generator import generate_music

        t0 = time.time()
        base_prompt = custom_prompt or prompt
        lyric_hint = _clean_lyrics_hint(lyrics)
        melody_hint = (
            "warm melodic lead, smooth vocal-like phrasing, natural legato, expressive rise and fall, "
            "gentle dynamics, soft emotional cadence"
        )
        final_prompt = f"{base_prompt}, {melody_hint}"
        if lyric_hint:
            final_prompt = f"{final_prompt}, lyric themes: {lyric_hint}"
        dur = min(duration, 30)

        gen_out = generate_music(
            prompt=final_prompt,
            duration=dur,
            guidance_scale=min(guidance_scale, 3.8),
            temperature=0.9,
            model_name=kwargs.get("model", "facebook/musicgen-small"),
        )
        wav_bytes = gen_out[0] if isinstance(gen_out, (tuple, list)) else gen_out

        # Phase 2.2A: Loại bỏ Bark hoàn toàn khỏi MusicGenProvider.
        # MusicGen là mô hình tạo nhạc nền (Instrumental / Melodic Lead).
        # Tuyệt đối không gọi Bark để tạo vocal tiếng Việt do hạn chế thanh điệu và phát âm.
        # Khi có lyrics và yêu cầu vocal, hệ thống chuyển sang chế độ Melodic Lead (nhạc cụ dẫn dắt giai điệu).
        has_melodic_lead = bool("melodic lead" in final_prompt)
        is_vocal_requested = bool(lyrics and lyrics.strip() and vocal_gender != "instrumental")

        vocal_type = "melodic_lead" if (is_vocal_requested and has_melodic_lead) else "instrumental"
        vocal_generated = False
        fallback_reason = "no_compatible_vietnamese_svs" if is_vocal_requested else None

        if is_vocal_requested:
            logger.info(
                "[MusicGenProvider] Chưa có mô hình SVS tiếng Việt tương thích. "
                "Tạo bản nhạc nền Melodic Lead chất lượng cao (không dùng Bark)."
            )

        elapsed = round(time.time() - t0, 1)

        return {
            "audio_bytes": wav_bytes,
            "duration": dur,
            "elapsed": elapsed,
            "prompt": final_prompt,
            "seed": seed or "0",
            "lyrics": lyrics or "",
            "format": "wav",
            "provider": self.name,
            "mastered": True,
            "vocal_type": vocal_type,
            "vocal_generated": vocal_generated,
            "fallback_reason": fallback_reason,
        }

    def is_available(self) -> bool:
        try:
            from ..music_generator import load_model
            return True
        except Exception:
            return False
