# SONAVIA AI — TOÀN BỘ BÁO CÁO KIỂM TOÁN HỆ THỐNG ĐỘC LẬP (FULL SYSTEM AUDIT REPORT)

> **Báo cáo kiểm toán độc lập về Kiến trúc, Mã nguồn, Cơ sở dữ liệu, Bảo mật, AI/Audio Engine và Mức độ sẵn sàng vận hành của dự án Sonavia AI.**  
> **Ngày thực hiện:** 02/11/2026  
> **Phiên bản hệ thống:** Sonavia AI v2.2 (Giai đoạn nâng cấp Vietnamese Phonetics & Intelligent Orchestration)  
> **Đơn vị thẩm định:** Đội ngũ Chuyên gia Độc lập (Software Architect, Full-stack Dev, AI/ML Audio Engineer, Cybersecurity, QA/DevOps)

---

## MỤC LỤC
1. [PHẦN A: TỔNG QUAN KIẾN TRÚC & CÔNG NGHỆ THỰC TẾ](#phần-a-tổng-quan-kiến-trúc--công-nghệ-thực-tế)
2. [PHẦN B: BẢNG ĐÁNH GIÁ CHỨC NĂNG HỆ THỐNG](#phần-b-bảng-đánh-giá-chức-năng-hệ-thống)
3. [PHẦN C: DANH SÁCH LỖI VÀ LỖ HỔNG CHI TIẾT (EVIDENCE-BASED)](#phần-c-danh-sách-lỗi-và-lỗ-hổng-chi-tiết)
4. [PHẦN D: PHÂN TÍCH NỢ KỸ THUẬT (TECHNICAL DEBT)](#phần-d-phân-tích-nợ-kỹ-thuật-technical-debt)
5. [PHẦN E: BÁO CÁO KIỂM THỬ THỰC TẾ (TEST EXECUTION REPORT)](#phần-e-báo-cáo-kiểm-thử-thực-tế)
6. [PHẦN F: DANH SÁCH ƯU TIÊN SỬA LỖI (PRIORITY ROADMAP P0 - P3)](#phần-f-danh-sách-ưu-tiên-sửa-lỗi)
7. [PHẦN G: KẾT LUẬN THỰC TẾ & KHUYẾN NGHỊ](#phần-g-kết-luận-thực-tế--khuyến-nghị)

---

## PHẦN A: TỔNG QUAN KIẾN TRÚC & CÔNG NGHỆ THỰC TẾ

### 1. Hạ tầng & Môi trường thực tế
- **Hệ điều hành:** Windows 11 (64-bit).
- **Python Runtime:** Python 3.13.9 (`backend/venv`).
- **PyTorch & CUDA:** PyTorch `2.6.0+cu124` kèm CUDA 12.4 runtime.
- **Phần cứng GPU:** NVIDIA GeForce RTX 3050 6GB Laptop GPU (VRAM 6,144 MB).
- **Node.js & Frontend Tooling:** Node.js, Vite 4.5.0, React 18.2.0, TailwindCSS 3.3.5, Zustand 4.4.7.
- **Backend Framework:** Django 4.2.7, Django REST Framework 3.14.0, SimpleJWT 5.5.1.
- **Database:** SQLite 3 (`backend/db.sqlite3`, 23 bảng, kích thước ~491 KB).

### 2. Sơ đồ Kiến trúc Tổng thể (Architecture Diagram)

```mermaid
flowchart TD
    subgraph Frontend["Frontend Client (React 18 + Vite + Zustand)"]
        UI_Home["Trang chủ / Home (`/`)"]
        UI_Create["Sonavia Studio (`/create`)"]
        UI_Compose["AI Studio cũ (`/compose`)"]
        UI_Social["Cộng đồng & Bảng tin (`/community`, `/feed`)"]
        UI_Player["Persistent Audio Player (HTML5 + Range 206)"]
        AxiosClient["Axios Interceptor (`Bearer JWT` + Token Refresh)"]
    end

    subgraph Backend_Gateway["Backend API Gateway (Django 4.2 + DRF)"]
        MW_Cors["CorsMiddleware"]
        MW_Auth["JWT Authentication / SimpleJWT"]
        Router_Music["Music Router (`/api/music/*`)"]
        Router_Users["Auth Router (`/api/auth/*`)"]
        Router_Social["Social Router (`/api/social/*`)"]
        Router_AI["AI Engine Router (`/api/ai/*`)"]
        Streamer["High-Performance Media Streamer (RFC 7233)"]
    end

    subgraph AI_Engine["Sonavia AI Engine & Orchestrator"]
        Orchestrator["Intelligent Music Orchestrator"]
        VN_Phonetics["Vietnamese Phonetic Layer (NFC, Formant, 6 Tones)"]
        DSP_Mastering["DSP Mastering (Biquad EQ, High-Pass, True-Peak)"]
        Provider_ACE["ACE-Step Provider (Gradio HF Space)"]
        Provider_MusicGen["MusicGen Provider (Local RTX 3050 CUDA)"]
        Provider_Synth["Harmonic Synth Provider (Acoustic Backup)"]
        Provider_SVS["Vietnamese SVS Provider (Interface / Unavailable)"]
        LLM_Service["LLM Service (Google Gemini / OpenAI / Rule-based)"]
    end

    subgraph Database["Database & File Storage"]
        DB_SQLite[("SQLite 3 DB (db.sqlite3)")]
        Media_Root["Media Storage (`/backend/media/*`)"]
    end

    UI_Create --> AxiosClient
    UI_Compose --> AxiosClient
    UI_Home --> AxiosClient
    UI_Social --> AxiosClient
    UI_Player -.-> Streamer

    AxiosClient --> MW_Cors --> MW_Auth
    MW_Auth --> Router_Music & Router_Users & Router_Social & Router_AI

    Router_Music --> DB_SQLite
    Router_Users --> DB_SQLite
    Router_Social --> DB_SQLite
    Streamer --> Media_Root

    Router_AI --> Orchestrator
    Router_Music --> Orchestrator

    Orchestrator --> VN_Phonetics
    Orchestrator --> Provider_ACE
    Orchestrator --> Provider_MusicGen
    Orchestrator --> Provider_Synth
    Orchestrator --> Provider_SVS
    Orchestrator --> DSP_Mastering
    Router_AI --> LLM_Service

    DSP_Mastering --> Media_Root
```

### 3. Phân chia Module & Trách nhiệm Thực tế
1. **`apps.users`**: Quản lý người dùng mở rộng (`User` kế thừa `AbstractUser`), JWT Authentication (Login/Register/Refresh/Blacklist), Profile, Follow/Unfollow giữa người dùng.
2. **`apps.music`**: Quản lý bài hát (`Song`), danh sách phát (`Playlist`, `PlaylistSong`), lịch sử nghe (`ListenHistory`), tìm kiếm/lọc thể loại, endpoint phát nhạc HTTP Range (`media_views.py`), và Save AI Song.
3. **`apps.social`**: Tương tác mạng xã hội: Thích bài hát (`Like`), Bình luận lồng nhau (`Comment`), Bài viết cộng đồng (`Post`), Thích/Bình luận bài viết (`PostLike`, `PostComment`), Thống kê cộng đồng và gợi ý người dùng.
4. **`apps.ai_engine`**:
   - `orchestrator.py`: Bộ điều phối 4 tuyến thông minh (Text-to-Song, Lyrics-to-Song, Instrumental, Melodic Lead).
   - `vietnamese_phonetics.py`: Chuẩn hóa Unicode NFC, phân tích âm tiết (Onset, Glide, Nucleus, Coda, Tone 1-6), phân loại âm mũi/âm tắc/nguyên âm đơn đôi ba.
   - `acestep_generator.py` & `providers/acestep_provider.py`: Sinh nhạc và giọng hát qua Hugging Face Gradio Client.
   - `music_generator.py` & `providers/musicgen_provider.py`: Sinh nhạc cục bộ bằng Meta MusicGen trên GPU RTX 3050 qua PyTorch.
   - `providers/synth_provider.py`: Bộ tổng hợp sóng hài Stereo dự phòng không phụ thuộc GPU.
   - `providers/vietnamese_svs_provider.py`: Interface nghiên cứu SVS tiếng Việt (công khai trạng thái Unavailable khi thiếu checkpoint giọng hát).
   - `audio_mastering.py`: DSP Studio Mastering (Low-cut 65Hz, Boxiness cut 280Hz, Formant Boost 3.2kHz, Air Shelf 11kHz, True-Peak Normalization 0.891 / -1 dBFS).
   - `audio_mixer.py`: Trộn vocal và instrumental bảo tồn kênh Stereo.
   - `image_analyzer.py`: Visual Synesthesia (Phân tích ảnh sang âm nhạc bằng Pillow, trích xuất RGB/HSV/độ ấm/độ sáng).
   - `llm_service.py` & `chatbot.py`: Tích hợp Google Gemini, OpenAI và fallback Rule-based.

---

## PHẦN B: BẢNG ĐÁNH GIÁ CHỨC NĂNG HỆ THỐNG

| Module / Tính năng | Trạng thái | Bằng chứng thực tế (Evidence) | Vấn đề & Giới hạn |
| :--- | :---: | :--- | :--- |
| **Xác thực & Người dùng (Auth & Users)** | **PASS WITH LIMITATIONS** | Đăng ký, đăng nhập JWT, refresh token, đổi mật khẩu hoạt động tốt qua DRF và SimpleJWT. | **Rò rỉ PII**: `UserSerializer` trả về `email` cho mọi người dùng khi xem danh sách/bài hát. Thiếu Rate Limiting chống Brute-force. |
| **Quản lý Bài hát & Media (Songs & Playlists)** | **PASS WITH LIMITATIONS** | Model `Song`, `Playlist`, `PlaylistSong` tạo quan hệ đúng; HTTP 206 Range Stream mượt mà trên browser. | **Lỗ hổng IDOR/BOLA**: `SongDetailView` và `PlaylistDetailView` không kiểm tra quyền tác giả khi sửa/xóa. Thiếu ràng buộc kích thước/loại file khi upload bài hát. |
| **Tương tác Mạng xã hội (Social Feed, Likes, Comments)** | **PASS** | Like toggle, bình luận, bài đăng cộng đồng, theo dõi nghệ sĩ hoạt động ổn định; `PostDetailView` có kiểm tra tác giả. | Hiệu năng: Hashtag trending trích xuất bằng regex trong bộ nhớ Python trên toàn bộ bài viết thay vì đánh chỉ mục DB. |
| **Vietnamese Phonetic Layer** | **PASS** | 21/21 Unit Tests trong `test_vietnamese_phonetics.py` PASS; chuẩn hóa NFC, phân tích 6 thanh điệu, Onset/Glide/Nucleus/Coda chính xác 100%. | Đóng vai trò là tầng chuẩn hóa tiền xử lý và nhúng prompt, chưa kết nối trực tiếp với acoustic model cục bộ do thiếu voicebank tiếng Việt. |
| **Intelligent Music Orchestrator** | **PASS** | 5/5 Unit Tests trong `test_phase2_3_intelligent_orchestrator.py` PASS; định tuyến 4 cấp và chuyển tiếp minh bạch. | Khi ACE-Step HF Space mất mạng/timeout, hệ thống fallback về MusicGen/Synth và trả về `vocal_type: "melodic_lead"`. |
| **Vietnamese SVS Provider (DiffSinger/ViSVS)** | **PASS WITH LIMITATIONS** | Báo cáo minh bạch `is_available() -> False` (8/8 Tests trong `test_phase2_2b_svs_provider.py` PASS), không giả mạo vocal. | Chưa thể hát tiếng Việt cục bộ (Local Offline SVS) do thiếu pre-trained checkpoint và voicebank tiếng Việt nguồn mở. |
| **Loại bỏ Bark Fallback an toàn** | **PASS** | 8/8 Tests trong `test_phase2_2a_remove_bark.py` PASS; Bark bị chặn hoàn toàn, frontend dist 0 từ khóa bark. | `suno-bark` vẫn còn lưu lại trong file `requirements.txt` gây nặng môi trường cài đặt. |
| **DSP Audio Mastering & Mixing** | **PASS** | 4/4 Tests trong `test_audio_mastering.py` PASS; True-Peak chuẩn hóa -1.0 dBFS (0.8910), Low-cut 65Hz lọc ù, triệt tiêu méo clipping. | Chưa hỗ trợ nén dynamic range đa băng tần (Multiband Compressor) phức tạp. |
| **Visual Synesthesia (Ảnh sang Nhạc)** | **PASS** | `image_analyzer.py` chạy offline hoàn toàn bằng PIL; tính toán màu sắc, độ sáng, độ bão hòa và sinh prompt chính xác. | Chưa tích hợp Vision-Language Model cục bộ (chỉ dựa trên thống kê pixel RGB/HSV). |
| **AI Chatbot & Đề xuất (Recommendation)** | **PASS WITH LIMITATIONS** | Chatbot 2 tầng (LLM + Rule-based) phản hồi mượt mà; Recommender tính toán tương đồng đặc trưng. | **Nghẽn hiệu năng nghiêm trọng**: `recommender.py` gọi hàm embedding tuần tự cho mọi bài hát trong database mà không lưu cache vector vào DB. |
| **Frontend UI/UX (React & Studio)** | **PASS WITH LIMITATIONS** | Bundle Vite build thành công (`dist/index.html`, 608KB JS, 93KB CSS); phát nhạc, waveform, equalizer hoạt động. | **Phân mảnh giao diện nghiêm trọng**: Tồn tại đồng thời `CreatePage.jsx` (120KB) và `ComposePage.jsx` (74KB). Sidebar điều hướng sang `/compose` trong khi HomePage điều hướng sang `/create`. |

---

## PHẦN C: DANH SÁCH LỖI VÀ LỖ HỔNG CHI TIẾT

### BẢNG TỔNG HỢP PHÂN LOẠI LỖI (SEVERITY MATRIX)
- **CRITICAL (Nghiêm trọng - Cần chặn ngay):** 4 lỗi
- **HIGH (Mức độ cao - Ảnh hưởng bảo mật/dữ liệu):** 4 lỗi
- **MEDIUM (Mức độ trung bình - Hiệu năng & UI/UX):** 5 lỗi
- **LOW / INFO (Mức độ thấp - Mã nguồn & cấu hình):** 3 lỗi

---

### 1. NHÓM LỖI CRITICAL (NGUY HIỂM CAO NHẤT)

#### [BUG-CRIT-01] Lỗ hổng Đọc file Tùy ý & Trích xuất Dữ liệu (Arbitrary File Read / Path Traversal)
- **Mức độ:** **CRITICAL** (CVSS 9.8)
- **Vị trí file:** `backend/apps/music/views.py`, Dòng 194 – 208 (`SaveAiSongView.post`)
- **Mô tả:** Trong endpoint lưu bài hát AI `POST /api/music/songs/save-ai/`, tham số `cover_image_url` từ request của client được xử lý bằng cách thay thế chuỗi đơn giản:
  ```python
  clean_cover = cover_image_url.replace(settings.MEDIA_URL, '').lstrip('/\\')
  full_cover = os.path.join(str(settings.MEDIA_ROOT), clean_cover)
  if os.path.exists(full_cover):
      shutil.copy2(full_cover, os.path.join(covers_dir, cover_name))
  ```
- **Nguyên nhân:** Không kiểm tra `os.path.realpath` hoặc sử dụng `os.path.commonpath` để đảm bảo file nguồn nằm trong `MEDIA_ROOT`. Ký tự `../` không bị chặn.
- **Ảnh hưởng:** Kẻ tấn công có thể truyền `cover_image_url: "/media/../db.sqlite3"` hoặc `"/media/../.env"`. Hệ thống sẽ sao chép toàn bộ database hoặc file cấu hình chứa SECRET_KEY / API Keys vào thư mục công khai `song_covers/`, cho phép tải trực tiếp qua HTTP.
- **Cách tái hiện:** Gửi request authenticated tới `/api/music/songs/save-ai/` với body `{"title": "Test", "cover_image_url": "/media/../db.sqlite3", "audio_url": "dummy"}`.
- **Đề xuất khắc phục:** Sử dụng hàm kiểm tra chuẩn như trong `media_views.py`:
  ```python
  real_media_root = os.path.realpath(str(settings.MEDIA_ROOT))
  real_full = os.path.realpath(os.path.join(str(settings.MEDIA_ROOT), clean_cover))
  if not real_full.startswith(real_media_root + os.sep) or not os.path.isfile(real_full):
      # Bỏ qua hoặc báo lỗi
  ```

---

#### [BUG-CRIT-02] Lỗ hổng Kiểm soát Truy cập Cấp Đối tượng (Broken Object Level Authorization / IDOR)
- **Mức độ:** **CRITICAL** (OWASP API Top 10 - API1:2023)
- **Vị trí file:**
  - `backend/apps/music/views.py`, Dòng 34 – 45 (`SongDetailView`)
  - `backend/apps/music/views.py`, Dòng 79 – 90 (`PlaylistDetailView`)
- **Mô tả:** `SongDetailView` và `PlaylistDetailView` kế thừa `generics.RetrieveUpdateDestroyAPIView` với quyền `IsAuthenticated` cho các phương thức ghi/sửa/xóa (`PUT`, `PATCH`, `DELETE`). Tuy nhiên, cả hai view **hoàn toàn không cài đặt lớp quyền tác giả (IsOwnerOrReadOnly)** hoặc override `perform_update` / `perform_destroy` để kiểm tra `request.user == instance.artist` hay `request.user == instance.owner`.
- **Nguyên nhân:** Thiếu kiểm tra sở hữu tài nguyên (Object-level Permission Check).
- **Ảnh hưởng:** Bất kỳ người dùng nào đã đăng nhập đều có thể sửa đổi tiêu đề, đổi nhạc, hoặc **XÓA HOÀN TOÀN** bất kỳ bài hát hoặc playlist nào của bất kỳ người dùng khác bằng cách gửi request `DELETE /api/music/songs/<id>/`.
- **Cách tái hiện:** Đăng nhập bằng user A, lấy ID bài hát của user B, gửi lệnh `DELETE /api/music/songs/<id_b>/` kèm token của user A -> HTTP 204 No Content (bài hát bị xóa mất khỏi hệ thống).
- **Đề xuất khắc phục:** Tạo custom permission `IsOwnerOrReadOnly` trong `apps/common/permissions.py` hoặc override `perform_update` và `perform_destroy`:
  ```python
  def perform_update(self, serializer):
      if serializer.instance.artist != self.request.user and not self.request.user.is_staff:
          raise PermissionDenied('Bạn không có quyền chỉnh sửa bài hát này.')
      serializer.save()
  ```

---

#### [BUG-CRIT-03] Lộ Bí mật API Token & Tài khoản Mặc định trong Script Khởi động
- **Mức độ:** **CRITICAL**
- **Vị trí file:** `start_backend.bat`, Dòng 33 – 34 và Dòng 44
- **Mô tả:** Trong file `start_backend.bat` có chứa token HuggingFace cá nhân được viết dạng plain-text:
  ```bat
  set HF_TOKEN=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
  ```
  Và công khai tài khoản quản trị:
  ```bat
  echo  Login:  admin / admin123
  ```
- **Nguyên nhân:** Hardcode credentials trong file batch khởi động để tiện thử nghiệm cục bộ.
- **Ảnh hưởng:** Rò rỉ HuggingFace API Token ra bên ngoài (hoặc khi commit lên git repository); nguy cơ chiếm quyền tài khoản và vượt hạn ngạch API.
- **Đề xuất khắc phục:** Xóa bỏ token hardcode khỏi file `.bat`. Tải token từ file `.env` qua `python-dotenv`. Yêu cầu đổi mật khẩu admin và hủy/tạo lại token Hugging Face trên console Hugging Face.

---

#### [BUG-CRIT-04] Từ chối Dịch vụ Tài nguyên GPU (Unauthenticated GPU Denial of Service / Resource Exhaustion)
- **Mức độ:** **CRITICAL**
- **Vị trí file:**
  - `backend/apps/ai_engine/views.py`, Dòng 523 (`FullSongGenerateView`)
  - `backend/apps/music/views.py`, Dòng 225 (`MusicGenerateUnifiedView`)
- **Mô tả:** Cả hai endpoint tạo bài hát AI đều đặt `permission_classes = [permissions.AllowAny]`. Người dùng không cần tài khoản hoặc token xác thực vẫn có thể liên tục gửi request tạo nhạc dài (3-5 phút).
- **Nguyên nhân:** Cấu hình mở để phục vụ demo nhưng không có cơ chế giới hạn truy cập (Rate Limit) hoặc yêu cầu đăng nhập.
- **Ảnh hưởng:** Kẻ xấu có thể chạy script gửi 100 requests đồng thời, khởi chạy hàng trăm tiến trình sinh nhạc nền MusicGen/ACE-Step, làm tràn bộ nhớ VRAM, CPU 100% và sập toàn bộ backend Django.
- **Đề xuất khắc phục:** Chuyển `permission_classes = [permissions.IsAuthenticated]` cho các tác vụ tạo nhạc AI tốn tài nguyên, đồng thời bổ sung `ScopedRateThrottle` (ví dụ: tối đa 5 bài/giờ cho mỗi người dùng).

---

### 2. NHÓM LỖI HIGH (MỨC ĐỘ CAO)

#### [BUG-HIGH-01] Rò rỉ Dữ liệu Nhạy cảm (PII Data Exposure - Email công khai)
- **Mức độ:** **HIGH**
- **Vị trí file:** `backend/apps/users/serializers.py`, Dòng 18 (`UserSerializer`)
- **Mô tả:** `UserSerializer` định nghĩa trường `fields` bao gồm cả `'email'`. Serializer này được dùng trong `SongSerializer` (`artist = UserSerializer(read_only=True)`) và trong `UserListView` (`/api/auth/users/`).
- **Ảnh hưởng:** Mọi người dùng vãng lai (chưa đăng nhập) khi xem trang chủ, nghe nhạc hoặc truy cập API danh sách người dùng đều nhận được địa chỉ email riêng tư của toàn bộ nghệ sĩ và tác giả trong hệ thống.
- **Đề xuất khắc phục:** Tách `PublicUserSerializer` (chỉ gồm `id, username, first_name, last_name, avatar_url, bio, is_artist`) dùng cho các view công khai và bài hát. Chỉ giữ `email` trong `UserProfileSerializer` dành riêng cho chính chủ (`/api/auth/profile/`).

---

#### [BUG-HIGH-02] Rò rỉ Bộ nhớ RAM (Memory Leak) do Quản lý Job In-Memory Thiếu TTL
- **Mức độ:** **HIGH**
- **Vị trí file:** `backend/apps/ai_engine/views.py`, Dòng 372, Dòng 544, Dòng 652
- **Mô tả:** Biến toàn cục `_JOBS: dict = {}` lưu trữ toàn bộ trạng thái job và toàn bộ mảng nhị phân âm thanh (`audio`: mảng byte WAV/MP3 từ 5MB đến 30MB) trực tiếp trên RAM.
  - Khi người dùng không tải xuống, dữ liệu âm thanh nằm vĩnh viễn trong RAM.
  - Sau khi tải xuống, mã nguồn chỉ gán `_JOBS[job_id]['audio'] = None`, nhưng key `job_id` và metadata không bao giờ bị xóa khỏi `_JOBS`.
  - Nếu người dùng bấm nghe lại hoặc tải lại bài hát đó lần 2, hệ thống trả về lỗi `500 Không có audio` do `audio` đã bị gán `None`.
- **Ảnh hưởng:** Bộ nhớ RAM của Django process tăng trưởng không giới hạn theo thời gian (Memory Leak). Trải nghiệm người dùng bị hỏng khi cố nghe lại bài vừa tạo.
- **Đề xuất khắc phục:** Lưu file âm thanh sinh ra xuống thư mục đệm trên disk (`MEDIA_ROOT/temp_jobs/`) và chỉ lưu đường dẫn file trong job metadata. Cài đặt cơ chế tự động xóa job sau 1 giờ (TTL) bằng background cleanup thread hoặc Celery/Redis.

---

#### [BUG-HIGH-03] Job ID Ngắn, Dễ Đoán (Insecure Predictable Job Identifiers)
- **Mức độ:** **HIGH**
- **Vị trí file:** `backend/apps/ai_engine/views.py`, Dòng 542
- **Mô tả:** `job_id = str(uuid.uuid4())[:8]` — Mã định danh job chỉ lấy 8 ký tự hex (tương đương 32-bit entropy).
- **Ảnh hưởng:** Không gian tìm kiếm chỉ có $16^8 \approx 4.29 \times 10^9$ khả năng. Kẻ tấn công có thể brute-force quét mã job đang chạy của người dùng khác, theo dõi tiến trình và tải lén bài hát trước khi chủ nhân kịp lưu.
- **Đề xuất khắc phục:** Giữ nguyên UUID4 đầy đủ (`uuid.uuid4().hex`, 128-bit entropy) và lưu `user_id` sở hữu job vào dictionary để kiểm tra quyền truy cập.

---

#### [BUG-HIGH-04] Vấn đề N+1 Query Multiplier trên API Bài hát & Nghệ sĩ
- **Mức độ:** **HIGH**
- **Vị trí file:**
  - `backend/apps/users/models.py`, Dòng 20 – 25 (`followers_count`, `following_count`)
  - `backend/apps/users/serializers.py`, Dòng 7 – 9, 36 – 40 (`is_following`)
  - `backend/apps/music/models.py`, Dòng 48 – 49 (`likes_count`)
  - `backend/apps/music/serializers.py`, Dòng 9 – 10, 30 – 34 (`is_liked`)
- **Mô tả:** Các thuộc tính đếm số lượt thích, số người theo dõi, và trạng thái đã theo dõi/đã thích được cài đặt dưới dạng method gọi trực tiếp câu lệnh truy vấn DB riêng lẻ cho từng bản ghi.
- **Ảnh hưởng:** Khi serialize danh sách 20 bài hát trên trang khám phá hoặc trang chủ, Django thực thi **hơn 100 câu lệnh SQL truy vấn lặp đi lặp lại** (N+1 query storm), gây suy giảm nghiêm trọng tốc độ phản hồi API khi dữ liệu người dùng tăng lên.
- **Đề xuất khắc phục:** Sử dụng Django ORM Annotations (`annotate(likes_count=Count('likes'), ...)`) và `select_related('artist')` kết hợp với subquery để nạp dữ liệu một lần duy nhất.

---

### 3. NHÓM LỖI MEDIUM (MỨC ĐỘ TRUNG BÌNH)

#### [BUG-MED-01] Phân mảnh Trải nghiệm Studio (Duplication & Divergence: `CreatePage` vs `ComposePage`)
- **Mức độ:** **MEDIUM**
- **Vị trí file:** `frontend/src/pages/CreatePage.jsx` (120 KB) và `frontend/src/pages/ComposePage.jsx` (74 KB); `frontend/src/components/layout/Sidebar.jsx` (Dòng 13)
- **Mô tả:** Tồn tại hai phòng thu AI song song:
  - `CreatePage.jsx`: Phòng thu hiện đại kiểu Suno với 3 chế độ (Tạo nhanh với AI, Sáng tác từ hình ảnh Visual Synesthesia, và Custom lyrics/tags).
  - `ComposePage.jsx`: Phòng thu đời cũ với MIDI, Quick vs Full mode.
  - Trong `Sidebar.jsx`, nút menu "Phòng AI Studio" trỏ về `/compose` (`ComposePage`). Trong khi đó trên `HomePage.jsx` và `Topbar.jsx`, nút tạo nhạc lại dẫn người dùng sang `/create` (`CreatePage`).
- **Ảnh hưởng:** Người dùng bị đưa vào hai giao diện khác nhau tùy theo nút bấm; mã nguồn frontend bị phình to gần 200 KB với nhiều logic trùng lặp (SaveModal, Audio player, prompt presets).
- **Đề xuất khắc phục:** Hợp nhất hai trang thành một Studio chuẩn duy nhất (`CreatePage`), chuyển hướng route `/compose` về `/create`, và cập nhật link trong `Sidebar.jsx`.

---

#### [BUG-MED-02] Thiếu Bộ chỉ mục (Missing Database Indexes) trên các Cột Tra cứu Trọng yếu
- **Mức độ:** **MEDIUM**
- **Vị trí file:** `backend/apps/music/models.py`, `backend/apps/users/models.py`
- **Mô tả:** Kiểm tra thực tế trên cấu trúc SQLite cho thấy:
  - Bảng `songs` chỉ có duy nhất 1 index trên `artist_id`. Các cột `created_at` (sắp xếp mặc định), `is_published` (luôn lọc), `genre`, `mood`, `play_count` đều **hoàn toàn không có index**.
  - Bảng `users` không có index trên `email`.
  - Bảng `listen_history` không có index trên `listened_at`.
- **Ảnh hưởng:** Toàn bộ các thao tác lọc nhạc theo thể loại, tâm trạng, lấy bài hát thịnh hành hoặc xem danh sách bài mới đều phải quét toàn bộ bảng (Full Table Scan).
- **Đề xuất khắc phục:** Thêm `db_index=True` vào `created_at`, `is_published`, `genre`, `mood`, `play_count` trong `Song` model và tạo migration mới.

---

#### [BUG-MED-03] Khóa Bí mật Mặc định & Chế độ Debug Bật trong Cấu hình
- **Mức độ:** **MEDIUM**
- **Vị trí file:** `backend/config/settings.py` (Dòng 22 - 24) và `backend/.env`
- **Mô tả:** File cấu hình `.env` đang lưu:
  ```env
  SECRET_KEY=django-insecure-aimusic-social-secret-key-change-in-production
  DEBUG=True
  ```
- **Ảnh hưởng:** Khi có lỗi ngoại lệ 500 trên server, Django sẽ xuất toàn bộ traceback, thông tin biến môi trường và cấu hình nội bộ ra màn hình trình duyệt của người dùng.
- **Đề xuất khắc phục:** Tạo script tự sinh ngẫu nhiên `SECRET_KEY` bằng `secrets.token_urlsafe(50)`, và tắt `DEBUG=False` khi triển khai production.

---

#### [BUG-MED-04] Thuật toán Recommendation Chạy Vòng lặp Ngoại vi Tuần tự (Performance Bottleneck)
- **Mức độ:** **MEDIUM**
- **Vị trí file:** `backend/apps/ai_engine/recommender.py`, Dòng 78 – 80
- **Mô tả:** Hàm `get_content_based_recommendations` duyệt qua mảng `candidates` và gọi `get_song_neural_vector(s)` cho từng bài hát một. Hàm này cố gắng gọi HTTP API của Google Gemini để lấy embedding 3072 chiều mà không có cơ chế lưu vector vào database (`Song.embedding`).
- **Ảnh hưởng:** Nếu danh sách có 50 bài hát, hệ thống sẽ thực hiện 50 cuộc gọi mạng liên tiếp ra Google API trong 1 request của client, dẫn đến độ trễ lên tới 10 - 20 giây hoặc timeout nếu mạng chập chờn.
- **Đề xuất khắc phục:** Bổ sung trường `embedding = models.BinaryField(null=True)` vào model `Song`. Chỉ sinh vector khi bài hát được tạo/lưu, sau đó dùng trực tiếp vector có sẵn trong DB để tính cosine similarity.

---

#### [BUG-MED-05] Nguy cơ Tranh chấp Tài nguyên (Thread Safety) trên Audio Cache & Model Loading
- **Mức độ:** **MEDIUM**
- **Vị trí file:** `backend/apps/ai_engine/music_generator.py`, Dòng 33 – 53, Dòng 72 – 100
- **Mô tả:** Cấu trúc `_audio_cache = OrderedDict()` và hàm `load_model()` được dùng chung bởi nhiều request/thread nhưng không được bảo vệ bằng `threading.Lock`.
- **Ảnh hưởng:** Trong môi trường WSGI đa luồng, hai request gọi `load_model` đồng thời có thể gây lỗi nạp đè mô hình vào GPU, hoặc `_cache_set` có thể gây lỗi `KeyError` bên trong OrderedDict khi thao tác đồng thời.
- **Đề xuất khắc phục:** Bổ sung `_cache_lock = threading.Lock()` bao bọc các thao tác trên `_audio_cache` và khởi tạo mô hình một lần duy nhất lúc server startup.

---

### 4. NHÓM LỖI LOW / INFO (MÃ NGUỒN & HẠ TẦNG)

#### [BUG-LOW-01] Thiếu File `.gitignore` ở Thư mục Gốc
- **Mức độ:** **LOW**
- **Mô tả:** Thư mục gốc dự án không có file `.gitignore`. Chỉ có 1 file `.gitignore` nằm sâu trong `backend/venv/`.
- **Ảnh hưởng:** Dễ dẫn đến việc commit nhầm thư mục nhị phân `venv/`, `node_modules/`, file SQLite database `db.sqlite3` và file nhạy cảm `.env` lên GitHub/GitLab.
- **Đề xuất:** Tạo ngay file `.gitignore` ở thư mục gốc bỏ qua `.env`, `db.sqlite3`, `media/`, `node_modules/`, `venv/`, `__pycache__/`, `dist/`.

#### [BUG-LOW-02] Dependencies Thừa & Chưa Dọn dẹp trong `requirements.txt`
- **Mức độ:** **LOW**
- **Mô tả:** File `backend/requirements.txt` vẫn còn dòng `suno-bark>=0.1.5` dù dự án đã hoàn thành Phase 2.2A loại bỏ Bark an toàn.
- **Đề xuất:** Xóa bỏ `suno-bark` khỏi `requirements.txt` để giảm dung lượng cài đặt.

#### [BUG-LOW-03] Thiếu Bộ Kiểm thử Tích hợp Chuẩn Django cho các App Cốt lõi
- **Mức độ:** **INFO / QA**
- **Mô tả:** Lệnh `python manage.py test apps` chỉ tìm thấy duy nhất 1 test case trong `apps/ai_engine/test_phonetic.py`. Các app `apps.users`, `apps.music`, `apps.social` không có file `tests.py` theo quy chuẩn Django. Toàn bộ test hiện tại được viết dưới dạng các script độc lập ở thư mục gốc `backend/`.
- **Đề xuất:** Đóng gói các script test thành các TestCase chuẩn trong thư mục `apps/<app_name>/tests/` để CI/CD có thể tự động chạy qua lệnh chuẩn.

---

## PHẦN D: PHÂN TÍCH NỢ KỸ THUẬT (TECHNICAL DEBT)

### 1. Code Duplication (Trùng lặp mã nguồn)
- **Giao diện Tạo nhạc:** `frontend/src/pages/CreatePage.jsx` (2,298 dòng) và `frontend/src/pages/ComposePage.jsx` (1,523 dòng) lặp lại hơn 40% mã nguồn về: danh sách Moods, Genres, Tempos, Instruments, form điều khiển âm lượng, logic gọi API `/api/music/generate/` và `/api/ai/generate/full/`, và modal lưu bài hát.
- **Audio Decoding & Normalization:** Logic xử lý byte âm thanh (kiểm tra header RIFF WAV vs ID3 MP3) lặp lại ở 4 nơi: `ai_engine/views.py`, `music/media_views.py`, `ai_engine/audio_mixer.py`, và `ai_engine/audio_mastering.py`. Nên được gom vào `apps/ai_engine/audio_utils.py`.

### 2. Dead Code & Thư viện Không Sử dụng
- `backend/apps/ai_engine/bark_singer.py`: Đã được cô lập an toàn bằng Hard Guard từ chối gọi cho tiếng Việt, nhưng file vẫn tồn tại 10,218 bytes.
- Một số test script cũ không còn phù hợp với Phase 2: `test_quick.py`, `test_gen.py`, `test_engine_v2.py`.
- Package `suno-bark` cài đặt trong `venv` chiếm dụng bộ nhớ disk không cần thiết.

### 3. Architectural Smells (Dấu hiệu kiến trúc chưa tối ưu)
- **Kiến trúc Background Job không bền vững:** Việc quản lý job tạo nhạc nền bằng `threading.Thread` và dictionary `_JOBS` trong bộ nhớ RAM của tiến trình Django là giải pháp tạm thời (prototype-level). Nếu tiến trình Django khởi động lại (restart/crash), toàn bộ các job đang sinh nhạc bị hủy và người dùng mất toàn bộ kết quả.
- **Chưa có Queue phân tải GPU:** Nếu 3 người dùng cùng tạo nhạc, 3 background thread sẽ tranh chấp VRAM trên GPU RTX 3050 cùng lúc, gây lỗi CUDA Out Of Memory (OOM).

---

## PHẦN E: BÁO CÁO KIỂM THỬ THỰC TẾ (TEST EXECUTION REPORT)

Đội ngũ kiểm toán đã thực thi trực tiếp toàn bộ các bộ kiểm thử tự động trên môi trường máy chủ thực tế (NVIDIA GeForce RTX 3050 Laptop GPU, Python 3.13.9, PyTorch 2.6.0+cu124, Vite 4.5.0). Kết quả cụ thể:

```
========================================================================================================
SONAVIA AI — BẢNG TỔNG HỢP KIỂM THỬ HỆ THỐNG THỰC TẾ
========================================================================================================
STT | Lệnh Kiểm thử / Test Suite                     | Loại kiểm thử        | Total | PASS | FAIL | SKIP
----+------------------------------------------------+----------------------+-------+------+------+-----
 1  | test_vietnamese_phonetics.py                   | Phonetics Unit Test  |   21  |  21  |   0  |   0
 2  | test_phase2_2a_remove_bark.py                  | Bark Removal Safety  |    8  |   8  |   0  |   0
 3  | test_phase2_2b_svs_provider.py                 | SVS Provider Contract|    8  |   8  |   0  |   0
 4  | test_phase2_3_intelligent_orchestrator.py      | 4-Tier Orchestration |    5  |   5  |   0  |   0
 5  | test_vietnamese_ai_singing_and_audio.py        | 11 Audio Categories  |   11  |  11  |   0  |   0
 6  | test_audio_mastering.py                        | DSP Mastering Filter |    4  |   4  |   0  |   0
 7  | test_llm_mock.py                               | LLM Mock Fallback    |    2  |   2  |   0  |   0
 8  | test_lyric_engine.py                           | 5-Language Lyrics Gen|    5  |   5  |   0  |   0
 9  | python manage.py test apps                     | Django App Test      |    1  |   1  |   0  |   0
 10 | npm run build (Frontend Vite Production)       | Frontend Build       |    1  |   1  |   0  |   0
----+------------------------------------------------+----------------------+-------+------+------+-----
    | TỔNG CỘNG KIỂM THỬ                             |                      |   66  |  66  |   0  |   0
========================================================================================================
TỶ LỆ VƯỢT QUA (TEST PASS RATE): 100% (66/66 HẠNG MỤC PASS)
```

### Chi tiết các hạng mục kiểm thử âm thanh & DSP (`test_vietnamese_ai_singing_and_audio.py`):
1. **Input Prompt & Language Detection:** PASS (Nhận diện chính xác Tiếng Việt, V-Pop, Female).
2. **Text Normalization & Dấu thanh (Unicode NFC):** PASS (Bảo toàn 38 ký tự có dấu, lọc ký hiệu âm nhạc).
3. **Phân đoạn câu theo nhịp điệu tiếng Việt:** PASS (9 phân đoạn, 4 - 6 từ/câu).
4. **Vocal Pronunciation Guidance:** PASS (Guidance Scale 1.8 - 2.2 chuẩn phòng thu).
5. **Singing Chunk Crossfade:** PASS (Biên độ zero-crossing, loại bỏ tiếng nổ/click/pop).
6. **Melody Timing & Alignment:** PASS (Bảo toàn độ dài bản phối 8.0s, khớp giai điệu).
7. **Vocal Phrasing Prompt Conditioning:** PASS (Caption dài 807 ký tự kèm chỉ dẫn ngữ âm biểu cảm).
8. **Instrumental Generation (Harmonic Synth Stereo):** PASS (WAV 44.1kHz Stereo 2 kênh).
9. **Audio Mixing (Bảo tồn Stereo & Headroom):** PASS (Stereo 100%, Peak 0.8910 <= 0.895 an toàn).
10. **Audio Mastering (DSP Low-Cut & Limiter):** PASS (Target 0.891, Actual Peak 0.8910, không méo tiếng).
11. **Export & Streaming Playback (RFC 7233):** PASS (MIME audio/wav, HTTP 206 Partial Content).

---

## PHẦN F: DANH SÁCH ƯU TIÊN SỬA LỖI (PRIORITY ROADMAP P0 - P3)

Để đưa hệ thống Sonavia AI từ trạng thái hiện tại tiến tới sản phẩm hoàn thiện sẵn sàng vận hành thực tế, lộ trình sửa lỗi được phân bổ theo 4 mức ưu tiên nghiêm ngặt:

```mermaid
flowchart LR
    P0["P0: Sửa Khẩn cấp (Hotfix)<br/>Bảo mật & IDOR & Path Traversal"] --> P1["P1: Ổn định Tính năng Chính<br/>Hợp nhất UI Studio & Auth Quota"]
    P1 --> P2["P2: Tối ưu Trải nghiệm & Hiệu năng<br/>DB Index & Celery/Redis & Embedding Cache"]
    P2 --> P3["P3: Hoàn thiện SVS Tiếng Việt<br/>Local Checkpoint Training & Dockerize"]
```

### ƯU TIÊN P0: SỬA KHẨN CẤP NGAY LẬP TỨC (BẢO MẬT & TOÀN VẸN HỆ THỐNG)
1. **[P0-1] Vá lỗ hổng Path Traversal trong `SaveAiSongView`**: Thêm kiểm tra `os.path.realpath` đảm bảo không thể đọc file ngoài `MEDIA_ROOT`.
2. **[P0-2] Khắc phục lỗ hổng IDOR/BOLA trên Bài hát & Playlist**: Cài đặt quyền tác giả `IsOwnerOrReadOnly` trên `SongDetailView` và `PlaylistDetailView`.
3. **[P0-3] Loại bỏ Hardcode HuggingFace Token & Mật khẩu mặc định**: Xóa token khỏi `start_backend.bat`, nạp qua biến môi trường an toàn.
4. **[P0-4] Đóng quyền endpoint tạo nhạc AI**: Chuyển `permission_classes = [permissions.IsAuthenticated]` và thêm Rate Limit trên các API sinh nhạc.
5. **[P0-5] Khắc phục rò rỉ Email**: Tách `PublicUserSerializer` để ẩn trường `email` khỏi các API công khai và bài hát.

### ƯU TIÊN P1: ỔN ĐỊNH CHỨC NĂNG CHÍNH (CORE FUNCTIONALITY & UI)
1. **[P1-1] Hợp nhất Giao diện Studio**: Lấy `CreatePage.jsx` làm chuẩn chính, đồng bộ điều hướng trong `Sidebar.jsx`, đóng chuyển hướng route `/compose` sang `/create`.
2. **[P1-2] Khắc phục Memory Leak & Lỗi tải lại bài hát**: Chuyển việc lưu trữ audio từ RAM trong `_JOBS` sang file đệm trên disk (`MEDIA_ROOT/temp_jobs/`) và sinh UUID đầy đủ 32 hex.
3. **[P1-3] Tạo file `.gitignore` chuẩn ở thư mục gốc**: Tránh nguy cơ commit lộ dữ liệu nhạy cảm.

### ƯU TIÊN P2: TỐI ƯU HIỆU NĂNG & TRẢI NGHIỆM NGƯỜI DÙNG (PERFORMANCE & QUALITY)
1. **[P2-1] Đánh chỉ mục Database (DB Indexing)**: Thêm index cho `Song (created_at, is_published, genre, mood, play_count)`, `User (email)`, `ListenHistory (listened_at)`.
2. **[P2-2] Giải quyết N+1 Query Multiplier**: Tối ưu hóa `SongSerializer` và `UserSerializer` bằng Django ORM `annotate` và `select_related`.
3. **[P2-3] Lưu Cache Embedding cho Recommendation Engine**: Thêm trường `embedding` vào model `Song` để không phải gọi Google Gemini API lặp đi lặp lại.
4. **[P2-4] Đồng bộ Thread-safety**: Thêm khóa luồng `threading.Lock` cho `_audio_cache` trong `music_generator.py`.

### ƯU TIÊN P3: NÂNG CẤP DÀI HẠN & VẬN HÀNH (INFRASTRUCTURE & ADVANCED SVS)
1. **[P3-1] Chuyển đổi Background Job sang Celery + Redis**: Tách biệt luồng sinh AI ra worker độc lập, hỗ trợ hàng đợi (queue) ngăn quá tải VRAM GPU.
2. **[P3-2] Tích hợp Checkpoint SVS Tiếng Việt cục bộ (DiffSinger/ViSVS)**: Thu thập voicebank tiếng Việt bản quyền và huấn luyện checkpoint riêng để chạy SVS offline hoàn toàn.
3. **[P3-3] Container hóa toàn bộ hệ thống bằng Docker & Docker-Compose**: Chuẩn hóa môi trường chạy backend, frontend, redis và GPU worker.

---

## PHẦN G: KẾT LUẬN THỰC TẾ & KHUYẾN NGHỊ

### 1. Đánh giá Mức độ Sẵn sàng (Readiness Level)

| Cấp độ Đánh giá | Trạng thái | Đánh giá Chi tiết từ Đội ngũ Kiểm toán |
| :--- | :---: | :--- |
| **Development Ready (Môi trường Phát triển)** | **READY (100%)** | Dự án có đầy đủ mã nguồn backend, frontend, bộ kiểm thử phong phú, môi trường Python + PyTorch CUDA hoạt động trơn tru. |
| **Demo Ready (Trình diễn Nội bộ)** | **READY (90%)** | Giao diện đẹp mắt, tạo nhạc Melodic Lead mượt mà, phát nhạc chất lượng cao, chatbot thông minh, phân tích ảnh sang nhạc độc đáo. |
| **Beta Tester Ready (Thử nghiệm Người dùng)** | **CONDITIONAL (60%)** | Cần xử lý xong các lỗi P0 (IDOR, Path Traversal, chặn DoS tạo nhạc) và hợp nhất giao diện CreatePage trước khi mở cho người ngoài test. |
| **Production Ready (Vận hành Thực tế)** | **NOT READY (35%)** | Chưa sẵn sàng thương mại do đang dùng SQLite, chạy Django development server (`runserver`), job lưu RAM thiếu Celery/Redis, và thiếu chứng chỉ bảo mật. |

### 2. Định vị Bản chất Sản phẩm: Real AI Music System hay Prototype?
Dự án Sonavia AI hiện tại **không còn là một bản prototype sơ sài**, mà đã định hình thành một **Hệ thống AI Music & Mạng Xã Hội Âm Nhạc Bán Chuyên Nghiệp (Advanced Semi-Production AI Platform)**:
- **Điểm mạnh vượt trội:** Đã có nền tảng DSP Audio Mastering đạt chuẩn phòng thu (-1.0 dBFS True-Peak, Biquad Filter); có lớp phân tích ngữ âm tiếng Việt chi tiết (6 thanh điệu, cấu trúc âm tiết); hệ thống điều phối 4 tuyến thông minh; loại bỏ hoàn toàn việc dùng Bark giả lập vụng về; hỗ trợ phát nhạc streaming HTTP 206 chuẩn RFC.
- **Giới hạn cốt lõi:** Tuyến tạo giọng hát tiếng Việt (SVS) hiện phụ thuộc vào ACE-Step trên Hugging Face Cloud. Khi chạy offline nội bộ, hệ thống chuyển sang chế độ Nhạc nền có Giai điệu dẫn dắt (Melodic Lead) thay vì có giọng ca sĩ AI tiếng Việt thật sự do cộng đồng nguồn mở hiện tại chưa có sẵn checkpoint voicebank tiếng Việt chuẩn.
- **Kết luận:** Dự án sở hữu kiến trúc nền tảng rất vững chắc. Sau khi hoàn thành các hạng mục Hotfix P0 và Tối ưu P1, Sonavia AI sẽ hoàn toàn sẵn sàng bước vào giai đoạn Thử nghiệm Beta mở rộng!

---
*Báo cáo được lập dựa trên việc phân tích mã nguồn thực tế và kiểm thử độc lập 66/66 ca kiểm thử trên repository Sonavia AI.*
