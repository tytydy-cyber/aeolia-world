import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {WorldAudio} from './audio.js';
import {MotionEffects} from './effects.js';
import {applyTravelerDesign} from './character-designs.js';

const stageKey=new URLSearchParams(location.search).get('stage')==='somnia'?'somnia':'parallax';
const STAGES={
  parallax:{name:'パララックス',code:'CLOSED COMPLEX 02',intro:'閉館したホテル、学校、浴場、商業施設。すべてが一棟の中で、用途を忘れたまま続いている。',sky:0x747462,fog:0x777666,fogDensity:.0045,ground:0x82775e,spawn:[11,0,63],limitY:21,
    notes:[[-55,0,34,'閉鎖された宴会場','椅子だけが、壇上のない方向を向いている。'],[52,0,38,'夜間の受付','呼び鈴は鳴るが、奥から返事はない。'],[-52,0,-38,'水のない浴場','排水口から遠い雨音が聞こえる。'],[48,0,-42,'地下搬入口','案内板には存在しない階が記されている。'],[0,0,-69,'消灯した渡り廊下','窓の向こうにも同じ廊下が続いている。']]},
  somnia:{name:'ソムニア',code:'FORGOTTEN SUBURB 03',intro:'夕方の学校、真昼の団地、夜明け前の公園。扉を隔てて、別々の記憶が隣り合う。',sky:0xa8b3d4,fog:0xb9b6ca,fogDensity:.0034,ground:0x8b9877,spawn:[0,0,62],limitY:48,
    notes:[[-54,0,24,'夕方の昇降口','靴箱には、まだ温かい上履きが一足だけ残る。'],[53,0,30,'昼の団地','すべてのベランダで同じカーテンが揺れている。'],[-45,0,-42,'朝の来ない公園','遊具の影だけが先に動く。'],[47,0,-45,'時間不明のプール','水面は空ではなく、教室の天井を映している。'],[0,0,-74,'草原の非常口','扉の向こうにも風が吹いている。']]}
};
const cfg=STAGES[stageKey];
document.title=`${cfg.name} — AEOLIA`;for(const id of ['title','worldName'])document.querySelector('#'+id).textContent=cfg.name;for(const id of ['code','worldCode'])document.querySelector('#'+id).textContent=cfg.code;document.querySelector('#intro').textContent=cfg.intro;

const scene=new THREE.Scene();scene.background=new THREE.Color(cfg.sky);scene.fog=new THREE.FogExp2(cfg.fog,cfg.fogDensity);
const camera=new THREE.PerspectiveCamera(60,innerWidth/innerHeight,.1,650),renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.02;renderer.domElement.tabIndex=0;document.body.prepend(renderer.domElement);
scene.add(new THREE.HemisphereLight(stageKey==='parallax'?0xded4a2:0xcdd9ff,stageKey==='parallax'?0x35362e:0x625a72,1.9));
const sun=new THREE.DirectionalLight(stageKey==='parallax'?0xffe4a3:0xffd1d9,2.2);sun.position.set(-45,85,30);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=sun.shadow.camera.bottom=-100;sun.shadow.camera.right=sun.shadow.camera.top=100;scene.add(sun);
function patternTexture(base,line,kind){const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d');x.fillStyle=base;x.fillRect(0,0,128,128);x.fillStyle=line;
  if(kind==='carpet')for(let i=0;i<520;i++){const px=(i*47)%128,py=(i*79)%128;x.globalAlpha=.08+(i%5)*.025;x.fillRect(px,py,1+(i%3),1)}
  else{for(let i=0;i<=128;i+=16){x.globalAlpha=.16;x.fillRect(i,0,1,128);x.fillRect(0,i,128,1)}}
  const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(kind==='carpet'?18:8,kind==='carpet'?15:5);t.colorSpace=THREE.SRGBColorSpace;return t}
const floorMap=patternTexture(stageKey==='parallax'?'#85795d':'#879475',stageKey==='parallax'?'#413d34':'#43533e','carpet'),wallMap=patternTexture(stageKey==='parallax'?'#c9c39e':'#d5d0c6','#8c876f','grid');
const mats={
  carpet:new THREE.MeshStandardMaterial({map:floorMap,roughness:1}),wall:new THREE.MeshStandardMaterial({map:wallMap,roughness:.9}),dark:new THREE.MeshStandardMaterial({color:0x273238,roughness:.75}),wood:new THREE.MeshStandardMaterial({color:0x765645,roughness:.9}),pink:new THREE.MeshStandardMaterial({color:0xcf8fa4,roughness:.8}),water:new THREE.MeshPhysicalMaterial({color:0x7ca9bd,transparent:true,opacity:.72,roughness:.16}),glow:new THREE.MeshStandardMaterial({color:0xffecc0,emissive:0xffd98b,emissiveIntensity:1.3,roughness:.3})
};
const colliders=[],world=new THREE.Group();scene.add(world);
function mesh(g,m,x,y,z,shadow=true){const o=new THREE.Mesh(g,m);o.position.set(x,y,z);o.castShadow=shadow;o.receiveShadow=shadow;world.add(o);return o}
function box(x,y,z,w,h,d,m=mats.wall,solid=false){const o=mesh(new THREE.BoxGeometry(w,h,d),m,x,y,z);if(solid)colliders.push({x,z,w:w/2,d:d/2,bottom:y-h/2,top:y+h/2});return o}
function wall(x,z,w,d,h=10,m=mats.wall){return box(x,h/2,z,w,h,d,m,true)}
function lightPanel(x,y,z,w=4,d=1.2){const p=box(x,y,z,w,.12,d,mats.glow,false);const l=new THREE.PointLight(0xffe5aa,30,42);l.position.set(x,y-.3,z);world.add(l);return p}

function buildParallax(){
  box(0,-.35,0,200,.7,170,mats.carpet);box(0,24,0,200,.8,170,mats.dark,false);for(const [x,z,w,d] of [[0,-84,200,2],[0,84,200,2],[-99,0,2,170],[99,0,2,170]])wall(x,z,w,d,24,mats.dark);
  // Four recognizable facilities joined by a broad central concourse.
  for(const [x,z,w,d] of [[-50,17,2,92],[-18,50,66,2],[-18,-10,66,2],[50,15,2,94],[18,-12,66,2],[-52,-45,74,2],[52,-48,72,2]])wall(x,z,w,d,9);
  wall(-5,52,20,2,9);wall(34,52,34,2,9);
  for(let row=-2;row<=2;row++)for(let i=-4;i<=4;i++)lightPanel(i*20,23.4,row*31+8,7,1.4);
  for(const x of [-82,-67,-52,-37,-22]){box(x,1.5,34,9,3,1,mats.wood,true);box(x,3.3,34,8,.3,3,mats.wall)}
  // Hotel desk and luggage rhythm.
  box(65,1.2,38,26,2.4,3,mats.wood,true);for(let i=0;i<7;i++)box(55+i*4,.45,31,1.8,.9,1.3,i%2?mats.dark:mats.pink,true);
  // Empty bath and tiled rim.
  box(-66,-.55,-43,28,.45,22,mats.water);for(const [x,z,w,d] of [[-66,-54,32,2],[-66,-32,32,2],[-81,-43,2,22],[-51,-43,2,22]])box(x,.25,z,w,.5,d,mats.wall,true);
  // Loading bay stripes and impossible numbered doors.
  for(let i=0;i<7;i++){box(26+i*8,.02,-40,4,.04,18,i%2?mats.dark:mats.wall,false);const door=box(25+i*10,3,-56,6,6,.45,mats.dark,true);door.userData.anomaly=i===5}
  // Repeating columns make scale readable while instancing keeps cost low.
  const cols=new THREE.InstancedMesh(new THREE.CylinderGeometry(.55,.65,10,10),mats.wall,40),dummy=new THREE.Object3D();let n=0;
  for(let x=-88;x<=88;x+=22)for(const z of [-72,-20,18,70]){dummy.position.set(x,5,z);dummy.updateMatrix();cols.setMatrixAt(n++,dummy.matrix)}cols.count=n;cols.castShadow=true;cols.receiveShadow=true;world.add(cols);
}
function buildSomnia(){
  box(0,-.4,0,230,.8,200,mats.carpet);const road=new THREE.MeshStandardMaterial({color:0x666b70,roughness:1});box(0,.01,0,18,.08,200,road,false);box(0,.015,0,1,.09,190,mats.wall,false);
  // School at sunset.
  box(-58,9,24,58,18,32,mats.wall,true);for(let r=0;r<3;r++)for(let c=0;c<6;c++)box(-80+c*9,6+r*5,40.15,4,2.7,.3,mats.dark,false);box(-58,1,43,16,2,5,mats.wood,true);
  // Apartment blocks and identical curtains.
  for(const z of [15,42]){box(62,12,z,36,24,15,mats.wall,true);for(let r=0;r<4;r++)for(let c=0;c<5;c++){box(46+c*8,5+r*5,z-7.6,3.5,2,.2,mats.dark,false);box(46+c*8,4+r*5,z-8,6,.18,1.2,mats.wood,false)}}
  // Playground silhouettes.
  const pole=(x,z,h=5)=>box(x,h/2,z,.22,h,.22,mats.dark);for(const x of [-56,-48]){pole(x,-42);pole(x,-34);box(x,4.8,-38,.22,.22,8,mats.dark)}
  const slide=box(-34,2.2,-45,10,.4,3,mats.pink,true);slide.rotation.z=-.28;for(let i=0;i<6;i++)pole(-62+i*3,-55,3+Math.sin(i)*.4);
  // Indoor pool without enclosing walls: a room remembered outdoors.
  box(48,-.15,-48,34,.3,22,mats.water);for(const z of [-58,-38])box(48,.18,z,38,.35,2,mats.wall,true);for(const x of [30,66])box(x,.18,-48,2,.35,22,mats.wall,true);
  // Doors standing alone across the field.
  for(const [x,z,r] of [[-20,-68,0],[20,-73,.3],[78,-70,-.2]]){const g=new THREE.Group();for(const [px,py,w,h] of [[-2,2.7,.3,5.4],[2,2.7,.3,5.4],[0,5.25,4.3,.3]]){const q=new THREE.Mesh(new THREE.BoxGeometry(w,h,.35),mats.pink);q.position.set(px,py,0);g.add(q)}g.position.set(x,0,z);g.rotation.y=r;world.add(g)}
  // Trees as a small instanced grove.
  const trunks=new THREE.InstancedMesh(new THREE.CylinderGeometry(.25,.48,5,8),mats.wood,45),crowns=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(2.2,1),new THREE.MeshStandardMaterial({color:0x667a64,roughness:1}),45),dummy=new THREE.Object3D();
  for(let i=0;i<45;i++){const a=i*2.399,r=74+(i%5)*5,x=Math.cos(a)*r,z=Math.sin(a)*r;dummy.position.set(x,2.5,z);dummy.updateMatrix();trunks.setMatrixAt(i,dummy.matrix);dummy.position.y=6;dummy.scale.set(1+(i%3)*.15,.8+(i%2)*.2,1);dummy.updateMatrix();crowns.setMatrixAt(i,dummy.matrix)}trunks.castShadow=crowns.castShadow=true;world.add(trunks,crowns);
}
(stageKey==='parallax'?buildParallax:buildSomnia)();

// The same remembered species takes on each world's materials.
const creatures=[];
const groundRoutes=stageKey==='parallax'?[[10,64,6],[-70,35,9],[66,38,10],[-66,-43,7],[64,-50,8],[0,24,13],[-23,-29,8],[25,-29,8]]:[[0,67,9],[-56,23,16],[61,28,13],[-48,-43,12],[48,-48,11],[0,-20,18],[78,-66,8],[-82,-63,10]];
function makeGroundCreature(i){const g=new THREE.Group(),bodyMat=new THREE.MeshStandardMaterial({color:stageKey==='parallax'?0xb6aa79:0xd7b4c5,emissive:stageKey==='parallax'?0x3a361e:0x4a3141,emissiveIntensity:.35,roughness:.8});
  const body=new THREE.Mesh(new THREE.CapsuleGeometry(.62,1.25,5,10),bodyMat);body.rotation.z=Math.PI/2;body.position.y=1.35;g.add(body);const head=new THREE.Mesh(new THREE.SphereGeometry(.48,14,10),bodyMat);head.position.set(1,1.65,0);g.add(head);
  for(const z of [-.38,.38])for(const x of [-.55,.6]){const leg=new THREE.Mesh(new THREE.CapsuleGeometry(.09,.75,4,7),bodyMat);leg.position.set(x,.62,z);g.add(leg)}
  for(const z of [-.28,.28]){const horn=new THREE.Mesh(new THREE.ConeGeometry(.09,.8,7),mats.glow);horn.position.set(1.14,2.28,z);horn.rotation.z=-.35;g.add(horn)}
  const [cx,cz,radius]=groundRoutes[i],phase=i*1.7;g.position.set(cx+Math.cos(phase)*radius,0,cz+Math.sin(phase)*radius);world.add(g);creatures.push({g,phase,speed:.09+i*.003,radius,cx,cz,kind:'ground'});
}
function makeBird(i){const g=new THREE.Group(),m=new THREE.MeshStandardMaterial({color:stageKey==='parallax'?0xd8d0a7:0xede2ec,side:THREE.DoubleSide,roughness:.8});for(const side of [-1,1]){const wing=new THREE.Mesh(new THREE.PlaneGeometry(1.2,.5,2,1),m);wing.position.x=side*.58;wing.rotation.y=side*.18;g.add(wing)}world.add(g);creatures.push({g,phase:i/18*Math.PI*2,speed:.08+i*.001,radius:35+(i%4)*6,kind:'bird'})}
for(let i=0;i<8;i++)makeGroundCreature(i);for(let i=0;i<18;i++)makeBird(i);

const player=new THREE.Group(),coat=new THREE.MeshStandardMaterial({color:0x526e78,roughness:.9}),skin=new THREE.MeshStandardMaterial({color:0xd9ad88,roughness:.8});scene.add(player);
const robe=new THREE.Mesh(new THREE.CapsuleGeometry(.52,1.45,8,16),coat);robe.position.y=1.35;player.add(robe);const head=new THREE.Mesh(new THREE.SphereGeometry(.42,20,14),skin);head.position.y=2.65;player.add(head);const hat=new THREE.Mesh(new THREE.CylinderGeometry(.72,.78,.12,28),mats.wood);hat.position.y=3.02;player.add(hat);const crown=new THREE.Mesh(new THREE.CylinderGeometry(.38,.48,.34,24),mats.wood);crown.position.y=3.2;player.add(crown);player.traverse(o=>{if(o.isMesh)o.castShadow=true});player.position.set(...cfg.spawn);
let avatarMixer=null,avatarActions={},avatarState='';function setAvatarAction(name){if(name===avatarState||!avatarActions[name])return;const next=avatarActions[name],previous=avatarActions[avatarState];next.reset().fadeIn(.2).play();if(previous)previous.fadeOut(.2);avatarState=name}
new GLTFLoader().load('assets/aeolia-traveler.glb',gltf=>{const model=gltf.scene;model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true}});player.add(model);applyTravelerDesign(THREE,player,model,localStorage.getItem('aeolia-character')||'ember');for(const o of [robe,head,hat,crown])o.visible=false;avatarMixer=new THREE.AnimationMixer(model);for(const clip of gltf.animations)avatarActions[clip.name]=avatarMixer.clipAction(clip);setAvatarAction('Idle')},undefined,error=>console.warn('Traveler model fallback in use',error));
const sound=new WorldAudio(),motionEffects=new MotionEffects(THREE,scene,camera);
const keys={},velocity=new THREE.Vector3(),lastSafe=player.position.clone(),targetCam=new THREE.Vector3();let yaw=0,pitch=.25,flying=false,started=false,dragging=false,previous=null,bob=0,nextAnomaly=performance.now()+360000+Math.random()*240000,recenterYaw=null,travelYaw=0;
function contains(c,x,z,margin=.55){return Math.abs(x-c.x)<c.w+margin&&Math.abs(z-c.z)<c.d+margin}
function validGround(x,z){return Math.abs(x)<(stageKey==='parallax'?96:112)&&Math.abs(z)<(stageKey==='parallax'?81:96)}
function resetKeys(){for(const k in keys)delete keys[k];velocity.set(0,0,0);dragging=false}
function saveNote(note){let notes=[];try{notes=JSON.parse(localStorage.getItem('aeolia-notes')||'[]')}catch{}const id=stageKey+':'+note[3];if(notes.some(n=>n.id===id))return false;notes.push({id,world:cfg.name,name:note[3],text:note[4]});localStorage.setItem('aeolia-notes',JSON.stringify(notes));return true}
let nextDiscover=0;
function discover(t){if(t<nextDiscover)return;nextDiscover=t+500;let nearest=cfg.notes[0],best=Infinity;for(const n of cfg.notes){const d=Math.hypot(player.position.x-n[0],player.position.z-n[2]);if(d<best){best=d;nearest=n}if(d<10&&saveNote(n)){sound.chime();showEvent(n[3])}}document.querySelector('#place').textContent=nearest[3]}
let eventTimer;function showEvent(text){const e=document.querySelector('#event');e.querySelector('div').textContent=text;e.classList.add('on');clearTimeout(eventTimer);eventTimer=setTimeout(()=>e.classList.remove('on'),2600)}
function anomaly(t){if(t<nextAnomaly)return;nextAnomaly=t+360000+Math.random()*300000;const candidates=[];world.traverse(o=>{if(o.userData.anomaly)candidates.push(o)});if(candidates.length){const o=candidates[Math.floor(Math.random()*candidates.length)];o.visible=!o.visible}scene.fog.density=cfg.fogDensity*1.8;setTimeout(()=>scene.fog.density=cfg.fogDensity,9000);showEvent(stageKey==='parallax'?'さっきまで、ここに扉はなかった。':'遠くで下校のチャイムが鳴った。')}
function updateCreatures(dt,t){for(const c of creatures){c.phase+=c.speed*dt;const flee=Math.max(0,12-player.position.distanceTo(c.g.position));c.phase+=flee*dt*.025;c.g.position.x=(c.cx||0)+Math.cos(c.phase)*c.radius;c.g.position.z=(c.cz||0)+Math.sin(c.phase)*c.radius;if(c.kind==='bird'){c.g.position.y=10+(c.radius-35)*.18+Math.sin(t*.002+c.phase)*2;c.g.rotation.y=-c.phase+Math.PI/2;c.g.children.forEach((w,i)=>w.rotation.z=(i?-1:1)*(.22+Math.sin(t*.008+c.phase)*.35))}else{c.g.position.y=Math.abs(Math.sin(t*.003+c.phase))*.12;c.g.rotation.y=-c.phase;c.g.rotation.z=Math.sin(t*.004+c.phase)*.025}}}
function update(dt,t){if(keys.KeyQ||keys.KeyE)recenterYaw=null;if(keys.KeyQ)yaw+=dt*1.2;if(keys.KeyE)yaw-=dt*1.2;if(recenterYaw!==null){const d=Math.atan2(Math.sin(recenterYaw-yaw),Math.cos(recenterYaw-yaw));yaw+=d*(1-Math.exp(-7*dt));pitch=THREE.MathUtils.damp(pitch,.25,7,dt);if(Math.abs(d)<.005)recenterYaw=null}const fwd=new THREE.Vector3(-Math.sin(yaw),0,-Math.cos(yaw)),right=new THREE.Vector3(Math.cos(yaw),0,-Math.sin(yaw)),input=new THREE.Vector3().addScaledVector(fwd,(keys.ArrowUp||keys.KeyW?1:0)-(keys.ArrowDown||keys.KeyS?1:0)).addScaledVector(right,(keys.ArrowRight||keys.KeyD?1:0)-(keys.ArrowLeft||keys.KeyA?1:0));if(input.lengthSq())input.normalize();const fast=keys.ControlLeft||keys.ControlRight,speed=flying?(fast?42:26):(fast?16:10);velocity.x=THREE.MathUtils.damp(velocity.x,input.x*speed,input.lengthSq()?5:15,dt);velocity.z=THREE.MathUtils.damp(velocity.z,input.z*speed,input.lengthSq()?5:15,dt);velocity.y=flying?THREE.MathUtils.damp(velocity.y,((keys.Space?1:0)-(keys.ShiftLeft||keys.ShiftRight?1:0))*16,6,dt):-12;
  const before=player.position.clone();for(const axis of ['x','z']){const old=player.position[axis];player.position[axis]+=velocity[axis]*dt;const blocked=colliders.some(c=>contains(c,player.position.x,player.position.z)&&player.position.y<c.top&&player.position.y+3.6>c.bottom);if(blocked||!validGround(player.position.x,player.position.z)){player.position[axis]=old;velocity[axis]=0}}
  player.position.y+=velocity.y*dt;if(player.position.y<0){player.position.y=0;velocity.y=0;lastSafe.copy(player.position)}if(player.position.y>cfg.limitY){player.position.y=cfg.limitY;velocity.y=Math.min(0,velocity.y)}if(player.position.y<-20)player.position.copy(lastSafe);
  const hs=Math.hypot(velocity.x,velocity.z);if(hs>.15){travelYaw=Math.atan2(-velocity.x,-velocity.z);const a=Math.atan2(velocity.x,velocity.z),d=Math.atan2(Math.sin(a-player.rotation.y),Math.cos(a-player.rotation.y));player.rotation.y+=d*(1-Math.exp(-7*dt))}bob+=hs*dt;robe.position.y=1.35+Math.abs(Math.sin(bob))*.045;if(avatarMixer){setAvatarAction(flying?'Fly':hs>.1?'Walk':'Idle');if(avatarActions.Walk)avatarActions.Walk.timeScale=Math.max(.55,hs/5.8);avatarMixer.update(dt)}
  const dist=flying?12:9,up=flying?6:4.2;targetCam.set(player.position.x+Math.sin(yaw)*dist,player.position.y+up+Math.sin(pitch)*6,player.position.z+Math.cos(yaw)*dist);camera.position.lerp(targetCam,1-Math.exp(-8*dt));camera.lookAt(player.position.x,player.position.y+2,player.position.z);updateCreatures(dt,t);motionEffects.update(dt,player.position,velocity,flying,player.position.y<.15);sound.update(dt,velocity.length(),flying,player.position.y<.15,false);discover(t);anomaly(t)
}
function loop(t){const elapsed=previous===null?0:Math.min(.1,(t-previous)/1000);previous=t;if(started&&elapsed){const steps=Math.ceil(elapsed*120);for(let i=0;i<steps;i++)update(elapsed/steps,t)}renderer.render(scene,camera);if(location.search.includes('debug=1'))document.querySelector('#perf').value=`${renderer.info.render.calls} calls\n${renderer.info.render.triangles.toLocaleString()} triangles\n${player.position.x.toFixed(1)}, ${player.position.y.toFixed(1)}, ${player.position.z.toFixed(1)}`;requestAnimationFrame(loop)}
camera.position.set(cfg.spawn[0],7,cfg.spawn[2]+10);camera.lookAt(player.position);requestAnimationFrame(loop);
addEventListener('keydown',e=>{if(!started)return;if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(e.code))e.preventDefault();keys[e.code]=true;if(e.code==='KeyF'&&!e.repeat){flying=!flying;velocity.y=flying?3:0;motionEffects.flightBurst(player.position,flying);sound.flightCue(flying);showEvent(flying?'飛行へ':'歩行へ')}if(e.code==='KeyC'&&!e.repeat)recenterYaw=travelYaw});addEventListener('keyup',e=>keys[e.code]=false);addEventListener('blur',()=>{resetKeys();previous=null;sound.pause()});document.addEventListener('visibilitychange',()=>{if(document.hidden){resetKeys();previous=null;sound.pause()}else if(started)sound.start()});
renderer.domElement.addEventListener('pointerdown',e=>{if(started){dragging=true;renderer.domElement.setPointerCapture(e.pointerId);renderer.domElement.style.cursor='grabbing'}});addEventListener('pointerup',()=>{dragging=false;renderer.domElement.style.cursor='grab'});addEventListener('pointermove',e=>{if(dragging&&e.buttons){yaw-=e.movementX*.003;pitch=THREE.MathUtils.clamp(pitch+e.movementY*.002,-.5,1.1)}});renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());
document.querySelector('#enter').onclick=()=>{started=true;sound.start();renderer.domElement.focus();const v=document.querySelector('#veil');v.style.opacity=0;v.style.pointerEvents='none';setTimeout(()=>v.remove(),850)};addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});if(location.search.includes('debug=1'))document.querySelector('#perf').hidden=false;
