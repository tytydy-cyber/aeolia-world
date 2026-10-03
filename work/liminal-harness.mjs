import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import * as Core from './three.core.mjs';
import {mergeGeometries} from './asset-loader.mjs';
import {WorldAudio} from '../outputs/audio.js';
import {MotionEffects} from '../outputs/effects.js';
import {applyTravelerDesign} from '../outputs/character-designs.js';
import {Emotes,EMOTE_KEYS} from '../outputs/emotes.js';

// Runs the actual liminal.js for one stage with only DOM, canvas and GPU mocked.
const source=readFileSync(new URL('../outputs/liminal.js',import.meta.url),'utf8').replace(/^import .*$/gm,'');
const canvas2d=()=>new Proxy({},{get:(target,key)=>key in target?target[key]:/^create.*Gradient$/.test(key)?()=>({addColorStop(){}}):()=>{},set:(target,key,value)=>{target[key]=value;return true}});
function element(tagName='DIV'){return {tagName,textContent:'',innerHTML:'',value:'',hidden:false,style:{},dataset:{},children:[],classList:{add(){},remove(){},toggle(){},contains(){return false}},events:new Map(),addEventListener(type,fn){if(!this.events.has(type))this.events.set(type,[]);this.events.get(type).push(fn)},setAttribute(){},getAttribute(){return null},focus(){},blur(){},setPointerCapture(){},remove(){},append(){},appendChild(){},prepend(){},querySelector(selector){this.found??=new Map();if(!this.found.has(selector))this.found.set(selector,element());return this.found.get(selector)},querySelectorAll(){return []},getContext:canvas2d,width:0,height:0}}
class Renderer{constructor(){this.domElement=element('CANVAS');this.shadowMap={};this.info={render:{calls:0,triangles:0}}}setPixelRatio(){}setSize(){}render(){}}
class TextureLoader{load(){return new Core.Texture()}}

export function loadStage(stage,{blockStorage=false,traveler=null}={}){
  // Only the traveler can be supplied (as a parsed glTF-like object); other assets stay unloaded.
  class GLTFLoader{load(url,callback){if(traveler&&url.includes('traveler'))callback(traveler)}}
  const listeners=new Map(),elements=new Map(),store=new Map();
  const document={body:element('BODY'),hidden:false,title:'',createElement:element,addEventListener(){},querySelector(s){if(!elements.has(s))elements.set(s,element(s==='#characterSelect'?'SELECT':'DIV'));return elements.get(s)},querySelectorAll(){return []}};
  const context=vm.createContext({THREE:{...Core,WebGLRenderer:Renderer,TextureLoader},GLTFLoader,mergeGeometries,Emotes,EMOTE_KEYS,WorldAudio,MotionEffects,applyTravelerDesign,document,location:{search:`?stage=${stage}`},URLSearchParams,localStorage:blockStorage?{getItem(){throw new Error('SecurityError')},setItem(){throw new Error('SecurityError')}}:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,String(v))},innerWidth:1280,innerHeight:800,devicePixelRatio:1,matchMedia(){return {matches:false}},addEventListener(type,fn){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(fn)},requestAnimationFrame(){},setTimeout(){},clearTimeout(){},console:{...console,assert(condition,message){assert.ok(condition,message)}},performance,Date});
  vm.runInContext(source,context);
  const run=s=>vm.runInContext(s,context);
  const dispatch=(type,values={})=>{const e={target:document.body,preventDefault(){},...values};for(const fn of listeners.get(type)||[])fn(e);return e};
  // Advance the game by `n` frames at `hz`, using the same 120 Hz sub-stepping as the page loop.
  // The clock keeps running across calls, like requestAnimationFrame time, so timed checks (discoveries every 500 ms) keep firing.
  let clock=0;
  const frames=(n=60,hz=60)=>{const steps=Math.ceil(120/hz);for(let i=0;i<n;i++){clock+=1000/hz;for(let j=0;j<steps;j++)run(`update(${1/hz/steps},${clock})`)}};
  const reset=(x,y,z)=>run(`resetKeys();started=true;yaw=0;pitch=.25;recenterYaw=null;player.position.set(${x},${y},${z});velocity.set(0,0,0)`);
  return {run,dispatch,frames,reset,elements};
}
