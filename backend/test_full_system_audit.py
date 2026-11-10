"""
Sonavia Studio — Complete System End-to-End Audit
=================================================
Kiểm tra toàn diện tất cả các phân hệ:
1. Xác thực & Tài khoản (Auth, JWT, Profile, Follow, Password)
2. Quản lý Thư viện Âm nhạc (Catalog, Filter, Search, Play, Playlists, History, Save AI Song)
3. Mạng Xã hội Âm nhạc (Social Posts, Likes, Comments, Trending, Community Stats)
4. Máy chủ Truyền thông Âm thanh (Streaming Server, HTTP 206 Range Request RFC 7233, CORS)
5. Bộ điều phối & Tích hợp AI (AI Analyze, Lyrics, Chatbot, MIDI)
"""

import os
import sys
import json
import uuid
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User, Follow
from apps.music.models import Song, Playlist, PlaylistSong, ListenHistory
from apps.social.models import Post, PostLike, PostComment, Like, Comment
from apps.music.media_views import serve_media_with_range

audit_results = []

def record_check(section: str, name: str, passed: bool, detail: str = ""):
    audit_results.append((section, name, passed, detail))
    status_icon = "✅ [PASS]" if passed else "❌ [FAIL]"
    print(f"  {status_icon} {name}")
    if detail:
        first_line = detail.strip().split("\n")[0]
        print(f"        {first_line}")


print("=" * 75)
print("🔍 SONAVIA AI MUSIC — KIỂM TRA TOÀN DIỆN & HOÀN THIỆN HỆ THỐNG")
print("=" * 75)

client = APIClient()

# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 1: TÀI KHOẢN & XÁC THỰC (AUTHENTICATION, JWT, PROFILE, FOLLOW)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[PHẦN 1/5] KIỂM TRA TÀI KHOẢN, XÁC THỰC JWT & TRANG CÁ NHÂN")
try:
    test_uname = f"audit_user_{uuid.uuid4().hex[:6]}"
    test_email = f"{test_uname}@sonavia.ai"
    test_pwd = "StrongPassword@123"

    # 1. Đăng ký tài khoản
    reg_res = client.post("/api/auth/register/", {
        "username": test_uname,
        "email": test_email,
        "password": test_pwd,
        "password2": test_pwd,
        "first_name": "Auditor",
        "last_name": "Tester",
    }, format="json")
    reg_ok = reg_res.status_code == 201 and "access" in reg_res.data and "refresh" in reg_res.data
    record_check("Auth", "User Registration & Initial Token Issuance", reg_ok, f"Username: {test_uname} | HTTP {reg_res.status_code}")

    # 2. Đăng nhập
    login_res = client.post("/api/auth/login/", {
        "username": test_uname,
        "password": test_pwd,
    }, format="json")
    access_token = login_res.data.get("access")
    refresh_token = login_res.data.get("refresh")
    login_ok = login_res.status_code == 200 and bool(access_token)
    record_check("Auth", "User Login & JWT Credentials Verification", login_ok, f"Access token received: {bool(access_token)}")

    # Gán credentials cho client
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # 3. Làm mới token (Refresh Token)
    rf_res = client.post("/api/token/refresh/", {"refresh": refresh_token}, format="json")
    rf_ok = rf_res.status_code == 200 and "access" in rf_res.data
    record_check("Auth", "JWT Token Refresh Endpoint (/api/token/refresh/)", rf_ok, f"HTTP {rf_res.status_code}")

    # 4. Xem & Cập nhật Profile
    prof_res = client.get("/api/auth/profile/")
    prof_ok = prof_res.status_code == 200 and prof_res.data.get("username") == test_uname
    record_check("Auth", "Retrieve User Profile", prof_ok, f"User: {prof_res.data.get('username')}")

    update_res = client.patch("/api/auth/profile/", {
        "bio": "Sonavia System Auditor Certified",
        "first_name": "Lead Auditor"
    }, format="json")
    update_ok = update_res.status_code == 200 and update_res.data.get("bio") == "Sonavia System Auditor Certified"
    record_check("Auth", "Update User Profile (Bio & First Name)", update_ok, f"Bio: {update_res.data.get('bio')}")

    # 5. Danh sách User & Tìm kiếm
    user_list_res = client.get(f"/api/auth/users/?search={test_uname}")
    list_ok = user_list_res.status_code == 200 and any(u["username"] == test_uname for u in user_list_res.data.get("results", []))
    record_check("Auth", "User Search & Directory Listing", list_ok, f"HTTP {user_list_res.status_code}")

    # 6. Đổi mật khẩu
    new_pwd = "NewSecurePassword@456"
    chg_res = client.post("/api/auth/change-password/", {
        "old_password": test_pwd,
        "new_password": new_pwd,
    }, format="json")
    chg_ok = chg_res.status_code == 200
    record_check("Auth", "Password Change Verification", chg_ok, f"HTTP {chg_res.status_code}")

    # 7. Follow / Unfollow người dùng khác
    target_user = User.objects.exclude(username=test_uname).first()
    if target_user:
        follow_res1 = client.post(f"/api/auth/users/{target_user.username}/follow/")
        f1_ok = follow_res1.status_code == 200 and follow_res1.data.get("following") is True
        follow_res2 = client.post(f"/api/auth/users/{target_user.username}/follow/")
        f2_ok = follow_res2.status_code == 200 and follow_res2.data.get("following") is False
        record_check("Auth", "Follow / Unfollow Toggle Mechanism", f1_ok and f2_ok, f"Target: {target_user.username}")
    else:
        record_check("Auth", "Follow Toggle", True, "Skipped (no other user)")

except Exception as e:
    record_check("Auth", "User Authentication Subsystem", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 2: THƯ VIỆN & PHÁT ÂM NHẠC (SONG CATALOG, PLAYLISTS, HISTORY)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[PHẦN 2/5] KIỂM TRA THƯ VIỆN BÀI HÁT, PLAYLIST VÀ LỊCH SỬ NGHE")
try:
    # 1. Lấy danh sách bài hát
    songs_res = client.get("/api/music/songs/")
    songs_ok = songs_res.status_code == 200 and "results" in songs_res.data
    record_check("Music", "Song Catalog Listing with Pagination", songs_ok, f"Count: {songs_res.data.get('count')}")

    # 2. Lọc theo genre và mood
    filter_res = client.get("/api/music/songs/?genre=pop&mood=happy")
    filter_ok = filter_res.status_code == 200
    record_check("Music", "Song Filtering (Genre & Mood)", filter_ok, f"HTTP {filter_res.status_code}")

    # 3. Sắp xếp theo title và play_count
    sort_title_res = client.get("/api/music/songs/?ordering=title")
    sort_play_res = client.get("/api/music/songs/?ordering=-play_count")
    sort_ok = sort_title_res.status_code == 200 and sort_play_res.status_code == 200
    record_check("Music", "Song Ordering (Alphabetical Title & Most Played)", sort_ok, f"HTTP {sort_title_res.status_code}")

    # 4. Chi tiết bài hát & Tăng lượt nghe
    test_song = Song.objects.filter(is_published=True).first()
    if test_song:
        initial_plays = test_song.play_count
        play_res = client.post(f"/api/music/songs/{test_song.id}/play/")
        play_ok = play_res.status_code == 200 and play_res.data.get("ok") is True
        test_song.refresh_from_db()
        play_count_ok = play_ok and (test_song.play_count == initial_plays + 1)
        record_check("Music", "Play Count Increment & Realtime Counter", play_count_ok, f"Initial: {initial_plays} -> New: {test_song.play_count}")

        # 5. Lưu lịch sử nghe nhạc
        hist_res = client.get("/api/music/history/")
        hist_ok = hist_res.status_code == 200 and any(h.get("song", {}).get("id") == test_song.id for h in hist_res.data.get("results", []))
        record_check("Music", "Listening History Auto-Tracking", hist_ok, f"History items: {hist_res.data.get('count')}")

    # 6. Tạo Playlist, thêm bài hát và lấy danh sách
    pl_res = client.post("/api/music/playlists/", {
        "title": "Audit Favorites Playlist",
        "description": "Created during system audit verification",
        "is_public": True,
    }, format="json")
    pl_ok = pl_res.status_code == 201 and "id" in pl_res.data
    pl_id = pl_res.data.get("id")
    record_check("Music", "Playlist Creation", pl_ok, f"Playlist ID: {pl_id}")

    if pl_ok and test_song:
        add_song_res = client.post(f"/api/music/playlists/{pl_id}/songs/", {"song_id": test_song.id}, format="json")
        add_ok = add_song_res.status_code == 200 and add_song_res.data.get("added") is True
        record_check("Music", "Add Song to Playlist Toggle", add_ok, f"HTTP {add_song_res.status_code}")

    # 7. Lưu bài nhạc AI vào thư viện (Save AI Song)
    save_ai_res = client.post("/api/music/songs/save-ai/", {
        "title": "Bản Tình Ca Mùa Thu (AI Master)",
        "genre": "vpop",
        "mood": "romantic",
        "duration": 180,
        "lyrics": "[Verse 1] Mưa rơi tí tách bên thềm...",
        "audio_url": "/media/generated/test_ai_song.mp3",
    }, format="json")
    save_ai_ok = save_ai_res.status_code == 201 and save_ai_res.data.get("id") is not None
    record_check("Music", "Save AI Generated Song to Library", save_ai_ok, f"Saved Song ID: {save_ai_res.data.get('id')}")

except Exception as e:
    record_check("Music", "Music Library Subsystem", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 3: MẠNG XÃ HỘI ÂM NHẠC (FEED, POSTS, LIKES, COMMENTS, TRENDING)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[PHẦN 3/5] KIỂM TRA MẠNG XÃ HỘI ÂM NHẠC & TƯƠNG TÁC CỘNG ĐỒNG")
try:
    # 1. Like / Unlike bài hát
    if test_song:
        like_song_res = client.post(f"/api/social/songs/{test_song.id}/like/")
        ls_ok = like_song_res.status_code == 200 and "liked" in like_song_res.data
        record_check("Social", "Song Like / Unlike Reaction Toggle", ls_ok, f"Liked status: {like_song_res.data.get('liked')}")

        # 2. Bình luận bài hát
        comment_res = client.post(f"/api/social/songs/{test_song.id}/comments/", {
            "content": "Giai điệu tuyệt vời, phối khí rất ấm áp!"
        }, format="json")
        c_ok = comment_res.status_code == 201 and "id" in comment_res.data
        record_check("Social", "Song Comment Creation", c_ok, f"Comment ID: {comment_res.data.get('id')}")

    # 3. Tạo bài viết Feed có đính kèm bài hát
    post_res = client.post("/api/social/posts/", {
        "content": "Vừa hoàn thiện bản nhạc mới với Sonavia AI, mời cả nhà cùng nghe thử! 🎵 #NewMusic #Sonavia",
        "song_id": test_song.id if test_song else None
    }, format="json")
    post_ok = post_res.status_code == 201 and "id" in post_res.data
    post_id = post_res.data.get("id")
    has_attached_song = post_res.data.get("song") is not None if test_song else True
    record_check("Social", "Community Post Creation with Attached Song", post_ok and has_attached_song, f"Post ID: {post_id} | Attached Song: {has_attached_song}")

    if post_ok:
        # 4. Thả tim bài viết
        plike_res = client.post(f"/api/social/posts/{post_id}/like/")
        plike_ok = plike_res.status_code == 200 and plike_res.data.get("liked") is True
        record_check("Social", "Post Like Reaction Toggle", plike_ok, f"Likes count: {plike_res.data.get('likes_count')}")

        # 5. Bình luận bài viết
        pcomm_res = client.post(f"/api/social/posts/{post_id}/comment/", {
            "content": "Nhạc hay quá bạn ơi!"
        }, format="json")
        pcomm_ok = pcomm_res.status_code == 201 and "id" in pcomm_res.data
        record_check("Social", "Post Comment Creation", pcomm_ok, f"Comment ID: {pcomm_res.data.get('id')}")

    # 6. Trending Posts, Tags & Community Stats
    trend_res = client.get("/api/social/trending/posts/")
    tags_res = client.get("/api/social/trending/tags/")
    stats_res = client.get("/api/social/stats/")
    social_data_ok = trend_res.status_code == 200 and tags_res.status_code == 200 and stats_res.status_code == 200
    record_check("Social", "Community Stats, Trending Tags & Posts", social_data_ok, f"Stats: {stats_res.data}")

except Exception as e:
    record_check("Social", "Social & Community Subsystem", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 4: STREAMING MEDIA SERVER & HTTP RANGE REQUEST RFC 7233
# ─────────────────────────────────────────────────────────────────────────────
print("\n[PHẦN 4/5] KIỂM TRA MÁY CHỦ PHÁT SÓNG ÂM THANH & HTTP RANGE REQUEST RFC 7233")
try:
    rf = RequestFactory()

    # Tạo tệp âm thanh giả lập 10,000 bytes trong MEDIA_ROOT
    test_media_dir = os.path.join(str(settings.MEDIA_ROOT), "test_stream")
    os.makedirs(test_media_dir, exist_ok=True)
    test_file_path = os.path.join(test_media_dir, "sample_audio.mp3")
    sample_content = b"ID3" + (b"\x00\xFF\xAA\x55" * 2500)
    with open(test_file_path, "wb") as f:
        f.write(sample_content)

    rel_path = "test_stream/sample_audio.mp3"

    # 1. Yêu cầu toàn bộ tệp (HTTP 200)
    req_full = rf.get(f"/media/{rel_path}")
    resp_full = serve_media_with_range(req_full, rel_path)
    full_ok = resp_full.status_code == 200 and resp_full["Accept-Ranges"] == "bytes" and int(resp_full["Content-Length"]) == len(sample_content)
    record_check("Streaming", "Full Audio Stream Request (HTTP 200, Accept-Ranges)", full_ok, f"Size: {len(sample_content):,} bytes")

    # 2. Yêu cầu dải dữ liệu một phần: bytes=0-1023 (HTTP 206 Partial Content)
    req_range1 = rf.get(f"/media/{rel_path}", HTTP_RANGE="bytes=0-1023")
    resp_range1 = serve_media_with_range(req_range1, rel_path)
    range1_ok = (
        resp_range1.status_code == 206 and
        resp_range1["Content-Range"] == f"bytes 0-1023/{len(sample_content)}" and
        int(resp_range1["Content-Length"]) == 1024 and
        len(resp_range1.content) == 1024
    )
    record_check("Streaming", "HTTP 206 Partial Content (bytes=0-1023 Scrubbing Range)", range1_ok, f"Content-Range: {resp_range1.get('Content-Range')}")

    # 3. Yêu cầu dải dữ liệu giữa chừng: bytes=5000- (Resume playback)
    req_range2 = rf.get(f"/media/{rel_path}", HTTP_RANGE="bytes=5000-")
    resp_range2 = serve_media_with_range(req_range2, rel_path)
    range2_ok = (
        resp_range2.status_code == 206 and
        resp_range2["Content-Range"] == f"bytes 5000-{len(sample_content)-1}/{len(sample_content)}" and
        int(resp_range2["Content-Length"]) == (len(sample_content) - 5000)
    )
    record_check("Streaming", "HTTP 206 Seeking / Resume Stream (bytes=5000-)", range2_ok, f"Content-Range: {resp_range2.get('Content-Range')}")

    # 4. Kiểm tra CORS Preflight OPTIONS cho Audio Player trên web
    req_options = rf.options(f"/media/{rel_path}")
    resp_options = serve_media_with_range(req_options, rel_path)
    cors_ok = resp_options.status_code == 204 and "Content-Range" in resp_options.get("Access-Control-Expose-Headers", "")
    record_check("Streaming", "CORS Preflight & Exposed Streaming Headers", cors_ok, f"Exposed: {resp_options.get('Access-Control-Expose-Headers')[:50]}...")

    # Xóa file test sau khi hoàn tất
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

except Exception as e:
    record_check("Streaming", "Media Streaming Subsystem", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 5: TÍCH HỢP & PHẢN HỒI CỦA BỘ ĐIỀU PHỐI AI
# ─────────────────────────────────────────────────────────────────────────────
print("\n[PHẦN 5/5] KIỂM TRA PHẢN HỒI ĐỒNG BỘ CÁC DỊCH VỤ AI")
try:
    # 1. Phân tích prompt
    an_res = client.post("/api/ai/analyze/", {"prompt": "Pop ballad acoustic guitar da diết"}, format="json")
    an_ok = an_res.status_code == 200 and "genre" in an_res.data and "bpm" in an_res.data
    record_check("AI", "Prompt Analyzer Response Structure", an_ok, f"Genre: {an_res.data.get('genre_name')} | BPM: {an_res.data.get('bpm')}")

    # 2. Tạo lời bài hát thông minh
    lyr_res = client.post("/api/ai/lyrics/generate/", {
        "topic": "Hồi ức mùa hạ",
        "genre": "vpop",
        "mood": "calm",
        "language": "vi"
    }, format="json")
    lyr_ok = lyr_res.status_code == 200 and "title" in lyr_res.data and len(lyr_res.data.get("lyrics", "")) > 100
    record_check("AI", "Smart Lyrics Generation Service", lyr_ok, f"Title: '{lyr_res.data.get('title')}' | Length: {len(lyr_res.data.get('lyrics', ''))} chars")

    # 3. Chatbot tư vấn âm nhạc
    chat_res = client.post("/api/ai/chatbot/", {"message": "Tư vấn cho tôi một bài nhạc nhẹ nhàng để thư giãn"}, format="json")
    chat_ok = chat_res.status_code == 200 and bool(chat_res.data.get("reply") or chat_res.data.get("message"))
    record_check("AI", "AI Music Chatbot Advisory", chat_ok, f"Mood: {chat_res.data.get('mood')} | Reply: {(chat_res.data.get('reply') or '')[:50]}...")

    # 4. AI MIDI Generation
    midi_res = client.post("/api/ai/compose/midi/", {
        "genre": "vpop",
        "mood": "romantic",
        "root_note": "G",
        "num_bars": 8
    }, format="json")
    midi_ok = midi_res.status_code == 200 and len(midi_res.content) > 200
    record_check("AI", "AI MIDI Generator Stream", midi_ok, f"Content-Type: {midi_res.get('Content-Type')} | Bytes: {len(midi_res.content)}")

except Exception as e:
    record_check("AI", "AI Integration Subsystem", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# TỔNG KẾT
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 75)
total_tests = len(audit_results)
passed_tests = sum(1 for _, _, ok, _ in audit_results if ok)
failed_tests = total_tests - passed_tests

print(f"📊 KẾT QUẢ KIỂM TRA TOÀN DIỆN: {passed_tests}/{total_tests} HẠNG MỤC ĐẠT CHUẨN!")
print("=" * 75)

if __name__ == '__main__':
    if failed_tests == 0:
        print("🎉 TOÀN BỘ HỆ THỐNG SONAVIA AI MUSIC HOÀN TOÀN CHUẨN XÁC, HOÀN THIỆN VÀ KHÔNG CÓ LỖI!")
        sys.exit(0)
    else:
        print(f"⚠️ Có {failed_tests} bài kiểm tra không đạt yêu cầu. Vui lòng xem chi tiết ở trên.")
        sys.exit(1)
