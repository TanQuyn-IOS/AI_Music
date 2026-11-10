"""
Sonavia Studio — ACE-Step Music Provider
==========================================
Wrapper cho ACE-Step HF Space Engine:
- Tạo nhạc kèm giọng hát thật studio-grade
- Đa ngôn ngữ (vi, ko, ja, zh, en)
- Quality presets: fast / balanced / high
- Fast Health Probe & Circuit Breaker: Loại bỏ hoàn toàn độ trễ 60s khi mất mạng.
"""

import logging
from typing import Dict, Any, Optional
from .base_provider import BaseMusicProvider
from ..acestep_generator import generate_with_acestep, is_acestep_available

logger = logging.getLogger(__name__)


class AceStepProvider(BaseMusicProvider):
    name = "acestep"
    has_vocals = True
    supports_multilingual = True

    def generate(
        self,
        prompt: str,
        lyrics: str = "",
        duration: int = 0,          # 0 = auto
        genre: str = "pop",
        mood: str = "happy",
        vocal_gender: str = "female",
        seed: Optional[str] = None,
        custom_prompt: str = "",
        guidance_scale: Optional[float] = None,
        infer_steps: Optional[int] = None,
        quality: str = "balanced",
        song_config: Optional[Dict] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        result = generate_with_acestep(
            prompt=prompt,
            lyrics=lyrics,
            duration=duration,
            genre=genre,
            mood=mood,
            instruments=kwargs.get("instruments", "full"),
            custom_prompt=custom_prompt,
            guidance_scale=guidance_scale,
            infer_steps=infer_steps,
            seed=seed or "",
            vocal_gender=vocal_gender,
            quality=quality,
            song_config=song_config,
        )
        result["format"] = "mp3"
        result["provider"] = self.name
        return result

    def is_available(self) -> bool:
        """
        Kiểm tra trạng thái Space HF nhanh chóng (<2.0s) kèm Circuit Breaker.
        Ngăn chặn hoàn toàn việc treo tiến trình hoặc blocking UI khi mất kết nối mạng.
        """
        try:
            return is_acestep_available(fast=True)
        except Exception as e:
            logger.debug(f"[AceStepProvider] is_available check failed: {e}")
            return False
