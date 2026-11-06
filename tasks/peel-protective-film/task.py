"""Peel the blue film from its raised tab while holding the loose steel plate in place.
Lay the detached film on the table, entirely outside the plate, and withdraw both hands.
The plate may translate at most 30 mm, rise 5 mm, and rotate or tilt 10 degrees throughout.
"""
from pathlib import Path
import sys

# yam_arena loads task files by path, without adding their directory to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from yam_arena.task_file import Box
from geometry import FILM_NAMES, PLATE_POS, PLATE_SIZE, STRIP_SIZE, TAB_POS, TAB_SIZE, strip_pos
from filmkit import install, trial

SCENE = 'station'
# Trial counts the full second itself so a timeout cannot bypass the hold.
SUCCESS_HOLD_S = 0.0
SCORE_OVER = 'end'
OBJECTS = [Box(name='steel_plate', pos=tuple(map(float, PLATE_POS)), size=tuple(map(float, PLATE_SIZE)),
               mass=.280, color=(.65, .67, .69)),
           Box(name='pull_tab', pos=tuple(map(float, TAB_POS)), size=tuple(map(float, TAB_SIZE)),
               mass=.0015, color=(.03, .2, .85))]
OBJECTS += [Box(name=name, pos=tuple(map(float, strip_pos(i))), size=tuple(map(float, STRIP_SIZE)),
                mass=.00074, color=(.03, .2, .85)) for i, name in enumerate(FILM_NAMES[1:])]
install(Path(__file__).resolve())


def score(objects):
    return trial.score(objects)


def success(objects):
    return score(objects) == 1.0


def distance(objects):
    return (13 - trial.peeled) * .01


def demo():
    from yam_arena.demo import Waypoint as W
    z = float(PLATE_POS[2] + PLATE_SIZE[2]/2)
    right = [W(3, (.28, -.062, z+.08), -.015, 'approach tab'),
             W(2, (.28, -.062, z+.016), -.015, 'descend'),
             W(1, (.28, -.062, z+.016), 0., 'grasp'),
             W(2, (.28, -.062, z+.023), 0., 'wait for support'),
             W(15, (.28, -.335, z+.023), 0., 'peel'),
             W(2, (.28, -.335, z+.10), 0., 'lift clear'),
             W(2, (.17, -.30, z+.10), 0., 'carry'),
             W(3, (.17, -.40, z+.016), 0., 'lay out film'),
             W(2, (.17, -.40, z+.016), -.047, 'release'),
             W(1, (.17, -.37, z+.016), -.047, 'slide fingers clear'),
             W(2, (.17, -.37, z+.12), -.047, 'withdraw'),
             W(2, (.17, -.37, z+.12), -.047, 'settle')]
    left = [W(5, (.30, .14, z+.06), 0., 'approach support'),
            W(3, (.30, .14, z+.010), 0., 'press'),
            W(23, (.30, .14, z+.010), 0., 'hold plate'),
            W(2, (.30, .14, z+.12), 0., 'withdraw'),
            W(2, (.30, .14, z+.12), 0., 'settle')]
    return dict(left=left, right=right)
