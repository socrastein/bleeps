import unittest

from bleeps.synth import HIGHEST_FREQUENCY, SAMPLE_RATE, delayed, mix, scaled, silence, square_wave, strike, tone


class SynthTests(unittest.TestCase):
    def test_silence_lasts_as_long_as_asked_and_is_all_zero(self):
        samples = silence(0.5)
        self.assertEqual(len(samples), SAMPLE_RATE // 2)
        self.assertEqual(set(samples), {0.0})

    def test_tone_has_the_right_length_starts_quiet_and_dies_away(self):
        samples = tone(440.0, 1.0, 0.2)
        self.assertEqual(len(samples), SAMPLE_RATE)
        self.assertEqual(samples[0], 0.0)
        # The first tenth of a second is far stronger than the last
        loud_start = max(abs(sample) for sample in samples[: SAMPLE_RATE // 10])
        quiet_end = max(abs(sample) for sample in samples[-SAMPLE_RATE // 10 :])
        self.assertGreater(loud_start, 5 * quiet_end)

    def test_tone_above_what_the_sample_rate_can_hold_is_silent_instead_of_a_wrong_note(self):
        samples = tone(HIGHEST_FREQUENCY + 1, 0.1, 0.1)
        self.assertEqual(set(samples), {0.0})

    def test_a_slower_attack_makes_the_start_gentler_without_changing_how_long_it_lasts(self):
        partials = [(1.0, 1.0, 1.0)]
        quick = strike(440.0, partials, 0.5)
        slow = strike(440.0, partials, 0.5, attack_seconds=0.08)
        self.assertEqual(len(quick), len(slow))
        first_ten_milliseconds = SAMPLE_RATE // 100
        self.assertGreater(max(abs(sample) for sample in quick[:first_ten_milliseconds]), 2 * max(abs(sample) for sample in slow[:first_ten_milliseconds]))

    def test_scaled_multiplies_every_sample(self):
        self.assertEqual(scaled([1.0, -2.0, 0.5], 2.0), [2.0, -4.0, 1.0])

    def test_mix_adds_sample_by_sample_and_pads_the_shorter_sound_with_silence(self):
        self.assertEqual(mix([1.0, 1.0, 1.0], [2.0]), [3.0, 1.0, 1.0])

    def test_delayed_puts_silence_in_front(self):
        samples = delayed([1.0, 1.0], 0.1)
        delay = int(0.1 * SAMPLE_RATE)
        self.assertEqual(samples[:delay], [0.0] * delay)
        self.assertEqual(samples[delay:], [1.0, 1.0])

    def test_strike_is_a_mix_of_its_partials_and_lasts_the_given_time(self):
        samples = strike(440.0, [(1.0, 1.0, 0.1), (2.0, 0.5, 0.1)], 0.5)
        self.assertEqual(len(samples), SAMPLE_RATE // 2)
        self.assertGreater(max(samples), 0.0)

    def test_square_wave_is_the_same_every_time(self):
        self.assertEqual(square_wave(200.0, 0.01), square_wave(200.0, 0.01))


if __name__ == "__main__":
    unittest.main()
