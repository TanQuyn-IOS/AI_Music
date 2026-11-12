import logging
import os
import shutil
import uuid

logger = logging.getLogger(__name__)
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import F, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Song, Playlist, PlaylistSong, ListenHistory, GENRE_CHOICES, MOOD_CHOICES
from .serializers import SongSerializer, PlaylistSerializer, ListenHistorySerializer


class SongListCreateView(generics.ListCreateAPIView):
    serializer_class = SongSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['genre', 'mood', 'artist', 'artist__username']
    search_fields = ['title', 'artist__username', 'tags']
    ordering_fields = ['created_at', 'play_count', 'title']

    def get_queryset(self):
        return Song.objects.filter(is_published=True).select_related('artist')

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}


class SongDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Song.objects.all()
    serializer_class = SongSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_update(self, serializer):
        if serializer.instance.artist != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied('Bạn không có quyền chỉnh sửa bài hát này.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.artist != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied('Bạn không có quyền xóa bài hát này.')
        instance.delete()

    def retrieve(self, request, *args, **kwargs):
        song = self.get_object()
        # Chỉ tăng play_count khi có query ?play=1 (frontend gửi khi thực sự phát nhạc)
        if request.query_params.get('play') == '1':
            Song.objects.filter(pk=song.pk).update(play_count=F('play_count') + 1)
            song.refresh_from_db(fields=['play_count'])
        serializer = self.get_serializer(song)
        return Response(serializer.data)


class PlaylistListCreateView(generics.ListCreateAPIView):
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        user = self.request.query_params.get('user')
        if user:
            return Playlist.objects.filter(owner__username=user)
        if self.request.user.is_authenticated:
            from django.db.models import Q
            return Playlist.objects.filter(
                Q(is_public=True) | Q(owner=self.request.user)
            ).distinct()
        return Playlist.objects.filter(is_public=True)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}


class PlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_update(self, serializer):
        if serializer.instance.owner != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied('Bạn không có quyền chỉnh sửa danh sách phát này.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied('Bạn không có quyền xóa danh sách phát này.')
        instance.delete()


class PlaylistAddSongView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
        song_id = request.data.get('song_id')
        song = get_object_or_404(Song, pk=song_id)
        ps, created = PlaylistSong.objects.get_or_create(playlist=playlist, song=song)
        if not created:
            ps.delete()
            return Response({'added': False, 'message': 'Đã xóa bài hát khỏi playlist'})
        return Response({'added': True, 'message': 'Đã thêm bài hát vào playlist'})


class ListenHistoryView(generics.ListCreateAPIView):
    serializer_class = ListenHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ListenHistory.objects.filter(user=self.request.user).select_related('song')

    def get_serializer_context(self):
        return {'request': self.request}


class TrendingSongsView(generics.ListAPIView):
    serializer_class = SongSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Song.objects.filter(is_published=True).select_related('artist').order_by('-play_count')[:20]

    def get_serializer_context(self):
        return {'request': self.request}


class SemanticSongSearchView(APIView):
    """
    Tìm kiếm ngữ nghĩa bài hát sử dụng Gemini Neural Embedding 3072 chiều.
    GET /api/music/songs/semantic-search/?q=khúc hát mùa đông&limit=15&min_score=0.1
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'results': [], 'query': '', 'total': 0, 'type': 'neural_semantic_3072'})

        limit = min(int(request.query_params.get('limit', 15)), 50)
        min_score = float(request.query_params.get('min_score', 0.05))

        from apps.ai_engine.llm_service import get_neural_embedding
        import numpy as np

        query_vec = get_neural_embedding(query)
        if query_vec is None:
            songs = Song.objects.filter(is_published=True).filter(
                Q(title__icontains=query) | Q(tags__icontains=query) | Q(lyrics__icontains=query)
            ).select_related('artist')[:limit]
            serializer = SongSerializer(songs, many=True, context={'request': request})
            return Response({'results': serializer.data, 'query': query, 'total': len(serializer.data), 'type': 'keyword_fallback'})

        published_songs = list(Song.objects.filter(is_published=True).select_related('artist'))
        scored_songs = []
        for song in published_songs:
            text_rep = f"{song.title} {song.genre} {song.mood} {song.tags} {song.lyrics[:200] if song.lyrics else ''}"
            song_vec = get_neural_embedding(text_rep)
            if song_vec is not None and song_vec.shape == query_vec.shape:
                score = float(np.dot(query_vec, song_vec))
                if score >= min_score:
                    scored_songs.append((score, song))

        scored_songs.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_songs[:limit]

        data = []
        for score, song in top_matches:
            item = SongSerializer(song, context={'request': request}).data
            item['similarity_score'] = round(score, 4)
            data.append(item)

        return Response({
            'results': data,
            'query': query,
            'total': len(data),
            'type': 'neural_semantic_3072'
        })



class IncrementPlayCountView(APIView):
    """Tăng lượt nghe khi người dùng thực sự phát nhạc"""
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        Song.objects.filter(pk=pk, is_published=True).update(
            play_count=F('play_count') + 1
        )
        # Lưu lịch sử nghe nếu đã đăng nhập
        if request.user.is_authenticated:
            ListenHistory.objects.create(user=request.user, song_id=pk)
        return Response({'ok': True})


class SaveAiSongView(APIView):
    """
    Lưu bài nhạc AI vào thư viện — nhận WAV file upload + metadata.
    POST /music/songs/save-ai/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        import os
        from django.core.files.base import ContentFile

        title       = request.data.get('title', '').strip() or 'AI Song'
        genre       = request.data.get('genre', 'other')
        mood        = request.data.get('mood', '')
        try:
            duration = int(float(request.data.get('duration') or 0))
        except (ValueError, TypeError):
            duration = 0
        lyrics      = request.data.get('lyrics', '')
        description = request.data.get('description', '')
        is_published = str(request.data.get('is_published', 'true')).lower() == 'true'
        audio_file = request.FILES.get('audio_file')
        audio_url  = request.data.get('audio_url', '').strip()

        if not audio_file and not audio_url:
            return Response({'error': 'Thiếu file audio hoặc đường dẫn âm thanh'}, status=400)

        # Giới hạn kích thước 50MB nếu upload file
        if audio_file and audio_file.size > 50 * 1024 * 1024:
            return Response({'error': 'File quá lớn (tối đa 50MB)'}, status=400)

        song = Song(
            title=title,
            artist=request.user,
            genre=genre if genre in dict(GENRE_CHOICES) else 'other',
            mood=mood if mood in dict(MOOD_CHOICES) else '',
            duration=duration,
            lyrics=lyrics,
            description=description or '🤖 Sonavia AI Studio Generated',
            is_published=is_published,
            audio_url=audio_url,
        )

        if audio_file:
            safe_title = "".join(c for c in title if c.isalnum() or c in ' _-').strip()
            safe_title = safe_title[:50] or 'ai_song'
            orig_ext = os.path.splitext(getattr(audio_file, 'name', ''))[1].lower()
            if orig_ext not in ['.mp3', '.wav', '.ogg', '.m4a']:
                orig_ext = '.mp3' if 'mpeg' in getattr(audio_file, 'content_type', '') else '.wav'
            filename = f"{safe_title.replace(' ', '_')}{orig_ext}"
            song.audio_file.save(filename, audio_file, save=False)

        cover_image_url = request.data.get('cover_image_url', '').strip()
        if cover_image_url and not song.cover_image:
            try:
                import shutil
                from django.conf import settings
                clean_cover = cover_image_url.replace(settings.MEDIA_URL, '').lstrip('/\\')
                full_cover = os.path.join(str(settings.MEDIA_ROOT), clean_cover)
                real_media_root = os.path.realpath(str(settings.MEDIA_ROOT))
                real_full_cover = os.path.realpath(full_cover)
                if real_full_cover.startswith(real_media_root + os.sep) and os.path.isfile(real_full_cover):
                    covers_dir = os.path.join(str(settings.MEDIA_ROOT), 'song_covers')
                    os.makedirs(covers_dir, exist_ok=True)
                    cover_name = f"cover_{uuid.uuid4().hex[:8]}_{os.path.basename(real_full_cover)}"
                    shutil.copy2(real_full_cover, os.path.join(covers_dir, cover_name))
                    song.cover_image = f"song_covers/{cover_name}"
            except Exception:
                pass

        song.save()

        from .serializers import SongSerializer
        return Response(
            SongSerializer(song, context={'request': request}).data,
            status=201
        )


class MusicGenerateUnifiedView(APIView):
    """
    Sonavia Studio Unified Music Generator
    POST /api/music/generate/
    Frontend chỉ cần gửi prompt và thông số chung. Không cần biết provider bên dưới.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import os
        import time
        import uuid
        import base64
        import logging
        import traceback
        from django.http import HttpResponse
        from django.conf import settings

        logger = logging.getLogger(__name__)

        try:
            from apps.ai_engine.orchestrator import sonavia_orchestrator

            prompt             = str(request.data.get("prompt", "") or "").strip()
            language           = str(request.data.get("language", "auto") or "auto").strip()
            vocal              = str(request.data.get("vocal", "auto") or "auto").strip()
            try:
                duration       = int(float(request.data.get("duration") or 180))
            except (ValueError, TypeError):
                duration       = 180
            seed               = str(request.data.get("seed", "") or "").strip()
            custom_lyrics      = str(request.data.get("custom_lyrics", "") or "").strip()
            instrumental       = bool(request.data.get("instrumental", False))
            try:
                guidance       = float(request.data.get("guidance_scale") or 14.5)
            except (ValueError, TypeError):
                guidance       = 14.5
            try:
                infer_steps    = int(float(request.data.get("infer_steps") or 60))
            except (ValueError, TypeError):
                infer_steps    = 60
            preferred_provider = request.data.get("preferred_provider")

            if not prompt:
                return Response({
                    "success": False,
                    "error": {
                        "code": "EMPTY_PROMPT",
                        "message": "Vui lòng nhập mô tả bài hát bạn muốn tạo.",
                        "stage": "validation"
                    }
                }, status=400)

            # Ràng buộc tham số
            duration    = max(15, min(duration, 240))
            guidance    = max(5.0, min(guidance, 18.0))
            infer_steps = max(50, min(infer_steps, 80))

            result = sonavia_orchestrator.generate_song(
                prompt=prompt,
                language=language,
                vocal=vocal,
                duration=duration,
                guidance_scale=guidance,
                infer_steps=infer_steps,
                seed=seed,
                custom_lyrics=custom_lyrics,
                instrumental=instrumental,
                preferred_provider=preferred_provider,
            )

            audio_bytes = result["audio_bytes"]
            if isinstance(audio_bytes, (tuple, list)):
                audio_bytes = audio_bytes[0]

            fmt = result.get("format", "mp3")
            ext = f".{fmt}" if fmt else ".mp3"
            content_type = "audio/wav" if fmt == "wav" else "audio/mpeg"

            config = result["config"]
            song_title = result["title"]
            lyrics = result["lyrics"]

            # Lưu file MP3/WAV vào thư mục generated
            gen_dir = os.path.join(settings.MEDIA_ROOT, "generated")
            os.makedirs(gen_dir, exist_ok=True)
            safe_seed = result["seed"]
            file_name = f"sonavia_{config['language']}_{config['genre']}_{safe_seed}_{uuid.uuid4().hex[:6]}{ext}"
            file_path = os.path.join(gen_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            audio_url = f"{settings.MEDIA_URL}generated/{file_name}"

            # ── Validation kiểm tra tính toàn vẹn của tệp âm thanh (Section F) ──
            if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:
                raise RuntimeError("Tệp âm thanh được tạo không hợp lệ hoặc rỗng.")

            # ── Lưu vào Database Song model (Section H) ──
            from apps.music.models import Song
            from apps.users.models import User

            author = request.user if request.user and request.user.is_authenticated else (
                User.objects.filter(is_staff=True).first() or User.objects.first()
            )
            if not author:
                author, _ = User.objects.get_or_create(
                    username='sonavia_ai',
                    defaults={
                        'first_name': 'Sonavia',
                        'last_name': 'AI Studio',
                        'is_artist': True,
                        'bio': 'Trợ lý âm nhạc AI của Sonavia Studio',
                    }
                )

            cover_image_url = request.data.get("cover_image_url", "").strip()
            db_song = None
            try:
                db_song = Song.objects.create(
                    title=song_title,
                    artist=author,
                    audio_url=audio_url,
                    genre=config["genre"] if config["genre"] in dict(GENRE_CHOICES) else 'other',
                    mood=config["mood"] if config["mood"] in dict(MOOD_CHOICES) else '',
                    duration=int(result["duration"]),
                    lyrics=lyrics or '',
                    description=f"AI Generated ({config['language'].upper()}) - Prompt: {prompt[:200]}",
                    is_published=True,
                )
                if cover_image_url:
                    try:
                        import shutil
                        clean_cover = cover_image_url.replace(settings.MEDIA_URL, '').lstrip('/\\')
                        full_cover = os.path.join(str(settings.MEDIA_ROOT), clean_cover)
                        real_media_root = os.path.realpath(str(settings.MEDIA_ROOT))
                        real_full_cover = os.path.realpath(full_cover)
                        if real_full_cover.startswith(real_media_root + os.sep) and os.path.isfile(real_full_cover):
                            covers_dir = os.path.join(str(settings.MEDIA_ROOT), 'song_covers')
                            os.makedirs(covers_dir, exist_ok=True)
                            cover_name = f"cover_{uuid.uuid4().hex[:8]}_{os.path.basename(real_full_cover)}"
                            shutil.copy2(real_full_cover, os.path.join(covers_dir, cover_name))
                            db_song.cover_image = f"song_covers/{cover_name}"
                            db_song.save(update_fields=['cover_image'])
                    except Exception as cv_err:
                        logger.warning(f"Failed to attach cover image: {cv_err}")

            except Exception as db_err:
                logger.warning(f"[MusicGenerateUnifiedView] Lỗi lưu Song vào database: {db_err}")

            song_id = db_song.id if db_song else int(safe_seed or time.time())
            if db_song and db_song.cover_image:
                resolved_cover_url = request.build_absolute_uri(db_song.cover_image.url)
            elif cover_image_url:
                resolved_cover_url = request.build_absolute_uri(cover_image_url) if cover_image_url.startswith('/') else cover_image_url
            else:
                resolved_cover_url = None

            full_audio_url = request.build_absolute_uri(audio_url) if audio_url.startswith('/') else audio_url

            # Response object chuẩn hóa theo Section C
            response_payload = {
                "success": True,
                "song": {
                    "id": song_id,
                    "title": song_title,
                    "audio_url": full_audio_url,
                    "cover_image_url": resolved_cover_url,
                    "lyrics": lyrics,
                    "language": config["language"],
                    "genre": config["genre_name"],
                    "mood": config["mood_name"],
                    "bpm": config["bpm"],
                    "key": config["key"],
                    "vocal": config["vocal_gender"],
                    "duration": result["duration"],
                    "seed": safe_seed,
                    "theme": config.get("theme", ""),
                    "format": fmt,
                    "task_type": result.get("task_type", "text_to_song"),
                    "vocal_type": result.get("vocal_type", "vocal" if config["vocal_gender"] != "instrumental" else "instrumental"),
                    "vocal_generated": result.get("vocal_generated", False),
                    "fallback_reason": result.get("fallback_reason"),
                    "provider": result.get("provider", "sonavia-engine"),
                    "phonetic_summary": result.get("phonetic_summary"),
                }
            }

            # Nếu client yêu cầu binary audio stream trực tiếp (thông qua query param ?format=audio)
            if request.query_params.get("format") == "audio":
                from apps.ai_engine.header_utils import safe_header_val, safe_content_disposition
                resp = HttpResponse(audio_bytes, content_type=content_type)
                resp["Content-Disposition"] = safe_content_disposition(f"{song_title[:40]}{ext}", disposition="inline")
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
                resp["X-Seed"]         = str(safe_seed)
                resp["X-Audio-Url"]    = safe_header_val(audio_url)
                if lyrics:
                    try:
                        resp["X-Lyrics-B64"] = base64.b64encode(lyrics.encode("utf-8")).decode("ascii")
                    except Exception:
                        pass
                resp["Access-Control-Expose-Headers"] = (
                    "X-Song-Title, X-Language, X-Genre, X-Mood, X-BPM, X-Key, "
                    "X-Vocal, X-Theme, X-Duration, X-Elapsed, X-Seed, "
                    "X-Audio-Url, X-Lyrics-B64, Content-Disposition"
                )
                return resp

            # Mặc định trả về JSON HTTP 200 chuẩn
            return Response(response_payload, status=200)

        except Exception as e:
            logger.error(f"[MusicGenerateUnifiedView] Lỗi: {e}")
            raw_err = str(e).strip()
            first_line = raw_err.split("\n")[0].strip()
            error_code = "MUSIC_GENERATION_FAILED"
            stage = "music_generation"

            if "zerogpu" in raw_err.lower() or "quota" in raw_err.lower():
                user_msg = "Hạn ngạch server AI đang tạm bận. Vui lòng chờ 2-3 phút và bấm Tạo lại."
                error_code = "AI_QUOTA_EXCEEDED"
            elif "timed out" in raw_err.lower() or "timeout" in raw_err.lower():
                user_msg = "Kết nối quá hạn. Vui lòng thử lại sau giây lát."
                error_code = "CONNECTION_TIMED_OUT"
            elif "<!doctype" in raw_err.lower() or "html" in raw_err.lower() or not first_line:
                user_msg = "Máy chủ AI đang khởi động lại hoặc tạm bận. Vui lòng thử lại sau 1-2 phút."
                error_code = "SERVER_UNAVAILABLE"
            else:
                clean_line = first_line[:120].replace("Không thể kết nối đến ACE-Step Space:", "").strip()
                user_msg = clean_line or "Không thể tạo bản nhạc vào lúc này. Vui lòng thử lại."

            return Response({
                "success": False,
                "error": {
                    "code": error_code,
                    "message": user_msg,
                    "stage": stage
                }
            }, status=500)



class SongExtendView(APIView):
    """
    Mở rộng bài hát thêm 30s - 60s (Inpainting & Continuation).
    POST /api/music/songs/<int:pk>/extend/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        song = get_object_or_404(Song, pk=pk)
        duration = int(request.data.get('duration', 60))
        prompt = request.data.get('prompt', '').strip()
        additional_lyrics = request.data.get('additional_lyrics', '').strip()

        try:
            from .audio_extend import extend_song
            extended = extend_song(
                parent_song=song,
                user=request.user,
                duration_sec=duration,
                continuation_prompt=prompt,
                additional_lyrics=additional_lyrics
            )
            serializer = SongSerializer(extended, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"[SongExtendView] Error extending song {pk}: {e}")
            return Response({'error': f'Không thể mở rộng bài hát: {str(e)}'}, status=500)
