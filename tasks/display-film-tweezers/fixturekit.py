"""Create one rigid compound body (carrier with clamped phone, or folded film end) from documented parts."""


def replace_mesh(prim, config, parts, contact_offset=.0002):
    from isaaclab.sim.utils import bind_physics_material, bind_visual_material
    from isaaclab.sim.spawners.materials import PreviewSurfaceCfg, spawn_preview_surface
    from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema
    stage=prim.GetStage();path=str(prim.GetPath())
    stage.RemovePrim(path+'/geometry/mesh')
    for part in parts:
        if part.shape=='cylinder':
            # Visual rounding only (vertical axis); collision stays with the boxes.
            shape=UsdGeom.Cylinder.Define(stage,path+'/geometry/'+part.name)
            shape.CreateAxisAttr('Z');shape.CreateRadiusAttr(part.size[0]/2);shape.CreateHeightAttr(part.size[2])
            shape.AddTranslateOp().Set(Gf.Vec3d(*part.center))
        else:
            shape=UsdGeom.Cube.Define(stage,path+'/geometry/'+part.name)
            shape.CreateSizeAttr(1.)
            shape.AddTranslateOp().Set(Gf.Vec3d(*part.center))
            shape.AddScaleOp().Set(Gf.Vec3f(*part.size))
        if part.collide:
            UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
            collision=PhysxSchema.PhysxCollisionAPI.Apply(shape.GetPrim())
            collision.CreateContactOffsetAttr(contact_offset)
            collision.CreateRestOffsetAttr(0.)
            bind_physics_material(str(shape.GetPath()),path+'/geometry/'+config.physics_material_path)
        # A material per part keeps the tray, phone frame, glass and film visibly distinct.
        material_path=str(shape.GetPath())+'/material'
        spawn_preview_surface(material_path,PreviewSurfaceCfg(diffuse_color=part.color))
        bind_visual_material(str(shape.GetPath()),material_path)
