"""Build DENDICH / RADIO SILENCE from scratch in Blender 4.3.

The model is procedural original geometry based on the supplied turnaround.
It exports a GLB payload and packages VRM 1.0 extensions without third-party
Blender add-ons so the build is reproducible in the cloud environment.
"""
import bpy, math, json, struct, pathlib, sys
from mathutils import Vector

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'output'; RENDERS=ROOT/'renders'; OUT.mkdir(exist_ok=True); RENDERS.mkdir(exist_ok=True)

def mat(name,color,rough=.55,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m

CHARCOAL=mat('Charcoal textile #111713',(0.024,0.035,0.027),.88)
BLACK=mat('Soft black',(0.009,0.012,0.011),.62);OLIVE=mat('Deep olive #293229',(0.053,0.073,0.052),.84)
OLIVE2=mat('Olive webbing',(0.105,0.125,0.087),.78);SAND=mat('Sand #b9a47a',(0.48,0.39,0.25),.72)
IVORY=mat('Textile ivory #ebe4d7',(.82,.78,.68),.68);RED=mat('Muted ON AIR red #b76552',(.48,.075,.045),.35)
SKIN=mat('Warm skin',(0.56,0.30,0.21),.52);SKIN_LIP=mat('Natural lips',(.33,.105,.085),.45)
HAIR=mat('Near-black chestnut hair',(.035,.018,.014),.42);HAIR_HI=mat('Chestnut hair highlight',(.10,.045,.025),.38)
EYEWHITE=mat('Warm sclera',(.82,.79,.70),.32);IRIS=mat('Grey olive iris',(.18,.24,.14),.3);AMBER=mat('Amber eye catch',(.63,.34,.07),.25)
MOUTH=mat('Mouth cavity',(.055,.009,.012),.48);TEETH=mat('Teeth',(.82,.78,.66),.36);METAL=mat('Headset metal',(.22,.21,.18),.25,.5)
SCREEN=mat('Radio screen',(.015,.11,.075),.23);GLOVE=mat('Glove textile',(.018,.021,.019),.82)

def smooth(o):
    if o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    return o

def uv(name,loc,scale,material,seg=48,rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return smooth(o)

def cube(name,loc,scale,material,bevel=.04,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
    return o

def cyl(name,loc,radius,depth,material,rot=(0,0,0),vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(material);return smooth(o)

def capsule(name,a,b,radii,material):
    a=Vector(a);b=Vector(b);mid=(a+b)*.5;length=(b-a).length
    o=uv(name,mid,(radii[0],radii[1],length*.53),material,40,24);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def hair_lock(name,root,tip,width,material,bend=(0,-.025,.025)):
    a=Vector(root);t=Vector(tip);m=(a+t)*.5+Vector(bend);side=Vector((1,0,0))*width;depth=Vector((0,width*.32,0))
    verts=[a-side-depth,a+side-depth,a+side+depth,a-side+depth,m-side*.72-depth,m+side*.72-depth,m+side*.72+depth,m-side*.72+depth,t-depth*.2,t+depth*.2]
    faces=[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,8),(5,6,9,8),(6,7,9),(7,4,8),(0,3,2,1)]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(material);o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    bevel=o.modifiers.new('Soft hair edges','BEVEL');bevel.width=.006;bevel.segments=2
    return smooth(o)

def anime_head(name,material):
    levels=[(1.855,.018,.055),(1.88,.072,.085),(1.92,.108,.105),(1.98,.133,.113),(2.06,.145,.116),(2.13,.137,.112),(2.19,.105,.092),(2.225,.035,.040)]
    seg=64;verts=[];faces=[]
    for z,rx,ry in levels:
        for i in range(seg):
            a=math.tau*i/seg
            # A slightly flatter front plane gives the eyes room and a sharper jaw.
            y=ry*math.sin(a)+.004
            if y<0:y*=.88
            verts.append((rx*math.cos(a),y,z))
    for j in range(len(levels)-1):
        for i in range(seg):
            q=j*seg+i;n=j*seg+(i+1)%seg;faces.append((q,n,n+seg,q+seg))
    faces += [tuple(range(seg-1,-1,-1)),tuple((len(levels)-1)*seg+i for i in range(seg))]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(material);o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return smooth(o)

def almond_eye(name,cx):
    seg=48;verts=[(cx,-.126,2.047)];faces=[]
    for i in range(seg):
        a=math.tau*i/seg;nx=math.cos(a);nz=math.sin(a);verts.append((cx+.045*nx,-.127,2.047+.017*nz*(.88+.12*nx)))
    for i in range(seg):faces.append((0,1+i,1+(i+1)%seg))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(EYEWHITE);o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    o.shape_key_add(name='Basis');base=[v.co.copy() for v in o.data.vertices]
    for keyname,factor in [('Blink',.025),('Tired',.45),('Wide',1.25),('Squint',.28)]:
        k=o.shape_key_add(name=keyname)
        for v,b in zip(k.data,base):v.co=(b.x,b.y,2.047+(b.z-2.047)*factor)
    return o

def curve(name,points,bevel,material,cyclic=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=bevel;c.bevel_resolution=3
    s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for b,p in zip(s.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    s.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(material);return o

def text(name,body,loc,size,material,extr=.006,align='CENTER'):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.align_x=align;c.align_y='CENTER';c.size=size;c.extrude=extr;c.bevel_depth=.0015
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(math.pi/2,0,0);o.data.materials.append(material);return o

def parent_bone(o,arm,bone):
    o.parent=arm;o.parent_type='BONE';o.parent_bone=bone

def weight(o,arm,bone):
    if o.type!='MESH':
        bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object
    vg=o.vertex_groups.new(name=bone);vg.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Humanoid deformation','ARMATURE');mod.object=arm;o.parent=arm
    return o

def rig():
    bpy.ops.object.armature_add(location=(0,0,0));arm=bpy.context.object;arm.name='DENDICH_Rig';arm.show_in_front=True
    bpy.ops.object.mode_set(mode='EDIT');eb=arm.data.edit_bones;eb.remove(eb[0])
    specs=[
      ('hips',None,(0,0,1.02),(0,0,1.20)),('spine','hips',(0,0,1.20),(0,0,1.42)),('chest','spine',(0,0,1.42),(0,0,1.64)),('upperChest','chest',(0,0,1.64),(0,0,1.76)),('neck','upperChest',(0,0,1.76),(0,0,1.88)),('head','neck',(0,0,1.88),(0,0,2.12)),
      ('leftEye','head',(-.052,-.105,2.035),(-.052,-.14,2.035)),('rightEye','head',(.052,-.105,2.035),(.052,-.14,2.035)),('jaw','head',(0,-.09,1.975),(0,-.13,1.94)),
    ]
    for side,s in [('left',1),('right',-1)]:
      specs += [(side+'Shoulder','upperChest',(s*.09,0,1.70),(s*.22,0,1.68)),(side+'UpperArm',side+'Shoulder',(s*.22,0,1.68),(s*.48,0,1.58)),(side+'LowerArm',side+'UpperArm',(s*.48,0,1.58),(s*.70,-.005,1.42)),(side+'Hand',side+'LowerArm',(s*.70,-.005,1.42),(s*.79,-.02,1.37)),
      (side+'UpperLeg','hips',(s*.105,0,1.05),(s*.13,0,.61)),(side+'LowerLeg',side+'UpperLeg',(s*.13,0,.61),(s*.13,-.01,.18)),(side+'Foot',side+'LowerLeg',(s*.13,-.01,.18),(s*.13,-.17,.07)),(side+'Toes',side+'Foot',(s*.13,-.17,.07),(s*.13,-.28,.055))]
      # Simple finger chains help VRM hand tracking compatibility.
      for finger,xoff in [('Thumb',-.02),('Index',-.01),('Middle',0),('Ring',.01),('Little',.02)]:
        a=(s*(.79+xoff),-.02,1.37);b=(s*(.835+xoff),-.035,1.345);c=(s*(.87+xoff),-.045,1.33)
        specs += [(side+finger+'Proximal',side+'Hand',a,b),(side+finger+'Intermediate',side+finger+'Proximal',b,c),(side+finger+'Distal',side+finger+'Intermediate',c,(s*(.89+xoff),-.05,1.32))]
    for name,parent,a,b in specs:
        bone=eb.new(name);bone.head=a;bone.tail=b
        if parent:bone.parent=eb[parent]
    # Hair spring chains, all beneath head.
    for i in range(10):
        x=(-.16+i*.035);z=2.19-abs(i-4.5)*.006
        for j in range(2):
            name=f'hair_{i}_{j}';bone=eb.new(name);bone.head=(x,.02,z-j*.085);bone.tail=(x,-.005,z-(j+1)*.085);bone.parent=eb['head'] if j==0 else eb[f'hair_{i}_{j-1}']
    bpy.ops.object.mode_set(mode='OBJECT');return arm

def face(arm):
    # Mature narrow head and separate jaw/chin volume.
    head=anime_head('Face',SKIN);weight(head,arm,'head')
    neck=uv('Neck',(0,.012,1.80),(.080,.072,.16),SKIN);weight(neck,arm,'neck')
    # Nose has a restrained anime wedge, kept clear in frontal close-up.
    nose=uv('Nose',(0,-.121,2.006),(.014,.017,.037),SKIN,32,20);weight(nose,arm,'head')
    # Eye whites: flattened ovals with morph targets for blinks and tired expression.
    eyes=[]
    for side,x in [('L',-.058),('R',.058)]:
        e=almond_eye('Eye_'+side,x);weight(e,arm,'head')
        eyes.append(e)
        iris=uv('Iris_'+side,(x,-.132,2.046),(.013,.003,.014),IRIS,32,20);weight(iris,arm,'head');iris.shape_key_add(name='Basis')
        ib=[v.co.copy() for v in iris.data.vertices]
        for keyname,dx,dz in [('LookLeft',-.012,0),('LookRight',.012,0),('LookUp',0,.010),('LookDown',0,-.010)]:
            k=iris.shape_key_add(name=keyname)
            for v,b in zip(k.data,ib):v.co=(b.x+dx,b.y,b.z+dz)
        pupil=uv('Pupil_'+side,(x,-.133,2.046),(.005,.002,.009),BLACK,24,16);weight(pupil,arm,'head')
        catch=uv('EyeCatch_'+side,(x-.004,-.136,2.054),(.0025,.001,.0035),AMBER,16,8);weight(catch,arm,'head')
    # Strong expressive brows.
    for side,s in [('L',-1),('R',1)]:
        b=curve('Brow_'+side,[(s*.102,-.126,2.085),(s*.060,-.132,2.096),(s*.022,-.128,2.090)],.0055,HAIR);weight(b,arm,'head')
    # Mouth is a compact oval; shapes supply five phonemes and emotions.
    mouth=uv('Mouth',(0,-.114,1.944),(.042,.009,.010),MOUTH,48,24);weight(mouth,arm,'head');mouth.shape_key_add(name='Basis');base=[v.co.copy() for v in mouth.data.vertices]
    shapes={'A':(.85,2.8),'I':(1.45,.70),'U':(.60,1.45),'E':(1.30,1.35),'O':(.68,2.35),'Smile':(1.35,.75),'Sad':(.95,.55),'Surprised':(.72,2.8),'Irritated':(1.05,.45),'Awkward':(.90,.65)}
    for name,(sx,sz) in shapes.items():
        k=mouth.shape_key_add(name=name)
        for v,b in zip(k.data,base):v.co=(b.x*sx,b.y,b.z*sz)
    teeth=cube('Teeth',(0,-.125,1.950),(.028,.003,.0035),TEETH,.003);weight(teeth,arm,'head')
    lip=curve('Subtle smirk',[(-.040,-.128,1.947),(0,-.131,1.940),(.043,-.128,1.949)],.0035,SKIN_LIP);weight(lip,arm,'head')
    return head,eyes,mouth

def hair(arm):
    # Layered tapered locks approximated as overlapping bevel curves. The front
    # stays above the eye line, while side/back locks establish the turnaround.
    objects=[]
    cap=uv('Hair cap',(0,.014,2.125),(.153,.120,.140),HAIR,48,32);weight(cap,arm,'head');objects.append(cap)
    locks=[
      (-.13,-.13,2.20,-.09,-.145,2.07),(-.09,-.14,2.23,-.045,-.151,2.075),(-.04,-.145,2.235,.00,-.153,2.09),(.01,-.145,2.23,.045,-.153,2.06),(.06,-.135,2.22,.085,-.146,2.075),(.11,-.12,2.20,.13,-.13,2.08),
      (-.15,-.07,2.18,-.175,-.05,2.02),(.15,-.07,2.18,.175,-.05,2.01),(-.17,.00,2.14,-.18,.05,1.99),(.17,.00,2.14,.18,.05,1.99),
      (-.12,.08,2.20,-.16,.10,2.03),(-.06,.12,2.24,-.08,.14,2.02),(0,.13,2.25,.01,.15,2.02),(.07,.12,2.23,.09,.14,2.02),(.13,.08,2.19,.16,.10,2.02),
      (-.10,-.04,2.25,-.17,-.10,2.18),(.10,-.04,2.25,.18,-.08,2.17),(-.03,.00,2.27,-.13,-.05,2.22),(.03,.00,2.27,.14,-.03,2.21)]
    for i,(x1,y1,z1,x2,y2,z2) in enumerate(locks):
        o=hair_lock('Hair lock %02d'%i,(x1,y1,z1),(x2,y2,z2),.022 if i<6 else .027,HAIR_HI if i%5==0 else HAIR);weight(o,arm,'head');objects.append(o)
    # Ten physics locks match the spring chains in the rig.
    for i in range(10):
        x=-.16+i*.035;o=hair_lock('Physics hair %02d'%i,(x,.04,2.19),(x*1.10,.02,2.02),.016,HAIR,bend=(0,.015,.015))
        weight(o,arm,f'hair_{i}_1');objects.append(o)
    return objects

def torso_and_limbs(arm):
    objs=[]
    # Hoodie volumes, adult masculine shoulder-to-waist taper.
    torso=uv('Hoodie torso',(0,.02,1.48),(.30,.17,.40),CHARCOAL,48,32);weight(torso,arm,'chest');objs.append(torso)
    waist=uv('Hoodie waist',(0,.02,1.20),(.245,.145,.22),CHARCOAL);weight(waist,arm,'spine');objs.append(waist)
    hood=curve('Lowered hood',[(-.18,.08,1.75),(0,.18,1.84),(.18,.08,1.75)],.055,CHARCOAL);weight(hood,arm,'upperChest');objs.append(hood)
    collar=curve('High collar',[(-.13,-.08,1.75),(0,-.12,1.79),(.13,-.08,1.75)],.035,CHARCOAL);weight(collar,arm,'upperChest');objs.append(collar)
    for side,s in [('left',1),('right',-1)]:
        ua=capsule(side+' hoodie sleeve',(s*.22,0,1.68),(s*.47,0,1.58),(.095,.090),CHARCOAL);weight(ua,arm,side+'UpperArm');objs.append(ua)
        la=capsule(side+' forearm sleeve',(s*.48,0,1.57),(s*.69,-.005,1.42),(.075,.072),CHARCOAL);weight(la,arm,side+'LowerArm');objs.append(la)
        hand=uv(side+' fingerless glove',(s*.755,-.015,1.37),(.060,.040,.082),GLOVE);weight(hand,arm,side+'Hand');objs.append(hand)
        thigh=uv(side+' tactical trouser thigh',(s*.135,.02,.82),(.145,.14,.33),CHARCOAL);weight(thigh,arm,side+'UpperLeg');objs.append(thigh)
        shin=uv(side+' tactical trouser shin',(s*.135,.01,.38),(.12,.115,.30),CHARCOAL);weight(shin,arm,side+'LowerLeg');objs.append(shin)
        boot=uv(side+' field boot',(s*.135,-.075,.105),(.125,.19,.105),BLACK);weight(boot,arm,side+'Foot');objs.append(boot)
        knee=cube(side+' knee pad',(s*.135,-.125,.55),(.105,.025,.105),OLIVE,.03);weight(knee,arm,side+'LowerLeg');objs.append(knee)
    return objs

def equipment(arm):
    objects=[]
    # Chest rig foundation, webbing and shoulder straps.
    plate=cube('Light chest rig',(0,-.168,1.50),(.245,.045,.255),OLIVE,.035);weight(plate,arm,'chest');objects.append(plate)
    for x in [-.18,-.09,0,.09,.18]:
        strap=cube('MOLLE vertical',(x,-.218,1.52),(.013,.008,.205),OLIVE2,.004);weight(strap,arm,'chest');objects.append(strap)
    for z in [1.36,1.44,1.52,1.60,1.68]:
        strap=cube('MOLLE horizontal',(0,-.220,z),(.225,.007,.010),OLIVE2,.004);weight(strap,arm,'chest');objects.append(strap)
    for x in [-.17,.17]:
        s=cube('Shoulder webbing',(x,-.112,1.72),(.035,.025,.18),OLIVE2,.012,rot=(0,0,-x*.8));weight(s,arm,'upperChest');objects.append(s)
    for x in [-.15,0,.15]:
        p=cube('Utility pouch',(x,-.235,1.27),(.068,.040,.105),OLIVE,.018);weight(p,arm,'spine');objects.append(p)
        flap=cube('Pouch flap',(x,-.279,1.33),(.064,.008,.033),OLIVE2,.008);weight(flap,arm,'spine');objects.append(flap)
    # Exact editable text patches.
    for name,body,loc,size in [('Patch_DENDICH','DENDICH',(0,-.275,1.61),.058),('Patch_RADIO_SILENCE','RADIO SILENCE',(0,-.276,1.53),.038),('Patch_RS01','RS-01',(-.10,-.276,1.69),.035)]:
        back=cube(name+'_back',(loc[0],loc[1]+.012,loc[2]),(.13 if body=='RADIO SILENCE' else .09,.007,.030),BLACK,.006);weight(back,arm,'chest');objects.append(back)
        o=text(name,body,loc,size,IVORY);weight(o,arm,'chest');objects.append(o)
    # Radio body and screen.
    radio=cube('Chest radio',(.155,-.275,1.49),(.070,.035,.105),BLACK,.012);weight(radio,arm,'chest');objects.append(radio)
    screen=cube('Radio LCD',(.155,-.314,1.53),(.050,.006,.033),SCREEN,.004);weight(screen,arm,'chest');objects.append(screen)
    for i in range(3):
        btn=cyl('Radio button',(.125+i*.03,-.324,1.445),.009,.008,METAL,rot=(math.pi/2,0,0),vertices=20);weight(btn,arm,'chest');objects.append(btn)
    freq=text('Frequency','145.800',(.155,-.324,1.535),.018,IVORY,.002);weight(freq,arm,'chest');objects.append(freq)
    antenna=cyl('Radio antenna',(.19,-.278,1.64),.009,.25,BLACK);weight(antenna,arm,'chest');objects.append(antenna)
    # PTT is distinct and readable in OBS.
    ptt=cube('PTT',(-.17,-.275,1.51),(.045,.025,.060),BLACK,.010);weight(ptt,arm,'chest');objects.append(ptt)
    key=cube('PTT key',(-.17,-.304,1.51),(.022,.007,.023),METAL,.005);weight(key,arm,'chest');objects.append(key)
    led=uv('ON AIR indicator',(-.135,-.313,1.555),(.008,.004,.008),RED,16,8);weight(led,arm,'chest');objects.append(led)
    cable=curve('PTT cable',[(-.17,-.29,1.56),(-.24,-.22,1.69),(-.19,-.12,1.88)],.008,BLACK);weight(cable,arm,'chest');objects.append(cable)
    return objects

def headset(arm):
    objects=[]
    band=curve('Headset headband',[(-.16,.00,2.13),(-.10,.05,2.27),(0,.07,2.31),(.10,.05,2.27),(.16,.00,2.13)],.018,BLACK);weight(band,arm,'head');objects.append(band)
    for side,s in [('L',-1),('R',1)]:
        cup=uv('Headset cup '+side,(s*.17,-.003,2.08),(.035,.055,.075),BLACK,32,24);weight(cup,arm,'head');objects.append(cup)
        pad=uv('Headset cushion '+side,(s*.151,-.004,2.08),(.018,.060,.065),CHARCOAL,24,16);weight(pad,arm,'head');objects.append(pad)
        hinge=cube('Headset hinge '+side,(s*.177,-.033,2.145),(.022,.018,.026),SAND,.006);weight(hinge,arm,'head');objects.append(hinge)
    boom=curve('Boom microphone',[(.17,-.03,2.09),(.19,-.10,2.02),(.115,-.16,1.965)],.009,METAL);weight(boom,arm,'head');objects.append(boom)
    mic=uv('Microphone',(.10,-.165,1.962),(.030,.020,.018),BLACK,32,16);weight(mic,arm,'head');objects.append(mic)
    return objects

def export_vrm1(arm):
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type in {'MESH','ARMATURE','FONT','CURVE'}:o.select_set(True)
    glb=OUT/'DENDICH.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_skins=True,export_all_influences=True,export_extras=True,export_yup=True)
    data=glb.read_bytes();jlen,jtype=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+jlen]);binary=data[20+jlen:]
    nodes={n.get('name'):i for i,n in enumerate(doc['nodes'])};human={}
    mapping=['hips','spine','chest','upperChest','neck','head','leftEye','rightEye','jaw','leftShoulder','leftUpperArm','leftLowerArm','leftHand','rightShoulder','rightUpperArm','rightLowerArm','rightHand','leftUpperLeg','leftLowerLeg','leftFoot','leftToes','rightUpperLeg','rightLowerLeg','rightFoot','rightToes']
    for b in mapping:human[b]={'node':nodes[b]}
    def morph(node,key):
        mi=doc['nodes'][nodes[node]]['mesh'];names=doc['meshes'][mi].get('extras',{}).get('targetNames',[]);return {'node':nodes[node],'index':names.index(key),'weight':1}
    def binds(*items):return {'morphTargetBinds':[morph(*i) for i in items],'isBinary':False,'overrideBlink':'none','overrideLookAt':'none','overrideMouth':'none'}
    preset={
      'blink':binds(('Eye_L','Blink'),('Eye_R','Blink')),'blinkLeft':binds(('Eye_L','Blink')),'blinkRight':binds(('Eye_R','Blink')),
      'aa':binds(('Mouth','A')),'ih':binds(('Mouth','I')),'ou':binds(('Mouth','U')),'ee':binds(('Mouth','E')),'oh':binds(('Mouth','O')),
      'happy':binds(('Mouth','Smile')),'sad':binds(('Mouth','Sad'),('Eye_L','Tired'),('Eye_R','Tired')),'angry':binds(('Mouth','Irritated'),('Eye_L','Squint'),('Eye_R','Squint')),
      'relaxed':binds(('Eye_L','Tired'),('Eye_R','Tired')),'surprised':binds(('Mouth','Surprised'),('Eye_L','Wide'),('Eye_R','Wide')),
      'lookLeft':binds(('Iris_L','LookLeft'),('Iris_R','LookLeft')),'lookRight':binds(('Iris_L','LookRight'),('Iris_R','LookRight')),
      'lookUp':binds(('Iris_L','LookUp'),('Iris_R','LookUp')),'lookDown':binds(('Iris_L','LookDown'),('Iris_R','LookDown'))}
    custom={'tired':binds(('Eye_L','Tired'),('Eye_R','Tired')),'serious':binds(('Eye_L','Squint'),('Eye_R','Squint')),'irritated':binds(('Mouth','Irritated'),('Eye_L','Squint'),('Eye_R','Squint')),'awkward':binds(('Mouth','Awkward')),'what_the_hell':binds(('Eye_L','Squint'),('Mouth','Awkward'))}
    vrm={'specVersion':'1.0','meta':{'name':'DENDICH / RADIO SILENCE','version':'1.0','authors':['DENDICH','Codex procedural build'],'copyrightInformation':'Original character based on supplied production brief','contactInformation':'','references':['DENDICH production brief and supplied reference sheets'],'thirdPartyLicenses':'','avatarPermission':'onlyAuthor','allowExcessivelyViolentUsage':False,'allowExcessivelySexualUsage':False,'commercialUsage':'personalNonProfit','allowPoliticalOrReligiousUsage':False,'allowAntisocialOrHateUsage':False,'creditNotation':'required','allowRedistribution':False,'modification':'allowModificationRedistribution','otherLicenseUrl':'https://vrm.dev/licenses/1.0/'},
      'humanoid':{'humanBones':human},'firstPerson':{'meshAnnotations':[{'node':nodes[n.get('name')],'type':'auto'} for n in doc['nodes'] if 'mesh' in n]},
      'lookAt':{'offsetFromHeadBone':[0,-.10,.04],'type':'expression','rangeMapHorizontalInner':{'inputMaxValue':45,'outputScale':1},'rangeMapHorizontalOuter':{'inputMaxValue':45,'outputScale':1},'rangeMapVerticalDown':{'inputMaxValue':35,'outputScale':1},'rangeMapVerticalUp':{'inputMaxValue':35,'outputScale':1}},
      'expressions':{'preset':preset,'custom':custom}}
    spring={'specVersion':'1.0','colliders':[{'node':nodes['head'],'shape':{'sphere':{'offset':[0,0,0],'radius':.17}}}], 'colliderGroups':[{'name':'Head','colliders':[0]}], 'springs':[]}
    for i in range(10):spring['springs'].append({'name':f'Hair {i+1}','joints':[{'node':nodes[f'hair_{i}_0'],'hitRadius':.012,'stiffness':1.15,'gravityPower':.08,'gravityDir':[0,-1,0],'dragForce':.35},{'node':nodes[f'hair_{i}_1'],'hitRadius':.01,'stiffness':.85,'gravityPower':.12,'gravityDir':[0,-1,0],'dragForce':.42}],'colliderGroups':[0]})
    doc.setdefault('extensions',{})['VRMC_vrm']=vrm;doc['extensions']['VRMC_springBone']=spring
    used=doc.setdefault('extensionsUsed',[])
    for x in ['VRMC_vrm','VRMC_springBone']:
        if x not in used:used.append(x)
    raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
    out=OUT/'DENDICH_RADIO_SILENCE.vrm';out.write_bytes(struct.pack('<III',0x46546c67,2,20+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw+binary);glb.unlink();return out

def lighting_and_render():
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
    scene.view_settings.look='AgX - Medium High Contrast';scene.world.color=(.008,.010,.009)
    for loc,energy,color,size in [((-3,-4,5),900,(1,.72,.55),4),((3,-2,3),650,(.55,.68,1),3),((0,2,4),800,(.62,.75,.62),3)]:
        bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=energy;l.data.color=color;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,1.45))-l.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(0,-5.1,1.55));cam=bpy.context.object;cam.data.lens=58;cam.rotation_euler=(Vector((0,0,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    scene.render.filepath=str(RENDERS/'DENDICH_full_front.png');bpy.ops.render.render(write_still=True)
    cam.location=(.55,-4.1,1.78);cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=68;scene.render.filepath=str(RENDERS/'DENDICH_halfbody_3q.png');bpy.ops.render.render(write_still=True)
    cam.location=(0,-3.0,2.03);cam.rotation_euler=(Vector((0,0,2.01))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=72;scene.render.filepath=str(RENDERS/'DENDICH_face_closeup.png');bpy.ops.render.render(write_still=True)

def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    arm=rig();face(arm);hair(arm);torso_and_limbs(arm);equipment(arm);headset(arm)
    lighting_and_render();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'DENDICH_RADIO_SILENCE.blend'));export_vrm1(arm)

if __name__=='__main__':main()
