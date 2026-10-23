"""Check facial triangles against the real peel, for every individual expression."""
import bpy,pathlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path(__file__).resolve().parents[1]
failures=[]
for kind in ['orange','pineapple']:
    bpy.ops.wm.open_mainfile(filepath=str(root/'models'/f'{kind}.blend'))
    body=bpy.data.objects['Fruit_body'];verts=[body.matrix_world@v.co for v in body.data.vertices]
    bvh=BVHTree.FromPolygons(verts,[tuple(p.vertices) for p in body.data.polygons])
    if kind=='pineapple':
        scales=[p for p in body.data.polygons if 'pineapple natural skin' in body.data.materials[p.material_index].name]
        inward=sum(p.normal.dot(p.center-Vector((0,0,1.5))) < -.0001 for p in scales)
        assert scales and inward/len(scales)<.02, 'Pineapple fruitlet normals point inward'
    for name in ['Eye_L','Eye_R','Mouth']:
        ob=bpy.data.objects[name];colors=ob.data.color_attributes['Color'].data
        for key in ob.data.shape_keys.key_blocks:
            bad=0;minimum=1
            for poly in ob.data.polygons:
                if sum(colors[i].color[3] for i in poly.vertices)/len(poly.vertices)<.5:continue
                center=sum((ob.matrix_world@key.data[i].co for i in poly.vertices),Vector())/len(poly.vertices)
                hit=bvh.ray_cast(Vector((center.x,-3,center.z)),Vector((0,1,0)))[0]
                if hit is not None:
                    clearance=hit.y-center.y;minimum=min(minimum,clearance)
                    if clearance<-.001:bad+=1
            if bad:failures.append(f'{kind} {name} {key.name}: {bad} triangles inside peel, minimum {minimum:.5f}')
    print(kind,'facial clearance checked')
for f in failures:print(f)
assert not failures, 'Face/peel intersections remain'
