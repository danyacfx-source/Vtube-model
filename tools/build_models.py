"""Build original fruit avatars with Blender 4.3+, then package VRM 0.0."""
import bpy, math, json, struct, pathlib
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[1]

def mat(name, color, rough=.65):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough
    return m

def sphere(name, loc, scale, material, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return o

def join(objects,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]; bpy.ops.object.join(); objects[0].name=name
    return objects[0]

def leaf(name, base, tip, width, material):
    b=Vector(base); t=Vector(tip); d=t-b
    side=Vector((d.z,0,-d.x)).normalized()*width
    mid=b+d*.52; ridge=mid+Vector((0,-.055,0))
    vs=[b, mid+side,t,mid-side,ridge]
    me=bpy.data.meshes.new(name); me.from_pydata(vs,[],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)]); me.materials.append(material)
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); return ob

def rig():
    bpy.ops.object.armature_add(location=(0,0,0)); arm=bpy.context.object; arm.name='FruitHumanoid'
    bpy.ops.object.mode_set(mode='EDIT'); eb=arm.data.edit_bones; eb.remove(eb[0])
    specs=[('hips',None,(0,0,.65),(0,0,.85)),('spine','hips',(0,0,.85),(0,0,1.05)),('chest','spine',(0,0,1.05),(0,0,1.25)),('neck','chest',(0,0,1.25),(0,0,1.4)),('head','neck',(0,0,1.4),(0,0,1.7))]
    for side,s in [('left',1),('right',-1)]:
        specs += [(side+'UpperLeg','hips',(s*.12,0,.65),(s*.12,0,.36)),(side+'LowerLeg',side+'UpperLeg',(s*.12,0,.36),(s*.12,0,.08)),(side+'Foot',side+'LowerLeg',(s*.12,0,.08),(s*.12,-.15,.04)),(side+'Shoulder','chest',(s*.04,0,1.22),(s*.2,0,1.22)),(side+'UpperArm',side+'Shoulder',(s*.2,0,1.22),(s*.43,0,1.22)),(side+'LowerArm',side+'UpperArm',(s*.43,0,1.22),(s*.65,0,1.22)),(side+'Hand',side+'LowerArm',(s*.65,0,1.22),(s*.76,0,1.22))]
    for name,parent,a,b in specs:
        bone=eb.new(name); bone.head=a; bone.tail=b
        if parent:bone.parent=eb[parent]
    bpy.ops.object.mode_set(mode='OBJECT'); return arm,[s[0] for s in specs]

def bind(obj,arm):
    vg=obj.vertex_groups.new(name='head'); vg.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    mod=obj.modifiers.new('Humanoid skin','ARMATURE'); mod.object=arm; obj.parent=arm

def pack_vrm(glb,out,bones,title):
    data=glb.read_bytes(); length,kind=struct.unpack_from('<II',data,12); doc=json.loads(data[20:20+length]); binary=data[20+length:]
    nodes={n.get('name'):i for i,n in enumerate(doc['nodes'])}
    groups=[]
    for preset,targets in [('blink',[('Eye_L','Blink'),('Eye_R','Blink')]),('blink_l',[('Eye_L','Blink')]),('blink_r',[('Eye_R','Blink')])]+[(x,[('Mouth',x.upper())]) for x in ['a','i','u','e','o']]+[('joy',[('Eye_L','Happy'),('Eye_R','Happy'),('Mouth','JOY')])]:
        binds=[]
        for meshname,key in targets:
            node=doc['nodes'][nodes[meshname]]; mi=node['mesh']; names=doc['meshes'][mi]['extras']['targetNames']
            binds.append({'mesh':mi,'index':names.index(key),'weight':100})
        groups.append({'name':preset,'presetName':preset,'binds':binds,'materialValues':[],'isBinary':False})
    materials=[]
    for m in doc.get('materials',[]):
        c=m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])
        materials.append({'name':m['name'],'shader':'VRM/MToon','renderQueue':2000,'floatProperties':{'_BlendMode':0,'_CullMode':2,'_ZWrite':1,'_Cutoff':.5,'_BumpScale':1,'_ReceiveShadowRate':1,'_ShadeShift':0,'_ShadeToony':.8,'_LightColorAttenuation':0,'_IndirectLightIntensity':.1,'_OutlineWidthMode':0,'_OutlineWidth':0,'_MToonVersion':38},'vectorProperties':{'_Color':c,'_ShadeColor':[c[0]*.72,c[1]*.72,c[2]*.72,1],'_EmissionColor':[0,0,0,1],'_MainTex':[0,0,1,1]},'textureProperties':{},'keywordMap':{},'tagMap':{'RenderType':'Opaque'}})
    doc.setdefault('extensions',{})['VRM']={'exporterVersion':'FruitAvatars-1.0','specVersion':'0.0','meta':{'title':title,'version':'1.0','author':'Vtube-model','contactInformation':'','reference':'','allowedUserName':'Everyone','violentUssageName':'Disallow','sexualUssageName':'Disallow','commercialUssageName':'Allow','otherPermissionUrl':'','licenseName':'CC0','otherLicenseUrl':''},'humanoid':{'humanBones':[{'bone':b,'node':nodes[b],'useDefaultValues':True} for b in bones],'armStretch':.05,'legStretch':.05,'upperArmTwist':.5,'lowerArmTwist':.5,'upperLegTwist':.5,'lowerLegTwist':.5,'feetSpacing':0,'hasTranslationDoF':False},'firstPerson':{'firstPersonBone':nodes['head'],'firstPersonBoneOffset':{'x':0,'y':0,'z':0},'meshAnnotations':[{'mesh':i,'firstPersonFlag':'Auto'} for i in range(len(doc['meshes']))],'lookAtTypeName':'Bone','lookAtHorizontalInner':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtHorizontalOuter':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtVerticalDown':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtVerticalUp':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10}},'blendShapeMaster':{'blendShapeGroups':groups},'secondaryAnimation':{'boneGroups':[],'colliderGroups':[]},'materialProperties':materials}
    doc.setdefault('extensionsUsed',[]).append('VRM')
    j=json.dumps(doc,separators=(',',':')).encode(); j+=b' '*((-len(j))%4)
    out.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+binary)

def build(kind):
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    orange=mat('Orange peel',(1,.26,.012)); yellow=mat('Golden pineapple',(.95,.53,.045)); rim=mat('Pineapple diamond edges',(.42,.21,.025)); green=mat('Leaf green',(.12,.44,.045)); lightgreen=mat('Leaf highlights',(.3,.66,.055)); black=mat('Chocolate eyes',(.035,.018,.012),.28); white=mat('Eye sparkle',(1,.97,.88)); blush=mat('Peach cheeks',(1,.22,.12)); mouthmat=mat('Mouth interior',(.16,.018,.035))
    arm,bones=rig(); static=[]
    if kind=='orange':
        static.append(sphere('Orange',(0,0,1.5),(.52,.43,.50),orange,64,40))
        static.append(sphere('Stem',(0,0,2),(.035,.035,.07),rim))
        static.append(leaf('Orange leaf',(0,0,2.01),(.36,-.02,2.12),.105,green))
        # Small low-poly dimples, concentrated away from the face.
        for row in range(11):
            lat=-1.15+row*.21
            for col in range(24):
                ang=col*math.tau/24+(row%2)*.13
                x=.522*math.cos(lat)*math.cos(ang); y=.432*math.cos(lat)*math.sin(ang); z=1.5+.502*math.sin(lat)
                if y<-.25 and abs(x)<.37 and 1.25<z<1.8:continue
                static.append(sphere('Peel detail',(x,y,z),(.007,.007,.007),yellow,8,4))
        face_y=-.421; eyez=1.61; mouthz=1.38; cheekz=1.46
    else:
        static.append(sphere('Pineapple core',(0,0,1.5),(.44,.34,.61),rim,48,32))
        # Raised golden scales follow the ellipsoid, leaving a smooth face panel.
        for row in range(12):
            lat=-1.25+row*.22
            for col in range(20):
                ang=col*math.tau/20+(row%2)*math.pi/20
                x=.443*math.cos(lat)*math.cos(ang); y=.343*math.cos(lat)*math.sin(ang); z=1.5+.613*math.sin(lat)
                o=sphere('Golden scale',(x,y,z),(.065,.035,.075),yellow,8,6)
                o.rotation_euler[2]=ang+math.pi/2; static.append(o)
        static.append(sphere('Smooth face',(0,-.315,1.5),(.325,.06,.32),yellow,40,24))
        for i in range(11):
            a=i*2.399; spread=.25 if i<7 else .12; h=.42+(i%3)*.08
            static.append(leaf('Crown leaf',(math.cos(a)*.055,math.sin(a)*.055,2.02),(math.cos(a)*spread,math.sin(a)*spread,2.02+h),.075,green if i%2 else lightgreen))
        face_y=-.373; eyez=1.62; mouthz=1.38; cheekz=1.47
    for s,side in [(-1,'L'),(1,'R')]:
        x=s*.165
        pieces=[sphere('Eye_'+side,(x,face_y,eyez),(.062,.031,.088),black),sphere('Glint',(x-.016,face_y-.029,eyez+.026),(.018,.008,.023),white,20,12),sphere('Glint small',(x+.02,face_y-.028,eyez-.025),(.008,.006,.01),white,16,8)]
        eye=join(pieces,'Eye_'+side); eye.shape_key_add(name='Basis')
        for name,factor in [('Blink',.055),('Happy',.3)]:
            key=eye.shape_key_add(name=name)
            for v in key.data:v.co.z*=factor
        bind(eye,arm)
        static.append(sphere('Blush',(s*.265,face_y+.015,cheekz),(.062,.018,.028),blush))
        static.append(sphere('Brow',(x,face_y+.02,eyez+.135),(.064,.018,.012),black))
    mouth=sphere('Mouth',(0,face_y-.008,mouthz),(.079,.022,.023),mouthmat,40,24); mouth.shape_key_add(name='Basis')
    for name,sx,sz in [('A',1,3.3),('I',1.4,1.4),('U',.55,2.3),('E',1.2,2.2),('O',.75,3.2),('JOY',1.45,1.8)]:
        key=mouth.shape_key_add(name=name)
        for v in key.data:v.co.x*=sx; v.co.z*=sz
    bind(mouth,arm); body=join(static,'Fruit_body'); bind(body,arm)
    bpy.ops.object.select_all(action='DESELECT')
    for o in [arm,body,mouth,bpy.data.objects['Eye_L'],bpy.data.objects['Eye_R']]:o.select_set(True)
    glb=ROOT/'models'/f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_skins=True,export_all_influences=True,export_extras=True,export_yup=True)
    pack_vrm(glb,ROOT/'models'/f'{kind}.vrm',bones, 'Orange' if kind=='orange' else 'Pineapple')
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=False
    scene.world.color=(.25,.25,.25); scene.render.resolution_x=800; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=True
    for loc,power,size in [((-3,-4,6),450,4),((3,-2,3),250,3),((0,3,4),350,3)]:
        bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.data.energy=power; o.data.shape='DISK'; o.data.size=size; o.rotation_euler=(Vector((0,0,1.6))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(.15,-5,2.3)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,1.7))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=1.95; scene.camera=cam
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/f'{kind}.blend'))
    scene.render.filepath=str(ROOT/'previews'/f'{kind}.png'); bpy.ops.render.render(write_still=True)
    glb.unlink()

for kind in ['orange','pineapple']:build(kind)
