"""Render actual rig turns to prove the visible fruit follows the head bone."""
import bpy,pathlib,math
root=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'models/pineapple.blend'))
scene=bpy.context.scene;scene.render.resolution_percentage=52;scene.cycles.samples=24
arm=bpy.data.objects['FruitHumanoid'];head=arm.pose.bones['head'];head.rotation_mode='XYZ'
# Blender bones point along local Y: yaw therefore uses pose-bone Y, while Z
# is the familiar in-plane head roll.
states=[('front',0,0,0),('left45',0,math.radians(-45),0),('right45',0,math.radians(45),0),('profile',0,math.radians(90),0),('back',0,math.pi,0),('tilt',math.radians(12),math.radians(-18),math.radians(-22))]
for label,x,y,z in states:
    head.rotation_euler=(x,y,z);scene.render.filepath=str(root/'previews'/f'pineapple-tracking-{label}.png');bpy.ops.render.render(write_still=True)
head.rotation_euler=(0,0,0)
