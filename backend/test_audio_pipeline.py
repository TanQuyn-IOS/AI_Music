# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

if __name__ == '__main__':
    from django.test import Client

    client = Client()

    print("=== BẮT ĐẦU TEST TOÀN DIỆN PIPELINE AUDIO ===")

    # 1. Test POST /api/music/generate/
    print("\n1. Gửi request POST /api/music/generate/ ...")
    # Test với prompt ngắn
    payload = {
        "prompt": "test acoustic chill",
        "duration": 15,
        "seed": "123456",
        "instrumental": True,
    }
    # Gọi endpoint
    response = client.post("/api/music/generate/", data=payload, content_type="application/json")
    print("Response Status Code:", response.status_code)
    print("Response Content-Type:", response.get("Content-Type"))
    print("Response Headers:")
    for k, v in response.items():
        if k.startswith("X-") or k in ["Content-Disposition", "Content-Type", "Content-Length"]:
            print(f"  {k}: {v}")

    content_len = len(response.content)
    print(f"Content length received: {content_len} bytes")
    if content_len > 0:
        print(f"First 16 bytes: {response.content[:16]}")

    # 2. Kiểm tra file trên disk
    audio_url = response.get("X-Audio-Url")
    print(f"\n2. X-Audio-Url: {audio_url}")
    if audio_url:
        # URL dạng /media/generated/sonavia_...mp3
        from django.conf import settings
        rel_path = audio_url.replace(settings.MEDIA_URL, "")
        disk_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        print(f"Disk path: {disk_path}")
        print(f"Disk file exists: {os.path.exists(disk_path)}")
        if os.path.exists(disk_path):
            size = os.path.getsize(disk_path)
            print(f"Disk file size: {size} bytes")

        # 3. Test GET request đến audio_url qua static/media serving của Django
        print(f"\n3. Test GET request đến audio_url: {audio_url}")
        media_resp = client.get(audio_url)
        print("Media GET Status Code:", media_resp.status_code)
        print("Media GET Content-Type:", media_resp.get("Content-Type"))
        print("Media GET Content-Length:", media_resp.get("Content-Length"))

        # 4. Test Range request (Partial Content 206)
        print("\n4. Test HTTP Range Request (HTTP_RANGE='bytes=0-1024')")
        range_resp = client.get(audio_url, HTTP_RANGE="bytes=0-1024")
        print("Range GET Status Code:", range_resp.status_code)
        print("Range GET Content-Range:", range_resp.get("Content-Range"))
        print("Range GET Accept-Ranges:", range_resp.get("Accept-Ranges"))

print("\n=== HOÀN TẤT KIỂM TRA ===")
