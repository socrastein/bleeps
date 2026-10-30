# bleeps

Makes and finishes the small alert sounds an app needs: beeps, bells, whistles, buzzers. Python's standard library only, so there is
nothing to install and no recording to license.

An app should hold only its finished `.wav` files. This tool lives apart from every app, makes the sounds, and checks them; you copy
the results into whichever app wants them.

## Use

You need Python 3.9 or newer and nothing else. From this folder:

```
python3 -m bleeps list                        # the sounds it can make, and what each models
python3 -m bleeps make --out ~/somewhere      # make all of them as ~/somewhere/NAME.wav
python3 -m bleeps make chime gong --out out   # make only these
python3 -m bleeps soften recording.wav        # fade the end of a recording so it does not click (in place)
python3 -m bleeps check app/assets/sounds/*.wav
```

`pip install .` also gives a `bleeps` command, which you can then run from anywhere.

`check` prints one line per file (length, peak, RMS) and a line for each problem, and exits 1 if any file has one, so it can run in a
script. It looks for: a format other than mono 16-bit 22050 Hz, clipping, silence, a length under 0.05 s or over 4 s, and an abrupt
end (a click).

## The sounds

13 are made here: chime, bell, buzzer, schoolBell, boxingBell, deskBell, bikeBell, cowbell, gong, whistle, trainWhistle, airHorn,
clockAlarm. The file name is the sound's name. Every one fades out over its last 30 ms so none ends with a click.

## Two things worth knowing

**Loudness is not peak.** The peak (biggest sample) is easy to match, but a bell that dies away is much quieter than a steady buzz
at the same peak. The RMS (average strength) is much closer to how loud something seems, so recipes that die away are saved at a
higher peak (see `Recipe.peak` in `bleeps/recipes.py`). `check` shows the RMS, so you can compare sounds, including ones this tool
did not make.

**Recorded sounds can be softened.** `soften` fades the end of any mono 16-bit WAV, in place or into another folder (`--out`). A
file that already ends softly is left exactly as it is, so running it twice is harmless.

## Adding a sound

Write a function in `bleeps/recipes.py` that returns a list of samples (build it from the blocks in `bleeps/synth.py`; its docstring
says what it models), then add a `Recipe(...)` line to `RECIPES`. Run `python3 -m bleeps make yourSound --out out` and
`python3 -m bleeps check out/yourSound.wav`.

## Tests

```
python3 -m unittest discover -s tests -t .
```

## Layout

| File | What it holds |
|---|---|
| `bleeps/synth.py` | the building blocks: tones, struck bells, mixing, delaying |
| `bleeps/recipes.py` | the named sounds and the peak each is saved at |
| `bleeps/finish.py` | loudness scaling, the end fade, and the "ends softly" test |
| `bleeps/wavfile.py` | reading and writing mono 16-bit WAV files |
| `bleeps/check.py` | the checks behind `bleeps check` |
| `bleeps/cli.py` | the command line |

## Licence

MIT: use it however you like, for anything. See `LICENSE`.
