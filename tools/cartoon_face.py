"""Opaque, layered cartoon facial geometry with VRM-compatible morph names."""
import math
import bpy


def make_accent(api,name,cx,cz,width,height,color):
    material=api['mat'](name+' material',color,.58);segments=64
    verts=[(cx,api['surface']('pineapple',cx,cz,.024),cz)];faces=[]
    for i in range(segments):
        a=math.tau*i/segments;x=cx+width*math.cos(a);z=cz+height*math.sin(a)
        verts.append((x,api['surface']('pineapple',x,z,.024),z))
    for i in range(segments):faces.append((0,1+i,1+(i+1)%segments))
    return api['mesh_object'](name,verts,faces,material)


def make_feature(api, name, cx, cz, mouth=False):
    material_specs=[('Ink',(.012,.018,.025)),('White',(.94,.96,.90)),('Iris',(.025,.38,.28)),('Pupil',(.006,.012,.018)),('Spark',(1,1,1)),('Tongue',(.85,.15,.24))]
    materials=[api['mat']('Cartoon '+n,c,.45) for n,c in material_specs]
    # Each disk has fixed topology, allowing every expression to share indices.
    parts=[(0,'border'),(1,'white'),(2,'iris'),(3,'pupil'),(4,'spark'),(4,'spark2'),(0,'brow')] if not mouth else [(0,'cavity'),(1,'teeth'),(5,'tongue')]
    rings=8;segments=64
    samples=[(j/rings,math.tau*i/segments) for j in range(rings+1) for i in range(segments)]

    def vertices(expression):
        verts=[]
        for _,part in parts:
            for r,a in samples:
                nx=r*math.cos(a);nz=r*math.sin(a)
                if mouth:
                    styles={'Basis':(.145,.007,0),'A':(.130,.095,1),'I':(.170,.027,1),'U':(.075,.060,0),'E':(.165,.065,1),'O':(.080,.105,0),'JOY':(.170,.090,1),'SORROW':(.130,.009,0),'ANGRY':(.145,.018,0)}
                    w,h,showteeth=styles[expression]
                    curve=(-.020 if expression=='SORROW' else .024)*nx*nx
                    offset=.022
                    if part=='cavity':x=cx+w*nx;z=cz+h*nz+curve
                    elif part=='teeth':
                        x=cx+w*.78*nx;z=cz+h*.55+h*.20*nz+curve
                        offset=.033 if showteeth else .010
                        if not showteeth:x=cx+w*.001*nx;z=cz+h*.001*nz
                    else:
                        x=cx+w*.60*nx;z=cz-h*.63+h*.23*nz+curve
                        offset=.036 if h>.04 else .010
                        if h<=.04:x=cx+w*.001*nx;z=cz+h*.001*nz
                else:
                    # Happy raises the brows rather than squeezing the eyes:
                    # additive Joy + Blink must still produce closed eyes.
                    blink=expression=='Blink'
                    squash=.035 if blink else 1
                    dx={'LookLeft':.026,'LookRight':-.026}.get(expression,0)
                    dz={'LookUp':.019,'LookDown':-.019}.get(expression,0)
                    spec={'border':(.143,.120,0,0,.016),'white':(.130,.107,0,0,.025),'iris':(.059,.079,dx,dz,.037),'pupil':(.030,.056,dx,dz,.045),'spark':(.017,.023,dx-.017,dz+.032,.053),'spark2':(.008,.010,dx+.020,dz-.029,.054),'brow':(.118,.012,0,.153,.021)}
                    w,h,ox,oz,offset=spec[part]
                    x=cx+ox+w*nx
                    z=cz+(oz+h*nz)*(1 if part=='brow' else squash)
                    if blink and part not in {'border','brow'}:offset=.010
                    if expression=='Happy' and part=='brow':z+=.018
                    if part=='brow':z+=.012*nx*(1 if cx<0 else -1)
                # Every visible layer follows the actual skin rather than a flat plane.
                y=api['surface']('pineapple',x,z,offset)
                verts.append((x,y,z))
        return verts

    faces=[];indices=[];stride=len(samples)
    for p,(material,_) in enumerate(parts):
        for j in range(rings):
            for i in range(segments):
                q=p*stride+j*segments+i;n=p*stride+j*segments+(i+1)%segments
                faces.append((q,q+segments,n+segments,n));indices.append(material)
    ob=api['mesh_object'](name,vertices('Basis'),faces,materials[0])
    for material in materials[1:]:ob.data.materials.append(material)
    for polygon,index in zip(ob.data.polygons,indices):polygon.material_index=index
    ob['face_style']='cartoon'
    ob.shape_key_add(name='Basis')
    names=['A','I','U','E','O','JOY','SORROW','ANGRY'] if mouth else ['Blink','Happy','LookLeft','LookRight','LookUp','LookDown']
    for expression in names:
        key=ob.shape_key_add(name=expression)
        for v,co in zip(key.data,vertices(expression)):v.co=co
    return ob
