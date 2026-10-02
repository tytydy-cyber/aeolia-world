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
console.log('PASS: facility and suburb travel is frame-rate independent at 30/60/120 Hz and boosted flight cannot tunnel through walls; vertical flight stops on solid tops and under ceilings.');
