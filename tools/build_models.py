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
    for preset,targets in [('blink',[('Eye_L','Blink'),('Eye_R','Blink')]),('blink_l',[('Eye_L','Blink')]),('blink_r',[('Eye_R','Blink')])]+[(x,[('Mouth',x.upper())]) for x in ['a','i','u','e','o']]+[('joy',[('Eye_L','Happy'),('Eye_R','Happy'),('Mouth','JOY')]),('sorrow',[('Mouth','SORROW')]),('angry',[('Mouth','ANGRY')]),('fun',[('Mouth','JOY')])]:
        binds=[]
        for meshname,key in targets:
            node=doc['nodes'][nodes[meshname]]; mi=node['mesh']; names=doc['meshes'][mi]['extras']['targetNames']
            binds.append({'mesh':mi,'index':names.index(key),'weight':100})
        groups.append({'name':preset,'presetName':preset,'binds':binds,'materialValues':[],'isBinary':False})
    materials=[]
    for m in doc.get('materials',[]):
        c=m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])
        materials.append({'name':m['name'],'shader':'VRM/MToon','renderQueue':2000,'floatProperties':{'_BlendMode':0,'_CullMode':2,'_ZWrite':1,'_Cutoff':.5,'_BumpScale':1,'_ReceiveShadowRate':1,'_ShadeShift':0,'_ShadeToony':.8,'_LightColorAttenuation':0,'_IndirectLightIntensity':.1,'_OutlineWidthMode':0,'_OutlineWidth':0,'_MToonVersion':38},'vectorProperties':{'_Color':c,'_ShadeColor':[c[0]*.72,c[1]*.72,c[2]*.72,1],'_EmissionColor':[0,0,0,1],'_MainTex':[0,0,1,1]},'textureProperties':{},'keywordMap':{},'tagMap':{'RenderType':'Opaque'}})
    for source, target in zip(doc.get('materials', []), materials):
        tex=source.get('pbrMetallicRoughness',{}).get('baseColorTexture')
        if tex:
            target['textureProperties']={'_MainTex':tex['index'],'_ShadeTexture':tex['index']}
    doc.setdefault('extensions',{})['VRM']={'exporterVersion':'FruitAvatars-2.0','specVersion':'0.0','meta':{'title':title,'version':'2.0','author':'Vtube-model','contactInformation':'','reference':'','allowedUserName':'Everyone','violentUssageName':'Disallow','sexualUssageName':'Disallow','commercialUssageName':'Allow','otherPermissionUrl':'','licenseName':'CC0','otherLicenseUrl':''},'humanoid':{'humanBones':[{'bone':b,'node':nodes[b],'useDefaultValues':True} for b in bones],'armStretch':.05,'legStretch':.05,'upperArmTwist':.5,'lowerArmTwist':.5,'upperLegTwist':.5,'lowerLegTwist':.5,'feetSpacing':0,'hasTranslationDoF':False},'firstPerson':{'firstPersonBone':nodes['head'],'firstPersonBoneOffset':{'x':0,'y':0,'z':0},'meshAnnotations':[{'mesh':i,'firstPersonFlag':'Auto'} for i in range(len(doc['meshes']))],'lookAtTypeName':'Bone','lookAtHorizontalInner':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtHorizontalOuter':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtVerticalDown':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtVerticalUp':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10}},'blendShapeMaster':{'blendShapeGroups':groups},'secondaryAnimation':{'boneGroups':[],'colliderGroups':[]},'materialProperties':materials}
    doc.setdefault('extensionsUsed',[]).append('VRM')
    j=json.dumps(doc,separators=(',',':')).encode(); j+=b' '*((-len(j))%4)
    out.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+binary)

# Version 2: UV-painted continuous skin, curved foliage and expressive face meshes.
import numpy as np

def mesh_object(name, vertices, faces, material):
    me=bpy.data.meshes.new(name); me.from_pydata(vertices,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); me.materials.append(material)
    for p in me.polygons:p.use_smooth=True
    return ob

def skin_material(kind):
    size=1024; yy,xx=np.mgrid[0:size,0:size].astype(float); u=xx/size; v=yy/size
    rng=np.random.default_rng(419)
    if kind=='orange':
        # Subtle pores are painted into the embedded texture, not floating beads.
        grain=rng.random((size,size)); pore=np.maximum(0,(grain-.88)/.12)
        brightness=1-.09*pore+.025*np.sin(u*math.tau*9)*np.sin(v*math.pi*7)
        rgb=np.stack([.98*brightness, (.40+.10*v)*brightness, (.025+.018*v)*brightness],axis=-1)
    else:
        # Interlocking diagonal grooves, with a small star in each scale.
        a=u*18+v*12; b=u*18-v*12
        da=np.abs((a+.5)%1-.5); db=np.abs((b+.5)%1-.5)
        groove=np.exp(-(np.minimum(da,db)/.045)**2)
        border=np.exp(-(np.minimum(da,db)/.085)**2)
        mid=np.sin(math.pi*a)**2*np.sin(math.pi*b)**2
        brightness=.82+.18*mid-.30*groove-.06*border
        # Quiet the pattern behind the face, with a soft boundary.
        front=np.minimum(abs(u-.75),1-abs(u-.75))
        clear=np.exp(-((front/.14)**6+((v-.52)/.24)**6))
        brightness=brightness*(1-clear)+(.97+.015*mid)*clear
        rgb=np.stack([.97*brightness,(.59+.08*v)*brightness,.10*brightness],axis=-1)
        rgb+=rng.normal(0,.004,(size,size,1))
    rgba=np.concatenate([np.clip(rgb,0,1),np.ones((size,size,1))],axis=-1).astype(np.float32)
    im=bpy.data.images.new(kind+'_skin_1k',width=size,height=size); im.pixels.foreach_set(rgba.ravel()); im.pack()
    m=mat(kind+' painted skin',(1,1,1),.62); nodes=m.node_tree.nodes
    tex=nodes.new('ShaderNodeTexImage'); tex.image=im
    m.node_tree.links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
    return m

RADII={ 'orange':(.53,.46,.49), 'pineapple':(.44,.37,.57) }

def surface(kind,x,z,offset=0):
    rx,ry,rz=RADII[kind]; h=(z-1.5)/rz
    if kind=='pineapple':
        width=max(.001,1-abs(h)**3.3)**.5
        y=-ry*width*math.sqrt(max(.01,1-(x/(rx*width))**2))
    else:y=-ry*math.sqrt(max(.01,1-(x/rx)**2-h*h))
    return y-offset

def fruit_body(kind,material):
    rx,ry,rz=RADII[kind]; n=160; rings=96; verts=[]; uv=[]; faces=[]
    for j in range(rings+1):
        v=j/rings; lat=(v-.5)*math.pi; h=math.sin(lat)
        width=math.cos(lat) if kind=='orange' else max(0,1-abs(h)**3.3)**.5
        for i in range(n+1):
            u=i/n; a=u*math.tau
            bump=.0008*math.sin(a*77+lat*57)*math.sin(lat*103) if kind=='orange' else 0
            if kind=='pineapple':
                da=abs(((u*18+v*12+.5)%1)-.5); db=abs(((u*18-v*12+.5)%1)-.5)
                clear=math.exp(-((abs(u-.75)/.14)**6+((v-.52)/.24)**6))
                bump=.005*(math.sin(math.pi*(u*18+v*12))**2*math.sin(math.pi*(u*18-v*12))**2)*(1-clear)
            verts.append(((rx*width+bump)*math.cos(a),(ry*width+bump)*math.sin(a),1.5+rz*h)); uv.append((u,v))
    for j in range(rings):
        for i in range(n):
            k=j*(n+1)+i; faces.append((k,k+1,k+n+2,k+n+1))
    ob=mesh_object('Fruit_body',verts,faces,material); layer=ob.data.uv_layers.new(name='UVMap')
    for p in ob.data.polygons:
        for li in p.loop_indices:layer.data[li].uv=uv[ob.data.loops[li].vertex_index]
    return ob

def ribbon(name,base,tip,width,material,bend=.1):
    base=Vector(base); tip=Vector(tip); d=tip-base; side=Vector((d.z,0,-d.x)).normalized()
    verts=[]; faces=[]; steps=18
    for i in range(steps+1):
        t=i/steps; c=base+d*t+Vector((0,-bend*math.sin(math.pi*t),.07*math.sin(math.pi*t)))
        w=width*math.sin(math.pi*t)**.8+.0003
        for j in range(5):
            q=(j-2)/2; v=c+side*w*q+Vector((0,-.022*(1-q*q)*math.sin(math.pi*t),0)); verts.append(tuple(v))
    for i in range(steps):
        for j in range(4):k=i*5+j;faces.append((k,k+1,k+6,k+5))
    ob=mesh_object(name,verts,faces,material)
    solid=ob.modifiers.new('Leaf thickness','SOLIDIFY');solid.thickness=.004
    bpy.context.view_layer.objects.active=ob; bpy.ops.object.modifier_apply(modifier=solid.name)
    return ob

def tube(name,points,radius,material):
    curve=bpy.data.curves.new(name,'CURVE'); curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=3
    sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(ob);ob.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def patch(name,kind,cx,cz,wx,hz,material,offset=.008):
    verts=[(cx,surface(kind,cx,cz,offset),cz)];faces=[]
    for i in range(64):
        a=i*math.tau/64;x=cx+wx*math.cos(a);z=cz+hz*math.sin(a);verts.append((x,surface(kind,x,z,offset),z))
    for i in range(64):faces.append((0,1+i,1+(i+1)%64))
    return mesh_object(name,verts,faces,material)

def make_mouth(kind,dark,tongue,teeth,outline):
    # One continuous smile silhouette; inner patches deform with every vowel.
    params={'Basis':(.105,.019,.033),'A':(.098,.100,.014),'I':(.145,.042,.018),'U':(.052,.068,0),'E':(.128,.071,.016),'O':(.070,.093,0),'JOY':(.142,.088,.035),'SORROW':(.095,.012,-.030),'ANGRY':(.11,.021,-.012)}
    cz=1.345; pieces=[]
    def coords(p,layer):
        w,h,curve=p; vs=[]
        for j in range(9):
            r=j/8
            for i in range(64):
                a=math.tau*i/64; xx=r*math.cos(a); zz=r*math.sin(a)
                if layer==0:x=w*xx;z=cz+h*zz+curve*(xx*xx)
                elif layer==1:x=w*.64*xx;z=cz-h*.55+h*.28*zz+curve*(.64*xx)**2
                else:x=w*.70*xx;z=cz+h*.67+h*.13*zz+curve*(.70*xx)**2
                off=.012+layer*.002
                vs.append((x,surface(kind,x,z,off),z))
        return vs
    faces=[]
    for j in range(8):
        for i in range(64):k=j*64+i;n=j*64+(i+1)%64;faces.append((k,k+64,n+64,n))
    for layer,material in enumerate([dark,tongue,teeth]):
        ob=mesh_object('MouthLayer',coords(params['Basis'],layer),faces,material);ob.shape_key_add(name='Basis')
        for name,p in params.items():
            if name=='Basis':continue
            key=ob.shape_key_add(name=name)
            for v,co in zip(key.data,coords(p,layer)):v.co=co
        pieces.append(ob)
    return join(pieces,'Mouth')

def build(kind):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    skin=skin_material(kind);green=mat('Deep leaf green',(.045,.22,.012));lightgreen=mat('Fresh leaf green',(.12,.39,.022));vein=mat('Leaf veins',(.26,.48,.045));stem=mat('Natural stem',(.18,.075,.022))
    dark=mat('Espresso outline',(.018,.008,.006),.48);white=mat('Warm eye white',(.95,.89,.73),.3);spark=mat('Catchlights',(1,1,.98),.18)
    iris=mat('Amber iris',(.26,.075,.012),.24) if kind=='orange' else mat('Teal iris',(.012,.19,.14),.24)
    irisl=mat('Iris lower light',(.68,.27,.025),.3) if kind=='orange' else mat('Jade lower light',(.035,.40,.25),.3)
    cheek=mat('Soft apricot blush',(.95,.20,.055));mouthdark=mat('Mouth interior',(.065,.007,.012));tongue=mat('Tongue',(.91,.14,.19));teeth=mat('Smile ivory',(1,.91,.75))
    arm,bones=rig();static=[fruit_body(kind,skin)]
    if kind=='orange':
        static.append(tube('Curved stem',[(0,0,1.98),(.005,0,2.04),(.035,.008,2.09)],.018,stem))
        static.append(ribbon('Broad citrus leaf',(.015,0,2.04),(.38,.025,2.17),.115,green,.09))
        static.append(tube('Leaf midrib',[(.02,-.006,2.045),(.12,-.09,2.12),(.25,-.065,2.16),(.37,.02,2.17)],.0035,vein))
        static.append(ribbon('Small citrus leaf',(.005,.02,2.02),(-.19,.05,2.13),.063,lightgreen,.045))
    else:
        # Broad recurved outer leaves and a tall, layered central crown.
        for row,count in [(0,9),(1,7),(2,5)]:
            for i in range(count):
                a=i*math.tau/count+row*.5;spread=[.36,.26,.13][row];height=[.30,.43,.56][row]
                base=(.055*math.cos(a),.055*math.sin(a),2.005+row*.015)
                tip=(spread*math.cos(a),spread*math.sin(a),2.005+height+(i%2)*.035)
                static.append(ribbon('Crown blade',base,tip,[.075,.062,.047][row],green if i%3 else lightgreen,.08))
    # Larger inset-looking eyes, colored irises and highlights; no protruding eyebrow rods.
    for s,side in [(-1,'L'),(1,'R')]:
        x=s*.183;z=1.60;y=surface(kind,x,z,.012)
        pieces=[sphere('Eye_'+side,(x,y,z),(.100,.025,.128),dark,40,28),sphere('Sclera',(x,y-.018,z),(.088,.019,.115),white,40,28),sphere('Iris',(x+s*.005,y-.035,z-.005),(.065,.013,.088),iris,40,24),sphere('Iris glow',(x+s*.005,y-.045,z-.036),(.050,.007,.045),irisl,32,20),sphere('Pupil',(x+s*.005,y-.050,z+.004),(.043,.009,.064),dark,32,24),sphere('Large catchlight',(x-.025,y-.061,z+.046),(.023,.006,.028),spark,24,16),sphere('Small catchlight',(x+.026,y-.058,z-.034),(.010,.005,.012),spark,20,12)]
        eye=join(pieces,'Eye_'+side);eye.shape_key_add(name='Basis')
        light_vertices={vi for polygon in eye.data.polygons if eye.data.materials[polygon.material_index]!=dark for vi in polygon.vertices}
        for name in ['Blink','Happy']:
            key=eye.shape_key_add(name=name)
            for vi,v in enumerate(key.data):
                # Full closure becomes a curved eyelid; retract light-colored layers.
                xx=v.co.x; original_z=v.co.z
                v.co.z=original_z*.025+( .020 if name=='Happy' else -.010)*(1-(xx/.1)**2)
                v.co.y=surface(kind,x+xx,z+v.co.z,.004)-y
                if vi in light_vertices:v.co.y+=.065
        bind(eye,arm)
        points=[]
        for i in range(25):
            t=i/24;xx=x+(t-.5)*.145;zz=1.778+.022*math.sin(math.pi*t)+(s*.012)*(t-.5)
            points.append((xx,surface(kind,xx,zz,.010),zz))
        static.append(tube('Expressive brow',points,.008,dark))
        static.append(patch('Cheek',kind,s*.294,1.445,.052,.019,cheek,.0025))
        for i in range(3):static.append(patch('Freckle',kind,s*(.264+i*.025),1.465+(i%2)*.012,.004,.004,stem,.01))
    mouth=make_mouth(kind,mouthdark,tongue,teeth,dark);bind(mouth,arm)
    body=join(static,'Fruit_body');bind(body,arm)
    bpy.ops.object.select_all(action='DESELECT')
    for o in [arm,body,mouth,bpy.data.objects['Eye_L'],bpy.data.objects['Eye_R']]:o.select_set(True)
    glb=ROOT/'models'/f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_skins=True,export_all_influences=True,export_extras=True,export_yup=True)
    pack_vrm(glb,ROOT/'models'/f'{kind}.vrm',bones,'Orange' if kind=='orange' else 'Pineapple');glb.unlink()
    bpy.context.preferences.filepaths.save_version=0;scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
    scene.world.color=(.16,.16,.16);scene.view_settings.view_transform='AgX'
    scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    for loc,power,size in [((-3,-4,6),350,4),((3,-2,3),160,3),((1,3,4),450,3)]:
        bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector((0,0,1.6))-ob.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(.10,-5,2.02));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.76 if kind=='pineapple' else 1.68))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.0 if kind=='pineapple' else 1.6;scene.camera=cam
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/f'{kind}.blend'))
    scene.render.filepath=str(ROOT/'previews'/f'{kind}.png');bpy.ops.render.render(write_still=True)
    # Exercise actual shape keys in an additional render, rather than only inspecting metadata.
    for name in ['Eye_L','Eye_R']:bpy.data.objects[name].data.shape_keys.key_blocks['Happy'].value=1
    mouth.data.shape_keys.key_blocks['JOY'].value=1
    scene.render.resolution_percentage=65;scene.render.filepath=str(ROOT/'previews'/f'{kind}-joy.png');bpy.ops.render.render(write_still=True)

for kind in ['orange','pineapple']:build(kind)
