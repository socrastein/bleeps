"""
bleeps: makes and finishes the small alert sounds an app needs (beeps, bells, whistles, buzzers), using only Python's standard
library, so there is nothing to install and no recording to license.

Run it from the command line (`python3 -m bleeps --help`) and copy the finished .wav files into the app that wants them; the app
itself holds only the sound files, never this code.

The pieces, from the bottom up:
- synth.py: the building blocks of a sound (tones, struck bells, mixing, delaying).
- recipes.py: the named sounds made from those blocks, each with the loudness it should be saved at.
- finish.py: loudness scaling and the fade at the end that stops a sound ending with a click.
- wavfile.py: reading and writing mono 16-bit WAV files.
- check.py: the checks that tell whether a sound file is well made.
- cli.py: the command line (list, make, soften, check).
"""

__version__ = "0.1.0"
