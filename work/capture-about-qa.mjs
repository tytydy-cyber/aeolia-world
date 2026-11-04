import {execFile} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
import {once} from 'node:events';

const mobile=process.argv.includes('--mobile'),browser='/Applications/Vivaldi.app/Contents/MacOS/Vivaldi',port=9347,delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const child=execFile(browser,[`--remote-debugging-port=${port}`,'--headless=new','--hide-scrollbars',`--window-size=${mobile?'390,844':'1440,900'}`,'--force-device-scale-factor=1','--user-data-dir=/tmp/aeolia-about-qa','about:blank']);
try{
  let list;for(let i=0;i<40;i++){try{list=await fetch(`http://127.0.0.1:${port}/json`).then(r=>r.json());break}catch{await delay(250)}}
  if(!list)throw new Error('headless browser did not start');
  const socket=new WebSocket(list.find(x=>x.type==='page').webSocketDebuggerUrl);await once(socket,'open');let id=0;const pending=new Map();
  socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const call=++id;pending.set(call,m=>m.error?reject(new Error(m.error.message)):resolve(m.result));socket.send(JSON.stringify({id:call,method,params}))});
  await send('Page.navigate',{url:'http://localhost:8767/about.html?v=qa4'});await delay(2500);
  for(const [name,selector] of mobile?[['mobile-characters','#characters'],['mobile-bugs','#bugs'],['mobile-final','.final']]:[['top','body'],['process','#process'],['bugs','#bugs'],['final','.final']]){
    await send('Runtime.evaluate',{expression:`document.querySelector('${selector}').scrollIntoView()`});await delay(350);const {data}=await send('Page.captureScreenshot',{format:'jpeg',quality:86,fromSurface:true,captureBeyondViewport:false});await writeFile(`/tmp/aeolia-about-${name}.jpg`,Buffer.from(data,'base64'));console.log(name);
  }
  socket.close();
}finally{child.kill('SIGTERM')}
