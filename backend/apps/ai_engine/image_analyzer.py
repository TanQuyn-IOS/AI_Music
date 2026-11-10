"""
Sonavia Studio — Image to Music AI Analyzer (Synesthesia Engine)
================================================================
Phân tích hình ảnh thành cảm xúc, màu sắc, không gian thẩm mỹ và chuyển hóa thành âm nhạc:
- Trích xuất màu sắc chủ đạo, bảng màu (Palette), độ sáng (Luminance), độ bão hòa (Saturation), nhiệt độ màu (Warmth).
- Phân tích độ tương phản và kết cấu đường nét (Texture/Dynamics).
- Suy luận không gian (Atmosphere), thể loại âm nhạc (Genre), tâm trạng (Mood), nhịp điệu (BPM), điệu thức (Key).
- Tự động sáng tác Prompt âm nhạc giàu tính biểu cảm và gợi ý lời bài hát phù hợp với bức ảnh.
"""

import os
import re
import uuid
import math
import logging
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageStat, ImageOps

logger = logging.getLogger(__name__)


class ImageToMusicAnalyzer:
    """Bộ phân tích thị giác và chuyển hóa hình ảnh thành cấu hình âm nhạc Sonavia."""

    @classmethod
    def analyze_image(cls, image_input, save_dir: str = None, language: str = "auto") -> Dict[str, Any]:
        """
        Nhận vào đường dẫn file, file object hoặc PIL.Image và trả về phân tích âm nhạc chi tiết.
        """
        if isinstance(image_input, (str, bytes, os.PathLike)):
            img = Image.open(image_input)
        elif hasattr(image_input, 'read'):
            if hasattr(image_input, 'seek'):
                try:
                    image_input.seek(0)
                except Exception:
                    pass
            img = Image.open(image_input)
        else:
            img = image_input

        # Đảm bảo hệ màu RGB an toàn, bảo toàn độ trong suốt nếu có
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[3])
            img_rgb = bg
        else:
            img_rgb = img.convert('RGB')

        # ── 1. Lưu bản sao ảnh vào media nếu có save_dir ──
        image_url = ""
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            file_name = f"vp_{uuid.uuid4().hex[:12]}.jpg"
            target_path = os.path.join(save_dir, file_name)
            # Lưu ảnh kích thước hợp lý cho cover web
            save_img = img_rgb.copy()
            save_img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            save_img.save(target_path, "JPEG", quality=90)
            image_url = f"/media/visual_prompts/{file_name}"

        # ── 2. Resize nhỏ để tính toán cực nhanh ──
        thumb = img_rgb.resize((120, 120), Image.Resampling.BILINEAR)
        pixels = list(thumb.getdata())
        total_pixels = len(pixels)

        # Tính toán thông số màu RGB & HSV
        r_total, g_total, b_total = 0, 0, 0
        hues = []
        saturations = []
        brightnesses = []

        # Color bins
        color_bins = {
            "red": 0, "orange": 0, "yellow": 0, "green": 0,
            "cyan": 0, "blue": 0, "purple": 0, "pink": 0, "gray": 0
        }

        for r, g, b in pixels:
            r_total += r
            g_total += g
            b_total += b

            # RGB -> HSV
            r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
            c_max = max(r_norm, g_norm, b_norm)
            c_min = min(r_norm, g_norm, b_norm)
            delta = c_max - c_min

            # Hue
            if delta == 0:
                h = 0
            elif c_max == r_norm:
                h = (60 * ((g_norm - b_norm) / delta) + 360) % 360
            elif c_max == g_norm:
                h = (60 * ((b_norm - r_norm) / delta) + 120) % 360
            else:
                h = (60 * ((r_norm - g_norm) / delta) + 240) % 360

            s = 0 if c_max == 0 else (delta / c_max)
            v = c_max

            hues.append(h)
            saturations.append(s)
            brightnesses.append(v)

            # Phân loại màu
            if s < 0.15 or v < 0.15:
                color_bins["gray"] += 1
            elif (h >= 345 or h < 15):
                color_bins["red"] += 1
            elif 15 <= h < 45:
                color_bins["orange"] += 1
            elif 45 <= h < 70:
                color_bins["yellow"] += 1
            elif 70 <= h < 165:
                color_bins["green"] += 1
            elif 165 <= h < 200:
                color_bins["cyan"] += 1
            elif 200 <= h < 260:
                color_bins["blue"] += 1
            elif 260 <= h < 315:
                color_bins["purple"] += 1
            else:
                color_bins["pink"] += 1

        avg_r = r_total / total_pixels
        avg_g = g_total / total_pixels
        avg_b = b_total / total_pixels

        avg_sat = sum(saturations) / total_pixels
        avg_val = sum(brightnesses) / total_pixels

        # Tính nhiệt độ màu (Warm vs Cool)
        # R + 0.5G vs B + 0.5G
        warmth_score = (avg_r - avg_b) / 255.0  # -1.0 (very cool) to +1.0 (very warm)

        # Trích xuất bảng màu đại diện (Palette 5 màu)
        quantized = thumb.quantize(colors=5, method=Image.Quantize.FASTOCTREE)
        palette_raw = quantized.getpalette()[:15]
        palette_hex = []
        for i in range(0, len(palette_raw), 3):
            pr, pg, pb = palette_raw[i], palette_raw[i+1], palette_raw[i+2]
            palette_hex.append(f"#{pr:02x}{pg:02x}{pb:02x}")

        # Tìm màu chiếm ưu thế nhất (loại trừ màu xám nếu có màu rực rỡ)
        sorted_colors = sorted(
            [(k, v) for k, v in color_bins.items() if k != "gray"],
            key=lambda x: x[1],
            reverse=True
        )
        dominant_color = sorted_colors[0][0] if sorted_colors and sorted_colors[0][1] > 0.05 * total_pixels else "neutral"

        # ── 3. Thử phân tích bằng Multimodal Vision AI thật sự (Google Gemini / OpenAI Vision) ──
        try:
            from .llm_service import is_llm_available, analyze_image_with_vision_llm, get_active_provider
            if is_llm_available():
                import io
                bio = io.BytesIO()
                # Kích thước tối ưu cho AI nhận diện sắc nét và truyền tải nhanh (~800px)
                vision_img = img_rgb.copy()
                vision_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                vision_img.save(bio, format="JPEG", quality=85)
                raw_bytes = bio.getvalue()

                vision_data = analyze_image_with_vision_llm(raw_bytes, mime_type="image/jpeg", language=language)
                if vision_data and (vision_data.get("title") or vision_data.get("lyrics")):
                    provider_name, _ = get_active_provider()
                    engine_name = "Google Gemini Vision" if provider_name == "gemini" else "OpenAI GPT-4o Vision"

                    title = str(vision_data.get("title", "Khúc Ca Từ Bức Ảnh")).strip()
                    lyrics = str(vision_data.get("lyrics", "")).strip()
                    prompt_ai = str(vision_data.get("prompt", "")).strip()
                    genre = str(vision_data.get("genre", "vpop")).strip().lower()
                    genre_name = str(vision_data.get("genre_name", "V-Pop Ballad")).strip()
                    mood = str(vision_data.get("mood", "calm")).strip().lower()
                    mood_name = str(vision_data.get("mood_name", "Bình yên")).strip()
                    atmosphere = str(vision_data.get("atmosphere", "")).strip()
                    vocal = str(vision_data.get("vocal", "female")).strip()
                    key = str(vision_data.get("key", "C Major")).strip()

                    # Parse BPM an toàn
                    raw_bpm = vision_data.get("bpm", 85)
                    try:
                        bpm = int(re.search(r'\d+', str(raw_bpm)).group(0))
                    except Exception:
                        bpm = 85

                    # Parse visual_tags an toàn
                    raw_tags = vision_data.get("visual_tags", ["#SonaviaAI", "#MusicFromImage"])
                    if isinstance(raw_tags, str):
                        visual_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                    elif isinstance(raw_tags, list):
                        visual_tags = [str(t) for t in raw_tags]
                    else:
                        visual_tags = ["#SonaviaAI", "#MusicFromImage"]

                    chosen_lang = (language or "auto").strip().lower()
                    resolved_lang = chosen_lang if chosen_lang != "auto" else ("vi" if any(c in lyrics for c in 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ') else "vi")

                    logger.info(f"[ImageAnalyzer] {engine_name} phân tích thành công: '{title}' ({resolved_lang})")
                    return {
                        "success": True,
                        "scene": genre,
                        "title": title,
                        "prompt": prompt_ai,
                        "genre": genre,
                        "genre_name": genre_name,
                        "mood": mood,
                        "mood_name": mood_name,
                        "bpm": bpm,
                        "key": key,
                        "vocal": vocal,
                        "language": resolved_lang,
                        "atmosphere": atmosphere or f"Không gian âm nhạc được truyền cảm hứng từ màu sắc và đường nét của bức ảnh.",
                        "visual_tags": visual_tags,
                        "lyrics": lyrics,
                        "image_url": image_url,
                        "cover_image_url": image_url,
                        "palette": palette_hex,
                        "visual_metrics": {
                            "palette": palette_hex,
                            "brightness": round(avg_val, 2),
                            "saturation": round(avg_sat, 2),
                            "warmth": "warm" if warmth_score > 0.1 else "cool" if warmth_score < -0.1 else "neutral",
                            "dominant_color": dominant_color,
                        },
                        "is_real_ai": True,
                        "ai_engine": engine_name,
                    }
        except Exception as vision_err:
            logger.warning(f"[ImageAnalyzer] Vision AI tạm thời gián đoạn ({vision_err}), fallback sang phân tích quang học:")

        # ── 4. Dự phòng: Phán đoán bối cảnh quang học & ánh xạ mẫu (Heuristic Fallback) ──
        scene_type = cls._infer_scene(avg_val, avg_sat, warmth_score, dominant_color)
        music_profile = cls._map_scene_to_music(scene_type, avg_val, avg_sat, warmth_score, dominant_color)

        title = music_profile["title"]
        lyrics = music_profile["lyrics"]
        lang_choice = (language or "auto").strip().lower()

        if lang_choice in ("ko", "ja", "zh", "en"):
            try:
                from .lyric_engine import generate_multilingual_lyrics
                multi_res = generate_multilingual_lyrics(
                    language=lang_choice,
                    theme=music_profile.get("mood", "calm"),
                    genre=music_profile.get("genre", "pop"),
                    vocal_gender=music_profile.get("vocal", "female"),
                    user_prompt=title,
                )
                if multi_res.get("lyrics"):
                    lyrics = multi_res["lyrics"]
                    title = multi_res.get("title", title)
            except Exception as lyr_err:
                logger.warning(f"[ImageAnalyzer] Fallback multilingual lyrics failed: {lyr_err}")

        return {
            "success": True,
            "scene": scene_type,
            "title": title,
            "prompt": music_profile["prompt"],
            "genre": music_profile["genre"],
            "genre_name": music_profile["genre_name"],
            "mood": music_profile["mood"],
            "mood_name": music_profile["mood_name"],
            "bpm": music_profile["bpm"],
            "key": music_profile["key"],
            "vocal": music_profile["vocal"],
            "language": lang_choice if lang_choice != "auto" else "vi",
            "atmosphere": music_profile["atmosphere"],
            "visual_tags": music_profile["visual_tags"],
            "lyrics": lyrics,
            "image_url": image_url,
            "cover_image_url": image_url,
            "palette": palette_hex,
            "visual_metrics": {
                "palette": palette_hex,
                "brightness": round(avg_val, 2),
                "saturation": round(avg_sat, 2),
                "warmth": "warm" if warmth_score > 0.1 else "cool" if warmth_score < -0.1 else "neutral",
                "dominant_color": dominant_color,
            },
            "is_real_ai": False,
            "ai_engine": "Heuristic Color Optics",
        }

    @classmethod
    def _infer_scene(cls, brightness: float, saturation: float, warmth: float, dominant_color: str) -> str:
        """Nhận diện bối cảnh/tâm trạng bức ảnh từ các chỉ số thị giác."""
        # Đêm tối hoặc huyền ảo
        if brightness < 0.32:
            if dominant_color in ["purple", "pink", "cyan"]:
                return "neon_cyber_night"      # Thành phố đêm neon / Cyberpunk
            elif dominant_color in ["blue", "neutral"]:
                return "deep_midnight_lonely"   # Đêm khuya cô đơn / Trăng sao
            else:
                return "dark_mystic"           # Bí ẩn / Trầm lắng

        # Hoàng hôn hoặc chiều tà (ấm áp, cam, hồng, đỏ)
        if warmth > 0.15 and dominant_color in ["orange", "red", "yellow", "pink"]:
            return "golden_sunset_romantic"     # Hoàng hôn vàng lãng mạn / Chiều tà

        # Bình minh hoặc sáng tươi tắn rạng ngời
        if brightness > 0.65 and saturation > 0.40 and dominant_color in ["yellow", "orange", "pink"]:
            return "bright_sunny_cheerful"      # Ngày nắng rực rỡ / Năng lượng tuổi trẻ

        # Thiên nhiên, cây cỏ, núi rừng
        if dominant_color == "green":
            return "nature_forest_peaceful"     # Rừng xanh / Bình yên thiên nhiên

        # Biển cả hoặc bầu trời trong xanh
        if dominant_color in ["blue", "cyan"] and brightness >= 0.4:
            return "ocean_blue_sky_freedom"     # Biển xanh / Bầu trời bao la / Tự do

        # Mưa hoặc mờ sương, u buồn (độ bão hòa màu thấp, xám hoặc nhạt)
        if saturation < 0.22:
            if brightness < 0.5:
                return "rainy_melancholic_room" # Mưa buồn hoài niệm / Kỷ niệm cũ
            else:
                return "minimal_soft_morning"   # Sương sớm dịu êm / Nhẹ nhàng

        # Năng động, màu sắc tương phản cao
        if saturation > 0.6:
            return "vibrant_festival_energy"    # Lễ hội sôi động / Sắc màu bùng nổ

        # Mặc định: Bình yên thư thái
        return "calm_warm_intimate"

    @classmethod
    def _map_scene_to_music(
        cls, scene: str, brightness: float, saturation: float, warmth: float, dominant_color: str
    ) -> Dict[str, Any]:
        """Quy đổi bối cảnh thị giác sang thông số âm nhạc chuẩn Sonavia."""

        if scene == "golden_sunset_romantic":
            return {
                "title": "Ánh Hoàng Hôn Chiều Tà",
                "genre": "vpop",
                "genre_name": "V-Pop Ballad",
                "mood": "romantic",
                "mood_name": "Lãng mạn & Hoài niệm",
                "bpm": 76,
                "key": "G Major",
                "vocal": "female",
                "atmosphere": "Ánh hoàng hôn rực rỡ buông xuống, không gian ấm áp ngập tràn yêu thương và nỗi nhớ da diết.",
                "visual_tags": ["#HoàngHôn", "#LãngMạn", "#ẤmÁp", "#VPopBallad", "#Piano"],
                "prompt": (
                    "Bản V-Pop Pop Ballad lãng mạn sâu lắng, giai điệu piano ấm áp hòa cùng tiếng violin da diết, "
                    "không khí hoàng hôn bình yên ngập tràn tình cảm, giọng hát nữ trong trẻo truyền cảm, studio recording"
                ),
                "lyrics": (
                    "[Intro]\n"
                    "Gió khẽ lay qua từng giọt nắng phai...\n\n"
                    "[Verse 1]\n"
                    "Chiều hoàng hôn buông nhuộm vàng góc phố quen\n"
                    "Bóng ai ngang qua mang theo bao êm đềm\n"
                    "Từng ánh mắt nụ cười còn vương vấn mãi\n"
                    "Dẫu thời gian trôi lòng này chẳng nhạt phai.\n\n"
                    "[Chorus]\n"
                    "Gửi vào mây ngàn muôn lời yêu thương ấy\n"
                    "Gửi trọn chân tình theo gió bay về nơi người\n"
                    "Dù cho sóng gió muôn trùng đường xa cách\n"
                    "Chỉ cần bên nhau, tim này mãi bình yên."
                )
            }

        elif scene == "neon_cyber_night":
            return {
                "title": "Đêm Neon Rực Sáng",
                "genre": "electronic",
                "genre_name": "Synthwave / EDM",
                "mood": "energetic",
                "mood_name": "Huyền ảo & Sôi động",
                "bpm": 126,
                "key": "A Minor",
                "vocal": "female",
                "atmosphere": "Ánh đèn neon tím hồng huyền ảo trong đêm đô thị hiện đại, nhịp điệu bassline lôi cuốn.",
                "visual_tags": ["#Cyberpunk", "#NeonNight", "#Synthwave", "#EDM", "#MidnightDrive"],
                "prompt": (
                    "Synthwave 80s retro electronic dance, pulsing analog bassline, neon synth lead, "
                    "dreamy night drive atmosphere, upbeat punchy drums, modern futuristic mix, high energy"
                ),
                "lyrics": (
                    "[Intro]\n"
                    "Ánh đèn thành phố rực sáng màn đêm...\n\n"
                    "[Verse 1]\n"
                    "Băng qua đại lộ ánh đèn neon sáng soi\n"
                    "Giai điệu rộn ràng xua tan bao chơi vơi\n"
                    "Những bước chân hòa vào đêm không ngủ\n"
                    "Thế giới này là của riêng chúng ta.\n\n"
                    "[Chorus]\n"
                    "Hát vang lên giữa bầu trời đêm lấp lánh\n"
                    "Đốt cháy đam mê cùng muôn sắc màu rạng ngời\n"
                    "Tonight we fly into the electric light\n"
                    "Bay thật xa chạm tới muôn ngàn vì sao."
                )
            }

        elif scene == "rainy_melancholic_room":
            return {
                "title": "Giai Điệu Chiều Mưa",
                "genre": "lofi",
                "genre_name": "Lo-Fi Chill / Ballad",
                "mood": "sad",
                "mood_name": "Buồn da diết & Lắng đọng",
                "bpm": 68,
                "key": "D Minor",
                "vocal": "female",
                "atmosphere": "Những giọt mưa tí tách bên khung cửa sổ mờ sương, ký ức xưa ùa về sâu lắng.",
                "visual_tags": ["#MưaRơi", "#LoFiChill", "#BuồnDaDiết", "#KỷNiệm", "#SâuLắng"],
                "prompt": (
                    "Lo-fi chill hip hop beat with melancholic emotional acoustic piano, soft rain sound in background, "
                    "mellow warm bass, gentle nostalgic vocal melody, relaxing vintage warmth, slow tempo"
                ),
                "lyrics": (
                    "[Intro]\n"
                    "Từng hạt mưa rơi lạnh buốt tâm hồn...\n\n"
                    "[Verse 1]\n"
                    "Ngồi bên ô cửa ngắm nhìn hạt mưa bay\n"
                    "Bao nhiêu kỷ niệm ùa về đong đầy\n"
                    "Tách trà ấm dần nguội theo nỗi nhớ\n"
                    "Góc quán xưa người đi chẳng trở lại.\n\n"
                    "[Chorus]\n"
                    "Mưa ơi xin đừng làm cay khóe mắt\n"
                    "Xóa đi muộn phiền trả lại những bình yên\n"
                    "Để tim ta học cách quên một người\n"
                    "Sau cơn mưa trời rồi sẽ lại sáng trong."
                )
            }

        elif scene == "ocean_blue_sky_freedom":
            return {
                "title": "Biển Xanh & Khát Vọng",
                "genre": "pop",
                "genre_name": "Modern Pop",
                "mood": "uplifting",
                "mood_name": "Phấn khởi & Tự do",
                "bpm": 118,
                "key": "C Major",
                "vocal": "male",
                "atmosphere": "Bầu trời xanh ngắt ngút ngàn, tiếng sóng biển vỗ rì rào và cảm giác tự do bất tận.",
                "visual_tags": ["#BiểnXanh", "#BầuTrời", "#TựDo", "#KhátVọng", "#UpliftingPop"],
                "prompt": (
                    "Uplifting acoustic pop, bright acoustic guitar strums, breezy ocean feel, inspiring orchestral swells, "
                    "driving drum rhythm, passionate and hopeful vocals, clear sunny horizon sound"
                ),
                "lyrics": (
                    "[Intro]\n"
                    "Mở rộng vòng tay đón gió biển khơi...\n\n"
                    "[Verse 1]\n"
                    "Trước mắt ta là biển trời bao la\n"
                    "Sóng vỗ rì rào ngân vang muôn bài ca\n"
                    "Bỏ lại sau lưng muộn phiền ngày cũ\n"
                    "Đón chào bình minh rực rỡ chân trời xa.\n\n"
                    "[Chorus]\n"
                    "Vươn đôi cánh bay về phía mặt trời\n"
                    "Khát khao tự do căng tràn trong tim tôi\n"
                    "Dẫu phía trước bao ngàn trùng bão tố\n"
                    "Ta vẫn mỉm cười vững bước trên đường đi."
                )
            }

        elif scene == "nature_forest_peaceful":
            return {
                "title": "Giai Điệu Rừng Xanh",
                "genre": "folk",
                "genre_name": "Acoustic Folk",
                "mood": "calm",
                "mood_name": "Bình yên & Thư thái",
                "bpm": 80,
                "key": "E Major",
                "vocal": "female",
                "atmosphere": "Khu rừng xanh mướt ngập tràn ánh nắng ban mai len qua kẽ lá, tiếng chim hót yên bình.",
                "visual_tags": ["#RừngXanh", "#ThiênNhiên", "#BìnhYên", "#AcousticGuitar", "#ThưGiãn"],
                "prompt": (
                    "Peaceful acoustic folk, intimate wooden guitar fingerpicking, gentle wooden flute melody, "
                    "soft strings, organic nature atmosphere, warm soothing vocals, serene forest calm"
                ),
                "lyrics": (
                    "[Intro]\n"
                    "Lắng nghe hơi thở của đất trời...\n\n"
                    "[Verse 1]\n"
                    "Nắng sớm rọi qua tán lá thông reo\n"
                    "Dòng suối trong veo lững lờ trôi êm đềm\n"
                    "Hít hà thật sâu mùi hương của cỏ dại\n"
                    "Cảm nhận sự sống ngập tràn nơi đây.\n\n"
                    "[Chorus]\n"
                    "Về lại với thiên nhiên bình dị đơn sơ\n"
                    "Để tâm hồn được tắm mát trong trẻo\n"
                    "Mỗi bước chân nâng niu từng mầm sống\n"
                    "Hạnh phúc là khi lòng ta biết an yên."
                )
            }

        elif scene == "bright_sunny_cheerful":
            return {
                "title": "Nắng Sớm Tươi Vui",
                "genre": "kpop",
                "genre_name": "K-Pop / Upbeat Pop",
                "mood": "happy",
                "mood_name": "Vui tươi & Trẻ trung",
                "bpm": 124,
                "key": "F Major",
                "vocal": "female",
                "atmosphere": "Ánh nắng vàng rực rỡ, ngập tràn nụ cười, nguồn năng lượng tích cực lan tỏa khắp nơi.",
                "visual_tags": ["#NắngSớm", "#VuiVẻ", "#KPop", "#TuổiTrẻ", "#NăngLượng"],
                "prompt": (
                    "Upbeat bright pop, cheerful brass accents, catchy synth melodies, fun bouncy bassline, "
                    "sweet and happy female vocals, high energy smile-inducing music, radio hit quality"
                ),
                "lyrics": (
                    "[Intro]\n"
                    "Một ngày mới thật tuyệt vời đã đến!\n\n"
                    "[Verse 1]\n"
                    "Mở cửa sổ đón chào nắng mai tươi vui\n"
                    "Nụ cười rạng rỡ xua tan đi ngậm ngùi\n"
                    "Bước ra phố hòa mình cùng điệu nhạc\n"
                    "Hôm nay chắc chắn sẽ là ngày tuyệt nhất.\n\n"
                    "[Chorus]\n"
                    "Hãy cùng nhảy múa dưới ánh mặt trời\n"
                    "Lan tỏa yêu thương đến khắp muôn nơi\n"
                    "Cười thật tươi vì thanh xuân tươi đẹp\n"
                    "La la la la, hạnh phúc quanh ta!"
                )
            }

        elif scene == "vibrant_festival_energy":
            return {
                "title": "Vũ Điệu Bùng Nổ",
                "genre": "electronic",
                "genre_name": "EDM / Electro Pop",
                "mood": "energetic",
                "mood_name": "Sôi động & Bốc lửa",
                "bpm": 132,
                "key": "F# Minor",
                "vocal": "duet",
                "atmosphere": "Lễ hội âm thanh và ánh sáng bùng cháy, sắc màu rực rỡ, cảm xúc thăng hoa ngút ngàn.",
                "visual_tags": ["#LễHội", "#EDMDrop", "#SôiĐộng", "#BốcLửa", "#PartyTime"],
                "prompt": (
                    "Energetic EDM dance anthem, powerful festival synth drop, heavy driving 808 kick, "
                    "dynamic buildup, hype vocal chops, party club energy, modern electronic master"
                ),
                "lyrics": (
                    "[Intro]\n"
                    "Are you ready for the beat drop?!\n\n"
                    "[Verse 1]\n"
                    "Âm bass dồn dập rung chuyển cả màn đêm\n"
                    "Muôn sắc màu hòa cùng tiếng hò reo vang\n"
                    "Chẳng còn âu lo, chẳng còn khoảng cách\n"
                    "Tất cả cháy hết mình trong từng khoảnh khắc.\n\n"
                    "[Chorus]\n"
                    "Bùng nổ đam mê cùng muôn ánh sáng\n"
                    "Nhảy múa cùng nhịp đập của con tim\n"
                    "We own the night, we light up the sky\n"
                    "Để khoảnh khắc này sống mãi trong ta!"
                )
            }

        else:  # calm_warm_intimate
            return {
                "title": "Những Giây Phút Bình Yên",
                "genre": "r&b",
                "genre_name": "R&B / Soul",
                "mood": "calm",
                "mood_name": "Ấm áp & Bình yên",
                "bpm": 84,
                "key": "Bb Major",
                "vocal": "female",
                "atmosphere": "Không gian ấm cúng, êm dịu và thân thương, giai điệu ngọt ngào xoa dịu mọi muộn phiền.",
                "visual_tags": ["#BìnhYên", "#ẤmÁp", "#RnB", "#ThưGiãn", "#NgọtNgào"],
                "prompt": (
                    "Smooth warm R&B groove, gentle Rhodes electric piano, mellow bassline, silky smooth vocal phrasing, "
                    "cozy intimate late-afternoon vibe, relaxed and heartfelt atmosphere"
                ),
                "lyrics": (
                    "[Intro]\n"
                    "Nhẹ nhàng từng nhịp đập êm ái...\n\n"
                    "[Verse 1]\n"
                    "Từng góc nhỏ thân thương trong căn nhà\n"
                    "Giai điệu dịu êm xoa dịu tháng ngày qua\n"
                    "Cần gì tìm kiếm nơi đâu xa xôi\n"
                    "Hạnh phúc giản đơn là những phút an yên này.\n\n"
                    "[Chorus]\n"
                    "Nhắm mắt lại và lắng nghe con tim\n"
                    "Để tình yêu thương vỗ về tâm hồn\n"
                    "Mỗi sớm mai thức dậy lòng không vướng bận\n"
                    "Đó là món quà tuyệt vời nhất trần gian."
                )
            }
