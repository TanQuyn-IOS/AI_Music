  # 🎵 AI Music Social

Mạng xã hội âm nhạc thông minh với AI đề xuất nhạc, phân tích mood, chatbot tư vấn và trình sáng tác tự động.

## Tech Stack

| Tầng | Công nghệ |
|------|-----------|
| **Frontend** | React 18 + Vite + Tailwind CSS + Zustand |
| **Backend** | Django 4.2 + Django REST Framework + JWT |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **AI** | scikit-learn · midiutil · Markov Chain |

---

## Tính năng

### 🎧 Nghe nhạc
- Player cố định ở bottom: shuffle, repeat (none/all/one), seek, volume
- Queue panel — xem và điều hướng danh sách phát
- Lịch sử nghe tự động ghi nhận, dùng cho AI đề xuất

### 🤖 AI thông minh
- **Đề xuất theo content**: cosine similarity giữa genre/mood/tempo vectors
- **Đề xuất theo lịch sử**: tính điểm dựa trên genre/mood ưa thích
- **Đề xuất theo mood**: filter + sort theo lượt phát
- **Hồ sơ âm nhạc AI**: top genres/moods, tempo trung bình, cá tính âm nhạc
- **Chatbot**: rule-based, nhận diện mood từ tiếng Việt/Anh, gợi ý bài hát

### 🎼 AI Music Composer
- Chọn mood · thể loại · giọng · BPM · số ô nhịp
- Preview: scale, chord progression, cấu trúc track
- Tạo file MIDI 3-track (chords piano + melody piano + bass guitar)
- Tạo lời tiếng Việt bằng Markov Chain
- Lưu bài vào thư viện

### 📱 Mạng xã hội
- Đăng bài với ảnh đính kèm và bài hát đính kèm
- Like, bình luận, xóa bài đăng của mình
- Follow/unfollow người dùng
- Feed riêng chỉ hiển thị bài của người đang theo dõi
- Phân trang "Xem thêm" cho feed

### 🔔 Thông báo
- Notification bell hiển thị số tương tác mới trên bài đăng của bạn
- Tự động poll mỗi 60 giây

### 👤 Hồ sơ & Cài đặt
- Upload avatar + cover photo
- Đổi mật khẩu với strength indicator
- Chọn thể loại nhạc yêu thích
- Tab "Hồ sơ AI" trên trang cá nhân

---

## Cài đặt

### Yêu cầu
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend

# Tạo và kích hoạt virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình môi trường
cp .env.example .env
# Chỉnh sửa .env nếu cần (SECRET_KEY, database, v.v.)

# Khởi tạo database
python manage.py migrate

# Tạo tài khoản admin
python manage.py createsuperuser

# (Tuỳ chọn) Seed dữ liệu mẫu
python seed_data.py

# Chạy server
python manage.py runserver
```

Backend chạy tại: http://localhost:8000  
Admin panel: http://localhost:8000/admin

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend chạy tại: http://localhost:5173

### Chạy nhanh bằng batch file (Windows)

```bash
# Terminal 1
start_backend.bat

# Terminal 2
start_frontend.bat
```

---

## Tài khoản demo

| Vai trò | Username | Password |
|---------|----------|----------|
| Admin | `admin` | `admin123` |
| Demo user | `demo` | `demo123` |

---

## Cấu trúc dự án

```
AI Music/
├── backend/
│   ├── apps/
│   │   ├── users/          # Auth, profile, follow
│   │   ├── music/          # Songs, playlists, listen history
│   │   ├── social/         # Posts, likes, comments
│   │   └── ai_engine/      # Chatbot, recommender, music composer
│   ├── config/             # Settings, URLs, WSGI
│   ├── media/              # Upload files
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/            # Axios instance với JWT interceptor
        ├── components/     # Layout, Player, Search, SongCard...
        ├── pages/          # 13 pages
        └── store/          # Zustand: authStore, playerStore
```

---

## API Endpoints chính

```
# Auth
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/logout/
GET    /api/auth/profile/
PATCH  /api/auth/profile/

# Music
GET    /api/music/songs/
POST   /api/music/songs/
GET    /api/music/songs/trending/
POST   /api/music/songs/<id>/play/
GET    /api/music/playlists/

# Social
POST   /api/social/songs/<id>/like/
GET    /api/social/songs/<id>/comments/
GET    /api/social/posts/
POST   /api/social/posts/
DELETE /api/social/posts/<id>/

# AI
GET    /api/ai/recommend/song/<id>/
GET    /api/ai/recommend/user/
GET    /api/ai/recommend/mood/?mood=<mood>
GET    /api/ai/profile/
POST   /api/ai/chatbot/
POST   /api/ai/compose/preview/
POST   /api/ai/compose/lyrics/
POST   /api/ai/compose/midi/
```

---

## Môi trường Production

1. Đổi `DEBUG=False` trong `.env`
2. Set `SECRET_KEY` mạnh
3. Cấu hình PostgreSQL thay cho SQLite
4. Chạy `python manage.py collectstatic`
5. Dùng Gunicorn + Nginx cho backend
6. Build frontend: `npm run build`
