import assert from 'node:assert/strict';
import {readFileSync,statSync} from 'node:fs';
import * as THREE from './three.core.mjs';
import {loadHouse} from './asset-loader.mjs';

const assets=[
  'playroom/playroom-playground-pack.glb',
  'playroom/playroom-child-town-pack.glb',
  'playroom/playroom-quiet-rooms-pack.glb',
  'playroom/playroom-cloud-corridor-pack.glb',
];

for(const file of assets){
  const path=new URL('../outputs/assets/'+file,import.meta.url);
  assert.ok(statSync(path).size<3_000_000,`${file} stays under 3 MB`);
  const gltf=await loadHouse(file);gltf.scene.updateMatrixWorld(true);
  const box=new THREE.Box3().setFromObject(gltf.scene),size=box.getSize(new THREE.Vector3());
  assert.ok(size.x>.5&&size.y>.5&&size.z>.5&&Math.max(size.x,size.y,size.z)<40,`${file} has useful finite bounds`);
  let triangles=0;const materials=new Set(),faces=new Set();
  gltf.scene.traverse(mesh=>{
    if(!mesh.isMesh)return;
    const geometry=mesh.geometry,position=geometry.attributes.position,index=geometry.index;
    for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material])materials.add(material.name);
    const count=index?.count??position.count;triangles+=count/3;
    for(let i=0;i<count;i+=3){
      const points=[];
      for(let j=0;j<3;j++){
        const vertex=index?index.getX(i+j):i+j;
        points.push(new THREE.Vector3().fromBufferAttribute(position,vertex).applyMatrix4(mesh.matrixWorld));
      }
      const area=new THREE.Triangle(...points).getArea();assert.ok(area>1e-8,`${file} ${mesh.name} triangle ${i/3} is not degenerate`);
      const signature=points.map(v=>[v.x,v.y,v.z].map(n=>Math.round(n*10000)).join(',')).sort().join('|');
      assert.ok(!faces.has(signature),`${file} has no exact duplicate coplanar triangles`);faces.add(signature);
    }
  });
  assert.ok(triangles<150_000,`${file} stays below triangle budget`);
  assert.ok(materials.size<=10,`${file} uses at most ten materials`);
  // Surfaces read apart without textures: fabric has sheen, plastic a clear coat, everything else stays a standard material.
  const glb=readFileSync(path),json=JSON.parse(glb.subarray(20,20+glb.readUInt32LE(12)).toString());
  for(const {name,extensions={}} of json.materials){
    assert.equal(!!extensions.KHR_materials_sheen,/fabric/.test(name),`${file} ${name} sheen only on fabric`);
    assert.equal(!!extensions.KHR_materials_clearcoat,/plastic|vinyl/.test(name),`${file} ${name} clear coat only on plastic and vinyl`);
  }
  console.log(`${file}: ${statSync(path).size} bytes, ${triangles} triangles, ${materials.size} materials, bounds ${size.toArray().map(n=>n.toFixed(2)).join('×')}`);
}
assert.ok(readFileSync(new URL('../source/previews/playroom-zone-assets-preview.png',import.meta.url)).length>10_000,'overview preview exists');
console.log('PASS: four web GLBs parsed; size, triangles, materials, bounds, degenerate and duplicate faces, fabric sheen and plastic clear coat checked.');
