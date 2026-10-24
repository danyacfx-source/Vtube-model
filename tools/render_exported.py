"""Render the actual exported glTF payload, independently of the source meshes."""
import bpy,pathlib,shutil,sys
root=pathlib.Path(__file__).resolve().parents[1]
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['orange','pineapple']
for kind in selected:
    assert kind in {'orange','pineapple'}
    bpy.ops.wm.open_mainfile(filepath=str(root/'models'/f'{kind}.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.context.scene.objects:
        if ob.type in {'MESH','ARMATURE'}:ob.select_set(True)
    bpy.ops.object.delete(use_global=False)
    dest=pathlib.Path('/tmp')/f'fruit-{kind}-roundtrip.glb';shutil.copyfile(root/'models'/f'{kind}.vrm',dest)
    bpy.ops.import_scene.gltf(filepath=str(dest))
    scene=bpy.context.scene;scene.render.resolution_percentage=50;scene.cycles.samples=32
    scene.render.filepath=str(root/'validation'/f'{kind}-roundtrip.png');bpy.ops.render.render(write_still=True)
