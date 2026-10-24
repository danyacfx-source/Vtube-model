"""Upgrade the version-4 pineapple source without rebuilding its skin or crown.

Run once on the original v4 source. Subsequent builds use build_models.py.
"""
import pathlib,runpy
import bpy
from mathutils.bvhtree import BVHTree

root=pathlib.Path(__file__).resolve().parents[1]
api=runpy.run_path(str(root/'tools/build_models.py'))
bpy.ops.wm.open_mainfile(filepath=str(root/'models/pineapple.blend'))
body=bpy.data.objects['Fruit_body']
surface=BVHTree.FromPolygons([body.matrix_world@v.co for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons])
refine=api['refine_vseeface_feature'];refine.__globals__['FACE_SURFACE']=surface
for name,cx,cz,width,height in [('Eye_L',-.19,1.60,.14,.078),('Eye_R',.19,1.60,.14,.078),('Mouth',0,1.32,.19,.107)]:
    ob=bpy.data.objects[name]
    assert 'LookUp' not in ob.data.shape_keys.key_blocks, 'Already upgraded; rebuild instead'
    for key in ob.data.shape_keys.key_blocks:key.value=0
    refine(ob,'pineapple',cx,cz,width,height,name=='Mouth')
arm=bpy.data.objects['FruitHumanoid']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'models/pineapple.blend'))
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
    if ob.type in {'MESH','ARMATURE'}:ob.select_set(True)
glb=root/'models/pineapple.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_tangents=True,export_skins=True,export_all_influences=True,export_extras=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True,export_yup=True)
api['pack_vrm'](glb,root/'models/pineapple.vrm',[b.name for b in arm.data.bones],'Pineapple');glb.unlink()
scene=bpy.context.scene;scene.render.resolution_percentage=55;scene.cycles.samples=24
for expression in ['neutral','A','I','U','E','O','Blink','LookLeft','LookRight','LookUp','LookDown','JOY']:
    for name in ['Eye_L','Eye_R','Mouth']:
        for key in bpy.data.objects[name].data.shape_keys.key_blocks:
            key.value=1 if key.name==expression else 0
    scene.render.filepath=str(root/'previews'/f'pineapple-vseeface-{expression.lower()}.png')
    bpy.ops.render.render(write_still=True)
