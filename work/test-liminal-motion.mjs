import assert from 'node:assert/strict';
import {loadStage} from './liminal-harness.mjs';

// Behaviour checks for the facility and suburb, running the actual liminal.js.
for(const stage of ['parallax','somnia']){
  const game=loadStage(stage);
  const {run,frames,reset}=game;
  assert.equal(run('boundaryBatch.count'),stage==='parallax'?64:72,`${stage}: visible boundary follows the full ground perimeter in one batch`);
  assert.equal(run('boundaryBatch.userData.visibleWorldBoundary'),true,`${stage}: boundary geometry is marked as the visible world edge`);

  // Same travel in one second at 30/60/120 Hz.
  const travel=[30,60,120].map(hz=>{reset(0,20,0);run('keys.ArrowUp=true');frames(hz,hz);run('keys.ArrowUp=false');return -run('player.position.z')});
  assert.ok(Math.max(...travel)-Math.min(...travel)<.1,`${stage}: frame-rate independent travel (${travel.map(v=>v.toFixed(3))})`);

  // Boosted flight at 30 Hz cannot tunnel through a wall (the thinnest full-height box in the stage).
  const wall=run("colliders.filter(c=>c.w>2&&c.bottom<=0&&c.top>=8&&validGround(c.x,c.z+c.d+4)).sort((a,b)=>a.d-b.d)[0]");
  assert.ok(wall,`${stage}: has a full-height wall to test against`);
  for(const hz of [30,120]){
    reset(wall.x,1,wall.z+wall.d+4);run('keys.ArrowUp=true;keys.ControlLeft=true');frames(hz,hz);run('keys.ArrowUp=false;keys.ControlLeft=false');
    assert.ok(run('player.position.z')>=wall.z+wall.d,`${stage}: boosted flight stops at a wall at ${hz} Hz`);
  }
}
// Vertical movement respects solid tops and undersides, so the traveler never ends up inside a pillar or ceiling.
{
  const suburb=loadStage('somnia');
  suburb.reset(0,46,-170);suburb.run('keys.ShiftLeft=true');suburb.frames(120);suburb.run('keys.ShiftLeft=false');
  assert.ok(Math.abs(suburb.run('player.position.y')-40)<.01,`descending onto the solar collector pillar lands on its top (${suburb.run('player.position.y')})`);
  suburb.run('keys.ArrowDown=true');suburb.frames(30);suburb.run('keys.ArrowDown=false');
  assert.ok(suburb.run('player.position.z')>-168,'the traveler can leave the pillar top sideways');
  const facility=loadStage('parallax');
  facility.reset(-30,6,35);facility.run('keys.Space=true');facility.frames(120);facility.run('keys.Space=false');
  assert.ok(Math.abs(facility.run('player.position.y+3.6')-13.45)<.01,`rising under the banquet ceiling stops below it (${facility.run('player.position.y')})`);
}
// Notifications: only discoveries carry the 発見 heading; a drag cancels the camera's turn toward a discovery.
{
  const game=loadStage('parallax'),heading=()=>game.elements.get('#event').querySelector('small');
  const [x,,z]=game.run("cfg.notes.find(n=>n[3]==='宴会場')");
  game.reset(x+3,1,z);game.frames(70);
  assert.equal(heading().textContent,'発見');assert.equal(heading().hidden,false,'discoveries show the 発見 heading');
  game.run('recenterYaw=yaw+2');
  const canvas=game.run('renderer.domElement');for(const fn of canvas.events.get('pointerdown'))fn({button:0,pointerId:1});
  game.dispatch('pointermove',{buttons:1,movementX:40,movementY:0});
  assert.equal(game.run('recenterYaw'),null,'dragging cancels the pending camera turn');
  const gate=game.run('routeGates[0].o.position.toArray()');game.reset(gate[0],gate[1],gate[2]+6);game.run('yaw=0;keys.ArrowUp=true');game.frames(30);game.run('keys.ArrowUp=false');
  assert.ok(game.elements.get('#event').querySelector('div').textContent.startsWith('気流'),'passing a wind gate shows its own message');
  assert.equal(heading().hidden,true,'wind gate messages hide the 発見 heading');
}
// With storage blocked the stage still starts, and a discovery is announced once, not every half second.
{
  const game=loadStage('somnia',{blockStorage:true});
  const [x,,z]=game.run('cfg.notes[0]');game.reset(x+3,1,z);
  const messages=new Set();for(let i=0;i<8;i++){game.frames(30);messages.add(game.elements.get('#event').querySelector('div').textContent)}
  assert.equal(game.run('readNotes().length'),1,'blocked storage keeps the journal in memory');
  game.elements.get('#event').querySelector('div').textContent='';game.frames(120);
  assert.equal(game.elements.get('#event').querySelector('div').textContent,'','a remembered discovery is not announced again');
}
// Returning to the window resumes sound that leaving it paused, as on the floating islands.
for(const stage of ['parallax','somnia']){
  const game=loadStage(stage);
  game.run("started=true;sound.start=async()=>{sound.paused=false;return true};sound.pause=()=>{sound.paused=true};sound.start()");
  game.dispatch('blur');assert.equal(game.run('sound.paused'),true,`${stage}: leaving the window pauses sound`);
  game.dispatch('focus');assert.equal(game.run('sound.paused'),false,`${stage}: returning to the window resumes sound`);
}
console.log('PASS: facility and suburb travel is frame-rate independent at 30/60/120 Hz and boosted flight cannot tunnel through walls; vertical flight stops on solid tops and under ceilings; notification headings; drag cancels camera recentering; blocked storage; sound resumes on focus.');
