"""Replace only pineapple face geometry; preserve its textured body and rig."""
import pathlib,runpy,math
import bpy
from mathutils.bvhtree import BVHTree

root=pathlib.Path(__file__).resolve().parents[1]
api=runpy.run_path(str(root/'tools/build_models.py'))
make=runpy.run_path(str(root/'tools/cartoon_face.py'))['make_feature']
accent=runpy.run_path(str(root/'tools/cartoon_face.py'))['make_accent']
bpy.ops.wm.open_mainfile(filepath=str(root/'models/pineapple.blend'))
body=bpy.data.objects['Fruit_body'];arm=bpy.data.objects['FruitHumanoid']
humanoid=[b.name for b in arm.data.bones if not b.name.startswith('leaf_spring_')]
api['surface'].__globals__['FACE_SURFACE']=BVHTree.FromPolygons([body.matrix_world@v.co for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons])
for name in ['Eye_L','Eye_R','Mouth','Cheek_L','Cheek_R']:
    if bpy.data.objects.get(name):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
for name,cx,cz in [('Eye_L',-.18,1.63),('Eye_R',.18,1.63),('Mouth',0,1.32)]:
    ob=make(api,name,cx,cz,name=='Mouth');api['bind'](ob,arm)
# Six spring bones distribute the upper crown by angle. Bases stay on the head;
# tips inherit the spring bone progressively, avoiding a detached-looking crown.
bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for bone in list(arm.data.edit_bones):
    if bone.name.startswith('leaf_spring_'):arm.data.edit_bones.remove(bone)
for i in range(6):
    a=math.tau*i/6;b=arm.data.edit_bones.new(f'leaf_spring_{i}');b.head=(0,0,2.02);b.tail=(.30*math.cos(a),.30*math.sin(a),2.48);b.parent=arm.data.edit_bones['head']
bpy.ops.object.mode_set(mode='OBJECT')
head=body.vertex_groups.get('head')
groups=[body.vertex_groups.new(name=f'leaf_spring_{i}') for i in range(6)]
for v in body.data.vertices:
    if v.co.z<=2.04:continue
    angle=(math.atan2(v.co.y,v.co.x)+math.tau)%math.tau;index=int((angle+math.pi/6)/math.tau*6)%6;w=min(.88,max(0,(v.co.z-2.04)/.38))
    head.add([v.index],1-w,'REPLACE');groups[index].add([v.index],w,'REPLACE')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'models/pineapple.blend'))
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
    if ob.type in {'MESH','ARMATURE'}:ob.select_set(True)
glb=root/'models/pineapple.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_tangents=True,export_skins=True,export_all_influences=True,export_extras=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True,export_yup=True)
api['pack_vrm'](glb,root/'models/pineapple.vrm',humanoid,'Pineapple');glb.unlink()
scene=bpy.context.scene;scene.render.resolution_percentage=55;scene.cycles.samples=24
for expression in ['neutral','A','I','U','E','O','Blink','Happy','LookLeft','LookRight','LookUp','LookDown','JOY','SORROW','ANGRY','joy-blink']:
    for name in ['Eye_L','Eye_R','Mouth']:
        for key in bpy.data.objects[name].data.shape_keys.key_blocks:
            active=key.name==expression or (expression in {'JOY','joy-blink'} and key.name in {'Happy','JOY'}) or (expression=='joy-blink' and key.name=='Blink')
            key.value=1 if active else 0
    scene.render.filepath=str(root/'previews'/f'pineapple-cartoon-{expression.lower()}.png');bpy.ops.render.render(write_still=True)
