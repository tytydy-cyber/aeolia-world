import assert from 'node:assert/strict';
import {statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const file='playroom/playroom-architecture.glb',bytes=statSync(new URL('../outputs/assets/'+file,import.meta.url)).size;
assert.ok(bytes<=2_000_000,'architecture GLB stays at or under 2 MB');
const gltf=await loadHouse(file);gltf.scene.updateMatrixWorld(true);

// Four modules, each fetched by node name, each standing at its own origin.
const modules=['ArchPassage','CloudNiche','WaveSoffit','PaddedColumn'].map(name=>{const node=gltf.scene.getObjectByName(name);assert.ok(node,`${name} node exists`);return node});
const size=node=>new THREE.Box3().setFromObject(node);
const [arch,niche,soffit,column]=modules.map(size);
assert.ok(Math.abs(arch.max.x-arch.min.x-11.2)<.5&&Math.abs(arch.max.y-7.4)<.3&&arch.min.y>-.01,'arch is about 11 m wide and 7.4 m tall on the floor');
assert.ok(soffit.max.y<=.06&&soffit.min.y<-1&&soffit.max.x-soffit.min.x>11.9,'soffit is a 12 m ceiling drop hanging below y=0');
assert.ok(Math.abs(column.max.y-6)<.01&&column.min.y>-.01,'column runs floor to 6 m');
assert.ok(niche.max.y<=5.05&&niche.min.z>-.01,'niche block stands on the floor and backs onto z=0');
const archVerts=[];modules[0].traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position;for(let i=0;i<p.count;i++)archVerts.push(new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld))});
// The opening is 8 m between straight jambs up to 3.6 m, then a basket arch to 6 m; allow 0.2 m for the rolled trim.
const inOpening=v=>v.y<3.6?Math.abs(v.x)<3.8:(v.x/3.8)**2+((v.y-3.6)/2.2)**2<1;
assert.ok(!archVerts.some(inOpening),'the arch opening stays clear about 8 m wide and 6 m high');

// Material names say what the surface is, and roughness and metalness agree with the name.
// The game groups by these names (soft / fabric / wall, plastic, steel), mirroring compactAsset in playroom.js.
const materials=new Map(),classes=new Set();
gltf.scene.traverse(o=>{if(o.isMesh)materials.set(o.material.name,o.material)});
assert.ok(materials.size<=6,'at most six materials');
for(const [name,m] of materials){
  if(/fabric|soft/i.test(name)){classes.add('fabric');assert.ok(m.roughness>=.85&&m.metalness===0,`${name} is matte fabric`)}
  else if(/painted|wall/i.test(name)){classes.add('paint');assert.ok(m.roughness>=.7&&m.metalness===0,`${name} is matte paint`)}
  else if(/steel|metal/i.test(name)){classes.add('metal');assert.ok(m.metalness>=.5&&m.roughness<=.5,`${name} is metal`)}
  else if(/plastic/i.test(name)){classes.add('plastic');assert.ok(m.roughness<=.6&&m.metalness===0,`${name} is glossy plastic`)}
  else if(/light/i.test(name))assert.ok(m.emissive.getHex()>0,`${name} glows`);
  else assert.fail(`${name} does not name its surface class`);
}
assert.deepEqual([...classes].sort(),['fabric','metal','paint','plastic'],'fabric, paint, plastic and metal are all present');

// No degenerate, duplicate or overlapping coplanar triangles anywhere in the kit.
// Modules share the GLB origin but are placed separately, so overlaps are only checked within one module.
const tris=[];
modules.forEach((node,module)=>node.traverse(o=>{
  if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;
  for(let i=0;i<count;i+=3)tris.push(Object.assign([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)),{module}));
}));
assert.ok(tris.length<=30_000,`${tris.length} triangles within 30k`);
const signatures=new Set(),planes=new Map();
for(const t of tris){
  const triangle=new THREE.Triangle(...t);assert.ok(triangle.getArea()>1e-8,'no degenerate triangle');
  const signature=t.module+':'+t.map(v=>v.toArray().map(n=>Math.round(n*1e4)).join(',')).sort().join('|');
  assert.ok(!signatures.has(signature),'no exact duplicate triangle');signatures.add(signature);
  const n=triangle.getNormal(new THREE.Vector3()),s=Math.sign(n.x||n.y||n.z),key=[...n.clone().multiplyScalar(s).toArray(),n.dot(t[0])*s].map(x=>Math.round(x*500)).join(',')+':'+t.module;
  if(!planes.has(key))planes.set(key,[]);planes.get(key).push({t,n});
}
// Area of the intersection of two coplanar triangles, by clipping one against the other in 2D.
function overlap(a,b,n){
  const axis=[Math.abs(n.x),Math.abs(n.y),Math.abs(n.z)],drop=axis.indexOf(Math.max(...axis)),flat=v=>v.toArray().filter((_,i)=>i!==drop);
  const area=poly=>poly.reduce((sum,p,i)=>{const q=poly[(i+1)%poly.length];return sum+p[0]*q[1]-q[0]*p[1]},0)/2;
  let clip=a.map(flat);const edge=b.map(flat);if(area(edge)<0)edge.reverse();
  for(let i=0;i<3&&clip.length;i++){
    const [p,q]=[edge[i],edge[(i+1)%3]],inside=v=>(q[0]-p[0])*(v[1]-p[1])-(q[1]-p[1])*(v[0]-p[0])>=0,next=[];
    clip.forEach((v,j)=>{const w=clip[(j+1)%clip.length];if(inside(v)){next.push(v);if(!inside(w))next.push(cross(v,w,p,q))}else if(inside(w))next.push(cross(v,w,p,q))});clip=next;
  }
  return clip.length>2?Math.abs(area(clip)):0;
}
function cross([x1,y1],[x2,y2],[x3,y3],[x4,y4]){const d=(x1-x2)*(y3-y4)-(y1-y2)*(x3-x4),t=((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))/d;return [x1+t*(x2-x1),y1+t*(y2-y1)]}
let overlaps=0;
for(const group of planes.values())for(let i=0;i<group.length;i++)for(let j=i+1;j<group.length;j++)if(overlap(group[i].t,group[j].t,group[i].n)>1e-4)overlaps++;
assert.equal(overlaps,0,'no overlapping coplanar triangles');
console.log(`${file}: ${bytes} bytes, ${tris.length} triangles, ${materials.size} materials`);
console.log('PASS: playroom architecture kit — four named modules, bounds, clear arch opening, named surface classes, no degenerate, duplicate or coplanar-overlapping faces.');
