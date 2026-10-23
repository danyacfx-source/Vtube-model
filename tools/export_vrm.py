"""Re-export existing Blender sources without regenerating geometry or renders."""
import bpy,pathlib,runpy
root=pathlib.Path(__file__).resolve().parents[1]
pack=runpy.run_path(str(root/'tools/build_models.py'))['pack_vrm']
for kind in ['orange','pineapple']:
    bpy.ops.wm.open_mainfile(filepath=str(root/'models'/f'{kind}.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    arm=bpy.data.objects['FruitHumanoid']
    for ob in bpy.context.scene.objects:
        if ob.type in {'MESH','ARMATURE'}:ob.select_set(True)
    glb=root/'models'/f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_tangents=True,export_skins=True,export_all_influences=True,export_extras=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True,export_yup=True)
    pack(glb,root/'models'/f'{kind}.vrm',[b.name for b in arm.data.bones],kind.title());glb.unlink()
