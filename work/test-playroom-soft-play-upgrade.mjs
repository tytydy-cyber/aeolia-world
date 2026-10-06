import assert from 'node:assert/strict';
import {statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const file='playroom/playroom-soft-play-upgrade.glb',bytes=statSync(new URL('../outputs/assets/'+file,import.meta.url)).size;
assert.ok(bytes<=2_000_000,'soft play GLB stays at or under 2 MB');
const gltf=await loadHouse(file);gltf.scene.updateMatrixWorld(true);
const names=['SoftSlideTower','RoundedBallPit'];
const modules=names.map(name=>{const node=gltf.scene.getObjectByName(name);assert.ok(node,`${name} node exists`);return node});
const triangles=node=>{const out=[];node.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;for(let i=0;i<count;i+=3)out.push([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)))});return out};
const sets=modules.map(triangles),box=t=>new THREE.Box3().setFromPoints(t.flat());

// Both fit inside the assets they replace, so the existing placements, colliders and walkways still hold.
for(const [i,old] of ['playroom/playroom-slide.glb','playroom/playroom-ball-pit.glb'].entries()){
  const previous=await loadHouse(old);previous.scene.updateMatrixWorld(true);
  const was=new THREE.Box3().setFromObject(previous.scene,true).expandByScalar(.02),now=box(sets[i]);
  assert.ok(was.containsBox(now),`${names[i]} stays within the bounds of ${old}`);
  assert.ok(Math.abs(now.min.y+.01)<1e-4,`${names[i]} sinks 1 cm into the floor`);
}
// The slide keeps a passage under its deck at least 2 m wide at its game scale of 1.5 (3.45 m here).
const passage=new THREE.Box3(new THREE.Vector3(-1.15,0,-.8),new THREE.Vector3(1.15,2.4,.8));
assert.ok(!sets[0].some(t=>passage.intersectsTriangle(new THREE.Triangle(...t))),'a passage under the slide deck stays clear');
// The pit's soft floor is about 14 × 10 m at its game scale of 2.2, and the walls rise no higher than the old rim.
const inner=box(sets[1].filter(t=>t.every(v=>v.y>.13&&v.y<.15)));
assert.ok(inner.max.x-inner.min.x>6.3&&inner.max.z-inner.min.z>4.2,'the pit keeps its inner size');
const balls=sets[1].filter(t=>t.some(v=>v.y>.2)&&t.every(v=>Math.abs(v.x)<3.36&&Math.abs(v.z)<2.33)).length;
assert.ok(balls>10_000,'the pit holds a deep layer of balls');

// Faded coral, cream, dull blue and meadow green only, nothing saturated like a primary colour.
const palette=['#c48070','#e2d4b6','#708aa0','#92a076'].map(h=>new THREE.Color(h));
const materials=new Map();gltf.scene.traverse(o=>{if(o.isMesh)materials.set(o.material.name,o.material)});
assert.ok(materials.size<=6,'at most six materials');
for(const [name,m] of materials){
  assert.ok(palette.some(c=>Math.abs(c.r-m.color.r)+Math.abs(c.g-m.color.g)+Math.abs(c.b-m.color.b)<.03),`${name} uses the soft palette`);
  const hsl=m.color.clone().convertLinearToSRGB().getHSL({});assert.ok(hsl.s<.55,`${name} is not a primary colour`);
}
for(const c of palette)assert.ok([...materials.values()].some(m=>Math.abs(c.r-m.color.r)+Math.abs(c.g-m.color.g)+Math.abs(c.b-m.color.b)<.03),'every palette colour is used');

// Closed solids with outward normals: each module encloses positive volume.
for(const [i,t] of sets.entries()){const volume=t.reduce((sum,[a,b,c])=>sum+a.dot(b.clone().cross(c))/6,0);assert.ok(volume>0,`${names[i]} faces outward (volume ${volume.toFixed(2)})`)}

// No degenerate, duplicate or overlapping coplanar triangles within a module (modules share the origin).
const tris=[];
modules.forEach((node,module)=>node.traverse(o=>{
  if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;
  for(let i=0;i<count;i+=3)tris.push(Object.assign([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)),{module}));
}));
assert.ok(tris.length<=35_000,`${tris.length} triangles within 35k`);
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
console.log(`${file}: ${bytes} bytes, ${tris.length} triangles, ${materials.size} materials, ${names.map((n,i)=>n+' '+box(sets[i]).getSize(new THREE.Vector3()).toArray().map(x=>x.toFixed(2)).join('×')).join(', ')}`);
console.log('PASS: playroom soft play — named nodes inside the old bounds, sunk 1 cm, slide passage, pit size and ball layer, soft palette, outward solids, no degenerate, duplicate or coplanar-overlapping faces.');
