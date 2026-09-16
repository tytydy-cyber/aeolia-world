const palettes={
  ember:{Coat:0x9f413b,Mantle:0x642f35,Scarf:0xe1b967,Leather:0x72513d},
  mist:{Coat:0x527b83,Mantle:0x274c59,Scarf:0xd8ddd0,Leather:0x55463d},
  lilac:{Coat:0x756183,Mantle:0x433750,Scarf:0xe4b7c8,Leather:0x60483e}
};

function part(THREE,geometry,material,x,y,z,parent){const o=new THREE.Mesh(geometry,material);o.position.set(x,y,z);o.castShadow=true;parent.add(o);return o}

function buildVariants(THREE,player){
  const mist=new THREE.Group(),lilac=new THREE.Group();player.add(mist,lilac);
  const mistCloth=new THREE.MeshStandardMaterial({color:0x527b83,roughness:.9}),mistDark=new THREE.MeshStandardMaterial({color:0x274c59,roughness:.88}),glass=new THREE.MeshPhysicalMaterial({color:0xb9e5e3,metalness:.25,roughness:.18,transmission:.25});
  const hood=part(THREE,new THREE.SphereGeometry(.58,28,18,0,Math.PI*2,0,2.28),mistCloth,0,3.08,-.08,mist);hood.scale.set(1.08,1.06,.94);
  for(const side of [-1,1]){const lens=part(THREE,new THREE.TorusGeometry(.15,.035,8,22),glass,side*.18,3.1,.5,mist);lens.rotation.x=Math.PI/2}
  part(THREE,new THREE.BoxGeometry(.22,.065,.08),mistDark,0,3.1,.48,mist);
  const cape=part(THREE,new THREE.PlaneGeometry(1.35,2.25,4,10),mistCloth,0,1.9,-.55,mist);cape.material.side=THREE.DoubleSide;
  part(THREE,new THREE.BoxGeometry(.9,1.05,.38),mistDark,0,1.9,-.55,mist);
  for(const side of [-1,1]){const tank=part(THREE,new THREE.CylinderGeometry(.12,.15,1.15,12),glass,side*.32,1.95,-.81,mist);tank.rotation.z=.05*side;const fin=part(THREE,new THREE.BoxGeometry(.15,.8,.05),mistCloth,side*.58,1.75,-.62,mist);fin.rotation.z=-side*.38}

  const lilacCloth=new THREE.MeshStandardMaterial({color:0x756183,roughness:.93}),lilacDark=new THREE.MeshStandardMaterial({color:0x433750,roughness:.92}),light=new THREE.MeshStandardMaterial({color:0xf1cad8,emissive:0xc46d9d,emissiveIntensity:1.1,roughness:.3});
  const mantle=part(THREE,new THREE.SphereGeometry(.86,28,18,0,Math.PI*2,0,1.35),lilacCloth,0,2.46,0,lilac);mantle.scale.set(1,.55,.8);
  const hoodCone=part(THREE,new THREE.ConeGeometry(.53,1.45,28),lilacDark,0,3.72,-.05,lilac);hoodCone.rotation.z=-.12;
  const halo=part(THREE,new THREE.TorusGeometry(.72,.035,8,40),light,0,3.65,-.08,lilac);halo.rotation.x=Math.PI/2;
  const veil=part(THREE,new THREE.PlaneGeometry(1.18,2.5,4,12),lilacCloth,.12,1.85,-.6,lilac);veil.material.side=THREE.DoubleSide;veil.rotation.z=-.12;
  const lantern=part(THREE,new THREE.SphereGeometry(.2,18,12),light,.82,1.72,.12,lilac);part(THREE,new THREE.TorusGeometry(.24,.025,6,18,Math.PI),lilacDark,.82,2.02,.12,lilac).rotation.x=Math.PI/2;
  return {mist,lilac};
}

export function applyTravelerDesign(THREE,player,model,name='ember'){
  const style=palettes[name]||palettes.ember,variants=player.userData.designVariants??=buildVariants(THREE,player);
  variants.mist.visible=name==='mist';variants.lilac.visible=name==='lilac';
  model?.traverse(o=>{if(!o.isMesh)return;const objectName=o.name.toLowerCase().replace(/[^a-z]/g,''),replaceClassic=name!=='ember'&&(objectName.includes('hat')||objectName.includes('satchel')||objectName.includes('scarf')),hideHair=name==='mist'&&objectName.includes('hair');o.visible=!replaceClassic&&!hideHair;const color=style[o.material.name];if(color!==undefined)o.material.color.setHex(color)});
  return style;
}

export {palettes};
