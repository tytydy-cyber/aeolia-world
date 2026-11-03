import {execFile} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {once} from 'node:events';

const browser='/Applications/Vivaldi.app/Contents/MacOS/Vivaldi',port=9343,root='http://localhost:8767/aeolia.html?trailer5=';
const shots=[['reveal',26],['bridge',24]],delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const child=execFile(browser,[`--remote-debugging-port=${port}`,'--headless=new','--hide-scrollbars','--window-size=1280,720','--force-device-scale-factor=1','--user-data-dir=/tmp/aeolia-first-five-browser','about:blank']);
try{
  let list;for(let i=0;i<40;i++){try{list=await fetch(`http://127.0.0.1:${port}/json`).then(r=>r.json());break}catch{await delay(250)}}
  if(!list)throw new Error('headless browser did not start');
  const socket=new WebSocket(list.find(x=>x.type==='page').webSocketDebuggerUrl);await once(socket,'open');let id=0;const pending=new Map();
  socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const call=++id;pending.set(call,m=>m.error?reject(new Error(m.error.message)):resolve(m.result));socket.send(JSON.stringify({id:call,method,params}))});
  const base=new URL('./generated-first-five/',import.meta.url);await mkdir(base,{recursive:true});
  for(const [name,count] of shots){const dir=new URL(`${name}/`,base);await mkdir(dir,{recursive:true});await send('Page.navigate',{url:root+name});await delay(7000);await send('Runtime.evaluate',{expression:'globalThis.__startTrailer?.()'});for(let i=1;i<=count;i++){const {data}=await send('Page.captureScreenshot',{format:'jpeg',quality:92,fromSurface:true,captureBeyondViewport:false});await writeFile(new URL(`${String(i).padStart(4,'0')}.jpg`,dir),Buffer.from(data,'base64'));await delay(90)}console.log(name)}
  socket.close();
}finally{child.kill('SIGTERM')}
