"""
Sonavia AI - Vietnamese Phonetic Layer
======================================
Module phân tích ngữ âm tiếng Việt phục vụ Singing Voice Synthesis (SVS),
AI Music Generation và Audio Orchestration.

Mô hình cấu trúc âm tiết tiếng Việt (theo ngữ âm học thực nghiệm & GS. Đoàn Thiện Thuật):
    Âm tiết (Syllable) = Thanh điệu (Tone)
                       + Âm đầu (Onset / C1)
                       + Âm đệm (Glide / -w-)
                       + Âm chính (Nucleus / V)
                       + Âm cuối (Coda / C2)

Quy tắc cốt lõi:
1. Chuẩn hóa 100% Unicode NFC.
2. Bảo tồn nguyên văn ca từ và toàn bộ dấu thanh tiếng Việt (không xóa dấu để phiên âm).
3. Phân biệt rõ rệt giữa:
   - Thanh điệu ngôn ngữ (Linguistic Lexical Tone: micro-intonation / pitch contour 0-5)
   - Cao độ giai điệu âm nhạc (Melodic Musical Pitch: nốt nhạc diatonic / MIDI note).
4. Phân loại trọng số âm học (Acoustic Weight):
   - Open: âm tiết mở (ngân vang dài, legato)
   - Nasal: âm cuối mũi (-m, -n, -ng, -nh, tạo cộng hưởng nasal murmur)
   - Stop: âm cuối tắc (-c, -ch, -p, -t, ngắt staccato dứt khoát)
   - Semivowel: bán âm cuối (-i, -y, -u, -o, chuyển dịch lướt)
5. Xử lý chuẩn xác các trường hợp đặc thù: qu-, gi-, ngh/gh, khuỷu, thuở, gì, giếng,
   các âm tiết mở đầu bằng nguyên âm (zero onset), các nguyên âm đôi, ba.
6. Hỗ trợ phân biệt dữ liệu chuẩn (certain), suy luận (inferred), từ ngoại lai (non_vietnamese)
   và dấu câu (punctuation).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class ToneType(IntEnum):
    """
    Sáu thanh điệu tiếng Việt chuẩn.
    Mã số 0-5 chuẩn hóa theo hệ thống ngữ âm học tiếng Việt.
    """
    NGANG = 0   # Không dấu (Bình thanh / Mid-level / IPA: 33)
    HUYEN = 1   # Dấu huyền (Trầm bình / Low-falling / IPA: 21)
    SAC = 2     # Dấu sắc (Cao thăng / High-rising / IPA: 35)
    HOI = 3     # Dấu hỏi (Trầm thăng - giáng thăng / Dipping-rising / IPA: 313)
    NGA = 4     # Dấu ngã (Cao gãy / Broken-rising / IPA: 305)
    NANG = 5    # Dấu nặng (Trầm nhập / Low-checked / IPA: 21?)


class AcousticWeight(str, Enum):
    """
    Phân loại âm học âm cuối phục vụ tổng hợp giọng hát (SVS):
    - OPEN: Âm tiết mở (không có phụ âm cuối). Cho phép ngân vang nguyên âm legato tự nhiên.
    - NASAL: Âm cuối vang mũi (-m, -n, -ng, -nh). Tạo cộng hưởng xoang mũi ở đuôi nốt.
    - STOP: Âm cuối tắc (-p, -t, -c, -ch). Khép thanh môn/miệng, ngắt staccato dứt khoát.
    - SEMIVOWEL: Bán âm cuối (-i, -y, -u, -o). Lướt chuyển nguyên âm mượt mà.
    """
    OPEN = "open"
    NASAL = "nasal"
    STOP = "stop"
    SEMIVOWEL = "semivowel"


class VowelType(str, Enum):
    """
    Phân loại cấu trúc nguyên âm:
    - MONOPHTHONG: Nguyên âm đơn (a, ă, â, e, ê, i, y, o, ô, ơ, u, ư)
    - DIPHTHONG: Nguyên âm đôi (iê/yê/ia/ya, uô/ua, ươ/ưa)
    - TRIPHTHONG: Tổ hợp âm đệm + đôi, hoặc đôi + bán âm cuối (chiều, người, khuyên, khuỷu)
    """
    MONOPHTHONG = "monophthong"
    DIPHTHONG = "diphthong"
    TRIPHTHONG = "triphthong"


class AnalysisStatus(str, Enum):
    """
    Trạng thái đánh giá độ tin cậy của kết quả phân tích:
    - CERTAIN: Âm tiết chuẩn tiếng Việt hợp lệ 100%.
    - INFERRED: Âm tiết tiếng Việt có dạng cấu tạo suy luận / biến thể hợp lệ.
    - NON_VIETNAMESE: Từ ngoại lai hoặc từ mượn chưa Việt hóa.
    - PUNCTUATION: Ký tự dấu câu hoặc ký hiệu phân tách.
    - UNKNOWN: Chuỗi không xác định hoặc không đủ cơ sở ngữ âm.
    """
    CERTAIN = "certain"
    INFERRED = "inferred"
    NON_VIETNAMESE = "non_vietnamese"
    PUNCTUATION = "punctuation"
    UNKNOWN = "unknown"


# Bảng ánh xạ dấu thanh Unicode NFD combining diacritics sang ToneType
TONE_COMBINING_MARKS: Dict[str, Tuple[int, str, str, str]] = {
    "\u0300": (ToneType.HUYEN.value, "huyền", "falling", "low-falling (21)"),
    "\u0301": (ToneType.SAC.value, "sắc", "rising", "high-rising (35)"),
    "\u0309": (ToneType.HOI.value, "hỏi", "dipping_rising", "dipping-rising (313)"),
    "\u0303": (ToneType.NGA.value, "ngã", "broken_rising", "broken-rising (305)"),
    "\u0323": (ToneType.NANG.value, "nặng", "checked_low", "low-checked (21?)"),
}

# Thông tin chi tiết về từng thanh điệu tiếng Việt
TONE_METADATA: Dict[int, Dict[str, Any]] = {
    ToneType.NGANG.value: {
        "name": "ngang",
        "diacritic": "",
        "contour": "level",
        "ipa": "33",
        "description": "Thanh ngang (bình thanh, không dấu)",
        "svs_singing_hint": "Giữ cao độ ổn định tự nhiên theo nốt nhạc, không lướt cao độ.",
    },
    ToneType.HUYEN.value: {
        "name": "huyền",
        "diacritic": "\u0300",
        "contour": "falling",
        "ipa": "21",
        "description": "Thanh huyền (trầm bình, dấu huyền)",
        "svs_singing_hint": "Bắt đầu nhẹ ở cao độ nốt hoặc hơi thấp hơn, lướt nhẹ xuống ở đuôi âm tiết.",
    },
    ToneType.SAC.value: {
        "name": "sắc",
        "diacritic": "\u0301",
        "contour": "rising",
        "ipa": "35",
        "description": "Thanh sắc (cao thăng, dấu sắc)",
        "svs_singing_hint": "Tấn công dứt khoát, vuốt vi chỉnh cao độ đi lên ở phần cuối âm tiết.",
    },
    ToneType.HOI.value: {
        "name": "hỏi",
        "diacritic": "\u0309",
        "contour": "dipping_rising",
        "ipa": "313",
        "description": "Thanh hỏi (trầm thăng / giáng thăng, dấu hỏi)",
        "svs_singing_hint": "Chùng nhẹ cao độ xuống ở giữa rồi lượn nhẹ lên lại ở đuôi âm tiết.",
    },
    ToneType.NGA.value: {
        "name": "ngã",
        "diacritic": "\u0303",
        "contour": "broken_rising",
        "ipa": "305",
        "description": "Thanh ngã (cao gãy, dấu ngã)",
        "svs_singing_hint": "Lên cao có độ nghẽn nhẹ thanh môn (glottal catch) trước khi ngân vang.",
    },
    ToneType.NANG.value: {
        "name": "nặng",
        "diacritic": "\u0323",
        "contour": "checked_low",
        "ipa": "21?",
        "description": "Thanh nặng (trầm nhập, dấu nặng)",
        "svs_singing_hint": "Cao độ rơi nhanh xuống cực trầm, khép thanh môn ngắt âm ngắn gọn.",
    },
}

# Danh sách phụ âm đầu tiếng Việt (xếp theo độ dài giảm dần để match greedy)
ONSET_3_CHAR: List[str] = ["ngh"]
ONSET_2_CHAR: List[str] = ["ch", "gh", "gi", "kh", "nh", "ng", "ph", "qu", "th", "tr"]
ONSET_1_CHAR: List[str] = [
    "b", "c", "d", "đ", "g", "h", "k", "l", "m", "n", "p", "r", "s", "t", "v", "x"
]

# Các nguyên âm đôi chính tắc của tiếng Việt
DIPHTHONGS_LIST: List[str] = ["iê", "yê", "ia", "ya", "uô", "ua", "ươ", "ưa"]

# Phụ âm cuối tiếng Việt (xếp theo độ dài giảm dần)
CODA_2_CHAR: List[str] = ["ng", "nh", "ch"]
CODA_1_CHAR: List[str] = ["c", "m", "n", "p", "t", "i", "y", "u", "o"]

# Ký tự nguyên âm đơn tiếng Việt chuẩn (dạng NFC không dấu thanh)
VIETNAMESE_VOWELS: set[str] = {
    "a", "ă", "â", "e", "ê", "i", "y", "o", "ô", "ơ", "u", "ư"
}

# Ký tự cấm trong tiếng Việt thuần túy (ngoại lai)
NON_VIETNAMESE_LETTERS: set[str] = {"f", "j", "w", "z"}

# Regex lọc dấu câu gắn liền ở đầu/cuối từ
PUNCTUATION_REGEX = re.compile(r"^[\s\.,;:!\?\-\"'\(\)\[\]\{\}\<\>…“”‘’«»/\\_]+|[\s\.,;:!\?\-\"'\(\)\[\]\{\}\<\>…“”‘’«»/\\_]+$")


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SyllableAnalysis:
    """
    Cấu trúc dữ liệu phân tích chi tiết của một âm tiết tiếng Việt.
    """
    raw: str                       # Chuỗi gốc nguyên bản nhập vào
    normalized: str                # Chuỗi sau chuẩn hóa Unicode NFC
    onset: str                     # Âm đầu (C1, rỗng nếu zero-onset)
    glide: str                     # Âm đệm (o hoặc u, rỗng nếu không có)
    nucleus: str                   # Âm chính (nguyên âm đơn hoặc đôi)
    coda: str                      # Âm cuối (phụ âm cuối hoặc bán âm cuối)
    tone: int                      # Mã thanh điệu (0-5)
    tone_name: str                 # Tên thanh điệu ('ngang', 'huyền', 'sắc', 'hỏi', 'ngã', 'nặng')
    pitch_contour: str             # Đường nét cao độ ngữ âm ('level', 'falling', 'rising', ...)
    vowel_type: str                # 'monophthong', 'diphthong', 'triphthong'
    acoustic_weight: str           # 'open', 'nasal', 'stop', 'semivowel'
    is_vietnamese: bool            # True nếu là âm tiết tiếng Việt chuẩn
    status: str                    # certain, inferred, non_vietnamese, punctuation, unknown
    confidence: float              # Độ tin cậy (0.0 đến 1.0)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi thành Dictionary chuẩn JSON."""
        return asdict(self)


@dataclass
class LyricLineAnalysis:
    """
    Kết quả phân tích cho một dòng ca từ (verse line).
    """
    line_number: int
    raw_line: str
    normalized_line: str
    syllables: List[SyllableAnalysis]
    syllable_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "raw_line": self.raw_line,
            "normalized_line": self.normalized_line,
            "syllables": [s.to_dict() for s in self.syllables],
            "syllable_count": self.syllable_count,
        }


@dataclass
class LyricAnalysis:
    """
    Kết quả phân tích toàn bộ văn bản ca từ (Lyrics Analysis Report).
    """
    original_text: str
    normalized_text: str
    lines: List[LyricLineAnalysis]
    total_syllables: int
    vietnamese_syllable_count: int
    tone_distribution: Dict[str, int]
    acoustic_distribution: Dict[str, int]
    vowel_distribution: Dict[str, int]
    is_all_vietnamese: bool
    phonetic_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "lines": [line.to_dict() for line in self.lines],
            "total_syllables": self.total_syllables,
            "vietnamese_syllable_count": self.vietnamese_syllable_count,
            "tone_distribution": self.tone_distribution,
            "acoustic_distribution": self.acoustic_distribution,
            "vowel_distribution": self.vowel_distribution,
            "is_all_vietnamese": self.is_all_vietnamese,
            "phonetic_summary": self.phonetic_summary,
        }


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def normalize_nfc(text: str) -> str:
    """
    Chuẩn hóa chuỗi văn bản sang Unicode NFC (Canonical Composition).
    Đảm bảo các ký tự tiếng Việt có dấu luôn ở dạng tổ hợp chuẩn,
    bảo toàn 100% ca từ nguyên bản không bị biến dạng hay mất dấu.
    """
    if not text:
        return ""
    return unicodedata.normalize("NFC", str(text))


def extract_tone(syllable: str) -> Tuple[int, str, str, str]:
    """
    Nhận diện và tách thanh điệu tiếng Việt thông qua phân rã NFD.
    Bảo toàn nguyên bản các dấu chất lượng nguyên âm (ă, â, ê, ô, ơ, ư).

    Returns:
        Tuple[tone_id, tone_name, pitch_contour, base_nfc]
        - tone_id: 0 (ngang), 1 (huyền), 2 (sắc), 3 (hỏi), 4 (ngã), 5 (nặng)
        - tone_name: 'ngang', 'huyền', 'sắc', 'hỏi', 'ngã', 'nặng'
        - pitch_contour: 'level', 'falling', 'rising', 'dipping_rising', 'broken_rising', 'checked_low'
        - base_nfc: Chuỗi âm tiết đã loại bỏ dấu thanh điệu nhưng giữ nguyên nón, móc, trăng (NFC).
    """
    normalized = normalize_nfc(syllable.strip().lower())
    if not normalized:
        return (ToneType.NGANG.value, "ngang", "level", "")

    nfd = unicodedata.normalize("NFD", normalized)
    tone_id = ToneType.NGANG.value
    tone_name = "ngang"
    pitch_contour = "level"

    base_chars: List[str] = []
    for char in nfd:
        if char in TONE_COMBINING_MARKS:
            t_id, t_name, p_cont, _ = TONE_COMBINING_MARKS[char]
            tone_id = t_id
            tone_name = t_name
            pitch_contour = p_cont
        else:
            base_chars.append(char)

    base_nfc = unicodedata.normalize("NFC", "".join(base_chars))
    return (tone_id, tone_name, pitch_contour, base_nfc)


def get_tone_info(tone: Union[int, ToneType]) -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết về thanh điệu và gợi ý tổng hợp giọng hát (SVS).
    """
    tone_val = int(tone)
    return TONE_METADATA.get(tone_val, TONE_METADATA[ToneType.NGANG.value])


def decompose_syllable(token: str) -> SyllableAnalysis:
    """
    Phân tích toàn diện một âm tiết tiếng Việt thành các thành phần ngữ âm:
    Onset, Glide, Nucleus, Coda, Tone, VowelType, AcousticWeight.

    Args:
        token: Từ đơn hoặc âm tiết cần phân tích.

    Returns:
        SyllableAnalysis: Đối tượng chứa toàn bộ kết quả phân tích có cấu trúc.
    """
    raw_str = str(token)
    cleaned_nfc = normalize_nfc(raw_str.strip())

    # Trường hợp rỗng
    if not cleaned_nfc:
        return SyllableAnalysis(
            raw=raw_str,
            normalized="",
            onset="",
            glide="",
            nucleus="",
            coda="",
            tone=ToneType.NGANG.value,
            tone_name="ngang",
            pitch_contour="level",
            vowel_type="monophthong",
            acoustic_weight=AcousticWeight.OPEN.value,
            is_vietnamese=False,
            status=AnalysisStatus.UNKNOWN.value,
            confidence=0.0,
            notes=["Chuỗi rỗng hoặc chỉ có khoảng trắng."],
        )

    # Kiểm tra thuần dấu câu
    if re.fullmatch(r"[\s\.,;:!\?\-\"'\(\)\[\]\{\}\<\>…“”‘’«»/\\_]+", cleaned_nfc):
        return SyllableAnalysis(
            raw=raw_str,
            normalized=cleaned_nfc,
            onset="",
            glide="",
            nucleus="",
            coda="",
            tone=ToneType.NGANG.value,
            tone_name="ngang",
            pitch_contour="level",
            vowel_type="monophthong",
            acoustic_weight=AcousticWeight.OPEN.value,
            is_vietnamese=False,
            status=AnalysisStatus.PUNCTUATION.value,
            confidence=1.0,
            notes=["Ký tự dấu câu / phân cách."],
        )

    # Tách dấu câu bọc quanh từ nếu có (ví dụ: "vắng," -> core="vắng")
    core_word = PUNCTUATION_REGEX.sub("", cleaned_nfc)
    if not core_word:
        core_word = cleaned_nfc

    lower_word = core_word.lower()

    # Kiểm tra ký tự ngoại lai (f, j, w, z)
    has_foreign_letter = any(ch in NON_VIETNAMESE_LETTERS for ch in lower_word)

    # 1. Tách thanh điệu
    tone_id, tone_name, pitch_contour, base_nfc = extract_tone(lower_word)

    # Kiểm tra nếu từ không có nguyên âm tiếng Việt nào
    has_vietnamese_vowel = any(v in base_nfc for v in VIETNAMESE_VOWELS)
    if not has_vietnamese_vowel or has_foreign_letter:
        return SyllableAnalysis(
            raw=raw_str,
            normalized=cleaned_nfc,
            onset=base_nfc,
            glide="",
            nucleus="",
            coda="",
            tone=tone_id,
            tone_name=tone_name,
            pitch_contour=pitch_contour,
            vowel_type="monophthong",
            acoustic_weight=AcousticWeight.OPEN.value,
            is_vietnamese=False,
            status=AnalysisStatus.NON_VIETNAMESE.value,
            confidence=0.2 if has_vietnamese_vowel else 0.0,
            notes=[
                "Chứa ký tự ngoại lai (f, j, w, z)" if has_foreign_letter else "Không tìm thấy nguyên âm tiếng Việt chuẩn."
            ],
        )

    # 2. Tách âm đầu (Onset - C1)
    onset = ""
    rest = base_nfc

    if base_nfc.startswith("qu"):
        onset = "qu"
        rest = base_nfc[2:]
    elif base_nfc.startswith("gi"):
        # Phân tích trường hợp đặc biệt gi-:
        # - "giếng", "giết": onset "gi", rest bắt đầu bằng "iê..."
        # - "gió", "giá", "giúp", "giữa": theo sau bởi nguyên âm khác -> onset "gi", rest từ vị trí 2
        # - "gì", "gìn", "gít": không có nguyên âm nào khác -> con chữ 'i' vừa là âm chính vừa thuộc nhóm gi
        if base_nfc.startswith("giê"):
            onset = "gi"
            rest = "iê" + base_nfc[3:]
        elif len(base_nfc) > 2 and base_nfc[2] in "aăâeêoôơuưy":
            onset = "gi"
            rest = base_nfc[2:]
        else:
            # Các từ như: gì, gí, gĩ, gỉ, gị, gìn, gít
            onset = "gi"
            rest = "i" + base_nfc[2:]
    elif any(base_nfc.startswith(o) for o in ONSET_3_CHAR):
        onset = base_nfc[:3]
        rest = base_nfc[3:]
    elif any(base_nfc.startswith(o) for o in ONSET_2_CHAR):
        for o in ONSET_2_CHAR:
            if base_nfc.startswith(o):
                onset = o
                rest = base_nfc[len(o):]
                break
    elif any(base_nfc.startswith(o) for o in ONSET_1_CHAR):
        onset = base_nfc[:1]
        rest = base_nfc[1:]
    else:
        # Âm tiết mở đầu bằng nguyên âm (Zero Onset: ơi, uống, ánh, yêu, êm, ...)
        onset = ""
        rest = base_nfc

    # 3. Tách âm cuối (Coda - C2)
    coda = ""
    nucleus_and_glide = rest

    found_coda = False
    for c in CODA_2_CHAR:
        if rest.endswith(c) and len(rest) > len(c):
            coda = c
            nucleus_and_glide = rest[:-len(c)]
            found_coda = True
            break

    if not found_coda:
        for c in CODA_1_CHAR:
            if rest.endswith(c) and len(rest) > len(c):
                coda = c
                nucleus_and_glide = rest[:-len(c)]
                break

    # 4. Tách âm đệm (Glide) và âm chính (Nucleus)
    glide = ""
    nucleus = nucleus_and_glide

    if onset == "qu":
        # Với âm đầu qu-, âm đệm /-w-/ được ghi bằng con chữ 'u'
        glide = "u"
    elif len(nucleus_and_glide) > 1:
        # Âm đệm 'o' trước a, ă, e (hoa, hoặc, hoè, loạng, xoài)
        if nucleus_and_glide.startswith("o") and len(nucleus_and_glide) >= 2 and nucleus_and_glide[1] in "aăe":
            glide = "o"
            nucleus = nucleus_and_glide[1:]
        # Âm đệm 'u' trước y, ê, ơ, â, a (thuở, thuế, xuân, khuỷu, khuyên)
        elif nucleus_and_glide.startswith("u") and len(nucleus_and_glide) >= 2 and nucleus_and_glide[1] in "yêơâa":
            # Ngoại trừ nguyên âm đôi uô và ua (buông, mùa, úa)
            if not (nucleus_and_glide.startswith("uô") or nucleus_and_glide == "ua"):
                glide = "u"
                nucleus = nucleus_and_glide[1:]

    # 5. Phân loại cấu trúc nguyên âm (Vowel Type)
    vowel_type = VowelType.MONOPHTHONG.value
    if nucleus in DIPHTHONGS_LIST:
        if (coda in ["i", "y", "u", "o"]) or glide:
            vowel_type = VowelType.TRIPHTHONG.value
        else:
            vowel_type = VowelType.DIPHTHONG.value
    elif (glide and coda in ["i", "y", "u", "o"]) or len(nucleus) >= 3:
        vowel_type = VowelType.TRIPHTHONG.value

    # 6. Phân loại trọng số âm học (Acoustic Weight)
    if not coda:
        acoustic_weight = AcousticWeight.OPEN.value
    elif coda in ["ng", "nh", "m", "n"]:
        acoustic_weight = AcousticWeight.NASAL.value
    elif coda in ["c", "ch", "p", "t"]:
        acoustic_weight = AcousticWeight.STOP.value
    else:
        acoustic_weight = AcousticWeight.SEMIVOWEL.value

    # 7. Đánh giá tính chuẩn xác ngữ âm và trạng thái tin cậy theo luật kết hợp tiếng Việt
    notes: List[str] = []
    is_vietnamese = True
    status = AnalysisStatus.CERTAIN.value
    confidence = 1.0

    # Tất cả các phụ âm tiếng Việt
    vietnamese_consonants = {
        "b", "c", "d", "đ", "g", "h", "k", "l", "m", "n", "p", "r", "s", "t", "v", "x"
    }

    # Kiểm tra 1: Sau âm đầu, phần còn lại có bắt đầu bằng phụ âm không (cụm phụ âm ngoại lai như st-, sp-, cl-)
    if rest and rest[0] in vietnamese_consonants:
        is_vietnamese = False
        status = AnalysisStatus.NON_VIETNAMESE.value
        confidence = 0.1
        notes.append(f"Chứa cụm phụ âm đầu ngoại lai không tồn tại trong tiếng Việt ('{onset}{rest[0]}').")

    # Kiểm tra 2: Âm chính có thuộc tập nguyên âm hợp lệ của tiếng Việt không
    elif not nucleus or (nucleus not in VIETNAMESE_VOWELS and nucleus not in DIPHTHONGS_LIST):
        is_vietnamese = False
        status = AnalysisStatus.NON_VIETNAMESE.value
        confidence = 0.2
        notes.append(f"Tổ hợp nguyên âm '{nucleus}' không phải nguyên âm tiếng Việt chuẩn.")

    # Kiểm tra 3: Quy tắc âm tiết tắc khép (Checked Syllable):
    # Trong tiếng Việt, âm cuối tắc (-p, -t, -c, -ch) chỉ đi với thanh Sắc (2) hoặc Nặng (5)
    elif acoustic_weight == AcousticWeight.STOP.value and tone_id not in [ToneType.SAC.value, ToneType.NANG.value]:
        is_vietnamese = False
        status = AnalysisStatus.NON_VIETNAMESE.value
        confidence = 0.2
        notes.append(
            f"Âm cuối tắc (-{coda}) đi với thanh {tone_name} không hợp lệ trong tiếng Việt chính tắc (từ ngoại lai hoặc thiếu dấu)."
        )

    return SyllableAnalysis(
        raw=raw_str,
        normalized=cleaned_nfc,
        onset=onset,
        glide=glide,
        nucleus=nucleus,
        coda=coda,
        tone=tone_id,
        tone_name=tone_name,
        pitch_contour=pitch_contour,
        vowel_type=vowel_type,
        acoustic_weight=acoustic_weight,
        is_vietnamese=is_vietnamese,
        status=status,
        confidence=confidence,
        notes=notes,
    )


def analyze_lyrics(lyrics: str) -> LyricAnalysis:
    """
    Phân tích toàn diện văn bản ca từ (Lyrics) nhiều dòng.
    Bảo toàn toàn bộ cấu trúc nguyên văn, thống kê thanh điệu, trọng số âm học
    và xuất báo cáo ngữ âm phục vụ SVS.
    """
    raw_text = str(lyrics)
    norm_text = normalize_nfc(raw_text)

    lines_raw = norm_text.splitlines()
    analyzed_lines: List[LyricLineAnalysis] = []

    total_syllables = 0
    vietnamese_count = 0

    tone_distribution: Dict[str, int] = {
        "ngang": 0, "huyền": 0, "sắc": 0, "hỏi": 0, "ngã": 0, "nặng": 0
    }
    acoustic_distribution: Dict[str, int] = {
        "open": 0, "nasal": 0, "stop": 0, "semivowel": 0
    }
    vowel_distribution: Dict[str, int] = {
        "monophthong": 0, "diphthong": 0, "triphthong": 0
    }

    line_idx = 1
    for line in lines_raw:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        tokens = stripped_line.split()
        syllables: List[SyllableAnalysis] = []

        for token in tokens:
            analysis = decompose_syllable(token)
            syllables.append(analysis)

            # Chỉ thống kê các từ không phải dấu câu
            if analysis.status != AnalysisStatus.PUNCTUATION.value:
                total_syllables += 1
                if analysis.is_vietnamese:
                    vietnamese_count += 1
                    tone_distribution[analysis.tone_name] = tone_distribution.get(analysis.tone_name, 0) + 1
                    acoustic_distribution[analysis.acoustic_weight] = acoustic_distribution.get(analysis.acoustic_weight, 0) + 1
                    vowel_distribution[analysis.vowel_type] = vowel_distribution.get(analysis.vowel_type, 0) + 1

        analyzed_lines.append(
            LyricLineAnalysis(
                line_number=line_idx,
                raw_line=line,
                normalized_line=stripped_line,
                syllables=syllables,
                syllable_count=len(syllables),
            )
        )
        line_idx += 1

    is_all_vietnamese = (vietnamese_count == total_syllables and total_syllables > 0)

    # Tổng kết ngữ âm
    summary_parts = [
        f"Tổng số âm tiết: {total_syllables}",
        f"Âm tiết tiếng Việt hợp lệ: {vietnamese_count}/{total_syllables} ({vietnamese_count / max(total_syllables, 1) * 100:.1f}%)",
        f"Phân bố thanh điệu: [Ngang: {tone_distribution.get('ngang', 0)}, Huyền: {tone_distribution.get('huyền', 0)}, Sắc: {tone_distribution.get('sắc', 0)}, Hỏi: {tone_distribution.get('hỏi', 0)}, Ngã: {tone_distribution.get('ngã', 0)}, Nặng: {tone_distribution.get('nặng', 0)}]",
        f"Trọng số âm học: [Open (ngân dài): {acoustic_distribution.get('open', 0)}, Nasal (vang mũi): {acoustic_distribution.get('nasal', 0)}, Stop (ngắt tắc): {acoustic_distribution.get('stop', 0)}, Semivowel (bán âm): {acoustic_distribution.get('semivowel', 0)}]",
        f"Cấu trúc nguyên âm: [Đơn: {vowel_distribution.get('monophthong', 0)}, Đôi: {vowel_distribution.get('diphthong', 0)}, Ba: {vowel_distribution.get('triphthong', 0)}]",
    ]
    phonetic_summary = " | ".join(summary_parts)

    return LyricAnalysis(
        original_text=raw_text,
        normalized_text=norm_text,
        lines=analyzed_lines,
        total_syllables=total_syllables,
        vietnamese_syllable_count=vietnamese_count,
        tone_distribution=tone_distribution,
        acoustic_distribution=acoustic_distribution,
        vowel_distribution=vowel_distribution,
        is_all_vietnamese=is_all_vietnamese,
        phonetic_summary=phonetic_summary,
    )


def build_svs_phonetic_prompt(lyrics: str) -> str:
    """
    Tạo phonetic prompt định hướng cho mô hình Singing Voice Synthesis (SVS).
    Bảo toàn 100% ca từ tiếng Việt có dấu, đồng thời bổ sung chú giải thanh điệu [T0-T5],
    đặc tính ngân vang (legato/sustain/staccato) để mô hình AI hát chuẩn dấu thanh và nhịp.
    """
    analysis = analyze_lyrics(lyrics)
    prompt_lines: List[str] = []

    for line in analysis.lines:
        annotated_syllables: List[str] = []
        for syl in line.syllables:
            if not syl.is_vietnamese:
                annotated_syllables.append(syl.raw)
                continue

            # Ký hiệu chú thích ngữ âm SVS: từ[T<tone>_<acoustic_weight>]
            # Ví dụ: Nắng[T2_nasal], chiều[T1_semivowel], ca[T0_open], ngút[T2_stop]
            tag = f"[T{syl.tone}_{syl.acoustic_weight}]"
            annotated_syllables.append(f"{syl.raw}{tag}")

        prompt_lines.append(" ".join(annotated_syllables))

    return "\n".join(prompt_lines)


# Alias tương thích ngược
analyze_syllable = decompose_syllable
SyllablePhonetics = SyllableAnalysis


def detect_repetition_anomalies(text: str, max_repeat: int = 3) -> Tuple[bool, List[str]]:
    """
    Phát hiện hiện tượng lặp từ bất thường (stuttering / repetitive looping anomaly):
    - Kiểm tra lặp lại cùng một từ hoặc cụm từ nhiều lần liên tiếp (> max_repeat).
    - Trả về (has_anomaly, anomaly_list).
    """
    words = text.lower().split()
    if not words:
        return False, []

    anomalies = []
    repeat_count = 1
    prev_word = words[0]

    for w in words[1:]:
        if w == prev_word:
            repeat_count += 1
            if repeat_count > max_repeat:
                anomalies.append(f"Lặp từ bất thường: '{w}' ({repeat_count} lần)")
        else:
            prev_word = w
            repeat_count = 1

    return len(anomalies) > 0, anomalies

