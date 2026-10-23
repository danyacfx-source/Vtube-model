"""Render the exported source expression states for visual inspection."""
import bpy, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
for kind in ['orange','pineapple']:
    bpy.ops.wm.open_mainfile(filepath=str(root/'models'/f'{kind}.blend'))
    scene=bpy.context.scene;scene.render.resolution_percentage=40;scene.cycles.samples=24
    for expression in ['A','I','U','E','O','Blink','SORROW','ANGRY']:
        for name in ['Eye_L','Eye_R','Mouth']:
            keys=bpy.data.objects[name].data.shape_keys.key_blocks
            for key in keys:key.value=0
            if expression in keys:keys[expression].value=1
        scene.render.filepath=str(root/'previews'/f'{kind}-{expression.lower()}.png')
        bpy.ops.render.render(write_still=True)
