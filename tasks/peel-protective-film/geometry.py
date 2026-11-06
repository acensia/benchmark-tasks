"""Physical dimensions shared by the scene, cohesive model, and scorer (SI units)."""
import itertools
import numpy as np

TABLE_Z = 0.7475
PLATE_SIZE = np.array([0.10, 0.35, 0.001])
PLATE_POS = np.array([0.28, -0.01, TABLE_Z + PLATE_SIZE[2]/2])
STRIP_SIZE = np.array([0.08, 0.01, 0.001])
TAB_SIZE = np.array([0.08, 0.02, 0.001])
N = 13
FILM_Z = TABLE_Z + PLATE_SIZE[2] + STRIP_SIZE[2]/2
CREASE_Y = -0.055
TAB_ANGLE = np.deg2rad(110)  # +y edge leans toward -y, 70 degrees above the plate
TAB_QUAT = np.array([np.sin(TAB_ANGLE / 2), 0., 0., np.cos(TAB_ANGLE / 2)])
TAB_POS = np.array([0.28, CREASE_Y + 0.01 * np.cos(TAB_ANGLE),
                    FILM_Z + 0.01 * np.sin(TAB_ANGLE)])
FILM_NAMES = ('pull_tab',) + tuple(f'film_{i:02d}' for i in range(N))
SIZES = dict(steel_plate=PLATE_SIZE, pull_tab=TAB_SIZE,
             **{name: STRIP_SIZE for name in FILM_NAMES[1:]})


def rotation(q):
    """Quaternion xyzw to rotation; reject invalid observations instead of awarding credit."""
    q = np.asarray(q, dtype=float)
    if q.shape != (4,) or not np.all(np.isfinite(q)) or np.linalg.norm(q) < 1e-9:
        raise ValueError('invalid quaternion')
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def corners(state, size):
    local = np.array(list(itertools.product((-0.5, 0.5), repeat=3))) * size
    return local @ rotation(state.quat_xyzw).T + np.asarray(state.pos)


def strip_pos(i):
    return np.array([0.28, CREASE_Y - (i + 0.5) * 0.01, FILM_Z])
