"""
The checks that tell whether a sound file is well made. A file that fails is not necessarily broken, but it is worth a look: a
click at the end or clipping are things people hear and cannot easily say what is wrong.
"""

import math
from dataclasses import dataclass, field

from bleeps.finish import ALREADY_SOFT_SHARE, MAX_SAMPLE, ending_level_share, loudest_sample
from bleeps.synth import SAMPLE_RATE
from bleeps.wavfile import read_wav

# Shorter than this is a click, not a sound
DEFAULT_MIN_SECONDS = 0.05
# Longer than this would still be ringing when the next alert of a short interval phase starts
DEFAULT_MAX_SECONDS = 4.0


@dataclass(frozen=True)
class Report:
    """The result of checking one file: its measurements, and what is wrong with it (nothing, if it is fine)."""

    path: str
    seconds: float
    peak: int
    rms: float
    problems: list = field(default_factory=list)

    @property
    def ok(self):
        """True when nothing is wrong."""
        return len(self.problems) == 0


def rms_of(samples):
    """The average strength of the sound over its whole length: the best simple measure of how loud it seems."""
    if len(samples) == 0:
        return 0.0
    total = sum(sample * sample for sample in samples)
    return math.sqrt(total / len(samples))


def check_file(path, sample_rate=SAMPLE_RATE, min_seconds=DEFAULT_MIN_SECONDS, max_seconds=DEFAULT_MAX_SECONDS):
    """
    Checks one WAV file.

    It must be mono 16-bit at `sample_rate`, between `min_seconds` and `max_seconds` long, never clip (reach the largest value a
    16-bit sample can hold, where the sound is cut flat), not be silent, and end softly (see finish.ends_softly).
    """
    data = read_wav(path)
    problems = []

    if not data.is_mono_16_bit:
        problems.append(f"not mono 16-bit (it is {data.channels} channel(s), {data.bits_per_sample}-bit)")
        return Report(str(path), data.seconds, 0, 0.0, problems)

    if data.sample_rate != sample_rate:
        problems.append(f"sample rate is {data.sample_rate} Hz, not {sample_rate} Hz")

    seconds = data.seconds
    if seconds < min_seconds:
        problems.append(f"only {seconds:.2f} s long (less than {min_seconds} s)")
    if seconds > max_seconds:
        problems.append(f"{seconds:.2f} s long (more than {max_seconds} s)")

    if len(data.samples) == 0 or loudest_sample(data.samples) == 0:
        problems.append("silent")
        return Report(str(path), seconds, 0, 0.0, problems)

    peak = loudest_sample(data.samples)
    if peak >= MAX_SAMPLE:
        problems.append("clips (reaches the largest value a 16-bit sample can hold)")

    ending_share = ending_level_share(data.samples, data.sample_rate)
    if ending_share > ALREADY_SOFT_SHARE:
        percent = round(ending_share * 100)
        problems.append(f"ends abruptly (still at {percent}% of its peak in its last half millisecond), so it clicks")

    return Report(str(path), seconds, peak, rms_of(data.samples), problems)
