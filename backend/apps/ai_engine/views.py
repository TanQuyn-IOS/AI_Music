from .header_utils import safe_header_val, safe_content_disposition
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.http import HttpResponse
import threading
import uuid
import time as _time
import logging
from apps.music.models import Song, ListenHistory
from apps.music.serializers import SongSerializer

logger = logging.getLogger(__name__)
from .recommender import (
    get_content_based_recommendations,
    get_user_based_recommendations,
    get_mood_based_recommendations,
    get_music_profile,
)
from .chatbot import get_chatbot_response
from .music_composer import generate_midi, generate_lyrics, NOTES, PROGRESSIONS, MOOD_TO_TEMPO


class RecommendSimilarView(APIView):
    """Đề xuất bài tương tự dựa trên content"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, song_id):
        try:
            target_song = Song.objects.get(pk=song_id, is_published=True)
        except Song.DoesNotExist:
            return Response({'error': 'Không tìm thấy bài hát.'}, status=404)

        all_songs = list(Song.objects.filter(is_published=True))
        recommended = get_content_based_recommendations(target_song, all_songs, top_n=10)
        serializer = SongSerializer(recommended, many=True, context={'request': request})
        return Response({'recommendations': serializer.data, 'based_on': target_song.title})


class RecommendForUserView(APIView):
    """Đề xuất dựa trên lịch sử nghe của user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        history = list(
            ListenHistory.objects.filter(user=request.user)
            .select_related('song', 'song__artist')
            .order_by('-listened_at')[:50]
        )
        all_songs = list(Song.objects.filter(is_published=True).select_related('artist'))
        recommended = get_user_based_recommendations(request.user, all_songs, history, top_n=15)
        serializer = SongSerializer(recommended, many=True, context={'request': request})
        return Response({'recommendations': serializer.data})


class RecommendByMoodView(APIView):
    """Đề xuất theo mood"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        mood = request.query_params.get('mood', '')
        if not mood:
            return Response({'error': 'Vui lòng cung cấp mood.'}, status=400)

        all_songs = list(Song.objects.filter(is_published=True).select_related('artist'))
        recommended = get_mood_based_recommendations(mood, all_songs, top_n=10)
        serializer = SongSerializer(recommended, many=True, context={'request': request})
        return Response({'recommendations': serializer.data, 'mood': mood})


class MusicProfileView(APIView):
    """Hồ sơ sở thích âm nhạc của user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        history = list(
            ListenHistory.objects.filter(user=request.user)
            .select_related('song')
            .order_by('-listened_at')[:100]
        )
        profile = get_music_profile(history)
        return Response(profile)


class ChatbotView(APIView):
    """AI Chatbot tư vấn âm nhạc"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'Vui lòng nhập tin nhắn.'}, status=400)

        songs = list(Song.objects.filter(is_published=True).select_related('artist')[:100])
        response = get_chatbot_response(message, songs)
        return Response(response)


# ─── AI Composer Views ─────────────────────────────────────────────────────

class ComposeLyricsView(APIView):
    """AI tạo lời bài hát"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        mood = request.data.get('mood', 'happy')
        genre = request.data.get('genre', 'pop')
        title = request.data.get('title', '')
        num_verses = int(request.data.get('num_verses', 2))
        has_chorus = request.data.get('has_chorus', True)
        if isinstance(has_chorus, str):
            has_chorus = has_chorus.lower() != 'false'

        try:
            result = generate_lyrics(
                mood=mood,
                genre=genre,
                title=title,
                num_verses=min(num_verses, 3),
                has_chorus=has_chorus,
            )
            return Response(result)
        except Exception as e:
            return Response({'error': f'Lỗi tạo lời: {str(e)}'}, status=500)


class ComposeMidiView(APIView):
    """AI tạo file MIDI nhạc"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        genre = request.data.get('genre', 'pop')
        mood = request.data.get('mood', 'happy')
        root_note = request.data.get('root_note', 'C')
        num_bars = int(request.data.get('num_bars', 16))
        bpm = request.data.get('bpm')
        bpm = int(bpm) if bpm else None

        # Validate
        if root_note not in NOTES:
            root_note = 'C'
        num_bars = max(4, min(num_bars, 64))

        try:
            midi_bytes = generate_midi(
                genre=genre,
                mood=mood,
                root_note=root_note,
                num_bars=num_bars,
                bpm=bpm,
            )
            filename = f"ai_music_{genre}_{mood}_{root_note}.mid"
            response = HttpResponse(midi_bytes, content_type='audio/midi')
            response['Content-Disposition'] = safe_content_disposition(filename, disposition='attachment')
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            return response
        except Exception as e:
            return Response({'error': f'Lỗi tạo MIDI: {str(e)}'}, status=500)


class ComposePreviewView(APIView):
    """Preview thông tin bản nhạc trước khi tạo MIDI"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        genre = request.data.get('genre', 'pop')
        mood = request.data.get('mood', 'happy')
        root_note = request.data.get('root_note', 'C')
        num_bars = int(request.data.get('num_bars', 16))
        bpm = request.data.get('bpm')

        from .music_composer import (
            build_progression, get_scale, NOTES,
            MOOD_TO_MODE, MOOD_TO_TEMPO, SCALE_INTERVALS
        )

        root_idx = NOTES.index(root_note) if root_note in NOTES else 0
        root_midi = 48 + root_idx
        mode = MOOD_TO_MODE.get(mood, 'major')
        tempo = int(bpm) if bpm else MOOD_TO_TEMPO.get(mood, 120)

        scale_notes = get_scale(root_midi, mode)
        chords = build_progression(genre, root_midi, mode)

        # Chuyển MIDI numbers về tên nốt
        def midi_to_name(n):
            return NOTES[n % 12] + str(n // 12 - 1)

        chord_names = []
        for chord in chords:
            root_name = NOTES[chord[0] % 12]
            chord_names.append(root_name)

        scale_names = [NOTES[n % 12] for n in scale_notes]
        estimated_duration = round((num_bars * 4 / tempo) * 60, 1)

        return Response({
            'genre': genre,
            'mood': mood,
            'root_note': root_note,
            'mode': mode,
            'bpm': tempo,
            'num_bars': num_bars,
            'scale': scale_names,
            'chord_progression': chord_names,
            'estimated_duration_seconds': estimated_duration,
            'tracks': ['Chords (Piano)', 'Melody (Piano)', 'Bass (Electric Bass)'],
        })


class ComposerOptionsView(APIView):
    """Trả về các options cho composer"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'genres': list(PROGRESSIONS.keys()),
            'moods': list(MOOD_TO_TEMPO.keys()),
            'notes': NOTES,
            'num_bars_options': [4, 8, 16, 32, 64],
        })


# ─── MusicGen AI Generate Views ───────────────────────────────────────────────

class MusicGenerateView(APIView):
    """
    Tạo nhạc thật bằng MusicGen AI.
    POST /ai/generate/music/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import traceback

        genre      = request.data.get('genre', 'pop')
        mood       = request.data.get('mood', 'happy')
        tempo      = request.data.get('tempo', 'medium')
        instruments= request.data.get('instruments', 'full')
        custom     = request.data.get('custom_prompt', '').strip()
        duration   = int(request.data.get('duration', 15))   # Mặc định 15s (nhanh hơn 30s gấp đôi)
        guidance   = float(request.data.get('guidance_scale', 3.0))
        temperature= float(request.data.get('temperature', 1.0))
        model_name = request.data.get('model', 'facebook/musicgen-small')

        # Validate
        duration = max(5, min(duration, 30))
        guidance = max(1.0, min(guidance, 10.0))
        temperature = max(0.5, min(temperature, 2.0))

        try:
            from .music_generator import generate_music_full
            result = generate_music_full(
                genre=genre,
                mood=mood,
                tempo=tempo,
                instruments=instruments,
                custom_prompt=custom,
                duration=duration,
                guidance_scale=guidance,
                temperature=temperature,
                model_name=model_name,
            )

            # Trả về WAV audio & lưu vào media/generated để không bị mất khi reload
            from django.http import HttpResponse
            from django.conf import settings
            import os

            audio_url = ""
            try:
                gen_dir = os.path.join(settings.MEDIA_ROOT, 'generated')
                os.makedirs(gen_dir, exist_ok=True)
                file_name = f"musicgen_{uuid.uuid4().hex[:10]}.wav"
                file_path = os.path.join(gen_dir, file_name)
                with open(file_path, 'wb') as f:
                    f.write(result['audio'])
                audio_url = f"{settings.MEDIA_URL}generated/{file_name}"
            except Exception as save_err:
                logger.warning(f"Could not persist MusicGen audio: {save_err}")

            resp = HttpResponse(result['audio'], content_type='audio/wav')
            resp['Content-Disposition'] = safe_content_disposition(f"ai_music_{genre}_{mood}.wav", disposition="inline")
            resp['X-Prompt'] = safe_header_val(result['prompt'][:200])
            resp['X-Duration'] = str(result['duration'])
            resp['X-Model'] = safe_header_val(result['model'])
            if audio_url:
                resp['X-Audio-Url'] = safe_header_val(audio_url)
            resp['Access-Control-Expose-Headers'] = 'X-Prompt, X-Duration, X-Model, X-Audio-Url, Content-Disposition'
            return resp

        except Exception as e:
            tb = traceback.format_exc()
            return Response({
                'error': f'Lỗi tạo nhạc: {str(e)}',
                'detail': tb[-500:] if len(tb) > 500 else tb
            }, status=500)
class MusicGeneratePreviewView(APIView):
    """Preview prompt sẽ được gửi vào MusicGen trước khi generate."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .music_generator import build_prompt
        genre      = request.data.get('genre', 'pop')
        mood       = request.data.get('mood', 'happy')
        tempo      = request.data.get('tempo', 'medium')
        instruments= request.data.get('instruments', 'full')
        custom     = request.data.get('custom_prompt', '').strip()

        prompt = build_prompt(genre, mood, tempo, instruments, custom)
        return Response({
            'prompt': prompt,
            'genre': genre,
            'mood': mood,
            'tempo': tempo,
            'instruments': instruments,
        })


class MusicGenerateStatusView(APIView):
    """Kiểm tra model đã load chưa + thông tin GPU."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .music_generator import _model, _model_name, _device, _audio_cache
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            gpu_name  = torch.cuda.get_device_name(0) if cuda_available else None
            vram_total= round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1) if cuda_available else 0
            vram_used = round(torch.cuda.memory_allocated(0) / 1024**3, 2) if cuda_available else 0
        except Exception:
            cuda_available = False
            gpu_name = None
            vram_total = 0
            vram_used = 0

        return Response({
            'model_loaded':  _model is not None,
            'model_name':    _model_name,
            'device':        _device,
            'cuda_available': cuda_available,
            'gpu_name':      gpu_name,
            'vram_total_gb': vram_total,
            'vram_used_gb':  vram_used,
            'cache_size':    len(_audio_cache),   # Số bài đang cache
        })


class MusicGenerateOptionsView(APIView):
    """Trả về tất cả options cho generate form."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .music_generator import GENRE_PROMPTS, MOOD_PROMPTS, TEMPO_PROMPTS, INSTRUMENT_PROMPTS
        return Response({
            'genres': list(GENRE_PROMPTS.keys()),
            'moods': list(MOOD_PROMPTS.keys()),
            'tempos': list(TEMPO_PROMPTS.keys()),
            'instruments': list(INSTRUMENT_PROMPTS.keys()),
            'models': [
                {'id': 'facebook/musicgen-small',  'name': 'Small (Nhanh ~8-15s)', 'vram': '2GB'},
                {'id': 'facebook/musicgen-medium', 'name': 'Medium (Tốt hơn ~20s)', 'vram': '4GB'},
            ],
            'duration_range': {'min': 5, 'max': 30, 'default': 15},
        })


# ─── Full Song Generator (MusicGen + Bark) ────────────────────────────────────

# Job store (in-memory + disk cache cho audio) — {job_id: {status, progress, ...}}
_JOBS: dict = {}
_JOBS_LOCK = threading.Lock()


def _save_job_audio(job_id: str, audio_bytes, fmt: str = 'wav') -> str:
    """Lưu file âm thanh job xuống đĩa để tránh tốn RAM và cho phép phát/tải nhiều lần."""
    try:
        from django.conf import settings
        temp_dir = os.path.join(str(settings.MEDIA_ROOT), 'temp_jobs')
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{job_id}.{fmt}")
        with open(file_path, 'wb') as f:
            f.write(audio_bytes)
        return file_path
    except Exception as e:
        logger.warning(f"Failed to cache job audio to disk: {e}")
        return ""


def _cleanup_old_jobs():
    """Tự động dọn dẹp các job và file đệm cũ hơn 2 giờ để giải phóng dung lượng đĩa và RAM."""
    now = _time.time()
    with _JOBS_LOCK:
        expired = [jid for jid, info in _JOBS.items() if (now - info.get('started', now)) > 7200]
        for jid in expired:
            info = _JOBS.pop(jid, None)
            if info and info.get('audio_path') and os.path.isfile(info['audio_path']):
                try:
                    os.remove(info['audio_path'])
                except Exception:
                    pass


def _run_full_generation_job(
    job_id: str,
    genre: str, mood: str, tempo: str, instruments: str,
    custom_prompt: str, total_duration: int,
    lyrics: str, voice: str,
    with_vocal: bool,
    guidance_scale: float, temperature: float,
    model_name: str,
):
    """Hàm chạy trong background thread — tạo nhạc + giọng hát."""
    import traceback
    from .music_generator import generate_long_music_bytes, unload_model
    from .audio_mixer import mix_to_wav_bytes, music_only_to_wav_bytes

    def update(step, total, message, pct=None):
        with _JOBS_LOCK:
            _JOBS[job_id]['step']    = step
            _JOBS[job_id]['total']   = total
            _JOBS[job_id]['message'] = message
            if pct is not None:
                _JOBS[job_id]['pct'] = pct
            else:
                _JOBS[job_id]['pct'] = int(step / max(total, 1) * 100)

    try:
        # ── ƯU TIÊN SONAVIA STUDIO ORCHESTRATOR (ACE-STEP + AI MASTERING) ──
        try:
            update(1, 4, "🎤 Khởi tạo AI Engine tạo bài hát chuẩn phòng thu Sonavia...", pct=20)
            from .orchestrator import sonavia_orchestrator

            v_gender = "female"
            if voice in ["male_vi", "male_deep"]:
                v_gender = "male"
            elif voice == "duet":
                v_gender = "duet"
            elif not with_vocal:
                v_gender = "instrumental"

            update(2, 4, "🎵 AI đang hòa âm và xử lý âm thanh audiophile...", pct=50)
            orch_res = sonavia_orchestrator.generate_song(
                prompt=custom_prompt or f"{genre} {mood} music with {instruments}",
                language="vi" if (voice.endswith("_vi") or any(c in lyrics for c in 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ')) else "auto",
                vocal=v_gender,
                duration=min(total_duration, 240),
                guidance_scale=8.5,
                infer_steps=60,
                custom_lyrics=lyrics if with_vocal else "",
                instrumental=not with_vocal,
            )
            final_audio = orch_res["audio_bytes"]
            prompt_used = orch_res.get("title", custom_prompt)

            update(4, 4, "✨ Đã hoàn tất bài hát chuẩn chất lượng cao!", pct=100)
            vocal_type = orch_res.get("vocal_type", "vocal" if with_vocal else "instrumental")
            vocal_gen = orch_res.get("vocal_generated", bool(with_vocal and orch_res.get("provider") == "acestep"))
            fb_reason = orch_res.get("fallback_reason")

            final_fmt = orch_res.get("format", "mp3")
            audio_path = _save_job_audio(job_id, final_audio, final_fmt)
            with _JOBS_LOCK:
                _JOBS[job_id].update({
                    'status':          'done',
                    'pct':             100,
                    'message':         '✅ Hoàn thành bài hát!',
                    'audio':           final_audio,
                    'audio_path':      audio_path,
                    'prompt':          prompt_used,
                    'genre':           genre,
                    'mood':            mood,
                    'duration':        total_duration,
                    'format':          orch_res.get("format", "mp3"),
                    'vocal_type':      vocal_type,
                    'vocal_generated': vocal_gen,
                    'fallback_reason': fb_reason,
                })
            return
        except Exception as orch_err:
            logger.warning(f"Sonavia Orchestrator in full generation job fallback: {orch_err}")
            update(0, 10, "Đang chuyển sang engine phụ...", pct=5)

        # ── PHASE 1: Tạo nhạc nền ──────────────────────────
        update(0, 10, "🎵 Tạo nhạc nền với MusicGen...", pct=5)

        n_segments = max(1, int(total_duration / 25))

        def music_progress(step, total, msg):
            # Map sang 5-50% tổng
            pct = 5 + int(step / max(total, 1) * 45)
            update(step, total, f"🎹 {msg}", pct=pct)

        music_bytes, music_sr, prompt_used = generate_long_music_bytes(
            genre=genre, mood=mood, tempo=tempo, instruments=instruments,
            custom_prompt=custom_prompt,
            total_duration=total_duration,
            guidance_scale=guidance_scale,
            temperature=temperature,
            model_name=model_name,
            progress_callback=music_progress,
        )

        # Giải phóng VRAM trước khi chạy Bark
        update(n_segments, n_segments, "Giải phóng VRAM...", pct=50)
        unload_model()

        # ── PHASE 2: Xử lý nhạc nền (Phase 2.2A: Loại bỏ Bark khỏi fallback vocal tiếng Việt) ──
        # Tuyệt đối không gọi Bark để tạo vocal tiếng Việt do hạn chế thanh điệu và phát âm.
        # Nếu có lyrics, MusicGen sinh bản nhạc Melodic Lead với giai điệu dẫn dắt biểu cảm.
        has_melodic_lead = bool(with_vocal and lyrics.strip())
        vocal_type = "melodic_lead" if has_melodic_lead else "instrumental"
        vocal_gen = False
        fb_reason = "no_compatible_vietnamese_svs" if has_melodic_lead else None

        update(1, 1, "🎚️ Hoàn thiện bản nhạc chất lượng cao...", pct=92)
        final_wav = music_only_to_wav_bytes(music_bytes)

        msg = "✅ Hoàn thành bản nhạc (Melodic Lead)!" if has_melodic_lead else "✅ Hoàn thành bản nhạc nền!"

        audio_path = _save_job_audio(job_id, final_wav, 'wav')
        # ── DONE ──────────────────────────────────────────
        with _JOBS_LOCK:
            _JOBS[job_id].update({
                'status':          'done',
                'pct':             100,
                'message':         msg,
                'audio':           final_wav,
                'audio_path':      audio_path,
                'prompt':          prompt_used,
                'genre':           genre,
                'mood':            mood,
                'duration':        total_duration,
                'format':          'wav',
                'vocal_type':      vocal_type,
                'vocal_generated': vocal_gen,
                'fallback_reason': fb_reason,
            })

    except Exception as exc:
        tb = traceback.format_exc()
        with _JOBS_LOCK:
            _JOBS[job_id].update({
                'status':  'error',
                'message': f'Lỗi: {str(exc)}',
                'detail':  tb[-800:],
            })


class FullSongGenerateView(APIView):
    """
    Bắt đầu tạo bài nhạc đầy đủ (MusicGen + Bark) trong background.
    POST /ai/generate/full/
    Returns: { job_id }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        genre         = request.data.get('genre', 'vpop')
        mood          = request.data.get('mood', 'romantic')
        tempo         = request.data.get('tempo', 'medium')
        instruments   = request.data.get('instruments', 'full')
        custom_prompt = request.data.get('custom_prompt', '').strip()
        total_duration= int(request.data.get('total_duration', 180))  # giây (mặc định 3 phút)
        lyrics        = request.data.get('lyrics', '')
        voice         = request.data.get('voice', 'female_vi')
        with_vocal    = bool(request.data.get('with_vocal', True)) and bool(lyrics.strip())
        guidance      = float(request.data.get('guidance_scale', 3.0))
        temperature   = float(request.data.get('temperature', 1.0))
        model_name    = request.data.get('model', 'facebook/musicgen-small')

        # Validate
        total_duration = max(30, min(total_duration, 300))

        _cleanup_old_jobs()
        job_id = uuid.uuid4().hex
        with _JOBS_LOCK:
            _JOBS[job_id] = {
                'status':  'running',
                'pct':     0,
                'step':    0,
                'total':   1,
                'message': 'Đang khởi động...',
                'started': _time.time(),
            }

        # Chạy trong background thread
        t = threading.Thread(
            target=_run_full_generation_job,
            args=(
                job_id, genre, mood, tempo, instruments,
                custom_prompt, total_duration,
                lyrics, voice, with_vocal,
                guidance, temperature, model_name,
            ),
            daemon=True,
        )
        t.start()

        n_seg = max(1, int(total_duration / 25))
        est_music = n_seg * 25
        est_vocal = (len([l for l in lyrics.split('\n') if l.strip()]) * 180) if with_vocal else 0
        est_total = est_music + est_vocal

        return Response({
            'job_id': job_id,
            'estimated_seconds': est_total,
            'with_vocal': with_vocal,
            'total_duration': total_duration,
        })


class FullSongStatusView(APIView):
    """
    Poll trạng thái job tạo nhạc.
    GET /ai/generate/full/<job_id>/status/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, job_id):
        with _JOBS_LOCK:
            job = _JOBS.get(job_id)

        if not job:
            return Response({'error': 'Không tìm thấy job'}, status=404)

        # Tính elapsed time
        elapsed = int(_time.time() - job.get('started', _time.time()))

        return Response({
            'job_id':          job_id,
            'status':          job['status'],
            'pct':             job.get('pct', 0),
            'message':         job.get('message', ''),
            'elapsed':         elapsed,
            'error':           job.get('detail', '') if job['status'] == 'error' else None,
            'vocal_type':      job.get('vocal_type'),
            'vocal_generated': job.get('vocal_generated'),
            'fallback_reason': job.get('fallback_reason'),
        })


class FullSongDownloadView(APIView):
    """
    Tải file WAV khi job hoàn thành.
    GET /ai/generate/full/<job_id>/download/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, job_id):
        with _JOBS_LOCK:
            job = _JOBS.get(job_id)

        if not job:
            return Response({'error': 'Job không tồn tại'}, status=404)
        if job['status'] != 'done':
            return Response({'error': f'Job chưa hoàn thành: {job["status"]}'}, status=400)

        audio = job.get('audio')
        if not audio and job.get('audio_path') and os.path.isfile(job['audio_path']):
            try:
                with open(job['audio_path'], 'rb') as f:
                    audio = f.read()
            except Exception as e:
                logger.error(f"Error reading job audio file: {e}")

        if not audio:
            return Response({'error': 'Không có dữ liệu audio cho job này'}, status=404)

        genre = job.get('genre', 'music')
        mood  = job.get('mood', 'ai')
        fmt   = str(job.get('format', 'wav')).lower()

        # Tự động nhận diện định dạng chuẩn của byte stream
        if isinstance(audio, (bytes, bytearray)):
            if audio[:3] == b'ID3' or (len(audio) > 1 and audio[0] == 0xFF and (audio[1] & 0xE0) == 0xE0):
                fmt = 'mp3'
            elif audio[:4] == b'RIFF':
                fmt = 'wav'

        content_type = 'audio/mpeg' if fmt == 'mp3' else 'audio/wav'
        ext = f'.{fmt}'

        resp = HttpResponse(audio, content_type=content_type)
        resp['Content-Disposition'] = safe_content_disposition(f"full_song_{genre}_{mood}{ext}", disposition="inline")
        resp['X-Prompt']   = safe_header_val(job.get('prompt', '')[:200])
        resp['X-Duration'] = str(job.get('duration', 0))
        resp['X-Format']   = fmt
        resp['Access-Control-Expose-Headers'] = 'X-Prompt, X-Duration, X-Format, Content-Disposition'

        # Giải phóng audio bytes khỏi RAM nếu đã được lưu đệm an toàn trên disk
        if job.get('audio_path'):
            with _JOBS_LOCK:
                if job_id in _JOBS:
                    _JOBS[job_id]['audio'] = None

        return resp


class FullSongOptionsView(APIView):
    """Options cho full song generator."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .music_generator import GENRE_PROMPTS, MOOD_PROMPTS, TEMPO_PROMPTS, INSTRUMENT_PROMPTS
        vocal_profiles = [
            {'id': 'female_vi', 'name': 'Nữ V-Pop trong trẻo, truyền cảm'},
            {'id': 'male_vi', 'name': 'Nam V-Pop ấm áp, nội lực'},
            {'id': 'female_soft', 'name': 'Nữ Ballad sâu lắng, nhẹ nhàng'},
            {'id': 'male_deep', 'name': 'Nam Ballad trầm ấm'},
            {'id': 'vocal_duet', 'name': 'Song ca Nam & Nữ hòa quyện'},
            {'id': 'instrumental', 'name': 'Nhạc không lời (Instrumental)'},
        ]
        return Response({
            'genres':      list(GENRE_PROMPTS.keys()),
            'moods':       list(MOOD_PROMPTS.keys()),
            'tempos':      list(TEMPO_PROMPTS.keys()),
            'instruments': list(INSTRUMENT_PROMPTS.keys()),
            'voices':      [p['id'] for p in vocal_profiles],
            'voice_profiles': vocal_profiles,
            'models': [
                {'id': 'facebook/musicgen-small',  'name': 'Small (Nhanh)', 'vram': '2GB'},
                {'id': 'facebook/musicgen-medium', 'name': 'Medium (Tốt hơn)', 'vram': '4GB'},
            ],
            'duration_options': [
                {'seconds': 60,  'label': '1 phút'},
                {'seconds': 90,  'label': '1.5 phút'},
                {'seconds': 120, 'label': '2 phút'},
                {'seconds': 150, 'label': '2.5 phút'},
                {'seconds': 180, 'label': '3 phút'},
                {'seconds': 240, 'label': '4 phút'},
                {'seconds': 300, 'label': '5 phút'},
            ],
        })


# ─── Smart Lyrics Generator View ──────────────────────────────────────────────

class SmartLyricsGenerateView(APIView):
    """
    Tự động sinh lời bài hát chuẩn Suno / ACE-Step [Verse], [Chorus], [Bridge], [Outro]
    và gợi ý tiêu đề theo chủ đề/thể loại/tâm trạng (hỗ trợ tiếng Việt và đa ngôn ngữ).
    POST /ai/lyrics/generate/
    Body: { topic, genre, mood, vocal_gender, language }
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        topic = request.data.get("topic", "").strip()
        genre = request.data.get("genre", "vpop").strip()
        mood = request.data.get("mood", "happy").strip()
        vocal_gender = request.data.get("vocal_gender", "female").strip()
        language = request.data.get("language", "auto").strip()

        if not topic:
            return Response({"error": "Vui lòng nhập chủ đề hoặc câu chuyện cho bài hát."}, status=400)

        t0 = _time.time()
        try:
            from .prompt_analyzer import PromptAnalyzerService
            from .lyric_engine import generate_multilingual_lyrics
            from .smart_lyrics import generate_structured_lyrics

            config = PromptAnalyzerService.analyze(
                prompt=topic,
                user_language=language,
                user_vocal=vocal_gender,
            )

            target_lang = language.lower() if (language and language != "auto") else config.get("language", "vi")

            if target_lang == "vi":
                result = generate_structured_lyrics(
                    topic=topic,
                    genre=genre if genre not in ("", "auto") else config.get("genre", "vpop"),
                    mood=mood if mood not in ("", "happy") else config.get("mood", "happy"),
                    vocal_gender=vocal_gender,
                )
            else:
                lyric_data = generate_multilingual_lyrics(
                    language=target_lang,
                    theme=config.get("theme", "love"),
                    genre=config.get("genre", "pop"),
                    vocal_gender=config.get("vocal_gender", vocal_gender),
                    user_prompt=topic,
                )
                result = {
                    "title": lyric_data["title"],
                    "lyrics": lyric_data["lyrics"],
                    "style_tags": lyric_data["style_tags"],
                    "theme": lyric_data["theme"],
                    "language": target_lang,
                }

            elapsed = round(_time.time() - t0, 3)
            logger.info(
                f"[SmartLyricsGenerateView] Sinh lời thành công: '{result.get('title')}' "
                f"({result.get('theme')}, {detected_lang}) trong {elapsed}s"
            )
            return Response(result)

        except Exception as e:
            elapsed = round(_time.time() - t0, 3)
            logger.error(f"[SmartLyricsGenerateView] Lỗi sinh lời bài hát ({elapsed}s): {e}")
            return Response({"error": "Dịch vụ AI sinh lời bài hát tạm thời gián đoạn. Vui lòng thử lại sau."}, status=500)



# ─── ACE-Step Generator Views ─────────────────────────────────────────────────

class AceStepGenerateView(APIView):
    """
    Tạo nhạc có giọng hát bằng ACE-Step (HF Space, miễn phí).
    POST /ai/acestep/generate/
    Body: { prompt, lyrics, duration, genre, mood, instruments, guidance_scale, infer_steps, seed, vocal_gender }
    Returns: audio/mpeg (MP3)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import traceback

        prompt       = request.data.get("prompt", "").strip()
        lyrics       = request.data.get("lyrics", "").strip()
        duration     = int(request.data.get("duration", 180))  # mặc định 180s (3 phút)
        genre        = request.data.get("genre", "pop")
        mood         = request.data.get("mood", "happy")
        instruments  = request.data.get("instruments", "full")
        custom_prompt= request.data.get("custom_prompt", "").strip()
        guidance     = float(request.data.get("guidance_scale", 8.5))
        infer_steps  = int(request.data.get("infer_steps", 60))
        seed         = str(request.data.get("seed", "")).strip()
        vocal_gender = str(request.data.get("vocal_gender", "female")).strip()

        # Validate
        duration    = max(15, min(duration, 240))
        guidance    = max(5.0, min(guidance, 10.5))
        infer_steps = max(50, min(infer_steps, 80))

        try:
            from .acestep_generator import generate_with_acestep
            result = generate_with_acestep(
                prompt=prompt,
                lyrics=lyrics,
                duration=duration,
                genre=genre,
                mood=mood,
                instruments=instruments,
                custom_prompt=custom_prompt,
                guidance_scale=guidance,
                infer_steps=infer_steps,
                seed=seed,
                vocal_gender=vocal_gender,
            )

            audio_bytes = result["audio_bytes"]
            from django.conf import settings
            import os
            import base64

            audio_url = ""
            try:
                gen_dir = os.path.join(settings.MEDIA_ROOT, 'generated')
                os.makedirs(gen_dir, exist_ok=True)
                actual_seed = str(result.get("seed", seed or uuid.uuid4().hex[:8]))
                file_name = f"acestep_seed_{actual_seed}_{uuid.uuid4().hex[:6]}.mp3"
                file_path = os.path.join(gen_dir, file_name)
                with open(file_path, "wb") as f:
                    f.write(audio_bytes)
                audio_url = f"{settings.MEDIA_URL}generated/{file_name}"
            except Exception as save_err:
                logger.warning(f"Could not persist ACE-Step audio: {save_err}")

            resp = HttpResponse(audio_bytes, content_type="audio/mpeg")
            resp["Content-Disposition"] = safe_content_disposition(f"acestep_{genre}_{mood}.mp3", disposition="inline")
            resp["X-Prompt"]   = safe_header_val(result["prompt"][:200])
            resp["X-Duration"] = str(result["duration"])
            resp["X-Elapsed"]  = str(result["elapsed"])
            resp["X-Seed"]     = str(result.get("seed", ""))
            resp["X-Model"]    = "ACE-Step"
            if result.get("lyrics"):
                try:
                    resp["X-Lyrics-B64"] = base64.b64encode(result["lyrics"].encode("utf-8")).decode("ascii")
                except Exception:
                    pass
            if audio_url:
                resp["X-Audio-Url"] = safe_header_val(audio_url)
            resp["Access-Control-Expose-Headers"] = "X-Prompt, X-Duration, X-Elapsed, X-Seed, X-Model, X-Audio-Url, X-Lyrics-B64, Content-Disposition"
            return resp

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"ACE-Step error: {e}")
            err_msg = str(e)
            if "ZeroGPU quota" in err_msg or "zerogpu" in err_msg.lower():
                user_msg = "Hạn ngạch miễn phí Hugging Face ZeroGPU đang tạm hết lượt trong vài phút tới (do tạo nhiều bản liên tiếp). Bạn hãy chờ 3-5 phút hoặc chọn Engine MusicGen GPU nhé!"
            elif "timed out" in err_msg.lower() or "read operation" in err_msg.lower():
                user_msg = "Kết nối đến server AI bị quá hạn mạng. Vui lòng bấm Tạo lại."
            else:
                user_msg = f"Lỗi tạo nhạc: {err_msg}"

            return Response({
                "error":  user_msg,
                "detail": tb[-600:],
            }, status=500)
class AceStepStatusView(APIView):
    """Kiểm tra trạng thái kết nối ACE-Step."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .acestep_generator import _client
        return Response({
            "connected": _client is not None,
            "model":     "ACE-Step",
            "space":     "ACE-Step/ACE-Step",
            "free":      True,
            "has_vocals": True,
            "max_duration": 240,
        })


class AceStepRecoverView(APIView):
    """
    Tìm file audio đã tạo trước đó dựa vào seed.
    GET /api/ai/acestep/recover/?seed=3575
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        seed = request.query_params.get("seed", "").strip()
        if not seed:
            return Response({"found": False, "error": "Seed required"}, status=400)

        from django.conf import settings
        import os
        import glob

        generated_dir = os.path.join(settings.MEDIA_ROOT, "generated")
        if not os.path.exists(generated_dir):
            return Response({"found": False}, status=404)

        # Tìm kiếm bằng toàn bộ seed trước, sau đó thử 4 số cuối
        matches = glob.glob(os.path.join(generated_dir, f"*{seed}*.*"))
        if not matches and len(seed) >= 4:
            seed_clean = seed[-4:]
            matches = glob.glob(os.path.join(generated_dir, f"*{seed_clean}*.*"))

        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            matched_file = os.path.basename(matches[0])
            audio_url = f"{settings.MEDIA_URL}generated/{matched_file}"
            return Response({"found": True, "audio_url": audio_url, "filename": matched_file})

        return Response({"found": False}, status=404)


# ─── Phase 1: Prompt Analyzer View ────────────────────────────────────────────

class AnalyzePromptView(APIView):
    """
    Phân tích prompt ngắn thành SongConfiguration chi tiết.
    POST /api/ai/analyze/
    Body: { prompt, language?, vocal? }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        prompt       = request.data.get("prompt", "").strip()
        language     = request.data.get("language", "auto").strip()
        vocal        = request.data.get("vocal", "auto").strip()
        instrumental = bool(request.data.get("instrumental", False))

        if not prompt:
            return Response({"error": "Vui lòng nhập mô tả bài hát."}, status=400)

        try:
            from .prompt_analyzer import PromptAnalyzerService
            config = PromptAnalyzerService.analyze(
                prompt=prompt,
                user_language=language,
                user_vocal=vocal,
                is_instrumental=instrumental,
            )
            return Response(config)
        except Exception as e:
            logger.error(f"AnalyzePrompt error: {e}")
            return Response({"error": str(e)}, status=500)


# ─── Phase 3: Smart Generate View (Unified Endpoint) ─────────────────────────

class SmartGenerateView(APIView):
    """
    Pipeline hoàn chỉnh: Prompt → Analyze → Lyrics → ACE-Step → MP3
    POST /api/ai/generate/smart/
    Body: {
        prompt,           # bắt buộc: mô tả ngắn của user
        language?,        # 'auto'|'vi'|'ko'|'ja'|'zh'|'en'
        vocal?,           # 'auto'|'female'|'male'|'duet'|'instrumental'
        duration?,        # giây, mặc định 180
        guidance_scale?,  # mặc định 14.0
        infer_steps?,     # mặc định 60
        seed?,            # tuỳ chọn
        custom_lyrics?,   # nếu user muốn tự cung cấp lời
        instrumental?,    # bool
    }
    Returns: audio/mpeg (MP3) + X-* headers với metadata đầy đủ
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import traceback
        import base64

        prompt        = request.data.get("prompt", "").strip()
        language      = request.data.get("language", "auto").strip()
        vocal         = request.data.get("vocal", "auto").strip()
        duration      = int(request.data.get("duration", 0))     # 0 = auto
        guidance      = request.data.get("guidance_scale", None)  # None = use preset
        infer_steps   = request.data.get("infer_steps", None)     # None = use preset
        seed          = str(request.data.get("seed", "")).strip()
        custom_lyrics = request.data.get("custom_lyrics", "").strip()
        instrumental  = bool(request.data.get("instrumental", False))
        quality       = request.data.get("quality", "balanced").strip().lower()

        if not prompt:
            return Response({"error": "Vui lòng nhập mô tả bài hát."}, status=400)

        if quality not in ("fast", "balanced", "high"):
            quality = "balanced"

        # duration validation — 0 means auto-detect in generator
        if duration > 0:
            duration = max(15, min(duration, 240))
        if guidance is not None:
            guidance = float(guidance)
        if infer_steps is not None:
            infer_steps = int(infer_steps)

        try:
            # ── STEP 1: Phân tích Prompt ──────────────────────────────────────
            from .prompt_analyzer import PromptAnalyzerService
            config = PromptAnalyzerService.analyze(
                prompt=prompt,
                user_language=language,
                user_vocal=vocal,
                is_instrumental=instrumental,
            )
            logger.info(
                f"[SmartGen] ① PARSED CONFIG:\n"
                f"   Lang={config['language']} Genre={config['genre']} "
                f"Mood={config['mood']} BPM={config['bpm']} Vocal={config['vocal_gender']}\n"
                f"   Theme={config['theme']} Key={config['key']}\n"
                f"   Model prompt preview: {config['model_prompt'][:120]}"
            )

            # ── STEP 1b: Expanded Caption qua CaptionBuilder ─────────────────
            from .caption_builder import build_rich_caption
            expanded_caption = build_rich_caption(config, quality=quality)
            logger.info(f"[SmartGen] ② EXPANDED CAPTION:\n   {expanded_caption[:200]}")

            # ── STEP 2: Sinh Lời Bài Hát ─────────────────────────────────────
            if custom_lyrics:
                lyrics = custom_lyrics
                song_title = prompt[:50]
                logger.info(f"[SmartGen] ③ LYRICS: User-provided ({len(lyrics)} chars)")
            elif config["vocal_gender"] == "instrumental":
                lyrics = ""
                song_title = prompt[:50]
                logger.info("[SmartGen] ③ LYRICS: Instrumental (no lyrics)")
            else:
                from .lyric_engine import generate_multilingual_lyrics
                structure_labels = [s["label"] for s in config.get("structure", [])]
                lyric_result = generate_multilingual_lyrics(
                    language=config["language"],
                    theme=config["theme"],
                    genre=config["genre"],
                    vocal_gender=config["vocal_gender"],
                    user_prompt=prompt,
                    structure_labels=structure_labels if structure_labels else None,
                )
                lyrics = lyric_result["lyrics"]
                song_title = lyric_result["title"]
                logger.info(
                    f"[SmartGen] ③ LYRICS GENERATED:\n"
                    f"   Title: {song_title}\n"
                    f"   Lang: {lyric_result['language']} | Theme: {lyric_result['theme']}\n"
                    f"   Preview: {lyrics[:120]}"
                )

            # ── STEP 3: Tạo Nhạc với ACE-Step ────────────────────────────────
            logger.info(
                f"[SmartGen] ④ ACE-STEP PARAMS:\n"
                f"   Quality={quality} | Duration={duration or 'auto'} | Seed={seed or 'random'}"
            )
            from .acestep_generator import generate_with_acestep
            result = generate_with_acestep(
                prompt=prompt,
                lyrics=lyrics,
                duration=duration,       # 0 = auto in generator
                genre=config["genre"],
                mood=config["mood"],
                instruments="full",
                custom_prompt=expanded_caption,   # ← rich caption
                guidance_scale=guidance,           # None = use preset
                infer_steps=infer_steps,           # None = use preset
                seed=seed,
                vocal_gender=config["vocal_gender"],
                quality=quality,
                song_config=config,               # ← truyền config để build rich caption
            )

            audio_bytes = result["audio_bytes"]
            if isinstance(audio_bytes, (tuple, list)):
                audio_bytes = audio_bytes[0]

            # ── STEP 4: Audio Validation ─────────────────────────────────────
            audio_size = len(audio_bytes) if audio_bytes else 0
            if audio_size < 1000:
                logger.error(f"[SmartGen] ⑤ AUDIO VALIDATION FAILED: only {audio_size} bytes")
                raise ValueError("Audio file quá nhỏ — ACE-Step có thể bị lỗi generation.")
            logger.info(f"[SmartGen] ⑤ AUDIO VALIDATION OK: {audio_size:,} bytes | elapsed={result.get('elapsed', 0)}s")

            # ── STEP 5: Lưu file MP3 ─────────────────────────────────────────
            from django.conf import settings
            import os

            audio_url = ""
            try:
                gen_dir = os.path.join(settings.MEDIA_ROOT, "generated")
                os.makedirs(gen_dir, exist_ok=True)
                actual_seed = str(result.get("seed", seed or uuid.uuid4().hex[:8]))
                file_name = (
                    f"smart_{config['language']}_{config['genre']}"
                    f"_{quality}_{actual_seed}_{uuid.uuid4().hex[:6]}.mp3"
                )
                file_path = os.path.join(gen_dir, file_name)
                with open(file_path, "wb") as f:
                    f.write(audio_bytes)
                audio_url = f"{settings.MEDIA_URL}generated/{file_name}"
                logger.info(f"[SmartGen] ⑥ AUDIO SAVED: {file_name}")
            except Exception as save_err:
                logger.warning(f"[SmartGen] Could not save audio: {save_err}")

            # ── STEP 6: Trả về Response ───────────────────────────────────────
            resp = HttpResponse(audio_bytes, content_type="audio/mpeg")
            resp["Content-Disposition"] = safe_content_disposition(f"{song_title[:40]}.mp3", disposition="inline")
            resp["X-Song-Title"]   = safe_header_val(song_title[:200])
            resp["X-Language"]     = safe_header_val(config.get("language", ""))
            resp["X-Genre"]        = safe_header_val(config.get("genre_name", ""))
            resp["X-Mood"]         = safe_header_val(config.get("mood_name", ""))
            resp["X-BPM"]          = str(config.get("bpm", 120))
            resp["X-Key"]          = safe_header_val(config.get("key", "C"))
            resp["X-Vocal"]        = safe_header_val(config.get("vocal_gender", "auto"))
            resp["X-Theme"]        = safe_header_val(config.get("theme", ""))
            resp["X-Duration"]     = str(result["duration"])
            resp["X-Elapsed"]      = str(result["elapsed"])
            resp["X-Seed"]         = str(result.get("seed", ""))
            resp["X-Model"]        = "ACE-Step-Smart-v2"
            resp["X-Quality"]      = safe_header_val(quality)
            resp["X-Model-Prompt"] = safe_header_val(expanded_caption[:200])
            if audio_url:
                resp["X-Audio-Url"] = safe_header_val(audio_url)
            if lyrics:
                try:
                    resp["X-Lyrics-B64"] = base64.b64encode(
                        lyrics.encode("utf-8")
                    ).decode("ascii")
                except Exception:
                    pass
            resp["Access-Control-Expose-Headers"] = (
                "X-Song-Title, X-Language, X-Genre, X-Mood, X-BPM, X-Key, "
                "X-Vocal, X-Theme, X-Duration, X-Elapsed, X-Seed, X-Model, "
                "X-Quality, X-Model-Prompt, X-Audio-Url, X-Lyrics-B64, Content-Disposition"
            )
            return resp

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"[SmartGen] Error: {e}")
            err_msg = str(e)
            if "ZeroGPU quota" in err_msg or "zerogpu" in err_msg.lower():
                user_msg = "Hạn ngạch miễn phí Hugging Face ZeroGPU đang tạm hết. Vui lòng chờ 3-5 phút rồi thử lại."
            elif "timed out" in err_msg.lower() or "read operation" in err_msg.lower():
                user_msg = "Kết nối đến server AI bị quá hạn. Vui lòng bấm Tạo lại."
            else:
                user_msg = f"Lỗi tạo nhạc: {err_msg}"
            return Response({"error": user_msg, "detail": tb[-600:]}, status=500)


class AnalyzeImageView(APIView):
    """
    Sonavia Visual Synesthesia Engine:
    POST /api/ai/analyze-image/
    Nhận hình ảnh upload (file, base64 hoặc URL) và phân tích cảm xúc, màu sắc, bối cảnh
    để tạo prompt âm nhạc, thể loại, tâm trạng, nhịp điệu và lời bài hát tương ứng.
    """
    permission_classes = [permissions.AllowAny]

    def get_parsers(self):
        from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
        return [MultiPartParser(), FormParser(), JSONParser()]

    def post(self, request):
        import os
        import base64
        import io
        import json
        from django.conf import settings
        from .image_analyzer import ImageToMusicAnalyzer

        image_file = None
        image_base64 = ""
        image_url = ""
        preset_scene = ""
        language = "auto"

        # 1. Thử lấy file từ multipart
        try:
            image_file = request.FILES.get('image')
        except Exception:
            pass

        # 2. Thử lấy parameters từ request.data
        try:
            image_base64 = (request.data.get('image_base64') or '').strip()
            image_url = (request.data.get('image_url') or '').strip()
            preset_scene = (request.data.get('preset_scene') or '').strip()
            language = (request.data.get('language') or 'auto').strip()
        except Exception:
            pass

        # 3. Fallback đọc từ raw request.body nếu multipart gặp sự cố ở tầng parser
        if not image_file and not image_base64 and not image_url and not preset_scene and getattr(request, 'body', None):
            try:
                body_data = json.loads(request.body.decode('utf-8'))
                image_base64 = (body_data.get('image_base64') or '').strip()
                image_url = (body_data.get('image_url') or '').strip()
                preset_scene = (body_data.get('preset_scene') or '').strip()
                language = (body_data.get('language') or language).strip()
            except Exception:
                pass

        save_dir = os.path.join(str(settings.MEDIA_ROOT), 'visual_prompts')
        os.makedirs(save_dir, exist_ok=True)

        try:
            if image_file:
                result = ImageToMusicAnalyzer.analyze_image(image_file, save_dir=save_dir, language=language)
            elif image_base64:
                if ',' in image_base64:
                    image_base64 = image_base64.split(',', 1)[1]
                img_data = base64.b64decode(image_base64)
                img_io = io.BytesIO(img_data)
                result = ImageToMusicAnalyzer.analyze_image(img_io, save_dir=save_dir, language=language)
            elif image_url:
                clean_url = image_url.replace(settings.MEDIA_URL, '').lstrip('/\\')
                local_path = os.path.join(str(settings.MEDIA_ROOT), clean_url)
                if os.path.exists(local_path):
                    result = ImageToMusicAnalyzer.analyze_image(local_path, save_dir=save_dir, language=language)
                else:
                    return Response({'error': 'Không tìm thấy file hình ảnh.'}, status=400)
            elif preset_scene:
                from PIL import Image as PilImage, ImageDraw
                img = PilImage.new('RGB', (800, 800))
                draw = ImageDraw.Draw(img)
                palette_map = {
                    'golden_sunset_romantic': [(255, 94, 58), (255, 149, 0), (255, 204, 0)],
                    'neon_cyber_night': [(15, 12, 41), (147, 51, 234), (6, 182, 212)],
                    'rainy_melancholic_room': [(40, 50, 65), (90, 105, 120), (160, 175, 190)],
                    'ocean_blue_sky_freedom': [(14, 165, 233), (56, 189, 248), (224, 242, 254)],
                    'nature_forest_peaceful': [(20, 83, 45), (34, 197, 94), (187, 247, 208)],
                }
                colors = palette_map.get(preset_scene, [(99, 102, 241), (34, 211, 238)])
                for y in range(800):
                    ratio = y / 799.0
                    if len(colors) >= 3:
                        if ratio < 0.5:
                            sub_r = ratio * 2
                            c1, c2 = colors[0], colors[1]
                        else:
                            sub_r = (ratio - 0.5) * 2
                            c1, c2 = colors[1], colors[2]
                    else:
                        sub_r = ratio
                        c1, c2 = colors[0], colors[1]
                    r = int(c1[0] + (c2[0] - c1[0]) * sub_r)
                    g = int(c1[1] + (c2[1] - c1[1]) * sub_r)
                    b = int(c1[2] + (c2[2] - c1[2]) * sub_r)
                    draw.line([(0, y), (800, y)], fill=(r, g, b))
                result = ImageToMusicAnalyzer.analyze_image(img, save_dir=save_dir, language=language)
            else:
                return Response({'error': 'Vui lòng cung cấp hình ảnh (file, base64 hoặc URL).'}, status=400)

            return Response(result, status=200)

        except Exception as e:
            logger.error(f"[AnalyzeImageView] Lỗi phân tích ảnh: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': f'Không thể phân tích hình ảnh: {str(e)}'
            }, status=500)


# ─── Enhance Prompt View (Magic Prompt Enhancer) ──────────────────────────────

class EnhancePromptView(APIView):
    """
    API tối ưu hóa và làm giàu prompt bằng Gemini.
    POST /api/ai/prompt/enhance/
    Body: { "prompt": "nhạc buồn trời mưa", "language": "vi" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        prompt = request.data.get("prompt", "").strip()
        language = request.data.get("language", "auto").strip()

        if not prompt:
            return Response({"error": "Vui lòng nhập ý tưởng bài hát để tối ưu hóa."}, status=400)

        try:
            from .llm_service import enhance_prompt_with_llm
            result = enhance_prompt_with_llm(user_prompt=prompt, language=language)
            return Response(result, status=200)
        except Exception as e:
            logger.error(f"[EnhancePromptView] Error: {e}", exc_info=True)
            return Response({"error": str(e)}, status=500)


# ─── Vietnamese Emotion Classifier View ────────────────────────────────────────

class EmotionClassifyView(APIView):
    """
    Phân loại cảm xúc tiếng Việt chuẩn 6 nhãn (Happy, Sad, Nostalgic, Calm, Energetic, Angry)
    POST /api/ai/emotion/classify/
    Body: { "text": "Hôm nay tôi rất buồn..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .emotion_classifier import classify_vietnamese_emotion
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "Vui lòng nhập văn bản hoặc lời ca cần phân tích cảm xúc."}, status=400)
        try:
            res = classify_vietnamese_emotion(text)
            return Response(res, status=200)
        except Exception as e:
            logger.error(f"[EmotionClassifyView] Lỗi phân loại cảm xúc: {e}", exc_info=True)
            return Response({"error": f"Lỗi phân loại cảm xúc: {str(e)}"}, status=500)

        except Exception as e:
            logger.error(f"[EnhancePromptView] Lỗi tối ưu prompt: {e}")
            return Response({
                "success": False,
                "error": f"Không thể tối ưu hóa prompt: {str(e)}"
            }, status=500)


