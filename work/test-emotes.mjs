import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {run,dispatch,reset,frames} from './test-controls.mjs';
import {loadStage} from './liminal-harness.mjs';
import * as THREE from './three.core.mjs';

// The traveler asset carries the three emote clips next to the locomotion loops.
const glb=readFileSync(new URL('../outputs/assets/aeolia-traveler.glb',import.meta.url)),json=JSON.parse(glb.subarray(20,20+glb.readUInt32LE(12)).toString());
const clipNames=json.animations.map(a=>a.name).sort();
assert.deepEqual(clipNames,['Bow','Fly','Idle','Spin','Walk','Wave'],'traveler GLB has locomotion and emote clips');
const mobile=readFileSync(new URL('../outputs/mobile-controls.js',import.meta.url),'utf8');
for(const code of ['Digit1','Digit2','Digit3'])assert.ok(mobile.includes(`button('${code}'`),`phone controls expose ${code}`);
// Stages listen for camera drags on window, so a finger on a phone button must not reach them.
assert.ok(mobile.includes("addEventListener('pointermove',e=>e.stopPropagation())")&&mobile.includes('const up=e=>{e.stopPropagation()'),'a held phone button neither turns the camera nor ends another finger\'s drag');

// Floating islands: give the test traveler clips with the real durations.
const durations=Object.fromEntries(json.animations.map(a=>[a.name,Math.max(...a.samplers.map(s=>json.accessors[s.input].max[0]))]));
run(`(()=>{const clips=${JSON.stringify(durations)};avatarMixer=new THREE.AnimationMixer(avatarModel);avatarActions={};for(const [name,duration] of Object.entries(clips))avatarActions[name]=avatarMixer.clipAction(new THREE.AnimationClip(name,duration,[]));emotes.active=null;emotes.attach(avatarMixer,avatarActions);avatarState='';setAvatarAction('Fly')})()`);

reset();dispatch('keydown',{code:'Digit1',repeat:false});
assert.equal(run('emotes.active'),'Wave','key 1 waves');assert.equal(run('avatarState'),'Wave');
dispatch('keydown',{code:'Digit2',repeat:false});assert.equal(run('emotes.active'),'Wave','a second emote waits for the first to finish');
frames(150);
assert.equal(run('emotes.active'),null,'the wave finishes');assert.equal(run('avatarState'),'Fly','flight resumes after the emote');

reset();frames(13*30,30);
assert.equal(run('emotes.active'),'Wave','idling for a while waves');
frames(90);assert.equal(run('emotes.active'),null);
reset();run('keys.ArrowUp=true');frames(13*30,30);run('keys.ArrowUp=false');
assert.equal(run('emotes.active'),null,'flying around never triggers the idle wave');

reset();run("player.position.set(-30,4,-28);emotes.active=null;discover()");
assert.equal(run('emotes.active'),'Bow','a new discovery bows');
// Facility and suburb use the same shared controller.
const traveler=()=>({scene:new THREE.Group(),animations:Object.entries(durations).map(([name,duration])=>new THREE.AnimationClip(name,duration,[]))});
for(const stage of ['parallax','somnia']){
  const game=loadStage(stage,{traveler:traveler()});
  game.reset(0,20,0);game.dispatch('keydown',{code:'Digit3',repeat:false});
  assert.equal(game.run('emotes.active'),'Spin',`${stage}: key 3 spins`);game.frames(120);
  assert.equal(game.run('emotes.active'),null,`${stage}: the spin finishes`);assert.equal(game.run('avatarState'),'Fly',`${stage}: flight resumes`);
  const [x,,z]=game.run('cfg.notes[0]');game.reset(x+3,1,z);game.frames(40);
  assert.equal(game.run('emotes.active'),'Bow',`${stage}: a discovery bows`);game.frames(150);
  game.run('nextGate=routeGates.length-1');const gate=game.run('routeGates.at(-1).o.position.toArray()');game.reset(...gate);game.frames(2);
  assert.equal(game.run('emotes.active'),'Spin',`${stage}: completing the wind gates spins`);
}
console.log('PASS: traveler emote clips, phone emote buttons, key emotes return to flight, one emote at a time, idle wave, discovery bow; facility and suburb key, discovery and gate emotes.');
