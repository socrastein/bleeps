"""
Finishing a sound: setting its loudness and fading its end.

Loudness has two measures, and they disagree for sounds of different kinds. The PEAK is the biggest single sample; the RMS (the
average strength over the whole sound) is much closer to how loud something seems. A sound that dies away, like a bell, has a high
peak and a low RMS, so at the same peak it seems much quieter than a steady buzz. That is why recipes carry their own peak
instead of every sound being scaled to the same one.
"""

from bleeps.synth import SAMPLE_RATE

# How long the last part of a sound is faded out, so it does not end with a click
END_FADE_SECONDS = 0.03

# A sound whose last half millisecond is quieter than this share of its peak already ends softly. A sound faded over 30 ms ends
# below 2% by then, and one cut off while still loud is above 5%, so 3% tells the two apart.
ALREADY_SOFT_SHARE = 0.03

# The tail looked at to decide whether a sound ends softly, in seconds
ENDING_WINDOW_SECONDS = 0.0005

# The largest value a 16-bit sample can hold
MAX_SAMPLE = 32767


def loudest_sample(samples):
    """The biggest sample, ignoring sign: the sound's peak."""
    return max(abs(sample) for sample in samples)


def scale_to_peak(samples, peak):
    """The sound made louder or quieter so its loudest point is exactly `peak` (16-bit samples top out at 32767)."""
    loudest = loudest_sample(samples)
    factor = peak / loudest
    return [sample * factor for sample in samples]


def fade_out(samples, seconds, sample_rate=SAMPLE_RATE):
    """
    The sound with its last `seconds` brought smoothly down to nothing. A sound that is simply cut off ends with a click; this is
    what stops that. A sound shorter than the fade is faded along its whole length.
    """
    count = min(len(samples), int(seconds * sample_rate))
    faded = list(samples)
    for number in range(count):
        position = len(samples) - count + number
        faded[position] = samples[position] * (1.0 - (number + 1) / count)
    return faded


def ending_level_share(samples, sample_rate=SAMPLE_RATE):
    """How loud the very end of the sound is, as a share of its peak (0 is silent, 1 is as loud as its loudest point)."""
    window = int(ENDING_WINDOW_SECONDS * sample_rate)
    ending = samples[-window:]
    loudest = loudest_sample(samples)
    if loudest == 0:
        return 0.0
    return loudest_sample(ending) / loudest


def ends_softly(samples, sample_rate=SAMPLE_RATE):
    """True when the sound's end is already quiet enough not to click."""
    return ending_level_share(samples, sample_rate) <= ALREADY_SOFT_SHARE


def soften(samples, sample_rate=SAMPLE_RATE):
    """
    Fades the end of a sound so it no longer ends with a click, once.

    The fade is END_FADE_SECONDS long, or a quarter of the sound if that is shorter (a very short beep would otherwise be mostly
    fade). A sound that already ends softly comes back exactly as it was, so softening twice never fades it a second time.

    Returns the sound and how long the fade was in seconds (0.0 when nothing was changed).
    """
    if ends_softly(samples, sample_rate):
        return samples, 0.0
    seconds = len(samples) / sample_rate
    fade_seconds = min(END_FADE_SECONDS, seconds / 4)
    faded = fade_out(samples, fade_seconds, sample_rate)
    return faded, fade_seconds
