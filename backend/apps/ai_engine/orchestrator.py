"""
Sonavia Studio — Core Music Generation Orchestrator
=====================================================
Điều phối toàn bộ chu trình tạo nhạc 3-Tier Multi-Engine Architecture:
1. Tier 1 (Studio Vocals + Music): ACE-Step HF Space Engine
2. Tier 2 (Local Neural Music): Meta MusicGen AI (GPU/CPU)
3. Tier 3 (Instant Harmonic Symbolic Synth): Sonavia Acoustic Synth (100% offline, zero latency, guaranteed uptime)
Prompt -> Phân tích (PromptAnalyzer) -> Lời bài hát (LyricEngine) -> Điều phối Provider -> Audio Mastering -> Kết quả hoàn chỉnh.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from .prompt_analyzer import PromptAnalyzerService
from .lyric_engine import generate_multilingual_lyrics
from .providers.suno_provider import SunoProvider
from .providers.aimlapi_provider import AimlapiProvider
from .providers.acestep_provider import AceStepProvider
from .providers.musicgen_provider import MusicGenProvider
from .providers.synth_provider import AcousticSynthProvider
from .providers.vietnamese_svs_provider import VietnameseSVSProvider
from .vietnamese_phonetics import analyze_lyrics, build_svs_phonetic_prompt, normalize_nfc

logger = logging.getLogger(__name__)


class SonaviaOrchestrator:
    """Orchestrator trung tâm quản lý việc tạo nhạc của Sonavia Studio."""

    def __init__(self):
        self.suno_provider = SunoProvider()
        self.aimlapi_provider = AimlapiProvider()
        self.primary_provider = AceStepProvider()
        self.svs_provider = VietnameseSVSProvider()
        self.fallback_provider = MusicGenProvider()
        self.synth_provider = AcousticSynthProvider()

    def generate_song(
        self,
        prompt: str,
        language: str = "auto",
        vocal: str = "auto",
        duration: int = 180,
        guidance_scale: float = 8.5,
        infer_steps: int = 60,
        seed: Optional[str] = None,
        custom_lyrics: str = "",
        instrumental: bool = False,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Quy trình xử lý hoàn chỉnh chuẩn Sonavia Studio:
        1. Phân tích ngữ nghĩa prompt.
        2. Tự động sinh lời bài hát (nếu không phải instrumental và không có custom_lyrics).
        3. Thực hiện render audio qua Provider thích hợp với chuỗi Fallback 3 tầng kiên cố.
        4. Trả về metadata và audio bytes đã được tối ưu âm thanh (Mastering).
        """
        clean_prompt = prompt.strip() if prompt else "Bài hát về tình yêu cuộc sống"
        actual_seed = str(seed).strip() if seed else str(uuid.uuid4().int % 900000000 + 100000000)

        # ── 0. TỰ ĐỘNG PHÁT HIỆN TIẾNG VIỆT TỪ CA TỪ HOẶC PROMPT ──
        # Đảm bảo nếu lời bài hát là tiếng Việt thì ngôn ngữ bắt buộc phải là 'vi',
        # tuyệt đối không để lọt sang 'en' khiến AI chọn giọng ca sĩ tiếng Anh hát tiếng Việt!
        effective_language = (language or "auto").strip().lower()
        has_vietnamese_lyrics = bool(custom_lyrics and any(ch in custom_lyrics for ch in 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ'))
        if has_vietnamese_lyrics and effective_language in ("auto", "en", ""):
            effective_language = "vi"

        # ── 1. PHÂN TÍCH PROMPT ──
        config = PromptAnalyzerService.analyze(
            prompt=clean_prompt,
            user_language=effective_language,
            user_vocal=vocal,
            is_instrumental=instrumental,
        )
        if effective_language in ("ko", "ja", "zh", "en", "vi"):
            config["language"] = effective_language
        elif has_vietnamese_lyrics and config.get("language") != "vi":
            config["language"] = "vi"

        logger.info(
            f"[SonaviaOrchestrator] Phân tích xong: Lang={config['language']}, "
            f"Genre={config['genre']}, Mood={config['mood']}, BPM={config['bpm']}"
        )

        # ── 2. PHÂN LOẠI TÁC VỤ & XỬ LÝ CA TỪ ──
        is_inst_task = bool(instrumental or config["vocal_gender"] == "instrumental")
        has_custom = bool(custom_lyrics.strip())

        if is_inst_task:
            task_type = "instrumental"
            lyrics = ""
            song_title = f"{config['genre_name']} Melody"
        elif has_custom:
            task_type = "lyrics_to_song"
            lyrics = normalize_nfc(custom_lyrics.strip())
            song_title = clean_prompt[:40]
        else:
            task_type = "text_to_song"
            structure_labels = [s["label"] for s in config.get("structure", [])]
            lyric_data = generate_multilingual_lyrics(
                language=config["language"],
                theme=config["theme"],
                genre=config["genre"],
                vocal_gender=config["vocal_gender"],
                user_prompt=clean_prompt,
                structure_labels=structure_labels if structure_labels else None,
            )
            lyrics = normalize_nfc(lyric_data["lyrics"])
            song_title = lyric_data["title"]

        # Phân tích ngữ âm tiếng Việt nếu có ca từ
        phonetic_report = None
        if effective_language in ("ko", "ja", "zh", "en"):
            config["language"] = effective_language
            is_vietnamese = False
        else:
            is_vietnamese = config.get("language") == "vi" or bool(lyrics and any(ch in lyrics for ch in 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ'))
            if is_vietnamese:
                config["language"] = "vi"

        if is_vietnamese and lyrics:
            try:
                phonetic_report = analyze_lyrics(lyrics)
            except Exception as pe:
                logger.warning(f"[SonaviaOrchestrator] Lỗi phân tích ngữ âm: {pe}")

        # ── 3. CHỌN PROVIDER VÀ GENERATE VỚI 4-TIER MULTI-ENGINE ARCHITECTURE ──
        render_result = None

        # Xây dựng Rich Caption chuyên sâu (đặc biệt cho vocal rõ nét)
        rich_caption = ""
        try:
            from .caption_builder import build_rich_caption
            rich_caption = build_rich_caption(config, quality="balanced")
        except Exception as cb_err:
            logger.warning(f"[SonaviaOrchestrator] build_rich_caption warning: {cb_err}")

        custom_prompt_to_use = rich_caption or config.get("model_prompt") or clean_prompt

        if preferred_provider == "suno" or (self.suno_provider.is_available() and preferred_provider in (None, "auto", "suno")):
            provider = self.suno_provider
        elif preferred_provider == "aimlapi" or (self.aimlapi_provider.is_available() and preferred_provider in (None, "auto", "aimlapi")):
            provider = self.aimlapi_provider
        elif preferred_provider == "synth":
            provider = self.synth_provider
        elif preferred_provider in ["vietnamese_svs", "svs"]:
            provider = self.svs_provider
        elif preferred_provider in ["acoustic_svs", "vietnamese_acoustic_svs"]:
            provider = self.svs_provider
            kwargs["use_acoustic_engine"] = True
        elif preferred_provider == "musicgen" or (instrumental and duration <= 30 and preferred_provider == "local"):
            provider = self.fallback_provider
        else:
            provider = self.primary_provider

        try:
            render_result = provider.generate(
                prompt=clean_prompt,
                lyrics=lyrics,
                duration=duration,
                genre=config["genre"],
                mood=config["mood"],
                vocal_gender=config["vocal_gender"],
                seed=actual_seed,
                custom_prompt=custom_prompt_to_use,
                guidance_scale=guidance_scale,
                infer_steps=infer_steps,
                song_config=config,
                **kwargs
            )
        except Exception as primary_err:
            logger.warning(f"[SonaviaOrchestrator] Provider chính ({getattr(provider, 'name', 'primary')}) gặp sự cố: {primary_err}")

            # Tier 2: Thử Vietnamese SVS (nếu có model checkpoint khả dụng và có lyrics tiếng Việt)
            if render_result is None and provider != self.svs_provider and self.svs_provider.is_available() and is_vietnamese and lyrics:
                logger.info("[SonaviaOrchestrator] Đang kích hoạt Tier-2: Vietnamese SVS Deep Learning...")
                try:
                    render_result = self.svs_provider.generate(
                        prompt=clean_prompt,
                        lyrics=lyrics,
                        duration=duration,
                        genre=config["genre"],
                        mood=config["mood"],
                        vocal_gender=config["vocal_gender"],
                        seed=actual_seed,
                        custom_prompt=config["model_prompt"],
                        **kwargs
                    )
                except Exception as svs_err:
                    logger.warning(f"[SonaviaOrchestrator] Vietnamese SVS fallback gặp sự cố: {svs_err}")

            # Tier 3: Fallback sang MusicGen
            if provider != self.fallback_provider:
                logger.info("[SonaviaOrchestrator] Đang kích hoạt Tier-2 Fallback: MusicGen Local AI...")
                try:
                    render_result = self.fallback_provider.generate(
                        prompt=clean_prompt,
                        lyrics=lyrics if not instrumental else "",
                        duration=min(duration, 30),
                        genre=config["genre"],
                        mood=config["mood"],
                        vocal_gender=config["vocal_gender"],
                        custom_prompt=config["model_prompt"],
                        guidance_scale=min(guidance_scale, 7.0),
                        seed=actual_seed,
                        **kwargs
                    )
                except Exception as fallback_err:
                    logger.warning(f"[SonaviaOrchestrator] MusicGen fallback gặp sự cố: {fallback_err}")

            # Tier 4: Fallback kiên cố sang Sonavia Acoustic Harmonic Synthesizer
            if render_result is None:
                logger.info("[SonaviaOrchestrator] Đang kích hoạt Tier-3 Fallback: Sonavia Acoustic Synth...")
                try:
                    render_result = self.synth_provider.generate(
                        prompt=clean_prompt,
                        lyrics=lyrics,
                        duration=min(duration, 60),
                        genre=config["genre"],
                        mood=config["mood"],
                        vocal_gender=config["vocal_gender"],
                        seed=actual_seed,
                        custom_prompt=config["model_prompt"],
                        **kwargs
                    )
                except Exception as synth_err:
                    logger.error(f"[SonaviaOrchestrator] Mọi provider đều thất bại: {synth_err}")
                    raise RuntimeError("Hệ thống AI âm nhạc đang bảo trì. Vui lòng thử lại sau giây lát.") from primary_err

        audio_bytes = render_result["audio_bytes"]
        already_mastered = render_result.get("mastered", False)
        # Chỉ master đúng 1 lần duy nhất để bảo toàn độ trong trẻo, triệt tiêu méo tiếng do double-mastering
        if not already_mastered:
            try:
                from .audio_mastering import master_audio_bytes
                is_vi = (config.get("language") == "vi" or bool(lyrics and any(c in lyrics for c in 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ'))) and (effective_language not in ("ko", "ja", "zh", "en"))
                audio_bytes = master_audio_bytes(
                    audio_bytes,
                    is_vietnamese=is_vi,
                    output_format=render_result.get("format", "mp3"),
                )
            except Exception as master_err:
                logger.warning(f"[SonaviaOrchestrator] Audio mastering warning: {master_err}")

        # Xác định minh bạch trạng thái vocal (Phase 2.2A)
        provider_name = render_result.get("provider", getattr(provider, "name", "sonavia-engine"))
        is_acestep = (provider_name == "acestep")
        has_vocal_requested = bool(lyrics and not instrumental and config.get("vocal_gender") != "instrumental")

        if is_acestep and has_vocal_requested:
            vocal_type = "vocal"
            vocal_generated = True
            fallback_reason = None
        elif render_result.get("vocal_type"):
            vocal_type = render_result["vocal_type"]
            vocal_generated = render_result.get("vocal_generated", False)
            fallback_reason = render_result.get("fallback_reason")
        elif has_vocal_requested:
            vocal_type = "melodic_lead"
            vocal_generated = False
            fallback_reason = "no_compatible_vietnamese_svs"
        else:
            vocal_type = "instrumental"
            vocal_generated = False
            fallback_reason = None

        return {
            "title": song_title,
            "lyrics": lyrics,
            "audio_bytes": audio_bytes,
            "duration": render_result.get("duration", duration),
            "elapsed": render_result.get("elapsed", 0),
            "seed": render_result.get("seed", actual_seed),
            "format": render_result.get("format", "mp3"),
            "provider": provider_name,
            "config": config,
            "task_type": task_type,
            "vocal_type": vocal_type,
            "vocal_generated": vocal_generated,
            "fallback_reason": fallback_reason,
            "phonetic_summary": phonetic_report.phonetic_summary if phonetic_report else None,
            "tone_distribution": phonetic_report.tone_distribution if phonetic_report else None,
        }


# Singleton instance
sonavia_orchestrator = SonaviaOrchestrator()
