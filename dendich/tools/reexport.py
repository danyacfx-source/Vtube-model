"""Re-export the saved source after VRM metadata or binding changes."""
import bpy,pathlib,runpy
root=pathlib.Path(__file__).resolve().parents[1];api=runpy.run_path(str(root/'tools/build_dendich.py'))
bpy.ops.wm.open_mainfile(filepath=str(root/'output/DENDICH_RADIO_SILENCE.blend'))
api['export_vrm1'](bpy.data.objects['DENDICH_Rig'])
