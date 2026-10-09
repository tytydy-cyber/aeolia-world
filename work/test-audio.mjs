import assert from 'node:assert/strict';
import {WorldAudio} from '../outputs/audio.js';

// Validate scheduling/lifecycle without claiming to test a physical audio device.
class Param {
  constructor(){this.value=0;this.events=[]}
  setValueAtTime(value,time){assert.ok(Number.isFinite(value)&&Number.isFinite(time));this.value=value;this.events.push([value,time])}
  linearRampToValueAtTime(value,time){this.setValueAtTime(value,time)}
  exponentialRampToValueAtTime(value,time){assert.ok(value>0);this.setValueAtTime(value,time)}
  setTargetAtTime(value,time,constant){assert.ok(constant>0);this.setValueAtTime(value,time)}
}
class Node {
  constructor(ctx){this.ctx=ctx;this.gain=new Param();this.frequency=new Param();this.playbackRate=new Param();this.connections=[];ctx.nodes.push(this)}
  connect(node){this.connections.push(node)}
  disconnect(){this.connections=[]}
  start(time=0){assert.equal(this.started,undefined,'source starts only once');assert.ok(time>=this.ctx.currentTime);this.started=true}
  stop(time){assert.ok(time>=this.ctx.currentTime);this.stopAt=time}
}
class Context {
  static count=0;
  constructor(){Context.count++;this.nodes=[];this.state='suspended';this.currentTime=0;this.sampleRate=8000;this.destination={}}
  createGain(){return new Node(this)}
  createBiquadFilter(){return new Node(this)}
  createDelay(){const n=new Node(this);n.delayTime=new Param();return n}
  createDynamicsCompressor(){const n=new Node(this);n.threshold=new Param();n.knee=new Param();n.ratio=new Param();n.attack=new Param();n.release=new Param();return n}
  createBufferSource(){return new Node(this)}
  createOscillator(){return new Node(this)}
  createConvolver(){return new Node(this)}
  createBuffer(channels,length){const data=Array.from({length:channels},()=>new Float32Array(length));return {getChannelData:i=>data[i]}}
  async resume(){this.state='running'}
  async suspend(){this.state='suspended'}
  advance(seconds){this.currentTime+=seconds;for(const node of this.nodes)if(node.onended&&node.stopAt<=this.currentTime){node.onended();node.onended=null}}
}

const audio=new WorldAudio(Context);
assert.equal(Context.count,0,'no autoplay/context before gesture');
audio.update(.016,10,false,true,false);audio.chime();assert.equal(Context.count,0);
assert.ok(await audio.start());assert.equal(Context.count,1);assert.ok(audio.audible);
await audio.start();assert.equal(Context.count,1,'resume reuses the same context');
const c=audio.ctx;
assert.equal(audio.master.gain.value,.5);
assert.equal(audio.master.connections[0],audio.limiter,'all audio passes through limiter');
assert.equal(audio.limiter.connections[0],c.destination);assert.equal(audio.limiter.threshold.value,-6);assert.equal(audio.limiter.ratio.value,12);
for(const value of audio.noise.getChannelData(0))assert.ok(Number.isFinite(value)&&Math.abs(value)<=1,'bounded noise');
audio.nextPhrase=audio.nextDetail=Infinity;

function tick(speed,fly,ground,n=60,bridge=false){for(let i=0;i<n;i++){c.advance(1/60);audio.update(1/60,speed,fly,ground,bridge)}}
let steps=0;const originalStep=audio.step.bind(audio);audio.step=wood=>{steps++;originalStep(wood)};
tick(0,false,true);assert.equal(steps,0,'no steps at rest');
tick(10,false,true);assert.ok(steps>=4&&steps<=5,'footstep cadence follows walking');
let before=steps;tick(28,true,false);assert.equal(steps,before,'no footsteps while flying');
tick(10,false,false);assert.equal(steps,before,'no footsteps while falling');
tick(10,false,true,60,true);assert.ok(steps>before);assert.equal(c.nodes.filter(n=>n.type==='lowpass').at(-1).frequency.value,700,'wooden bridge sound');

c.advance(1);audio.chime();assert.equal(audio.voices.size,6,'two-tone bell partials');
c.advance(3);assert.equal(audio.voices.size,0,'finished voices are disconnected');
for(let i=0;i<20;i++)audio.chime();assert.ok(audio.voices.size<=24,'bounded simultaneous voices');
c.advance(3);assert.equal(audio.voices.size,0);
audio.setMuted(true);assert.equal(audio.master.gain.value,0);audio.chime();assert.equal(audio.voices.size,0);
before=steps;tick(10,false,true);assert.equal(steps,before,'muted footsteps do not schedule sources');
audio.setVolume(.7);assert.equal(audio.master.gain.value,0,'volume change preserves mute');
audio.setMuted(false);assert.equal(audio.master.gain.value,.7);
audio.setVolume(Infinity);assert.equal(audio.volume,.35);audio.setVolume(-1);assert.equal(audio.volume,0);audio.setVolume(2);assert.equal(audio.volume,1);
audio.pause();assert.equal(c.state,'suspended');assert.equal(audio.audible,false);assert.equal(audio.master.gain.value,0);
await audio.start();assert.ok(audio.audible);assert.equal(Context.count,1);
assert.equal(await new WorldAudio(null).start(),false,'unsupported audio does not break game');
audio.distantPhrase();assert.equal(audio.voices.size,8,'world selection schedules one quiet ascending phrase');
const complex=new WorldAudio(Context,'complex');await complex.start();complex.setEnvironment(3,.4);complex.update(.016,0,true,false,false);assert.equal(complex.hums.length,2,'closed facility has continuous machinery hum');assert.equal(complex.environment,3);assert.equal(complex.voices.size,9,'closed facility schedules melody and one district detail');
const suburb=new WorldAudio(Context,'suburb');await suburb.start();suburb.setEnvironment(3,.8);suburb.nextPhrase=Infinity;suburb.update(.016,12,true,false,false);assert.equal(suburb.environment,3);assert.equal(suburb.altitude,.8);assert.equal(suburb.voices.size,1,'suburb district schedules one restrained environmental detail');suburb.setEnvironment(99,-2);assert.equal(suburb.environment,4);assert.equal(suburb.altitude,0,'environment values remain bounded');
const playroom=new WorldAudio(Context,'playroom');await playroom.start();playroom.setEnvironment(2,.2);playroom.nextDetail=Infinity;playroom.distantPhrase();assert.equal(playroom.voices.size,3,'playroom schedules only a fragment of its shared melody');playroom.nextPhrase=0;playroom.update(.016,0,true,false,false);assert.equal(playroom.nextPhrase,9,'playroom renews its distant phrase before the ambience feels empty');playroom.nextPhrase=Infinity;playroom.nextDetail=0;playroom.update(.016,0,true,false,false);assert.equal(playroom.voices.size,7,'playroom adds a quiet room-specific sound');
const steadyVolume=playroom.master.gain.value;for(const zone of [0,1,2,3,4,1]){playroom.setEnvironment(zone,.2);playroom.nextDetail=0;playroom.update(.016,8,true,false,false);assert.equal(playroom.master.gain.value,steadyVolume,'room changes keep the continuous bed at one volume')}assert.ok(playroom.wind.started&&playroom.pads.every(pad=>pad.started),'wind and three pads prevent silent gaps in every room');
console.log('PASS: gesture-only start, single context, noise bounds, wind update, stone/wood steps, flight/fall silence, chimes, voice cleanup/cap, mute/volume, pause/resume, unavailable API. Audio output quality is not tested.');

// Indoor worlds sound enclosed: a room tail is mixed in, and flight air is quieter and darker than the open-sky gust.
const flightTone=async mood=>{const world=new WorldAudio(Context,mood);await world.start();world.nextPhrase=world.nextDetail=world.nextChord=Infinity;world.setEnvironment?.(0,.8);for(let i=0;i<60;i++){world.ctx.advance(1/60);world.update(1/60,35,true,false,false)}return world};
const sky=await flightTone('sky'),room=await flightTone('playroom'),facility=await flightTone('complex');
assert.ok(!sky.room&&room.room&&facility.room,'only indoor worlds get a room tail');
assert.equal(room.master.connections[0],room.limiter,'indoor audio still passes through the limiter first');
assert.ok(room.roomGain.connections.includes(room.limiter),'the room tail joins before the limiter');
assert.ok(room.filter.frequency.value<sky.filter.frequency.value*.6&&room.windGain.gain.value<sky.windGain.gain.value*.6,'indoor flight air is darker and quieter than the sky gust');
console.log('PASS: indoor worlds add a room tail and soften flight air.');
