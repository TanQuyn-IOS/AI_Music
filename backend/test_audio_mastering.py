# -*- coding: utf-8 -*-
"""
Test Suite for Audio Mastering & Vocal Clarity DSP Engine
"""
import sys
import os
import unittest
import numpy as np
import soundfile as sf
import io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.ai_engine.audio_mastering import (
    master_audio_array,
    master_audio_bytes,
    master_audio_file,
)


class AudioMasteringTestCase(unittest.TestCase):

    def setUp(self):
        self.sr = 44100
        self.duration = 2.0  # 2 seconds
        t = np.linspace(0, self.duration, int(self.sr * self.duration), endpoint=False)
        # Synthetic signal: 40Hz (rumble) + 1000Hz (mid) + 3400Hz (vocal presence) + 12000Hz (air)
        sig = (
            0.5 * np.sin(2 * np.pi * 40 * t) +       # sub-bass rumble to cut
            0.3 * np.sin(2 * np.pi * 1000 * t) +     # body
            0.2 * np.sin(2 * np.pi * 3400 * t) +     # vocal presence to boost
            0.1 * np.sin(2 * np.pi * 12000 * t)      # air
        )
        self.mono_signal = sig.astype(np.float32)
        self.stereo_signal = np.stack([sig, sig * 0.9], axis=1).astype(np.float32)

    def test_master_audio_array_peak_normalization(self):
        """Kiểm tra chuẩn hóa True-Peak không vượt quá 0.891 (-1.0 dBFS)"""
        mastered = master_audio_array(self.mono_signal, self.sr, is_vietnamese=True)
        peak = np.max(np.abs(mastered))
        self.assertAlmostEqual(peak, 0.891, places=2)
        self.assertTrue(np.all(np.abs(mastered) <= 0.895), "Âm thanh bị clipping vượt ngưỡng!")
        print("✓ Test Peak Normalization: PASSED (Peak =", peak, ")")

    def test_low_cut_filter_attenuation(self):
        """Kiểm tra bộ lọc cắt dải siêu trầm (<65Hz) trên tín hiệu hỗn hợp"""
        t = np.linspace(0, 1.0, self.sr, endpoint=False)
        # Tín hiệu hỗn hợp: 40Hz (rất mạnh: biên độ 1.0) + 1000Hz (biên độ 0.2)
        mixed_sig = np.sin(2 * np.pi * 40 * t) + 0.2 * np.sin(2 * np.pi * 1000 * t)
        mastered = master_audio_array(mixed_sig, self.sr)

        # Phân tích phổ FFT để kiểm tra tỷ lệ năng lượng 40Hz so với 1000Hz
        fft_orig = np.abs(np.fft.rfft(mixed_sig))
        fft_mast = np.abs(np.fft.rfft(mastered))
        freqs = np.fft.rfftfreq(len(mixed_sig), 1.0 / self.sr)

        idx_40 = np.argmin(np.abs(freqs - 40.0))
        idx_1000 = np.argmin(np.abs(freqs - 1000.0))

        ratio_orig = fft_orig[idx_40] / fft_orig[idx_1000]
        ratio_mast = fft_mast[idx_40] / fft_mast[idx_1000]

        attenuation_factor = ratio_mast / ratio_orig
        print("✓ Test Low-Cut Filter: Attenuation factor of 40Hz relative to 1000Hz =", round(attenuation_factor, 3))
        self.assertTrue(attenuation_factor < 0.50, "Bộ lọc 65Hz chưa suy giảm đủ tần số 40Hz")

    def test_stereo_processing(self):
        """Kiểm tra xử lý tín hiệu Stereo 2 kênh"""
        mastered = master_audio_array(self.stereo_signal, self.sr, is_vietnamese=True)
        self.assertEqual(mastered.shape, self.stereo_signal.shape)
        peak = np.max(np.abs(mastered))
        self.assertAlmostEqual(peak, 0.891, places=2)
        print("✓ Test Stereo Processing: PASSED (Shape =", mastered.shape, ")")

    def test_master_audio_bytes(self):
        """Kiểm tra xử lý trực tiếp mảng bytes trong RAM (WAV & MP3)"""
        wav_buf = io.BytesIO()
        sf.write(wav_buf, self.mono_signal, self.sr, format='WAV')
        raw_bytes = wav_buf.getvalue()

        mastered_bytes = master_audio_bytes(raw_bytes, is_vietnamese=True, output_format='WAV')
        self.assertTrue(len(mastered_bytes) > 1000)

        # Kiểm tra đọc lại audio đã master
        read_data, read_sr = sf.read(io.BytesIO(mastered_bytes))
        self.assertEqual(read_sr, self.sr)
        self.assertAlmostEqual(np.max(np.abs(read_data)), 0.891, places=2)
        print("✓ Test Master Audio Bytes (WAV): PASSED (Bytes length =", len(mastered_bytes), ")")


if __name__ == "__main__":
    unittest.main()
