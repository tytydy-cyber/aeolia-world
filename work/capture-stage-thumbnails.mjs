import {execFile} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {once} from 'node:events';

const browser='/Applications/Vivaldi.app/Contents/MacOS/Vivaldi';
const port=9338;
const root='http://localhost:8767/';
const shots=[
  ['floating-islands.jpg','aeolia.html',0],
  ['closed-complex.jpg','liminal.html?stage=parallax',0],
  ['solarpunk-suburb.jpg','liminal.html?stage=somnia',2600],
  ['dreamcore-playroom.jpg','playroom.html?debug=1&view=playground',0]
];
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const child=execFile(browser,[`--remote-debugging-port=${port}`,'--headless=new','--hide-scrollbars','--window-size=1280,720','--force-device-scale-factor=1','--user-data-dir=/tmp/aeolia-thumbnail-browser','about:blank']);

try{
  let list;
  for(let i=0;i<40;i++){
    try{list=await fetch(`http://127.0.0.1:${port}/json`).then(response=>response.json());break}catch{await delay(250)}
  }
  if(!list)throw new Error('headless browser did not start');
  const page=list.find(target=>target.type==='page');
  const socket=new WebSocket(page.webSocketDebuggerUrl);
  await once(socket,'open');
  let id=0;
  const pending=new Map();
  socket.onmessage=event=>{const message=JSON.parse(event.data);if(message.id&&pending.has(message.id)){pending.get(message.id)(message);pending.delete(message.id)}};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const call=++id;pending.set(call,message=>message.error?reject(new Error(message.error.message)):resolve(message.result));socket.send(JSON.stringify({id:call,method,params}))});
  await mkdir(new URL('../outputs/assets/thumbnails/',import.meta.url),{recursive:true});
  for(const [file,path,travel] of shots){
    await send('Page.navigate',{url:root+path});
    await delay(7000);
    if(travel){
      await send('Runtime.evaluate',{expression:"document.querySelector('#enter')?.click()"});
      await send('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowUp',code:'ArrowUp',windowsVirtualKeyCode:38});
      await delay(travel);
      await send('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowUp',code:'ArrowUp',windowsVirtualKeyCode:38});
      await delay(900);
    }
    await send('Runtime.evaluate',{expression:`
      document.querySelector('#veil')?.remove();
      const style=document.createElement('style');
      style.textContent='body>*:not(canvas){display:none!important}';
      document.head.append(style);
    `});
    await delay(500);
    const {data}=await send('Page.captureScreenshot',{format:'jpeg',quality:88,fromSurface:true,captureBeyondViewport:false});
    await writeFile(new URL('../outputs/assets/thumbnails/'+file,import.meta.url),Buffer.from(data,'base64'));
    console.log(file);
  }
  socket.close();
}finally{
  child.kill('SIGTERM');
}
