from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from yam_arena.task_file import ObjectState
from geometry import FILM_NAMES, PLATE_POS, SIZES, TABLE_Z, TAB_POS, TAB_QUAT, corners, strip_pos
from scoring import Trial


def state(name, pos, quat=(0., 0., 0., 1.)):
    s = ObjectState(np.array(pos), np.array(quat), np.zeros(3), np.zeros(3), np.zeros(3), np.zeros(3))
    c = corners(s, SIZES[name])
    return ObjectState(s.pos, s.quat_xyzw, s.lin_vel, s.ang_vel, c.min(0), c.max(0))


def initial():
    return dict(steel_plate=state('steel_plate', PLATE_POS),
                pull_tab=state('pull_tab', TAB_POS, TAB_QUAT),
                **{n: state(n, strip_pos(i)) for i, n in enumerate(FILM_NAMES[1:])})


def completed():
    o = initial()
    for i, name in enumerate(FILM_NAMES):
        o[name] = state(name, [.28, -.28-i*.01, TABLE_Z+.0005])
    return o


def settle(t, o, steps=20):
    for _ in range(steps):
        t.observe(o, hands_clear=True)
        t.finish_step(o, .05)


@pytest.mark.parametrize('count,expected', [(0,0), (2,0), (3,.25), (6,.25), (7,.5), (10,.5), (11,.75), (12,.75), (13,.75)])
def test_partial_credit(count, expected):
    t = Trial(); o = initial()
    t.observe(o, hands_clear=True); t.peeled = count
    assert t.score(o) == expected


def test_full_score_requires_disposal_and_withdrawal():
    t = Trial(); o = completed(); t.peeled = 13
    t.observe(o, hands_clear=False)
    assert t.score(o) == .75
    t.observe(o, hands_clear=True)
    settle(t, o)
    assert t.score(o) == 1.


def test_hovering_is_not_disposal():
    t = Trial(); o = completed(); t.peeled = 13
    for name in FILM_NAMES:
        o[name] = state(name, o[name].pos + [0,0,.02])
    t.observe(o, hands_clear=True)
    assert t.score(o) == .75


def test_precreased_tab_may_remain_raised_on_disposed_sheet():
    t = Trial(); o = completed(); t.peeled = 13
    o['pull_tab'] = state('pull_tab', [.28, -.28, TABLE_Z+.011], TAB_QUAT)
    t.observe(o, hands_clear=True)
    settle(t, o)
    assert t.score(o) == 1.


def test_centre_outside_but_edge_overlaps():
    t = Trial(); o = completed(); t.peeled = 13
    o['pull_tab'] = state('pull_tab', [.34, -.10, TABLE_Z+.0005])
    t.observe(o, hands_clear=True)
    assert t.score(o) == .75


@pytest.mark.parametrize('shift', [[.031,0,0], [0,0,.006]])
def test_plate_excursion_cannot_be_undone(shift):
    t = Trial(); o = completed(); t.peeled = 13
    o['steel_plate'] = state('steel_plate', PLATE_POS + shift)
    t.observe(o, hands_clear=True)
    o['steel_plate'] = state('steel_plate', PLATE_POS)
    t.observe(o, hands_clear=True)
    assert t.score(o) == 0.
    t.reset(); t.peeled = 13; t.observe(o, hands_clear=True)
    settle(t, o)
    assert t.score(o) == 1.


def test_timeout_before_one_second_does_not_receive_full_credit():
    t = Trial(); o = completed(); t.peeled = 13
    settle(t, o, 19)
    assert t.score(o) == .75
    # Reading the scorer repeatedly must not advance the hold timer.
    assert t.score(o) == .75
    settle(t, o, 1)
    assert t.score(o) == 1.


def test_disrupted_settling_restarts_full_second():
    t = Trial(); o = completed(); t.peeled = 13
    settle(t, o, 19)
    t.observe(o, hands_clear=False); t.finish_step(o, .05)
    settle(t, o, 19)
    assert t.score(o) == .75
    settle(t, o, 1)
    assert t.score(o) == 1.
    t.reset()
    assert t.settled_seconds == 0.


def test_invalid_state_fails_closed():
    t = Trial(); o = completed(); t.peeled = 13
    o['film_00'].pos[0] = float('nan')
    t.observe(o, hands_clear=True)
    assert t.score(o) == 0.


def test_invalid_quaternion_fails_closed():
    t = Trial(); o = completed(); t.peeled = 13
    o['film_00'].quat_xyzw[:] = 0
    t.observe(o, hands_clear=True)
    assert t.score(o) == 0.


@pytest.mark.parametrize('axis', [0, 2])
def test_plate_rotation_excursion_is_latched(axis):
    t = Trial(); o = initial()
    q = np.zeros(4); q[axis] = np.sin(np.deg2rad(11)/2); q[3] = np.cos(np.deg2rad(11)/2)
    o['steel_plate'] = state('steel_plate', PLATE_POS, q)
    t.observe(o, hands_clear=True)
    t.peeled = 7; t.observe(initial(), hands_clear=True)
    assert t.score(initial()) == 0.


def test_exact_translation_limit_is_allowed():
    t = Trial(); o = initial(); t.peeled = 7
    o['steel_plate'] = state('steel_plate', PLATE_POS + [.030,0,0])
    t.observe(o, hands_clear=True)
    assert t.score(o) == .5


def test_released_count_does_not_depend_on_current_position():
    t = Trial(); t.peeled = 7
    t.observe(initial(), hands_clear=True)
    assert t.score(initial()) == .5


def test_film_below_table_rejected():
    t = Trial(); o = completed(); t.peeled = 13
    o['film_00'] = state('film_00', [.2, -.3, TABLE_Z-.01])
    t.observe(o, hands_clear=True)
    assert t.score(o) == .75
