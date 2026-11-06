"""Measure M1 physical tool acquisition. Diagnostic only; no manufactured success score."""
import argparse,json,time,hashlib,shutil
from pathlib import Path
import numpy as np


def source_hash():
    root=Path(__file__).parent
    return hashlib.sha256(b''.join((root/n).read_bytes() for n in
                                   ('toolkit.py','tool_task.py','tool_load_task.py','tool_probe.py'))).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--steps',type=int,default=440);ap.add_argument('--hold',action='store_true')
    ap.add_argument('--load',action='store_true')
    ap.add_argument('--epochs',type=int,default=1)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    from inspect_robots import Scene
    from inspect_robots.types import Action
    from yam_arena.inspect_embodiment import YamArenaEmbodiment
    from yam_arena.demo import ArmPlan
    emb=YamArenaEmbodiment(task=str(Path(__file__).with_name('tool_load_task.py' if a.load else 'tool_task.py')),object_jitter=0,
                          control_hz=20,cam_width=320,cam_height=176)
    for epoch in range(a.epochs):
        run_out=a.out/str(epoch) if a.epochs>1 else a.out
        run_out.mkdir(parents=True,exist_ok=True)
        loaded_hash=source_hash()
        for name in ('toolkit.py','tool_task.py','tool_load_task.py','tool_probe.py'):
            (run_out/'source').mkdir(exist_ok=True)
            shutil.copyfile(Path(__file__).with_name(name),run_out/'source'/name)
        import toolkit
        if toolkit.COUPON_FIXTURE is not None:
            toolkit.COUPON_FIXTURE.GetJointEnabledAttr().Set(True)
        start=time.monotonic();obs=emb.reset(Scene(id='tool-m1',instruction='Pick up and replace the tweezers.'),seed=0)
        from yam_arena.scene import object_states
        import cv2
        action=np.array(obs.state['joint_pos'],copy=True)
        plan=ArmPlan(emb.task.demo()['right'],emb.rig.bases['right'])
        load_start=0.
        if a.load:
            for waypoint in emb.task.demo()['right']:
                if waypoint.label=='hold calibration loads':break
                load_start+=waypoint.duration
        failure=None
        trace=[]
        for step in range(a.steps):
            force=np.zeros(3)
            if a.load:
                import torch
                import toolkit
                t=(step+1)/20
                if t >= load_start+.5:
                    toolkit.COUPON_FIXTURE.GetJointEnabledAttr().Set(False)
                for lo,hi,magnitude,direction in [(1,3,3,'vertical'),(4,6,3,'peel'),
                                                    (7,9,6,'vertical'),(10,12,6,'peel')]:
                    if lo <= t-load_start < hi:
                        force = magnitude*np.array([0,0,-1] if direction=='vertical'
                                                    else [0,np.cos(np.deg2rad(10)),-np.sin(np.deg2rad(10))])
                coupon=emb._base.scene['load_coupon']
                coupon.permanent_wrench_composer.reset()
                coupon.permanent_wrench_composer.add_forces_and_torques(
                    torch.tensor(force,device=emb._base.device,dtype=torch.float32).reshape(1,1,3),
                    torch.zeros((1,1,3),device=emb._base.device),is_global=True)
            if not a.hold:action[7:]=plan.action7((step+1)/20)[0]
            result=emb.step(Action(action))
            objects=object_states(emb._env,emb.task.names)
            record={'step':step,'applied_coupon_force_N':force.tolist(),
                    'joints':result.observation.state['joint_pos'].tolist(),
                    'root_poses':{n:emb._env.unwrapped.arena_world.get_pose_w(n)[0].cpu().numpy().tolist()
                                  for n in (('tweezer_a','tweezer_b','load_coupon') if a.load
                                            else ('tweezer_a','tweezer_b'))},
                    'objects':{n:{'pos':s.pos.tolist(),'quat':s.quat_xyzw.tolist(),
                                  'vel':s.lin_vel.tolist(),'ang_vel':s.ang_vel.tolist()} for n,s in objects.items()}}
            trace.append(record)
            if a.load and load_start+.5 <= t < load_start+12:
                from geometry import rotation
                pa=record['root_poses']['tweezer_a'];pc=record['root_poses']['load_coupon']
                relative=rotation(pa[3:]).T@(np.array(pc[:3])-pa[:3])
                if np.linalg.norm(relative-np.array([0,0,-.055])) > .02:
                    failure='Coupon lost: displacement from expected tip grasp exceeds 20 mm.'
            if step%20==0:
                print(json.dumps({'step':step,'a':record['objects']['tweezer_a']['pos'],
                                  'b':record['objects']['tweezer_b']['pos']}),flush=True)
                for name,frame in result.observation.images.items():
                    cv2.imwrite(str(run_out/f'{step:04d}-{name}.png'),cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
                (run_out/'trace.json').write_text(json.dumps(trace))
            if failure:break
        (run_out/'trace.json').write_text(json.dumps(trace))
        (run_out/'summary.json').write_text(json.dumps({'steps':len(trace),'wall_seconds':time.monotonic()-start,
                                                    'worst_ik_mm':plan.worst_ik_mm,
                                                    'source_sha256':loaded_hash,
                                                    'source_unchanged':loaded_hash==source_hash(),
                                                    'load_start_s':load_start,'failure':failure},indent=2))
    emb.close()
if __name__=='__main__':main()
