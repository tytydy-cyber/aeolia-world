import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {run,dispatch,reset,frames,document} from './test-controls.mjs';

// Regression checks for the audit findings, using the actual game loop.
const result={};
result.travel={};
for(const hz of [5,10,15,20,30,60,120]){
  reset();run('previousFrame=null;keys.ArrowUp=true;loop(0)');
  const loop=run('loop');for(let i=1;i<=hz;i++)loop(i*1000/hz);
  result.travel[hz]=40-run('player.position.z');
}
assert.ok(Math.max(...Object.values(result.travel))-Math.min(...Object.values(result.travel))<.02,'5–120 FPS preserve elapsed movement time');

reset();dispatch('keydown',{code:'ArrowUp',target:{tagName:'BUTTON'}});frames();
assert.equal(40-run('player.position.z'),0,'focused controls retain native keyboard behavior');
result.focusRecovery={};
for(const selector of ['#soundToggle','#effectsToggle','#soundVolume','#paceInput']){
  reset();dispatch('keydown',{code:'ArrowUp'});
  const target=document.querySelector(selector);target.focus();
  assert.equal(run('Object.keys(keys).length'),0,'entering settings clears held input');
  dispatch(selector.endsWith('Toggle')?'click':'pointerup',{target});
  assert.equal(document.activeElement,run('renderer.domElement'),'pointer settings return focus to game');
  dispatch('keydown',{code:'ArrowUp'});frames();
  result.focusRecovery[selector]=40-run('player.position.z');
  assert.ok(result.focusRecovery[selector]>8,'movement works after settings');
}
reset();dispatch('keydown',{code:'ArrowUp'});
dispatch('keydown',{code:'Escape',target:{tagName:'INPUT'}});
result.escapeWithInputFocusClearsKeys=run('!keys.ArrowUp');
assert.equal(result.escapeWithInputFocusClearsKeys,true);
assert.equal(document.activeElement,run('renderer.domElement'));
reset();const slider=document.querySelector('#paceInput');slider.focus();
assert.equal(dispatch('keydown',{code:'ArrowRight',target:slider}).prevented,undefined,'native slider arrows not intercepted');
dispatch('keydown',{code:'Escape',target:slider});dispatch('keydown',{code:'ArrowUp'});frames();assert.ok(40-run('player.position.z')>8);

reset();run('player.position.set(-105,34,-95);keys.ArrowUp=true');frames(60);
result.towerPosition=run('player.position.toArray()');
assert.ok(Math.hypot(result.towerPosition[0]+105,result.towerPosition[2]+105)>=9.29,'tower wall blocks movement');
reset();run('player.position.set(112,54,-78);keys.ArrowUp=true');frames(120);
result.windmillPosition=run('player.position.toArray()');assert.ok(Math.hypot(result.windmillPosition[0]-112,result.windmillPosition[2]+92)>=9.65,'windmill blocks movement');
for(const [x,z,y] of [[-105,-105,78],[112,-92,94]]){
  reset();run(`player.position.set(${x},${y},${z+15});flying=true;keys.ArrowUp=true`);frames(60);
  assert.ok(run('player.position.z')<z,'can fly over landmark roofs');
}

reset();run('player.position.set(-78,10,-68);flying=true;keys.ArrowRight=true');frames(60);
result.underBridgePosition=run('player.position.toArray()');
assert.ok(result.underBridgePosition[0]>-65,'can fly beneath bridge');
assert.equal(result.underBridgePosition[1],10,'no teleport onto bridge');
result.deckAtCrossing=run('groundAt(-69.5,-68)');
reset();run('player.position.set(-69.5,10,-68);flying=true;keys.Space=true');frames(120);
result.bridgeCeilingY=run('player.position.y');assert.ok(Math.abs(result.bridgeCeilingY-(result.deckAtCrossing-.3-run('PLAYER_HEIGHT')))<.001,'bridge underside stops upward flight above the hat');
run('keys.Space=false;keys.ShiftLeft=true');frames(30);assert.ok(run('player.position.y')<17,'can descend away from ceiling');
reset();run('player.position.set(-69.5,30,-68)');frames(120);
result.bridgeLandingY=run('player.position.y');assert.equal(result.bridgeLandingY,20.5,'can land on bridge from above');
for(const b of run('BRIDGES')){
  const [ax,az,bx,bz]=b,t=.4,x=ax+(bx-ax)*t,z=az+(bz-az)*t;
  reset();run(`player.position.set(${x},groundAt(${x},${z}),${z});yaw=${Math.atan2(ax-bx,az-bz)};keys.ArrowUp=true`);frames(60);
  assert.ok(run(`player.position.distanceTo(new THREE.Vector3(${x},groundAt(${x},${z}),${z}))`)>8,'walk uphill along bridge');
}
reset();run('previousFrame=null;keys.ArrowUp=true;loop(0);loop(100)');
const beforePause=run('player.position.clone()');dispatch('blur');run('loop(5000)');assert.ok(run('player.position').equals(beforePause),'resume does not catch up hidden time');
run('keys.ArrowUp=true;loop(10000)');assert.ok(run('player.position').equals(beforePause),'long suspension does not teleport');
reset();run('previousFrame=null;loop(0);motionEffects.dust.next=0;motionEffects.emit(motionEffects.dust,0,3,40,0,0,0,2);loop(100)');
assert.ok(Math.abs(run('motionEffects.dust.items[0].age')-.1)<1e-9,'effects preserve slow-frame elapsed time');

const scene=run('scene');scene.updateMatrixWorld(true);
const stats={renderableObjects:0,meshBatches:0,sprites:0,triangles:0,shadowCastingMeshes:0};
scene.traverseVisible(o=>{
  if(o.isMesh){stats.meshBatches+=Array.isArray(o.material)?o.geometry.groups.length:1;stats.triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3*(o.isInstancedMesh?o.count:1);if(o.castShadow)stats.shadowCastingMeshes++}
  if(o.isSprite)stats.sprites++;
  if(o.isMesh||o.isSprite||o.isPoints||o.isLine)stats.renderableObjects++;
});result.scene=stats;

// CPU only: real scene transforms, camera raycasts and effects; renderer is a no-op.
result.cpuMs={};
for(const mode of ['idle','walk','fly']){
  reset();run(`flying=${mode==='fly'};keys.ArrowUp=${mode!=='idle'};previousFrame=null;loop(0)`);
  const loop=run('loop'),player=run('player'),samples=[];
  for(let i=1;i<=1800;i++){
    if(i%60===1)player.position.set(0,mode==='fly'?80:3,40);
    const start=performance.now();loop(i*1000/60);scene.updateMatrixWorld(true);
    if(i>300)samples.push(performance.now()-start);
  }
  samples.sort((a,b)=>a-b);
  result.cpuMs[mode]={samples:samples.length,median:samples[Math.floor(samples.length*.5)],p95:samples[Math.floor(samples.length*.95)],max:samples.at(-1)};
}
writeFileSync(new URL('./audit-results.json',import.meta.url),JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
