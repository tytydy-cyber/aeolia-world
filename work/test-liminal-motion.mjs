import assert from 'node:assert/strict';
import {loadStage} from './liminal-harness.mjs';

// Behaviour checks for the facility and suburb, running the actual liminal.js.
for(const stage of ['parallax','somnia']){
  const game=loadStage(stage);
  const {run,frames,reset}=game;

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
console.log('PASS: facility and suburb travel is frame-rate independent at 30/60/120 Hz and boosted flight cannot tunnel through walls.');
