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
        materials.append({'name':m['name'],'shader':'VRM/MToon','renderQueue':2000,'floatProperties':{'_BlendMode':0,'_CullMode':2,'_ZWrite':1,'_Cutoff':.5,'_BumpScale':1,'_ReceiveShadowRate':1,'_ShadeShift':0,'_ShadeToony':.15,'_LightColorAttenuation':0,'_IndirectLightIntensity':.1,'_OutlineWidthMode':0,'_OutlineWidth':0,'_MToonVersion':38},'vectorProperties':{'_Color':c,'_ShadeColor':[c[0]*.62,c[1]*.62,c[2]*.62,1],'_EmissionColor':[0,0,0,1],'_MainTex':[0,0,1,1]},'textureProperties':{},'keywordMap':{},'tagMap':{'RenderType':'Opaque'}})
    for source, target in zip(doc.get('materials', []), materials):
        tex=source.get('pbrMetallicRoughness',{}).get('baseColorTexture')
        if tex:
            target['textureProperties']={'_MainTex':tex['index'],'_ShadeTexture':tex['index']}
        normal=source.get('normalTexture')
        if normal:
            target['textureProperties']['_BumpMap']=normal['index']
            target['keywordMap']['_NORMALMAP']=True
    doc.setdefault('extensions',{})['VRM']={'exporterVersion':'FruitAvatars-3.0','specVersion':'0.0','meta':{'title':title,'version':'3.0','author':'Vtube-model','contactInformation':'','reference':'','allowedUserName':'Everyone','violentUssageName':'Disallow','sexualUssageName':'Disallow','commercialUssageName':'Allow','otherPermissionUrl':'','licenseName':'CC0','otherLicenseUrl':''},'humanoid':{'humanBones':[{'bone':b,'node':nodes[b],'useDefaultValues':True} for b in bones],'armStretch':.05,'legStretch':.05,'upperArmTwist':.5,'lowerArmTwist':.5,'upperLegTwist':.5,'lowerLegTwist':.5,'feetSpacing':0,'hasTranslationDoF':False},'firstPerson':{'firstPersonBone':nodes['head'],'firstPersonBoneOffset':{'x':0,'y':0,'z':0},'meshAnnotations':[{'mesh':i,'firstPersonFlag':'Auto'} for i in range(len(doc['meshes']))],'lookAtTypeName':'Bone','lookAtHorizontalInner':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtHorizontalOuter':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtVerticalDown':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtVerticalUp':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10}},'blendShapeMaster':{'blendShapeGroups':groups},'secondaryAnimation':{'boneGroups':[],'colliderGroups':[]},'materialProperties':materials}
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

def image_texture(name,rgb,noncolor=False):
    h,w=rgb.shape[:2];rgba=np.concatenate([np.clip(rgb,0,1),np.ones((h,w,1))],axis=-1).astype(np.float32)
    im=bpy.data.images.new(name,width=w,height=h)
    if noncolor:im.colorspace_settings.name='Non-Color'
    im.pixels.foreach_set(rgba.ravel());im.pack();return im

def skin_material(kind):
    size=1536; yy,xx=np.mgrid[0:size,0:size].astype(float);u=xx/size;v=yy/size
    rng=np.random.default_rng(419);noise=np.zeros_like(u)
    for i in range(12):
        k=2+i*3;noise+=np.sin(u*math.tau*k+rng.random()*6)*np.cos(v*math.tau*(k*.73)+rng.random()*6)/(i+3)
    if kind=='orange':
        # Irregular oil glands with shallow depressions and raised pore rims.
        cu=u*205+.15*np.sin(v*213);cv=v*112+.15*np.sin(u*237)
        ix=np.floor(cu).astype(int);iy=np.floor(cv).astype(int);closest=np.full_like(u,1e6)
        for ox in [-1,0,1]:
            for oy in [-1,0,1]:
                cx=ix+ox;cy=iy+oy
                jitter=np.mod(np.sin(cx*127.1+cy*311.7)*43758.5453,1)
                dx=cu-cx-.12-.76*jitter;dy=cv-cy-.12-.76*np.mod(jitter*7.31,1)
                closest=np.minimum(closest,(dx*dx+dy*dy)/(.10+.08*jitter)**2)
        r=np.sqrt(closest);pore=np.exp(-closest);rim=np.exp(-((r-1.55)/.55)**2)

        height=.12*noise-.32*pore+.08*rim
        mottling=.045*noise-.045*pore+.012*rim
        rgb=np.stack([.85+mottling,.33+mottling*.65+.025*np.sin(v*9),.025+mottling*.15],axis=-1)
        # Slight green near the stalk and muted natural pigment variation.
        green=np.exp(-((v-.985)/.05)**2)*.5
        rgb=rgb*(1-green[...,None])+np.array([.36,.38,.055])*green[...,None]
    else:
        # Diamond fruitlets: olive borders, golden centers and dry brown eyes.
        a=u*16+v*11+.13*np.sin(v*72+u*30)+.06*np.sin(u*212+v*95);b=u*16-v*11+.12*np.sin(u*63-v*41)+.05*np.sin(v*179+u*86)
        fa=a%1-.5;fb=b%1-.5;edge=np.maximum(abs(fa),abs(fb))
        ridge=np.exp(-((edge-.46)/.09)**2);center=np.exp(-((fa/(.15+.04*np.sin(np.floor(a)*8)))**2+(fb/.19)**2))
        radi=np.sqrt((fa/.5)**2+(fb/.5)**2)
        star=np.exp(-((radi-(.21+.065*np.cos(np.arctan2(fb,fa)*3+np.floor(a)*5)+.025*np.sin(np.arctan2(fb,fa)*7)))/.05)**2)
        variation=.105*np.sin(np.floor(a)*19+np.floor(b)*7)+.065*noise+.018*np.sin(u*823+v*732)*np.cos(u*532-v*651)
        gold=np.stack([.62+variation,.39+variation*.65,.10+variation*.25],axis=-1)
        olive=np.array([.22,.25,.08]);brown=np.array([.20,.105,.035])
        rgb=gold*(1-ridge[...,None]*.7)+olive*ridge[...,None]*.7
        dry=np.clip(center*.72+star*.18,0,1)
        rgb=rgb*(1-dry[...,None])+brown*dry[...,None]
        height=.26*(1-(edge/.5)**2)-.12*ridge+.12*star-.16*center+.035*noise
        rgb+=rng.normal(0,.008,(size,size,1))
    m=mat(kind+' natural skin',(1,1,1),.64);nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes.get('Principled BSDF')
    tex=nodes.new('ShaderNodeTexImage');tex.image=image_texture(kind+'_albedo_1536',rgb);links.new(tex.outputs['Color'],p.inputs['Base Color'])
    # Tangent-space normals are embedded in glTF and mirrored in VRM MToon.
    dy,dx=np.gradient(height);strength=2.6 if kind=='orange' else 11
    n=np.stack([-dx*strength,-dy*strength,np.ones_like(dx)],axis=-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
    texn=nodes.new('ShaderNodeTexImage');texn.image=image_texture(kind+'_normal_1536',n*.5+.5,True)
    normal=nodes.new('ShaderNodeNormalMap');links.new(texn.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],p.inputs['Normal'])
    return m

def leaf_material(kind):
    size=512;y,x=np.mgrid[0:size,0:size]/size
    if kind=='pineapple':
        stripe=.025*np.sin(x*190)+.015*np.sin(x*430+y*8)
        light=.85+.15*np.sin(y*math.pi)
        rgb=np.stack([(.19+stripe)*light,(.28+stripe)*light,(.14+stripe)*light],axis=-1)
        dry=np.maximum(0,(y-.87)/.13)[...,None];rgb=rgb*(1-dry*.6)+np.array([.38,.30,.16])*dry*.6
    else:
        veins=np.exp(-(abs(x-.5)/.012)**2)*.10
        lateral=np.exp(-(np.sin((y-abs(x-.5)*.65)*math.pi*13)/.1)**2)*.025
        rgb=np.stack([.045+veins+lateral,.18+veins+lateral,.025+veins*.4],axis=-1)
    m=mat(kind+' botanical foliage',(1,1,1),.6);t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=image_texture(kind+'_leaf',rgb);m.node_tree.links.new(t.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);return m

RADII={ 'orange':(.51,.47,.465), 'pineapple':(.44,.37,.57) }

def surface(kind,x,z,offset=0):
    rx,ry,rz=RADII[kind]; h=(z-1.5)/rz
    if kind=='pineapple':
        width=max(.001,1-abs(h)**3.3)**.5
        y=-ry*width*math.sqrt(max(.01,1-(x/(rx*width))**2))
    else:y=-ry*math.sqrt(max(.01,1-(x/rx)**2-h*h))
    return y-offset

def fruit_body(kind,material):
    rx,ry,rz=RADII[kind]; n=192; rings=128; verts=[]; uv=[]; faces=[]
    for j in range(rings+1):
        v=j/rings; lat=(v-.5)*math.pi; h=math.sin(lat)
        width=math.cos(lat) if kind=='orange' else max(0,1-abs(h)**3.3)**.5
        for i in range(n+1):
            u=i/n; a=u*math.tau
            bump=.0018*math.sin(a*17+lat*7)*math.sin(lat*13) if kind=='orange' else 0
            if kind=='pineapple':
                da=abs(((u*18+v*12+.5)%1)-.5); db=abs(((u*18-v*12+.5)%1)-.5)
                clear=.65*math.exp(-((abs(u-.75)/.12)**6+((v-.52)/.22)**6))
                aa=u*16+v*11+.13*math.sin(v*72+u*30)+.06*math.sin(u*212+v*95)
                bb=u*16-v*11+.12*math.sin(u*63-v*41)+.05*math.sin(v*179+u*86)
                bump=.022*(math.sin(math.pi*aa)**2*math.sin(math.pi*bb)**2)*(1-clear)
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
        t=i/steps; c=base+d*t+Vector((0,-bend*math.sin(math.pi*t),(.002 if name=='Calyx' else .07)*math.sin(math.pi*t)))
        w=width*(math.sin(math.pi*t)**1.35 if 'Crown' not in name else (1-t)**.65*(.65+.35*math.sin(math.pi*t)))+.0003
        for j in range(5):
            q=(j-2)/2; v=c+side*w*q+Vector((0,-.022*(1-q*q)*math.sin(math.pi*t),0)); verts.append(tuple(v))
    for i in range(steps):
        for j in range(4):k=i*5+j;faces.append((k,k+1,k+6,k+5))
    ob=mesh_object(name,verts,faces,material)
    uv=ob.data.uv_layers.new(name='UVMap')
    for polygon in ob.data.polygons:
        for li in polygon.loop_indices:
            vi=ob.data.loops[li].vertex_index;uv.data[li].uv=((vi%5)/4,(vi//5)/steps)
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
        w,h,curve=p;w*=.78;h*=.65;curve*=.4; vs=[]
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
    skin=skin_material(kind);green=leaf_material(kind);lightgreen=green;vein=mat('Leaf veins',(.26,.48,.045));stem=mat('Natural stem',(.18,.075,.022))
    dark=mat('Espresso outline',(.018,.008,.006),.48);white=mat('Warm eye white',(.52,.48,.39),.35);spark=mat('Catchlights',(1,1,.98),.18)
    iris=mat('Amber iris',(.26,.075,.012),.24) if kind=='orange' else mat('Teal iris',(.065,.095,.035),.3)
    irisl=mat('Iris lower light',(.68,.27,.025),.3) if kind=='orange' else mat('Jade lower light',(.12,.15,.045),.35)
    cheek=mat('Soft apricot blush',(.95,.20,.055));mouthdark=mat('Mouth interior',(.065,.007,.012));tongue=mat('Tongue',(.32,.055,.065));teeth=mat('Smile ivory',(.65,.58,.45))
    arm,bones=rig();static=[fruit_body(kind,skin)]
    if kind=='orange':
        static.append(tube('Short woody stem',[(0,0,1.95),(.005,0,1.985),(.012,.005,2.015)],.013,stem))
        for i in range(6):
            a=i*math.tau/6
            static.append(ribbon('Calyx',(.005,0,1.96),(.065*math.cos(a),.065*math.sin(a),1.943),.013,green,.008))
        static.append(ribbon('Citrus leaf',(.01,0,1.99),(.33,.055,2.08),.071,green,.045))
    else:
        # Narrow sword-shaped leaves with recurved outer tips and longitudinal veins.
        for row,count in [(0,10),(1,9),(2,7),(3,4)]:
            for i in range(count):
                a=i*math.tau/count+row*.61;spread=[.43,.34,.22,.09][row];height=[.22,.39,.55,.64][row]
                base=(.06*math.cos(a),.06*math.sin(a),2.015+row*.012)
                tip=(spread*math.cos(a),spread*math.sin(a),2.015+height+.035*math.sin(i*3.1))
                static.append(ribbon('Crown blade',base,tip,[.037,.035,.03,.022][row],green,.07))

    # Larger inset-looking eyes, colored irises and highlights; no protruding eyebrow rods.
    for s,side in [(-1,'L'),(1,'R')]:
        x=s*.183;z=1.60;y=surface(kind,x,z,.012)
        pieces=[sphere('Eye_'+side,(x,y,z),(.100,.025,.128),dark,40,28),sphere('Sclera',(x,y-.018,z),(.088,.019,.115),white,40,28),sphere('Iris',(x+s*.005,y-.035,z-.005),(.065,.013,.088),iris,40,24),sphere('Iris glow',(x+s*.005,y-.045,z-.036),(.050,.007,.045),irisl,32,20),sphere('Pupil',(x+s*.005,y-.050,z+.004),(.043,.009,.064),dark,32,24),sphere('Large catchlight',(x-.025,y-.061,z+.046),(.007,.003,.009),spark,24,16),sphere('Small catchlight',(x+.026,y-.058,z-.034),(.003,.002,.004),spark,20,12)]
        eye=join(pieces,'Eye_'+side)
        for vertex in eye.data.vertices:
            vertex.co.x*=.68;vertex.co.z*=.43;vertex.co.y*=.55
        eye.shape_key_add(name='Basis')
        light_vertices={vi for polygon in eye.data.polygons if eye.data.materials[polygon.material_index]!=dark for vi in polygon.vertices}
        for name in ['Blink','Happy']:
            key=eye.shape_key_add(name=name)
            for vi,v in enumerate(key.data):
                # Full closure becomes a curved eyelid; retract light-colored layers.
                xx=v.co.x; original_z=v.co.z
                v.co.z=original_z*.025+( .020 if name=='Happy' else -.010)*(1-(xx/.1)**2)
                v.co.y=surface(kind,x+xx,z+v.co.z,.010)-y
                if vi in light_vertices:v.co.y+=.065
        bind(eye,arm)

    mouth=make_mouth(kind,mouthdark,tongue,teeth,dark);bind(mouth,arm)
    body=join(static,'Fruit_body');bind(body,arm)
    bpy.ops.object.select_all(action='DESELECT')
    for o in [arm,body,mouth,bpy.data.objects['Eye_L'],bpy.data.objects['Eye_R']]:o.select_set(True)
    glb=ROOT/'models'/f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_tangents=True,export_skins=True,export_all_influences=True,export_extras=True,export_yup=True)
    pack_vrm(glb,ROOT/'models'/f'{kind}.vrm',bones,'Orange' if kind=='orange' else 'Pineapple');glb.unlink()
    bpy.context.preferences.filepaths.save_version=0;scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=False
    scene.world.color=(.16,.16,.16);scene.view_settings.view_transform='AgX'
    scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    for loc,power,size in [((-3,-4,6),350,4),((3,-2,3),160,3),((1,3,4),450,3)]:
        bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector((0,0,1.6))-ob.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(.10,-5,2.02));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.79 if kind=='pineapple' else 1.59))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.15 if kind=='pineapple' else 1.45;scene.camera=cam
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/f'{kind}.blend'))
    scene.render.filepath=str(ROOT/'previews'/f'{kind}.png');bpy.ops.render.render(write_still=True)
    # Exercise actual shape keys in an additional render, rather than only inspecting metadata.
    for name in ['Eye_L','Eye_R']:bpy.data.objects[name].data.shape_keys.key_blocks['Happy'].value=1
    mouth.data.shape_keys.key_blocks['JOY'].value=1
    scene.render.resolution_percentage=65;scene.render.filepath=str(ROOT/'previews'/f'{kind}-joy.png');bpy.ops.render.render(write_still=True)

import sys
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['orange','pineapple']
for kind in selected:
    if kind not in RADII:raise ValueError(kind)
    build(kind)
