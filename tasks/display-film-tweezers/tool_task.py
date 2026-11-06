"""M1 diagnostic: grasp, lift, adjust and replace a passive tweezer tool."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from yam_arena.task_file import Box
from toolkit import install
install()
SCENE = 'station'
SCORE_OVER = 'end'
Z = .7475
X,Y = .36,-.24
OBJECTS = [Box(name='tweezer_a',size=(.008,.006,.12),pos=(X,Y-.0044,Z+.063),mass=.0075,color=(.4,.45,.5)),
           Box(name='tweezer_b',size=(.008,.006,.12),pos=(X,Y+.0044,Z+.063),mass=.0075,color=(.4,.45,.5)),
           Box(name='stand_floor',size=(.03,.034,.003),pos=(X,Y,Z+.0015),color=(.1,.15,.2))]
for name,size,pos in [('left',(.003,.034,.020),(X-.0075,Y,Z+.013)),
                      ('right',(.003,.034,.020),(X+.0075,Y,Z+.013)),
                      ('front',(.018,.003,.020),(X,Y-.0145,Z+.013)),
                      ('back',(.018,.003,.020),(X,Y+.0145,Z+.013))]:
    OBJECTS.append(Box(name='stand_'+name,size=size,pos=pos,color=(.1,.15,.2)))


def demo():
    from yam_arena.demo import Waypoint as W
    h=Z+.003+.080
    return {'right':[W(3,(X,Y,h+.045),-.020,'approach'),
                     W(2,(X,Y,h),-.020,'descend'),
                     W(2,(X,Y,h),-.006,'grasp'),
                     W(3,(X,Y,h+.04),-.006,'lift'),
                     W(2,(X,Y,h+.04),-.004,'squeeze'),
                     W(2,(X,Y,h+.04),-.006,'relax'),
                     W(3,(X,Y,h),-.006,'replace'),
                     W(2,(X,Y,h),-.020,'release'),
                     W(3,(X,Y,h+.045),-.020,'withdraw')]}
