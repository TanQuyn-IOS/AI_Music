"""
Sonavia Studio — High-Performance Streaming Media Server
==========================================================
Hỗ trợ đầy đủ HTTP Range Request (RFC 7233) và CORS cho HTML5 Audio Player:
- HTTP 206 Partial Content khi có header Range
- Header Accept-Ranges: bytes
- Content-Range: bytes START-END/TOTAL
- Hỗ trợ audio scrubbing, seeking, resume playback
- Expose đầy đủ CORS headers cho frontend
"""

import os
import re
import mimetypes
import logging
from django.conf import settings
from django.http import HttpResponse, Http404

logger = logging.getLogger(__name__)


def serve_media_with_range(request, path: str):
    """
    Phục vụ media file tĩnh với hỗ trợ HTTP Range Request chuẩn RFC 7233
    cho thẻ <audio> và <video> trên trình duyệt.
    """
    # Xử lý nhanh CORS preflight request (OPTIONS)
    if request.method == 'OPTIONS':
        resp = HttpResponse(status=204)
        resp['Accept-Ranges'] = 'bytes'
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        origin = request.META.get('HTTP_ORIGIN', '')
        if origin and origin in allowed_origins:
            resp['Access-Control-Allow-Origin'] = origin
            resp['Access-Control-Allow-Credentials'] = 'true'
        else:
            resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Range, Content-Type, Authorization, Accept'
        resp['Access-Control-Expose-Headers'] = 'Content-Range, Content-Length, Accept-Ranges, Content-Disposition'
        return resp

    # Chuẩn hóa path tránh directory traversal
    clean_path = os.path.normpath(path).lstrip(r'/\.')
    full_path = os.path.join(str(settings.MEDIA_ROOT), clean_path)

    # Đảm bảo file nằm trong MEDIA_ROOT
    real_media_root = os.path.realpath(str(settings.MEDIA_ROOT))
    real_full_path = os.path.realpath(full_path)
    if not real_full_path.startswith(real_media_root + os.sep) and real_full_path != real_media_root:
        raise Http404("Invalid path")

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise Http404("Media file not found")

    file_size = os.path.getsize(full_path)
    ext = os.path.splitext(full_path)[1].lower()
    
    # Chuẩn hóa MIME type tuyệt đối cho HTML5 Audio Streaming
    if ext == '.mp3':
        content_type = 'audio/mpeg'
    elif ext == '.wav':
        content_type = 'audio/wav'
    elif ext in ['.ogg', '.oga']:
        content_type = 'audio/ogg'
    elif ext in ['.m4a', '.mp4']:
        content_type = 'audio/mp4'
    else:
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = 'application/octet-stream'

    if file_size == 0:
        response = HttpResponse(b'', status=200, content_type=content_type)
        response['Content-Length'] = '0'
        response['Accept-Ranges'] = 'bytes'
        return response

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

    if range_match:
        first_byte = int(range_match.group(1))
        last_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1

        # Kiểm tra tính hợp lệ của range
        if first_byte >= file_size or last_byte >= file_size or first_byte > last_byte:
            resp = HttpResponse(status=416)
            resp['Content-Range'] = f'bytes */{file_size}'
            return resp

        length = last_byte - first_byte + 1

        if request.method == 'HEAD':
            response = HttpResponse(b'', status=206, content_type=content_type)
        else:
            with open(full_path, 'rb') as f:
                f.seek(first_byte)
                data = f.read(length)
            response = HttpResponse(data, status=206, content_type=content_type)
        response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        response['Content-Length'] = str(length)
    else:
        # Request thông thường (không có Range)
        if request.method == 'HEAD':
            response = HttpResponse(b'', status=200, content_type=content_type)
        else:
            with open(full_path, 'rb') as f:
                data = f.read()
            response = HttpResponse(data, status=200, content_type=content_type)
        response['Content-Length'] = str(file_size)

    # Các header bắt buộc cho HTML5 Audio Streaming
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'public, max-age=86400'

    # CORS Headers cho phép trình duyệt phát audio từ origin khác
    allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    origin = request.META.get('HTTP_ORIGIN', '')
    if origin and origin in allowed_origins:
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Credentials'] = 'true'
    else:
        response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Range, Content-Type, Authorization, Accept'
    response['Access-Control-Expose-Headers'] = 'Content-Range, Content-Length, Accept-Ranges, Content-Disposition'

    return response
