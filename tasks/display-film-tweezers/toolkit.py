"""Passive parallel tweezer prototype. No attachment to the robot or pose following."""
import importlib.abc
import importlib.machinery
import sys

PATHS = {}
JOINT = None
COUPON_FIXTURE = None


def patch(scene):
    original = scene.task_object

    def object_spec(spec):
        global JOINT
        obj = original(spec)
        if spec.name not in ('tweezer_a', 'tweezer_b', 'load_coupon'):
            return obj
        from isaaclab.sim.spawners.shapes import spawn_cuboid
        from isaaclab.sim.utils import clone, bind_visual_material, bind_physics_material
        from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf
        cfg = obj.spawner_cfg
        cfg.rigid_props.solver_position_iteration_count = 128
        cfg.rigid_props.solver_velocity_iteration_count = 16
        cfg.collision_props.contact_offset = .0002
        cfg.collision_props.rest_offset = 0.
        cfg.physics_material.static_friction = 1.
        cfg.physics_material.dynamic_friction = .8
        if spec.name == 'load_coupon':
            @clone
            def coupon_spawn(path, config, *args, **kwargs):
                global COUPON_FIXTURE
                prim = spawn_cuboid.__wrapped__(path, config, *args, **kwargs)
                joint = UsdPhysics.FixedJoint.Define(prim.GetStage(),str(path)+'/test_fixture')
                joint.CreateBody1Rel().SetTargets([str(path)])
                joint.CreateLocalPos0Attr(Gf.Vec3f(*spec.pos))
                joint.CreateLocalPos1Attr(Gf.Vec3f(0,0,0))
                COUPON_FIXTURE = joint
                return prim
            cfg.func = coupon_spawn
            return scene.Object(name=spec.name, object_type=obj.object_type,
                                spawner_cfg=cfg, initial_pose=obj.initial_pose)
        sign = -1 if spec.name == 'tweezer_a' else 1

        @clone
        def spawn(path, config, *args, **kwargs):
            global JOINT
            prim = spawn_cuboid.__wrapped__(path, config, *args, **kwargs)
            stage = prim.GetStage()
            stage.RemovePrim(str(path)+'/geometry/mesh')
            parts = [('tip', (.004,.0008,.024), (0,0,-.048)),
                     ('neck', (.004,.0048,.004), (0,sign*.002,-.038)),
                     ('handle', (.008,.002,.096), (0,sign*.004,.012))]
            for name, size, pos in parts:
                cube = UsdGeom.Cube.Define(stage, str(path)+'/geometry/'+name)
                cube.CreateSizeAttr(1.)
                cube.AddTranslateOp().Set(Gf.Vec3d(*pos))
                cube.AddScaleOp().Set(Gf.Vec3f(*size))
                UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
                collision = PhysxSchema.PhysxCollisionAPI.Apply(cube.GetPrim())
                collision.CreateContactOffsetAttr(.0002)
                collision.CreateRestOffsetAttr(0.)
                bind_visual_material(str(cube.GetPath()), str(path)+'/geometry/material')
                bind_physics_material(str(cube.GetPath()), str(path)+'/geometry/'+config.physics_material_path)
            PATHS[spec.name] = str(path)
            if spec.name == 'tweezer_b':
                joint = UsdPhysics.PrismaticJoint.Define(stage,str(path)+'/spring')
                joint.CreateBody0Rel().SetTargets([PATHS['tweezer_a']])
                joint.CreateBody1Rel().SetTargets([str(path)])
                joint.CreateAxisAttr('Y')
                joint.CreateLocalPos0Attr(Gf.Vec3f(0,0,0))
                joint.CreateLocalPos1Attr(Gf.Vec3f(0,0,0))
                joint.CreateLowerLimitAttr(.0008)
                joint.CreateUpperLimitAttr(.0108)
                # The two tips physically stop against each other; keep contact
                # in addition to the joint limit under large gripper forces.
                joint.CreateCollisionEnabledAttr(True)
                drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(),'linear')
                drive.CreateTypeAttr('force')
                drive.CreateTargetPositionAttr(.0088)
                drive.CreateStiffnessAttr(150.)
                drive.CreateDampingAttr(.5)
                JOINT = joint
            return prim
        cfg.func = spawn
        return scene.Object(name=spec.name, object_type=obj.object_type,
                            spawner_cfg=cfg, initial_pose=obj.initial_pose)
    scene.task_object = object_spec


def install():
    if 'yam_arena.scene' in sys.modules:
        patch(sys.modules['yam_arena.scene'])
        return
    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname != 'yam_arena.scene':
                return None
            spec = importlib.machinery.PathFinder.find_spec(fullname,path)
            original = spec.loader
            class Loader(importlib.abc.Loader):
                def create_module(self, s): return original.create_module(s)
                def exec_module(self, module):
                    original.exec_module(module)
                    patch(module)
            spec.loader = Loader()
            return spec
    sys.meta_path.insert(0,Finder())
