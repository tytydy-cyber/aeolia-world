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
assert.ok(js.includes("addHorizon('assets/textures/complex-horizon-v1.png'")&&js.includes("addHorizon('assets/textures/distant-ruins.png'"),'both worlds have layered distant scenery');
assert.ok(js.includes('irregularGround()')&&js.includes('roughCylinder(')&&js.includes('c.radius!==undefined'),'natural ground, hills and their colliders share non-rectangular shapes');
assert.ok(js.includes('new THREE.ShapeGeometry(shape)')&&js.includes('o.rotation.x=-Math.PI/2'),'irregular ground renders its textured front face upward');
assert.ok(js.includes('new THREE.CylinderGeometry(245*scale')&&js.includes('const silhouettes=new THREE.InstancedMesh'),'horizon art wraps around a real low-cost 3D foreground layer');
assert.ok(!js.includes('box(0,-.35,0,350')&&!js.includes('box(0,-.4,0,400'),'world floors are no longer giant rectangles');
const edgeScale=(a,phase)=>.91+.075*Math.sin(a*3+phase)+.045*Math.sin(a*5-phase*.7)+.025*Math.sin(a*9+phase*.3),specs={parallax:[178,148,.4],somnia:[204,168,2.1]};
for(const [key,stage] of Object.entries(stages)){const [rx,rz,phase]=specs[key];for(const [x,,z,name] of [[...stage.spawn,'spawn'],...stage.notes]){const a=Math.atan2(z/rz,x/rx);assert.ok(Math.hypot(x/rx,z/rz)<edgeScale(a,phase)-.012,`${key} ${name} stays inside the irregular visible ground`)}}
for(const code of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','ShiftLeft'])assert.ok(mobile.includes(code),`mobile control exposes ${code}`);
assert.ok(!mobile.includes("button('KeyF'")&&!html.includes('飛行切替')&&!aeolia.includes('飛行切替'),'flight toggle is removed from every control surface');
assert.ok(mobile.includes('pointerdown')&&mobile.includes('pointercancel')&&mobile.includes('touch-action:none'),'mobile press-and-hold and swipe coexist safely');
const player=new THREE.Group(),model=new THREE.Group(),coat=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());coat.name='Sculpted coat';coat.material.name='Coat';const hat=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());hat.name='Hat brim';model.add(coat,hat);
applyTravelerDesign(THREE,player,model,'mist');assert.equal(hat.visible,false);assert.equal(player.userData.designVariants.mist.visible,true);assert.equal(player.userData.designVariants.lilac.visible,false);
applyTravelerDesign(THREE,player,model,'lilac');assert.equal(player.userData.designVariants.mist.visible,false);assert.equal(player.userData.designVariants.lilac.visible,true);assert.ok(player.userData.designVariants.lilac.children.length>=4,'lilac changes silhouette');
assert.equal(player.userData.designVariants.lilacHead.visible,true,'lilac headwear remains visible');
console.log('PASS: two independent worlds, 10 discoveries, station routes, shared movement/audio/effects controls.');
