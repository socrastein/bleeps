"""
Compressing finished sounds for the web: a WAV is large for what it holds (a 3-second gong is 130 KB), and an app that keeps every
alert for offline use downloads all of them. MP3 is the compressed format every browser plays, Safari included, and at the mono
64 kbit/s used here an alert sounds the same and is about a fifth of the size.

The encoding itself is done by LAME (https://lame.sourceforge.io/), an outside program, so the rest of this tool keeps to Python's
standard library: only `bleeps compress` needs it installed. Check the WAV first (`bleeps check`); the MP3 is made from it as it is.
"""

import shutil
import subprocess
from pathlib import Path

# The LAME program's name, as it is found on the PATH
ENCODER = "lame"

# Mono at a constant 64 kbit/s: the sounds are mono 22050 Hz, so they hold nothing above 11 kHz, which 64 kbit/s keeps whole.
# Constant, not variable, so every file's size is predictable from its length.
BITRATE_KBPS = 64


def encoder_is_installed():
    """Whether LAME can be found on the PATH."""
    return shutil.which(ENCODER) is not None


def encode_command(source, destination):
    """
    The LAME command that writes `destination` (an MP3) from `source` (a WAV): quiet, mono, at BITRATE_KBPS.

    LAME also writes a header saying how much silence its encoding added at the start and end, which browsers read to play the
    sound without that gap, so an alert still starts on time.
    """
    return [ENCODER, "--quiet", "-m", "m", "-b", str(BITRATE_KBPS), str(source), str(destination)]


def compress(source, output_folder):
    """
    Writes OUTPUT_FOLDER/NAME.mp3 from the WAV at `source` and returns its path. Raises OSError when LAME is not installed or
    fails, with LAME's own message.
    """
    destination = Path(output_folder) / (Path(source).stem + ".mp3")
    if not encoder_is_installed():
        raise OSError(f"{ENCODER} is not installed; `bleeps compress` needs it (https://lame.sourceforge.io/)")
    result = subprocess.run(encode_command(source, destination), capture_output=True, text=True)
    if result.returncode != 0:
        raise OSError(f"{ENCODER} could not encode {Path(source).name}: {result.stderr.strip()}")
    return destination
