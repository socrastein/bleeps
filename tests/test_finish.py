import unittest

from bleeps.finish import (
    ALREADY_SOFT_SHARE,
    END_FADE_SECONDS,
    ends_softly,
    ending_level_share,
    fade_out,
    loudest_sample,
    scale_to_peak,
    soften,
)
from bleeps.synth import SAMPLE_RATE


def loud_steady_sound(seconds):
    """A sound at full strength from start to end, which ends abruptly."""
    return [1000.0] * int(seconds * SAMPLE_RATE)


class FinishTests(unittest.TestCase):
    def test_scale_to_peak_makes_the_loudest_sample_exactly_the_peak(self):
        scaled = scale_to_peak([1.0, -4.0, 2.0], 100)
        self.assertEqual(loudest_sample(scaled), 100)
        self.assertEqual(scaled, [25.0, -100.0, 50.0])

    def test_fade_out_leaves_the_start_alone_and_ends_at_exactly_zero(self):
        sound = loud_steady_sound(1.0)
        faded = fade_out(sound, 0.1)
        fade_length = int(0.1 * SAMPLE_RATE)
        self.assertEqual(faded[: len(sound) - fade_length], sound[: len(sound) - fade_length])
        self.assertEqual(faded[-1], 0.0)

    def test_fade_out_comes_down_steadily(self):
        faded = fade_out(loud_steady_sound(1.0), 0.1)
        tail = faded[-int(0.1 * SAMPLE_RATE) :]
        self.assertEqual(tail, sorted(tail, reverse=True))

    def test_fade_out_does_not_change_the_sound_it_was_given(self):
        sound = loud_steady_sound(0.2)
        fade_out(sound, 0.1)
        self.assertEqual(set(sound), {1000.0})

    def test_a_sound_shorter_than_the_fade_is_faded_along_its_whole_length(self):
        faded = fade_out([1.0] * 10, 5.0)
        self.assertEqual(faded[-1], 0.0)
        self.assertLess(faded[0], 1.0)

    def test_a_sound_cut_off_loud_does_not_end_softly_and_a_faded_one_does(self):
        sound = loud_steady_sound(1.0)
        self.assertEqual(ending_level_share(sound), 1.0)
        self.assertFalse(ends_softly(sound))
        self.assertTrue(ends_softly(fade_out(sound, END_FADE_SECONDS)))

    def test_silence_counts_as_ending_softly_and_does_not_divide_by_zero(self):
        self.assertEqual(ending_level_share([0.0] * 100), 0.0)
        self.assertTrue(ends_softly([0.0] * 100))

    def test_soften_fades_a_sound_that_ends_abruptly_and_says_for_how_long(self):
        softened, seconds = soften(loud_steady_sound(1.0))
        self.assertEqual(seconds, END_FADE_SECONDS)
        self.assertTrue(ends_softly(softened))

    def test_soften_uses_a_quarter_of_a_very_short_sound(self):
        _, seconds = soften(loud_steady_sound(0.04))
        self.assertAlmostEqual(seconds, 0.01)

    def test_soften_leaves_a_sound_that_already_ends_softly_exactly_as_it_was(self):
        already_soft = fade_out(loud_steady_sound(1.0), END_FADE_SECONDS)
        result, seconds = soften(already_soft)
        self.assertEqual(seconds, 0.0)
        self.assertIs(result, already_soft)

    def test_softening_twice_gives_the_same_sound_as_softening_once(self):
        once, _ = soften(loud_steady_sound(1.0))
        twice, _ = soften(once)
        self.assertEqual(twice, once)

    def test_the_soft_threshold_separates_a_faded_end_from_a_cut_off_one(self):
        # The numbers the comment in finish.py quotes: faded under 2%, cut off over 5%
        self.assertLess(ending_level_share(fade_out(loud_steady_sound(1.0), END_FADE_SECONDS)), 0.02)
        self.assertGreater(0.05, ALREADY_SOFT_SHARE)


if __name__ == "__main__":
    unittest.main()
