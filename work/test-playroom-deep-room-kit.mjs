import assert from 'node:assert/strict';
import {statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const file='playroom/playroom-deep-room-kit.glb',bytes=statSync(new URL('../outputs/assets/'+file,import.meta.url)).size;
assert.ok(bytes<=1_500_000,'deep room kit GLB stays at or under 1.5 MB');
const gltf=await loadHouse(file);gltf.scene.updateMatrixWorld(true);
const names=['CloudCeilingCove','SoftWallAlcove','HangingCloudCluster'];
const modules=names.map(name=>{const node=gltf.scene.getObjectByName(name);assert.ok(node,`${name} node exists`);return node});
const triangles=node=>{const out=[];node.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;for(let i=0;i<count;i+=3)out.push([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)))});return out};
const sets=modules.map(triangles),box=t=>new THREE.Box3().setFromPoints(t.flat()),[cove,alcove,cluster]=sets.map(box);

// Ceiling pieces sink 5 cm into the ceiling and hang at most 6.4 m, so under the 16–20 m ceilings they stay
// above the 3.6 m walkway zone even at 1.5× (9.6 m drop leaves 6.4 m in a 16 m room).
for(const [i,b] of [[0,cove],[2,cluster]])assert.ok(Math.abs(b.max.y-.05)<1e-3&&b.min.y>=-6.4,`${names[i]} hangs from y=+0.05 to ${b.min.y.toFixed(2)}`);
assert.ok(cove.min.y>=-1.3,'the cove drops no more than 1.3 m');
// The cove's front edge swells into lobes instead of running straight like a beam.
const front=[];for(let x=-7.5;x<=7.5;x+=.5){const zs=sets[0].flat().filter(v=>Math.abs(v.x-x)<.06).map(v=>v.z);front.push(Math.max(...zs))}
assert.ok(Math.max(...front)-Math.min(...front)>.4,'cove front edge is lobed, not straight');
assert.ok(Math.abs(cove.min.z+.01)<1e-3&&Math.abs(alcove.min.z+.01)<1e-3,'cove and alcove backs sit 1 cm into the wall');

// The alcove is 1.2–1.8 m deep, stands on the floor and is closed at the back: a look straight in hits its back.
const alcoveDepth=alcove.max.z-alcove.min.z;
assert.ok(alcoveDepth>=1.2&&alcoveDepth<=1.8&&Math.abs(alcove.min.y+.01)<1e-4,`alcove is ${alcoveDepth.toFixed(2)} m deep and sinks 1 cm`);
const hit=new THREE.Raycaster(new THREE.Vector3(-.3,1.6,3),new THREE.Vector3(0,0,-1)).intersectObject(modules[1],true)[0];
assert.ok(hit&&hit.point.z>0&&hit.point.z<1.0,'the recess is closed at the back, not a passage');
const recess=[];modules[1].traverse(o=>{if(!o.isMesh||o.material.name!=='Dull blue wall recess')return;const p=o.geometry.attributes.position;for(let i=0;i<p.count;i++)recess.push(new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld))});
const side=sign=>Math.max(...recess.filter(v=>Math.sign(v.x+.3)===sign&&Math.abs(v.x+.3)>1).map(v=>v.y));
assert.ok(side(1)-side(-1)>.2,'the recess arch rises higher on the right: the alcove is asymmetric');

// The cluster is three to five clouds, each thick from every side.
const clouds=[];modules[2].traverse(o=>{if(o.isMesh&&/^Cloud_\d/.test(o.name))clouds.push(new THREE.Box3().setFromObject(o))});
assert.ok(clouds.length>=3&&clouds.length<=5,`${clouds.length} hanging clouds`);
for(const b of clouds){const s=b.getSize(new THREE.Vector3());assert.ok(Math.min(s.x,s.y,s.z)>=.5,'each cloud is thick in every direction')}
assert.ok(new Set(clouds.map(b=>b.min.y.toFixed(1))).size===clouds.length,'clouds hang at different heights');

// Faded sky, cream, dull blue and faded coral only.
const palette=['#a1baca','#e2d4b6','#708aa0','#c48070'].map(h=>new THREE.Color(h));
const materials=new Map();gltf.scene.traverse(o=>{if(o.isMesh)materials.set(o.material.name,o.material)});
assert.ok(materials.size<=5,'at most five materials');
const near=(c,m)=>Math.abs(c.r-m.color.r)+Math.abs(c.g-m.color.g)+Math.abs(c.b-m.color.b)<.03;
for(const [name,m] of materials)assert.ok(palette.some(c=>near(c,m)),`${name} uses the palette`);
for(const c of palette)assert.ok([...materials.values()].some(m=>near(c,m)),'every palette colour is used');

// Closed solids with outward normals.
for(const [i,t] of sets.entries()){const volume=t.reduce((sum,[a,b,c])=>sum+a.dot(b.clone().cross(c))/6,0);assert.ok(volume>0,`${names[i]} faces outward (volume ${volume.toFixed(2)})`)}

// No degenerate, duplicate or overlapping coplanar triangles within a module (modules share the origin).
const tris=[];
modules.forEach((node,module)=>node.traverse(o=>{
  if(!o.isMesh)return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;
  for(let i=0;i<count;i+=3)tris.push(Object.assign([0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld)),{module}));
}));
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
console.log(`${file}: ${bytes} bytes, ${tris.length} triangles, ${materials.size} materials, ${names.map((n,i)=>n+' '+box(sets[i]).getSize(new THREE.Vector3()).toArray().map(x=>x.toFixed(2)).join('×')).join(', ')}`);
console.log('PASS: playroom deep room kit — named nodes, ceiling sink and drop, lobed cove, closed asymmetric alcove, thick hanging clouds, palette, outward solids, no degenerate, duplicate or coplanar-overlapping faces.');
