import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from bleeps.cli import EXIT_FAILED, EXIT_OK, EXIT_PROBLEMS, main
from bleeps.recipes import RECIPES
from bleeps.synth import SAMPLE_RATE
from bleeps.wavfile import read_wav, write_wav


def run(*arguments):
    """Runs the command line and returns (exit code, what it printed, what it printed as errors)."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(arguments))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def abrupt_sound(self, name="beep.wav"):
        path = self.root / name
        write_wav(path, [1000.0] * (SAMPLE_RATE // 2))
        return path

    def test_list_names_every_sound(self):
        code, out, _ = run("list")
        self.assertEqual(code, EXIT_OK)
        for recipe in RECIPES:
            self.assertIn(recipe.name, out)

    def test_make_writes_only_the_named_sounds_into_a_folder_it_creates(self):
        target = self.root / "new" / "folder"
        code, out, _ = run("make", "deskBell", "chime", "--out", str(target))
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(sorted(path.name for path in target.iterdir()), ["chime.wav", "deskBell.wav"])
        self.assertIn("chime.wav", out)

    def test_make_with_an_unknown_name_fails_and_says_which_sounds_exist(self):
        code, _, err = run("make", "kazoo", "--out", str(self.root))
        self.assertEqual(code, EXIT_FAILED)
        self.assertIn("kazoo", err)
        self.assertIn("chime", err)

    def test_what_make_writes_passes_check(self):
        run("make", "bell", "gong", "--out", str(self.root))
        code, out, _ = run("check", str(self.root / "bell.wav"), str(self.root / "gong.wav"))
        self.assertEqual(code, EXIT_OK)
        self.assertNotIn("PROBLEM", out)

    def test_check_exits_1_and_names_the_problem_for_a_sound_that_clicks(self):
        code, out, _ = run("check", str(self.abrupt_sound()))
        self.assertEqual(code, EXIT_PROBLEMS)
        self.assertIn("PROBLEM", out)
        self.assertIn("click", out)

    def test_soften_changes_the_file_in_place_then_leaves_it_alone(self):
        path = self.abrupt_sound()
        code, out, _ = run("soften", str(path))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("faded", out)
        self.assertEqual(run("check", str(path))[0], EXIT_OK)

        before = path.read_bytes()
        _, out, _ = run("soften", str(path))
        self.assertIn("already ends softly", out)
        self.assertEqual(path.read_bytes(), before)

    def test_soften_into_a_folder_leaves_the_original_alone(self):
        path = self.abrupt_sound()
        original = path.read_bytes()
        target = self.root / "softened"
        run("soften", str(path), "--out", str(target))
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(run("check", str(target / "beep.wav"))[0], EXIT_OK)

    def test_a_missing_file_is_an_error_not_a_crash(self):
        code, _, err = run("check", str(self.root / "nothing.wav"))
        self.assertEqual(code, EXIT_FAILED)
        self.assertIn("bleeps:", err)

    def test_soften_refuses_a_stereo_file(self):
        import wave

        path = self.root / "stereo.wav"
        with wave.open(str(path), "wb") as file:
            file.setnchannels(2)
            file.setsampwidth(2)
            file.setframerate(SAMPLE_RATE)
            file.writeframes(b"\x01\x00" * 4000)
        code, _, err = run("soften", str(path))
        self.assertEqual(code, EXIT_FAILED)
        self.assertIn("not mono 16-bit", err)


if __name__ == "__main__":
    unittest.main()
