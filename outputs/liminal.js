import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {WorldAudio} from './audio.js?v=48';
import {MotionEffects} from './effects.js?v=48';
import {applyTravelerDesign} from './character-designs.js?v=45';

const stageKey=new URLSearchParams(location.search).get('stage')==='somnia'?'somnia':'parallax';
const STAGES={
  parallax:{name:'閉鎖施設',code:'COMPLEX 02',intro:'複数の施設が街区規模で連結された、使われていない巨大複合施設。',sky:0x747462,fog:0x777666,fogDensity:.0022,ground:0x82775e,spawn:[11,0,102],limitY:42,
    notes:[[-55,0,34,'宴会場','椅子が並んでいる。'],[52,0,38,'受付','呼び鈴が置かれている。'],[-52,0,-38,'浴場','水は抜かれている。'],[48,0,-42,'搬入口','案内板がある。'],[0,0,-69,'渡り廊下','窓の外にも廊下が見える。']]},
  somnia:{name:'郊外',code:'SOLARPUNK SUBURB 03',intro:'丘陵と水路の先まで、発電設備と空中庭園の郊外が続いている。',sky:0x92c8c5,fog:0xb8d5bf,fogDensity:.0018,ground:0x718c69,spawn:[0,0,86],limitY:58,
    notes:[[-54,0,24,'昇降口','靴箱に上履きがある。'],[53,0,30,'団地','同じカーテンが並んでいる。'],[-45,0,-42,'公園','遊具の影が動く。'],[47,0,-45,'プール','水面に教室の天井が映っている。'],[0,0,-74,'非常口','外は草地につながっている。']]}
};
const cfg=STAGES[stageKey];
document.title=`${cfg.name} — AEOLIA`;for(const id of ['title','worldName'])document.querySelector('#'+id).textContent=cfg.name;for(const id of ['code','worldCode'])document.querySelector('#'+id).textContent=cfg.code;document.querySelector('#intro').textContent=cfg.intro;

const scene=new THREE.Scene();scene.background=new THREE.Color(cfg.sky);scene.fog=new THREE.FogExp2(cfg.fog,cfg.fogDensity);
const camera=new THREE.PerspectiveCamera(60,innerWidth/innerHeight,.1,650),renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.02;renderer.domElement.tabIndex=0;document.body.prepend(renderer.domElement);
scene.add(new THREE.HemisphereLight(stageKey==='parallax'?0xded4a2:0xffefd1,stageKey==='parallax'?0x35362e:0x516953,1.9));
const sun=new THREE.DirectionalLight(stageKey==='parallax'?0xffe4a3:0xffd27a,stageKey==='parallax'?2.2:2.55);sun.position.set(-45,85,30);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=sun.shadow.camera.bottom=-100;sun.shadow.camera.right=sun.shadow.camera.top=100;scene.add(sun);
function patternTexture(base,line,kind){const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d');x.fillStyle=base;x.fillRect(0,0,128,128);x.fillStyle=line;
  if(kind==='carpet')for(let i=0;i<520;i++){const px=(i*47)%128,py=(i*79)%128;x.globalAlpha=.08+(i%5)*.025;x.fillRect(px,py,1+(i%3),1)}
  else{for(let i=0;i<=128;i+=16){x.globalAlpha=.16;x.fillRect(i,0,1,128);x.fillRect(0,i,128,1)}}
  const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(kind==='carpet'?18:8,kind==='carpet'?15:5);t.colorSpace=THREE.SRGBColorSpace;return t}
const floorMap=patternTexture(stageKey==='parallax'?'#85795d':'#879475',stageKey==='parallax'?'#413d34':'#43533e','carpet'),wallMap=patternTexture(stageKey==='parallax'?'#c9c39e':'#d5d0c6','#8c876f','grid');
const textureLoader=new THREE.TextureLoader(),surfaceMap=textureLoader.load(stageKey==='parallax'?'assets/textures/plaster-color.jpg':'assets/textures/grass-color.jpg'),structuralMap=textureLoader.load(stageKey==='parallax'?'assets/textures/slate-color.jpg':'assets/textures/stone-color.jpg');for(const map of [surfaceMap,structuralMap]){map.wrapS=map.wrapT=THREE.RepeatWrapping;map.repeat.set(12,10);map.colorSpace=THREE.SRGBColorSpace}
const mats={
  carpet:new THREE.MeshStandardMaterial({map:surfaceMap,roughness:1}),wall:new THREE.MeshStandardMaterial({map:structuralMap,roughness:.9}),dark:new THREE.MeshStandardMaterial({color:0x273238,roughness:.75}),wood:new THREE.MeshStandardMaterial({color:0x765645,roughness:.9}),pink:new THREE.MeshStandardMaterial({color:0xcf8fa4,roughness:.8}),water:new THREE.MeshPhysicalMaterial({color:0x7ca9bd,transparent:true,opacity:.72,roughness:.16}),glow:new THREE.MeshStandardMaterial({color:0xffecc0,emissive:0xffd98b,emissiveIntensity:1.3,roughness:.3}),solar:new THREE.MeshStandardMaterial({color:0x183e50,metalness:.72,roughness:.22,emissive:0x0c3541,emissiveIntensity:.45}),leaf:new THREE.MeshStandardMaterial({color:0x4d9b61,roughness:.82,emissive:0x183e23,emissiveIntensity:.2})
};
const colliders=[],world=new THREE.Group();scene.add(world);
function mesh(g,m,x,y,z,shadow=true){const o=new THREE.Mesh(g,m);o.position.set(x,y,z);o.castShadow=shadow;o.receiveShadow=shadow;world.add(o);return o}
function box(x,y,z,w,h,d,m=mats.wall,solid=false){const o=mesh(new THREE.BoxGeometry(w,h,d),m,x,y,z);if(solid)colliders.push({x,z,w:w/2,d:d/2,bottom:y-h/2,top:y+h/2});return o}
function wall(x,z,w,d,h=10,m=mats.wall){return box(x,h/2,z,w,h,d,m,true)}
function lightPanel(x,y,z,w=4,d=1.2){return box(x,y,z,w,.12,d,mats.glow,false)}
function addHorizon(file,y=35,scale=1){const t=textureLoader.load(file);t.colorSpace=THREE.SRGBColorSpace;const m=new THREE.MeshBasicMaterial({map:t,transparent:true,depthWrite:false,toneMapped:false,side:THREE.DoubleSide});for(const [z,ry] of [[-245,0],[245,Math.PI]]){const o=mesh(new THREE.PlaneGeometry(340*scale,110*scale),m,0,y,z,false);o.rotation.y=ry;o.renderOrder=-1}}

function corridorBackdrop(){const c=document.createElement('canvas');c.width=512;c.height=256;const x=c.getContext('2d'),g=x.createLinearGradient(0,0,0,256);g.addColorStop(0,'#77755f');g.addColorStop(.55,'#3f4137');g.addColorStop(1,'#161d1c');x.fillStyle=g;x.fillRect(0,0,512,256);x.fillStyle='#111716';for(let i=0;i<13;i++){const w=12+i%3*7,h=45+(i*31)%90;x.fillRect(i*43-10,256-h,w,h)}x.strokeStyle='#d5c98b55';x.lineWidth=2;for(let i=0;i<9;i++){x.beginPath();x.moveTo(256,128);x.lineTo(i*64,256);x.stroke()}const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return new THREE.MeshBasicMaterial({map:t,side:THREE.DoubleSide,toneMapped:false})}

function buildParallax(){
  box(0,-.35,0,350,.7,290,mats.carpet);addHorizon('assets/textures/complex-horizon-v1.png',39,1.05);
  // Broken outer districts extend the playable complex beyond the original central floor plan.
  const districts=[[-132,72,56,45,28],[128,62,70,38,18],[-118,-82,82,46,14],[116,-88,62,54,32],[-62,118,76,34,20],[62,-121,88,28,12]],districtWindows=new THREE.InstancedMesh(new THREE.BoxGeometry(4,2.1,.2),mats.dark,180),districtDummy=new THREE.Object3D();let districtCount=0;
  for(const [x,z,w,d,h] of districts){box(x,h/2,z,w,h,d,mats.wall,true);for(let yy=5;yy<h-2;yy+=5)for(let xx=x-w/2+5;xx<x+w/2-2;xx+=9){districtDummy.position.set(xx,yy,z+d/2+.12);districtDummy.updateMatrix();districtWindows.setMatrixAt(districtCount++,districtDummy.matrix)}}districtWindows.count=districtCount;world.add(districtWindows);
  for(const [x,z,w,d] of [[-98,48,66,7],[96,38,75,7],[-84,-57,90,7],[78,-70,84,7],[0,105,120,6]])box(x,7,z,w,1.1,d,mats.dark,true);
  // Four recognizable facilities joined by a broad central concourse.
  for(const [x,z,w,d] of [[-50,17,2,92],[-18,50,66,2],[-18,-10,66,2],[50,15,2,94],[18,-12,66,2],[-52,-45,74,2],[52,-48,72,2]])wall(x,z,w,d,9);
  wall(-5,52,20,2,9);wall(34,52,34,2,9);
  for(let row=-2;row<=2;row++)for(let i=-4;i<=4;i++)lightPanel(i*20,23.4,row*31+8,7,1.4);
  for(const x of [-62,0,62]){const l=new THREE.PointLight(0xffe5aa,58,115,2);l.position.set(x,18,0);world.add(l)}
  const backdrop=corridorBackdrop();for(const [x,z,w,ry] of [[-5,53.05,17,0],[34,53.05,30,0]]){const p=mesh(new THREE.PlaneGeometry(w,20),backdrop,x,11,z,false);p.rotation.y=ry}
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
  box(0,-.4,0,400,.8,330,mats.carpet);addHorizon('assets/textures/distant-ruins.png',43,1.15);const road=new THREE.MeshStandardMaterial({color:0x596365,roughness:1,map:wallMap});box(0,.01,0,18,.08,310,road,false);box(0,.015,0,1,.09,300,mats.wall,false);
  // Secondary roads and sloping garden districts prevent the world reading as one central strip.
  for(const [x,z,w,d,r] of [[-78,64,145,13,-.18],[92,-32,165,12,.23],[-108,-102,92,11,.38],[116,105,108,10,-.3]]){const lane=box(x,.02,z,w,.09,d,road,false);lane.rotation.y=r}
  for(const [x,z,s,h] of [[-164,66,32,8],[-154,-34,55,13],[142,42,48,10],[112,-120,62,16],[-48,-132,44,7]]){const hill=mesh(new THREE.CylinderGeometry(s*.72,s,h,9),mats.carpet,x,h/2-.2,z);hill.rotation.y=(x+z)*.01;colliders.push({x,z,w:s*.72,d:s*.72,bottom:0,top:h})}
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
  // Distant neighborhoods use a handful of shared meshes and irregular placement.
  const neighborhoods=[[-128,78,34,18,22],[-158,15,24,31,18],[-126,-61,45,14,26],[132,72,40,25,18],[158,8,27,16,23],[136,-83,52,20,21],[-38,128,46,15,24],[55,-133,38,28,20]],neighborhoodWindows=new THREE.InstancedMesh(new THREE.BoxGeometry(3.2,2,.2),mats.solar,190),neighborhoodDummy=new THREE.Object3D();let neighborhoodCount=0;
  for(const [x,z,w,h,d] of neighborhoods){box(x,h/2,z,w,h,d,mats.wall,true);for(let yy=5;yy<h-2;yy+=5)for(let xx=x-w/2+4;xx<x+w/2-2;xx+=8){neighborhoodDummy.position.set(xx,yy,z+d/2+.12);neighborhoodDummy.updateMatrix();neighborhoodWindows.setMatrixAt(neighborhoodCount++,neighborhoodDummy.matrix)}}neighborhoodWindows.count=neighborhoodCount;world.add(neighborhoodWindows);
  const canals=[[-72,-15,12,120,.15],[86,52,10,135,-.22],[-12,-112,115,9,.08]];for(const [x,z,w,d,r] of canals){const c=box(x,-.08,z,w,.18,d,mats.water,false);c.rotation.y=r}
  // Trees as a small instanced grove.
  const trunks=new THREE.InstancedMesh(new THREE.CylinderGeometry(.25,.48,5,8),mats.wood,45),crowns=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(2.2,1),new THREE.MeshStandardMaterial({color:0x667a64,roughness:1}),45),dummy=new THREE.Object3D();
  for(let i=0;i<45;i++){const a=i*2.399,r=74+(i%5)*5,x=Math.cos(a)*r,z=Math.sin(a)*r;dummy.position.set(x,2.5,z);dummy.updateMatrix();trunks.setMatrixAt(i,dummy.matrix);dummy.position.y=6;dummy.scale.set(1+(i%3)*.15,.8+(i%2)*.2,1);dummy.updateMatrix();crowns.setMatrixAt(i,dummy.matrix)}trunks.castShadow=crowns.castShadow=true;world.add(trunks,crowns);
  // Solar roofs, planted balconies and elevated gardens establish the suburb's solarpunk identity.
  const panels=new THREE.InstancedMesh(new THREE.BoxGeometry(5,.16,2.7),mats.solar,30);let p=0;
  for(const [x,y,z] of [[-76,18.5,18],[-68,18.5,18],[-60,18.5,18],[-52,18.5,18],[-44,18.5,18],[-76,18.5,27],[-68,18.5,27],[-60,18.5,27],[-52,18.5,27],[-44,18.5,27]]){dummy.position.set(x,y,z);dummy.rotation.x=-.24;dummy.updateMatrix();panels.setMatrixAt(p++,dummy.matrix)}
  for(const z of [15,42])for(const x of [51,58,65,72]){dummy.position.set(x,24.5,z);dummy.rotation.x=-.24;dummy.updateMatrix();panels.setMatrixAt(p++,dummy.matrix)}panels.count=p;panels.castShadow=true;world.add(panels);
  const planters=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1.15,1),mats.leaf,48);let q=0;
  for(const z of [7.2,34.2])for(let r=0;r<4;r++)for(let c=0;c<5;c++){dummy.position.set(46+c*8,5+r*5,z);dummy.rotation.set(0,0,0);dummy.scale.set(1.5,.65,.72);dummy.updateMatrix();planters.setMatrixAt(q++,dummy.matrix)}planters.count=q;planters.castShadow=true;world.add(planters);
  for(const [x,z] of [[-18,-20],[25,-12],[74,-20]]){box(x,5,z,.9,10,.9,mats.wood);box(x,10,z,13,.45,13,mats.wood,true);const garden=mesh(new THREE.IcosahedronGeometry(5.4,2),mats.leaf,x,12,z);garden.scale.y=.42;for(let i=0;i<6;i++){const petal=box(x,15,z,5,.16,2.5,mats.solar,false);petal.rotation.y=i*Math.PI/3;petal.rotation.z=.18}}
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
let avatarMixer=null,avatarActions={},avatarState='',avatarModel=null;function setAvatarAction(name){if(name===avatarState||!avatarActions[name])return;const next=avatarActions[name],previous=avatarActions[avatarState];next.reset().fadeIn(.2).play();if(previous)previous.fadeOut(.2);avatarState=name}
function setCharacterStyle(name){applyTravelerDesign(THREE,player,avatarModel,name)}
const characterSelect=document.querySelector('#characterSelect');characterSelect.value=localStorage.getItem('aeolia-character')||'ember';setCharacterStyle(characterSelect.value);characterSelect.addEventListener('change',e=>{localStorage.setItem('aeolia-character',e.target.value);setCharacterStyle(e.target.value);if(started)renderer.domElement.focus()});
new GLTFLoader().load('assets/aeolia-traveler.glb',gltf=>{const model=gltf.scene;avatarModel=model;model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true}});player.add(model);setCharacterStyle(characterSelect.value);for(const o of [robe,head,hat,crown])o.visible=false;avatarMixer=new THREE.AnimationMixer(model);for(const clip of gltf.animations)avatarActions[clip.name]=avatarMixer.clipAction(clip);setAvatarAction('Idle')},undefined,error=>console.warn('Traveler model fallback in use',error));
const sound=new WorldAudio(undefined,stageKey==='parallax'?'complex':'suburb'),motionEffects=new MotionEffects(THREE,scene,camera);
const keys={},velocity=new THREE.Vector3(),lastSafe=player.position.clone(),targetCam=new THREE.Vector3(),cameraFocus=player.position.clone().add(new THREE.Vector3(0,2,0)),focusTarget=new THREE.Vector3();let yaw=0,pitch=.25,flying=true,flightBlend=1,started=false,dragging=false,previous=null,bob=0,nextAnomaly=performance.now()+360000+Math.random()*240000,recenterYaw=null,travelYaw=0;
function contains(c,x,z,margin=.55){return Math.abs(x-c.x)<c.w+margin&&Math.abs(z-c.z)<c.d+margin}
function validGround(x,z){return Math.abs(x)<(stageKey==='parallax'?172:196)&&Math.abs(z)<(stageKey==='parallax'?142:161)}
function resetKeys(){for(const k in keys)delete keys[k];velocity.set(0,0,0);dragging=false}
function saveNote(note){let notes=[];try{notes=JSON.parse(localStorage.getItem('aeolia-notes')||'[]')}catch{}const id=stageKey+':'+note[3];if(notes.some(n=>n.id===id))return false;notes.push({id,world:cfg.name,name:note[3],text:note[4]});localStorage.setItem('aeolia-notes',JSON.stringify(notes));return true}
let nextDiscover=0;
function discover(t){if(t<nextDiscover)return;nextDiscover=t+500;let nearest=cfg.notes[0],best=Infinity;for(const n of cfg.notes){const d=Math.hypot(player.position.x-n[0],player.position.z-n[2]);if(d<best){best=d;nearest=n}if(d<10&&saveNote(n)){sound.chime();showEvent(n[3])}}document.querySelector('#place').textContent=nearest[3]}
let eventTimer;function showEvent(text){const e=document.querySelector('#event');e.querySelector('div').textContent=text;e.classList.add('on');clearTimeout(eventTimer);eventTimer=setTimeout(()=>e.classList.remove('on'),2600)}
function anomaly(t){if(t<nextAnomaly)return;nextAnomaly=t+360000+Math.random()*300000;const candidates=[];world.traverse(o=>{if(o.userData.anomaly)candidates.push(o)});if(candidates.length){const o=candidates[Math.floor(Math.random()*candidates.length)];o.visible=!o.visible}scene.fog.density=cfg.fogDensity*1.8;setTimeout(()=>scene.fog.density=cfg.fogDensity,9000);showEvent(stageKey==='parallax'?'扉が現れた。':'チャイムが鳴った。')}
function updateCreatures(dt,t){for(const c of creatures){c.phase+=c.speed*dt;const flee=Math.max(0,12-player.position.distanceTo(c.g.position));c.phase+=flee*dt*.025;c.g.position.x=(c.cx||0)+Math.cos(c.phase)*c.radius;c.g.position.z=(c.cz||0)+Math.sin(c.phase)*c.radius;if(c.kind==='bird'){c.g.position.y=10+(c.radius-35)*.18+Math.sin(t*.002+c.phase)*2;c.g.rotation.y=-c.phase+Math.PI/2;c.g.children.forEach((w,i)=>w.rotation.z=(i?-1:1)*(.22+Math.sin(t*.008+c.phase)*.35))}else{c.g.position.y=Math.abs(Math.sin(t*.003+c.phase))*.12;c.g.rotation.y=-c.phase;c.g.rotation.z=Math.sin(t*.004+c.phase)*.025}}}
function update(dt,t){if(keys.KeyQ||keys.KeyE)recenterYaw=null;if(keys.KeyQ)yaw+=dt*1.2;if(keys.KeyE)yaw-=dt*1.2;if(recenterYaw!==null){const d=Math.atan2(Math.sin(recenterYaw-yaw),Math.cos(recenterYaw-yaw));yaw+=d*(1-Math.exp(-7*dt));pitch=THREE.MathUtils.damp(pitch,.25,7,dt);if(Math.abs(d)<.005)recenterYaw=null}const fwd=new THREE.Vector3(-Math.sin(yaw),0,-Math.cos(yaw)),right=new THREE.Vector3(Math.cos(yaw),0,-Math.sin(yaw)),input=new THREE.Vector3().addScaledVector(fwd,(keys.ArrowUp||keys.KeyW?1:0)-(keys.ArrowDown||keys.KeyS?1:0)).addScaledVector(right,(keys.ArrowRight||keys.KeyD?1:0)-(keys.ArrowLeft||keys.KeyA?1:0));if(input.lengthSq())input.normalize();const fast=keys.ControlLeft||keys.ControlRight,speed=flying?(fast?42:26):(fast?16:10);velocity.x=THREE.MathUtils.damp(velocity.x,input.x*speed,input.lengthSq()?5:15,dt);velocity.z=THREE.MathUtils.damp(velocity.z,input.z*speed,input.lengthSq()?5:15,dt);velocity.y=flying?THREE.MathUtils.damp(velocity.y,((keys.Space?1:0)-(keys.ShiftLeft||keys.ShiftRight?1:0))*16,6,dt):-12;
  const before=player.position.clone();for(const axis of ['x','z']){const old=player.position[axis];player.position[axis]+=velocity[axis]*dt;const blocked=colliders.some(c=>contains(c,player.position.x,player.position.z)&&player.position.y<c.top&&player.position.y+3.6>c.bottom);if(blocked||!validGround(player.position.x,player.position.z)){player.position[axis]=old;velocity[axis]=0}}
  player.position.y+=velocity.y*dt;if(player.position.y<0){player.position.y=0;velocity.y=0;lastSafe.copy(player.position)}if(player.position.y>cfg.limitY){player.position.y=cfg.limitY;velocity.y=Math.min(0,velocity.y)}if(player.position.y<-20)player.position.copy(lastSafe);
  const hs=Math.hypot(velocity.x,velocity.z);let turn=0;if(hs>.15){travelYaw=Math.atan2(-velocity.x,-velocity.z);const a=Math.atan2(velocity.x,velocity.z);turn=Math.atan2(Math.sin(a-player.rotation.y),Math.cos(a-player.rotation.y));player.rotation.y+=turn*(1-Math.exp(-7*dt))}bob+=hs*dt;robe.position.y=1.35+Math.abs(Math.sin(bob))*.045+Math.sin(t*.006)*.035;player.rotation.x=THREE.MathUtils.damp(player.rotation.x,hs*.007-velocity.y*.012,4,dt);player.rotation.z=THREE.MathUtils.damp(player.rotation.z,THREE.MathUtils.clamp(-turn*.22,-.3,.3),5,dt);if(avatarMixer){setAvatarAction('Fly');if(avatarActions.Fly)avatarActions.Fly.timeScale=.8+Math.min(1.2,velocity.length()/24);avatarMixer.update(dt)}
  flightBlend=THREE.MathUtils.damp(flightBlend,flying?1:0,3.5,dt);const dist=9+flightBlend*3,up=4.2+flightBlend*1.8;targetCam.set(player.position.x+Math.sin(yaw)*dist,player.position.y+up+Math.sin(pitch)*6,player.position.z+Math.cos(yaw)*dist);camera.position.lerp(targetCam,1-Math.exp(-5.5*dt));focusTarget.set(player.position.x,player.position.y+2,player.position.z);cameraFocus.lerp(focusTarget,1-Math.exp(-9*dt));camera.lookAt(cameraFocus);updateCreatures(dt,t);motionEffects.update(dt,player.position,velocity,flying,player.position.y<.15);sound.update(dt,velocity.length(),flying,player.position.y<.15,false);discover(t);anomaly(t)
}
function loop(t){const elapsed=previous===null?0:Math.min(.1,(t-previous)/1000);previous=t;if(started&&elapsed){const steps=Math.ceil(elapsed*120);for(let i=0;i<steps;i++)update(elapsed/steps,t)}renderer.render(scene,camera);if(location.search.includes('debug=1'))document.querySelector('#perf').value=`${renderer.info.render.calls} calls\n${renderer.info.render.triangles.toLocaleString()} triangles\n${player.position.x.toFixed(1)}, ${player.position.y.toFixed(1)}, ${player.position.z.toFixed(1)}`;requestAnimationFrame(loop)}
camera.position.set(cfg.spawn[0],7,cfg.spawn[2]+10);camera.lookAt(player.position);requestAnimationFrame(loop);
addEventListener('keydown',e=>{if(!started)return;if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(e.code))e.preventDefault();keys[e.code]=true;if(e.code==='KeyC'&&!e.repeat)recenterYaw=travelYaw});addEventListener('keyup',e=>keys[e.code]=false);addEventListener('blur',()=>{resetKeys();previous=null;sound.pause()});document.addEventListener('visibilitychange',()=>{if(document.hidden){resetKeys();previous=null;sound.pause()}else if(started)sound.start()});
renderer.domElement.addEventListener('pointerdown',e=>{if(started){dragging=true;renderer.domElement.setPointerCapture(e.pointerId);renderer.domElement.style.cursor='grabbing'}});addEventListener('pointerup',()=>{dragging=false;renderer.domElement.style.cursor='grab'});addEventListener('pointermove',e=>{if(dragging&&e.buttons){yaw-=e.movementX*.003;pitch=THREE.MathUtils.clamp(pitch+e.movementY*.002,-.5,1.1)}});renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());
document.querySelector('#enter').onclick=()=>{started=true;sound.start();motionEffects.flightBurst(player.position,true);renderer.domElement.focus();const v=document.querySelector('#veil');v.style.opacity=0;v.style.pointerEvents='none';setTimeout(()=>v.remove(),850)};addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});if(location.search.includes('debug=1'))document.querySelector('#perf').hidden=false;
