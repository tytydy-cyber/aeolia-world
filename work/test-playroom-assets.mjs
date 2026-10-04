import assert from 'node:assert/strict';
import {loadHouse} from './asset-loader.mjs';

const expected={
  'playroom/playroom-rainbow.glb':{root:'Rainbow_arch',triangles:1500,meshes:8},
  'playroom/playroom-slide.glb':{root:'Slide_tower',triangles:1800,meshes:20},
  'playroom/playroom-ball-pit.glb':{root:'Ball_pit',triangles:5600,meshes:10},
};
for(const [file,budget] of Object.entries(expected)){
  const asset=await loadHouse(file);let meshes=0,triangles=0;
  asset.scene.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3}});
  assert.deepEqual(asset.scene.children.map(o=>o.name),[budget.root],`${file} keeps one reusable root`);
  assert.ok(meshes<=budget.meshes&&triangles<=budget.triangles,`${file} stays inside its browser asset budget (${meshes} meshes, ${triangles} triangles)`);
}
console.log('PASS: rainbow arch, curved slide tower and sparse ball pit parse as independent budgeted GLBs.');
