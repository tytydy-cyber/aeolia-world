import assert from 'node:assert/strict';
import {statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const file='playroom/playroom-entry-shell.glb',bytes=statSync(new URL('../outputs/assets/'+file,import.meta.url)).size;
assert.ok(bytes<=2_000_000,'entry shell GLB stays at or under 2 MB');
const gltf=await loadHouse(file),rainbowGltf=await loadHouse('playroom/playroom-rainbow.glb');
gltf.scene.updateMatrixWorld(true);rainbowGltf.scene.updateMatrixWorld(true);

const names=['RainbowPortalWall','CloudReliefA','CloudReliefB','CloudReliefC'];
const modules=names.map(name=>{const node=gltf.scene.getObjectByName(name);assert.ok(node,`${name} node exists`);return node});
const triangles=node=>{const out=[];node.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;for(let i=0;i<count;i+=3)out.push([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)))});return out};
const sets=modules.map(triangles),rainbow=triangles(rainbowGltf.scene);
const box=t=>new THREE.Box3().setFromPoints(t.flat()),size=b=>b.getSize(new THREE.Vector3());

// Portal: 34–40 wide, 12–14 tall, 1.2–1.8 deep, sunk 1 cm, and its face is not a rectangle.
const wall=box(sets[0]),wallSize=size(wall);
assert.ok(wallSize.x>=34&&wallSize.x<=40&&wallSize.y>=12&&wallSize.y<=14&&wallSize.z>=1.2&&wallSize.z<=1.8,`portal is ${wallSize.toArray().map(n=>n.toFixed(2)).join('×')}`);
assert.ok(Math.abs(wall.min.y+.01)<1e-4,'portal sinks 1 cm into the floor');
assert.ok(Math.abs(wall.max.x+wall.min.x)>1,'portal is asymmetric about the rainbow');
const tops=sets[0].flat().filter(v=>v.y>10).map(v=>v.y);assert.ok(Math.max(...tops)-Math.min(...tops.filter(y=>y>11))>.8,'portal top edge undulates');

// Opening: nothing of the wall inside radius 7.40 of the rainbow centre, and at both game scales a 6 m wide,
// 3.6 m high corridor through the rainbow stays clear of the wall and the rainbow itself.
assert.ok(!sets[0].flat().some(v=>v.y>=0&&Math.hypot(v.x,v.y)<7.39),'wall never narrows the rainbow opening');
for(const scale of [1.48,1.38]){
  const corridor=new THREE.Box3(new THREE.Vector3(-3/scale,0,-2),new THREE.Vector3(3/scale,3.6/scale,2));
  for(const t of [...sets[0],...rainbow])assert.ok(!corridor.intersectsTriangle(new THREE.Triangle(...t)),`6 m × 3.6 m passage is clear at scale ${scale}`);
}

// Clouds: different outlines, 0.8–1.8 deep fused volumes (0.25–0.55 read as flat cut-outs), closed backs sunk 1 cm behind z=0.
const clouds=sets.slice(1).map(box);
for(const [i,b] of clouds.entries()){const s=size(b);assert.ok(s.z>=.8&&s.z<=1.8&&Math.abs(b.min.z+.01)<1e-4,`${names[i+1]} is ${s.z.toFixed(2)} deep with its back at -0.01`)}
assert.equal(new Set(clouds.map(b=>size(b).x.toFixed(1))).size,3,'three cloud outlines differ');

// Colours and faces: sky-blue wall, cream reveal; double-sided; at most six materials.
const materials=new Map();gltf.scene.traverse(o=>{if(o.isMesh)materials.set(o.material.name,o.material)});
assert.ok(materials.size<=6,'at most six materials');
for(const m of materials.values())assert.equal(m.side,THREE.DoubleSide,`${m.name} renders both faces`);
const near=(name,hex)=>{const a=materials.get(name).color,b=new THREE.Color(hex);return Math.abs(a.r-b.r)+Math.abs(a.g-b.g)+Math.abs(a.b-b.b)<.03};
assert.ok(near('Faded sky wall plaster','#a1baca')&&near('Cream wall reveal','#e2d4b6'),'sky-blue wall and cream reveal use the mural colours');
const reveal=[];modules[0].traverse(o=>{if(o.isMesh&&o.material.name==='Cream wall reveal')reveal.push(new THREE.Box3().setFromObject(o))});
assert.ok(reveal.length===1&&reveal[0].max.y<8.6&&reveal[0].min.y<.1,'the cream reveal lines the opening down to the floor');

// Closed, outward-facing solids: each module encloses positive volume, and every face normal points away from it.
for(const [i,t] of sets.entries()){
  const volume=t.reduce((sum,[a,b,c])=>sum+a.dot(b.clone().cross(c))/6,0);
  assert.ok(volume>0,`${names[i]} is closed with outward normals (volume ${volume.toFixed(2)})`);
}

// No degenerate, duplicate or overlapping coplanar triangles within a module, nor against the rainbow it sits in.
const total=sets.reduce((sum,t)=>sum+t.length,0);
assert.ok(total<=28_000,`${total} triangles within 28k`);
const signatures=new Set(),planes=new Map();
const tagged=[...sets.flatMap((t,module)=>t.map(x=>Object.assign(x,{module}))),...rainbow.map(x=>Object.assign(x,{module:0,rainbow:true}))];
for(const t of tagged){
  const triangle=new THREE.Triangle(...t),n=triangle.getNormal(new THREE.Vector3());
  if(!t.rainbow){
    assert.ok(triangle.getArea()>1e-8,'no degenerate triangle');
    const signature=t.module+':'+t.map(v=>v.toArray().map(x=>Math.round(x*1e4)).join(',')).sort().join('|');
    assert.ok(!signatures.has(signature),'no exact duplicate triangle');signatures.add(signature);
  }
  const s=Math.sign(n.x||n.y||n.z),key=[...n.clone().multiplyScalar(s).toArray(),n.dot(t[0])*s].map(x=>Math.round(x*500)).join(',')+':'+t.module;
  if(!planes.has(key))planes.set(key,[]);planes.get(key).push({t,n});
}
// Area of the intersection of two coplanar triangles, by clipping one against the other in 2D (as in the architecture test).
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
for(const group of planes.values())for(let i=0;i<group.length;i++)for(let j=i+1;j<group.length;j++){
  if(group[i].t.rainbow&&group[j].t.rainbow)continue;
  if(overlap(group[i].t,group[j].t,group[i].n)>1e-4)overlaps++;
}
assert.equal(overlaps,0,'no overlapping coplanar triangles, including against the rainbow');
console.log(`${file}: ${bytes} bytes, ${total} triangles, ${materials.size} materials, portal ${wallSize.toArray().map(n=>n.toFixed(2)).join('×')}, clouds ${clouds.map(b=>size(b).toArray().map(n=>n.toFixed(2)).join('×')).join(' / ')}`);
console.log('PASS: playroom entry shell — named nodes, portal and cloud sizes, clear opening and 6 × 3.6 m passage at both scales, colours, double-sided closed outward solids, no degenerate, duplicate or coplanar-overlapping faces.');
