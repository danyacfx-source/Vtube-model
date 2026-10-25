"""Render real Blender expression previews from the saved source."""
import bpy,pathlib
root=pathlib.Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(root/'output/DENDICH_RADIO_SILENCE.blend'))
scene=bpy.context.scene;cam=scene.camera;cam.location=(0,-3.0,2.03);scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100
states={'neutral':{},'smile':{'Mouth':'Smile'},'laugh':{'Mouth':'A','Eye_L':'Squint','Eye_R':'Squint'},'tired':{'Eye_L':'Tired','Eye_R':'Tired'},'serious':{'Eye_L':'Squint','Eye_R':'Squint'},'irritated':{'Mouth':'Irritated','Eye_L':'Squint','Eye_R':'Squint'},'surprise':{'Mouth':'Surprised','Eye_L':'Wide','Eye_R':'Wide'},'awkward':{'Mouth':'Awkward'},'what-the-hell':{'Mouth':'Awkward','Eye_L':'Squint'}}
for label,active in states.items():
    for name in ['Eye_L','Eye_R','Mouth']:
        for key in bpy.data.objects[name].data.shape_keys.key_blocks:key.value=1 if active.get(name)==key.name else 0
    scene.render.filepath=str(root/'renders'/f'DENDICH_expression_{label}.png');bpy.ops.render.render(write_still=True)
