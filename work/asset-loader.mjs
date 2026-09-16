import {readFileSync} from 'node:fs';

// Import the exact browser loader against the same pinned Three.js core in Node.
const core=new URL('./three.core.mjs',import.meta.url).href;
const dataURL=source=>'data:text/javascript;base64,'+Buffer.from(source).toString('base64');
const read=name=>readFileSync(new URL(name,import.meta.url),'utf8').replaceAll("from 'three'",`from '${core}'`);
const utils=dataURL(read('./BufferGeometryUtils.js'));
const skeleton=dataURL(read('./SkeletonUtils.js'));
const source=read('./GLTFLoader.js').replace("'../utils/BufferGeometryUtils.js'",JSON.stringify(utils)).replace("'../utils/SkeletonUtils.js'",JSON.stringify(skeleton));
const {GLTFLoader}=await import(dataURL(source));
export async function loadHouse(){
  const bytes=readFileSync(new URL('../outputs/assets/aeolia-house.glb',import.meta.url));
  return new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
}
