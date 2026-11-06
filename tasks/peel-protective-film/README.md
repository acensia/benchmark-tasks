# Peel protective film from a loose steel plate

Dream-1 scored **0.0 in 2,400 steps**. The recorded scripted demo scored **1.0 in
704 steps**, matching three consecutive simulator resets. Both runs use seed 0
and the same fixed scene, physics and scorer. The uploaded videos and setup
screenshot are registered as media **M-F2ULE4** in `task.json`.

The task uses the calibrated YAM station in Isaac Lab-Arena 0.3.1. A 350 x 100 x 1 mm, 280 g steel plate
supports an 80 mm wide protective film with a raised 20 mm tab and 130 mm bonded length.
One arm supports the loose plate while the other peels and lays the film on the table.
All positions, sizes, masses and rotations are in `geometry.py` and `task.py`.

## Environment

Install [yam-arena](https://github.com/kairosiann/yam-isaac-lab-arena) at
`bd62771e60320433893bd1d2df0fc79b5ddcd6d1` with its `setup.sh`, then source the generated
`yam.env`. This provides Isaac Sim 6.1, Isaac Lab 3.0 and Inspect Robots. An RTX GPU is
required for simulation. CPU tests need the YAM package, NumPy and pytest only.

Run commands from the submission repository root. Both policies use zero object jitter:
independent object jitter would break the connected film's initial geometry.

```bash
python -m pytest tasks/peel-protective-film/tests -q

python tasks/peel-protective-film/probe.py --mode hold --steps 200 --out /tmp/film-hold
python tasks/peel-protective-film/probe.py --mode demo --steps 740 --epochs 3 --out /tmp/film-demo
bash tasks/peel-protective-film/validate.sh /path/to/arena/.venv/bin/python /tmp/film-validation

# Reads the exact instruction from task.json and records a source hash.
bash tasks/peel-protective-film/record.sh "$(command -v python)" yam_scripted /tmp/film-scripted
bash tasks/peel-protective-film/record.sh "$(command -v python)" dream /tmp/film-dream
```

Limit: 2,400 control steps at 20 Hz, 120 simulated seconds. Current scripted plan lasts
37 simulated seconds; the validated demo finishes after 35.2 simulated seconds.
Diagnostic wall time on an NVIDIA GeForce RTX 4070 Ti SUPER was 98–107 seconds per
trial (including reset; the first trial includes scene setup). The diagnostic
runner resets with seed 0; the fixed layout makes random seed irrelevant to object poses.
Reapply a fresh film between physical trials; simulator reset restores all adhesive joints.

The standard recorded demo took 102.6 seconds wall time for 704 steps and reported
`task_score: 1.0`, terminating with success. Dream-1 (`dreamlabs/dream-1-beta`) took
315.1 seconds wall time for 2,400 steps and reported `task_score: 0.0`, ending at
the step limit without a runtime error. `record.sh` stores the JSON score log,
per-step records and all three camera streams. To export them:

```bash
inspect-robots video /path/to/recording.json --out /path/to/videos
```

## Model and scoring

`filmkit.py` adds task-specific spawners and lifecycle hooks without editing yam-arena.
The film is a chain of rigid strips joined by permanent hinges. Each strip is bonded
to the plate by an angular spring. Only the current peel front can release, and only
after upward opening reaches 60 degrees. There is no force-norm break threshold that
allows compression to remove film. Spring and damping parameters are not fitted to
measured PE peel forces.
The tab crease drive is capped at 0.0002 N m so its initial fold can yield under manipulation.
Physics continues after a scoring failure; the failure only latches the trial score to zero.

`scoring.py` latches any plate excursion for the whole trial. The detached count is
irreversible until reset. A permanent hinge opening by more than 3 mm is treated as a
broken film/numerical failure and makes the trial invalid. Completion requires the sheet to have table contact, every strip within 30 mm above the tabletop and
entirely outside the plate with a 2 mm margin, moving under 10 mm/s and 0.5 rad/s,
and both measured TCPs at least 80 mm from the film and plate for one second. The
scorer counts this second itself, so a timeout cannot award premature full credit.
See `task.json` for score thresholds. AABB separation is conservative for rotated film pieces.

## Validation

- 31 CPU tests pass, including scoring boundaries, invalid outcomes, release direction,
  the full-second settling requirement, task loading and trajectory reachability.
- Untouched scene (200 steps), pressing and rubbing (400 steps each): no strips released,
  score 0, plate limits maintained.
- Single-arm scripted baseline (740 steps): score 0 after the plate moves beyond its
  allowed range. This tests that baseline, not every possible single-arm strategy.
- Bimanual demo: three consecutive resets, each 704 steps, score 1.0. The approximate
  inter-arm hull check found no overlap; it is not a formal collision proof.
- These results use core SHA-256
  `252f227537177e1f66e376d91265b3441fe49402e83f0bfed5e1074b2c34dc3f`
  (computed by `probe.py` from the four scene/physics/scoring source files).

The authenticated task board was checked on 2026-11-06: 701 entries, including
accepted, pending, being revised and prior-cohort plans. No direct protective-film
removal task was found. This is a dated overlap check, not a guarantee of acceptance.
The videos contain the overhead and two wrist-camera views at 20 fps.

## Relevance and distinction

Temporary surface-protection films remain on sheet metal during fabrication and are
removed at the end of production; see the manufacturer's
[stainless-steel film brochure](https://www.polifilm.com/content/uploads/Stainless-Steel-Protection-Films.pdf).
This task removes an intact sacrificial surface layer from a loose rigid workpiece and
clears it away. It differs from [lamp-cord splitting, PR #588](https://github.com/robocurve/benchmark-tasks/pull/588),
which splits a web between flexible conductors and must stop at a marked tear limit.
Sequential separation and two-arm cooperation alone are not claimed as novel.
