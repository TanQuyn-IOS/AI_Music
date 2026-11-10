"""
Sonavia AI - Unit Test Suite for Vietnamese Phonetic Layer
==========================================================
Kiểm thử toàn diện module backend/apps/ai_engine/vietnamese_phonetics.py
theo đúng các yêu cầu của Phase 2.1:
1. Chuẩn hóa 100% Unicode NFC.
2. Bảo tồn nguyên văn ca từ và dấu thanh tiếng Việt.
3. Độ chính xác phân tích âm tiết (Onset, Glide, Nucleus, Coda, Tone).
4. Nhận diện 6 thanh điệu (Ngang, Huyền, Sắc, Hỏi, Ngã, Nặng).
5. Phân loại trọng số âm học (Open, Nasal, Stop, Semivowel).
6. Phân tích nguyên âm đơn, đôi, ba.
7. Xử lý các ngoại lệ và ca từ biên (qu-, gi-, zero-onset, thuở, khuỷu, từ ngoại lai, dấu câu).
8. Bộ ca từ chuẩn 4 câu benchmark.
"""

import json
import sys
import unittest
import unicodedata

# Đảm bảo stdout hiển thị tiếng Việt chuẩn UTF-8 trên Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from apps.ai_engine.vietnamese_phonetics import (
    AcousticWeight,
    AnalysisStatus,
    LyricAnalysis,
    SyllableAnalysis,
    ToneType,
    VowelType,
    analyze_lyrics,
    build_svs_phonetic_prompt,
    decompose_syllable,
    extract_tone,
    get_tone_info,
    normalize_nfc,
)


class TestVietnamesePhoneticsBenchmark(unittest.TestCase):
    """
    Test Case 1: Kiểm thử toàn bộ 32 từ trong 4 câu ca từ Benchmark của Sonavia AI:
    Line 1: Nắng nghiêng chiều buông trên dòng sông vắng
    Line 2: Gió lạnh lùng ru từng nhánh bằng lăng
    Line 3: Gợi nỗi nhớ người thương năm tháng cũ
    Line 4: Khúc tình ca êm ái ngút ngàn xưa
    """

    def test_line_1_decomposition(self):
        # Line 1: Nắng nghiêng chiều buông trên dòng sông vắng
        expected = [
            # raw, onset, glide, nucleus, coda, tone, tone_name, acoustic_weight, vowel_type
            ("Nắng", "n", "", "ă", "ng", 2, "sắc", "nasal", "monophthong"),
            ("nghiêng", "ngh", "", "iê", "ng", 0, "ngang", "nasal", "diphthong"),
            ("chiều", "ch", "", "iê", "u", 1, "huyền", "semivowel", "triphthong"),
            ("buông", "b", "", "uô", "ng", 0, "ngang", "nasal", "diphthong"),
            ("trên", "tr", "", "ê", "n", 0, "ngang", "nasal", "monophthong"),
            ("dòng", "d", "", "o", "ng", 1, "huyền", "nasal", "monophthong"),
            ("sông", "s", "", "ô", "ng", 0, "ngang", "nasal", "monophthong"),
            ("vắng", "v", "", "ă", "ng", 2, "sắc", "nasal", "monophthong"),
        ]
        for raw, on, gl, nuc, cod, tone, tname, ac_wt, v_type in expected:
            res = decompose_syllable(raw)
            self.assertEqual(res.onset, on, f"Onset sai ở từ '{raw}': got '{res.onset}', expected '{on}'")
            self.assertEqual(res.glide, gl, f"Glide sai ở từ '{raw}': got '{res.glide}', expected '{gl}'")
            self.assertEqual(res.nucleus, nuc, f"Nucleus sai ở từ '{raw}': got '{res.nucleus}', expected '{nuc}'")
            self.assertEqual(res.coda, cod, f"Coda sai ở từ '{raw}': got '{res.coda}', expected '{cod}'")
            self.assertEqual(res.tone, tone, f"Tone sai ở từ '{raw}': got {res.tone}, expected {tone}")
            self.assertEqual(res.tone_name, tname, f"Tone name sai ở từ '{raw}': got '{res.tone_name}'")
            self.assertEqual(res.acoustic_weight, ac_wt, f"Acoustic weight sai ở từ '{raw}'")
            self.assertEqual(res.vowel_type, v_type, f"Vowel type sai ở từ '{raw}'")
            self.assertTrue(res.is_vietnamese)
            self.assertEqual(res.status, AnalysisStatus.CERTAIN.value)

    def test_line_2_decomposition(self):
        # Line 2: Gió lạnh lùng ru từng nhánh bằng lăng
        expected = [
            ("Gió", "gi", "", "o", "", 2, "sắc", "open", "monophthong"),
            ("lạnh", "l", "", "a", "nh", 5, "nặng", "nasal", "monophthong"),
            ("lùng", "l", "", "u", "ng", 1, "huyền", "nasal", "monophthong"),
            ("ru", "r", "", "u", "", 0, "ngang", "open", "monophthong"),
            ("từng", "t", "", "ư", "ng", 1, "huyền", "nasal", "monophthong"),
            ("nhánh", "nh", "", "a", "nh", 2, "sắc", "nasal", "monophthong"),
            ("bằng", "b", "", "ă", "ng", 1, "huyền", "nasal", "monophthong"),
            ("lăng", "l", "", "ă", "ng", 0, "ngang", "nasal", "monophthong"),
        ]
        for raw, on, gl, nuc, cod, tone, tname, ac_wt, v_type in expected:
            res = decompose_syllable(raw)
            self.assertEqual(res.onset, on, f"Onset sai ở từ '{raw}': got '{res.onset}', expected '{on}'")
            self.assertEqual(res.glide, gl, f"Glide sai ở từ '{raw}': got '{res.glide}', expected '{gl}'")
            self.assertEqual(res.nucleus, nuc, f"Nucleus sai ở từ '{raw}': got '{res.nucleus}', expected '{nuc}'")
            self.assertEqual(res.coda, cod, f"Coda sai ở từ '{raw}': got '{res.coda}', expected '{cod}'")
            self.assertEqual(res.tone, tone, f"Tone sai ở từ '{raw}': got {res.tone}, expected {tone}")
            self.assertEqual(res.tone_name, tname, f"Tone name sai ở từ '{raw}'")
            self.assertEqual(res.acoustic_weight, ac_wt, f"Acoustic weight sai ở từ '{raw}'")
            self.assertEqual(res.vowel_type, v_type, f"Vowel type sai ở từ '{raw}'")

    def test_line_3_decomposition(self):
        # Line 3: Gợi nỗi nhớ người thương năm tháng cũ
        expected = [
            ("Gợi", "g", "", "ơ", "i", 5, "nặng", "semivowel", "monophthong"),
            ("nỗi", "n", "", "ô", "i", 4, "ngã", "semivowel", "monophthong"),
            ("nhớ", "nh", "", "ơ", "", 2, "sắc", "open", "monophthong"),
            ("người", "ng", "", "ươ", "i", 1, "huyền", "semivowel", "triphthong"),
            ("thương", "th", "", "ươ", "ng", 0, "ngang", "nasal", "diphthong"),
            ("năm", "n", "", "ă", "m", 0, "ngang", "nasal", "monophthong"),
            ("tháng", "th", "", "a", "ng", 2, "sắc", "nasal", "monophthong"),
            ("cũ", "c", "", "u", "", 4, "ngã", "open", "monophthong"),
        ]
        for raw, on, gl, nuc, cod, tone, tname, ac_wt, v_type in expected:
            res = decompose_syllable(raw)
            self.assertEqual(res.onset, on, f"Onset sai ở từ '{raw}': got '{res.onset}', expected '{on}'")
            self.assertEqual(res.glide, gl, f"Glide sai ở từ '{raw}': got '{res.glide}', expected '{gl}'")
            self.assertEqual(res.nucleus, nuc, f"Nucleus sai ở từ '{raw}': got '{res.nucleus}', expected '{nuc}'")
            self.assertEqual(res.coda, cod, f"Coda sai ở từ '{raw}': got '{res.coda}', expected '{cod}'")
            self.assertEqual(res.tone, tone, f"Tone sai ở từ '{raw}': got {res.tone}, expected {tone}")
            self.assertEqual(res.tone_name, tname, f"Tone name sai ở từ '{raw}'")
            self.assertEqual(res.acoustic_weight, ac_wt, f"Acoustic weight sai ở từ '{raw}'")
            self.assertEqual(res.vowel_type, v_type, f"Vowel type sai ở từ '{raw}'")

    def test_line_4_decomposition(self):
        # Line 4: Khúc tình ca êm ái ngút ngàn xưa
        expected = [
            ("Khúc", "kh", "", "u", "c", 2, "sắc", "stop", "monophthong"),
            ("tình", "t", "", "i", "nh", 1, "huyền", "nasal", "monophthong"),
            ("ca", "c", "", "a", "", 0, "ngang", "open", "monophthong"),
            ("êm", "", "", "ê", "m", 0, "ngang", "nasal", "monophthong"),
            ("ái", "", "", "a", "i", 2, "sắc", "semivowel", "monophthong"),
            ("ngút", "ng", "", "u", "t", 2, "sắc", "stop", "monophthong"),
            ("ngàn", "ng", "", "a", "n", 1, "huyền", "nasal", "monophthong"),
            ("xưa", "x", "", "ưa", "", 0, "ngang", "open", "diphthong"),
        ]
        for raw, on, gl, nuc, cod, tone, tname, ac_wt, v_type in expected:
            res = decompose_syllable(raw)
            self.assertEqual(res.onset, on, f"Onset sai ở từ '{raw}': got '{res.onset}', expected '{on}'")
            self.assertEqual(res.glide, gl, f"Glide sai ở từ '{raw}': got '{res.glide}', expected '{gl}'")
            self.assertEqual(res.nucleus, nuc, f"Nucleus sai ở từ '{raw}': got '{res.nucleus}', expected '{nuc}'")
            self.assertEqual(res.coda, cod, f"Coda sai ở từ '{raw}': got '{res.coda}', expected '{cod}'")
            self.assertEqual(res.tone, tone, f"Tone sai ở từ '{raw}': got {res.tone}, expected {tone}")
            self.assertEqual(res.tone_name, tname, f"Tone name sai ở từ '{raw}'")
            self.assertEqual(res.acoustic_weight, ac_wt, f"Acoustic weight sai ở từ '{raw}'")
            self.assertEqual(res.vowel_type, v_type, f"Vowel type sai ở từ '{raw}'")


class TestVietnameseTones(unittest.TestCase):
    """
    Test Case 2: Kiểm thử nhận diện và bảo toàn 6 thanh điệu tiếng Việt.
    """

    def test_six_tones_minimal_pair(self):
        # Cặp tối thiểu: ba, bà, bá, bả, bã, bạ
        minimal_pairs = [
            ("ba", 0, "ngang", "level"),
            ("bà", 1, "huyền", "falling"),
            ("bá", 2, "sắc", "rising"),
            ("bả", 3, "hỏi", "dipping_rising"),
            ("bã", 4, "ngã", "broken_rising"),
            ("bạ", 5, "nặng", "checked_low"),
        ]
        for word, tone_id, tone_name, contour in minimal_pairs:
            t_id, t_name, p_cont, base = extract_tone(word)
            self.assertEqual(t_id, tone_id)
            self.assertEqual(t_name, tone_name)
            self.assertEqual(p_cont, contour)
            self.assertEqual(base, "ba")

            res = decompose_syllable(word)
            self.assertEqual(res.tone, tone_id)
            self.assertEqual(res.tone_name, tone_name)
            self.assertEqual(res.pitch_contour, contour)

    def test_tone_metadata_and_svs_hints(self):
        for tone_id in range(6):
            info = get_tone_info(tone_id)
            self.assertIn("name", info)
            self.assertIn("contour", info)
            self.assertIn("ipa", info)
            self.assertIn("svs_singing_hint", info)

    def test_unicode_nfd_to_nfc_consistency(self):
        # Kiểm tra tính nhất quán giữa chuỗi NFD (tách rời) và NFC (tổ hợp)
        words = ["nắng", "nghiêng", "buông", "người", "khuỷu", "thuở", "cũ", "nặng"]
        for w in words:
            nfc_form = unicodedata.normalize("NFC", w)
            nfd_form = unicodedata.normalize("NFD", w)

            res_nfc = decompose_syllable(nfc_form)
            res_nfd = decompose_syllable(nfd_form)

            self.assertEqual(res_nfc.tone, res_nfd.tone)
            self.assertEqual(res_nfc.tone_name, res_nfd.tone_name)
            self.assertEqual(res_nfc.nucleus, res_nfd.nucleus)
            self.assertEqual(res_nfc.coda, res_nfd.coda)
            self.assertEqual(res_nfc.onset, res_nfd.onset)
            self.assertEqual(res_nfc.normalized, res_nfd.normalized)


class TestComplexOnsetsAndEdgeCases(unittest.TestCase):
    """
    Test Case 3: Kiểm thử các phụ âm đầu đặc biệt và các trường hợp biên phức tạp.
    """

    def test_qu_onset_and_glide(self):
        # Các từ qu-: onset='qu', glide='u'
        qu_cases = [
            ("quanh", "qu", "u", "a", "nh", 0, "ngang"),
            ("quốc", "qu", "u", "ô", "c", 2, "sắc"),
            ("quê", "qu", "u", "ê", "", 0, "ngang"),
            ("quần", "qu", "u", "â", "n", 1, "huyền"),
            ("quý", "qu", "u", "y", "", 2, "sắc"),
            ("quở", "qu", "u", "ơ", "", 3, "hỏi"),
        ]
        for w, on, gl, nuc, cod, tone, tname in qu_cases:
            res = decompose_syllable(w)
            self.assertEqual(res.onset, on)
            self.assertEqual(res.glide, gl)
            self.assertEqual(res.nucleus, nuc)
            self.assertEqual(res.coda, cod)
            self.assertEqual(res.tone, tone)
            self.assertEqual(res.tone_name, tname)

    def test_gi_onset_edge_cases(self):
        # Các từ gi-:
        # - "gió", "giá": onset "gi", glide "", nucleus "o"/"a"
        # - "giếng", "giết": onset "gi", glide "", nucleus "iê"
        # - "gì", "gìn", "gít": onset "gi", glide "", nucleus "i"
        gi_cases = [
            ("gió", "gi", "", "o", "", 2, "sắc"),
            ("giá", "gi", "", "a", "", 2, "sắc"),
            ("giếng", "gi", "", "iê", "ng", 2, "sắc"),
            ("giết", "gi", "", "iê", "t", 2, "sắc"),
            ("gì", "gi", "", "i", "", 1, "huyền"),
            ("gìn", "gi", "", "i", "n", 1, "huyền"),
            ("gít", "gi", "", "i", "t", 2, "sắc"),
            ("giúp", "gi", "", "u", "p", 2, "sắc"),
            ("giữa", "gi", "", "ưa", "", 4, "ngã"),
        ]
        for w, on, gl, nuc, cod, tone, tname in gi_cases:
            res = decompose_syllable(w)
            self.assertEqual(res.onset, on, f"Onset sai ở từ '{w}': got '{res.onset}'")
            self.assertEqual(res.nucleus, nuc, f"Nucleus sai ở từ '{w}': got '{res.nucleus}'")
            self.assertEqual(res.coda, cod, f"Coda sai ở từ '{w}': got '{res.coda}'")
            self.assertEqual(res.tone, tone, f"Tone sai ở từ '{w}'")

    def test_zero_onset_words(self):
        # Từ mở đầu bằng nguyên âm (Zero Onset)
        zero_cases = [
            ("ơi", "", "", "ơ", "i", 0, "ngang", "semivowel"),
            ("uống", "", "", "uô", "ng", 2, "sắc", "nasal"),
            ("yêu", "", "", "yê", "u", 0, "ngang", "semivowel"),
            ("ánh", "", "", "a", "nh", 2, "sắc", "nasal"),
            ("êm", "", "", "ê", "m", 0, "ngang", "nasal"),
            ("ái", "", "", "a", "i", 2, "sắc", "semivowel"),
            ("ước", "", "", "ươ", "c", 2, "sắc", "stop"),
            ("anh", "", "", "a", "nh", 0, "ngang", "nasal"),
            ("em", "", "", "e", "m", 0, "ngang", "nasal"),
        ]
        for w, on, gl, nuc, cod, tone, tname, ac_wt in zero_cases:
            res = decompose_syllable(w)
            self.assertEqual(res.onset, on, f"Onset sai ở từ '{w}'")
            self.assertEqual(res.nucleus, nuc, f"Nucleus sai ở từ '{w}': got '{res.nucleus}'")
            self.assertEqual(res.coda, cod, f"Coda sai ở từ '{w}': got '{res.coda}'")
            self.assertEqual(res.tone, tone, f"Tone sai ở từ '{w}'")
            self.assertEqual(res.acoustic_weight, ac_wt, f"Acoustic weight sai ở từ '{w}'")

    def test_complex_glide_words(self):
        # Các từ có âm đệm phức tạp: thuở, khuỷu, ngoan, ngoài
        cases = [
            ("thuở", "th", "u", "ơ", "", 3, "hỏi", "open"),
            ("khuỷu", "kh", "u", "y", "u", 3, "hỏi", "semivowel"),
            ("ngoài", "ng", "o", "a", "i", 1, "huyền", "semivowel"),
            ("hoa", "h", "o", "a", "", 0, "ngang", "open"),
            ("khuyên", "kh", "u", "yê", "n", 0, "ngang", "nasal"),
            ("chuyện", "ch", "u", "yê", "n", 5, "nặng", "nasal"),
        ]
        for w, on, gl, nuc, cod, tone, tname, ac_wt in cases:
            res = decompose_syllable(w)
            self.assertEqual(res.onset, on, f"Onset sai ở từ '{w}'")
            self.assertEqual(res.glide, gl, f"Glide sai ở từ '{w}': got '{res.glide}'")
            self.assertEqual(res.nucleus, nuc, f"Nucleus sai ở từ '{w}': got '{res.nucleus}'")
            self.assertEqual(res.coda, cod, f"Coda sai ở từ '{w}': got '{res.coda}'")
            self.assertEqual(res.acoustic_weight, ac_wt)


class TestVowelTypesAndAcousticWeight(unittest.TestCase):
    """
    Test Case 4: Kiểm thử phân loại nguyên âm (Đơn, Đôi, Ba) và trọng số âm học (Open, Nasal, Stop, Semivowel).
    """

    def test_monophthong_vowels(self):
        # Nguyên âm đơn
        cases = ["ca", "mẹ", "đi", "ngủ", "bố", "nhà", "nắng", "dòng"]
        for w in cases:
            res = decompose_syllable(w)
            self.assertEqual(res.vowel_type, VowelType.MONOPHTHONG.value, f"Từ '{w}' phải là monophthong")

    def test_diphthong_vowels(self):
        # Nguyên âm đôi: iê/ia, uô/ua, ươ/ưa (không có bán âm cuối và không có âm đệm)
        cases = ["nghiêng", "buông", "thương", "xưa", "mùa", "kia", "biếc", "chùa"]
        for w in cases:
            res = decompose_syllable(w)
            self.assertEqual(res.vowel_type, VowelType.DIPHTHONG.value, f"Từ '{w}' phải là diphthong")

    def test_triphthong_vowels(self):
        # Nguyên âm ba / tổ hợp đệm + đôi hoặc đôi + bán âm
        cases = ["chiều", "người", "khuyên", "khuỷu", "ngoài", "yêu", "loay"]
        for w in cases:
            res = decompose_syllable(w)
            self.assertEqual(res.vowel_type, VowelType.TRIPHTHONG.value, f"Từ '{w}' phải là triphthong")

    def test_acoustic_weights(self):
        # Open: không có âm cuối
        for w in ["ca", "ru", "xưa", "cũ", "nhớ", "kỷ", "hoa", "thuở"]:
            res = decompose_syllable(w)
            self.assertEqual(res.acoustic_weight, AcousticWeight.OPEN.value, f"Từ '{w}' phải là open")

        # Nasal: -m, -n, -ng, -nh
        for w in ["nắng", "buông", "trên", "nhánh", "năm", "lạnh", "êm"]:
            res = decompose_syllable(w)
            self.assertEqual(res.acoustic_weight, AcousticWeight.NASAL.value, f"Từ '{w}' phải là nasal")

        # Stop: -p, -t, -c, -ch
        for w in ["khúc", "ngút", "mắt", "biếc", "đẹp", "thích", "bạc"]:
            res = decompose_syllable(w)
            self.assertEqual(res.acoustic_weight, AcousticWeight.STOP.value, f"Từ '{w}' phải là stop")

        # Semivowel: -i, -y, -u, -o
        for w in ["chiều", "gợi", "nỗi", "người", "nơi", "đáy", "sao", "khuỷu"]:
            res = decompose_syllable(w)
            self.assertEqual(res.acoustic_weight, AcousticWeight.SEMIVOWEL.value, f"Từ '{w}' phải là semivowel")


class TestRobustnessAndNonDestructiveInvariants(unittest.TestCase):
    """
    Test Case 5: Kiểm thử tính bất biến (không làm mất dấu) và độ ổn định với ca từ lỗi/ngoại lệ.
    """

    def test_preserve_lyrics_and_diacritics(self):
        # Đảm bảo ca từ và dấu thanh KHÔNG BAO GIỜ bị xóa hay biến dạng
        original = "Nắng nghiêng chiều buông trên dòng sông vắng\nGió lạnh lùng ru từng nhánh bằng lăng"
        analysis = analyze_lyrics(original)

        self.assertEqual(analysis.original_text, original)
        # Chuẩn hóa NFC giữ nguyên trọn vẹn văn bản
        self.assertEqual(analysis.normalized_text, unicodedata.normalize("NFC", original))
        # Không có từ nào bị mất dấu trong thuộc tính raw và normalized
        raw_words = [s.raw for line in analysis.lines for s in line.syllables]
        self.assertIn("Nắng", raw_words)
        self.assertIn("chiều", raw_words)
        self.assertIn("lạnh", raw_words)

    def test_empty_and_whitespace_input(self):
        res_empty = decompose_syllable("")
        self.assertEqual(res_empty.status, AnalysisStatus.UNKNOWN.value)
        self.assertFalse(res_empty.is_vietnamese)

        res_space = decompose_syllable("   \t  \n ")
        self.assertEqual(res_space.status, AnalysisStatus.UNKNOWN.value)
        self.assertFalse(res_space.is_vietnamese)

    def test_punctuation_handling(self):
        # Dấu câu đứng riêng
        for punct in [",", ".", "!", "?", "--", "...", ";"]:
            res = decompose_syllable(punct)
            self.assertEqual(res.status, AnalysisStatus.PUNCTUATION.value)
            self.assertFalse(res.is_vietnamese)

        # Từ có kèm dấu câu ở cuối (ví dụ: "vắng,")
        res_word = decompose_syllable("vắng,")
        self.assertEqual(res_word.onset, "v")
        self.assertEqual(res_word.nucleus, "ă")
        self.assertEqual(res_word.coda, "ng")
        self.assertEqual(res_word.tone, 2)
        self.assertTrue(res_word.is_vietnamese)

    def test_foreign_and_non_vietnamese_words(self):
        # Các từ tiếng Anh hoặc chứa ký tự ngoại lai (f, j, w, z)
        foreign_words = ["beat", "studio", "rap", "jazz", "show", "wifi", "DJ"]
        for fw in foreign_words:
            res = decompose_syllable(fw)
            self.assertFalse(res.is_vietnamese)
            self.assertEqual(res.status, AnalysisStatus.NON_VIETNAMESE.value)
            self.assertLessEqual(res.confidence, 0.3)

    def test_lyrics_analysis_full_report(self):
        lyrics = """Nắng nghiêng chiều buông trên dòng sông vắng
Gió lạnh lùng ru từng nhánh bằng lăng
Gợi nỗi nhớ người thương năm tháng cũ
Khúc tình ca êm ái ngút ngàn xưa"""

        report = analyze_lyrics(lyrics)
        self.assertEqual(report.total_syllables, 32)
        self.assertEqual(report.vietnamese_syllable_count, 32)
        self.assertTrue(report.is_all_vietnamese)

        # Kiểm tra tone distribution đủ 6 thanh
        self.assertGreater(report.tone_distribution["ngang"], 0)
        self.assertGreater(report.tone_distribution["huyền"], 0)
        self.assertGreater(report.tone_distribution["sắc"], 0)
        self.assertGreater(report.tone_distribution["ngã"], 0)
        self.assertGreater(report.tone_distribution["nặng"], 0)

        # Kiểm tra JSON serializability
        report_dict = report.to_dict()
        json_str = json.dumps(report_dict, ensure_ascii=False)
        self.assertIsInstance(json_str, str)
        self.assertIn("Nắng", json_str)

    def test_build_svs_phonetic_prompt(self):
        lyrics = "Nắng chiều buông"
        prompt = build_svs_phonetic_prompt(lyrics)
        # Kỳ vọng: Nắng[T2_nasal] chiều[T1_semivowel] buông[T0_nasal]
        self.assertIn("Nắng[T2_nasal]", prompt)
        self.assertIn("chiều[T1_semivowel]", prompt)
        self.assertIn("buông[T0_nasal]", prompt)


if __name__ == "__main__":
    unittest.main()
