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
  createDynamicsCompressor(){const n=new Node(this);n.threshold=new Param();n.knee=new Param();n.ratio=new Param();n.attack=new Param();n.release=new Param();return n}
  createBufferSource(){return new Node(this)}
  createOscillator(){return new Node(this)}
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
assert.equal(audio.master.gain.value,.35);
assert.equal(audio.master.connections[0],audio.limiter,'all audio passes through limiter');
assert.equal(audio.limiter.connections[0],c.destination);assert.equal(audio.limiter.threshold.value,-6);assert.equal(audio.limiter.ratio.value,12);
for(const value of audio.noise.getChannelData(0))assert.ok(Number.isFinite(value)&&Math.abs(value)<=1,'bounded noise');

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
console.log('PASS: gesture-only start, single context, noise bounds, wind update, stone/wood steps, flight/fall silence, chimes, voice cleanup/cap, mute/volume, pause/resume, unavailable API. Audio output quality is not tested.');
