import {execFile} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {once} from 'node:events';

const browser='/Applications/Vivaldi.app/Contents/MacOS/Vivaldi',port=9346,root='http://localhost:8767/aeolia.html?characterPreview=';
const names=['ember','mist','lilac'],delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const child=execFile(browser,[`--remote-debugging-port=${port}`,'--headless=new','--hide-scrollbars','--window-size=800,1000','--force-device-scale-factor=1','--user-data-dir=/tmp/aeolia-traveler-thumbnails','about:blank']);
try{
  let list;for(let i=0;i<40;i++){try{list=await fetch(`http://127.0.0.1:${port}/json`).then(r=>r.json());break}catch{await delay(250)}}
  if(!list)throw new Error('headless browser did not start');
  const socket=new WebSocket(list.find(x=>x.type==='page').webSocketDebuggerUrl);await once(socket,'open');let id=0;const pending=new Map();
  socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const call=++id;pending.set(call,m=>m.error?reject(new Error(m.error.message)):resolve(m.result));socket.send(JSON.stringify({id:call,method,params}))});
  const out=new URL('../outputs/assets/thumbnails/',import.meta.url);await mkdir(out,{recursive:true});
  for(const name of names){await send('Page.navigate',{url:root+name});await delay(6500);const {data}=await send('Page.captureScreenshot',{format:'jpeg',quality:92,fromSurface:true,captureBeyondViewport:false});await writeFile(new URL(`traveler-${name}.jpg`,out),Buffer.from(data,'base64'));console.log(name)}
  socket.close();
}finally{child.kill('SIGTERM')}
