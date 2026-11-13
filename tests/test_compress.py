import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bleeps import compress as compress_module
from bleeps.compress import BITRATE_KBPS, compress, encode_command, encoder_is_installed
from bleeps.synth import SAMPLE_RATE
from bleeps.wavfile import write_wav
from tests.test_cli import run


class EncodeCommandTests(unittest.TestCase):
    def test_asks_lame_for_quiet_mono_at_the_fixed_bitrate(self):
        command = encode_command("in/gong.wav", "out/gong.mp3")
        self.assertEqual(command, ["lame", "--quiet", "-m", "m", "-b", str(BITRATE_KBPS), "in/gong.wav", "out/gong.mp3"])


class CompressTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.source = self.root / "beep.wav"
        # Half a second of a quiet tone that fades to nothing, as a finished sound would
        samples = [3000.0 * (1 - index / (SAMPLE_RATE // 2)) for index in range(SAMPLE_RATE // 2)]
        write_wav(self.source, samples)

    def test_says_what_is_missing_when_lame_is_not_installed(self):
        with mock.patch.object(compress_module.shutil, "which", return_value=None):
            with self.assertRaisesRegex(OSError, "lame is not installed"):
                compress(self.source, self.root)

    @unittest.skipUnless(encoder_is_installed(), "LAME is not installed here")
    def test_writes_a_smaller_mp3_named_after_the_wav(self):
        destination = compress(self.source, self.root)
        self.assertEqual(destination, self.root / "beep.mp3")
        self.assertLess(destination.stat().st_size, self.source.stat().st_size)
        # An MP3 starts with an ID3 tag or a frame sync (eleven set bits)
        start = destination.read_bytes()[:3]
        self.assertTrue(start == b"ID3" or (start[0] == 0xFF and start[1] & 0xE0 == 0xE0))

    @unittest.skipUnless(encoder_is_installed(), "LAME is not installed here")
    def test_the_command_line_compresses_into_a_folder_it_creates(self):
        target = self.root / "web"
        code, out, _ = run("compress", str(self.source), "--out", str(target))
        self.assertEqual(code, 0)
        self.assertTrue((target / "beep.mp3").exists())
        self.assertIn("beep.mp3", out)

    def test_the_command_line_fails_cleanly_without_lame(self):
        with mock.patch.object(compress_module.shutil, "which", return_value=None):
            code, _, err = run("compress", str(self.source), "--out", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("not installed", err)
