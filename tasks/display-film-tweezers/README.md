# Remove display protective film with passive tweezers

Development status: M0 offline geometry passed for one measured acquisition pose;
repeat-pose margins are being checked. M1 contact loads passed three resets, while
stand return passed two of three (one angular-speed failure). Integrated physical
baselines are running; a full-score demo and Dream-1 are not yet validated.
No v1 score or media applies to this scene.

The loose 250 g carrier holds a display module and 66 × 130 mm protective film.
A recessed starter tab has an 8 mm grip surface and a 5.6 mm central entry notch.
The robot acquires a passive 120 mm tweezer tool, grasps the tab, removes the film,
places it outside the carrier, and returns the tool to its stand. The carrier and
starter-tab geometry are benchmark-designed fixtures, not an industry standard.

`fixture_geometry.py` defines every carrier and tab component. `tool_geometry.py`
and `toolkit.py` define the stand and tool. `motion.py` contains the candidate
68-second bimanual trajectory. All quantities use metres, kilograms and seconds.

## Environment and commands

Install [yam-arena](https://github.com/kairosiann/yam-isaac-lab-arena) at
`bd62771e60320433893bd1d2df0fc79b5ddcd6d1` using its setup instructions and source
`yam.env`. This provides Isaac Sim 6.1, Isaac Lab 3.0 and Inspect Robots. Simulation
requires an RTX GPU. CPU geometry diagnostics additionally use SciPy and trimesh.
Use zero object jitter: independent jitter would break the connected film geometry.

Run from the repository root:

```bash
python -m pytest tasks/display-film-tweezers/tests -q
python tasks/display-film-tweezers/tool_probe.py --load --steps 1060 --epochs 3 --out /tmp/tool-m1
python tasks/display-film-tweezers/analyze_tool.py /tmp/tool-m1/0 --return-steps 1060
python tasks/display-film-tweezers/probe.py --mode hold --steps 200 --out /tmp/display-hold
python tasks/display-film-tweezers/probe.py --mode direct --scenario all --steps 380 --out /tmp/display-direct
python tasks/display-film-tweezers/probe.py --mode demo --measure-load --steps 1400 --epochs 3 --out /tmp/display-demo
bash tasks/display-film-tweezers/record.sh /path/to/python yam_scripted /tmp/display-scripted
bash tasks/display-film-tweezers/record.sh /path/to/python dream /tmp/display-dream
```

Recording uses the instruction in `task.json`, seed 0, 20 Hz control and a 2,400-step
limit (120 simulated seconds). The candidate demo lasts 68 seconds. Integrated
wall time per trial is still to be measured. Diagnostic JSON preserves source
hashes, measured root poses, measured joints, scores and camera frames. Optional
contact sampling records transmitted tab load at every 240 Hz physics step.

## Physics and scoring

The film is a rigid tab and thirteen hinged strips. The current peel-front bond
releases at 60 degrees of upward opening. Compression or in-plane shear alone
cannot release a bond. The 0.03 N m/rad adhesive springs are an approximation,
not a fit to measured PE peel forces. Film thickness is inflated to 1 mm for
contact stability. Wrinkles, stretch, tearing, scratches and ESD are not modeled.

The tool comprises two 7.5 g rigid halves connected by a 150 N/m opening spring.
Robot contact alone moves and closes it; there is no tool attachment to the robot.
Its parallel jaw motion approximates tweezer flexure. Solver iterations are 128/16.
M1 separately checks 3 N and 6 N in two directions, relative slip ≤2 mm, rotation
≤10 degrees and tip–coupon penetration ≤0.1 mm. The 3 g, 1 mm coupon and its
releasable calibration fixture are diagnostic only and absent from the task scene.

Carrier excursions over 30 mm horizontally, 5 mm vertically or 10 degrees yaw/tilt
invalidate the whole trial. Film seam separation over 3 mm also invalidates it.
Consecutive release of 3/7/11 strips earns 0.25/0.5/0.75. Full credit additionally
requires all 13 released, the film supported by the table and entirely 2 mm outside
the carrier, every piece within 30 mm of the table and moving below 10 mm/s and
0.5 rad/s, and upright tool return. Return requires tip-centre horizontal error
≤3 mm, vertical error ≤5 mm, tilt ≤5 degrees, opening 6–10 mm and the same speed
limits. Both measured TCPs must be at least 80 mm from all task objects. These
completion conditions must remain true for a full second.

Direct baselines cover two-finger and single-finger entry, angled entry, side and
far film edges, and carrier lifting/pushing. A failed scripted baseline is evidence
about that attempt, not proof that every possible strategy is blocked. Reset uses
the same fixed layout and restores all adhesive joints; physical trials need fresh
film and the same starter-tab folds/cuts.

Display film removal with tweezers is illustrated in the manufacturer's
[assembly process](https://www.palmtech.com.tw/technical/assembly). The benchmark
focuses on contact tool manipulation and supported peeling, not optical quality.
