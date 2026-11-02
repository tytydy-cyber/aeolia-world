import {execFile} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {once} from 'node:events';

const browser='/Applications/Vivaldi.app/Contents/MacOS/Vivaldi',port=9342,root='http://localhost:8767/';
const shots=[['islands-wide','aeolia.html?trailer=1&shot=wide'],['islands-city','aeolia.html?trailer=1&shot=city'],['suburb-wide','liminal.html?stage=somnia&trailer=1&shot=wide'],['suburb-water','liminal.html?stage=somnia&trailer=1&shot=water'],['playroom-rainbow','playroom.html?trailer=1&shot=rainbow'],['playroom-playground','playroom.html?trailer=1&shot=playground']],selected=process.env.SHOTS?shots.filter(([name])=>process.env.SHOTS.split(',').includes(name)):shots;
const cards=[['opening','4つの世界を飛ぶ。','','d6a556'],['ending','AEOLIA','ブラウザで公開中','d6a556']];
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const child=execFile(browser,[`--remote-debugging-port=${port}`,'--headless=new','--hide-scrollbars','--window-size=1280,720','--force-device-scale-factor=1','--user-data-dir=/tmp/aeolia-cinematic-browser','about:blank']);

try{
  let list;for(let i=0;i<40;i++){try{list=await fetch(`http://127.0.0.1:${port}/json`).then(r=>r.json());break}catch{await delay(250)}}
  if(!list)throw new Error('headless browser did not start');
  const socket=new WebSocket(list.find(x=>x.type==='page').webSocketDebuggerUrl);await once(socket,'open');
  let id=0;const pending=new Map();socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const call=++id;pending.set(call,m=>m.error?reject(new Error(m.error.message)):resolve(m.result));socket.send(JSON.stringify({id:call,method,params}))});
  const base=new URL('./generated-cinematic/',import.meta.url);await mkdir(base,{recursive:true});
  for(const [name,path] of selected){const dir=new URL(`clip-${name}/`,base);await mkdir(dir,{recursive:true});await send('Page.navigate',{url:root+path});await delay(7000);for(let i=1;i<=36;i++){const {data}=await send('Page.captureScreenshot',{format:'jpeg',quality:90,fromSurface:true,captureBeyondViewport:false});await writeFile(new URL(`${String(i).padStart(4,'0')}.jpg`,dir),Buffer.from(data,'base64'));await delay(90)}console.log(name)}
  for(const [name,title,body,accent] of cards){const query=new URLSearchParams({kicker:name==='opening'?'A SHORT FLIGHT':'EXPLORE NOW',title,body,accent});await send('Page.navigate',{url:`${root}trailer-card.html?${query}`});await delay(500);const {data}=await send('Page.captureScreenshot',{format:'jpeg',quality:92,fromSurface:true,captureBeyondViewport:false});await writeFile(new URL(`card-${name}.jpg`,base),Buffer.from(data,'base64'))}
  socket.close();
}finally{child.kill('SIGTERM')}
