"""
Reading and writing WAV files, using Python's own `wave` module (which copes with files that carry extra parts, so none of the
header is read by hand).

Sounds are written as mono 16-bit, the plain format every browser and phone plays.
"""

import struct
import wave
from dataclasses import dataclass
from pathlib import Path

from bleeps.synth import SAMPLE_RATE


@dataclass(frozen=True)
class WavData:
    """What a WAV file holds: how it is stored, and its samples as whole numbers (for mono files, one per moment in time)."""

    channels: int
    bits_per_sample: int
    sample_rate: int
    samples: list

    @property
    def is_mono_16_bit(self):
        """True for the one format this tool works with."""
        return self.channels == 1 and self.bits_per_sample == 16

    @property
    def seconds(self):
        """How long the sound lasts."""
        return len(self.samples) / self.sample_rate


def read_wav(path):
    """
    Reads a WAV file. The samples are only decoded for 16-bit files (the rest are described but come back with no samples), so a
    caller can report "this is not 16-bit" instead of failing.
    """
    with wave.open(str(path), "rb") as file:
        channels = file.getnchannels()
        sample_width = file.getsampwidth()
        sample_rate = file.getframerate()
        frames = file.readframes(file.getnframes())

    bits_per_sample = sample_width * 8
    samples = []
    if sample_width == 2:
        count = len(frames) // 2
        samples = list(struct.unpack(f"<{count}h", frames))
    return WavData(channels=channels, bits_per_sample=bits_per_sample, sample_rate=sample_rate, samples=samples)


def write_wav(path, samples, sample_rate=SAMPLE_RATE):
    """
    Writes samples as a mono 16-bit WAV file, rounding each to a whole number. Nothing is scaled: set the loudness first
    (finish.scale_to_peak). Returns the size of the file in bytes.
    """
    rounded = [int(round(sample)) for sample in samples]
    data = b"".join(struct.pack("<h", value) for value in rounded)
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        file.writeframes(data)
    return Path(path).stat().st_size
