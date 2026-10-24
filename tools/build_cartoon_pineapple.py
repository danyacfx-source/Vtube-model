"""Replace only pineapple face geometry; preserve its textured body and rig."""
import pathlib,runpy
import bpy
from mathutils.bvhtree import BVHTree

root=pathlib.Path(__file__).resolve().parents[1]
api=runpy.run_path(str(root/'tools/build_models.py'))
make=runpy.run_path(str(root/'tools/cartoon_face.py'))['make_feature']
bpy.ops.wm.open_mainfile(filepath=str(root/'models/pineapple.blend'))
body=bpy.data.objects['Fruit_body'];arm=bpy.data.objects['FruitHumanoid']
api['surface'].__globals__['FACE_SURFACE']=BVHTree.FromPolygons([body.matrix_world@v.co for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons])
for name in ['Eye_L','Eye_R','Mouth']:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
for name,cx,cz in [('Eye_L',-.18,1.63),('Eye_R',.18,1.63),('Mouth',0,1.32)]:
    ob=make(api,name,cx,cz,name=='Mouth');api['bind'](ob,arm)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'models/pineapple.blend'))
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
    if ob.type in {'MESH','ARMATURE'}:ob.select_set(True)
glb=root/'models/pineapple.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_tangents=True,export_skins=True,export_all_influences=True,export_extras=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True,export_yup=True)
api['pack_vrm'](glb,root/'models/pineapple.vrm',[b.name for b in arm.data.bones],'Pineapple');glb.unlink()
scene=bpy.context.scene;scene.render.resolution_percentage=55;scene.cycles.samples=24
for expression in ['neutral','A','I','U','E','O','Blink','Happy','LookLeft','LookRight','LookUp','LookDown','JOY','SORROW','ANGRY','joy-blink']:
    for name in ['Eye_L','Eye_R','Mouth']:
        for key in bpy.data.objects[name].data.shape_keys.key_blocks:
            active=key.name==expression or (expression in {'JOY','joy-blink'} and key.name in {'Happy','JOY'}) or (expression=='joy-blink' and key.name=='Blink')
            key.value=1 if active else 0
    scene.render.filepath=str(root/'previews'/f'pineapple-cartoon-{expression.lower()}.png');bpy.ops.render.render(write_still=True)
