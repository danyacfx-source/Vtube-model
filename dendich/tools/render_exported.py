"""Round-trip render the actual exported VRM payload."""
import bpy,pathlib,shutil
from mathutils import Vector
root=pathlib.Path(__file__).resolve().parents[1];src=root/'output/DENDICH_RADIO_SILENCE.vrm';tmp=pathlib.Path('/tmp/DENDICH_roundtrip.glb');shutil.copyfile(src,tmp)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(tmp))
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=700;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True;scene.view_settings.look='AgX - Medium High Contrast'
for loc,power,size in [((-3,-4,5),900,4),((3,-2,3),650,3),((0,2,4),800,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.4,-4.2,1.75));cam=bpy.context.object;cam.data.lens=62;cam.rotation_euler=(Vector((0,0,1.58))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
scene.render.filepath=str(root/'renders/DENDICH_exported_roundtrip.png');bpy.ops.render.render(write_still=True)
