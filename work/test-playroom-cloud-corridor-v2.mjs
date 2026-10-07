import assert from 'node:assert/strict';
import {statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const file='playroom/playroom-cloud-corridor-v2.glb',bytes=statSync(new URL('../outputs/assets/'+file,import.meta.url)).size;
assert.ok(bytes<=2_000_000,'cloud corridor v2 GLB stays at or under 2 MB');
const gltf=await loadHouse(file);gltf.scene.updateMatrixWorld(true);
const names=['CloudCorridorShell','CloudFloorBanks','DistantCloudGate','FloatingCloudIslands'];
const modules=names.map(name=>{const node=gltf.scene.getObjectByName(name);assert.ok(node,`${name} node exists`);return node});
const triangles=node=>{const out=[];node.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;for(let i=0;i<count;i+=3)out.push([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)))});return out};
const sets=modules.map(triangles),box=t=>new THREE.Box3().setFromPoints(t.flat()),size=b=>b.getSize(new THREE.Vector3());
const hits=(b,t)=>t.some(x=>b.intersectsTriangle(new THREE.Triangle(...x)));

// Shell: at least 24 wide, 13 tall, 22 deep, sunk 1 cm, and nothing in the corridor's 8 × 6 m flight path
// or the 7 m × 3.6 m walkway over its whole length.
const shell=size(box(sets[0]));
assert.ok(shell.x>=24&&shell.y>=13&&shell.z>=22,`shell is ${shell.toArray().map(n=>n.toFixed(2)).join('×')}`);
for(const i of [0,1])assert.ok(Math.abs(box(sets[i]).min.y+.01)<1e-4||i===1,`${names[i]} sinks 1 cm`);
const flight=new THREE.Box3(new THREE.Vector3(-4,0,-11),new THREE.Vector3(4,6,11)),walk=new THREE.Box3(new THREE.Vector3(-3.5,0,-11),new THREE.Vector3(3.5,3.6,11));
for(const [i,t] of sets.entries())assert.ok(!hits(flight,t)&&!hits(walk,t),`${names[i]} keeps the flight path and walkway clear`);

// Floor banks sit on both sides, asymmetric, and leave most of the floor uncovered.
const banks=box(sets[1]),top=sign=>Math.max(...sets[1].flat().filter(v=>Math.sign(v.x)===sign).map(v=>v.y));
assert.ok(banks.min.x<-9&&banks.max.x>8&&Math.abs(top(-1)-top(1))>.5,'banks line both sides, higher on one side');
const footprint=sets[1].reduce((sum,[a,b,c])=>sum+Math.abs((b.x-a.x)*(c.z-a.z)-(c.x-a.x)*(b.z-a.z))/2,0)/2;
assert.ok(footprint<.5*shell.x*shell.z,'banks cover well under half the floor');

// Gate: at least two cloud arches stepping away beyond the far end, deep rather than a board.
const gate=box(sets[2]);assert.ok(gate.max.z<-11&&size(gate).z>5,'the gate layers recede beyond the corridor end');
const arches=new Set(sets[2].map(t=>Math.round(t[0].z/3)));assert.ok(arches.size>=2,'two or more gate layers');

// Islands: three named groups whose node sits at the group's centre; with ±1.5 m horizontal and ±0.5 m vertical drift
// each stays inside the shell, above the banks and out of the flight path, and is thick from every side.
const groups=['FloatingCloudIslandA','FloatingCloudIslandB','FloatingCloudIslandC'].map(n=>{const g=gltf.scene.getObjectByName(n);assert.ok(g,`${n} node exists`);return g});
const heights=new Set(),depths=new Set();
for(const g of groups){
  const b=box(triangles(g)),centre=b.getCenter(new THREE.Vector3()),origin=g.getWorldPosition(new THREE.Vector3());
  assert.ok(centre.distanceTo(origin)<.6,`${g.name} node sits at its centre`);
  const s=size(b);assert.ok(Math.min(s.x,s.y,s.z)>.8,`${g.name} is thick from every side`);
  const drift=b.clone().expandByVector(new THREE.Vector3(1.5,.5,1.5));
  assert.ok(!hits(drift,sets[0])&&!hits(drift,sets[1])&&!drift.intersectsBox(flight),`${g.name} drifts clear of the shell, banks and flight path`);
  heights.add(Math.round(origin.y));depths.add(Math.round(origin.z));
}
assert.ok(heights.size===3&&depths.size===3,'islands differ in height and depth');

// Faded sky, cream, pale grey-blue and a little coral; nothing pure white.
const palette=['#a1baca','#e2d4b6','#b0bec6','#c48070'].map(h=>new THREE.Color(h));
const materials=new Map();gltf.scene.traverse(o=>{if(o.isMesh)materials.set(o.material.name,o.material)});
assert.ok(materials.size<=6,'at most six materials');
const near=(c,m)=>Math.abs(c.r-m.color.r)+Math.abs(c.g-m.color.g)+Math.abs(c.b-m.color.b)<.03;
for(const [name,m] of materials){assert.ok(palette.some(c=>near(c,m)),`${name} uses the palette`);assert.ok(m.color.r+m.color.g+m.color.b<2.4,`${name} is not white`)}
for(const c of palette)assert.ok([...materials.values()].some(m=>near(c,m)),'every palette colour is used');

// Closed solids with outward normals.
for(const [i,t] of sets.entries()){const volume=t.reduce((sum,[a,b,c])=>sum+a.dot(b.clone().cross(c))/6,0);assert.ok(volume>0,`${names[i]} faces outward (volume ${volume.toFixed(2)})`)}

// No degenerate, duplicate or overlapping coplanar triangles within a module (modules share the origin).
const tris=[];
modules.forEach((node,module)=>node.traverse(o=>{
  if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;
  for(let i=0;i<count;i+=3)tris.push(Object.assign([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)),{module}));
}));
assert.ok(tris.length<=32_000,`${tris.length} triangles within 32k`);
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
console.log(`${file}: ${bytes} bytes, ${tris.length} triangles, ${materials.size} materials, ${names.map((n,i)=>n+' '+size(box(sets[i])).toArray().map(x=>x.toFixed(2)).join('×')).join(', ')}`);
console.log('PASS: playroom cloud corridor v2 — named nodes, shell size, clear flight path and walkway, uneven banks, layered gate, centred drifting islands, palette, outward solids, no degenerate, duplicate or coplanar-overlapping faces.');
