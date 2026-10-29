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
// New outer discoveries turn existing background districts into reachable destinations without placing the target inside solid geometry.
for(const [stage,names] of Object.entries({parallax:['給水塔','北側宿泊棟','東側倉庫'],somnia:['共同学舎','空中菜園','外周住宅区']})){
  const game=loadStage(stage);
  for(const name of names){
    const note=game.run(`cfg.notes.find(n=>n[3]===${JSON.stringify(name)})`);
    assert.ok(note,`${stage}: ${name} exists`);
    assert.equal(game.run(`colliders.some(c=>contains(c,${note[0]},${note[2]}))`),false,`${stage}: ${name} is reachable outside solid geometry`);
  }
}
// Wide floors use a footprint-rounding geometry: their corner radius can never fold through their thickness.
{
  const facility=loadStage('parallax'),surfaces=facility.run('flatSurfaces.map(o=>({position:o.position.toArray(),spec:o.userData.flatSurface,box:new THREE.Box3().setFromObject(o).getSize(new THREE.Vector3()).toArray()}))');
  assert.equal(surfaces.length,8,'facility registers five zone floors and three ceiling plates');
  for(const surface of surfaces)assert.ok(surface.box[1]>=surface.spec.h-.001&&surface.spec.r<=Math.min(surface.spec.w,surface.spec.d)/2,'rounded surface keeps a valid footprint radius');
  assert.ok(Math.max(...surfaces.slice(0,5).map(s=>s.box[1]))<.2,'zone floors stay thin instead of folding metres above and below the ground');
  assert.equal(new Set(surfaces.slice(5).map(s=>s.position[1])).size,3,'overlapping ceiling plates occupy separate depth layers');
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
// A column immediately behind the traveler pulls the camera in front of it instead of leaving the column across the view.
{
  const facility=loadStage('parallax');facility.reset(1.3,1,70);facility.run('yaw=-Math.PI/2');facility.frames(120);
  assert.ok(facility.run('camera.position.x')>.85,`camera stays on the traveler side of a nearby column (${facility.run('camera.position.x')})`);
}
// Notifications: only discoveries carry the 発見 heading; a drag cancels the camera's turn toward a discovery.
{
  const game=loadStage('parallax'),heading=()=>game.elements.get('#event').querySelector('small');
  const [x,,z]=game.run("cfg.notes.find(n=>n[3]==='宴会場')");
  game.reset(x+3,1,z);game.frames(70);
  assert.equal(heading().textContent,'発見');assert.equal(heading().hidden,false,'discoveries show the 発見 heading');
  assert.ok(!game.elements.get('#place').textContent.startsWith('宴会場'),'the guide advances to an unfinished destination after a discovery');
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
// A suburb discovery changes a concrete junction and the neighboring circuit, rather than text alone.
{
  const game=loadStage('somnia');game.run("activateSuburbCircuit('集光塔')");
  const colors=game.run("[4,3,0].map(i=>{const c=new THREE.Color();suburbCircuitMarkers.getColorAt(i,c);return c.getHex()})");
  assert.equal(colors.join(','),[0xffe2a0,0x9fe8d5,0x537b78].join(','),'collector discovery highlights its junction, adjacent segment and leaves distant branches muted');
}
// The facility service shortcut has a lit entrance and exit, and its five decks leave a clear flight lane above them.
{
  const game=loadStage('parallax');assert.equal(game.run("world.children.find(o=>o.userData.serviceDeckCount)?.userData.serviceDeckCount"),5,'facility connects the original three decks to an entrance and exit deck');
  game.run("activateFacilityRoute('渡り廊下')");const colors=game.run("[0,1,2,3].map(i=>{const c=new THREE.Color();facilityServiceThresholds.getColorAt(i,c);return c.getHex()})");
  assert.equal(colors.join(','),Array(4).fill(0xffdfa0).join(','),'walkway discovery lights every threshold through the lobby-side exit');
  for(const [x,y,z] of game.run("world.children.find(o=>o.userData.route)?.userData.route"))assert.equal(game.run(`colliders.some(c=>${y}>c.bottom&&${y}<c.top&&contains(c,${x},${z},.15))`),false,`service flight lane stays clear at ${x},${y},${z}`);
}
// Each facility discovery calls its named physical response; the loading-bay door stays present and changes material.
{
  const game=loadStage('parallax');assert.equal(game.run('[...facilityDiscoveryEffects.keys()].sort().join()'),['宴会場','受付','北側宿泊棟','搬入口','東側倉庫','浴場','渡り廊下','給水塔'].sort().join(),'all facility discoveries map to a concrete response');
  const before=game.run("[...world.children].find(o=>o.userData.label==='搬入口の扉が一枚だけ暗くなった。').material.color.getHex()");game.run("facilityDiscoveryEffects.get('搬入口')()");const after=game.run("[...world.children].find(o=>o.userData.label==='搬入口の扉が一枚だけ暗くなった。').material.color.getHex()");
  assert.notEqual(after,before,'loading-bay discovery changes its own door material');
}
// Completing a world changes the whole route and the saved notes restore that state on revisit.
for(const stage of ['parallax','somnia']){
  const game=loadStage(stage);game.run("stored('aeolia-notes',JSON.stringify(cfg.notes.map(n=>({id:stageKey+':'+n[3]}))));completeWorld()");
  assert.equal(game.run('worldComplete'),true,`${stage}: completion state is applied`);assert.ok(game.run('scene.fog.density<cfg.fogDensity'),`${stage}: completion clears the long view`);
}
// Returning to the window resumes sound that leaving it paused, as on the floating islands.
for(const stage of ['parallax','somnia']){
  const game=loadStage(stage);
  game.run("started=true;sound.start=async()=>{sound.paused=false;return true};sound.pause=()=>{sound.paused=true};sound.start()");
  game.dispatch('blur');assert.equal(game.run('sound.paused'),true,`${stage}: leaving the window pauses sound`);
  game.dispatch('focus');assert.equal(game.run('sound.paused'),false,`${stage}: returning to the window resumes sound`);
}
console.log('PASS: facility and suburb travel is frame-rate independent at 30/60/120 Hz and boosted flight cannot tunnel through walls; vertical flight stops on solid tops and under ceilings; notification headings; drag cancels camera recentering; blocked storage; sound resumes on focus.');
