"""Phone carrier, phone and folded film-end geometry, in metres.

A smartphone (71.5 x 147 x 7.8 mm) is clamped screen-up in the pocket of a loose assembly
carrier. The protective film covers the screen; its last 10 mm is folded down over the
phone's bottom end into the carrier's 6 mm relief channel. A 5.6 mm relief cut at the centre
of the fold lets tweezer tips pass behind the hanging film. The carrier is a
benchmark-designed fixture, not a manufacturer-standard one.
"""
from dataclasses import dataclass
import numpy as np

TABLE_Z=.7475
CARRIER_CENTER=np.array([.28,-.035,TABLE_Z+.0085])
CARRIER_SIZE=np.array([.110,.350,.017])
GLASS_Z=TABLE_Z+.015  # phone screen (cover glass) top
FILM_Z=GLASS_Z+.0005
FILM_SIZE=np.array([.066,.005,.001])  # one 5 mm film strip
CREASE_Y=-.055  # phone bottom end: the film folds down here
CHANNEL_Y=(-.055,-.049)  # relief channel between the phone's bottom end and the carrier
PHONE_SIZE=np.array([.0715,.147,.0078])
PHONE_CENTER=np.array([.28,CREASE_Y-PHONE_SIZE[1]/2,GLASS_Z-PHONE_SIZE[2]/2])
PHONE_RADIUS=.009  # plan-view corner radius
POCKET_GAP=.0004
NOTCH=.0056  # relief cut at the centre of the fold
END_ROOT=np.array([.28,-.05325,FILM_Z-.00475])
END_BOUNDS=np.array([.066,.0035,.0105])
END_SEAM=np.array([0,-.00175,.00475])  # the fold line, at the phone's bottom end


@dataclass(frozen=True)
class Part:
    name: str
    size: tuple  # box: x, y, z extents; cylinder: diameter, diameter, height (vertical axis)
    center: tuple
    color: tuple
    shape: str = 'box'
    collide: bool = True


def phone_outline(lo,hi,z0,z1,radius,name,color):
    """Rounded rectangle: two collision boxes, plus four visual-only corner cylinders."""
    (x0,y0),(x1,y1)=lo,hi
    r=radius
    boxes=[(name+'_wide',(x0,y0+r,z0),(x1,y1-r,z1)),(name+'_long',(x0+r,y0,z0),(x1-r,y1,z1))]
    out=[(n,a,b,color,'box',True) for n,a,b in boxes]
    for i,(cx,cy) in enumerate(((x0+r,y0+r),(x1-r,y0+r),(x0+r,y1-r),(x1-r,y1-r))):
        out.append((f'{name}_corner{i}',(cx-r,cy-r,z0),(cx+r,cy+r,z1),color,'cylinder',False))
    return out


def carrier_parts():
    """Each shape's local transform under one dynamic carrier root (carrier and clamped phone)."""
    def part(name,lo,hi,color,shape='box',collide=True):
        lo,hi=np.array(lo),np.array(hi)
        return Part(name,tuple(hi-lo),tuple((hi+lo)/2-CARRIER_CENTER),color,shape,collide)
    tray=(.80,.81,.78);frame=(.20,.21,.23);glass=(.02,.02,.025);dark=(.08,.08,.09)  # light POM tray, graphite phone
    px0,px1=PHONE_CENTER[0]-PHONE_SIZE[0]/2,PHONE_CENTER[0]+PHONE_SIZE[0]/2
    py0,py1=CREASE_Y-PHONE_SIZE[1],CREASE_Y
    pz0=GLASS_Z-PHONE_SIZE[2]
    gx0,gx1,gy0=px0+.0006,px1-.0006,py0+.0006  # cover glass inset from the frame
    gx,gy0_wall=POCKET_GAP,py0-POCKET_GAP
    parts=[part('base',(.225,-.21,TABLE_Z),(.335,.14,TABLE_Z+.003),tray),
           part('pocket_floor',(px0-gx,gy0_wall,TABLE_Z+.003),(px1+gx,CREASE_Y,pz0),tray)]
    parts+=[part(*p) for p in phone_outline((px0,py0),(px1,py1),pz0,GLASS_Z-.0006,PHONE_RADIUS,'phone_frame',frame)]
    parts+=[part(*p) for p in phone_outline((gx0,gy0),(gx1,py1),GLASS_Z-.0006,GLASS_Z,PHONE_RADIUS-.0006,'cover_glass',glass)]
    parts+=[part('front_camera',(.28-.0017,py0+.0058-.0017,GLASS_Z),(.28+.0017,py0+.0058+.0017,GLASS_Z+.0001),dark,'cylinder',False),
            part('earpiece',(.28-.005,py0+.0016,GLASS_Z),(.28+.005,py0+.0026,GLASS_Z+.0001),dark,'box',False),
            part('left_guard',(.225,-.21,TABLE_Z+.003),(px0-gx,.14,TABLE_Z+.017),tray),
            part('right_guard',(px1+gx,-.21,TABLE_Z+.003),(.335,.14,TABLE_Z+.017),tray),
            part('support_flange',(px0-gx,CHANNEL_Y[1],TABLE_Z+.003),(px1+gx,.14,TABLE_Z+.017),tray),
            part('back_guard',(px0-gx,-.21,TABLE_Z+.003),(px1+gx,gy0_wall,TABLE_Z+.017),tray)]
    return parts


def film_end_parts():
    """The folded film end: a full-width hanging flap joined to the fold line on both sides of the relief cut."""
    blue=(.03,.2,.85);half=FILM_SIZE[0]/2;lip=half-NOTCH/2
    return [Part('flap',(FILM_SIZE[0],.001,.010),(0,.00125,-.00025),blue),
            Part('fold_left',(lip,.003,.001),(-(NOTCH/2+lip/2),-.00025,.00475),blue),
            Part('fold_right',(lip,.003,.001),(NOTCH/2+lip/2,-.00025,.00475),blue)]


def strip_pos(i):
    return np.array([.28,CREASE_Y-(i+.5)*FILM_SIZE[1],FILM_Z])
