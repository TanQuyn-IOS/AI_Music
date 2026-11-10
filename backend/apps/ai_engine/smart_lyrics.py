"""
Smart Vietnamese Lyrics & Title Generator
=========================================
Sinh lời bài hát tiếng Việt chuẩn cấu trúc âm nhạc Suno:
- [Intro]
- [Verse 1]
- [Chorus]
- [Verse 2]
- [Chorus]
- [Bridge]
- [Outro]

Hỗ trợ đa dạng chủ đề và thể loại với vần điệu và cảm xúc chân thật.
"""

import random
import re

# ─── Kho dữ liệu chủ đề & cấu trúc lời tiếng Việt ────────────────────────────

LYRIC_THEMES = {
    "love": {
        "titles": [
            "Tình Yêu Không Lời", "Ánh Mắt Ngây Ngô", "Nơi Trái Tim Thuộc Về",
            "Bên Em Mùa Nắng Hạ", "Hẹn Ước Dưới Trăng", "Chỉ Cần Em Hạnh Phúc",
            "Giai Điệu Tình Yêu", "Nắm Chặt Tay Anh", "Một Đời Yêu Em",
        ],
        "verses_1": [
            "Từng giọt nắng khẽ rơi bên hiên nhà\nNụ cười em thắp sáng cả không gian\nBước chân qua góc phố quen ngày nào\nNgỡ như đôi ta đã thuộc về nhau từ lâu.",
            "Gió nhẹ lay khẽ vuốt mái tóc mềm\nLời thì thầm ấm áp giữa màn đêm\nÁnh mắt ai trao chan chứa bao niềm tin\nKhiến con tim anh bỗng hóa ngập ngừng.",
            "Chiều hoàng hôn buông nắng vàng dịu êm\nNhớ bờ môi ngọt ngào nhớ bàn tay mềm\nNhững phút giây bình yên bên cạnh người\nLà điều vô giá nhất cuộc đời anh.",
        ],
        "chorus": [
            "Và anh muốn hát cho em nghe khúc ca này\nGửi trọn yêu thương vào từng cơn gió bay\nDẫu cho mai sau bao sóng gió ngập tràn\nBàn tay anh vẫn luôn nắm chặt tay em.",
            "Nguyện làm ánh nắng sưởi ấm tim em mỗi ngày\nNguyện làm chiếc ô che chở giông bão qua đây\nChỉ cần nụ cười em mãi luôn rạng ngời\nTrái tim anh đã thấy cả bầu trời.",
            "Người là câu hát ngân vang mãi trong đời\nLà giấc mơ êm đềm anh luôn tìm tới\nYêu em trọn vẹn chẳng hề đổi thay\nBên nhau mãi mãi qua ngàn đắng cay.",
        ],
        "verses_2": [
            "Dù ngày mai dòng đời có xô nghiêng\nAnh vẫn đứng đây giữ trọn lời nguyền\nTừng kỷ niệm ta gom góp mỗi ngày\nSẽ là ngọn lửa ấm giữa trời đông.",
            "Mỗi sớm mai thức giấc nhìn thấy người\nLà thấy cả thế giới bừng nụ cười\nChẳng cần những thứ xa hoa lấp lánh\nChỉ cần có em bên cạnh mỗi sớm mai.",
        ],
        "bridge": [
            "Dẫu ngàn năm thời gian cứ thế trôi\nTình yêu đôi ta vẫn vẹn nguyên không phai phôi\nĐi qua ngàn bão giông để tìm thấy nhau\nGiữ lấy nhau cho đến muôn đời sau.",
        ],
        "outro": [
            "Mãi yêu em... người hỡi\nKhúc ca này trao riêng mình em.\nLa la la... yêu em mãi thôi.",
        ],
    },
    "sad": {
        "titles": [
            "Mưa Đêm Phố Vắng", "Kỷ Niệm Đã Phai", "Buông Tay Một Người",
            "Nốt Trầm Tan Vỡ", "Gió Lạnh Mùa Thu", "Tìm Lại Nụ Cười",
            "Đoạn Đường Không Nhau", "Cố Quên Một Hình Bóng", "Vết Thương Chưa Lành",
        ],
        "verses_1": [
            "Cơn mưa đêm rơi buốt giá đôi bờ vai\nTiếng thở dài rơi giữa phố dài không ai\nBóng hình em đã khuất xa chân trời\nĐể lại anh với ngổn ngang nỗi đau một đời.",
            "Ngồi trong căn phòng vắng đếm từng phút giây\nKhói thuốc tàn bay theo những đắng cay\nKỷ niệm xưa như nhát dao cứa vào tim\nBiết tìm đâu khi bóng người đã lặng im.",
            "Lá vàng rơi rụng đầy trên lối quen xưa\nBàn tay lạnh giá bước đi dưới chiều mưa\nLời hứa ngày xưa giờ hóa mây trời\nEm rời đi mang theo hết cả tiếng cười.",
        ],
        "chorus": [
            "Tại sao đôi ta phải cách xa như vậy\nĐể lại vết thương rỉ máu từng ngày\nCứ ngỡ bên nhau sẽ là mãi mãi\nNào ngờ hôm nay chỉ còn tiếng thở dài.",
            "Nước mắt rơi hòa vào cơn mưa đêm lạnh căm\nNgười đi để lại nỗi nhớ âm thầm\nBiết trách ai khi duyên phận lỡ làng\nChỉ trách lòng mình quá đỗi nặng mang.",
            "Tạm biệt người con gái anh từng yêu nhất\nKý ức hôm nay xin hóa thành tro tàn\nChúc em bình yên trên con đường mới\nPhía sau này còn riêng anh ngậm ngùi.",
        ],
        "verses_2": [
            "Đèn đường hiu hắt soi bóng đơn côi\nBước chân lạc lõng giữa biển người nổi trôi\nTự nhủ lòng phải mạnh mẽ đứng lên\nNhưng sao hình bóng ấy vẫn chưa thể quên.",
            "Góc quán quen giờ chỉ còn riêng anh\nLy cà phê đắng ngắt trong đêm lạnh\nTiếng nhạc buồn vang lên rưng rưng mắt lệ\nBiết bao giờ anh mới tìm lại nụ cười xưa.",
        ],
        "bridge": [
            "Có những nỗi đau không thể thốt nên lời\nChỉ biết ôm chặt niềm đau vào sâu lòng thôi\nNếu có kiếp sau xin đừng gặp lại\nĐể chẳng phải đau đớn như lúc này.",
        ],
        "outro": [
            "Mưa tạnh rồi... mà lòng chưa nguôi ngoai\nTạm biệt em... kỷ niệm đã phai.\nChỉ còn bóng đêm... và anh.",
        ],
    },
    "chill": {
        "titles": [
            "Phố Đêm Yên Bình", "Tách Cà Phê Ban Sáng", "Gió Mùa Lang Thang",
            "Những Ngày Bình Yên", "Gác Xép Nhỏ", "Trôi Đi Nỗi Lo",
            "Hương Cà Phê & Mưa", "Chiều Muộn Ven Hồ", "Thả Hồn Theo Gió",
        ],
        "verses_1": [
            "Bật một bản nhạc lo-fi quen thuộc\nNhìn ngoài ô cửa mưa rơi nhè nhẹ\nTách trà ấm nghi ngút khói bay\nGác lại hết bao mệt mỏi ban ngày.",
            "Chiều hoàng hôn nhuộm tím cả con đường\nGió thổi bay đi bao nỗi vấn vương\nBước thật chậm giữa dòng đời vội vã\nTìm lại bình yên sau những ngày phong ba.",
        ],
        "chorus": [
            "Thả hồn trôi theo từng nốt nhạc êm đềm\nBình yên ghé qua làm dịu mát trái tim\nChẳng cần bận tâm chuyện đúng sai ngày mai\nChỉ cần phút giây này ta được là chính mình.",
            "Hít một hơi thật sâu đón gió trời\nNở một nụ cười tiễn đưa ưu phiền rơi\nCuộc sống vốn dĩ giản đơn vậy thôi\nHạnh phúc là khi lòng ta thấy thảnh thơi.",
        ],
        "verses_2": [
            "Ngắm thành phố lên đèn lung linh sắc màu\nBao ồn ào dường như đã lùi lại phía sau\nNgồi nghe tiếng radio vang lên dịu dàng\nThấy lòng mình thênh thang giữa trần gian.",
        ],
        "bridge": [
            "Đôi khi chậm lại một chút để lắng nghe\nTiếng lòng mình giữa những bộn bề\nMọi giông bão rồi cũng sẽ qua đi\nChỉ còn lại sự an yên trong tim.",
        ],
        "outro": [
            "Bình yên là đây... trong khoảnh khắc này\nChúc em một đêm thật ngon giấc.\nNhạc du dương... tan vào đêm.",
        ],
    },
    "energy": {
        "titles": [
            "Cháy Hết Đam Mê", "Vượt Qua Giới Hạn", "Khát Vọng Tuổi Trẻ",
            "Bừng Sáng Tương Lai", "Không Thể Ngừng Lại", "Cất Cánh Bay Cao",
            "Ngọn Lửa Bất Diệt", "Chiến Binh Ánh Sáng", "Bước Ra Ánh Sáng",
        ],
        "verses_1": [
            "Thức giấc đón ánh bình minh rực lửa\nĐứng trước gương thấy niềm tin thắp sáng\nBao chông gai chẳng thể cản bước chân\nVì trong tim ta khát vọng ngút ngàn.",
            "Bao nhiêu lần ngã là bấy nhiêu lần đứng lên\nÁp lực tạo nên viên kim cương sáng chói\nĐường ta đi ta tự mình quyết định\nChẳng sợ bóng tối che lấp bình minh.",
        ],
        "chorus": [
            "Cháy hết mình cho tuổi trẻ hôm nay!\nBật tung năng lượng xua tan bóng tối này!\nHét thật to cho cả thế giới nghe\nTa là ai và ta sẽ làm được!",
            "Tiến lên phía trước không bao giờ lùi bước!\nNgọn lửa đam mê trong tim luôn rực sáng!\nChạm tay vào giấc mơ ta hằng mơ ước\nVinh quang đang chờ đón chúng ta!",
        ],
        "verses_2": [
            "Nhịp tim đập mạnh theo từng tiếng bass dồn\nÂm nhạc dẫn lối xua tan đi hoàng hôn\nCùng nhau vỗ tay hòa chung một nhịp\nNăng lượng bùng nổ không gì ngăn kịp.",
        ],
        "bridge": [
            "Dù ai nói gì... ta vẫn kiên cường!\nDù đường còn xa... ta vẫn tiến bước!\nChỉ một lần sống... hãy sống rực rỡ nhất!",
        ],
        "outro": [
            "Let's go! Bùng nổ nào!\nKhông gì là không thể!\nYeah... ta đã chiến thắng!",
        ],
    },
    "nostalgia": {
        "titles": [
            "Thanh Xuân Năm Ấy", "Chuyến Tàu Tuổi Trẻ", "Lời Hẹn Mùa Hè",
            "Gửi Tôi Của Ngày Xưa", "Sân Trường Nắng Rơi", "Mối Tình Đầu Đẹp Nhất",
            "Màu Áo Trắng Học Trò", "Ký Ức Thời Gian", "Tiếng Trống Trường Xưa",
        ],
        "verses_1": [
            "Mùa hạ năm ấy ve kêu râm ran trên cành\nTà áo trắng bay trong gió chiều thuở thanh xuân\nTrang lưu bút viết vội bao lời hẹn ước\nGiờ ngoảnh nhìn lại đã trôi xa mấy mùa hoa.",
            "Tiếng trống trường vang lên từng nhịp giục giã\nCánh phượng đỏ rơi ngập kín sân trường\nÁnh mắt ai trao nhau thẹn thùng buổi tan trường\nLà mối tình đầu đẹp nhất thời niên thiếu.",
        ],
        "chorus": [
            "Thanh xuân ơi xin trôi thật chậm thôi\nĐể ta giữ lại nụ cười bạn bè trên môi\nNhững ước mơ ngây ngô thời áo trắng\nTheo ta đi suốt cuộc đời này thênh thang.",
            "Dù sau này mỗi người một phương trời xa\nKý ức năm xưa vẫn không hề nhạt nhòa\nCảm ơn vì đã cùng nhau đi qua\nKhoảng trời thanh xuân đẹp đẽ nhất đời ta.",
        ],
        "verses_2": [
            "Chiếc xe đạp cũ cùng nhau qua phố dài\nNhững chiều tan học rộn rã tiếng cười vui\nGiờ đây trưởng thành giữa dòng đời hối hả\nChỉ mong một lần được trở lại ngày xưa.",
        ],
        "bridge": [
            "Thời gian vô tình chẳng đợi chờ một ai\nNhưng kỷ niệm đẹp sẽ còn mãi bên ta\nNụ cười thuở ấy ngây thơ trong sáng\nSưởi ấm lòng ta những lúc nhọc nhằn.",
        ],
        "outro": [
            "Tạm biệt thanh xuân rực rỡ nhất...\nHẹn gặp lại nhau ở cuối con đường.\nKý ức mãi xanh ngời.",
        ],
    },
}


def detect_theme(topic: str = "", mood: str = "", genre: str = "") -> str:
    """Tự động nhận diện theme dựa trên từ khóa tiếng Việt hoặc mood."""
    text = f"{topic} {mood} {genre}".lower()

    if any(k in text for k in ["buồn", "sad", "chia tay", "khóc", "thất tình", "cô đơn", "lạnh", "đau", "mất", "vỡ"]):
        return "sad"
    elif any(k in text for k in ["chill", "lo-fi", "lofi", "cà phê", "mưa", "thư giãn", "calm", "bình yên", "nhẹ"]):
        return "chill"
    elif any(k in text for k in ["cháy", "energetic", "rock", "edm", "nhảy", "sôi động", "chiến", "quyết tâm", "vui", "happy"]):
        return "energy"
    elif any(k in text for k in ["thanh xuân", "tuổi trẻ", "học trò", "trường", "xưa", "kỷ niệm", "nostalgia", "hoài niệm", "nhớ"]):
        return "nostalgia"
    else:
        return "love"  # default theme


def generate_structured_lyrics(
    topic: str = "",
    genre: str = "vpop",
    mood: str = "happy",
    vocal_gender: str = "female",
) -> dict:
    """
    Sinh toàn bộ cấu trúc lời bài hát chuẩn Suno và gợi ý tiêu đề:
    - Ưu tiên: Sử dụng LLM (Google Gemini / OpenAI) để sáng tác lời bài hát mới mẻ 100%,
      giàu chất thơ, chuẩn vần điệu, ngắt câu 5-8 từ giúp AI hát rõ lời.
    - Dự phòng: Tự động fallback về kho template mẫu nếu chưa có API key.

    Returns:
        {
            "title": str,
            "lyrics": str (formatted with [Intro], [Verse 1], [Chorus], etc.),
            "style_tags": str,
            "theme": str,
        }
    """
    # ── 1. Thử sáng tác bằng LLM thông minh thực thụ ──
    try:
        from .llm_service import is_llm_available, generate_lyrics_with_llm
        if is_llm_available():
            llm_res = generate_lyrics_with_llm(
                topic=topic.strip() or "tình yêu cuộc sống",
                genre=genre,
                mood=mood,
                vocal_gender=vocal_gender,
                language="vi",
            )
            if llm_res and llm_res.get("lyrics"):
                return llm_res
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[SmartLyrics] Fallback sang template: {e}")
    theme_key = detect_theme(topic, mood, genre)
    theme_data = LYRIC_THEMES.get(theme_key, LYRIC_THEMES["love"])

    # Chọn ngẫu nhiên components
    title = random.choice(theme_data["titles"])
    v1 = random.choice(theme_data["verses_1"])
    chorus = random.choice(theme_data["chorus"])
    v2 = random.choice(theme_data["verses_2"])
    bridge = random.choice(theme_data["bridge"])
    outro = random.choice(theme_data["outro"])

    # Nếu người dùng có nhập topic cụ thể, biến đổi tiêu đề cho phù hợp
    if topic.strip() and len(topic.strip()) < 35:
        custom_t = topic.strip().title()
        if random.random() > 0.4:
            title = custom_t

    # Lắp ghép theo format chuẩn Suno / ACE-Step
    lyrics = (
        f"[Intro]\n\n"
        f"[Verse 1]\n"
        f"{v1}\n\n"
        f"[Chorus]\n"
        f"{chorus}\n\n"
        f"[Verse 2]\n"
        f"{v2}\n\n"
        f"[Chorus]\n"
        f"{chorus}\n\n"
        f"[Bridge]\n"
        f"{bridge}\n\n"
        f"[Chorus]\n"
        f"{chorus}\n\n"
        f"[Outro]\n"
        f"{outro}"
    )

    # Xây dựng gợi ý style tags phù hợp
    genre_map = {
        "vpop": "Vietnamese pop, V-Pop, emotional ballad, melodic piano, acoustic guitar",
        "kpop": "K-Pop, catchy synth, upbeat modern beat, polished production",
        "pop": "pop, catchy melody, radio-friendly, modern drums",
        "rock": "rock, electric guitar overdrive, driving drums, energetic",
        "lofi": "lo-fi chill, relaxing beat, soft piano, rain sounds, mellow",
        "acoustic": "acoustic guitar, warm vocal, folk ballad, intimate",
        "rnb": "contemporary R&B, smooth groove, expressive vocals, 808 bass",
        "rap": "Vietnamese hip-hop, trap beat, rhythmic flow, punchy 808",
        "edm": "EDM, powerful synth lead, build-up, energetic bass drop",
    }
    base_style = genre_map.get(genre, "Vietnamese pop, emotional melody, acoustic")

    # Bổ sung tag giọng hát
    vocal_tag = ""
    if vocal_gender == "female":
        vocal_tag = "sweet female vocal, expressive singing"
    elif vocal_gender == "male":
        vocal_tag = "deep male vocal, soulful singing"
    elif vocal_gender == "duet":
        vocal_tag = "duet vocal, male and female harmony"
    else:
        vocal_tag = "clear emotional vocal"

    final_style = f"{base_style}, {vocal_tag}, high quality, studio recording"

    return {
        "title": title,
        "lyrics": lyrics,
        "style_tags": final_style,
        "theme": theme_key,
    }


# Alias tương thích ngược
generate_smart_lyrics = generate_structured_lyrics

