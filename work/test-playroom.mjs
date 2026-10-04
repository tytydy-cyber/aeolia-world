import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read=name=>readFileSync(new URL('../outputs/'+name,import.meta.url),'utf8');
const html=read('playroom.html'),js=read('playroom.js'),hub=read('index.html');
assert.ok(html.includes('DREAMCORE PLAYROOM 04')&&html.includes('playroom.js?v=4'),'playroom has its own entry page and module');
assert.ok(hub.includes('class="gate playroom"')&&hub.includes('4つのエリア'),'world select exposes the fourth world');
for(const asset of ['playroom-rainbow.glb','playroom-slide.glb','playroom-ball-pit.glb'])assert.ok(js.includes(asset),`${asset} is placed in the hall`);
for(const texture of ['sky-wallpaper.jpg','clouds-12-atlas.png','carpet.jpg'])assert.ok(js.includes(texture),`${texture} is used by the hall`);
assert.ok(js.includes("spawn:[0,0,25]")&&js.includes("Math.abs(x)<62&&Math.abs(z)<43")&&js.includes('limitY:28'),'hall has a bounded 130 by 90 metre playable volume');
assert.equal((js.match(/'[^']+','[^']+'\]/g)||[]).filter(s=>['大きな虹','滑り台の上','ボールプール','小さな扉','上の通路'].some(n=>s.includes(n))).length,5,'initial hall has five discoveries');
assert.ok(js.includes('const anomalies=[')&&js.includes('anomalyIndex++%anomalies.length'),'entry-local anomalies advance without overwriting the persistent journal');
assert.ok(js.includes("id='playroom:'+n[3]")&&js.includes("stored('aeolia-notes',JSON.stringify(notes))"),'playroom discoveries share the cross-world journal under their own namespace');
assert.ok(js.includes('mergeGeometries(cloudParts,false)')&&js.includes('mergeStatic()'),'cloud decals and static architecture are batched');
assert.ok(js.includes('function compactAsset(source)')&&js.includes("material?.name==='Faded red plastic'"),'Blender assets merge by material while retaining the slide anomaly');
console.log('PASS: fourth-world entry, bounded layered hall, Blender landmarks, authored textures, discoveries, anomalies and shared journal.');
