"""M1 load calibration: tool contacts a 1 mm coupon, released from its test fixture.

The probe applies a documented external test load to the coupon, never to the tool
or robot. This calibration fixture is not part of the submitted scene.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tool_task import OBJECTS, SCENE, SCORE_OVER, Z, X, Y
from yam_arena.task_file import Box
OBJECTS = list(OBJECTS) + [Box(name='load_coupon',size=(.008,.001,.01),
                             pos=(.28,-.06,Z+.025),mass=.003,color=(.03,.2,.85))]


def demo():
    from yam_arena.demo import Waypoint as W
    h=Z+.003+.080
    grip=Z+.020+.080
    return {'right':[W(3,(X,Y,h+.045),-.020,'approach'),
                     W(2,(X,Y,h),-.020,'descend'),
                     W(2,(X,Y,h),-.0067,'grasp tool with open tips'),
                     W(3,(X,Y,h+.04),-.0067,'lift tool'),
                     W(3,(.28,-.06,grip+.025),-.0067,'approach coupon'),
                     W(2,(.28,-.06,grip+.025),-.0067,'settle above coupon'),
                     W(4,(.28,-.06,grip),-.0067,'insert around coupon'),
                     W(2,(.28,-.06,grip),0.,'pinch coupon'),
                     W(12,(.28,-.06,grip),0.,'hold calibration loads'),
                     W(2,(.28,-.06,grip+.025),0.,'lift coupon'),
                     W(2,(.28,-.06,grip+.025),-.0067,'release coupon'),
                     W(3,(X,Y,h+.04),-.0067,'return above stand'),
                     W(3,(X,Y,h),-.0067,'lower into stand'),
                     W(2,(X,Y,h),-.020,'release tool'),
                     W(3,(X,Y,h+.110),-.020,'withdraw above tool'),
                     W(3,(.20,-.40,Z+.193),-.020,'clear stand'),
                     W(2,(.20,-.40,Z+.13),-.020,'settle')]}
