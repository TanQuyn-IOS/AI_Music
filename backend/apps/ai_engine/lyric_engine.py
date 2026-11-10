"""
Sonavia Studio — Multilingual Lyric Engine (Phase 2)
======================================================
Sinh lời bài hát tự động cho 5 ngôn ngữ:
  vi  — Tiếng Việt (V-Pop)
  ko  — 한국어 (K-Pop)
  ja  — 日本語 (J-Pop / Anime)
  zh  — 中文 (C-Pop / Mandopop)
  en  — English (Pop / Ballad)

Mỗi ngôn ngữ có:
  - Tiêu đề thể loại đặc trưng
  - Verse 1, Verse 2, Chorus, Bridge, Outro
  - Hỗ trợ đa theme (love, sad, chill, energy, nostalgia, youth, breakup)
  - Format chuẩn Suno/ACE-Step: [Intro], [Verse 1], [Chorus] ...
"""

import random
import re

# ═══════════════════════════════════════════════════════════════════════════════
# VIETNAMESE (vi)  ── đã có trong smart_lyrics.py, import lại ở đây
# ═══════════════════════════════════════════════════════════════════════════════
VI_LYRICS = {
    "love": {
        "titles": ["Tình Yêu Không Lời", "Ánh Mắt Ngây Ngô", "Nơi Trái Tim Thuộc Về",
                   "Bên Em Mùa Nắng Hạ", "Hẹn Ước Dưới Trăng", "Giai Điệu Tình Yêu"],
        "verses_1": [
            "Từng giọt nắng khẽ rơi bên hiên nhà\nNụ cười em thắp sáng cả không gian\nBước chân qua góc phố quen ngày nào\nNgỡ như đôi ta đã thuộc về nhau từ lâu.",
            "Chiều hoàng hôn buông nắng vàng dịu êm\nNhớ bờ môi ngọt ngào nhớ bàn tay mềm\nNhững phút giây bình yên bên cạnh người\nLà điều vô giá nhất cuộc đời anh.",
        ],
        "chorus": [
            "Và anh muốn hát cho em nghe khúc ca này\nGửi trọn yêu thương vào từng cơn gió bay\nDẫu cho mai sau bao sóng gió ngập tràn\nBàn tay anh vẫn luôn nắm chặt tay em.",
            "Người là câu hát ngân vang mãi trong đời\nLà giấc mơ êm đềm anh luôn tìm tới\nYêu em trọn vẹn chẳng hề đổi thay\nBên nhau mãi mãi qua ngàn đắng cay.",
        ],
        "verses_2": [
            "Dù ngày mai dòng đời có xô nghiêng\nAnh vẫn đứng đây giữ trọn lời nguyền\nTừng kỷ niệm ta gom góp mỗi ngày\nSẽ là ngọn lửa ấm giữa trời đông.",
        ],
        "bridge": [
            "Dẫu ngàn năm thời gian cứ thế trôi\nTình yêu đôi ta vẫn vẹn nguyên không phai phôi\nĐi qua ngàn bão giông để tìm thấy nhau\nGiữ lấy nhau cho đến muôn đời sau.",
        ],
        "outro": ["Mãi yêu em... người hỡi\nKhúc ca này trao riêng mình em.\nLa la la... yêu em mãi thôi."],
    },
    "sad": {
        "titles": ["Mưa Đêm Phố Vắng", "Kỷ Niệm Đã Phai", "Buông Tay Một Người",
                   "Nốt Trầm Tan Vỡ", "Gió Lạnh Mùa Thu", "Vết Thương Chưa Lành"],
        "verses_1": [
            "Cơn mưa đêm rơi buốt giá đôi bờ vai\nTiếng thở dài rơi giữa phố dài không ai\nBóng hình em đã khuất xa chân trời\nĐể lại anh với ngổn ngang nỗi đau một đời.",
            "Lá vàng rơi rụng đầy trên lối quen xưa\nBàn tay lạnh giá bước đi dưới chiều mưa\nLời hứa ngày xưa giờ hóa mây trời\nEm rời đi mang theo hết cả tiếng cười.",
        ],
        "chorus": [
            "Tại sao đôi ta phải cách xa như vậy\nĐể lại vết thương rỉ máu từng ngày\nCứ ngỡ bên nhau sẽ là mãi mãi\nNào ngờ hôm nay chỉ còn tiếng thở dài.",
            "Nước mắt rơi hòa vào cơn mưa đêm lạnh căm\nNgười đi để lại nỗi nhớ âm thầm\nBiết trách ai khi duyên phận lỡ làng\nChỉ trách lòng mình quá đỗi nặng mang.",
        ],
        "verses_2": [
            "Đèn đường hiu hắt soi bóng đơn côi\nBước chân lạc lõng giữa biển người nổi trôi\nTự nhủ lòng phải mạnh mẽ đứng lên\nNhưng sao hình bóng ấy vẫn chưa thể quên.",
        ],
        "bridge": [
            "Có những nỗi đau không thể thốt nên lời\nChỉ biết ôm chặt niềm đau vào sâu lòng thôi\nNếu có kiếp sau xin đừng gặp lại\nĐể chẳng phải đau đớn như lúc này.",
        ],
        "outro": ["Mưa tạnh rồi... mà lòng chưa nguôi ngoai\nTạm biệt em... kỷ niệm đã phai.\nChỉ còn bóng đêm... và anh."],
    },
    "chill": {
        "titles": ["Phố Đêm Yên Bình", "Tách Cà Phê Ban Sáng", "Những Ngày Bình Yên",
                   "Hương Cà Phê & Mưa", "Chiều Muộn Ven Hồ", "Thả Hồn Theo Gió"],
        "verses_1": [
            "Bật một bản nhạc lo-fi quen thuộc\nNhìn ngoài ô cửa mưa rơi nhè nhẹ\nTách trà ấm nghi ngút khói bay\nGác lại hết bao mệt mỏi ban ngày.",
            "Chiều hoàng hôn nhuộm tím cả con đường\nGió thổi bay đi bao nỗi vấn vương\nBước thật chậm giữa dòng đời vội vã\nTìm lại bình yên sau những ngày phong ba.",
        ],
        "chorus": [
            "Thả hồn trôi theo từng nốt nhạc êm đềm\nBình yên ghé qua làm dịu mát trái tim\nChẳng cần bận tâm chuyện đúng sai ngày mai\nChỉ cần phút giây này ta được là chính mình.",
        ],
        "verses_2": [
            "Ngắm thành phố lên đèn lung linh sắc màu\nBao ồn ào dường như đã lùi lại phía sau\nNgồi nghe tiếng radio vang lên dịu dàng\nThấy lòng mình thênh thang giữa trần gian.",
        ],
        "bridge": [
            "Đôi khi chậm lại một chút để lắng nghe\nTiếng lòng mình giữa những bộn bề\nMọi giông bão rồi cũng sẽ qua đi\nChỉ còn lại sự an yên trong tim.",
        ],
        "outro": ["Bình yên là đây... trong khoảnh khắc này\nChúc em một đêm thật ngon giấc.\nNhạc du dương... tan vào đêm."],
    },
    "energy": {
        "titles": ["Cháy Hết Đam Mê", "Vượt Qua Giới Hạn", "Khát Vọng Tuổi Trẻ",
                   "Bừng Sáng Tương Lai", "Ngọn Lửa Bất Diệt"],
        "verses_1": [
            "Thức giấc đón ánh bình minh rực lửa\nĐứng trước gương thấy niềm tin thắp sáng\nBao chông gai chẳng thể cản bước chân\nVì trong tim ta khát vọng ngút ngàn.",
        ],
        "chorus": [
            "Cháy hết mình cho tuổi trẻ hôm nay!\nBật tung năng lượng xua tan bóng tối này!\nHét thật to cho cả thế giới nghe\nTa là ai và ta sẽ làm được!",
        ],
        "verses_2": [
            "Nhịp tim đập mạnh theo từng tiếng bass dồn\nÂm nhạc dẫn lối xua tan đi hoàng hôn\nCùng nhau vỗ tay hòa chung một nhịp\nNăng lượng bùng nổ không gì ngăn kịp.",
        ],
        "bridge": ["Dù ai nói gì... ta vẫn kiên cường!\nDù đường còn xa... ta vẫn tiến bước!\nChỉ một lần sống... hãy sống rực rỡ nhất!"],
        "outro": ["Let's go! Bùng nổ nào!\nKhông gì là không thể!\nYeah... ta đã chiến thắng!"],
    },
    "nostalgia": {
        "titles": ["Thanh Xuân Năm Ấy", "Chuyến Tàu Tuổi Trẻ", "Gửi Tôi Của Ngày Xưa",
                   "Sân Trường Nắng Rơi", "Màu Áo Trắng Học Trò"],
        "verses_1": [
            "Mùa hạ năm ấy ve kêu râm ran trên cành\nTà áo trắng bay trong gió chiều thuở thanh xuân\nTrang lưu bút viết vội bao lời hẹn ước\nGiờ ngoảnh nhìn lại đã trôi xa mấy mùa hoa.",
        ],
        "chorus": [
            "Thanh xuân ơi xin trôi thật chậm thôi\nĐể ta giữ lại nụ cười bạn bè trên môi\nNhững ước mơ ngây ngô thời áo trắng\nTheo ta đi suốt cuộc đời này thênh thang.",
        ],
        "verses_2": [
            "Chiếc xe đạp cũ cùng nhau qua phố dài\nNhững chiều tan học rộn rã tiếng cười vui\nGiờ đây trưởng thành giữa dòng đời hối hả\nChỉ mong một lần được trở lại ngày xưa.",
        ],
        "bridge": [
            "Thời gian vô tình chẳng đợi chờ một ai\nNhưng kỷ niệm đẹp sẽ còn mãi bên ta\nNụ cười thuở ấy ngây thơ trong sáng\nSưởi ấm lòng ta những lúc nhọc nhằn.",
        ],
        "outro": ["Tạm biệt thanh xuân rực rỡ nhất...\nHẹn gặp lại nhau ở cuối con đường.\nKý ức mãi xanh ngời."],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# KOREAN (ko)  ── K-Pop, K-Ballad
# ═══════════════════════════════════════════════════════════════════════════════
KO_LYRICS = {
    "love": {
        "titles": ["별빛 아래서", "너라는 세상", "사랑해 그대를", "영원히 함께", "내 마음의 노래"],
        "verses_1": [
            "오늘도 너를 생각해\n하루가 지나가도 잊혀지지 않아\n네 미소가 내 곁에\n이 세상 모든 것이 빛나는 것 같아",
            "차가운 바람이 불어도\n네 온기가 내 마음을 녹여줘\n어두운 밤이 와도\n네 빛이 나를 밝혀줘",
        ],
        "chorus": [
            "사랑해 너를 사랑해\n이 마음은 영원히 변하지 않아\n네 손을 잡고 걸어갈게\n함께라면 두렵지 않아",
            "너와 함께라면 괜찮아\n어떤 어려움도 이겨낼 수 있어\n내 전부를 다 줄게\n영원히 네 곁에 있을게",
        ],
        "verses_2": [
            "시간이 지나가도\n우리의 사랑은 더 깊어져\n힘든 날에도 웃을 수 있어\n네가 있기 때문에",
        ],
        "bridge": [
            "어떤 말로도 표현할 수 없어\n이 감정이 얼마나 소중한지\n그냥 네 옆에 있고 싶어\n영원히 영원히",
        ],
        "outro": ["사랑해... 영원히\n함께해줘서 고마워\n우리 이대로 영원히"],
    },
    "sad": {
        "titles": ["이별 후에", "혼자인 밤", "눈물이 나", "그리움", "잊을 수 없어"],
        "verses_1": [
            "텅 빈 방 안에 홀로 남아\n네 흔적을 지우려 해도\n어디서나 네가 보여\n잊히지 않아 너란 사람",
            "차가운 바람이 부는 밤\n네 빈자리가 더 크게 느껴져\n전화기를 들었다 놓고\n결국 오늘도 혼자야",
        ],
        "chorus": [
            "보고 싶어 너무 보고 싶어\n이 마음은 어디로 가야 할까\n눈물이 멈추지 않아\n너 없이는 살 수가 없어",
            "왜 우리는 이렇게 됐을까\n분명 행복했던 날이 있었는데\n지금 이 순간 너무 힘들어\n그냥 네 목소리 듣고 싶어",
        ],
        "verses_2": [
            "앨범 속 사진을 보며\n그때가 얼마나 좋았는지\n돌아올 수 없는 시간\n그게 가장 아파",
        ],
        "bridge": [
            "미안해 미안해\n충분히 잘해주지 못해서\n이제는 늦었지만\n알았으면 좋았을 텐데",
        ],
        "outro": ["잘 있어... 행복해\n나는 괜찮을 거야\n언젠가는 잊을 수 있겠지"],
    },
    "chill": {
        "titles": ["느긋한 오후", "커피 한 잔", "비 오는 날", "조용한 시간", "여유로운 하루"],
        "verses_1": [
            "창문 밖에 빗소리가 들려\n따뜻한 커피 한 잔 들고\n음악을 틀고 눕는 거야\n오늘은 아무것도 안 해도 돼",
        ],
        "chorus": [
            "이런 시간이 좋아\n바쁜 일상에서 잠깐 벗어나\n나만의 시간 속에서\n그냥 쉬어가도 괜찮아",
        ],
        "verses_2": [
            "서두르지 않아도 돼\n천천히 가도 괜찮아\n지금 이 순간이 행복이야\n그것만으로도 충분해",
        ],
        "bridge": ["때로는 멈춰서\n자신을 돌아보는 시간이 필요해\n숨을 깊게 들이쉬고\n편안하게 쉬어가"],
        "outro": ["좋은 밤 되세요\n편안하게 쉬어요\nLa la la..."],
    },
    "energy": {
        "titles": ["달려가", "불꽃처럼", "지금 이 순간", "한계를 넘어", "빛나는 오늘"],
        "verses_1": [
            "일어나 지금 당장\n포기하기엔 너무 일러\n꿈을 향해 달려가\n멈추지 마 지금부터야",
        ],
        "chorus": [
            "불꽃처럼 타올라\n온 세상이 나를 보게 해\n이 순간을 영원히\n기억할 거야 우리 함께",
        ],
        "verses_2": [
            "넘어져도 일어나\n상처는 나를 더 강하게 해\n포기란 없어 내 사전엔\n오직 앞으로만 나아가",
        ],
        "bridge": ["지금 이 순간\n전부를 다 불태워\n후회 없이 살아가\nGo go go!"],
        "outro": ["우리 함께 달려가\n포기하지 마\nYeah! 할 수 있어!"],
    },
    "nostalgia": {
        "titles": ["그 시절로", "학창시절", "첫사랑", "추억 속에서", "그때 그 자리"],
        "verses_1": [
            "교복 입던 그 시절이\n지금도 생생히 기억나\n방과 후 함께 걷던 길\n그때가 제일 행복했어",
        ],
        "chorus": [
            "돌아갈 수 없어도\n그 기억은 영원히 내 안에\n청춘의 노래가\n지금도 내 맘 속에 울려",
        ],
        "verses_2": [
            "세월이 흘러가도\n변하지 않는 것들이 있어\n함께했던 그 날들\n소중하게 간직할게",
        ],
        "bridge": ["시간아 멈춰라\n이 순간이 영원하기를\n그때로 돌아가고 싶어\n단 하루만이라도"],
        "outro": ["그리운 그 시절\n잊지 않을게\n소중한 추억으로"],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# JAPANESE (ja)  ── J-Pop, Anime OST
# ═══════════════════════════════════════════════════════════════════════════════
JA_LYRICS = {
    "love": {
        "titles": ["星に願いを", "君のそばで", "永遠の愛", "キミと一緒に", "愛の歌"],
        "verses_1": [
            "毎日君のことを想ってる\n時間が経っても忘れられない\n君の笑顔が僕の隣に\nこの世界全てが輝いて見える",
            "冷たい風が吹いても\n君の温もりが心を溶かしてくれる\n暗い夜が来ても\n君の光が照らしてくれる",
        ],
        "chorus": [
            "愛してる 君を愛してる\nこの気持ちは永遠に変わらない\n君の手を握って歩いていくよ\n一緒なら怖くない",
            "君といればいい\nどんな困難も乗り越えられる\n全てを捧げるよ\n永遠に君の隣にいる",
        ],
        "verses_2": [
            "時間が過ぎても\n僕たちの愛はもっと深まって\n辛い日でも笑えるよ\n君がいるから",
        ],
        "bridge": [
            "言葉では表せない\nこの感情がどれほど大切か\nただ君の傍にいたい\n永遠に 永遠に",
        ],
        "outro": ["愛してる... 永遠に\n一緒にいてくれてありがとう\nいつまでも共に"],
    },
    "sad": {
        "titles": ["別れの後に", "ひとりの夜", "涙が出る", "想い出の中で", "忘れられない"],
        "verses_1": [
            "空の部屋にひとり残って\n君の痕跡を消そうとしても\nどこにでも君が見える\n忘れられない 君という人",
            "冷たい風が吹く夜\n君の空席がもっと大きく感じる\n電話を手に取っては置いて\n結局今夜もひとり",
        ],
        "chorus": [
            "会いたい すごく会いたい\nこの気持ちはどこへ向かえばいい\n涙が止まらない\n君なしでは生きられない",
        ],
        "verses_2": [
            "アルバムの写真を見ながら\nあの頃がどれほど良かったか\n戻れない時間\nそれが一番辛い",
        ],
        "bridge": ["ごめんね ごめんね\n十分に大切にしてあげられなくて\nもう遅いけど\nわかっていれば良かったのに"],
        "outro": ["さようなら... 幸せでいてね\n僕は大丈夫だよ\nいつか忘れられるかな"],
    },
    "chill": {
        "titles": ["のんびりな午後", "コーヒー一杯", "雨の日に", "静かな時間", "ゆったりとした日"],
        "verses_1": [
            "窓の外に雨音が聞こえる\n温かいコーヒーを片手に\n音楽をかけて横になるよ\n今日は何もしなくていい",
        ],
        "chorus": [
            "こんな時間が好き\n忙しい日常からちょっと離れて\n自分だけの時間の中で\nゆっくり休んでもいいんだよ",
        ],
        "verses_2": [
            "急がなくていい\nゆっくり行っても大丈夫\n今この瞬間が幸せ\nそれだけで十分だよ",
        ],
        "bridge": ["時には立ち止まって\n自分を振り返る時間が必要\n深呼吸して\nゆっくり休もう"],
        "outro": ["おやすみなさい\nゆっくり休んでね\nLa la la..."],
    },
    "energy": {
        "titles": ["走り出せ", "炎のように", "今この瞬間", "限界を超えて", "輝く今日"],
        "verses_1": [
            "立ち上がれ 今すぐ\n諦めるには早すぎる\n夢に向かって走り出せ\n止まるな 今からだ",
        ],
        "chorus": [
            "炎のように燃え上がれ\n全世界が僕を見るように\nこの瞬間を永遠に\n覚えているよ みんなと共に",
        ],
        "verses_2": [
            "倒れても立ち上がれ\n傷は僕を強くする\n諦めなんて僕の辞書にない\nただ前へ進むだけ",
        ],
        "bridge": ["今この瞬間\n全てを燃やし尽くせ\n後悔なく生きていけ\nGo go go!"],
        "outro": ["みんなと走り出そう\n諦めるな\nYeah! できるよ!"],
    },
    "nostalgia": {
        "titles": ["あの頃へ", "学生時代", "初恋", "思い出の中で", "あの場所に"],
        "verses_1": [
            "制服を着ていたあの頃が\n今でも鮮明に思い出せる\n放課後一緒に歩いた道\nあの頃が一番幸せだった",
        ],
        "chorus": [
            "戻れなくても\nその記憶は永遠に僕の中に\n青春の歌が\n今も心に響いている",
        ],
        "verses_2": [
            "月日が流れても\n変わらないものがある\n一緒にいたあの日々\n大切に胸に刻もう",
        ],
        "bridge": ["時よ止まれ\nこの瞬間が永遠であるように\nあの頃に戻りたい\nたった一日でもいいから"],
        "outro": ["懐かしいあの頃\n忘れないよ\n大切な思い出として"],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# CHINESE (zh)  ── C-Pop, Mandopop
# ═══════════════════════════════════════════════════════════════════════════════
ZH_LYRICS = {
    "love": {
        "titles": ["星光下的你", "爱你是我的幸运", "永远在一起", "心里有你", "我的爱"],
        "verses_1": [
            "每一天都在想着你\n时间流逝也不会忘记\n你的笑容在我身边\n这个世界因你而美丽",
            "即使寒风吹来\n你的温暖融化了我的心\n即使黑暗降临\n你的光芒照亮了我的路",
        ],
        "chorus": [
            "爱你 我爱你\n这份心意永远不会变\n牵着你的手走下去\n有你在我不害怕",
            "和你在一起就好\n任何困难都能克服\n把一切都给你\n永远陪在你身边",
        ],
        "verses_2": [
            "时光流逝\n我们的爱越来越深\n在艰难的日子里也能微笑\n因为有你在身边",
        ],
        "bridge": [
            "用语言无法表达\n这份感情有多珍贵\n只想陪在你身边\n永远 永远",
        ],
        "outro": ["爱你... 永远\n谢谢你陪伴我\n就这样永远在一起"],
    },
    "sad": {
        "titles": ["分手之后", "一个人的夜晚", "泪水流下", "思念", "忘不了你"],
        "verses_1": [
            "空荡荡的房间里独自留下\n想要抹去你的痕迹\n却在哪里都能看见你\n忘不了 忘不了你这个人",
            "寒风吹来的夜晚\n你的空位显得更大\n拿起电话又放下\n今晚还是独自一人",
        ],
        "chorus": [
            "想见你 太想见你\n这份心情该往哪里去\n泪水止不住流\n没有你我活不下去",
        ],
        "verses_2": [
            "翻看相册里的照片\n那时候多么美好\n回不去的时光\n是最深的痛",
        ],
        "bridge": ["对不起 对不起\n没有好好珍惜你\n现在已经太晚了\n早知道就好了"],
        "outro": ["再见了... 希望你幸福\n我会好起来的\n总有一天会忘记"],
    },
    "chill": {
        "titles": ["悠闲的下午", "一杯咖啡", "雨天", "安静的时光", "慢慢来"],
        "verses_1": [
            "窗外传来雨声\n捧着温热的咖啡\n放着音乐躺下来\n今天什么都不用做",
        ],
        "chorus": [
            "喜欢这样的时光\n暂时离开忙碌的日常\n在属于自己的时间里\n好好休息也没关系",
        ],
        "verses_2": [
            "不用着急\n慢慢来也没关系\n此刻就是幸福\n这样就已经足够了",
        ],
        "bridge": ["有时候要停下来\n需要一段时间来回顾自己\n深呼吸\n好好休息"],
        "outro": ["晚安\n好好休息\nLa la la..."],
    },
    "energy": {
        "titles": ["冲吧", "像火焰一样", "此刻", "超越极限", "闪耀的今天"],
        "verses_1": [
            "站起来 就是现在\n放弃还太早\n向着梦想冲去\n不要停 从现在开始",
        ],
        "chorus": [
            "像火焰一样燃烧\n让全世界都看见我\n将这个瞬间永远铭记\n和大家一起",
        ],
        "verses_2": [
            "跌倒了再站起来\n伤痛让我更坚强\n我的字典里没有放弃\n只有向前走",
        ],
        "bridge": ["就在此刻\n燃烧一切\n无怨无悔地活着\nGo go go!"],
        "outro": ["大家一起冲吧\n不要放弃\nYeah! 我们可以做到!"],
    },
    "nostalgia": {
        "titles": ["回到那时候", "学生时代", "初恋", "记忆中的你", "那个地方"],
        "verses_1": [
            "穿着校服的那些日子\n现在还记忆犹新\n放学后一起走的那条路\n那时候是最幸福的",
        ],
        "chorus": [
            "即使回不去\n那些记忆永远在我心中\n青春的歌声\n至今仍在心中回响",
        ],
        "verses_2": [
            "岁月流逝\n有些东西永远不会变\n一起度过的那些日子\n要好好珍藏在心里",
        ],
        "bridge": ["时间请停止\n让这个瞬间永远\n想回到那时候\n哪怕只有一天"],
        "outro": ["怀念那些日子\n不会忘记\n作为珍贵的记忆"],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# ENGLISH (en)  ── Pop, Ballad, Indie
# ═══════════════════════════════════════════════════════════════════════════════
EN_LYRICS = {
    "love": {
        "titles": ["Starlight", "All Of You", "Forever Yours", "Beside You", "Love Song"],
        "verses_1": [
            "Every single day I'm thinking of you\nTime may pass but I can't forget\nYour smile is always near me\nThis whole world is shining because of you",
            "Even when the cold wind blows\nYour warmth melts away my fears\nEven when the darkness falls\nYour light guides me through the night",
        ],
        "chorus": [
            "I love you, I love you\nThis feeling never gonna change\nI'll hold your hand and walk with you\nTogether we're not afraid",
            "As long as you're with me I'm fine\nWe can face any storm that comes\nI'll give you everything I have\nForever by your side",
        ],
        "verses_2": [
            "As time goes by\nOur love only grows deeper still\nOn the hardest days I still can smile\nBecause I have you here",
        ],
        "bridge": [
            "There are no words to describe\nHow precious this feeling truly is\nI just want to stay by your side\nForever and ever",
        ],
        "outro": ["I love you... forever\nThank you for being with me\nLet's stay like this forever"],
    },
    "sad": {
        "titles": ["After You Left", "Alone Tonight", "Tears Fall Down", "Missing You", "Can't Forget"],
        "verses_1": [
            "Alone in this empty room\nTrying to erase every trace of you\nBut I see you everywhere I go\nCan't forget you no matter what I do",
            "On these cold and windy nights\nYour absence feels even bigger\nI pick up the phone then put it down\nSpending another night alone",
        ],
        "chorus": [
            "I miss you so much I miss you\nWhere is this heart supposed to go\nThe tears just won't stop falling\nI can't go on without you here",
        ],
        "verses_2": [
            "Looking through old photographs\nRemembering how good it used to be\nThose times we can't go back to\nThat's the deepest hurt in me",
        ],
        "bridge": ["I'm sorry I'm so sorry\nI didn't cherish what we had\nIt's too late now to change things\nI wish I knew what I had"],
        "outro": ["Goodbye... I hope you're happy\nI'll be okay someday\nMaybe I'll forget in time"],
    },
    "chill": {
        "titles": ["Lazy Afternoon", "Coffee & Rain", "Quiet Time", "Easy Sunday", "Slow Down"],
        "verses_1": [
            "Rain is falling on the window pane\nI've got a warm cup in my hands\nPut on some music lie back down\nToday I don't have to do a thing",
        ],
        "chorus": [
            "I love these kinds of days\nSlipping away from the busy world\nIn my own little space of time\nIt's okay to just rest for a while",
        ],
        "verses_2": [
            "No need to rush around\nTaking it slow is just fine\nThis moment right here is happiness\nThat alone is more than enough",
        ],
        "bridge": ["Sometimes you gotta pause\nTake some time to look within\nBreathe in nice and deep\nLet yourself rest"],
        "outro": ["Good night everyone\nSleep well tonight\nLa la la..."],
    },
    "energy": {
        "titles": ["Run For It", "Like A Flame", "Right Now", "Break The Limit", "Shine Today"],
        "verses_1": [
            "Get up right now\nIt's too early to give up\nRun toward your dream\nDon't stop it starts today",
        ],
        "chorus": [
            "Burn like a flame\nLet the whole world see who we are\nThis moment forever\nWe'll remember it together",
        ],
        "verses_2": [
            "When you fall get back up again\nThe pain only makes you stronger\nThere's no giving up in my dictionary\nJust keep on moving forward",
        ],
        "bridge": ["Right here right now\nBurn it all the way down\nLive without regret\nGo go go!"],
        "outro": ["Let's run together\nDon't give up\nYeah! We can do it!"],
    },
    "nostalgia": {
        "titles": ["Back To Those Days", "School Days", "First Love", "In My Memories", "That Place"],
        "verses_1": [
            "Those days back in our school uniforms\nAre still so vivid in my mind\nThe road we walked together after class\nThose were the happiest days of my life",
        ],
        "chorus": [
            "Even if we can't go back\nThose memories live forever in my heart\nThe songs of our youth\nStill echoing inside me today",
        ],
        "verses_2": [
            "Even as the years go by\nSome things will never change\nAll those days we spent together\nI'll keep them safe inside my heart",
        ],
        "bridge": ["Time please stop\nLet this moment last forever\nI want to go back to those days\nJust for one more day"],
        "outro": ["Missing those days\nI'll never forget\nAs precious memories"],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# DISPATCH TABLE  ── map language -> lyrics database
# ═══════════════════════════════════════════════════════════════════════════════
LANG_DB = {
    "vi": VI_LYRICS,
    "ko": KO_LYRICS,
    "ja": JA_LYRICS,
    "zh": ZH_LYRICS,
    "en": EN_LYRICS,
}

# Theme fallback map (if requested theme not in DB for a language, use this)
THEME_FALLBACK = {
    "breakup": "sad",
    "summer": "love",
    "youth": "nostalgia",
    "relax": "chill",
    "motivation": "energy",
    "romantic": "love",
}


def _pick(lst: list) -> str:
    """Choose a random item from a list."""
    return random.choice(lst) if lst else ""


def generate_multilingual_lyrics(
    language: str = "vi",
    theme: str = "love",
    genre: str = "pop",
    vocal_gender: str = "female",
    user_prompt: str = "",
    structure_labels: list | None = None,
) -> dict:
    """
    Sinh lời bài hát theo ngôn ngữ và chủ đề với cấu trúc chuẩn Suno/ACE-Step:
    - Ưu tiên: Sử dụng LLM (Google Gemini / OpenAI) để sáng tác mới mẻ theo prompt thực tế.
    - Dự phòng: Tự động fallback về kho template đa ngôn ngữ.

    Args:
        language:        'vi'|'ko'|'ja'|'zh'|'en'
        theme:           'love'|'sad'|'chill'|'energy'|'nostalgia'|'breakup'|...
        genre:           Tên genre (để chọn style tags)
        vocal_gender:    'female'|'male'|'duet'|'instrumental'
        user_prompt:     Prompt gốc của user (để điều chỉnh tiêu đề nếu có)
        structure_labels: Danh sách nhãn section e.g. ['[Intro]','[Verse 1]',...]

    Returns:
        {
            'title': str,
            'lyrics': str,
            'style_tags': str,
            'theme': str,
            'language': str,
        }
    """
    # ── 1. Thử sáng tác qua LLM nếu khả dụng ──
    try:
        from .llm_service import is_llm_available, generate_lyrics_with_llm
        if is_llm_available():
            clean_topic = user_prompt.strip() if user_prompt else f"Bài hát chủ đề {theme} phong cách {genre}"
            llm_res = generate_lyrics_with_llm(
                topic=clean_topic,
                genre=genre,
                mood=theme,
                vocal_gender=vocal_gender,
                language=language,
                structure_labels=structure_labels,
            )
            if llm_res and llm_res.get("lyrics"):
                llm_res["language"] = language
                return llm_res
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[LyricEngine] LLM fallback: {e}")

    lang = language if language in LANG_DB else "en"
    db = LANG_DB[lang]

    # Resolve theme + fallback
    resolved_theme = theme
    if resolved_theme not in db:
        resolved_theme = THEME_FALLBACK.get(resolved_theme, "love")
    if resolved_theme not in db:
        resolved_theme = list(db.keys())[0]

    td = db[resolved_theme]

    # ── Title ──────────────────────────────────────────────────────────────────
    title = _pick(td["titles"])
    # If user typed a short specific prompt, use it as title (when language is vi)
    if user_prompt.strip() and len(user_prompt.strip()) < 40 and lang == "vi":
        if random.random() > 0.35:
            title = user_prompt.strip().title()

    # ── Structure ──────────────────────────────────────────────────────────────
    if structure_labels is None:
        structure_labels = ["[Intro]", "[Verse 1]", "[Chorus]", "[Verse 2]",
                            "[Chorus]", "[Bridge]", "[Final Chorus]", "[Outro]"]

    v1     = _pick(td.get("verses_1", [""]))
    chorus = _pick(td.get("chorus", [""]))
    v2     = _pick(td.get("verses_2", [""]))
    bridge = _pick(td.get("bridge", [""]))
    outro  = _pick(td.get("outro", [""]))

    def _has(label: str) -> bool:
        return any(s.lower() == label.lower() for s in structure_labels)

    parts = []
    for label in structure_labels:
        lbl_lower = label.lower()
        if "intro" in lbl_lower:
            parts.append(f"{label}\n\n")
        elif "verse 1" in lbl_lower or "verse1" in lbl_lower:
            parts.append(f"{label}\n{v1}\n\n")
        elif "verse 2" in lbl_lower or "verse2" in lbl_lower:
            parts.append(f"{label}\n{v2}\n\n")
        elif "bridge" in lbl_lower:
            parts.append(f"{label}\n{bridge}\n\n")
        elif "outro" in lbl_lower:
            parts.append(f"{label}\n{outro}")
        elif "final chorus" in lbl_lower:
            # Final chorus = chorus mạnh hơn, thêm lại bridge nếu có
            parts.append(f"{label}\n{chorus}\n\n")
        elif "chorus" in lbl_lower or "hook" in lbl_lower:
            parts.append(f"{label}\n{chorus}\n\n")
        elif "pre-chorus" in lbl_lower or "pre_chorus" in lbl_lower:
            # Pre-chorus: dùng đoạn đầu của bridge hoặc phần ngắn
            pre_lines = bridge.split('\n') if bridge else []
            pre_content = "\n".join(pre_lines[:2]) if len(pre_lines) >= 2 else bridge
            parts.append(f"{label}\n{pre_content}\n\n")
        elif "rap" in lbl_lower:
            parts.append(f"{label}\n{v2}\n\n")
        elif "dance break" in lbl_lower or "guitar solo" in lbl_lower:
            # Instrumental break — không cần lyrics, chỉ cần tag
            parts.append(f"{label}\n\n")
        elif "drop" in lbl_lower or "build" in lbl_lower:
            parts.append(f"{label}\n\n")
        else:
            parts.append(f"{label}\n{v1}\n\n")

    lyrics = "".join(parts).strip()

    # ── Style Tags ──────────────────────────────────────────────────────────────
    lang_name = {"vi": "Vietnamese", "ko": "Korean", "ja": "Japanese", "zh": "Chinese", "en": "English"}.get(lang, "English")
    genre_style = {
        "vpop": "Vietnamese pop, emotional ballad, melodic piano, acoustic guitar",
        "kpop": "K-Pop, catchy synth, upbeat modern beat, polished production",
        "jpop": "J-Pop, dynamic, bright, anime soundtrack style",
        "cpop": "C-Pop, poetic, atmospheric, traditional fusion, erhu strings",
        "pop":  "pop, catchy melody, radio-friendly, modern drums",
        "ballad": "ballad, grand piano, orchestral strings, heartfelt",
        "lofi": "lo-fi chill, relaxing beat, soft piano, rain sounds",
        "rnb":  "R&B, smooth groove, expressive vocals, 808 bass",
        "rock": "rock, electric guitar, driving drums, raw energy",
        "edm":  "EDM, powerful synth lead, bass drop, energetic",
        "acoustic": "acoustic guitar, warm vocal, folk ballad, intimate",
        "jazz": "jazz, saxophone, vintage, warm harmonic texture",
    }.get(genre, "pop, melodic, studio quality")

    if vocal_gender == "female":
        vocal_tag = f"solo {lang_name} female vocals, clear articulate singing, expressive"
    elif vocal_gender == "male":
        vocal_tag = f"solo {lang_name} male vocals, warm deep singing, articulate"
    elif vocal_gender == "duet":
        vocal_tag = f"{lang_name} duet vocals, male and female harmony"
    else:
        vocal_tag = "instrumental, no vocals, melodic lead"

    style_tags = f"{vocal_tag}, {genre_style}, high quality, studio recording"

    return {
        "title": title,
        "lyrics": lyrics,
        "style_tags": style_tags,
        "theme": resolved_theme,
        "language": lang,
    }
