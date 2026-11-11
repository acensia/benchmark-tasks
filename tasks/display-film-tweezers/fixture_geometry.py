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
FILM_COLOR=(.35,.62,.98)  # sRGB; protective PE film is a translucent light blue
FILM_OPACITY=.45


def linear_rgb(srgb):
    """Same sRGB-to-linear conversion the scene applies to task-object colours."""
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in srgb)


@dataclass(frozen=True)
class Part:
    name: str
    size: tuple  # bounding extents; a cylinder's height is its extent along `axis`
    center: tuple
    color: tuple
    shape: str = 'box'
    collide: bool = True
    axis: str = 'Z'  # cylinders only
    opacity: float = 1.


def phone_outline(lo,hi,z0,z1,radius,name,color,collide=True):
    """Rounded rectangle: two boxes (collision unless collide=False) and four visual-only corner cylinders."""
    (x0,y0),(x1,y1)=lo,hi
    r=radius
    boxes=[(name+'_wide',(x0,y0+r,z0),(x1,y1-r,z1)),(name+'_long',(x0+r,y0,z0),(x1-r,y1,z1))]
    out=[(n,a,b,color,'box',collide) for n,a,b in boxes]
    for i,(cx,cy) in enumerate(((x0+r,y0+r),(x1-r,y0+r),(x0+r,y1-r),(x1-r,y1-r))):
        out.append((f'{name}_corner{i}',(cx-r,cy-r,z0),(cx+r,cy+r,z1),color,'cylinder',False))
    return out


def carrier_parts():
    """Each shape's local transform under one dynamic carrier root (carrier and clamped phone)."""
    def part(name,lo,hi,color,shape='box',collide=True,axis='Z'):
        lo,hi=np.array(lo),np.array(hi)
        return Part(name,tuple(hi-lo),tuple((hi+lo)/2-CARRIER_CENTER),color,shape,collide,axis)
    tray=(.80,.81,.78);frame=(.20,.21,.23);glass=(.012,.012,.016);dark=(.08,.08,.09)  # light POM tray, graphite phone
    px0,px1=PHONE_CENTER[0]-PHONE_SIZE[0]/2,PHONE_CENTER[0]+PHONE_SIZE[0]/2
    py0,py1=CREASE_Y-PHONE_SIZE[1],CREASE_Y
    pz0=GLASS_Z-PHONE_SIZE[2]
    gx0,gx1,gy0=px0+.0006,px1-.0006,py0+.0006  # cover glass inset from the frame
    gx,gy0_wall=POCKET_GAP,py0-POCKET_GAP
    parts=[part('base',(.225,-.21,TABLE_Z),(.335,.14,TABLE_Z+.003),tray),
           part('pocket_floor',(px0-gx,gy0_wall,TABLE_Z+.003),(px1+gx,CREASE_Y,pz0),tray)]
    parts+=[part(*p) for p in phone_outline((px0,py0),(px1,py1),pz0,GLASS_Z-.0006,PHONE_RADIUS,'phone_frame',frame)]
    parts+=[part(*p) for p in phone_outline((gx0,gy0),(gx1,py1),GLASS_Z-.0006,GLASS_Z,PHONE_RADIUS-.0006,'cover_glass',glass)]
    parts+=[part('left_guard',(.225,-.21,TABLE_Z+.003),(px0-gx,.14,TABLE_Z+.017),tray),
            part('right_guard',(px1+gx,-.21,TABLE_Z+.003),(.335,.14,TABLE_Z+.017),tray),
            part('support_flange',(px0-gx,CHANNEL_Y[1],TABLE_Z+.003),(px1+gx,.14,TABLE_Z+.017),tray),
            part('back_guard',(px0-gx,-.21,TABLE_Z+.003),(px1+gx,gy0_wall,TABLE_Z+.017),tray)]
    return parts+phone_details(part,px0,px1,py0,py1,pz0)


def phone_details(part,px0,px1,py0,py1,pz0):
    """Visual-only details of a generic smartphone (no collision, no branding)."""
    screen=(.035,.04,.052);black=(.004,.004,.006);grille=(.13,.13,.14);metal=(.40,.41,.43)
    ins=.0024  # black border around the display's active area
    out=[part(*p) for p in phone_outline((px0+ins,py0+ins),(px1-ins,py1-ins),GLASS_Z,GLASS_Z+.00004,
                                          PHONE_RADIUS-ins,'display',screen,collide=False)]
    cy=py0+.0058  # punch-hole front camera
    out+=[part('camera_ring',(.28-.0019,cy-.0019,GLASS_Z),(.28+.0019,cy+.0019,GLASS_Z+.00008),grille,'cylinder',False),
          part('camera_lens',(.28-.0012,cy-.0012,GLASS_Z),(.28+.0012,cy+.0012,GLASS_Z+.00012),black,'cylinder',False),
          part('earpiece',(.28-.006,py0+.0011,GLASS_Z),(.28+.006,py0+.0019,GLASS_Z+.00008),grille,'box',False)]
    # Bottom end face (y=py1), seen through the relief channel: USB-C port, speaker and mic holes, screws.
    zm,face,h=pz0+PHONE_SIZE[2]/2,py1,.00008
    def hole(name,x,r,color):
        return part(name,(x-r,face,zm-r),(x+r,face+h,zm+r),color,'cylinder',False,'Y')
    out+=[part('usb_c',(.28-.00285,face,zm-.0016),(.28+.00285,face+h,zm+.0016),black,'box',False),
          hole('usb_c_left',.28-.00285,.0016,black),hole('usb_c_right',.28+.00285,.0016,black),
          hole('screw_left',.28-.0068,.0007,metal),hole('screw_right',.28+.0068,.0007,metal)]
    out+=[hole(f'speaker{k}',.28+.0105+k*.0022,.0006,black) for k in range(6)]
    out+=[hole(f'mic{k}',.28-.0105-k*.0022,.0006,black) for k in range(6)]
    # Carrier hardware: cap screws on the support flange (z = TABLE_Z+.017).
    out+=[part(f'carrier_screw{i}',(x-.00275,y-.00275,TABLE_Z+.017),(x+.00275,y+.00275,TABLE_Z+.0172),metal,'cylinder',False)
          for i,(x,y) in enumerate(((.255,-.02),(.305,-.02),(.255,.134),(.305,.134)))]
    return out


def film_end_parts():
    """The folded film end: a full-width hanging flap joined to the fold line on both sides of the relief cut."""
    blue=linear_rgb(FILM_COLOR);half=FILM_SIZE[0]/2;lip=half-NOTCH/2;o=FILM_OPACITY
    return [Part('flap',(FILM_SIZE[0],.001,.010),(0,.00125,-.00025),blue,opacity=o),
            Part('fold_left',(lip,.003,.001),(-(NOTCH/2+lip/2),-.00025,.00475),blue,opacity=o),
            Part('fold_right',(lip,.003,.001),(NOTCH/2+lip/2,-.00025,.00475),blue,opacity=o)]


def strip_pos(i):
    return np.array([.28,CREASE_Y-(i+.5)*FILM_SIZE[1],FILM_Z])
