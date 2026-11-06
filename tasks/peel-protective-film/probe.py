"""Diagnostic simulator runner. Saves measured states and camera frames; never overrides physics.

python probe.py --mode hold --steps 200 --out /tmp/film-hold
python probe.py --mode demo --steps 740 --out /tmp/film-demo
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def source_hash():
    root = Path(__file__).parent
    names = ('task.py', 'geometry.py', 'filmkit.py', 'scoring.py')
    return hashlib.sha256(b''.join(name.encode()+b'\0'+(root/name).read_bytes() for name in names)).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['hold', 'demo', 'single', 'press', 'shear'], default='hold')
    parser.add_argument('--steps', type=int, default=200)
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    from inspect_robots import Scene
    from inspect_robots.types import Action
    from yam_arena.inspect_embodiment import YamArenaEmbodiment
    from yam_arena.demo import ArmPlan

    emb = YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),
                             object_jitter=0, control_hz=20, cam_width=320, cam_height=176)
    loaded_hash = source_hash()
    for epoch in range(args.epochs):
        start = time.monotonic()
        obs = emb.reset(Scene(id='peel-film', instruction=__doc__), seed=0)
        from yam_arena.scene import object_states
        from filmkit import _paths, _bonds
        stage = _bonds[0].GetPrim().GetStage()
        config = {}
        for name, path in _paths.items():
            prim = stage.GetPrimAtPath(path)
            config[name] = {a.GetName(): a.Get() for a in prim.GetAttributes()
                            if a.GetName().startswith(('physics:', 'physxRigidBody:'))}
        config['bonds'] = [dict(body0=[str(p) for p in b.GetBody0Rel().GetTargets()],
                                body1=[str(p) for p in b.GetBody1Rel().GetTargets()],
                                attributes={a.GetName(): a.Get() for a in b.GetPrim().GetAttributes()})
                           for b in _bonds]
        (args.out/f'{epoch}-physics.json').write_text(json.dumps(config, default=str, indent=2))
        import cv2
        for name, frame in obs.images.items():
            cv2.imwrite(str(args.out / f'{epoch}-initial-{name}.png'), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            raw = emb._base.scene[name].data.output['rgb']
            raw = raw.torch if hasattr(raw, 'torch') else raw
            rgb = raw[0, ..., :3].cpu().numpy()
            cv2.imwrite(str(args.out / f'{epoch}-setup-{name}.png'), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        hold = obs.state['joint_pos']
        plans = {arm: ArmPlan(w, emb.rig.bases[arm]) for arm, w in emb.task.demo().items()}
        if args.mode in ('press', 'shear'):
            from yam_arena.demo import Waypoint as W
            from geometry import PLATE_POS, PLATE_SIZE
            press_z = float(PLATE_POS[2] + PLATE_SIZE[2]/2 + .010)
            moves = [
                W(8, (.28, -.09, .83), 0., 'approach film'),
                W(3, (.28, -.09, press_z), 0., 'press film')]
            if args.mode == 'shear':
                moves += [W(3, (.31, -.09, press_z), 0., 'rub across film'),
                          W(3, (.25, -.09, press_z), 0., 'rub back')]
            else:
                moves += [W(5, (.28, -.09, press_z), 0., 'hold pressure')]
            moves += [W(2, (.28, -.09, .83), 0., 'withdraw')]
            plans['right'] = ArmPlan(moves, emb.rig.bases['right'])
        records = []
        step_times = []
        for step in range(args.steps):
            action = hold if args.mode == 'hold' else np.concatenate(
                [plans[arm].action7((step+1)/20)[0] for arm in ('left', 'right')])
            if args.mode == 'single':
                action[:7] = hold[:7]
            tick = time.monotonic()
            result = emb.step(Action(action))
            step_times.append(time.monotonic()-tick)
            states = object_states(emb._env, emb.task.names)
            record = dict(step=step, info=result.info,
                          joint_pos=result.observation.state['joint_pos'].tolist(),
                          objects={name: dict(pos=s.pos.tolist(), quat=s.quat_xyzw.tolist(),
                                              vel=s.lin_vel.tolist(), ang_vel=s.ang_vel.tolist())
                                   for name, s in states.items()})
            records.append(record)
            if step % 20 == 0 or result.terminated:
                print(json.dumps(dict(epoch=epoch, step=step, info=result.info,
                                      plate=states['steel_plate'].pos.tolist())), flush=True)
                for name, frame in result.observation.images.items():
                    cv2.imwrite(str(args.out/f'{epoch}-{step:04d}-{name}.png'), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                (args.out/f'{epoch}-trace.json').write_text(json.dumps(records))
            if result.terminated:
                break
        (args.out/f'{epoch}-trace.json').write_text(json.dumps(records))
        summary = dict(mode=args.mode, epoch=epoch, steps=len(records), score=result.info['score'],
                       success=bool(result.terminated), final_info=result.info,
                       wall_seconds=time.monotonic()-start, max_step_seconds=max(step_times),
                       source_sha256=loaded_hash, source_unchanged=loaded_hash == source_hash())
        (args.out/f'{epoch}-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(f'epoch {epoch}: {time.monotonic()-start:.1f} seconds', flush=True)
    emb.close()


if __name__ == '__main__':
    main()
