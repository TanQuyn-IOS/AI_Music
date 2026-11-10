"""
Script thêm dữ liệu phong phú hơn cho demo
Chạy sau seed_data.py: python seed_extra.py
"""
import os
import sys
import django
import random

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User, Follow
from apps.music.models import Song, Playlist, PlaylistSong, ListenHistory
from apps.social.models import Like, Comment, Post, PostLike

print("🌱 Thêm dữ liệu phong phú...")

# Lấy users hiện có
try:
    demo = User.objects.get(username='demo')
    admin = User.objects.get(username='admin')
    son_tung = User.objects.get(username='son_tung')
except User.DoesNotExist:
    print("❌ Hãy chạy seed_data.py trước!")
    exit(1)

# ── Thêm bài hát quốc tế ──────────────────────────────────────────
extra_songs = [
    # Pop quốc tế
    {'title': 'Shape of You', 'artist': 'admin', 'genre': 'pop', 'mood': 'happy', 'tempo': 96.0, 'duration': 234},
    {'title': 'Stay With Me', 'artist': 'admin', 'genre': 'pop', 'mood': 'sad', 'tempo': 82.0, 'duration': 172},
    {'title': 'Perfect', 'artist': 'admin', 'genre': 'pop', 'mood': 'romantic', 'tempo': 96.0, 'duration': 263},
    {'title': 'Someone Like You', 'artist': 'admin', 'genre': 'pop', 'mood': 'melancholic', 'tempo': 67.0, 'duration': 285},
    {'title': 'Dance Monkey', 'artist': 'admin', 'genre': 'pop', 'mood': 'energetic', 'tempo': 98.0, 'duration': 210},
    # K-Pop
    {'title': 'Dynamite', 'artist': 'admin', 'genre': 'kpop', 'mood': 'happy', 'tempo': 114.0, 'duration': 199},
    {'title': 'Butter', 'artist': 'admin', 'genre': 'kpop', 'mood': 'energetic', 'tempo': 110.0, 'duration': 164},
    {'title': 'IDOL', 'artist': 'admin', 'genre': 'kpop', 'mood': 'uplifting', 'tempo': 130.0, 'duration': 254},
    {'title': 'Lovesick Girls', 'artist': 'admin', 'genre': 'kpop', 'mood': 'melancholic', 'tempo': 114.0, 'duration': 210},
    # Rock / Metal
    {'title': 'Smells Like Teen Spirit', 'artist': 'admin', 'genre': 'rock', 'mood': 'angry', 'tempo': 116.0, 'duration': 301},
    {'title': 'Sweet Child O Mine', 'artist': 'admin', 'genre': 'rock', 'mood': 'energetic', 'tempo': 125.0, 'duration': 356},
    {'title': 'Wish You Were Here', 'artist': 'admin', 'genre': 'rock', 'mood': 'melancholic', 'tempo': 64.0, 'duration': 334},
    # Jazz / Classical
    {'title': 'Take Five', 'artist': 'admin', 'genre': 'jazz', 'mood': 'calm', 'tempo': 174.0, 'duration': 324},
    {'title': 'Autumn Leaves', 'artist': 'admin', 'genre': 'jazz', 'mood': 'melancholic', 'tempo': 100.0, 'duration': 198},
    {'title': 'Moonlight Sonata', 'artist': 'admin', 'genre': 'classical', 'mood': 'melancholic', 'tempo': 58.0, 'duration': 342},
    # V-Pop thêm
    {'title': 'Tình Yêu Màu Nắng', 'artist': 'son_tung', 'genre': 'vpop', 'mood': 'romantic', 'tempo': 88.0, 'duration': 248},
    {'title': 'Muộn Rồi Mà Sao Còn', 'artist': 'son_tung', 'genre': 'vpop', 'mood': 'sad', 'tempo': 78.0, 'duration': 272},
    {'title': 'Có Chắc Yêu Là Đây', 'artist': 'son_tung', 'genre': 'vpop', 'mood': 'energetic', 'tempo': 120.0, 'duration': 198},
    # Hip-Hop / Electronic
    {'title': 'SICKO MODE', 'artist': 'demo', 'genre': 'hip_hop', 'mood': 'energetic', 'tempo': 155.0, 'duration': 312},
    {'title': 'Blinding Lights Remix', 'artist': 'demo', 'genre': 'electronic', 'mood': 'energetic', 'tempo': 171.0, 'duration': 220},
    {'title': 'Stay (feat. Justin Bieber)', 'artist': 'demo', 'genre': 'pop', 'mood': 'sad', 'tempo': 170.0, 'duration': 141},
    # Indie / Folk
    {'title': 'Ho Hey', 'artist': 'demo', 'genre': 'folk', 'mood': 'happy', 'tempo': 76.0, 'duration': 164},
    {'title': 'Skinny Love', 'artist': 'demo', 'genre': 'indie', 'mood': 'melancholic', 'tempo': 97.0, 'duration': 222},
    {'title': 'Little Talks', 'artist': 'demo', 'genre': 'indie', 'mood': 'uplifting', 'tempo': 111.0, 'duration': 263},
]

users_map = {u.username: u for u in User.objects.all()}
new_songs = []
for data in extra_songs:
    artist = users_map.get(data.pop('artist'), admin)
    song, created = Song.objects.get_or_create(
        title=data['title'], artist=artist,
        defaults={**data, 'play_count': random.randint(500, 100000)}
    )
    new_songs.append(song)
    if created:
        print(f"  🎵 {song.title}")

# ── Thêm playlists phong phú ──
all_songs = list(Song.objects.all())

playlists_extra = [
    {'name': 'Top Hits 2024', 'owner': demo, 'desc': 'Những bài hay nhất 2024'},
    {'name': 'Chill Vibes', 'owner': demo, 'desc': 'Nhạc thư giãn buổi tối'},
    {'name': 'Workout Mix', 'owner': demo, 'desc': 'Nhạc tập thể dục'},
    {'name': 'K-Pop Favorites', 'owner': demo, 'desc': 'K-Pop yêu thích'},
    {'name': 'Sad Hours', 'owner': demo, 'desc': 'Khi tâm trạng không tốt'},
    {'name': 'V-Pop Collection', 'owner': son_tung, 'desc': 'Tuyển tập V-Pop'},
]

for pl_data in playlists_extra:
    pl, created = Playlist.objects.get_or_create(
        name=pl_data['name'], owner=pl_data['owner'],
        defaults={'description': pl_data['desc'], 'is_public': True}
    )
    if created:
        songs_for_pl = random.sample(all_songs, min(8, len(all_songs)))
        for i, s in enumerate(songs_for_pl):
            PlaylistSong.objects.get_or_create(playlist=pl, song=s, defaults={'order': i})
        print(f"  📋 {pl.name}")

# ── Thêm lịch sử nghe ──
for user in [demo, admin]:
    songs_to_listen = random.sample(all_songs, min(15, len(all_songs)))
    for s in songs_to_listen:
        ListenHistory.objects.get_or_create(user=user, song=s)

# ── Thêm likes ──
for s in random.sample(all_songs, min(12, len(all_songs))):
    for user in [demo, admin]:
        Like.objects.get_or_create(user=user, song=s)

# ── Thêm posts phong phú ──
extra_posts = [
    (demo, "🎵 Vừa khám phá được album mới cực hay! AI đề xuất chính xác quá 🤖"),
    (demo, "Ai biết bài nhạc chill để làm việc không? Recommend giúp mình với 🙏"),
    (demo, "K-Pop ngày càng phát triển mạnh, thích quá! BTS, BLACKPINK đều bá đạo 🇰🇷✨"),
    (admin, "🎼 Chia sẻ một playlist chill cho cuối tuần. Enjoy! 🌿"),
    (admin, "Tính năng AI Sáng tác đã hoạt động! Thử tạo bản nhạc riêng xem sao 🎹"),
    (son_tung, "💙 Cảm ơn mọi người đã nghe nhạc. Mình đang làm album mới, sắp ra mắt!"),
    (son_tung, "V-Pop đang vươn ra thế giới rồi! Tự hào lắm 🇻🇳🎵"),
]

for author, content in extra_posts:
    post, created = Post.objects.get_or_create(content=content, author=author)
    if created:
        print(f"  📝 {content[:40]}...")

# ── Thêm comments ──
vpop_songs = Song.objects.filter(genre='vpop')[:5]
comment_texts = [
    "Bài này hay quá!! 🔥", "Nghe mãi không chán 🎵",
    "Cực phẩm luôn! ❤️", "Đỉnh của chóp!", "Mood cả ngày 💯",
    "Bài xuất sắc 🙌", "Ai cũng phải nghe bài này!",
]
for song in vpop_songs:
    for user in random.sample([demo, admin, son_tung], 2):
        text = random.choice(comment_texts)
        Comment.objects.get_or_create(user=user, song=song, defaults={'content': text})

print(f"\n✅ Đã thêm dữ liệu! Tổng: {Song.objects.count()} bài hát, {Playlist.objects.count()} playlist")
print(f"   {Post.objects.count()} posts, {Comment.objects.count()} comments, {Like.objects.count()} likes")
