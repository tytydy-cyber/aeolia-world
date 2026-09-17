import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import * as Core from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';
import {WorldAudio} from '../outputs/audio.js';
import {MotionEffects} from '../outputs/effects.js';
import {applyTravelerDesign,updateTravelerTraces} from '../outputs/character-designs.js';

// Actual scene and movement code, actual Three.js geometry; only DOM/GPU are mocked.
const listeners=new Map(),elements=new Map();
const on=(name,fn)=>{if(!listeners.has(name))listeners.set(name,[]);listeners.get(name).push(fn)};
function element(tagName='DIV'){return {tagName,events:new Map(),style:{},classList:{add(){},remove(){}},addEventListener(type,fn){if(!this.events.has(type))this.events.set(type,[]);this.events.get(type).push(fn)},setAttribute(){},focus(){document.activeElement=this;dispatch('focusin',{target:this})},setPointerCapture(){},remove(){},querySelector(){return element()},getContext(){return {createRadialGradient(){return {addColorStop(){}}},createLinearGradient(){return {addColorStop(){}}},fillRect(){}}}}}
const document={body:{tagName:'BODY',prepend(){}},hidden:false,addEventListener:on,createElement:element,querySelector(s){if(!elements.has(s))elements.set(s,element(['#paceInput','#soundVolume','#effectsToggle'].includes(s)?'INPUT':s==='#characterSelect'?'SELECT':['#enter','#soundToggle'].includes(s)?'BUTTON':'DIV'));return elements.get(s)}};
class Renderer{constructor(){this.domElement=element('CANVAS');this.shadowMap={}}setPixelRatio(){}setSize(){}render(){}}
class TextureLoader{load(path){assert.ok(readFileSync(new URL('../outputs/'+path,import.meta.url)).length>100,'texture file exists');return new Core.Texture()}}
const houseAsset=await loadHouse();
let assetMeshes=0,assetTriangles=0;
houseAsset.scene.traverse(o=>{if(o.isMesh){assetMeshes++;assetTriangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3}});
assert.ok(assetMeshes<=15,'asset draw-call budget');assert.ok(assetTriangles<70000,'asset triangle budget');
console.log(`Blender asset: ${assetMeshes} material batches, ${assetTriangles} triangles`);
let assetCallback;
class Loader{load(url,callback){assert.ok(['assets/aeolia-house.glb','assets/aeolia-traveler.glb'].includes(url));if(url.endsWith('house.glb'))assetCallback=callback}}
const localStorage={data:new Map(),getItem(k){return this.data.get(k)||null},setItem(k,v){this.data.set(k,String(v))}};
const context=vm.createContext({THREE:{...Core,WebGLRenderer:Renderer,TextureLoader},GLTFLoader:Loader,WorldAudio,MotionEffects,applyTravelerDesign,updateTravelerTraces,document,localStorage,innerWidth:1280,innerHeight:800,devicePixelRatio:1,addEventListener:on,requestAnimationFrame(){},setTimeout(){},console:{...console,assert(condition,message){assert.ok(condition,message)}},performance});
const html=readFileSync(new URL('../outputs/aeolia.html',import.meta.url),'utf8');
const script=html.match(/<script type="module">([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'');
vm.runInContext(script,context);
assetCallback(houseAsset);
const run=s=>vm.runInContext(s,context);
assert.equal(run('perfEnabled'),false,'performance meter stays inactive without debug query');
function dispatch(type,values={}){const e={target:type.startsWith('pointer')?run('renderer.domElement'):document.activeElement||document.body,preventDefault(){this.prevented=true},...values};for(const fn of e.target.events?.get(type)||[])fn(e);for(const fn of listeners.get(type)||[])fn(e);return e}
function inputPace(value){const target=document.querySelector('#paceInput');target.value=value;dispatch('input',{target})}
function frames(n=60,hz=60){const steps=Math.ceil(120/hz);for(let i=0;i<n;i++)for(let j=0;j<steps;j++)run(`update(${1/hz/steps},${i*1000/hz})`)}
function reset(){document.activeElement=document.body;run('resetInput();player.position.set(0,3,40);yaw=0;pitch=.28;flying=false;started=true;pace=1;travelYaw=0;scene.updateMatrixWorld(true)')}

assert.equal(run('houses.length'),9);
assert.equal(run('scenicLayers.length'),2,'two parallax ruin layers');
assert.equal(run("sky.material.map.image===null"),true,'generated panorama is loaded through the texture pipeline');
assert.deepEqual(Array.from(run('player.position')), [-25,3,5], 'spawn starts in the open central plaza');
assert.deepEqual(Array.from(run('camera.position')), [-25,9,14], 'camera starts behind the new spawn');
assert.equal(run('houses.every(h=>h.model && h.fallback.every(o=>!o.visible))'),true,'Blender models replace all houses');
let textured=0;run('houses[0].model').traverse(o=>{if(o.isMesh&&o.material.userData.textureKind){textured++;assert.ok(o.material.map&&o.material.bumpMap);assert.ok(o.geometry.attributes.uv)}});assert.ok(textured>=8,'textures reach imported Blender materials');
for(const h of run('houses')){
  const bounds=new Core.Box3().setFromObject(h.model);
  assert.ok(Math.abs(bounds.min.y-h.y)<.01,'Blender house grounded');
  assert.ok(bounds.getSize(new Core.Vector3()).y>h.h,'roof is above walls');
}

assert.equal(run('paveCount<3000'),true);
assert.equal(run('groundAt(500,500)'),-Infinity);
assert.equal(run('groundAt(-30,-52)'),3);assert.equal(run('groundAt(30,52)'),-Infinity,'main island boundary is strongly asymmetric');
assert.equal(run('groundAt(112,-92)'),54);
for(const island of run('Object.values(ISLANDS)')){const scales=Array.from({length:360},(_,i)=>run(`minorIslandScale(${i}*Math.PI/180,${island.phase})`));assert.ok(Math.max(...scales)-Math.min(...scales)>.45,'satellite island outline is strongly asymmetric')}
assert.ok(run('Math.hypot(BRIDGES[0][2]+105,BRIDGES[0][3]+105)')>27,'tower bridge ends at the island rim');
assert.ok(run('ISLANDS.tower.r*minorIslandScale(Math.atan2(BRIDGES[0][3]-ISLANDS.tower.z,BRIDGES[0][2]-ISLANDS.tower.x),ISLANDS.tower.phase)-Math.hypot(BRIDGES[0][2]-ISLANDS.tower.x,BRIDGES[0][3]-ISLANDS.tower.z)')<1,'tower bridge overlaps the irregular rim only enough for safe walking');
assert.equal(run('treeBatches.length'),5,'all trees share five draw batches');assert.ok(run('treeParts.branch.length')>=150);assert.ok(run('treeParts.leaf0.length+treeParts.leaf1.length+treeParts.leaf2.length')>=350);
for(const m of run('scene.children').filter(m=>m.isMesh))assert.ok(Number.isFinite(m.position.y),'finite scene position');

reset();const yaw0=run('yaw');dispatch('pointermove',{movementX:300,movementY:100,buttons:0});assert.equal(run('yaw'),yaw0,'normal mouse movement must not rotate');
dispatch('pointerdown',{button:0,pointerId:1});dispatch('pointermove',{movementX:80,movementY:20,buttons:1});assert.notEqual(run('yaw'),yaw0,'left drag rotates');dispatch('pointerup');
const yawAfterLeft=run('yaw');dispatch('pointermove',{movementX:300,movementY:100,buttons:0});assert.equal(run('yaw'),yawAfterLeft,'release stops left-drag orbit');
dispatch('pointerdown',{button:2,pointerId:1});dispatch('pointermove',{movementX:100,movementY:10,buttons:2});assert.notEqual(run('yaw'),yaw0,'right drag rotates');dispatch('pointerup');
dispatch('pointerdown',{button:2,pointerId:1});dispatch('pointermove',{movementX:0,movementY:-1000,buttons:2});assert.equal(run('pitch'),-.55,'right drag looks upward within safe limit');dispatch('pointermove',{movementX:0,movementY:2000,buttons:2});assert.equal(run('pitch'),1.15,'right drag looks downward within safe limit');dispatch('pointerup');
const yaw1=run('yaw');dispatch('pointermove',{movementX:300,movementY:100,buttons:0});assert.equal(run('yaw'),yaw1,'release must stop orbit');
assert.ok(!script.includes('requestPointerLock'),'no mouse capture');

reset();assert.ok(dispatch('keydown',{code:'ArrowUp'}).prevented);frames();const distance=40-run('player.position.z');assert.ok(distance>7.5&&distance<9.5,'faster up-arrow travel');assert.equal(run('yaw'),0,'walking keeps viewing angle');
dispatch('keyup',{code:'ArrowUp'});const stopZ=run('player.position.z');frames();assert.ok(Math.abs(stopZ-run('player.position.z'))<.7,'braking drift under 70cm');
reset();dispatch('keydown',{code:'ArrowRight'});frames(30);assert.ok(run('player.position.x')>1);assert.equal(run('yaw'),0);
reset();dispatch('keydown',{code:'ArrowLeft'});frames(30);assert.ok(run('player.position.x')< -1);
reset();dispatch('keydown',{code:'ArrowDown'});frames(30);assert.ok(run('player.position.z')>41);

reset();dispatch('keydown',{code:'ArrowUp'});frames(10);dispatch('keydown',{code:'ArrowRight'});const angleBefore=run('player.rotation.y');frames(1);assert.ok(Math.abs(run('player.rotation.y')-angleBefore)<.3,'gradual turning');
reset();dispatch('keydown',{code:'KeyF',repeat:false});dispatch('keydown',{code:'KeyF',repeat:true});assert.equal(run('flying'),true);dispatch('keydown',{code:'Space'});frames(120);assert.ok(run('player.position.y')>20,'flight gains height');dispatch('keyup',{code:'Space'});dispatch('keydown',{code:'ShiftLeft'});frames(120);assert.ok(run('player.position.y')>=4,'flight does not penetrate ground');
reset();dispatch('keydown',{code:'KeyQ'});frames(30);assert.ok(run('yaw')>.5);dispatch('blur');assert.equal(run('Object.keys(keys).length'),0);assert.equal(run('velocity.length()'),0);
reset();run('yaw=1.4;pitch=1');dispatch('keydown',{code:'KeyC',repeat:false});frames(90);assert.ok(Math.abs(run('yaw'))<.01&&Math.abs(run('pitch')-.28)<.01,'C smoothly restores last travel-facing camera');
reset();run('yaw=1;keys.ArrowUp=true');frames(30);run('keys.ArrowUp=false;yaw=-1');dispatch('keydown',{code:'KeyC',repeat:false});frames(90);assert.ok(Math.abs(run('yaw')-1)<.01,'C remembers travel direction after stopping');

// Every bridge collision height is generated from the same profile as its deck.
for(const b of run('BRIDGES'))for(let i=0;i<=100;i++){const t=i/100,[ax,az,bx,bz,y1,y2]=b,x=ax+(bx-ax)*t,z=az+(bz-az)*t;const y=run(`groundAt(${x},${z})`);assert.ok(Math.abs(y-(y1+(y2-y1)*t+Math.sin(t*Math.PI)*2))<.001,'bridge height')}
assert.ok(run('bridgeRails.length')>20);assert.ok(run('bridgeRails.filter(r=>Math.abs(r.rotation.z)>.01).length')>20,'rails follow bridge slopes');
run("setCharacterStyle('mist')");assert.equal(run('cloth.color.getHex()'),0x527b83,'character design changes without another rig');

reset();run('player.position.set(28,3,39);keys.ArrowUp=true');frames(390);assert.ok(run('player.position.y')>17,'stairs reach upper terrace');
reset();run('player.position.set(-43,3,-23);keys.ArrowUp=true');frames(100);assert.ok(run('player.position.z')>=-26.35,'wall collision');

// Time-step behavior should agree at common refresh rates.
const positions=[];for(const hz of [30,60,120]){reset();dispatch('keydown',{code:'ArrowUp'});frames(hz,hz);positions.push(run('player.position.z'))}
assert.ok(Math.max(...positions)-Math.min(...positions)<.1,'frame-rate independence');
reset();inputPace('1.6');assert.equal(run('pace'),1.6);inputPace('bad');assert.equal(run('pace'),1);
reset();inputPace('1.6');run('player.position.set(-43,3,-23);keys.ArrowUp=true;keys.ControlLeft=true');frames(100,20);assert.ok(run('player.position.z')>=-26.35,'maximum speed cannot tunnel through wall');
console.log('PASS: actual GLB parse/9 house placements, all arrow keys, passive mouse, drag/release, acceleration/braking, flight, focus loss, bridges, stairs, walls, speed slider, maximum-speed collision, 30/60/120 Hz. GPU rendering is not tested.');
const counts=Object.fromEntries(['pot','crate','bench','stall'].map(kind=>[kind,run(`props.filter(p=>p.kind==='${kind}').length`)]));
assert.ok(run('props.length')>=40,'meaningful street furniture count');
assert.ok(run('propBatches.length')<=7,'batch draw-call budget');
for(const batch of run('propBatches')){assert.equal(batch.castShadow,false);assert.ok(Number.isFinite(batch.boundingSphere.radius))}
const triangles=run('propBatches.reduce((sum,m)=>sum+(m.geometry.index?.count??m.geometry.attributes.position.count)/3*m.count,0)');
assert.ok(triangles<25000,'additional triangle budget');
console.log('Added street furniture:',counts,'batches:',run('propBatches.length'),'triangles:',triangles);
export {run,dispatch,reset,frames,document};
