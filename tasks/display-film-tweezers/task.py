"""Remove the protective film from a smartphone screen; the phone is clamped in a loose carrier.
Use the passive tweezers to grasp the film's folded end in the relief channel. Lay the detached film
entirely outside the carrier, return the tweezers upright to their stand, and
withdraw both hands. Throughout the trial the carrier must stay within 30 mm
horizontally, 5 mm vertically, and 10 degrees of its starting orientation.
"""
from pathlib import Path
import sys

# yam_arena loads task files by path, without adding their directory to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from yam_arena.task_file import Box
from geometry import FILM_NAMES, CARRIER_POS, CARRIER_SIZE, STRIP_SIZE, END_POS, END_SIZE, strip_pos
from fixture_geometry import FILM_COLOR
from filmkit import install, trial

SCENE = 'station'
# Trial counts the full second itself so a timeout cannot bypass the hold.
SUCCESS_HOLD_S = 0.0
SCORE_OVER = 'end'
OBJECTS = [Box(name='carrier', pos=tuple(map(float, CARRIER_POS)), size=tuple(map(float, CARRIER_SIZE)),
               mass=.250, color=(.12, .15, .18)),
           Box(name='film_end', pos=tuple(map(float, END_POS)), size=tuple(map(float, END_SIZE)),
               mass=.003, color=FILM_COLOR)]
OBJECTS += [Box(name=name, pos=tuple(map(float, strip_pos(i))), size=tuple(map(float, STRIP_SIZE)),
                mass=.0003, color=FILM_COLOR) for i, name in enumerate(FILM_NAMES[1:])]
from tool_geometry import tool_objects
OBJECTS += tool_objects()
install(Path(__file__).resolve())


def score(objects):
    return trial.score(objects)


def success(objects):
    return score(objects) == 1.0


def distance(objects):
    from geometry import N_BONDED, PITCH
    return (N_BONDED - trial.peeled) * PITCH



from motion import demo
