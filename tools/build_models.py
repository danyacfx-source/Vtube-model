"""Build original fruit avatars with Blender 4.3+, then package VRM 0.0."""
import bpy, math, json, struct, pathlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
FACE_SURFACE=None
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
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            # Blender emits a shader color plus the original vertex-color layer.
            # The original layer contains the edge opacity; preserve it as COLOR_0.
            if 'COLOR_1' in primitive['attributes']:
                primitive['attributes']['COLOR_0']=primitive['attributes']['COLOR_1']
            if 'normalTexture' not in doc['materials'][primitive['material']]:
                primitive['attributes'].pop('TANGENT',None)
            for attr in list(primitive['attributes']):
                if attr.startswith('COLOR_') and attr!='COLOR_0':del primitive['attributes'][attr]
    nodes={n.get('name'):i for i,n in enumerate(doc['nodes'])}
    groups=[]
    for preset,targets in [('blink',[('Eye_L','Blink'),('Eye_R','Blink')]),('blink_l',[('Eye_L','Blink')]),('blink_r',[('Eye_R','Blink')])]+[(x,[('Mouth',x.upper())]) for x in ['a','i','u','e','o']]+[('joy',[('Eye_L','Happy'),('Eye_R','Happy'),('Mouth','JOY')]),('sorrow',[('Mouth','SORROW')]),('angry',[('Mouth','ANGRY')]),('fun',[('Mouth','JOY')])]:
        binds=[]
        for meshname,key in targets:
            node=doc['nodes'][nodes[meshname]]; mi=node['mesh']; names=doc['meshes'][mi]['extras']['targetNames']
            binds.append({'mesh':mi,'index':names.index(key),'weight':100})
        groups.append({'name':preset,'presetName':preset,'binds':binds,'materialValues':[],'isBinary':False})
    materials=[]
    enhanced=title.lower()=='pineapple'
    if enhanced:
        for preset,key in [('lookup','LookUp'),('lookdown','LookDown'),('lookleft','LookLeft'),('lookright','LookRight')]:
            binds=[]
            for name in ['Eye_L','Eye_R']:
                mi=doc['nodes'][nodes[name]]['mesh']
                names=doc['meshes'][mi]['extras']['targetNames']
                binds.append({'mesh':mi,'index':names.index(key),'weight':100})
            groups.append({'name':preset,'presetName':preset,'binds':binds,'materialValues':[],'isBinary':False})
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
    # Official VRM 0 shader sentinel: preserve glTF metallic/roughness PBR.
    for target in materials:target['shader']='VRM_USE_GLTFSHADER'
    doc.setdefault('extensions',{})['VRM']={'exporterVersion':'FruitAvatars-4.0','specVersion':'0.0','meta':{'title':title,'version':'4.0','author':'Vtube-model','contactInformation':'','reference':'','allowedUserName':'Everyone','violentUssageName':'Disallow','sexualUssageName':'Disallow','commercialUssageName':'Allow','otherPermissionUrl':'','licenseName':'CC0','otherLicenseUrl':''},'humanoid':{'humanBones':[{'bone':b,'node':nodes[b],'useDefaultValues':True} for b in bones],'armStretch':.05,'legStretch':.05,'upperArmTwist':.5,'lowerArmTwist':.5,'upperLegTwist':.5,'lowerLegTwist':.5,'feetSpacing':0,'hasTranslationDoF':False},'firstPerson':{'firstPersonBone':nodes['head'],'firstPersonBoneOffset':{'x':0,'y':0,'z':0},'meshAnnotations':[{'mesh':i,'firstPersonFlag':'Auto'} for i in range(len(doc['meshes']))],'lookAtTypeName':'Bone','lookAtHorizontalInner':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtHorizontalOuter':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtVerticalDown':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10},'lookAtVerticalUp':{'curve':[0,0,0,1,1,1,1,0],'xRange':90,'yRange':10}},'blendShapeMaster':{'blendShapeGroups':groups},'secondaryAnimation':{'boneGroups':[],'colliderGroups':[]},'materialProperties':materials}
    doc.setdefault('extensionsUsed',[]).append('VRM')
    if enhanced:
        vrm=doc['extensions']['VRM']
        vrm['meta']['version']='5.0'
        vrm['meta']['title']='Pineapple — VSeeFace'
        vrm['exporterVersion']='FruitAvatars-5.0'
        vrm['firstPerson']['lookAtTypeName']='BlendShape'
        for direction in ['HorizontalInner','HorizontalOuter','VerticalDown','VerticalUp']:
            vrm['firstPerson']['lookAt'+direction]['yRange']=100
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
    size=2048; yy,xx=np.mgrid[0:size,0:size].astype(float);u=xx/size;v=yy/size
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
        # A 4x4 atlas of irregular dry fruitlet surfaces, applied to real hexagonal scales.
        tu=u*4%1;tv=v*4%1;tx=tu-.5;ty=tv-.5
        seed=np.floor(u*4)*13+np.floor(v*4)*29
        theta=np.arctan2(ty,tx);r=np.sqrt(tx*tx+ty*ty)
        turbulence=.025*np.sin(tu*39+tv*22+seed)+.017*np.sin(tv*91-tu*51)
        wound=np.exp(-((r+turbulence)/(.105+.015*np.sin(seed)))**2)
        cracks=np.exp(-(np.sin(theta*5+seed+.3*np.sin(r*20))/.12)**2)*np.exp(-((r-.15)/.12)**2)
        flecks=np.maximum(0,np.sin(u*1891+v*1223)*np.sin(v*2233-u*1773)-.45)
        variation=.055*noise+.025*np.sin(seed)+.025*np.sin(u*621+v*521)*np.cos(v*899)
        edge=np.clip((r-.25)/.35,0,1)
        gold=np.stack([.49+variation,.34+variation*.8,.105+variation*.4],axis=-1)
        olive=np.array([.22,.25,.105]);drybrown=np.array([.28,.17,.075])
        rgb=gold*(1-edge[...,None]*.8)+olive*edge[...,None]*.8
        damage=np.clip(wound*.85+cracks*.5,0,1)
        rgb=rgb*(1-damage[...,None])+drybrown*damage[...,None]
        rgb-=flecks[...,None]*.08
        height=.05*noise-.3*wound-.13*cracks+.06*flecks
        rgb+=rng.normal(0,.012,(size,size,1))
    m=mat(kind+' natural skin',(1,1,1),.52);nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes.get('Principled BSDF')
    tex=nodes.new('ShaderNodeTexImage');tex.image=image_texture(kind+'_albedo_2048',rgb);links.new(tex.outputs['Color'],p.inputs['Base Color'])
    # Tangent-space normals are embedded in glTF and mirrored in VRM MToon.
    dy,dx=np.gradient(height);strength=2.6 if kind=='orange' else 11
    n=np.stack([-dx*strength,-dy*strength,np.ones_like(dx)],axis=-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
    texn=nodes.new('ShaderNodeTexImage');texn.image=image_texture(kind+'_normal_2048',n*.5+.5,True)
    normal=nodes.new('ShaderNodeNormalMap');links.new(texn.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],p.inputs['Normal'])
    rough=np.clip((.46 if kind=='orange' else .74)+.09*noise,.25,.92)
    tr=nodes.new('ShaderNodeTexImage');tr.image=image_texture(kind+'_roughness',np.repeat(rough[...,None],3,axis=-1),True);links.new(tr.outputs['Color'],p.inputs['Roughness'])
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
    if FACE_SURFACE is not None:
        hit=FACE_SURFACE.ray_cast(Vector((x,-3,z)),Vector((0,1,0)))[0]
        if hit is not None:return hit.y-offset
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
            bump=.003*math.sin(a*5+lat*3)*math.sin(lat*7) if kind=='orange' else 0
            verts.append(((rx*width+bump)*math.cos(a),(ry*width+bump)*math.sin(a),1.5+rz*h)); uv.append((u,v))
    for j in range(rings):
        for i in range(n):
            k=j*(n+1)+i; faces.append((k,k+1,k+n+2,k+n+1))
    ob=mesh_object('Fruit_body',verts,faces,material); layer=ob.data.uv_layers.new(name='UVMap')
    for p in ob.data.polygons:
        for li in p.loop_indices:layer.data[li].uv=uv[ob.data.loops[li].vertex_index]
    return ob

def pineapple_scales(material):
    import random
    rng=random.Random(37);vertices=[];faces=[];uvs=[]
    step=.083;count=16;angle_step=math.tau/count
    corners=[(0,2/3),(.5,1/3),(.5,-1/3),(0,-2/3),(-.5,-1/3),(-.5,1/3)]
    # Each ring follows the fruit surface. The middle rises; edges and the central eye sink.
    for row in range(13):
        zc=.995+row*step
        for col in range(count):
            a=(col+(row%2)*.5)*angle_step
            tile=rng.randrange(16);depth=.006+rng.random()*.008;twist=rng.uniform(-.018,.018)
            start=len(vertices)
            for ring,radius in enumerate([0,.18,.45,.76,.98]):
                for k in range(18):
                    c0=corners[k//3];c1=corners[(k//3+1)%6];t=(k%3)/3
                    dx=(c0[0]*(1-t)+c1[0]*t)*radius;dz=(c0[1]*(1-t)+c1[1]*t)*radius
                    z=zc+dz*step;h=(z-1.5)/.57;width=max(.002,1-abs(h)**3.3)**.5
                    aa=a+dx*angle_step+twist*radius
                    bump=[depth*.75,depth*.9,depth,depth*.50,.001][ring]
                    bump+=.0015*math.sin(k*4+row+col)
                    xx=.44*width*math.cos(aa)
                    if math.sin(aa)<-.5:
                        masks=[math.exp(-(((xx-cx)/.16)**2+((z-1.60)/.105)**2)**2) for cx in [-.19,.19]]
                        masks.append(math.exp(-((xx/.22)**2+((z-1.32)/.14)**2)**2))
                        bump*=1-.97*max(masks)
                    vertices.append(((.44*width+bump)*math.cos(aa),(.37*width+bump)*math.sin(aa),z))
                    uvs.append(((tile%4+.5+dx*.93)/4,(tile//4+.5+dz*.70)/4))
            for ring in range(4):
                for k in range(18):
                    q=start+ring*18+k;n=start+ring*18+(k+1)%18
                    faces.append((q,n,n+18,q+18))
    ob=mesh_object('Individual pineapple fruitlets',vertices,faces,material);layer=ob.data.uv_layers.new(name='UVMap')
    for polygon in ob.data.polygons:
        for li in polygon.loop_indices:layer.data[li].uv=uvs[ob.data.loops[li].vertex_index]
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
    solid=ob.modifiers.new('Leaf thickness','SOLIDIFY');solid.thickness=.0015
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

def photo_material():
    m=mat('Photoreal human facial features',(1,1,1),.53);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'assets/human_features.png'),check_existing=True);tex.image.pack()
    color=n.new('ShaderNodeVertexColor');color.layer_name='Color'
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    l.new(tex.outputs['Color'],mix.inputs[1]);l.new(color.outputs['Color'],mix.inputs[2]);l.new(mix.outputs['Color'],p.inputs['Base Color']);l.new(color.outputs['Alpha'],p.inputs['Alpha'])
    m.surface_render_method='DITHERED'
    return m

def photo_feature(name,kind,cx,cz,width,height,region,material,mouth=False):
    verts=[];faces=[];uvs=[];colors=[];rings=16;segments=96
    for j in range(rings+1):
        r=j/rings
        for i in range(segments):
            a=i*math.tau/segments;nx=r*math.cos(a);nz=r*math.sin(a)
            x=cx+nx*width;z=cz+nz*height
            verts.append((x,surface(kind,x,z,.008+.012*(1-r*r)),z))
            uvs.append((region[0]+nx*region[2],1-region[1]+nz*region[3]))
            alpha=1 if r<.70 else max(0,(1-r)/.30)**1.5
            colors.append((1,1,1,alpha))
    for j in range(rings):
        for i in range(segments):
            q=j*segments+i;n=j*segments+(i+1)%segments;faces.append((q,q+segments,n+segments,n))
    ob=mesh_object(name,verts,faces,material);uv=ob.data.uv_layers.new(name='UVMap');vc=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
    for i,c in enumerate(colors):vc.data[i].color=c
    ob.data.color_attributes.active_color=vc
    for polygon in ob.data.polygons:
        for li in polygon.loop_indices:uv.data[li].uv=uvs[ob.data.loops[li].vertex_index]
    ob.shape_key_add(name='Basis')
    shapes={'A':(.88,1.45),'I':(1.08,.65),'U':(.58,1.0),'E':(1.10,1.12),'O':(.65,1.45),'JOY':(1.1,1.2),'SORROW':(.88,.55),'ANGRY':(1.02,.55)} if mouth else {'Blink':(1,.012),'Happy':(1,.10)}
    for keyname,(sx,sz) in shapes.items():
        key=ob.shape_key_add(name=keyname)
        for v,base in zip(key.data,verts):
            x=cx+(base[0]-cx)*sx;z=cz+(base[2]-cz)*sz
            if mouth and keyname in {'A','I','U','E','O','JOY'}:
                nz=(base[2]-cz)/height;openness=max(0,min(1,(.12-nz)/.45))
                z=base[2]-(sz-1)*height*openness
            if keyname=='SORROW':z-=.028*(1-((x-cx)/width)**2)
            if keyname=='Happy':z+=.015*(1-((x-cx)/width)**2)
            r2=((x-cx)/(width*sx))**2+((z-cz)/(height*sz))**2
            v.co=(x,surface(kind,x,z,.008+.012*max(0,1-r2)),z)
    if kind=='pineapple':
        refine_vseeface_feature(ob,kind,cx,cz,width,height,mouth)
    return ob

def refine_vseeface_feature(ob,kind,cx,cz,width,height,mouth):
    """Keep lips thick while closing the photographed mouth cavity at rest.

    Coordinates remain on the actual peel for every expression. Gaze warps
    the iris region gently while leaving the outer eyelid boundary fixed.
    """
    keys=ob.data.shape_keys.key_blocks
    source=[v.co.copy() for v in keys['Basis'].data]
    if mouth:
        openings={'Basis':.025,'A':1.18,'I':.22,'U':.55,'E':.70,'O':1.12,'JOY':.9,'SORROW':.06,'ANGRY':.10}
        widths={'Basis':1,'A':.88,'I':1.08,'U':.67,'E':1.08,'O':.70,'JOY':1.08,'SORROW':.96,'ANGRY':1.01}
        for key in keys:
            for v,base in zip(key.data,source):
                nx=(base.x-cx)/width;nz=(base.z-cz)/height
                gap=.29*math.sqrt(max(0,1-(nx/.83)**2))
                delta=max(-gap,min(gap,nz-.12))
                # Fade deformation to zero at the photographed patch boundary.
                fade=max(0,min(1,(1-abs(nz))/.32))
                z=base.z-(1-openings[key.name])*delta*height*fade
                x=cx+(base.x-cx)*widths[key.name]
                if key.name=='SORROW':z-=.014*max(0,1-nx*nx)
                if key.name=='JOY':z+=.010*nx*nx
                v.co=(x,surface(kind,x,z,.018),z)
        for v,basis in zip(ob.data.vertices,keys['Basis'].data):v.co=basis.co
    else:
        for name,dx,dz in [('LookLeft',.012,0),('LookRight',-.012,0),('LookUp',0,.008),('LookDown',0,-.008)]:
            key=ob.shape_key_add(name=name)
            for v,base in zip(key.data,source):
                nx=(base.x-cx)/width;nz=(base.z-cz)/height
                weight=max(0,1-nx*nx-nz*nz)**2
                x=base.x+dx*weight;z=base.z+dz*weight
                v.co=(x,surface(kind,x,z,.008+.012*weight),z)

def build(kind):
    global FACE_SURFACE
    FACE_SURFACE=None
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    skin=skin_material(kind);green=leaf_material(kind);lightgreen=green;vein=mat('Leaf veins',(.26,.48,.045));stem=mat('Natural stem',(.18,.075,.022))
    dark=mat('Espresso outline',(.018,.008,.006),.48);white=mat('Warm eye white',(.52,.48,.39),.35);spark=mat('Catchlights',(1,1,.98),.18)
    iris=mat('Amber iris',(.26,.075,.012),.24) if kind=='orange' else mat('Teal iris',(.065,.095,.035),.3)
    irisl=mat('Iris lower light',(.68,.27,.025),.3) if kind=='orange' else mat('Jade lower light',(.12,.15,.045),.35)
    cheek=mat('Soft apricot blush',(.95,.20,.055));mouthdark=mat('Mouth interior',(.065,.007,.012));tongue=mat('Tongue',(.32,.055,.065));teeth=mat('Smile ivory',(.65,.58,.45))
    arm,bones=rig();static=[fruit_body(kind,skin if kind=='orange' else mat('Pineapple crevices',(.09,.075,.025),.9))]
    if kind=='pineapple':static.append(pineapple_scales(skin))
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

    verts=[];polys=[]
    for obj in static:
        base=len(verts);verts.extend([obj.matrix_world@v.co for v in obj.data.vertices]);polys.extend([tuple(base+i for i in poly.vertices) for poly in obj.data.polygons])
    FACE_SURFACE=BVHTree.FromPolygons(verts,polys)
    face_mat=photo_material()
    for side,cx,region in [('L',-.19,(.50,.163,.37,.135)),('R',.19,(.50,.491,.37,.135))]:
        eye=photo_feature('Eye_'+side,kind,cx,1.60,.14,.078,region,face_mat)
        bind(eye,arm)
    mouth=photo_feature('Mouth',kind,0,1.32,.19,.107,(.50,.825,.46,.167),face_mat,True);bind(mouth,arm)
    body=join(static,'Fruit_body');bind(body,arm)
    bpy.ops.object.select_all(action='DESELECT')
    for o in [arm,body,mouth,bpy.data.objects['Eye_L'],bpy.data.objects['Eye_R']]:o.select_set(True)
    glb=ROOT/'models'/f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_tangents=True,export_skins=True,export_all_influences=True,export_extras=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True,export_yup=True)
    pack_vrm(glb,ROOT/'models'/f'{kind}.vrm',bones,'Orange' if kind=='orange' else 'Pineapple');glb.unlink()
    bpy.context.preferences.filepaths.save_version=0;scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=False
    scene.world.color=(.16,.16,.16);scene.view_settings.view_transform='AgX'
    scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    for loc,power,size in [((-3,-4,6),350,4),((3,-2,3),160,3),((1,3,4),450,3)]:
        bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector((0,0,1.6))-ob.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(.10,-5,2.02));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.79 if kind=='pineapple' else 1.59))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.15 if kind=='pineapple' else 1.45;scene.camera=cam
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/f'{kind}.blend'))
    scene.render.filepath=str(ROOT/'previews'/f'{kind}.png');bpy.ops.render.render(write_still=True)
    front_location=cam.location.copy();front_rotation=cam.rotation_euler.copy()
    cam.location=(2.7,-4,2.15);cam.rotation_euler=(Vector((0,0,1.72))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_percentage=65;scene.render.filepath=str(ROOT/'previews'/f'{kind}-three-quarter.png');bpy.ops.render.render(write_still=True)
    cam.location=front_location;cam.rotation_euler=front_rotation
    # Exercise actual shape keys in an additional render, rather than only inspecting metadata.
    for name in ['Eye_L','Eye_R']:bpy.data.objects[name].data.shape_keys.key_blocks['Happy'].value=1
    mouth.data.shape_keys.key_blocks['JOY'].value=1
    scene.render.resolution_percentage=65;scene.render.filepath=str(ROOT/'previews'/f'{kind}-joy.png');bpy.ops.render.render(write_still=True)

if __name__=='__main__':
    import sys
    selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['orange','pineapple']
    for kind in selected:
        if kind not in RADII:raise ValueError(kind)
        build(kind)
