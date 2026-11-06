"""Regression guards for the contact and jaw-gap measurement errors found in M1."""
import numpy as np
from analyze_tool import box_penetration
from tool_geometry import return_metrics
from test_scoring import initial,state
from geometry import rotation


def test_thin_contact_penetration_and_separation():
    tip=[.004,.0008,.024];coupon=[.008,.001,.010];eye=np.eye(3)
    assert np.isclose(box_penetration(np.zeros(3),eye,tip,[0,.00082,0],eye,coupon),.00008)
    assert box_penetration(np.zeros(3),eye,tip,[0,.001,0],eye,coupon)==0
    # A coupon beside the blade in x is not penetrating even if y/z overlap.
    assert box_penetration(np.zeros(3),eye,tip,[.007,0,0],eye,coupon)==0


def test_tip_gap_uses_both_half_rotations_not_root_separation():
    o=initial();root_a=np.array([.36,-.24045,.8105]);root_b=np.array([.36,-.23955,.8105])
    theta=.015;q=np.array([np.sin(theta/2),0,0,np.cos(theta/2)]);rb=rotation(q)
    o['tweezer_a']=state('tweezer_a',root_a+[0,-.0023,0])
    o['tweezer_b']=state('tweezer_b',root_b+rb@[0,.0023,0],q)
    measured=return_metrics(o)['gap_mm']
    assert np.isclose(measured,(.0009+.06*np.sin(theta)-.0008)*1000)
    assert measured>.99  # root-separation-only code incorrectly returned 0.1 mm
