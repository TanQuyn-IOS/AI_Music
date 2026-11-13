"""
Sonavia Studio — AI/ML API Music Provider (MiniMax Music 2.0 / ElevenLabs Music)
================================================================================
Tích hợp trực tiếp các mô hình AI âm nhạc thế hệ mới từ AIMLAPI:
- MiniMax Music 2.0 (hỗ trợ tạo nhạc có lời bài hát, nhiều thể loại)
- ElevenLabs Music
"""

import os
import time
import logging
try:
    import requests
except ImportError:
    requests = None
from typing import Dict, Any, Optional
from .base_provider import BaseMusicProvider

logger = logging.getLogger(__name__)


class AimlapiProvider(BaseMusicProvider):
    name = "aimlapi"
    has_vocals = True
    supports_multilingual = True

    def __init__(self):
        self._load_config()

    def _load_config(self):
        self.api_key = os.environ.get("AIMLAPI_KEY", "").strip()
        self.model = os.environ.get("AIMLAPI_MODEL", "minimax/music-2.0").strip()
        self.base_url = "https://api.aimlapi.com/v2/generate/audio"

    def is_available(self) -> bool:
        """Kiểm tra xem người dùng đã cung cấp AIMLAPI_KEY chưa."""
        if requests is None:
            return False
        self._load_config()
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        lyrics: str = "",
        duration: int = 180,
        genre: str = "pop",
        mood: str = "happy",
        vocal_gender: str = "male",
        seed: Optional[str] = None,
        custom_prompt: str = "",
        guidance_scale: float = 14.5,
        infer_steps: int = 60,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Gửi yêu cầu tạo nhạc đến AIMLAPI và poll kết quả âm thanh MP3.
        """
        self._load_config()
        if not self.is_available():
            raise RuntimeError("AIMLAPI_KEY chưa được cấu hình trong file .env.")

        t0 = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        final_prompt = custom_prompt or prompt or "Acoustic Pop, cheerful atmosphere"
        payload = {
            "model": self.model,
            "prompt": final_prompt[:1800],
        }

        # Nếu có ca từ, gửi kèm theo model MiniMax
        if lyrics.strip():
            payload["lyrics"] = lyrics.strip()[:2800]

        logger.info(f"[AimlapiProvider] Gửi yêu cầu tới AIMLAPI (Model: {self.model})...")

        try:
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 403:
                data = resp.json()
                msg = data.get("message") or "Tài khoản AIMLAPI của bạn chưa có số dư (Insufficient credits). Vui lòng nạp thêm tiền tại https://aimlapi.com/app/billing/ để tiếp tục."
                raise PermissionError(msg)
            resp.raise_for_status()
            res_data = resp.json()
        except requests.HTTPError as he:
            raise RuntimeError(f"Lỗi phản hồi từ AIMLAPI: {he.response.text}") from he
        except Exception as e:
            raise RuntimeError(f"Không thể kết nối tới AIMLAPI: {e}") from e

        generation_id = res_data.get("id") or res_data.get("generation_id")
        if not generation_id:
            # Trường hợp trả về trực tiếp url
            audio_url = res_data.get("audio_url") or res_data.get("audio_file", {}).get("url")
            if not audio_url:
                raise RuntimeError(f"AIMLAPI không trả về generation_id hợp lệ: {res_data}")
        else:
            # Poll kết quả theo vòng lặp
            logger.info(f"[AimlapiProvider] Task khởi tạo thành công (ID: {generation_id}). Bắt đầu polling...")
            audio_url = ""
            poll_url = f"{self.base_url}?generation_id={generation_id}"

            for _ in range(60):
                time.sleep(5)
                try:
                    p_resp = requests.get(poll_url, headers=headers, timeout=15)
                    if p_resp.status_code == 200:
                        p_data = p_resp.json()
                        st = str(p_data.get("status", "")).lower()
                        if st == "completed":
                            audio_url = (
                                p_data.get("audio_file", {}).get("url")
                                or p_data.get("audio_url")
                                or p_data.get("url")
                            )
                            break
                        elif st in ("error", "failed"):
                            err_msg = p_data.get("error", "Unknown error")
                            raise RuntimeError(f"AIMLAPI task thất bại: {err_msg}")
                except Exception as pe:
                    logger.debug(f"[AimlapiProvider] Polling: {pe}")

        if not audio_url:
            raise TimeoutError("Hết thời gian chờ AIMLAPI hoàn thành render audio.")

        # Tải bytes âm thanh
        audio_res = requests.get(audio_url, timeout=45)
        audio_res.raise_for_status()
        audio_bytes = audio_res.content

        return {
            "audio_bytes": audio_bytes,
            "duration": duration,
            "elapsed": round(time.time() - t0, 1),
            "prompt": prompt,
            "seed": seed or str(int(time.time())),
            "lyrics": lyrics,
            "format": "mp3",
            "provider": self.name,
            "mastered": True,
        }

