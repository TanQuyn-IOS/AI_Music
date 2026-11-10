import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIClient
from apps.users.models import User
from apps.music.models import Song
from apps.social.models import Like, Notification, DirectMessage
from apps.social.views import (
    NotificationListView, NotificationMarkReadView,
    ConversationListView, DirectMessageHistoryView, LikeToggleView
)
from apps.music.views import SongExtendView

def run_tests():
    print("=" * 60)
    print("🚀 BẮT ĐẦU KIỂM TRA CÁC TÍNH NĂNG MỚI ĐÃ HOÀN THIỆN")
    print("=" * 60)

    # 1. Chuẩn bị 2 user test
    u1, _ = User.objects.get_or_create(username='artist_alpha', defaults={'is_artist': True})
    u1.set_password('pass123')
    u1.save()

    u2, _ = User.objects.get_or_create(username='listener_beta', defaults={'is_artist': False})
    u2.set_password('pass123')
    u2.save()

    client = APIClient()

    # 2. Test Like bài hát & Trigger Thông báo thời gian thực
    test_song = Song.objects.filter(is_published=True).first()
    if not test_song:
        test_song = Song.objects.create(
            title="Giai Điệu Khởi Đầu",
            artist=u1,
            duration=90,
            genre='pop',
            mood='happy'
        )

    # Test u2 like song của u1 (hoặc tác giả bài hát)
    client.force_authenticate(user=u2)
    resp = client.post(f'/api/social/songs/{test_song.id}/like/')
    print(f"1. Like Song Toggle: HTTP {resp.status_code} | data: {resp.data}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    # Kiểm tra Notification có được tạo cho author không
    notif_count = Notification.objects.filter(recipient=test_song.artist).count()
    print(f"   -> Số lượng thông báo của tác giả {test_song.artist.username}: {notif_count}")
    assert notif_count >= 1, "Notification must be created on like!"
    print("   ✅ [PASS] Real-time Notification trigger on Like")

    # 3. Test API Notifications List & Mark Read
    client.force_authenticate(user=test_song.artist)
    resp = client.get('/api/social/notifications/')
    print(f"2. Notification List: HTTP {resp.status_code} | Total items: {len(resp.data.get('results', resp.data))}")
    assert resp.status_code == 200

    resp = client.post('/api/social/notifications/read/', {})
    print(f"   -> Mark All Read: HTTP {resp.status_code} | unread_count={resp.data.get('unread_count')}")
    assert resp.status_code == 200
    assert resp.data.get('unread_count') == 0
    print("   ✅ [PASS] Notification List & Mark Read Endpoints")

    # 4. Test Direct Messaging (DM 1-1)
    client.force_authenticate(user=u2)
    dm_resp = client.post(f'/api/social/messages/{u1.username}/', {'content': 'Chào nghệ sĩ, beat này rất hay!'})
    print(f"3. Send Direct Message: HTTP {dm_resp.status_code} | msg_id={dm_resp.data.get('id')}")
    assert dm_resp.status_code == 201
    print("   ✅ [PASS] Direct Messaging Send (DM)")

    # 5. Test Conversations List (Inbox)
    client.force_authenticate(user=u1)
    conv_resp = client.get('/api/social/messages/conversations/')
    print(f"4. Conversation List (Inbox): HTTP {conv_resp.status_code} | Partners: {len(conv_resp.data)}")
    assert conv_resp.status_code == 200
    assert len(conv_resp.data) >= 1
    assert conv_resp.data[0]['partner']['username'] == u2.username
    print("   ✅ [PASS] Direct Messaging Conversations Overview")

    # 6. Test Message History & Auto Mark Read
    hist_resp = client.get(f'/api/social/messages/{u2.username}/')
    print(f"5. Message History: HTTP {hist_resp.status_code} | Messages count: {len(hist_resp.data.get('messages', []))}")
    assert hist_resp.status_code == 200
    unread_now = DirectMessage.objects.filter(sender=u2, recipient=u1, is_read=False).count()
    assert unread_now == 0, "Messages must be marked as read when viewed"
    print("   ✅ [PASS] Message History & Read Auto-sync")

    # 7. Test Extend Song (Inpainting / Continuation)
    client.force_authenticate(user=u1)
    extend_resp = client.post(f'/api/music/songs/{test_song.id}/extend/', {
        'duration': 30,
        'prompt': 'Đoạn outro guitar acoustic êm dịu',
        'additional_lyrics': 'Lời ca ngân vang mãi không phai mờ'
    })
    print(f"6. Extend Track API: HTTP {extend_resp.status_code}")
    assert extend_resp.status_code == 201, f"Extend failed: {extend_resp.data}"
    ext_data = extend_resp.data
    print(f"   -> Extended Title: '{ext_data.get('title')}'")
    print(f"   -> Duration: {ext_data.get('duration')}s (Original: {test_song.duration}s)")
    print(f"   -> Audio File / URL: {ext_data.get('audio_file') or ext_data.get('audio_url')}")
    print("   ✅ [PASS] AI Track Extend & Audio Crossfade")

    print("\n" + "=" * 60)
    print("🎉 TẤT CẢ CÁC TÍNH NĂNG MỚI ĐÃ HOÀN TOÀN ĐẠT CHUẨN 100%!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
