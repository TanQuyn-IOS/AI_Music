"""
Script tạo dữ liệu mẫu cho AI Music Social
Chạy: python seed_data.py
"""
import os
import sys
import random
import django

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User, Follow
from apps.music.models import Song, Playlist, PlaylistSong, ListenHistory
from apps.social.models import Like, Comment, Post

print("🌱 Đang tạo dữ liệu mẫu...")

# Tạo users
users_data = [
    {'username': 'admin', 'email': 'admin@aimusic.vn', 'password': 'admin123', 'is_staff': True, 'is_superuser': True, 'is_artist': True, 'bio': 'Admin của AI Music Social'},
    {'username': 'son_tung', 'email': 'sontung@aimusic.vn', 'password': 'demo123', 'is_artist': True, 'bio': 'Ca sĩ, nhạc sĩ người Việt', 'first_name': 'Sơn Tùng', 'last_name': 'M-TP'},
    {'username': 'my_tam', 'email': 'mytam@aimusic.vn', 'password': 'demo123', 'is_artist': True, 'bio': 'Nữ ca sĩ hàng đầu Việt Nam', 'first_name': 'Mỹ', 'last_name': 'Tâm'},
    {'username': 'demo', 'email': 'demo@aimusic.vn', 'password': 'demo123', 'bio': 'Người yêu âm nhạc'},
    {'username': 'music_lover', 'email': 'lover@aimusic.vn', 'password': 'demo123', 'bio': 'Nghe nhạc mọi lúc mọi nơi'},
    {'username': 'rock_fan', 'email': 'rock@aimusic.vn', 'password': 'demo123', 'bio': 'Rock & Roll forever!'},
]

created_users = {}
for data in users_data:
    password = data.pop('password')
    user, created = User.objects.get_or_create(username=data['username'], defaults=data)
    if created:
        user.set_password(password)
        user.save()
        print(f"  ✅ Tạo user: {user.username}")
    created_users[user.username] = user

# Tạo follows
follow_pairs = [
    ('demo', 'son_tung'), ('demo', 'my_tam'),
    ('music_lover', 'son_tung'), ('music_lover', 'demo'),
    ('rock_fan', 'demo'), ('son_tung', 'my_tam'),
]
for follower_name, following_name in follow_pairs:
    Follow.objects.get_or_create(
        follower=created_users[follower_name],
        following=created_users[following_name]
    )

# Tạo songs
songs_data = [
    {'title': 'Hãy Trao Cho Anh', 'artist': 'son_tung', 'genre': 'vpop', 'mood': 'romantic', 'tempo': 95.0, 'duration': 231, 'audio_url': '', 'description': 'Hit V-Pop 2019'},
    {'title': 'Chạy Ngay Đi', 'artist': 'son_tung', 'genre': 'vpop', 'mood': 'energetic', 'tempo': 128.0, 'duration': 245, 'audio_url': '', 'description': 'Bài hát đình đám'},
    {'title': 'Lạc Trôi', 'artist': 'son_tung', 'genre': 'vpop', 'mood': 'melancholic', 'tempo': 80.0, 'duration': 268, 'audio_url': ''},
    {'title': 'Sóng Gió', 'artist': 'son_tung', 'genre': 'vpop', 'mood': 'sad', 'tempo': 75.0, 'duration': 256, 'audio_url': ''},
    {'title': 'Đừng Hỏi Em', 'artist': 'my_tam', 'genre': 'vpop', 'mood': 'sad', 'tempo': 70.0, 'duration': 240, 'audio_url': ''},
    {'title': 'Giả Vờ Thương', 'artist': 'my_tam', 'genre': 'vpop', 'mood': 'melancholic', 'tempo': 72.0, 'duration': 220, 'audio_url': ''},
    {'title': 'Because of You', 'artist': 'my_tam', 'genre': 'pop', 'mood': 'romantic', 'tempo': 90.0, 'duration': 230, 'audio_url': ''},
    {'title': 'Summertime Sadness', 'artist': 'admin', 'genre': 'pop', 'mood': 'sad', 'tempo': 82.0, 'duration': 265, 'audio_url': '', 'description': 'Classic pop'},
    {'title': 'Happy', 'artist': 'admin', 'genre': 'pop', 'mood': 'happy', 'tempo': 160.0, 'duration': 233, 'audio_url': ''},
    {'title': 'Bohemian Rhapsody', 'artist': 'admin', 'genre': 'rock', 'mood': 'energetic', 'tempo': 72.0, 'duration': 355, 'audio_url': ''},
    {'title': 'Hotel California', 'artist': 'admin', 'genre': 'rock', 'mood': 'melancholic', 'tempo': 75.0, 'duration': 390, 'audio_url': ''},
    {'title': 'Blue in Green', 'artist': 'admin', 'genre': 'jazz', 'mood': 'calm', 'tempo': 60.0, 'duration': 337, 'audio_url': ''},
    {'title': 'Clair de Lune', 'artist': 'admin', 'genre': 'classical', 'mood': 'calm', 'tempo': 50.0, 'duration': 310, 'audio_url': ''},
    {'title': 'Blinding Lights', 'artist': 'demo', 'genre': 'pop', 'mood': 'energetic', 'tempo': 171.0, 'duration': 200, 'audio_url': ''},
    {'title': 'Lo-fi Hip Hop Beat', 'artist': 'demo', 'genre': 'hip_hop', 'mood': 'calm', 'tempo': 85.0, 'duration': 180, 'audio_url': ''},
]

created_songs = []
for data in songs_data:
    artist = created_users[data.pop('artist')]
    song, created = Song.objects.get_or_create(
        title=data['title'], artist=artist,
        defaults={**data, 'play_count': random.randint(100, 50000)}
    )
    created_songs.append(song)
    if created:
        print(f"  🎵 Tạo bài: {song.title}")

# Tạo playlists
playlist_data = [
    {'name': 'V-Pop Hits 2024', 'owner': 'demo', 'description': 'Những bài V-Pop hay nhất'},
    {'name': 'Chill & Relax', 'owner': 'music_lover', 'description': 'Nhạc thư giãn'},
    {'name': 'Rock Classics', 'owner': 'rock_fan', 'description': 'Classic rock bất hủ'},
]

for data in playlist_data:
    owner = created_users[data.pop('owner')]
    pl, created = Playlist.objects.get_or_create(name=data['name'], owner=owner, defaults=data)
    if created:
        # Thêm vài bài vào playlist
        for i, song in enumerate(created_songs[:5]):
            PlaylistSong.objects.get_or_create(playlist=pl, song=song, defaults={'order': i})
        print(f"  📋 Tạo playlist: {pl.name}")

# Tạo lịch sử nghe
history_user = created_users['demo']
for song in random.sample(created_songs, min(8, len(created_songs))):
    ListenHistory.objects.get_or_create(user=history_user, song=song)

# Tạo likes
for song in created_songs[:6]:
    Like.objects.get_or_create(user=created_users['demo'], song=song)
    Like.objects.get_or_create(user=created_users['music_lover'], song=song)

# Tạo posts
posts_data = [
    {'author': 'demo', 'content': '🎵 Vừa nghe xong "Hãy Trao Cho Anh" - đỉnh thật! Sơn Tùng MTP mãi là legend V-Pop ❤️'},
    {'author': 'music_lover', 'content': 'Ai có gợi ý nhạc chill không? Đang cần thư giãn sau ngày dài 😌🎧'},
    {'author': 'rock_fan', 'content': 'Bohemian Rhapsody - bài hát vượt thời gian! Queen forever 🤘'},
    {'author': 'son_tung', 'content': '🎤 Cảm ơn mọi người đã ủng hộ! Sắp có sản phẩm mới rồi nhé 🔥'},
]

for data in posts_data:
    author = created_users[data.pop('author')]
    post, created = Post.objects.get_or_create(content=data['content'], author=author)
    if created:
        print(f"  📝 Tạo post: {post.content[:40]}...")

# Comments
if created_songs:
    Comment.objects.get_or_create(
        user=created_users['demo'],
        song=created_songs[0],
        defaults={'content': 'Bài này hay quá! 🔥'}
    )
    Comment.objects.get_or_create(
        user=created_users['music_lover'],
        song=created_songs[0],
        defaults={'content': 'Nghe mãi không chán 🎵'}
    )

print("\n✅ Tạo dữ liệu mẫu hoàn tất!")
print("\n📌 Tài khoản đăng nhập:")
print("  Admin: admin / admin123")
print("  Demo: demo / demo123")
print("  Nghệ sĩ: son_tung / demo123")
