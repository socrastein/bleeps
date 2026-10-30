import tempfile
import unittest
import wave
from pathlib import Path

from bleeps.check import check_file, rms_of
from bleeps.finish import END_FADE_SECONDS, fade_out
from bleeps.synth import SAMPLE_RATE
from bleeps.wavfile import write_wav


def steady(seconds, level=1000.0):
    return [level] * int(seconds * SAMPLE_RATE)


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def path(self, name="sound.wav"):
        return Path(self.folder.name) / name

    def test_a_well_made_sound_has_no_problems_and_its_measurements_are_reported(self):
        write_wav(self.path(), fade_out(steady(1.0), END_FADE_SECONDS))
        report = check_file(self.path())
        self.assertTrue(report.ok, report.problems)
        self.assertAlmostEqual(report.seconds, 1.0, places=2)
        self.assertEqual(report.peak, 1000)
        self.assertGreater(report.rms, 900)

    def test_a_sound_cut_off_while_loud_is_reported_as_clicking(self):
        write_wav(self.path(), steady(1.0))
        report = check_file(self.path())
        self.assertFalse(report.ok)
        self.assertTrue(any("click" in problem for problem in report.problems))

    def test_a_clipping_sound_is_reported(self):
        write_wav(self.path(), fade_out(steady(1.0, 32767.0), END_FADE_SECONDS))
        report = check_file(self.path())
        self.assertTrue(any("clips" in problem for problem in report.problems))

    def test_a_silent_sound_is_reported(self):
        write_wav(self.path(), [0.0] * SAMPLE_RATE)
        report = check_file(self.path())
        self.assertEqual(report.problems, ["silent"])

    def test_too_short_and_too_long_are_reported(self):
        write_wav(self.path("short.wav"), fade_out(steady(0.01), END_FADE_SECONDS))
        write_wav(self.path("long.wav"), fade_out(steady(5.0), END_FADE_SECONDS))
        self.assertTrue(any("only" in problem for problem in check_file(self.path("short.wav")).problems))
        self.assertTrue(any("long" in problem for problem in check_file(self.path("long.wav")).problems))
        # The limits can be changed
        self.assertTrue(check_file(self.path("long.wav"), max_seconds=10.0).ok)

    def test_the_wrong_sample_rate_is_reported(self):
        # A file made at 44100 Hz, with its end faded at that rate
        write_wav(self.path(), fade_out(steady(1.0), END_FADE_SECONDS, 44100), sample_rate=44100)
        report = check_file(self.path())
        self.assertTrue(any("sample rate" in problem for problem in report.problems))
        # Asked for the rate it really has, the same file is fine
        self.assertTrue(check_file(self.path(), sample_rate=44100).ok)

    def test_a_stereo_file_is_reported_and_nothing_else_is_measured(self):
        with wave.open(str(self.path()), "wb") as file:
            file.setnchannels(2)
            file.setsampwidth(2)
            file.setframerate(SAMPLE_RATE)
            file.writeframes(b"\x01\x00" * 4000)
        report = check_file(self.path())
        self.assertEqual(len(report.problems), 1)
        self.assertIn("not mono 16-bit", report.problems[0])

    def test_rms_of_a_constant_sound_is_that_constant_and_of_nothing_is_zero(self):
        self.assertAlmostEqual(rms_of([3.0, -3.0, 3.0]), 3.0)
        self.assertEqual(rms_of([]), 0.0)


if __name__ == "__main__":
    unittest.main()
