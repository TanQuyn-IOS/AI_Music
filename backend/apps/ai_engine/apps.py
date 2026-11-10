from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AiEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_engine'
    verbose_name = 'AI Engine'

    def ready(self):
        """
        Gọi khi Django server khởi động.
        Load MusicGen vào VRAM ngay + warm-up ACE-Step connection.
        """
        import os
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('DJANGO_WARMUP') == '1':
            try:
                from .music_generator import warmup_on_startup
                warmup_on_startup()
            except Exception as e:
                logger.warning(f"MusicGen warm-up skipped: {e}")
            try:
                from .acestep_generator import warmup_acestep
                warmup_acestep()
            except Exception as e:
                logger.warning(f"ACE-Step warm-up skipped: {e}")
