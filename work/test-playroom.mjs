import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read=name=>readFileSync(new URL('../outputs/'+name,import.meta.url),'utf8');
const html=read('playroom.html'),js=read('playroom.js'),hub=read('index.html');
assert.ok(html.includes('DREAMCORE PLAYROOM 04')&&html.includes('playroom.js?v=7'),'playroom has its own entry page and module');
assert.ok(hub.includes('class="gate playroom"')&&hub.includes('4つのエリア'),'world select exposes the fourth world');
for(const asset of ['playroom-rainbow.glb','playroom-slide.glb','playroom-ball-pit.glb','playroom-playground-pack.glb','playroom-child-town-pack.glb','playroom-quiet-rooms-pack.glb','playroom-cloud-corridor-pack.glb'])assert.ok(js.includes(asset),`${asset} is placed in the world`);
for(const texture of ['sky-wallpaper.jpg','clouds-12-atlas.png','carpet.jpg'])assert.ok(js.includes(texture),`${texture} is used by the hall`);
assert.ok(js.includes("spawn:[0,0,25]")&&js.includes("Math.abs(x)<92&&z<62&&z>-152")&&js.includes('limitY:32'),'seven districts share a bounded 190 by 220 metre playable volume');
assert.equal((js.match(/'[^']+','[^']+'\]/g)||[]).filter(s=>['大きな虹','滑り台の上','ボールプール','小さな扉','上の通路','遊具広場','奥のボールプール','子どもの街','最後の布団','誕生日席','雲の回廊','天井裏'].some(n=>s.includes(n))).length,12,'the expanded world has twelve discoveries');
for(const safe of ["[10,5,-55,'遊具広場'","[52,3,-63,'子どもの街'","[-49,2,-99,'最後の布団'","[48,2,-106,'誕生日席'","[14,18,-139,'雲の回廊'"])assert.ok(js.includes(safe),`${safe} is outside its solid proxy`);
assert.equal((js.match(/floorPatch\(\[/g)||[]).length,6,'six asymmetric floor fields distinguish the added districts');
assert.ok(js.includes('const anomalies=[')&&js.includes('anomalyIndex++%anomalies.length'),'entry-local anomalies advance without overwriting the persistent journal');
assert.ok(js.includes("id='playroom:'+n[3]")&&js.includes("stored('aeolia-notes',JSON.stringify(notes))"),'playroom discoveries share the cross-world journal under their own namespace');
assert.ok(js.includes('mergeGeometries(cloudParts,false)')&&js.includes('mergeStatic()'),'cloud decals and static architecture are batched');
assert.ok(js.includes('function compactAsset(source)')&&js.includes('vertexColors:true')&&js.includes("toNonIndexed()"),'Blender assets bake their colors into one draw batch per placement');
console.log('PASS: fourth-world entry, bounded layered hall, Blender landmarks, authored textures, discoveries, anomalies and shared journal.');
