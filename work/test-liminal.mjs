import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const js=readFileSync(new URL('../outputs/liminal.js',import.meta.url),'utf8');
const html=readFileSync(new URL('../outputs/liminal.html',import.meta.url),'utf8');
const hub=readFileSync(new URL('../outputs/index.html',import.meta.url),'utf8');
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
console.log('PASS: two independent worlds, 10 discoveries, station routes, shared movement/audio/effects controls.');
