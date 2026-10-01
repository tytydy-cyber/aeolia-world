import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import * as THREE from './three.core.mjs';
import {applyTravelerDesign} from '../outputs/character-designs.js';

const js=readFileSync(new URL('../outputs/liminal.js',import.meta.url),'utf8');
const html=readFileSync(new URL('../outputs/liminal.html',import.meta.url),'utf8');
const aeolia=readFileSync(new URL('../outputs/aeolia.html',import.meta.url),'utf8');
const hub=readFileSync(new URL('../outputs/index.html',import.meta.url),'utf8');
const mobile=readFileSync(new URL('../outputs/mobile-controls.js',import.meta.url),'utf8');
const source=js.match(/const STAGES=(\{[\s\S]*?\n\});\nconst cfg=/)?.[1];
assert.ok(source,'stage configuration is readable');
const stages=vm.runInNewContext(`(${source})`);
assert.deepEqual(Object.keys(stages),['parallax','somnia']);
for(const [key,stage] of Object.entries(stages)){
  assert.equal(stage.notes.length,5,`${key} has five main discoveries`);
  assert.equal(new Set(stage.notes.map(n=>n[3])).size,5,`${key} discovery names are unique`);
  assert.ok(stage.limitY>15,'flight remains available');
}
for(const code of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyW','KeyA','KeyS','KeyD','KeyC','KeyQ','KeyE','ControlLeft'])assert.ok(js.includes(code),`${code} remains supported`);
assert.ok(js.includes("new MotionEffects")&&js.includes("new WorldAudio"),'existing effects and audio are shared');
assert.ok(js.includes('flightBlend=THREE.MathUtils.damp')&&js.includes('cameraFocus.lerp'),'camera transition and aim are smoothed');
assert.equal((js.match(/new THREE\.PointLight/g)||[]).length,1,'facility lights are created by one bounded loop');
assert.ok(hub.includes('aeolia.html')&&hub.includes('stage=parallax')&&hub.includes('stage=somnia'),'station exposes all worlds');
for(const page of [html,aeolia]){
  assert.ok(page.includes('世界選択へ')&&page.includes('id="characterSelect"'),'every world exposes world and character selection');
  assert.ok(page.includes('.return{position:fixed;z-index:12;left:28px;top:82px'),'world selector stays in the same desktop position');
  for(const label of ['>↑ ↓ ← →</b> 飛行','>SPACE</b> 上昇','>SHIFT</b> 下降'])assert.ok(page.includes(label),`PC control label ${label} is explicit`);
}
assert.ok(js.includes('SOLARPUNK SUBURB 03')&&js.includes('const panels=new THREE.InstancedMesh')&&js.includes('const planters=new THREE.InstancedMesh'),'suburb has instanced solarpunk landmarks');
assert.ok(js.includes('function roundedBlock')&&js.includes('new THREE.TubeGeometry')&&js.includes('Aerial commons'),'both new worlds use layered non-rectangular structures');
assert.ok(js.includes('recognizable threshold')&&js.includes('Overlapping meadow islands'),'playtest fixes preserve a readable entrance and varied near ground');
assert.ok(js.includes('nextAnomaly=Infinity')&&js.includes('started=true;nextAnomaly=Date.now()+60000+Math.random()*60000')&&js.includes('function anomaly(){const now=Date.now()'),'events are scheduled from entry, first within about two minutes, and cannot fire on entry');
assert.ok(js.includes('d<NOTE_RADIUS&&low&&saveNote(n)')&&js.includes('降りると記録')&&js.includes('recenterYaw=Math.atan2(player.position.x-n[0]'),'discoveries require descending and turn the camera toward the place');
assert.ok(js.includes('mats.glow.clone()')&&js.includes('i===nextGate')&&js.includes('気流を乗り継いだ'),'wind gates form an ordered chain with the next gate highlighted');
assert.ok(html.includes('id="soundToggle"')&&html.includes('id="soundVolume"')&&js.includes('sound.setMuted(!sound.muted)'),'liminal worlds expose mute and volume like the floating islands');
assert.ok(html.indexOf("const suburb=new URLSearchParams")<html.indexOf('type="importmap"')&&html.includes("replaceChildren(first.name)"),'stage copy is complete before the external 3D module loads');
assert.ok(js.includes('smoothstep(player.position.y,5,24)')&&js.includes('boostTarget=diving?Math.min(10')&&js.includes('cameraProbe.lerpVectors'),'liminal flight changes with altitude, preserves dive momentum and avoids camera colliders');
assert.ok(js.includes('function routeGate')&&js.includes('function updateRouteGates')&&js.includes('speed=THREE.MathUtils.lerp(fast?42:26,fast?52:36,altitude)+diveBoost+routeBoost'),'multi-height wind gates produce a temporary movement benefit');
assert.ok(js.includes('A water tower anchors the horizon')&&js.includes('The solar collector closes the long view'),'both worlds have reachable navigation landmarks');
assert.ok(js.includes('function mesh(g,m,x,y,z,shadow=false)'),'static architecture skips redundant shadow passes by default');
assert.ok(js.includes('const accentBatch=new THREE.InstancedMesh')&&js.includes('renderer.shadowMap.enabled=false'),'repeated solar accents are batched and generated-material worlds skip dynamic shadow passes');
assert.ok(js.includes('mergeGeometries')&&js.includes('groundCreatureBatch=new THREE.InstancedMesh')&&js.includes('birdBatch=new THREE.InstancedMesh'),'animated creatures keep their silhouettes in two draw batches');
assert.ok(js.includes('complex-surface-v2.jpg')&&js.includes('solarpunk-surface-v2.jpg')&&js.includes("structuralMap.repeat.set(stageKey==='parallax'?6:3")&&js.includes('frame:new THREE.MeshStandardMaterial'),'world-specific material atlases repeat across broad surfaces while frames keep stable UVs');
assert.ok(js.includes("[65,0,38,'受付'")&&js.includes('const bell=mesh(new THREE.SphereGeometry'),'the reception discovery points at a visible bell');
assert.ok(js.includes('Broken ceiling plates enclose the complex')&&js.includes('limitY:38'),'the closed complex keeps the player below its broken ceiling');
assert.ok(hub.includes(".parallax{--scene:url('assets/textures/complex-horizon-v1.png')}")&&hub.includes(".somnia{--scene:url('assets/textures/distant-ruins.png')}"),'world cards use their generated scenery instead of flat gradients');
assert.ok(js.includes("全地点を巡った")&&js.includes("best<90")&&js.includes("count} / ${cfg.notes.length}"),'exploration provides proximity and completion feedback');
assert.ok(js.includes("addHorizon('assets/textures/complex-horizon-v1.png'")&&js.includes("addHorizon('assets/textures/distant-ruins.png'"),'both worlds have layered distant scenery');
assert.ok(js.includes('irregularGround()')&&js.includes('roughCylinder(')&&js.includes('c.radius!==undefined'),'natural ground, hills and their colliders share non-rectangular shapes');
assert.ok(js.includes('new THREE.ShapeGeometry(shape)')&&js.includes('o.rotation.x=-Math.PI/2'),'irregular ground renders its textured front face upward');
assert.ok(js.includes('new THREE.CylinderGeometry(245*scale')&&js.includes('const silhouettes=new THREE.InstancedMesh'),'horizon art wraps around a real low-cost 3D foreground layer');
assert.ok(!js.includes('box(0,-.35,0,350')&&!js.includes('box(0,-.4,0,400'),'world floors are no longer giant rectangles');
assert.ok(js.includes('depthWrite:false,polygonOffset:true')&&js.includes('box(48,.045,-48,34,.035,22,mats.water)')&&js.includes('box(x,.055,z,w,.035,d,mats.water,false)'),'suburb water avoids coplanar depth artifacts');
assert.ok(js.includes('corner:Math.min(r,w/2,d/2)')&&js.includes('Math.hypot(qx,qz)<c.corner+margin'),'rounded buildings use rounded collision bounds');
const contains=(c,x,z,margin=.55)=>{const dx=Math.abs(x-c.x),dz=Math.abs(z-c.z),qx=Math.max(dx-(c.w-c.corner),0),qz=Math.max(dz-(c.d-c.corner),0);return dx<c.w+margin&&dz<c.d+margin&&Math.hypot(qx,qz)<c.corner+margin};
const rounded={x:0,z:0,w:10,d:8,corner:4};assert.equal(contains(rounded,10,8),false,'empty rounded corner stays passable');assert.equal(contains(rounded,10,0),true,'visible rounded side still blocks');
assert.ok(js.includes('const slide=box(-34,2.2,-45,10,.4,3,mats.pink,false)'),'rotated slide no longer leaves an unrotated invisible wall');
const edgeScale=(a,phase)=>.91+.075*Math.sin(a*3+phase)+.045*Math.sin(a*5-phase*.7)+.025*Math.sin(a*9+phase*.3),specs={parallax:[178,148,.4],somnia:[204,168,2.1]};
for(const [key,stage] of Object.entries(stages)){const [rx,rz,phase]=specs[key];for(const [x,,z,name] of [[...stage.spawn,'spawn'],...stage.notes]){const a=Math.atan2(z/rz,x/rx);assert.ok(Math.hypot(x/rx,z/rz)<edgeScale(a,phase)-.012,`${key} ${name} stays inside the irregular visible ground`)}}
for(const [key,[x,z]] of Object.entries({parallax:[-95,-105],somnia:[0,-126]})){const [rx,rz,phase]=specs[key],a=Math.atan2(z/rz,x/rx);assert.ok(Math.hypot(x/rx,z/rz)<edgeScale(a,phase)-.012,`${key} landmark stays inside playable ground`)}
for(const code of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','ShiftLeft'])assert.ok(mobile.includes(code),`mobile control exposes ${code}`);
assert.ok(!mobile.includes("button('KeyF'")&&!html.includes('飛行切替')&&!aeolia.includes('飛行切替'),'flight toggle is removed from every control surface');
assert.ok(mobile.includes('pointerdown')&&mobile.includes('pointercancel')&&mobile.includes('touch-action:none'),'mobile press-and-hold and swipe coexist safely');
const player=new THREE.Group(),model=new THREE.Group(),coat=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());coat.name='Sculpted coat';coat.material.name='Coat';const hat=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());hat.name='Hat brim';model.add(coat,hat);
applyTravelerDesign(THREE,player,model,'mist');assert.equal(hat.visible,false);assert.equal(player.userData.designVariants.mist.visible,true);assert.equal(player.userData.designVariants.lilac.visible,false);
applyTravelerDesign(THREE,player,model,'lilac');assert.equal(player.userData.designVariants.mist.visible,false);assert.equal(player.userData.designVariants.lilac.visible,true);assert.ok(player.userData.designVariants.lilac.children.length>=4,'lilac changes silhouette');
assert.equal(player.userData.designVariants.lilacHead.visible,true,'lilac headwear remains visible');
console.log('PASS: two independent worlds, 10 discoveries, station routes, shared movement/audio/effects controls.');
