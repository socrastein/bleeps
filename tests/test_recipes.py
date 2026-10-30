import unittest

from bleeps.check import DEFAULT_MAX_SECONDS, rms_of
from bleeps.finish import MAX_SAMPLE, END_FADE_SECONDS, ends_softly, fade_out, loudest_sample, scale_to_peak
from bleeps.recipes import RECIPES, recipe_named
from bleeps.synth import SAMPLE_RATE


class RecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Making every sound takes a few seconds, so each is made once and shared by the tests
        cls.finished = {}
        for recipe in RECIPES:
            faded = fade_out(recipe.make(), END_FADE_SECONDS)
            cls.finished[recipe.name] = scale_to_peak(faded, recipe.peak)

    def test_names_are_unique_and_every_recipe_has_a_description(self):
        names = [recipe.name for recipe in RECIPES]
        self.assertEqual(len(names), len(set(names)))
        for recipe in RECIPES:
            self.assertGreater(len(recipe.description), 10, recipe.name)

    def test_every_sound_is_a_sensible_length_and_never_clips(self):
        for recipe in RECIPES:
            samples = self.finished[recipe.name]
            seconds = len(samples) / SAMPLE_RATE
            self.assertGreater(seconds, 0.05, recipe.name)
            self.assertLess(seconds, DEFAULT_MAX_SECONDS, recipe.name)
            self.assertLess(round(loudest_sample(samples)), MAX_SAMPLE, recipe.name)

    def test_every_sound_is_saved_at_its_recipes_peak(self):
        for recipe in RECIPES:
            self.assertAlmostEqual(loudest_sample(self.finished[recipe.name]), recipe.peak, places=3, msg=recipe.name)

    def test_every_sound_ends_softly(self):
        for recipe in RECIPES:
            self.assertTrue(ends_softly(self.finished[recipe.name]), recipe.name)

    def test_sounds_are_loud_enough_to_hear_and_none_is_far_louder_than_another(self):
        # RMS is the fair measure of loudness: the loudest sound should be within about three times the quietest
        levels = {name: rms_of(samples) for name, samples in self.finished.items()}
        self.assertGreater(min(levels.values()), 1500, levels)
        self.assertLess(max(levels.values()) / min(levels.values()), 6.0, levels)

    def test_the_gong_swells_in_rather_than_clicking_in(self):
        # A gong is swelled by a soft mallet: in its first 10 ms it is still far from its full strength
        gong = self.finished["gong"]
        first_ten_milliseconds = gong[: SAMPLE_RATE // 100]
        self.assertLess(loudest_sample(first_ten_milliseconds), 0.25 * loudest_sample(gong))

    def test_making_a_sound_twice_gives_exactly_the_same_sound(self):
        # The whistles use random breath noise, which is seeded so a sound never changes between runs
        for name in ("whistle", "trainWhistle", "chime"):
            recipe = recipe_named(name)
            self.assertEqual(recipe.make(), recipe.make(), name)

    def test_asking_for_an_unknown_sound_lists_the_real_ones(self):
        with self.assertRaises(KeyError) as caught:
            recipe_named("kazoo")
        self.assertIn("chime", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
