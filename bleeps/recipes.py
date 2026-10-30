"""
The sounds bleeps can make. Each recipe is a small function that returns a sound built from the blocks in synth.py, and RECIPES
lists them with the peak level each should be saved at.

To add a sound: write a function (its docstring says what it models), then add a Recipe line to RECIPES. `bleeps check` then
confirms the result is well made.
"""

import math
import random
from dataclasses import dataclass
from typing import Callable

from bleeps.synth import SAMPLE_RATE, delayed, mix, scaled, square_wave, strike, tone

# The peak (biggest sample) of a sound that stays loud for its whole length: about 40% of the 16-bit range. This is the level the
# interval timer's first two sounds, recorded before this tool existed, were at.
STEADY_PEAK = 13106


def chime():
    """Two rising notes, E5 then A5: friendly, and clearly different from a beep."""
    first = tone(659.25, 0.45, 0.12)
    second = delayed(tone(880.0, 0.55, 0.16), 0.17)
    return mix(first, second)


def bell():
    """A struck bell: warm and ringing."""
    partials = [
        # (frequency ratio, loudness, decay in seconds)
        (1.0, 1.0, 0.45),
        (2.0, 0.6, 0.30),
        (2.76, 0.4, 0.22),
        (5.4, 0.25, 0.14),
        (8.93, 0.15, 0.09),
    ]
    return strike(523.25, partials, 1.3)


def buzzer():
    """A low, harsh square-ish tone that is on for a moment: impossible to mistake for the other sounds."""
    frequency = 180.0
    seconds = 0.5
    edge = 0.01
    samples = []
    for index in range(int(seconds * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        # A square wave is the odd harmonics added up; the first four are enough for a rough buzz
        wave_value = sum(math.sin(2 * math.pi * frequency * harmonic * time) / harmonic for harmonic in (1, 3, 5, 7))
        fade_in = min(1.0, time / edge)
        fade_out = min(1.0, (seconds - time) / edge)
        samples.append(fade_in * fade_out * wave_value)
    return samples


# The partials of a typical struck bell, used for the bells below; each recipe picks the note and how long it rings
BELL_PARTIALS = [
    (1.0, 1.0, 0.45),
    (2.0, 0.6, 0.30),
    (2.76, 0.4, 0.22),
    (5.4, 0.25, 0.14),
]


def school_bell():
    """
    The old electric school bell: a clapper hammering a small metal bell about twenty times a second, so the ringing never dies
    down between strikes and the whole thing is one harsh, continuous clamour.
    """
    one_strike = strike(1180.0, BELL_PARTIALS, 0.3, decay_scale=0.18)
    strikes_per_second = 20
    total_strikes = 32
    layers = []
    for number in range(total_strikes):
        # Every other strike a little softer, as a real clapper's does
        loudness = 1.0 if number % 2 == 0 else 0.8
        layers.append(delayed(scaled(one_strike, loudness), number / strikes_per_second))
    return mix(*layers)


def boxing_bell():
    """Three clangs of a big ring bell, close together: the end of a round."""
    one_clang = strike(700.0, BELL_PARTIALS, 0.9, decay_scale=1.1)
    gap_seconds = 0.42
    return mix(one_clang, delayed(one_clang, gap_seconds), delayed(one_clang, 2 * gap_seconds))


def desk_bell():
    """The hotel-desk bell: one bright, high ding."""
    partials = [
        (1.0, 1.0, 0.30),
        (2.32, 0.5, 0.18),
        (4.25, 0.3, 0.12),
    ]
    return strike(2093.0, partials, 0.9)


def bike_bell():
    """
    A bicycle bell: two quick rings. Each ring is two high notes a little apart, and the two notes beating against each other is
    what makes the shimmer.
    """
    def ring():
        return mix(tone(3120.0, 0.35, 0.10), tone(3290.0, 0.35, 0.10))

    return mix(ring(), delayed(ring(), 0.2))


def cowbell():
    """The cowbell: two square waves a fifth apart that start loud and drop quickly, leaving a short hollow tail."""
    seconds = 0.6
    layers = []
    for frequency in (540.0, 800.0):
        wave_samples = square_wave(frequency, seconds)
        shaped = []
        for index, sample in enumerate(wave_samples):
            time = index / SAMPLE_RATE
            envelope = 0.7 * math.exp(-time / 0.06) + 0.3 * math.exp(-time / 0.25)
            edge = min(1.0, time / 0.002)
            shaped.append(sample * envelope * edge)
        layers.append(shaped)
    return mix(*layers)


# How long a gong takes to swell to full strength: a soft mallet on a large sheet of metal, so about six hundredths of a second
GONG_ATTACK_SECONDS = 0.06


def gong():
    """A low gong: a struck sheet of metal whose partials slowly drift apart, with a long, shimmering tail."""
    partials = [
        (1.0, 1.0, 1.4),
        (1.47, 0.7, 1.1),
        (2.09, 0.6, 0.9),
        (2.56, 0.4, 0.7),
        (3.2, 0.3, 0.5),
        (4.13, 0.2, 0.4),
    ]
    # A slow attack: a gong is swelled by the mallet, not clicked
    return strike(180.0, partials, 3.0, attack_seconds=GONG_ATTACK_SECONDS)


def pea_whistle():
    """
    A referee's pea whistle: a high steady note that scoops up at the start, a little breath, and the quick flutter the pea
    makes as it rolls about inside.
    """
    rng = random.Random(7)
    seconds = 0.7
    attack = 0.015
    release = 0.04
    phase = 0.0
    samples = []
    for index in range(int(seconds * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        # The pitch starts low and rises into the note within a few hundredths of a second
        frequency = 2950.0 - 250.0 * math.exp(-time / 0.03)
        phase += 2 * math.pi * frequency / SAMPLE_RATE
        note = math.sin(phase) + 0.2 * math.sin(2 * phase)
        flutter = 1.0 + 0.5 * math.sin(2 * math.pi * 32.0 * time)
        breath = 0.12 * rng.uniform(-1.0, 1.0)
        fade_in = min(1.0, time / attack)
        fade_out = min(1.0, (seconds - time) / release)
        samples.append(fade_in * fade_out * (note * flutter + breath))
    return samples


def train_whistle():
    """A steam train whistle: a chord that swells in with a slight scoop, holds, and lets go slowly."""
    rng = random.Random(11)
    seconds = 1.4
    attack = 0.15
    release_start = 1.0
    release = 0.4
    chord = (392.0, 493.88, 587.33)
    phases = [0.0] * len(chord)
    samples = []
    for index in range(int(seconds * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        scoop = 1.0 - 0.04 * math.exp(-time / 0.1)
        value = 0.0
        for number, frequency in enumerate(chord):
            phases[number] += 2 * math.pi * frequency * scoop / SAMPLE_RATE
            value += math.sin(phases[number]) + 0.3 * math.sin(2 * phases[number])
        value += 0.1 * rng.uniform(-1.0, 1.0)
        swell = min(1.0, time / attack)
        # Smoothly rounded, not a straight line, so the swell sounds like air building up
        swell = swell * swell * (3.0 - 2.0 * swell)
        let_go = 1.0 if time < release_start else max(0.0, 1.0 - (time - release_start) / release)
        samples.append(swell * let_go * value)
    return samples


def air_horn():
    """An air horn: two harsh buzzing notes sounded together, starting at once and cut off quickly at the end."""
    seconds = 0.9
    attack = 0.008
    release = 0.08
    samples = []
    for index in range(int(seconds * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        value = 0.0
        for fundamental in (415.0, 523.0):
            for harmonic in range(1, 8):
                value += math.sin(2 * math.pi * fundamental * harmonic * time) / harmonic ** 0.8
        fade_in = min(1.0, time / attack)
        fade_out = min(1.0, (seconds - time) / release)
        samples.append(fade_in * fade_out * value)
    return samples


def alarm_clock():
    """A digital alarm clock: groups of four quick beeps with a pause between the groups."""
    def beep():
        seconds = 0.075
        edge = 0.005
        samples = []
        for index in range(int(seconds * SAMPLE_RATE)):
            time = index / SAMPLE_RATE
            value = math.sin(2 * math.pi * 2200.0 * time) + 0.3 * math.sin(2 * math.pi * 6600.0 * time)
            fade_in = min(1.0, time / edge)
            fade_out = min(1.0, (seconds - time) / edge)
            samples.append(fade_in * fade_out * value)
        return samples

    def group():
        beeps = []
        for number in range(4):
            beeps.append(delayed(beep(), number * 0.15))
        return mix(*beeps)

    return mix(group(), delayed(group(), 0.95))


@dataclass(frozen=True)
class Recipe:
    """A named sound: how to make it, and the peak level to save it at."""

    name: str
    make: Callable[[], list]
    # The biggest sample the saved sound should have. Steady sounds use STEADY_PEAK. A sound that dies away (a bell) is much
    # quieter than a steady one at the same peak, so its recipe sets a higher one (still well short of the 32767 limit) to land
    # at about the same loudness; see finish.py.
    peak: int = STEADY_PEAK

    @property
    def description(self):
        """The recipe function's docstring, on one line."""
        text = self.make.__doc__ or ""
        return " ".join(text.split())


# Every sound, in the order they are listed and made. Names are the file names (without .wav), so they are written the way the apps
# using them name sounds.
RECIPES = [
    Recipe("chime", chime),
    Recipe("bell", bell),
    Recipe("buzzer", buzzer),
    Recipe("schoolBell", school_bell),
    Recipe("boxingBell", boxing_bell, peak=20000),
    Recipe("deskBell", desk_bell, peak=24000),
    Recipe("bikeBell", bike_bell, peak=24000),
    Recipe("cowbell", cowbell, peak=24000),
    Recipe("gong", gong, peak=26000),
    Recipe("whistle", pea_whistle),
    Recipe("trainWhistle", train_whistle),
    Recipe("airHorn", air_horn),
    Recipe("clockAlarm", alarm_clock),
]


def recipe_named(name):
    """The recipe with this name. Raises KeyError, listing the valid names, when there is none."""
    for recipe in RECIPES:
        if recipe.name == name:
            return recipe
    valid = ", ".join(recipe.name for recipe in RECIPES)
    raise KeyError(f"no sound called {name!r}; the sounds are: {valid}")
