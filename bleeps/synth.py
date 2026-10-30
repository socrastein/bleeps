"""
The building blocks of a sound. A sound is a list of samples (floats, any size: loudness is set when the sound is saved), and every
block returns one, so blocks combine freely: `mix` adds sounds together, `delayed` starts one later, `strike` makes a struck bell.

Every sound is made at one sample rate, SAMPLE_RATE: 22050 samples a second is plenty for alert sounds (it holds pitches up to
about 10 kHz) and keeps the files small.
"""

import math

# Samples per second. Small alert sounds do not need CD quality, and half the samples is half the file size.
SAMPLE_RATE = 22050

# Nothing above this can be stored at this sample rate (it would fold back down as a wrong, harsh note), so it is left out
HIGHEST_FREQUENCY = SAMPLE_RATE / 2 * 0.95


def silence(seconds):
    """A list of samples, all zero, lasting `seconds`."""
    return [0.0] * int(seconds * SAMPLE_RATE)


def tone(frequency, seconds, decay_seconds, attack_seconds=0.005):
    """
    One sine note: it starts almost at once (the attack avoids a click), then fades out exponentially.

    decay_seconds is how long the note takes to fall to about a third of its starting loudness; small numbers are short, dull
    notes, large numbers ring on.
    """
    if frequency > HIGHEST_FREQUENCY:
        return silence(seconds)
    samples = []
    for index in range(int(seconds * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        attack = min(1.0, time / attack_seconds)
        fade = math.exp(-time / decay_seconds)
        samples.append(attack * fade * math.sin(2 * math.pi * frequency * time))
    return samples


def scaled(samples, factor):
    """The sound, louder or quieter by `factor`."""
    return [factor * sample for sample in samples]


def mix(*layers):
    """Adds sounds together, sample by sample. Shorter sounds are treated as silent after they end."""
    length = max(len(layer) for layer in layers)
    mixed = [0.0] * length
    for layer in layers:
        for index, sample in enumerate(layer):
            mixed[index] += sample
    return mixed


def delayed(samples, seconds):
    """The sound, starting `seconds` later."""
    return silence(seconds) + samples


def strike(base, partials, seconds, decay_scale=1.0, attack_seconds=0.005):
    """
    A struck bell or gong: a base note plus partials that are not whole multiples of it, each dying away at its own speed.

    `partials` is a list of (frequency ratio, loudness, decay in seconds); `decay_scale` makes every decay longer or shorter at once.
    `attack_seconds` is how long the sound takes to swell to full strength: a small hard-struck bell is near instant, a gong swelled by
    a soft mallet takes several hundredths of a second.
    """
    layers = []
    for ratio, loudness, decay in partials:
        note = tone(base * ratio, seconds, decay * decay_scale, attack_seconds)
        layers.append(scaled(note, loudness))
    return mix(*layers)


def square_wave(frequency, seconds):
    """A square-ish wave (the first few odd harmonics), the hollow sound of cheap electronic instruments and cowbells."""
    samples = []
    for index in range(int(seconds * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        value = sum(math.sin(2 * math.pi * frequency * harmonic * time) / harmonic for harmonic in (1, 3, 5))
        samples.append(value)
    return samples
