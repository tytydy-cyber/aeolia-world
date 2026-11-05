import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

// Entry, return and shared-state wiring between the world select and all stages.
const read=name=>readFileSync(new URL('../outputs/'+name,import.meta.url),'utf8');
const hub=read('index.html'),aeolia=read('aeolia.html'),liminalPage=read('liminal.html'),liminal=read('liminal.js'),playroomPage=read('playroom.html'),playroom=read('playroom.js');

const gates=[...hub.matchAll(/class="gate [a-z]+" href="([^"]+)"/g)].map(m=>m[1]);
assert.deepEqual(gates,['aeolia.html','liminal.html?stage=parallax','liminal.html?stage=somnia','playroom.html'],'world select links each stage once');
for(const [name,page] of [['aeolia.html',aeolia],['liminal.html',liminalPage],['playroom.html',playroomPage]])assert.ok(page.includes('class="return" href="index.html"'),`${name} links back to the world select`);
for(const [name,page] of [['aeolia.html',aeolia],['liminal.html',liminalPage],['playroom.html',playroomPage]])assert.ok(page.includes('min-height:52px')&&page.includes('min-height:46px'),`${name} gives the enter and world-select actions a touch-sized target`);
assert.ok(hub.includes('.foot a,.journal{display:inline-flex;min-height:46px'),'world-select footer actions are not rendered as tiny text links');
assert.ok(liminal.includes("get('stage')==='somnia'?'somnia':'parallax'"),'unknown stage values fall back to the facility');

const options=page=>[...page.matchAll(/<option value="([a-z]+)">([^<]+)/g)].map(m=>m[1]+':'+m[2]);
assert.deepEqual(options(aeolia),options(liminalPage));assert.deepEqual(options(aeolia),options(playroomPage),'all stages offer the same traveler designs');
for(const [name,source] of [['aeolia.html',aeolia],['liminal.js',liminal],['playroom.js',playroom]]){
  assert.ok(source.includes("stored('aeolia-character')")&&source.includes("stored('aeolia-character',e.target.value)"),`${name} reads and stores the traveler choice under the shared key`);
  assert.ok(source.includes("stored('aeolia-notes')")&&source.includes("stored('aeolia-notes',JSON.stringify(notes))"),`${name} reads and appends to the shared journal`);
  assert.ok(source.includes('const memoryStore=new Map(),stored=(key,value)=>{try{'),`${name} falls back to memory when storage is blocked`);
}
assert.ok(aeolia.includes("id='aeolia:'+d.name")&&liminal.includes("id=stageKey+':'+note[3]")&&playroom.includes("id='playroom:'+n[3]"),'journal ids are namespaced per stage, so stages never overwrite each other');
for(const [name,page] of [['aeolia.html',aeolia],['liminal.html',liminalPage],['playroom.html',playroomPage]])assert.ok(page.includes('id="soundToggle"')&&page.includes('id="soundVolume"'),`${name} has mute and volume controls`);
for(const [name,page] of [['aeolia.html',aeolia],['liminal.html',liminalPage],['playroom.html',playroomPage]])assert.match(page,/<label id="pace">速さ <input id="paceInput" type="range" min="0\.7" max="1\.6" step="0\.1" value="1"[^>]*><output id="paceValue">1\.0×<\/output><\/label>/,`${name} exposes the shared desktop speed range`);
for(const [name,page] of [['liminal.html',liminalPage],['playroom.html',playroomPage]]){
  assert.match(page,/<div id="emoteControls"[^>]*>[\s\S]*?data-emote="Wave"[\s\S]*?data-emote="Bow"[\s\S]*?data-emote="Spin"[\s\S]*?<\/div>/,`${name} exposes all three desktop emote buttons`);
  assert.match(page,/@media\(pointer:coarse\),\(max-width:760px\)\{[^}]*#emoteControls\{display:none/,`${name} hides desktop emotes on coarse and narrow screens`);
}

// The world select counts and lists entries from every stage.
const store=new Map([['aeolia-notes',JSON.stringify([{id:'aeolia:市場',world:'浮島の街',name:'市場',text:'a'},{id:'parallax:受付',world:'閉鎖施設',name:'受付',text:'b'},{id:'somnia:公園',world:'郊外',name:'公園',text:'c'},{id:'playroom:虹',world:'遊戯室',name:'虹',text:'d'}])],['aeolia-endpoints',JSON.stringify([{id:'aeolia:雲上観測台',world:'浮島の街',name:'雲上観測台'}])]]);
const elements=new Map(),element=()=>({textContent:'',innerHTML:'',hidden:true,onclick:null});
const document={querySelector:s=>{if(!elements.has(s))elements.set(s,element());return elements.get(s)}};
const script=hub.match(/<script>([\s\S]*?)<\/script>/)[1];
new Function('localStorage','document','addEventListener',script)({getItem:k=>store.get(k)??null},document,()=>{});
assert.equal(document.querySelector('#found').textContent,'発見 4 ／ 終着点 1','world select counts discoveries and separately persisted endpoint arrivals');
document.querySelector('#journal').onclick();
for(const world of ['浮島の街','閉鎖施設','郊外','遊戯室'])assert.ok(document.querySelector('#entries').innerHTML.includes(world),`journal lists ${world}`);
// With storage blocked, the world select still renders.
{
  const blockedElements=new Map(),blocked={querySelector:s=>{if(!blockedElements.has(s))blockedElements.set(s,element());return blockedElements.get(s)}};
  new Function('localStorage','document','addEventListener',script)({getItem(){throw new Error('SecurityError')}},blocked,()=>{});
  assert.equal(blocked.querySelector('#found').textContent,'発見 0 ／ 終着点 0','world select shows zero discoveries and endpoints when storage is blocked');
}
console.log('PASS: world select links, return links, stage fallback, shared traveler and journal keys, per-stage journal ids, sound and pace controls, desktop emote buttons, cross-stage journal listing, blocked storage.');
