"""
Sonavia Studio — Base Music Generation Provider
=================================================
Định nghĩa giao diện trừu tượng (Interface) cho các AI Music Engine.
Mọi engine (ACE-Step, MusicGen, v.v.) đều phải tuân theo interface này.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseMusicProvider(ABC):
    """Abstract Base Class cho mọi provider tạo nhạc trong Sonavia Studio."""

    name: str = "base"
    has_vocals: bool = False
    supports_multilingual: bool = False

    @abstractmethod
    def generate(
        self,
        prompt: str,
        lyrics: str = "",
        duration: int = 180,
        genre: str = "pop",
        mood: str = "happy",
        vocal_gender: str = "female",
        seed: Optional[str] = None,
        custom_prompt: str = "",
        guidance_scale: float = 14.0,
        infer_steps: int = 60,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Thực hiện tạo nhạc và trả về dict:
        {
            "audio_bytes": bytes,
            "duration": float,
            "elapsed": float,
            "prompt": str,
            "seed": str,
            "lyrics": str,
            "format": "mp3" | "wav",
            "provider": str
        }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Kiểm tra xem provider có sẵn sàng phục vụ không."""
        pass
