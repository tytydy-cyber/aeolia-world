import assert from 'node:assert/strict';
import {statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const file='playroom/playroom-playground-v2.glb',bytes=statSync(new URL('../outputs/assets/'+file,import.meta.url)).size;
assert.ok(bytes<=1_500_000,'playground v2 GLB stays at or under 1.5 MB');
const gltf=await loadHouse(file);gltf.scene.updateMatrixWorld(true);
const names=['PlaygroundTowerV2','PlaygroundNetV2','PlaygroundSoftClusterV2'];
const modules=names.map(name=>{const node=gltf.scene.getObjectByName(name);assert.ok(node,`${name} node exists`);return node});
const triangles=node=>{const out=[];node.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;for(let i=0;i<count;i+=3)out.push([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)))});return out};
const sets=modules.map(triangles),box=t=>new THREE.Box3().setFromPoints(t.flat()),size=t=>box(t).getSize(new THREE.Vector3());

for(const [i,t] of sets.entries()){
  const b=box(t);
  assert.ok(Math.abs(b.min.y+.01)<1e-4,`${names[i]} sinks 1 cm`);
  assert.ok(b.getCenter(new THREE.Vector3()).setY(0).length()<1.5,`${names[i]} is centred on its origin`);
}
const [tower,netSize,soft]=sets.map(size);
assert.ok(tower.x<=24&&tower.z<=11&&tower.y>=7,`tower ${tower.x.toFixed(2)} × ${tower.y.toFixed(2)} × ${tower.z.toFixed(2)} m`);
assert.ok(netSize.z>=.8,'the net bellies out instead of being a flat panel');
assert.ok(soft.y>=1.5*3.6&&soft.y<=3*3.6&&soft.x<=11,`soft cluster ${soft.x.toFixed(2)} × ${soft.y.toFixed(2)} m is 1.5–3 traveler heights`);

// A clear 4 m wide x 4.2 m high passage runs through the tower along Z at x=0; the tunnel only crosses above it.
const passage=new THREE.Box3(new THREE.Vector3(-2,0,-20),new THREE.Vector3(2,4.2,20));
assert.equal(sets[0].filter(t=>passage.intersectsTriangle(new THREE.Triangle(...t))).length,0,'nothing intrudes into the central passage');
assert.ok(sets[0].some(t=>t.every(v=>Math.abs(v.x)<2&&v.y>4.2)),'the tunnel spans the passage overhead');

// Not mirror-symmetric: few tower vertices have a mirror partner across x=0 (or across the bounding-box centre).
const cell=v=>[v.x,v.y,v.z].map(n=>Math.round(n*5)).join(',');
for(const cx of [0,box(sets[0]).getCenter(new THREE.Vector3()).x]){
  const points=sets[0].flat(),cells=new Set(points.map(cell));
  const mirrored=points.filter(v=>cells.has(cell(new THREE.Vector3(2*cx-v.x,v.y,v.z)))).length/points.length;
  assert.ok(mirrored<.2,`tower is asymmetric about x=${cx.toFixed(2)} (${(mirrored*100).toFixed(1)}% mirrored)`);
}

// Faded blue, meadow green, faded yellow and coral, plus cream rope.
const palette=['#708aa0','#92a076','#e8cb8b','#c48070','#e2d4b6'].map(h=>new THREE.Color(h));
const materials=new Map();gltf.scene.traverse(o=>{if(o.isMesh)materials.set(o.material.name,o.material)});
assert.ok(materials.size<=5,'at most five materials');
const near=(c,m)=>Math.abs(c.r-m.color.r)+Math.abs(c.g-m.color.g)+Math.abs(c.b-m.color.b)<.03;
for(const [name,m] of materials)assert.ok(palette.some(c=>near(c,m)),`${name} uses the palette`);
for(const c of palette)assert.ok([...materials.values()].some(m=>near(c,m)),'every palette colour is used');
for(const [i,t] of sets.entries()){const volume=t.reduce((sum,[a,b,c])=>sum+a.dot(b.clone().cross(c))/6,0);assert.ok(volume>0,`${names[i]} faces outward (volume ${volume.toFixed(2)})`)}

// No degenerate, duplicate or overlapping coplanar triangles within a module (modules share the origin).
const tris=sets.flatMap((t,module)=>t.map(v=>Object.assign(v,{module})));
assert.ok(tris.length<=24_000,`${tris.length} triangles within 24k`);
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
console.log(`${file}: ${bytes} bytes, ${tris.length} triangles, ${materials.size} materials, ${names.map((n,i)=>n+' '+size(sets[i]).toArray().map(x=>x.toFixed(2)).join('×')+' ('+sets[i].length+' tri)').join(', ')}`);
console.log('PASS: playroom playground v2 — three named groups sunk 1 cm, clear central passage under the tunnel, asymmetric tower, bellied net, 1.5–3 traveler-high soft cluster, palette, outward solids, no degenerate, duplicate or coplanar-overlapping faces.');
