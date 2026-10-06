import assert from 'node:assert/strict';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const expected={
  'playroom/playroom-rainbow.glb':{root:'Rainbow_arch',triangles:1700,meshes:8},
  'playroom/playroom-slide.glb':{root:'Slide_tower',triangles:1800,meshes:20},
  'playroom/playroom-ball-pit.glb':{root:'Ball_pit',triangles:5600,meshes:10},
};
for(const [file,budget] of Object.entries(expected)){
  const asset=await loadHouse(file);let meshes=0,triangles=0;
  asset.scene.updateMatrixWorld(true);const size=new THREE.Box3().setFromObject(asset.scene).getSize(new THREE.Vector3());
  asset.scene.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3}});
  assert.deepEqual(asset.scene.children.map(o=>o.name),[budget.root],`${file} keeps one reusable root`);
  assert.ok(meshes<=budget.meshes&&triangles<=budget.triangles,`${file} stays inside its browser asset budget (${meshes} meshes, ${triangles} triangles)`);
  if(file.includes('rainbow')){
    assert.ok(size.z>=1.89,`rainbow has a substantial back profile (${size.z.toFixed(2)}m)`);
    let caps=0;asset.scene.traverse(o=>{if(!o.isMesh||!/Rainbow_band/.test(o.name))return;const p=o.geometry.attributes.position,index=o.geometry.index,count=index?.count??p.count;let minRadius=Infinity,maxRadius=0;for(let i=0;i<p.count;i++){const v=new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld),r=Math.hypot(v.x,v.y);minRadius=Math.min(minRadius,r);maxRadius=Math.max(maxRadius,r)}assert.ok(minRadius>=4.79,'rainbow opening radius stays at least 4.8 m');assert.ok(maxRadius-minRadius>=.5,'rainbow bands keep visible radial thickness');for(let i=0;i<count;i+=3){const t=[0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld));if(Math.max(...t.map(v=>v.z))-Math.min(...t.map(v=>v.z))<1e-3&&t.every(v=>Math.abs(Math.abs(v.z)-.95)<1e-3)){caps++;const tri=new THREE.Triangle(...t),normal=tri.getNormal(new THREE.Vector3()),centroid=tri.getMidpoint(new THREE.Vector3());assert.ok(normal.z*centroid.z>0,'rainbow front and rear caps face outwards')}}});assert.ok(caps>=300,'both faces of all rainbow bands are closed');
  }
}
console.log('PASS: rainbow arch, curved slide tower and sparse ball pit parse as independent budgeted GLBs.');
