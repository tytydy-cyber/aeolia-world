import assert from 'node:assert/strict';
import {statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const file='playroom/playroom-quiet-split.glb',bytes=statSync(new URL('../outputs/assets/'+file,import.meta.url)).size;
assert.ok(bytes<=1_500_000,'quiet split GLB stays at or under 1.5 MB');
const gltf=await loadHouse(file);gltf.scene.updateMatrixWorld(true);
const names=['NapRoomSet','BirthdayRoomSet'];
const modules=names.map(name=>{const node=gltf.scene.getObjectByName(name);assert.ok(node,`${name} node exists`);return node});
const triangles=node=>{const out=[];node.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;for(let i=0;i<count;i+=3)out.push([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)))});return out};
const sets=modules.map(triangles),box=t=>new THREE.Box3().setFromPoints(t.flat());

// Each set stands on its floor centre within 22 × 8 m, sinks 1 cm, and keeps a 3 m aisle clear to 3.6 m high.
const aisle=new THREE.Box3(new THREE.Vector3(-1.5,0,-4),new THREE.Vector3(1.5,3.6,4));
for(const [i,t] of sets.entries()){
  const b=box(t);
  assert.ok(b.min.x>=-11&&b.max.x<=11&&b.min.z>=-4&&b.max.z<=4,`${names[i]} fits in 22 × 8 m around its origin`);
  assert.ok(Math.abs(b.min.y+.01)<1e-4,`${names[i]} sinks 1 cm`);
  assert.ok(!t.some(x=>aisle.intersectsTriangle(new THREE.Triangle(...x))),`${names[i]} keeps the 3 m aisle clear`);
  assert.ok(b.min.x<-5&&b.max.x>5,`${names[i]} uses both sides of the aisle`);
}
// Sized for the 3.6 m traveler: nothing in the nap set taller than a low screen, table and chairs at a child's scale.
assert.ok(box(sets[0]).max.y<2.2,'nap furniture stays low');
const party=box(sets[1]),overAisle=sets[1].flat().filter(v=>Math.abs(v.x)<1.5);
assert.ok(party.max.y>4.4&&party.max.y<5.2&&Math.min(...overAisle.map(v=>v.y))>3.6,'a party arch spans the aisle above head height');

const materials=new Map();gltf.scene.traverse(o=>{if(o.isMesh)materials.set(o.material.name,o.material)});
assert.ok(materials.size<=6,'at most six materials');
for(const [i,t] of sets.entries()){const volume=t.reduce((sum,[a,b,c])=>sum+a.dot(b.clone().cross(c))/6,0);assert.ok(volume>0,`${names[i]} faces outward (volume ${volume.toFixed(2)})`)}

// No degenerate, duplicate or overlapping coplanar triangles within a module (modules share the origin).
const tris=[];
modules.forEach((node,module)=>node.traverse(o=>{
  if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;
  for(let i=0;i<count;i+=3)tris.push(Object.assign([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)),{module}));
}));
assert.ok(tris.length<=14_600,`${tris.length} triangles within 14,600`);
const signatures=new Set(),planes=new Map();
for(const t of tris){
  const triangle=new THREE.Triangle(...t);assert.ok(triangle.getArea()>1e-8,'no degenerate triangle');
  const signature=t.module+':'+t.map(v=>v.toArray().map(n=>Math.round(n*1e4)).join(',')).sort().join('|');
  assert.ok(!signatures.has(signature),'no exact duplicate triangle');signatures.add(signature);
  const n=triangle.getNormal(new THREE.Vector3()),s=Math.sign(n.x||n.y||n.z),key=[...n.clone().multiplyScalar(s).toArray(),n.dot(t[0])*s].map(x=>Math.round(x*500)).join(',')+':'+t.module;
  if(!planes.has(key))planes.set(key,[]);planes.get(key).push({t,n});
}
// Area of the intersection of two coplanar triangles, by clipping one against the other in 2D (same as the architecture test).
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
console.log(`${file}: ${bytes} bytes, ${tris.length} triangles, ${materials.size} materials, ${names.map((n,i)=>n+' '+box(sets[i]).getSize(new THREE.Vector3()).toArray().map(x=>x.toFixed(2)).join('×')+' ('+sets[i].length+' tri)').join(', ')}`);
console.log('PASS: playroom quiet split — two named sets within 22 × 8 m, sunk 1 cm, clear 3 m aisle, traveler-scale furniture, outward solids, no degenerate, duplicate or coplanar-overlapping faces.');
