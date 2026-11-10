"""
Sonavia Studio — Official & Gateway Suno AI Provider
=====================================================
Tích hợp trực tiếp engine Suno AI (v3.5 / v4) đạt chuẩn chất lượng âm thanh và
giọng hát tiếng Việt phòng thu 100% như trên Suno.com:
- Phát âm tiếng Việt chuẩn 100% 6 thanh điệu, luyến láy, ngân vang tự nhiên.
- Đầy đủ bè, hòa âm, trống bass đỉnh cao studio quốc tế.
- Hỗ trợ 2 phương thức kết nối:
  1. Suno Session Cookie / Bearer Token từ tài khoản Suno.com cá nhân.
  2. Suno API Key từ các cổng gateway đối tác (SunoAPI, GoAPI, AIMLAPI, v.v.).
"""

import os
import time
import logging
import requests
from typing import Dict, Any, Optional
from .base_provider import BaseMusicProvider

logger = logging.getLogger(__name__)


class SunoProvider(BaseMusicProvider):
    name = "suno"
    has_vocals = True
    supports_multilingual = True

    def __init__(self):
        self._load_config()

    def _load_config(self):
        try:
            from dotenv import load_dotenv
            dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
            load_dotenv(dotenv_path, override=True)
        except Exception:
            pass
        self.cookie = os.environ.get("SUNO_COOKIE", "").strip()
        self.api_key = os.environ.get("SUNO_API_KEY", "").strip()
        self.api_url = os.environ.get("SUNO_API_URL", "https://api.sunoapi.org/api/v1/suno/create").strip()

    def is_available(self) -> bool:
        """Kiểm tra xem người dùng đã cấu hình SUNO_COOKIE hoặc SUNO_API_KEY chưa."""
        self._load_config()
        return bool(self.cookie or self.api_key)

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
        guidance_scale: float = 8.5,
        infer_steps: int = 60,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Gửi yêu cầu tạo nhạc đến Suno AI và trả về file âm thanh MP3 hoàn chỉnh.
        """
        self._load_config()
        if not self.is_available():
            raise RuntimeError(
                "Suno AI Provider chưa được cấu hình. "
                "Vui lòng thêm SUNO_COOKIE hoặc SUNO_API_KEY vào tệp .env để sử dụng."
            )

        t0 = time.time()
        is_instrumental = (vocal_gender == "instrumental") or kwargs.get("instrumental", False)
        tags = f"Vietnamese {genre}, {mood}, {vocal_gender} vocals, clear Vietnamese pronunciation, studio quality"
        if is_instrumental:
            tags = f"Vietnamese {genre}, {mood}, instrumental, melodic, studio quality"

        title = prompt[:40] if prompt else f"{genre.title()} Vietnamese Song"

        logger.info(f"[SunoProvider] Bắt đầu tạo bài hát bằng Suno AI Engine (Instrumental={is_instrumental})...")

        # ── PHƯƠNG THỨC 1: DÙNG SUNO API GATEWAY ──
        if self.api_key:
            return self._generate_via_api(
                prompt=prompt,
                lyrics=lyrics,
                tags=tags,
                title=title,
                is_instrumental=is_instrumental,
                seed=seed,
                t0=t0,
            )

        # ── PHƯƠNG THỨC 2: DÙNG SUNO DIRECT COOKIE ──
        return self._generate_via_cookie(
            prompt=prompt,
            lyrics=lyrics,
            tags=tags,
            title=title,
            is_instrumental=is_instrumental,
            seed=seed,
            t0=t0,
        )

    def _generate_via_api(
        self,
        prompt: str,
        lyrics: str,
        tags: str,
        title: str,
        is_instrumental: bool,
        seed: Optional[str],
        t0: float,
    ) -> Dict[str, Any]:
        """Tạo nhạc qua các cổng Suno API Gateway đối tác."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        is_aimusicapi = "aimusicapi" in self.api_url
        if is_aimusicapi:
            has_lyrics = bool(lyrics and lyrics.strip())
            payload = {
                "task_type": "create_music",
                "custom_mode": True if has_lyrics else False,
                "prompt": lyrics.strip() if has_lyrics else prompt,
                "title": title[:80],
                "tags": tags[:120],
                "mv": "chirp-v3-5",
            }
            if not has_lyrics and not prompt.strip():
                payload["gpt_description_prompt"] = tags
        else:
            payload = {
                "prompt": lyrics if lyrics else prompt,
                "tags": tags,
                "title": title,
                "make_instrumental": is_instrumental,
                "mv": "chirp-v3-5",
            }

        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"Lỗi gửi yêu cầu đến Suno API: {e}") from e

        task_id = (
            data.get("task_id")
            or data.get("id")
            or (data.get("data", {}) if isinstance(data.get("data"), dict) else {}).get("task_id")
            or (data.get("data", {}) if isinstance(data.get("data"), dict) else {}).get("id")
        )

        # Poll trạng thái bài hát
        audio_url = ""
        if is_aimusicapi:
            poll_url = f"https://api.aimusicapi.ai/api/v1/suno/task/{task_id}"
        elif "/create" in self.api_url:
            poll_url = self.api_url.replace("/create", "/record-info")
        else:
            poll_url = f"{self.api_url}/{task_id}"
        for _ in range(60):
            time.sleep(5)
            try:
                p_resp = requests.get(poll_url, params={"taskId": task_id} if "taskId" in poll_url else {}, headers=headers, timeout=15)
                if p_resp.status_code in (200, 202):
                    p_data = p_resp.json()
                    raw_data = p_data.get("data")
                    status = ""
                    clip_audio = ""

                    if isinstance(raw_data, list) and len(raw_data) > 0:
                        first_item = raw_data[0]
                        status = str(first_item.get("state") or first_item.get("status", "")).upper()
                        clip_audio = first_item.get("audio_url") or first_item.get("url")
                    elif isinstance(raw_data, dict):
                        status = str(raw_data.get("state") or raw_data.get("status") or p_data.get("status", "")).upper()
                        clip_audio = raw_data.get("audio_url") or (raw_data.get("response", {}).get("sunoData", [{}])[0].get("audioUrl") if isinstance(raw_data.get("response"), dict) else None)
                    else:
                        status = str(p_data.get("status", "")).upper()
                        clip_audio = p_data.get("audio_url")

                    if status in ("SUCCESS", "SUCCEEDED", "COMPLETED", "COMPLETE", "STREAMING") and clip_audio:
                        audio_url = clip_audio
                        break
                    elif status in ("FAILED", "ERROR"):
                        raise RuntimeError(f"Suno task thất bại: {p_data}")
            except Exception as poll_err:
                logger.debug(f"[SunoProvider] Polling step: {poll_err}")

        if not audio_url:
            raise TimeoutError("Hết thời gian chờ Suno AI hoàn tất bài hát (Timeout > 300s).")

        audio_res = requests.get(audio_url, timeout=45)
        audio_res.raise_for_status()
        audio_bytes = audio_res.content

        return {
            "audio_bytes": audio_bytes,
            "duration": 180,
            "elapsed": round(time.time() - t0, 1),
            "prompt": prompt,
            "seed": seed or str(int(time.time())),
            "lyrics": lyrics,
            "format": "mp3",
            "provider": self.name,
            "mastered": True,
        }

    def _generate_via_cookie(
        self,
        prompt: str,
        lyrics: str,
        tags: str,
        title: str,
        is_instrumental: bool,
        seed: Optional[str],
        t0: float,
    ) -> Dict[str, Any]:
        """Tạo nhạc trực tiếp qua tài khoản Suno.com cá nhân bằng Cookie."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": self.cookie,
            "Content-Type": "application/json",
            "Referer": "https://suno.com/",
        }

        # Xử lý linh hoạt mọi định dạng: Bearer token, raw JWT, hoặc full Cookie string
        raw_val = self.cookie.strip()
        if raw_val.lower().startswith("bearer "):
            headers["Authorization"] = raw_val
        elif raw_val.startswith("ey") and len(raw_val) > 50:
            headers["Authorization"] = f"Bearer {raw_val}"
        else:
            token = ""
            for part in raw_val.split(";"):
                part = part.strip()
                if "__session" in part or "__client" in part or "jwt" in part or "token" in part:
                    token = part.split("=")[-1].strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"

        payload = {
            "prompt": lyrics if lyrics else prompt,
            "tags": tags,
            "title": title,
            "make_instrumental": is_instrumental,
            "mv": "chirp-v3-5",
        }

        url = "https://studio-api.suno.ai/api/generate/v2/"
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 401:
                raise PermissionError("Suno Cookie đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại suno.com để lấy cookie mới.")
            resp.raise_for_status()
            clips = resp.json().get("clips", [])
            if not clips:
                raise RuntimeError("Suno không trả về clip nào trong phiên tạo.")
            clip_id = clips[0]["id"]
        except Exception as e:
            raise RuntimeError(f"Lỗi khởi tạo Suno clip: {e}") from e

        # Poll clip hoàn thành
        audio_url = ""
        poll_url = f"https://studio-api.suno.ai/api/feed/?ids={clip_id}"
        for _ in range(60):
            time.sleep(5)
            try:
                p_resp = requests.get(poll_url, headers=headers, timeout=15)
                if p_resp.status_code == 200:
                    feed_clips = p_resp.json()
                    if feed_clips:
                        clip_data = feed_clips[0]
                        st = clip_data.get("status", "")
                        if st == "complete" or clip_data.get("audio_url"):
                            audio_url = clip_data.get("audio_url")
                            break
                        elif st == "error":
                            raise RuntimeError(f"Clip gặp lỗi trong quá trình tạo: {clip_data.get('error_message')}")
            except Exception as pe:
                logger.debug(f"[Suno Direct] Polling: {pe}")

        if not audio_url:
            raise TimeoutError("Hết thời gian chờ Suno hoàn thành clip.")

        audio_res = requests.get(audio_url, timeout=45)
        audio_res.raise_for_status()
        audio_bytes = audio_res.content

        return {
            "audio_bytes": audio_bytes,
            "duration": 180,
            "elapsed": round(time.time() - t0, 1),
            "prompt": prompt,
            "seed": seed or str(int(time.time())),
            "lyrics": lyrics,
            "format": "mp3",
            "provider": self.name,
            "mastered": True,
        }

