"""Structural checks for the exported VRM 1.0 avatar."""
import json,struct,pathlib
root=pathlib.Path(__file__).resolve().parents[1];path=root/'output/DENDICH_RADIO_SILENCE.vrm';data=path.read_bytes()
magic,version,total=struct.unpack_from('<III',data);assert (magic,version,total)==(0x46546c67,2,len(data))
n,t=struct.unpack_from('<II',data,12);assert t==0x4e4f534a;doc=json.loads(data[20:20+n])
assert {'VRMC_vrm','VRMC_springBone'}<=set(doc['extensionsUsed'])
vrm=doc['extensions']['VRMC_vrm'];assert vrm['specVersion']=='1.0'
bones=vrm['humanoid']['humanBones'];required={'hips','spine','chest','neck','head','leftUpperArm','leftLowerArm','leftHand','rightUpperArm','rightLowerArm','rightHand','leftUpperLeg','leftLowerLeg','leftFoot','rightUpperLeg','rightLowerLeg','rightFoot'}
assert required<=bones.keys();assert all(0<=x['node']<len(doc['nodes']) for x in bones.values())
presets=vrm['expressions']['preset'];assert {'blink','blinkLeft','blinkRight','aa','ih','ou','ee','oh','happy','sad','angry','relaxed','surprised','lookLeft','lookRight','lookUp','lookDown'}<=presets.keys()
assert {'tired','serious','irritated','awkward','what_the_hell'}<=vrm['expressions']['custom'].keys()
for expression in list(presets.values())+list(vrm['expressions']['custom'].values()):
    assert expression.get('morphTargetBinds')
    for bind in expression['morphTargetBinds']:
        node=doc['nodes'][bind['node']];mesh=doc['meshes'][node['mesh']]
        assert 0<=bind['index']<len(mesh['primitives'][0]['targets']) and bind['weight']==1
spring=doc['extensions']['VRMC_springBone'];assert spring['specVersion']=='1.0' and len(spring['springs'])==10
assert all(len(s['joints'])==2 and s['colliderGroups']==[0] for s in spring['springs'])
assert any(n.get('name')=='Patch_DENDICH' for n in doc['nodes']);assert any(n.get('name')=='Patch_RADIO_SILENCE' for n in doc['nodes'])
assert all('uri' not in im for im in doc.get('images',[]))
tris=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])
print(f'PASS: VRM 1.0, {len(bones)} humanoid bones, {len(presets)} presets, {len(vrm["expressions"]["custom"])} custom expressions, 10 hair springs, {tris:,} triangles')
