import tempfile
import unittest
import wave
from pathlib import Path

from bleeps.wavfile import read_wav, write_wav


class WavFileTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "sound.wav"

    def test_what_is_written_reads_back_as_mono_16_bit_and_rounded(self):
        size = write_wav(self.path, [0.4, 0.6, -1.5, 32767.0], sample_rate=22050)
        data = read_wav(self.path)
        self.assertTrue(data.is_mono_16_bit)
        self.assertEqual(data.sample_rate, 22050)
        self.assertEqual(data.samples, [0, 1, -2, 32767])
        self.assertEqual(size, self.path.stat().st_size)
        self.assertAlmostEqual(data.seconds, 4 / 22050)

    def test_a_stereo_file_is_described_but_not_decoded_as_mono(self):
        with wave.open(str(self.path), "wb") as file:
            file.setnchannels(2)
            file.setsampwidth(2)
            file.setframerate(44100)
            file.writeframes(b"\x00\x00" * 8)
        data = read_wav(self.path)
        self.assertFalse(data.is_mono_16_bit)
        self.assertEqual(data.channels, 2)

    def test_an_8_bit_file_is_described_with_no_samples(self):
        with wave.open(str(self.path), "wb") as file:
            file.setnchannels(1)
            file.setsampwidth(1)
            file.setframerate(8000)
            file.writeframes(b"\x80" * 8)
        data = read_wav(self.path)
        self.assertEqual(data.bits_per_sample, 8)
        self.assertEqual(data.samples, [])


if __name__ == "__main__":
    unittest.main()
