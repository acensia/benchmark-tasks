from pathlib import Path
import numpy as np
from yam_arena.task_file import load
from yam_arena.demo import ArmPlan
from yam_arena.station import rig
from yam_arena import ik


def test_task_loads_and_both_full_trajectories_are_reachable():
    task = load(Path(__file__).resolve().parents[1] / 'task.py')
    assert len(task.objects) == 22
    assert task.scene == 'station'
    assert task.score_over == 'end'
    for arm, waypoints in task.demo().items():
        plan = ArmPlan(waypoints, rig().bases[arm])
        for t in np.arange(.05, plan.duration + .05, .05):
            action, _ = plan.action7(t)
            assert np.all(action[:6] >= ik.LOWER)
            assert np.all(action[:6] <= ik.UPPER)
        assert plan.worst_ik_mm < .5
        assert plan.worst_ik_deg < .1
