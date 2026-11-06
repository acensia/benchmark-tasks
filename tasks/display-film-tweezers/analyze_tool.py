"""Offline M1 audit from measured root poses and measured robot joints.

No simulated state is changed. A complete two-second load phase is required;
short, interrupted or lost-coupon trials cannot pass.
"""
import argparse,json,hashlib,shutil
from pathlib import Path
import numpy as np
from geometry import rotation
from yam_arena.ik import tcp_pose
from yam_arena.station import BASES


def angle(a,b):
    return float(np.rad2deg(np.arccos(np.clip((np.trace(a.T@b)-1)/2,-1,1))))


def box_penetration(ca,ra,sa,cb,rb,sb):
    """Exact OBB separating-axis overlap; zero for separated boxes (metres)."""
    axes=[*ra.T,*rb.T]+[np.cross(a,b) for a in ra.T for b in rb.T]
    overlaps=[]
    for axis in axes:
        length=np.linalg.norm(axis)
        if length<1e-10:continue
        axis=axis/length
        extent_a=np.abs(ra.T@axis)@(np.asarray(sa)/2)
        extent_b=np.abs(rb.T@axis)@(np.asarray(sb)/2)
        overlap=extent_a+extent_b-abs(axis@(np.asarray(cb)-ca))
        if overlap<=0:return 0.
        overlaps.append(float(overlap))
    return min(overlaps)


def coupon_penetration(row):
    pc=np.array(row['root_poses']['load_coupon']);rc=rotation(pc[3:])
    values=[]
    for name in ('tweezer_a','tweezer_b'):
        pt=np.array(row['root_poses'][name]);rt=rotation(pt[3:])
        values.append(box_penetration(pt[:3]+rt@[0,0,-.048],rt,[.004,.0008,.024],
                                      pc[:3],rc,[.008,.001,.010])*1000)
    return max(values)


def poses(row):
    a=np.array(row['root_poses']['tweezer_a']);b=np.array(row['root_poses']['tweezer_b'])
    r=rotation(a[3:]);centre=(a[:3]+b[:3])/2
    tcp,hand=tcp_pose(np.array(row['joints'][7:13]),BASES['right'])
    coupon=np.array(row['root_poses']['load_coupon'])
    return dict(tool_in_hand=hand.T@(centre-tcp),tool_rotation=hand.T@r,
                coupon_in_tool=r.T@(coupon[:3]-centre),coupon_rotation=r.T@rotation(coupon[3:]),
                root_gap=float((r.T@(b[:3]-a[:3]))[1]-.0008),
                gap=float((r.T@(b[:3]+rotation(b[3:])@[0,0,-.06]-a[:3]-r@[0,0,-.06]))[1]-.0008),
                tip=centre+(rotation(a[3:])+rotation(b[3:]))@np.array([0,0,-.03]))


def audit(folder):
    rows=json.loads((folder/'trace.json').read_text())
    summary=json.loads((folder/'summary.json').read_text())
    start=summary.get('load_start_s',17.)
    before=min(round((start+.45)*20)-1,len(rows)-1)
    reference=poses(rows[before])
    pickup=poses(rows[139])
    acquisition=poses(rows[min(round(start*20)-1,len(rows)-1)])
    phases=[]
    for lo,hi,force,label in [(1,3,3,'vertical'),(4,6,3,'peel170'),(7,9,6,'vertical'),(10,12,6,'peel170')]:
        selected=[r for r in rows if lo <= (r['step']+1)/20-start < hi]
        data=[poses(r) for r in selected]
        record=dict(force_N=force,direction=label,samples=len(data),required_samples=40)
        if data:
            for key,position,orientation in [('tool','tool_in_hand','tool_rotation'),('coupon','coupon_in_tool','coupon_rotation')]:
                record[key+'_slip_mm']=max(float(np.linalg.norm(p[position]-reference[position])*1000) for p in data)
                record[key+'_rotation_deg']=max(angle(reference[orientation],p[orientation]) for p in data)
            expected=force*np.array([0,0,-1] if label=='vertical' else
                                     [0,np.cos(np.deg2rad(10)),-np.sin(np.deg2rad(10))])
            record['applied_force_valid']=all(np.allclose(r['applied_coupon_force_N'],expected,atol=1e-7,rtol=0)
                                              for r in selected)
            record['max_tip_coupon_penetration_mm']=max(coupon_penetration(r) for r in selected)
        expected_steps=list(range(round((start+lo)*20)-1,round((start+hi)*20)-1))
        record['steps_valid']=[r['step'] for r in selected]==expected_steps
        record['passed']=bool(len(data)==40 and record['steps_valid'] and record.get('applied_force_valid')
                              and record.get('tool_slip_mm',float('inf'))<=2
                              and record.get('coupon_slip_mm',float('inf'))<=2
                              and record.get('tool_rotation_deg',float('inf'))<=10
                              and record.get('coupon_rotation_deg',float('inf'))<=10)
        record['passed']=record['passed'] and record.get('max_tip_coupon_penetration_mm',float('inf'))<=.1
        phases.append(record)
    acquisition_slip=float(np.linalg.norm(acquisition['tool_in_hand']-pickup['tool_in_hand'])*1000)
    approach=[poses(r) for r in rows[139:round(start*20)]]
    max_acquisition_slip=max(float(np.linalg.norm(p['tool_in_hand']-pickup['tool_in_hand'])*1000) for p in approach)
    max_acquisition_rotation=max(angle(pickup['tool_rotation'],p['tool_rotation']) for p in approach)
    preserved_hash=hashlib.sha256(b''.join((folder/'source'/n).read_bytes() for n in
        ('toolkit.py','tool_task.py','tool_load_task.py','tool_probe.py'))).hexdigest()
    valid=(summary.get('source_unchanged') is True and max_acquisition_slip<=2 and max_acquisition_rotation<=10
           and preserved_hash==summary.get('source_sha256')
           and summary.get('failure') is None and len(rows)==summary.get('steps')
           and [r['step'] for r in rows]==list(range(len(rows))))
    result=dict(source_sha256=summary.get('source_sha256'),source_unchanged=summary.get('source_unchanged'),
                acquisition_tool_slip_mm=acquisition_slip,
                acquisition_max_slip_mm=max_acquisition_slip,acquisition_max_rotation_deg=max_acquisition_rotation,
                preserved_source_matches=preserved_hash==summary.get('source_sha256'),
                phases=phases,passed_3N=bool(valid and all(p['passed'] for p in phases if p['force_N']==3)),
                passed_6N=bool(valid and all(p['passed'] for p in phases if p['force_N']==6)))
    shutil.copyfile(__file__,folder/'audit-source.py')
    shutil.copyfile(Path(__file__).with_name('geometry.py'),folder/'audit-geometry.py')
    result['audit_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (folder/'load-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def return_audit(folder, expected_steps):
    """Evaluate the numeric stand-return protocol over the final measured second."""
    import itertools
    rows=json.loads((folder/'trace.json').read_text())
    summary=json.loads((folder/'summary.json').read_text())
    complete=(len(rows)==expected_steps==summary.get('steps')
              and [r['step'] for r in rows]==list(range(expected_steps))
              and summary.get('source_unchanged') is True and summary.get('failure') is None)
    signs=np.array(list(itertools.product((-.5,.5),repeat=3)))
    measured=[]
    for row in rows[-20:]:
        p=poses(row);roots=row['root_poses'];floor=np.array(row['objects']['stand_floor']['pos'])
        target=floor+np.array([0,0,.0015])
        tilt=max(float(np.rad2deg(np.arccos(np.clip(rotation(roots[n][3:])[2,2],-1,1))))
                 for n in ('tweezer_a','tweezer_b'))
        boxes=[]
        for n,sgn in [('tweezer_a',-1),('tweezer_b',1)]:
            root=np.array(roots[n]);local=signs*np.array([.008,.0054,.12])+[0,sgn*.0023,0]
            world=local@rotation(root[3:]).T+root[:3]
            boxes.append((world.min(0),world.max(0)))
        stand_center=floor+np.array([0,0,.010])
        boxes.append((stand_center-[.015,.017,.0115],stand_center+[.015,.017,.0115]))
        clearance=[]
        for arm,q in [('left',row['joints'][:6]),('right',row['joints'][7:13])]:
            tcp,_=tcp_pose(np.array(q),BASES[arm])
            clearance.extend(float(np.linalg.norm(tcp-np.clip(tcp,lo,hi))) for lo,hi in boxes)
        speed=max(np.linalg.norm(row['objects'][n]['vel']) for n in ('tweezer_a','tweezer_b'))
        spin=max(np.linalg.norm(row['objects'][n]['ang_vel']) for n in ('tweezer_a','tweezer_b'))
        measured.append(dict(xy_mm=float(np.linalg.norm((p['tip']-target)[:2])*1000),
                             z_mm=float(abs(p['tip'][2]-target[2])*1000),tilt_deg=tilt,
                             gap_mm=p['gap']*1000,hand_clearance_mm=min(clearance)*1000,
                             speed_mm_s=float(speed*1000),spin_rad_s=float(spin)))
    passed=complete and len(measured)==20 and all(m['xy_mm']<=3 and m['z_mm']<=5 and m['tilt_deg']<=5
        and 6<=m['gap_mm']<=10 and m['hand_clearance_mm']>=80 and m['speed_mm_s']<10
        and m['spin_rad_s']<.5 for m in measured)
    result=dict(passed=passed,complete=complete,expected_steps=expected_steps,samples=len(measured),
                maxima={k:max(m[k] for m in measured) for k in measured[0]},
                min_hand_clearance_mm=min(m['hand_clearance_mm'] for m in measured))
    (folder/'return-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path)
    p.add_argument('--return-steps',type=int,help='Require a complete stand-return protocol of this many steps')
    args=p.parse_args();result={'load':audit(args.folder)}
    passed=result['load']['passed_3N'] and result['load']['passed_6N']
    if args.return_steps is not None:
        result['return']=return_audit(args.folder,args.return_steps)
        passed=passed and result['return']['passed']
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if passed else 1)
