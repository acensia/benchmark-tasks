"""Outcome scoring, independent of Isaac. History is updated once per control step."""
import numpy as np
from geometry import FILM_NAMES, N_BONDED, CARRIER_POS, CARRIER_SIZE, SIZES, TABLE_Z, corners, rotation
from tool_geometry import TOOL_NAMES,returned


class Trial:
    def __init__(self):
        self.reset()

    def reset(self):
        self.peeled = 0
        self.invalid = False
        self.hands_clear = False
        self.settled_seconds = 0.

    def observe(self, objects, *, hands_clear):
        self.hands_clear = bool(hands_clear)
        try:
            for name in (*SIZES,*TOOL_NAMES,'stand_floor'):
                s = objects[name]
                if not all(np.all(np.isfinite(v)) for v in
                           (s.pos, s.quat_xyzw, s.lin_vel, s.ang_vel)):
                    self.invalid = True
                rotation(s.quat_xyzw)
            p = objects['carrier']
            r = rotation(p.quat_xyzw)
            # Throughout the trial: no lifting, dragging and replacing, or rotating the carrier.
            self.invalid |= bool(np.linalg.norm(np.asarray(p.pos)[:2] - CARRIER_POS[:2]) > .030 + 1e-9)
            self.invalid |= bool(abs(p.pos[2] - CARRIER_POS[2]) > .005 + 1e-9)
            self.invalid |= bool(r[2, 2] < np.cos(np.deg2rad(10)) - 1e-9)
            self.invalid |= bool(abs(np.arctan2(r[1, 0], r[0, 0])) > np.deg2rad(10) + 1e-9)
        except (KeyError, ValueError, IndexError):
            self.invalid = True

    def disposed(self, objects):
        if not self.hands_clear or not returned(objects):
            return False
        plate = objects['carrier']
        r = rotation(plate.quat_xyzw)
        table_contact = False
        for name in FILM_NAMES:
            s = objects[name]
            world = corners(s, SIZES[name])
            local = (world - plate.pos) @ r
            # Conservative whole-piece separation, including a 2 mm margin.
            outside = any(local[:, axis].min() >= CARRIER_SIZE[axis]/2 + .002 or
                          local[:, axis].max() <= -CARRIER_SIZE[axis]/2 - .002
                          for axis in (0, 1))
            # Permit the precreased tab to remain raised after disposal. The sheet
            # must have table support, remain entirely within 30 mm of the surface,
            # be settled, and be clear of both hands; an airborne sheet cannot pass.
            table_contact |= bool(TABLE_Z - .002 <= world[:, 2].min() <= TABLE_Z + .003)
            near_table = (world[:, 2].min() >= TABLE_Z - .002
                          and world[:, 2].max() <= TABLE_Z + .030)
            if not (outside and near_table and s.resting(max_speed=.01, max_spin=.5)):
                return False
        return table_contact

    def score(self, objects):
        if self.invalid:
            return 0.0
        if self.settled_seconds >= 1. - 1e-9 and self.peeled == N_BONDED and self.disposed(objects):
            return 1.0
        # Consecutive peeled adhesive length: 30 / 60 / 90 mm of 120 mm.
        return .75 if self.peeled >= 9 else .5 if self.peeled >= 6 else .25 if self.peeled >= 3 else 0.0

    def finish_step(self, objects, dt):
        """Count stable time exactly once per measured control step, even at timeout."""
        stable = not self.invalid and self.peeled == N_BONDED and self.disposed(objects)
        self.settled_seconds = self.settled_seconds + dt if stable else 0.
