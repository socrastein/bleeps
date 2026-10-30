"""
The command line:

    bleeps list                      the sounds it can make
    bleeps make [NAME ...] --out DIR make sounds (all of them if none are named) as DIR/NAME.wav
    bleeps soften FILE ...           fade the end of recorded sounds so they no longer click
    bleeps check FILE ...            check that sound files are well made

Without installing it, run `python3 -m bleeps ...` from the folder that holds the `bleeps` folder.
"""

import argparse
import sys
from pathlib import Path

from bleeps.check import DEFAULT_MAX_SECONDS, DEFAULT_MIN_SECONDS, check_file
from bleeps.finish import scale_to_peak, fade_out, soften, END_FADE_SECONDS
from bleeps.recipes import RECIPES, recipe_named
from bleeps.synth import SAMPLE_RATE
from bleeps.wavfile import read_wav, write_wav

# Exit codes: 0 when all is well, 1 when a check found a problem, 2 when the command could not be carried out
EXIT_OK = 0
EXIT_PROBLEMS = 1
EXIT_FAILED = 2


def command_list(arguments):
    """Prints each sound's name and what it models."""
    for recipe in RECIPES:
        print(f"{recipe.name:14s} {recipe.description}")
    return EXIT_OK


def command_make(arguments):
    """Makes the named sounds (all of them when none are named) into the output folder."""
    if len(arguments.names) == 0:
        recipes = list(RECIPES)
    else:
        try:
            recipes = [recipe_named(name) for name in arguments.names]
        except KeyError as error:
            print(f"bleeps: {error.args[0]}", file=sys.stderr)
            return EXIT_FAILED

    output = Path(arguments.out)
    output.mkdir(parents=True, exist_ok=True)
    for recipe in recipes:
        samples = recipe.make()
        faded = fade_out(samples, END_FADE_SECONDS)
        scaled_samples = scale_to_peak(faded, recipe.peak)
        path = output / f"{recipe.name}.wav"
        size = write_wav(path, scaled_samples)
        print(f"{path.name}: {len(scaled_samples) / SAMPLE_RATE:.2f} s, {size} bytes")
    return EXIT_OK


def command_soften(arguments):
    """Fades the end of each recorded sound, in place or into the output folder. A sound that already ends softly is left alone."""
    output = Path(arguments.out) if arguments.out else None
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)

    status = EXIT_OK
    for name in arguments.files:
        source = Path(name)
        data = read_wav(source)
        if not data.is_mono_16_bit:
            print(f"{source.name}: not mono 16-bit, which is all this knows how to fade", file=sys.stderr)
            status = EXIT_FAILED
            continue

        softened, fade_seconds = soften(data.samples, data.sample_rate)
        destination = source if output is None else output / source.name
        if fade_seconds == 0.0:
            print(f"{source.name}: already ends softly, left as it is")
            if destination != source:
                write_wav(destination, data.samples, data.sample_rate)
            continue
        write_wav(destination, softened, data.sample_rate)
        print(f"{source.name}: end faded over {fade_seconds * 1000:.0f} ms")
    return status


def command_check(arguments):
    """Checks each file and prints one line for it (and a line for each problem). Exits 1 when any file has a problem."""
    status = EXIT_OK
    for name in arguments.files:
        report = check_file(name, arguments.rate, arguments.min_seconds, arguments.max_seconds)
        file_name = Path(name).name
        verdict = "ok" if report.ok else "PROBLEM"
        print(f"{file_name:18s} {report.seconds:5.2f} s  peak {report.peak:5d}  rms {report.rms:6.0f}  {verdict}")
        for problem in report.problems:
            print(f"    {problem}")
        if not report.ok:
            status = EXIT_PROBLEMS
    return status


def build_parser():
    """The argument parser for all four commands."""
    parser = argparse.ArgumentParser(prog="bleeps", description="Makes and finishes small alert sounds.")
    commands = parser.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("list", help="list the sounds it can make")
    listing.set_defaults(run=command_list)

    make = commands.add_parser("make", help="make sounds into a folder")
    make.add_argument("names", nargs="*", help="the sounds to make (default: all of them)")
    make.add_argument("--out", required=True, help="the folder to write NAME.wav files into (made if it is missing)")
    make.set_defaults(run=command_make)

    softening = commands.add_parser("soften", help="fade the end of recorded sounds so they no longer click")
    softening.add_argument("files", nargs="+", help="the WAV files to soften")
    softening.add_argument("--out", help="write the results into this folder instead of changing the files in place")
    softening.set_defaults(run=command_soften)

    checking = commands.add_parser("check", help="check that sound files are well made")
    checking.add_argument("files", nargs="+", help="the WAV files to check")
    checking.add_argument("--rate", type=int, default=SAMPLE_RATE, help=f"the sample rate they should have (default {SAMPLE_RATE})")
    checking.add_argument("--min-seconds", type=float, default=DEFAULT_MIN_SECONDS, help="the shortest a sound may be")
    checking.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS, help="the longest a sound may be")
    checking.set_defaults(run=command_check)
    return parser


def main(argv=None):
    """Runs the command line. Returns the exit code (see EXIT_OK and the others)."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        return arguments.run(arguments)
    except (OSError, EOFError) as error:
        # A missing file, a folder that cannot be written, a file that is not a WAV at all
        print(f"bleeps: {error}", file=sys.stderr)
        return EXIT_FAILED
