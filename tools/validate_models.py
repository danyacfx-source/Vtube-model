"""Check the VRM 0 skeleton, face bindings and binary container."""
import json, pathlib, struct
root=pathlib.Path(__file__).resolve().parents[1]
required={'hips','spine','chest','neck','head'}|{s+b for s in ('left','right') for b in ('UpperArm','LowerArm','Hand','UpperLeg','LowerLeg','Foot')}
for path in sorted((root/'models').glob('*.vrm')):
    data=path.read_bytes(); magic,version,size=struct.unpack_from('<III',data)
    assert (magic,version,size)==(0x46546c67,2,len(data))
    n,t=struct.unpack_from('<II',data,12); assert t==0x4e4f534a
    doc=json.loads(data[20:20+n]); v=doc['extensions']['VRM']; assert v['specVersion']=='0.0'
    bones={b['bone']:b['node'] for b in v['humanoid']['humanBones']}; assert required<=bones.keys()
    assert len(set(bones.values()))==len(bones)
    assert all(0<=i<len(doc['nodes']) for i in bones.values())
    skin_nodes=[n for n in doc['nodes'] if 'mesh' in n]
    assert len(skin_nodes)==4 and all('skin' in n for n in skin_nodes)
    for node in skin_nodes:
        skin=doc['skins'][node['skin']]; assert bones['head'] in skin['joints']
        for p in doc['meshes'][node['mesh']]['primitives']:
            assert {'POSITION','JOINTS_0','WEIGHTS_0'}<=p['attributes'].keys()
    groups={g['presetName']:g for g in v['blendShapeMaster']['blendShapeGroups']}
    assert {'a','i','u','e','o','blink','blink_l','blink_r','joy','sorrow','angry','fun'}<=groups.keys()
    for g in groups.values():
        assert g['binds']
        for b in g['binds']:
            mesh=doc['meshes'][b['mesh']]
            assert b['weight']==100
            for p in mesh['primitives']:
                target=p['targets'][b['index']]['POSITION']; acc=doc['accessors'][target]
                assert any(abs(x)>1e-6 for x in acc['min']+acc['max']), 'Empty expression'
    assert len(v['materialProperties'])==len(doc['materials'])
    assert v['meta']['version']=='3.0'
    textured=[(m,vm) for m,vm in zip(doc['materials'],v['materialProperties']) if 'baseColorTexture' in m.get('pbrMetallicRoughness',{})]
    assert textured, 'Skin texture must be embedded for VSeeFace'
    for m,vm in textured:
        ti=m['pbrMetallicRoughness']['baseColorTexture']['index']
        assert vm['textureProperties']['_MainTex']==ti
        image=doc['images'][doc['textures'][ti]['source']]
        assert 'bufferView' in image and image['mimeType']=='image/png'
    normal_materials=[(m,vm) for m,vm in zip(doc['materials'],v['materialProperties']) if 'normalTexture' in m]
    assert normal_materials, 'Realistic peel normal map missing'
    for m,vm in normal_materials:
        assert vm['textureProperties']['_BumpMap']==m['normalTexture']['index']
        assert vm['keywordMap']['_NORMALMAP']
    assert all('uri' not in image for image in doc.get('images',[])), 'External image dependency'

    triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])
    print(f'{path.name}: PASS; {len(bones)} humanoid bones, {len(groups)} expression presets, {triangles:,} triangles')
