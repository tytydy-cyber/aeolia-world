import assert from 'node:assert/strict';
import {statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const file='playroom/playroom-floor-modules.glb',bytes=statSync(new URL('../outputs/assets/'+file,import.meta.url)).size;
assert.ok(bytes<=2_000_000,'floor kit GLB stays at or under 2 MB');
const gltf=await loadHouse(file);gltf.scene.updateMatrixWorld(true);

const names=['RainbowWallJoin','CloudCarpet','SoftMeadowBerm','PaddedFenceIsland'];
const modules=names.map(name=>{const node=gltf.scene.getObjectByName(name);assert.ok(node,`${name} node exists`);return node});
const vertices=node=>{const out=[];node.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position;for(let i=0;i<p.count;i++)out.push(new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld))});return out};
const [join,carpet,berm,island]=modules.map(vertices);
for(const [i,v] of [join,carpet,berm,island].entries())assert.ok(Math.abs(Math.min(...v.map(p=>p.y))+.01)<1e-4,`${names[i]} bottom sits 1 cm below its origin`);

// The joins hug the rainbow (outer band radius 6.38) without entering its opening, and stand on both sides.
assert.ok(!join.some(p=>Math.hypot(p.x,p.y)<6.15),'wall joins leave the rainbow opening clear');
assert.ok(join.some(p=>p.x<-10.9)&&join.some(p=>p.x>10.9),'wall joins reach out to both sides');
const top=v=>Math.max(...v.map(p=>p.y));
assert.ok(top(carpet)>=.07&&top(carpet)<=.15,'cloud carpet is 8–16 cm thick');
assert.ok(top(berm)>=.25&&top(berm)<=.65,'meadow berm crest is 25–65 cm high');
assert.ok(top(island)<1.1,'fence island stays low enough to see over');

// Colours come from the murals: faded blue, meadow green, cream and faded coral.
const palette=[[160,182,196],[146,160,118],[226,212,182],[196,128,112]].map(([r,g,b])=>new THREE.Color().setRGB(r/255,g/255,b/255,THREE.SRGBColorSpace));
const materials=new Map();gltf.scene.traverse(o=>{if(o.isMesh)materials.set(o.material.name,o.material)});
assert.ok(materials.size<=6,'at most six materials');
for(const [name,m] of materials)assert.ok(palette.some(c=>Math.abs(c.r-m.color.r)+Math.abs(c.g-m.color.g)+Math.abs(c.b-m.color.b)<.03),`${name} uses a mural colour`);
for(const c of palette)assert.ok([...materials.values()].some(m=>Math.abs(c.r-m.color.r)+Math.abs(c.g-m.color.g)+Math.abs(c.b-m.color.b)<.03),'every mural colour is used');

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
console.log(`${file}: ${bytes} bytes, ${tris.length} triangles, ${materials.size} materials`);
console.log('PASS: playroom floor kit — four named modules sunk 1 cm, clear rainbow opening, carpet and berm heights, mural colours, no degenerate, duplicate or coplanar-overlapping faces.');
