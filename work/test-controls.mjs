import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import * as Core from './three.core.mjs';
import {loadHouse,mergeGeometries} from './asset-loader.mjs';
import {WorldAudio} from '../outputs/audio.js';
import {MotionEffects} from '../outputs/effects.js';
import {applyTravelerDesign} from '../outputs/character-designs.js';

// Actual scene and movement code, actual Three.js geometry; only DOM/GPU are mocked.
const listeners=new Map(),elements=new Map();
const on=(name,fn)=>{if(!listeners.has(name))listeners.set(name,[]);listeners.get(name).push(fn)};
function element(tagName='DIV'){return {tagName,events:new Map(),style:{},classList:{add(){},remove(){}},addEventListener(type,fn){if(!this.events.has(type))this.events.set(type,[]);this.events.get(type).push(fn)},setAttribute(){},focus(){document.activeElement=this;dispatch('focusin',{target:this})},setPointerCapture(){},remove(){},querySelector(){return element()},getContext(){return {createRadialGradient(){return {addColorStop(){}}},createLinearGradient(){return {addColorStop(){}}},fillRect(){}}}}}
const makeDocument=(store,listen)=>({body:{tagName:'BODY',prepend(){}},hidden:false,addEventListener:listen,createElement:element,querySelector(s){if(!store.has(s))store.set(s,element(['#paceInput','#soundVolume','#effectsToggle'].includes(s)?'INPUT':s==='#characterSelect'?'SELECT':['#enter','#soundToggle'].includes(s)?'BUTTON':'DIV'));return store.get(s)}});
const document=makeDocument(elements,on);
class Renderer{constructor(){this.domElement=element('CANVAS');this.shadowMap={}}setPixelRatio(){}setSize(){}render(){}}
class TextureLoader{load(path){assert.ok(readFileSync(new URL('../outputs/'+path.split('?')[0],import.meta.url)).length>100,'texture file exists');return new Core.Texture()}}
const houseAsset=await loadHouse();
let assetMeshes=0,assetTriangles=0;
houseAsset.scene.traverse(o=>{if(o.isMesh){assetMeshes++;assetTriangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3}});
assert.ok(assetMeshes<=15,'asset draw-call budget');assert.ok(assetTriangles<70000,'asset triangle budget');
console.log(`Blender asset: ${assetMeshes} material batches, ${assetTriangles} triangles`);
const lodAsset=await loadHouse('aeolia-house-lod.glb');
let lodMeshes=0,lodTriangles=0;
lodAsset.scene.traverse(o=>{if(o.isMesh){lodMeshes++;lodTriangles+=o.geometry.index.count/3}});
assert.ok(lodMeshes<=4&&lodTriangles<=5000,`LOD house budget (${lodMeshes} batches, ${lodTriangles} triangles)`);
const districtAsset=await loadHouse('aeolia-island-modules.glb');
assert.deepEqual(districtAsset.scene.children.map(o=>o.name),['Market_module','Bell_tower_module','Windmill_module','Water_garden_module','Cloud_stop_module'],'five district modules exist in the shipped GLB');
const assetCallbacks={};
class Loader{load(url,callback){assert.ok(['assets/aeolia-house.glb','assets/aeolia-house-lod.glb','assets/aeolia-traveler.glb','assets/aeolia-island-modules.glb'].includes(url));assetCallbacks[url]=callback}}
const localStorage={data:new Map(),getItem(k){return this.data.get(k)||null},setItem(k,v){this.data.set(k,String(v))}};
const gameContext=(overrides={})=>vm.createContext({THREE:{...Core,WebGLRenderer:Renderer,TextureLoader},GLTFLoader:Loader,mergeGeometries,houseAsset,lodAsset,WorldAudio,MotionEffects,applyTravelerDesign,document,localStorage,innerWidth:1280,innerHeight:800,devicePixelRatio:1,matchMedia(){return {matches:false}},addEventListener:on,requestAnimationFrame(){},setTimeout(){},console:{...console,assert(condition,message){assert.ok(condition,message)}},performance,...overrides});
const context=gameContext();
const html=readFileSync(new URL('../outputs/aeolia.html',import.meta.url),'utf8');
const script=html.match(/<script type="module">([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'');
vm.runInContext(script,context);
assetCallbacks['assets/aeolia-house.glb'](houseAsset);assetCallbacks['assets/aeolia-house-lod.glb'](lodAsset);await new Promise(resolve=>setImmediate(resolve));
assetCallbacks['assets/aeolia-island-modules.glb'](districtAsset);await new Promise(resolve=>setImmediate(resolve));
const run=s=>vm.runInContext(s,context);
// A failed house download keeps the procedural fallback houses and tells the player.
{
  const failedElements=new Map(),failed=gameContext({document:makeDocument(failedElements,()=>{}),addEventListener(){},GLTFLoader:class{load(url,callback,progress,onError){if(url.includes('house'))onError(new Error('offline'))}},console:{...console,error(){},assert(condition,message){assert.ok(condition,message)}}});
  vm.runInContext(script,failed);await new Promise(resolve=>setImmediate(resolve));
  assert.ok(vm.runInContext('houseBatches.length===0&&houses.every(h=>h.fallback.length&&h.fallback.every(o=>o.visible))',failed),'fallback houses stay visible when assets fail');
  assert.ok(failedElements.get('#assetState').textContent.includes('読み込めませんでした'),'asset failure is reported');
}
assert.equal(run('perfEnabled'),false,'performance meter stays inactive without debug query');
function dispatch(type,values={}){const e={target:type.startsWith('pointer')?run('renderer.domElement'):document.activeElement||document.body,preventDefault(){this.prevented=true},...values};for(const fn of e.target.events?.get(type)||[])fn(e);for(const fn of listeners.get(type)||[])fn(e);return e}
function inputPace(value){const target=document.querySelector('#paceInput');target.value=value;dispatch('input',{target})}
function frames(n=60,hz=60){const steps=Math.ceil(120/hz);for(let i=0;i<n;i++)for(let j=0;j<steps;j++)run(`update(${1/hz/steps},${i*1000/hz})`)}
function reset(){document.activeElement=document.body;run('resetInput();player.position.set(0,3,40);yaw=0;pitch=.28;flying=true;started=true;pace=1;travelYaw=0;scene.updateMatrixWorld(true)')}

assert.equal(run('houses.length'),9);
assert.equal(run('districtModules.length'),5,'all five district modules are placed');
assert.ok(run('districtBatches.length')<=4,'five districts merge into at most four material batches');
assert.equal(run('discoveries.length'),7,'the circuit covers the central island, three outer islands and cloud layer');
assert.ok(run('districtPlacements.every(([,x,y,z])=>y-groundAt(x,z)>=.08-1e-9)'),'district modules sit above their ground instead of sharing a coplanar layer');
assert.ok(run('districtPlacements.filter(p=>p[4]).every(([,x,,z,c])=>!propColliders.some(p=>Math.abs(x-p.x)<c.w+p.w&&Math.abs(z-p.z)<c.d+p.d))'),'district modules do not overlap existing street furniture');
assert.ok(run('districtModules.every(object=>{const box=new THREE.Box3().setFromObject(object);return box.min.y-groundAt(object.position.x,object.position.z)>=.079})'),'district geometry stays physically above the terrain layer');
assert.equal(run('scenicLayers.length'),2,'two parallax ruin layers');
assert.equal(run("sky.material.map.image===null"),true,'generated panorama is loaded through the texture pipeline');
assert.deepEqual(Array.from(run('player.position')), [-25,3,5], 'spawn starts in the open central plaza');
assert.deepEqual(Array.from(run('camera.position')), [-25,9,14], 'camera starts behind the new spawn');
const houseTriangles=()=>run('houseBatches.reduce((sum,b)=>sum+b.geometry.index.count/3,0)');
assert.ok(run('houseBatches.length')<=8,`desktop house batches (${run('houseBatches.length')})`);
const desktopHouseTriangles=houseTriangles();assert.ok(desktopHouseTriangles<=115000,`desktop house triangles (${desktopHouseTriangles})`);
assert.ok(desktopHouseTriangles>2*assetTriangles,'two houses keep full detail on desktop');
assert.equal(run('houses.every(h=>h.fallback.every(o=>!o.visible))'),true,'batched Blender models replace all fallback houses');
let textured=0;for(const batch of run('houseBatches'))if(batch.material.userData.textureKind){textured++;assert.ok(batch.material.map&&batch.material.bumpMap);assert.ok(batch.geometry.attributes.uv)}assert.equal(textured,4,'plaster, stone, slate and wood each reach one textured batch');
assert.ok(run('houseBatches.every(b=>b.material.vertexColors&&b.geometry.attributes.color)'),'merged batches carry roof tint and LOD shading as vertex color');
run('houseBatches.forEach(b=>scene.remove(b));houseBatches.length=0;placeHouses(null,houseParts(lodAsset))');
const phoneHouseTriangles=houseTriangles();assert.ok(run('houseBatches.length')<=4&&phoneHouseTriangles<=45000,`phone uses LOD only (${run('houseBatches.length')} batches, ${phoneHouseTriangles} triangles)`);
run('houseBatches.forEach(b=>scene.remove(b));houseBatches.length=0;placeHouses(houseParts(houseAsset),houseParts(lodAsset))');
console.log(`House rendering: desktop ${desktopHouseTriangles} triangles, phone ${phoneHouseTriangles} triangles`);
assert.ok(run('houseBatches.every(batch=>!batch.castShadow&&batch.receiveShadow)'),'houses receive nearby shadows without a second full geometry pass');
assert.equal(run('cloudBatch.count'),160,'all distant clouds share one draw batch');

assert.equal(run('paveCount<3000'),true);
assert.equal(run('groundAt(500,500)'),-Infinity);
assert.equal(run('groundAt(-30,-52)'),3);assert.equal(run('groundAt(30,52)'),-Infinity,'main island boundary is strongly asymmetric');
assert.equal(run('groundAt(112,-92)'),54);
for(const island of run('Object.values(ISLANDS)')){const scales=Array.from({length:360},(_,i)=>run(`minorIslandScale(${i}*Math.PI/180,${island.phase})`));assert.ok(Math.max(...scales)-Math.min(...scales)>.45,'satellite island outline is strongly asymmetric')}
assert.ok(run('Math.hypot(BRIDGES[0][2]+105,BRIDGES[0][3]+105)')>27,'tower bridge ends at the island rim');
assert.ok(run('ISLANDS.tower.r*minorIslandScale(Math.atan2(BRIDGES[0][3]-ISLANDS.tower.z,BRIDGES[0][2]-ISLANDS.tower.x),ISLANDS.tower.phase)-Math.hypot(BRIDGES[0][2]-ISLANDS.tower.x,BRIDGES[0][3]-ISLANDS.tower.z)')<1,'tower bridge overlaps the irregular rim only enough for safe walking');
assert.equal(run('treeBatches.length'),5,'all trees share five draw batches');assert.ok(run('treeParts.branch.length')>=150);assert.ok(run('treeParts.leaf0.length+treeParts.leaf1.length+treeParts.leaf2.length')>=300);assert.ok(run('treeBatches.every(b=>!b.castShadow&&b.receiveShadow)'),'trees keep lighting without a duplicate shadow pass');
for(const m of run('scene.children').filter(m=>m.isMesh))assert.ok(Number.isFinite(m.position.y),'finite scene position');

reset();const yaw0=run('yaw');dispatch('pointermove',{movementX:300,movementY:100,buttons:0});assert.equal(run('yaw'),yaw0,'normal mouse movement must not rotate');
dispatch('pointerdown',{button:0,pointerId:1});dispatch('pointermove',{movementX:80,movementY:20,buttons:1});assert.notEqual(run('yaw'),yaw0,'left drag rotates');dispatch('pointerup');
const yawAfterLeft=run('yaw');dispatch('pointermove',{movementX:300,movementY:100,buttons:0});assert.equal(run('yaw'),yawAfterLeft,'release stops left-drag orbit');
dispatch('pointerdown',{button:2,pointerId:1});dispatch('pointermove',{movementX:100,movementY:10,buttons:2});assert.notEqual(run('yaw'),yaw0,'right drag rotates');dispatch('pointerup');
dispatch('pointerdown',{button:2,pointerId:1});dispatch('pointermove',{movementX:0,movementY:-1000,buttons:2});assert.equal(run('pitch'),-.55,'right drag looks upward within safe limit');dispatch('pointermove',{movementX:0,movementY:2000,buttons:2});assert.equal(run('pitch'),1.15,'right drag looks downward within safe limit');dispatch('pointerup');
const yaw1=run('yaw');dispatch('pointermove',{movementX:300,movementY:100,buttons:0});assert.equal(run('yaw'),yaw1,'release must stop orbit');
assert.ok(!script.includes('requestPointerLock'),'no mouse capture');

reset();assert.ok(dispatch('keydown',{code:'ArrowUp'}).prevented);frames();const distance=40-run('player.position.z');assert.ok(distance>18&&distance<30,`up-arrow flies forward until terrain rises (${distance})`);assert.equal(run('yaw'),0,'flight keeps viewing angle');
dispatch('keyup',{code:'ArrowUp'});const stopZ=run('player.position.z');frames();assert.ok(Math.abs(stopZ-run('player.position.z'))<1.7,'flight braking drift stays bounded');
reset();dispatch('keydown',{code:'ArrowRight'});frames(30);assert.ok(run('player.position.x')>1);assert.equal(run('yaw'),0);
reset();dispatch('keydown',{code:'ArrowLeft'});frames(30);assert.ok(run('player.position.x')< -1);
reset();dispatch('keydown',{code:'ArrowDown'});frames(30);assert.ok(run('player.position.z')>41);

reset();dispatch('keydown',{code:'ArrowUp'});frames(10);dispatch('keydown',{code:'ArrowRight'});const angleBefore=run('player.rotation.y');frames(1);assert.ok(Math.abs(run('player.rotation.y')-angleBefore)<.3,'gradual turning');
reset();assert.equal(run('flying'),true,'flight is always active');dispatch('keydown',{code:'KeyF',repeat:false});assert.equal(run('flying'),true,'F no longer disables flight');dispatch('keydown',{code:'Space'});frames(120);assert.ok(run('player.position.y')>20,'flight gains height');dispatch('keyup',{code:'Space'});dispatch('keydown',{code:'ShiftLeft'});frames(120);assert.ok(run('player.position.y')>=4,'flight does not penetrate ground');
reset();dispatch('keydown',{code:'KeyQ'});frames(30);assert.ok(run('yaw')>.5);dispatch('blur');assert.equal(run('Object.keys(keys).length'),0);assert.equal(run('velocity.length()'),0);
reset();run('yaw=1.4;pitch=1');dispatch('keydown',{code:'KeyC',repeat:false});frames(90);assert.ok(Math.abs(run('yaw'))<.01&&Math.abs(run('pitch')-.28)<.01,'C smoothly restores last travel-facing camera');
reset();run('player.position.y=30;yaw=1;keys.ArrowUp=true');frames(30);run('keys.ArrowUp=false;yaw=-1');dispatch('keydown',{code:'KeyC',repeat:false});frames(90);assert.ok(Math.abs(run('yaw')-1)<.01,'C remembers travel direction after stopping');

reset();run('player.position.y=4;keys.ArrowRight=true');frames(120);const lowCruise=run('Math.hypot(velocity.x,velocity.z)');
reset();run('player.position.y=30;keys.ArrowRight=true');frames(120);const highCruise=run('Math.hypot(velocity.x,velocity.z)');assert.ok(highCruise>lowCruise+7,'high flight cruises faster than low flight');
reset();run('player.position.y=70;keys.ArrowUp=true;keys.ShiftLeft=true');frames(90);const dive=run('[diveBoost,Math.hypot(velocity.x,velocity.z)]');assert.ok(dive[0]>5&&dive[1]>40,`descent converts into forward glide speed (${dive})`);

// Every bridge collision height is generated from the same profile as its deck.
for(const b of run('BRIDGES'))for(let i=0;i<=100;i++){const t=i/100,[ax,az,bx,bz,y1,y2]=b,x=ax+(bx-ax)*t,z=az+(bz-az)*t;const y=run(`groundAt(${x},${z})`);assert.ok(Math.abs(y-(y1+(y2-y1)*t+Math.sin(t*Math.PI)*2))<.001,'bridge height')}
assert.ok(run('bridgeRails.length')>20);assert.ok(run('bridgeRails.filter(r=>Math.abs(r.rotation.z)>.01).length')>20,'rails follow bridge slopes');
assert.equal(run('bridgeBatch.count'),run('bridgeParts.length'),'all bridge pieces share one draw batch');assert.equal(run('stairBatch.count'),50,'all stairs share one draw batch');
run("setCharacterStyle('mist')");assert.equal(run('cloth.color.getHex()'),0x527b83,'character design changes without another rig');

reset();run('player.position.set(28,3,39);keys.ArrowUp=true');frames(390);assert.ok(run('player.position.y')>17,'stairs reach upper terrace');
reset();run('player.position.set(-43,3,-23);keys.ArrowUp=true');frames(100);assert.ok(run('player.position.z')>=-26.35,'wall collision');
reset();run('player.position.set(0,-30,80);keys.ArrowUp=true');frames(120);assert.ok(run('player.position.z')<55,'island underside uses its tapered rock shape instead of the top footprint');
reset();run('player.position.set(0,20,715);keys.ArrowDown=true;keys.ControlLeft=true');frames(120);assert.ok(run('Math.hypot(player.position.x,player.position.z)')<=720.01,'world boundary stays inside the sky sphere');
reset();run('player.position.set(112,60,-92);update(.016,0);player.position.y=-86;update(.016,16)');assert.ok(run('Math.hypot(player.position.x-112,player.position.z+92)<1&&player.position.y===55'),'cloud fall returns to the most recent island');

// Time-step behavior should agree at common refresh rates.
const positions=[];for(const hz of [30,60,120]){reset();dispatch('keydown',{code:'ArrowUp'});frames(hz,hz);positions.push(run('player.position.z'))}
assert.ok(Math.max(...positions)-Math.min(...positions)<.1,'frame-rate independence');
reset();inputPace('1.6');assert.equal(run('pace'),1.6);inputPace('bad');assert.equal(run('pace'),1);
reset();inputPace('1.6');run('player.position.set(-43,3,-23);keys.ArrowUp=true;keys.ControlLeft=true');frames(100,20);assert.ok(run('player.position.z')>=-26.35,'maximum speed cannot tunnel through wall');
localStorage.data.clear();reset();run('player.position.set(-105,80,-116)');run('discover()');assert.equal(localStorage.getItem('aeolia-notes'),null,'flying high over a landmark does not record it');assert.ok(document.querySelector('#place').textContent.includes('降りると記録'),'high pass hints that descending records the place');
run('player.position.set(-105,34,-116)');run('discover()');run('discover()');const saved=JSON.parse(localStorage.getItem('aeolia-notes'));assert.deepEqual(saved.map(n=>n.id),['aeolia:鐘楼'],'floating-island discoveries persist once to the shared journal');assert.ok(saved[0].world&&saved[0].text,'journal entries carry world and description');
frames(90);assert.ok(run('Math.hypot(-Math.sin(yaw)-0,-Math.cos(yaw)-1)')<.05,'camera turns toward the discovered landmark');assert.ok(document.querySelector('#place').textContent.includes('記録済'),'recorded places are marked');
// Colonnade, ring beam and windmill blades block at cruise and boost speed and at 30/60/120 Hz.
function sweep(start,direction,boost,hz,seconds=2){reset();run(`player.position.set(${start});yaw=Math.atan2(-(${direction[0]}),-(${direction[1]}));keys.ArrowUp=true;keys.ControlLeft=${boost}`);const steps=Math.ceil(120/hz),path=[];for(let i=0;i<hz*seconds;i++){for(let j=0;j<steps;j++)run(`update(${1/hz/steps},${i*1000/hz})`);path.push(run('player.position.toArray()'))}run('keys.ArrowUp=false;keys.ControlLeft=false');return path}
const ringDirection=[Math.cos(Math.PI/10),Math.sin(Math.PI/10)];
for(const hz of [30,60,120])for(const boost of [false,true]){
  const label=`${hz} Hz${boost?' with boost':''}`;
  assert.ok(sweep('88,8,85',[0,1],boost,hz).every(([x,,z])=>Math.hypot(x-88,z-100)>=.76+.58-.01),`colonnade column blocks at ${label}`);
  assert.ok(sweep('78,13,100',ringDirection,boost,hz).every(([x,,z])=>Math.hypot(x-78,z-100)<10),`colonnade ring beam blocks at ${label}`);
  assert.ok(sweep('125,77,-60',[0,-1],boost,hz).every(([,,z])=>z>=-84.2+.35+.58-.01),`windmill blades block at ${label}`);
}
sweep('125,77,-60',[0,-1],true,60);const bladeContact=run('player.position.toArray()');
run('keys.ArrowDown=true');frames(60);run('keys.ArrowDown=false');assert.ok(run('player.position.z')>bladeContact[2]+5,'player can back away after touching the blades');
sweep('125,77,-60',[0,-1],false,60);run('keys.Space=true');frames(60);run('keys.Space=false');assert.ok(run('player.position.y')>77+5,'player can climb along the blade disc without sticking');
// Distant islands: unreachable scenery in two draws, hazier once the player flies out.
assert.equal(run('distantIslands.length'),2,'twelve distant islands draw as two merged meshes');
assert.ok(run('distantIslands.every(m=>!cameraBlockers.includes(m))&&!solidColliders.some(c=>Math.hypot(c.x,c.z)>200)&&groundAt(330,0)===-Infinity'),'distant islands stay without ground, collision or camera blocking');
assert.ok(run('!distantMaterials[1].map&&!distantMaterials[1].color.equals(MAT.grass.color)'),'distant island tops do not reuse the reachable grass surface');
reset();run('player.position.set(0,20,0)');frames(1);const nearHaze=run('distantMaterials.map(m=>m.opacity)');
reset();run('player.position.set(0,20,330)');frames(1);const farHaze=run('distantMaterials.map(m=>m.opacity)');
assert.ok(nearHaze.every(o=>o===1)&&farHaze.every(o=>o<.5),`distant islands fade beyond 220 m (${nearHaze} -> ${farHaze})`);
// The camera stays out of the tapered rock when the player flies beneath an island.
// 0.3 m tolerance: the analytic rock shape differs from the faceted, rippled mesh the camera ray actually hits.
for(const [y,z] of [[-20,44],[-30,32],[-40,22]]){reset();run(`player.position.set(0,${y},${z});yaw=Math.PI;pitch=.28`);frames(90);assert.ok(!run('islandRockContains(camera.position.x,camera.position.z,camera.position.y,-.3)'),`camera stays outside the rock below the cliff (${y}, ${z})`)}
// The Blender traveler leans toward its direction of travel, whichever way it heads.
assetCallbacks['assets/aeolia-traveler.glb']({scene:new Core.Group(),animations:['Idle','Walk','Fly'].map(name=>new Core.AnimationClip(name,1,[]))});
for(const [key,direction] of [['ArrowRight',[1,0,0]],['ArrowUp',[0,0,-1]],['ArrowLeft',[-1,0,0]]]){
  reset();run(`player.position.set(0,20,0);keys.${key}=true`);frames(90);run(`keys.${key}=false`);
  const up=run('new THREE.Vector3(0,1,0).applyQuaternion(avatarModel.getWorldQuaternion(new THREE.Quaternion())).toArray()');
  assert.ok(up[0]*direction[0]+up[2]*direction[2]>.1&&Math.abs(up[0]*direction[2]-up[2]*direction[0])<.1,`traveler leans forward, not sideways, when moving ${key} (${up.map(v=>v.toFixed(2))})`);
}
console.log('PASS: actual GLB parse/9 house placements, all arrow keys, passive mouse, drag/release, acceleration/braking, flight, focus loss, bridges, stairs, walls, speed slider, maximum-speed collision, 30/60/120 Hz, colonnade/blade collision, distant haze, under-island camera, discovery journal. GPU rendering is not tested.');
const counts=Object.fromEntries(['pot','crate','bench','stall'].map(kind=>[kind,run(`props.filter(p=>p.kind==='${kind}').length`)]));
assert.ok(run('props.length')>=40,'meaningful street furniture count');
assert.ok(run('propBatches.length')<=7,'batch draw-call budget');
for(const batch of run('propBatches')){assert.equal(batch.castShadow,false);assert.ok(Number.isFinite(batch.boundingSphere.radius))}
const triangles=run('propBatches.reduce((sum,m)=>sum+(m.geometry.index?.count??m.geometry.attributes.position.count)/3*m.count,0)');
assert.ok(triangles<25000,'additional triangle budget');
console.log('Added street furniture:',counts,'batches:',run('propBatches.length'),'triangles:',triangles);
export {run,dispatch,reset,frames,document};
