import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import * as THREE from './three.core.mjs';
import {applyTravelerDesign} from '../outputs/character-designs.js';

const js=readFileSync(new URL('../outputs/liminal.js',import.meta.url),'utf8');
const html=readFileSync(new URL('../outputs/liminal.html',import.meta.url),'utf8');
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
for(const code of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyW','KeyA','KeyS','KeyD','KeyF','KeyC','KeyQ','KeyE','ControlLeft'])assert.ok(js.includes(code),`${code} remains supported`);
assert.ok(js.includes("new MotionEffects")&&js.includes("new WorldAudio"),'existing effects and audio are shared');
assert.ok(hub.includes('aeolia.html')&&hub.includes('stage=parallax')&&hub.includes('stage=somnia'),'station exposes all worlds');
assert.ok(html.includes('停留所へ戻る')&&html.includes('SPACE / SHIFT'),'worlds retain return and flight controls');
for(const code of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyF','Space','ShiftLeft'])assert.ok(mobile.includes(code),`mobile control exposes ${code}`);
assert.ok(mobile.includes('pointerdown')&&mobile.includes('pointercancel')&&mobile.includes('touch-action:none'),'mobile press-and-hold and swipe coexist safely');
const player=new THREE.Group(),model=new THREE.Group(),coat=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());coat.name='Sculpted coat';coat.material.name='Coat';const hat=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());hat.name='Hat brim';model.add(coat,hat);
applyTravelerDesign(THREE,player,model,'mist');assert.equal(hat.visible,false);assert.equal(player.userData.designVariants.mist.visible,true);assert.equal(player.userData.designVariants.lilac.visible,false);
applyTravelerDesign(THREE,player,model,'lilac');assert.equal(player.userData.designVariants.mist.visible,false);assert.equal(player.userData.designVariants.lilac.visible,true);assert.ok(player.userData.designVariants.lilac.children.length>=4,'lilac changes silhouette');
console.log('PASS: two independent worlds, 10 discoveries, station routes, shared movement/audio/effects controls.');
