import * as THREE from 'three';
import {GLTFLoader} from './vendor/three/loaders/GLTFLoader.js';

const $=id=>document.getElementById(id);
const video=$('cameraVideo'),stage=$('stage');
const state={running:false,starting:false,stream:null,tracker:null,lastSeen:0,frames:0,lastFps:performance.now(),active:null,neutral:null,latestPose:null,loadId:0,frameId:0};
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(34,1,.01,30);camera.position.set(0,.14,3.35);camera.lookAt(0,.14,0);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0x171c17,1);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;stage.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xfff4e5,0x52583c,2));
for(const [xyz,power] of [[[2,3,4],3],[[-3,1,2],1.5],[[1,3,-2],2]]){const l=new THREE.DirectionalLight(0xffffff,power);l.position.set(...xyz);scene.add(l);}
const pivot=new THREE.Group();scene.add(pivot);
const loader=new GLTFLoader(),models=new Map(),targetPose=new THREE.Vector3();
const tiles={};
for(const name of ['Eye_L','Eye_R','Mouth']){const canvas=document.createElement('canvas');canvas.width=512;canvas.height=256;const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.minFilter=THREE.LinearFilter;texture.generateMipmaps=false;tiles[name]={canvas,ctx:canvas.getContext('2d'),texture};}
const resize=()=>{const {width,height}=stage.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/Math.max(height,1);camera.updateProjectionMatrix();};new ResizeObserver(resize).observe(stage);
function status(text){$('status').textContent=text;}
function fail(text){$('error').hidden=false;$('error').textContent=text;}
function hideFace(){if(state.active)for(const ob of state.active.userData.features)ob.visible=false;}
function clearError(){$('error').hidden=true;$('error').textContent='';}
async function loadModel(kind){
  const id=++state.loadId;status('Загружаю '+(kind==='orange'?'апельсин':'ананас')+'…');
  try{
    if(!models.has(kind)){
      const gltf=await loader.loadAsync(`models/${kind}.vrm`);const model=gltf.scene;model.position.y=-1.5;model.userData.features=[];model.updateMatrixWorld(true);
      model.traverse(ob=>{
        if(!ob.isMesh)return;
        const key=['Eye_L','Eye_R','Mouth'].find(n=>ob.name===n||ob.name.startsWith(n+'_')||ob.name.startsWith(n+'.'));
        if(!key)return;
        const geometry=ob.geometry.clone(),p=geometry.attributes.position,uv=new Float32Array(p.count*2),box=new THREE.Box3(),points=[];
        // Skin meshes may retain Blender's local axes under a rotated armature.
        // Build projection UVs in the displayed coordinate system, not local XY.
        if(ob.isSkinnedMesh)ob.skeleton.update();
        for(let i=0;i<p.count;i++){const v=new THREE.Vector3();ob.getVertexPosition(i,v);v.applyMatrix4(ob.matrixWorld);points.push(v);box.expandByPoint(v);}
        for(let i=0;i<p.count;i++){uv[2*i]=(points[i].x-box.min.x)/(box.max.x-box.min.x);uv[2*i+1]=(points[i].y-box.min.y)/(box.max.y-box.min.y);}
        geometry.setAttribute('uv',new THREE.BufferAttribute(uv,2));ob.geometry=geometry;
        ob.material=new THREE.MeshBasicMaterial({map:tiles[key].texture,transparent:true,depthWrite:false,side:THREE.DoubleSide,toneMapped:false,vertexColors:false});
        if(ob.morphTargetInfluences)ob.morphTargetInfluences.fill(0);ob.visible=false;ob.renderOrder=2;ob.frustumCulled=false;model.userData.features.push(ob);
      });
      if(model.userData.features.length!==3)throw new Error('В модели не найдены три лицевые сетки.');
      models.set(kind,model);
    }
    if(id!==state.loadId)return;
    if(state.active)pivot.remove(state.active);state.active=models.get(kind);hideFace();pivot.add(state.active);
    const center=kind==='pineapple'?.30:.07;camera.position.set(0,center+.02,kind==='pineapple'?3.5:2.8);camera.lookAt(0,center,0);
    status(state.running?'Камера включена — ищу лицо':'Модель готова. Включи камеру.');
  }catch(e){fail('Не удалось загрузить модель: '+e.message);status('Ошибка загрузки модели');}
}
function crop(tile,source,points,leftIndex,rightIndex,zoom,mouth=false){
  const a=points[leftIndex],b=points[rightIndex],w=source.videoWidth||source.width,h=source.videoHeight||source.height;
  const dx=(b.x-a.x)*w,dy=(b.y-a.y)*h,cx=(a.x+b.x)*w/2;
  let cy=(a.y+b.y)*h/2,span=Math.hypot(dx,dy),angle=Math.atan2(dy,dx);
  if(angle>Math.PI/2)angle-=Math.PI;if(angle< -Math.PI/2)angle+=Math.PI;
  const width=Math.max(8,span*(mouth?1.55:1.75)/zoom),height=width*(mouth?.60:.54);
  if(mouth)cy=(points[13].y+points[14].y)*h/2;
  const {ctx,canvas}=tile,W=canvas.width,H=canvas.height;
  ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation='source-over';ctx.clearRect(0,0,W,H);
  ctx.translate(W/2,H/2);if($('mirror').checked)ctx.scale(-1,1);ctx.scale(W/width,H/height);ctx.rotate(-angle);ctx.drawImage(source,-cx,-cy);
  ctx.setTransform(W/2,0,0,H/2,W/2,H/2);ctx.globalCompositeOperation='destination-in';
  const fade=ctx.createRadialGradient(0,0,.64,0,0,1);fade.addColorStop(0,'rgba(255,255,255,1)');fade.addColorStop(1,'rgba(255,255,255,0)');ctx.fillStyle=fade;ctx.fillRect(-1,-1,2,2);
  ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation='source-over';tile.texture.needsUpdate=true;
}
function applyResults(results,source=video){
  const points=results.multiFaceLandmarks?.[0];
  if(!points){if(performance.now()-state.lastSeen>650){hideFace();status('Лицо не найдено — посмотри в камеру');}return;}
  if(!(source.videoWidth||source.width))return;
  state.lastSeen=performance.now();
  const mirror=$('mirror').checked;
  crop(tiles.Eye_L,source,points,...(mirror?[362,263]:[33,133]),+$('eyeZoom').value);
  crop(tiles.Eye_R,source,points,...(mirror?[33,133]:[362,263]),+$('eyeZoom').value);
  crop(tiles.Mouth,source,points,61,291,+$('mouthZoom').value,true);
  const left=points[33],right=points[263],eyes={x:(left.x+right.x)/2,y:(left.y+right.y)/2,z:(left.z+right.z)/2},mouth=points[13];
  const pose={yaw:Math.atan2(right.z-left.z,right.x-left.x),pitch:Math.atan2(mouth.z-eyes.z,mouth.y-eyes.y),roll:Math.atan2((right.y-left.y)*(source.videoHeight||source.height),(right.x-left.x)*(source.videoWidth||source.width))};
  state.latestPose=pose;if(!state.neutral)state.neutral={...pose};
  const strength=+$('motion').value,sign=mirror?-1:1;
  targetPose.set(THREE.MathUtils.clamp(-(pose.pitch-state.neutral.pitch),-.4,.4)*strength,THREE.MathUtils.clamp(-(pose.yaw-state.neutral.yaw),-.65,.65)*strength*sign,THREE.MathUtils.clamp(-(pose.roll-state.neutral.roll),-.45,.45)*strength*sign);
  if(state.active)for(const ob of state.active.userData.features)ob.visible=true;
  status('В эфире: изображение с твоей камеры');
  state.frames++;const now=performance.now();if(now-state.lastFps>1000){$('fps').textContent=Math.round(state.frames*1000/(now-state.lastFps))+' кадр/с';state.frames=0;state.lastFps=now;}
}
async function ensureTracker(){
  if(state.tracker)return state.tracker;
  const tracker=new window.FaceMesh({locateFile:file=>new URL(`vendor/mediapipe/${file}`,location.href).href});
  tracker.setOptions({maxNumFaces:1,refineLandmarks:false,minDetectionConfidence:.5,minTrackingConfidence:.5,selfieMode:false});
  tracker.onResults(results=>{if(state.running)applyResults(results);});
  await tracker.initialize();state.tracker=tracker;return tracker;
}
async function cameraList(){
  const devices=await navigator.mediaDevices.enumerateDevices(),old=$('camera').value;$('camera').replaceChildren(new Option('Камера по умолчанию',''));
  let n=0;for(const d of devices)if(d.kind==='videoinput')$('camera').add(new Option(d.label||`Камера ${++n}`,d.deviceId));$('camera').value=old;
}
async function loop(token){
  if(!state.running||token!==state.frameId)return;
  try{if(video.readyState>=2)await state.tracker.send({image:video});}
  catch(e){if(state.running){fail('Сбой обработки камеры: '+e.message);stop();}return;}
  if(state.running&&token===state.frameId)requestAnimationFrame(()=>loop(token));
}
async function start(){
  if(state.starting||state.running)return;state.starting=true;$('start').disabled=true;clearError();
  try{
    if(!navigator.mediaDevices?.getUserMedia)throw new Error('Открой приложение через Запустить.bat, а не двойным щелчком по HTML.');
    const device=$('camera').value;status('Ожидаю разрешение камеры…');
    state.stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1280},height:{ideal:720},...(device?{deviceId:{exact:device}}:{})},audio:false});
    video.srcObject=state.stream;await video.play();await cameraList();status('Запускаю отслеживание лица…');await ensureTracker();
    state.running=true;state.neutral=null;state.lastSeen=0;state.frames=0;state.lastFps=performance.now();$('stop').disabled=false;$('calibrate').disabled=false;$('camera').disabled=true;
    loop(++state.frameId);
  }catch(e){stop();const messages={NotAllowedError:'Разреши доступ к камере в браузере и нажми «Включить камеру» снова.',NotFoundError:'Камера не найдена. Подключи веб-камеру.',NotReadableError:'Камера занята. Закрой VSeeFace и другие приложения, использующие её.'};fail(messages[e.name]||e.message);}
  finally{state.starting=false;$('start').disabled=state.running;}
}
function stop(){state.running=false;state.frameId++;state.stream?.getTracks().forEach(t=>t.stop());state.stream=null;video.srcObject=null;hideFace();targetPose.set(0,0,0);$('start').disabled=false;$('stop').disabled=true;$('calibrate').disabled=true;$('camera').disabled=false;$('fps').textContent='';status('Камера остановлена');}
$('start').onclick=start;$('stop').onclick=stop;$('fruit').onchange=()=>loadModel($('fruit').value);
$('calibrate').onclick=()=>{if(state.latestPose){state.neutral={...state.latestPose};targetPose.set(0,0,0);}};
$('showCamera').onchange=()=>{video.hidden=!$('showCamera').checked;};
$('mirror').onchange=()=>{state.neutral=null;};
$('background').onchange=()=>{const value=$('background').value;renderer.setClearColor(value==='green'?0x00ff00:value==='blue'?0x0000ff:0x171c17,value==='transparent'?0:1);stage.style.background=value==='transparent'?'repeating-conic-gradient(#242824 0% 25%,#343834 0% 50%) 0/24px 24px':'';};
for(const [input,output] of [['eyeZoom','eyeValue'],['mouthZoom','mouthValue'],['motion','motionValue']])$(input).oninput=()=>{$(output).value=(+$(input).value).toFixed(2);};
$('output').onclick=()=>{document.body.classList.add('output-mode');resize();};
addEventListener('keydown',e=>{if(e.key==='Escape'){document.body.classList.remove('output-mode');resize();}});
addEventListener('pagehide',stop);
function render(){requestAnimationFrame(render);pivot.rotation.x=THREE.MathUtils.lerp(pivot.rotation.x,targetPose.x,.16);pivot.rotation.y=THREE.MathUtils.lerp(pivot.rotation.y,targetPose.y,.16);pivot.rotation.z=THREE.MathUtils.lerp(pivot.rotation.z,targetPose.z,.16);if(state.running&&state.lastSeen&&performance.now()-state.lastSeen>900)hideFace();renderer.render(scene,camera);}render();
// Read-only diagnostics and an explicit test-image hook. Neither requests the camera.
window.LiveFruit={getState:()=>({running:state.running,model:$('fruit').value,features:state.active?.userData.features.length||0,visible:state.active?.userData.features.filter(o=>o.visible).length||0,lastSeen:state.lastSeen}),
  async testImage(image){const tracker=await ensureTracker();return new Promise(async(resolve,reject)=>{tracker.onResults(r=>{applyResults(r,image);resolve(r.multiFaceLandmarks?.[0]?.length||0);tracker.onResults(results=>{if(state.running)applyResults(results);});});try{await tracker.send({image});}catch(e){reject(e);}});},stop};
await loadModel('orange');
