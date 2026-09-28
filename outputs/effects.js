// Fixed-size particle pools: two draw calls, no per-frame geometry allocations.
export class MotionEffects {
  constructor(THREE,scene,camera){
    this.THREE=THREE;this.camera=camera;this.enabled=!globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    this.dustClock=0;this.airClock=0;this.wasGrounded=true;this.time=0;this.flightBand=0;
    this.right=new THREE.Vector3();
    this.dust=this.pool(64,false,scene);this.air=this.pool(64,true,scene);
  }
  pool(count,line,scene){
    const T=this.THREE,vertices=count*(line?2:1),geometry=new T.BufferGeometry();
    const position=new Float32Array(vertices*3),alpha=new Float32Array(vertices),size=new Float32Array(vertices),tint=new Float32Array(vertices*3);
    for(let i=0;i<vertices;i++){size[i]=line?1:.42;tint.set(line?[.72,.9,1]:[.94,.72,.43],i*3)}
    for(const [name,array,itemSize] of [['position',position,3],['aAlpha',alpha,1],['aSize',size,1],['aTint',tint,3]])geometry.setAttribute(name,new T.BufferAttribute(array,itemSize).setUsage(T.DynamicDrawUsage));
    const vertexShader=`attribute float aAlpha;attribute float aSize;attribute vec3 aTint;
      varying float vAlpha;varying vec3 vTint;uniform float viewport;
      void main(){vec4 p=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*p;
      gl_PointSize=clamp(aSize*viewport/max(1.,-p.z),1.,60.);vAlpha=aAlpha;vTint=aTint;}`;
    const material=new T.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{viewport:{value:600}},vertexShader,
      fragmentShader:`varying float vAlpha;varying vec3 vTint;void main(){
      float fade=${line?'1.':'pow(max(0.,1.-length(gl_PointCoord-vec2(.5))*2.),2.)'};
      gl_FragColor=vec4(vTint,vAlpha*fade);}`});
    const object=line?new T.LineSegments(geometry,material):new T.Points(geometry,material);object.frustumCulled=false;scene.add(object);
    return {count,line,geometry,object,material,position,alpha,size,next:0,items:Array.from({length:count},()=>({age:99,life:0,x:0,y:0,z:0,vx:0,vy:0,vz:0,ex:0,ey:0,ez:0}))};
  }
  emit(pool,x,y,z,vx,vy,vz,life,length=0){
    const p=pool.items[pool.next];pool.next=(pool.next+1)%pool.count;
    Object.assign(p,{age:0,life,x,y,z,vx,vy,vz,ex:x-vx*length,ey:y-vy*length,ez:z-vz*length});
  }
  flightBurst(position,takeoff=true){
    if(!this.enabled)return;
    for(let i=0;i<24;i++){
      const a=i/24*Math.PI*2,speed=takeoff?5:3.2;
      this.emit(this.air,position.x+Math.cos(a)*.45,position.y+1.2,position.z+Math.sin(a)*.45,Math.cos(a)*speed,takeoff?1.8:-.6,Math.sin(a)*speed,.85,-1.25);
    }
    for(let i=0;i<16;i++){const a=i/16*Math.PI*2;this.emit(this.dust,position.x,position.y+.15,position.z,Math.cos(a)*2.4,.6+Math.random()*.5,Math.sin(a)*2.4,1)}
  }
  update(dt,position,velocity,flying,grounded){
    dt=Math.min(Math.max(dt,0),.05);
    this.time+=dt;
    const speed=Math.hypot(velocity.x,velocity.z),total=velocity.length();
    const allow=this.enabled;
    if(allow&&grounded&&!flying&&speed>1){
      this.dustClock+=dt*Math.min(speed,18);
      if(this.dustClock>1.05){
        this.dustClock%=1.05;
        for(let i=0;i<4;i++)this.emit(this.dust,position.x+(Math.random()-.5)*.75,position.y+.16,position.z+(Math.random()-.5)*.75,-velocity.x*.045+(Math.random()-.5)*.55,.35+Math.random()*.4,-velocity.z*.045+(Math.random()-.5)*.55,.75+Math.random()*.45);
      }
    }else this.dustClock=0;
    if(allow&&grounded&&!flying&&!this.wasGrounded){
      for(let i=0;i<12;i++){const a=i/12*Math.PI*2;this.emit(this.dust,position.x,position.y+.12,position.z,Math.cos(a)*1.6,.5,Math.sin(a)*1.6,.7)}
    }
    const band=flying?(total>24?2:total>5?1:0):0;
    if(allow&&band>this.flightBand)for(let i=0;i<14;i++){const a=i/14*Math.PI*2;this.emit(this.air,position.x+Math.cos(a)*.7,position.y+1.5+Math.sin(a*2)*.25,position.z+Math.sin(a)*.7,Math.cos(a)*3,Math.sin(a*2)*1.2,Math.sin(a)*3,.72,-.8)}
    this.flightBand=band;
    if(allow&&flying&&total>2){
      this.airClock+=dt;
      const interval=total>24?.018:.04;
      if(this.airClock>interval){
        this.airClock%=interval;this.right.set(1,0,0).applyQuaternion(this.camera.quaternion);
        const streams=total>24?3:2;
        for(let lane=0;lane<streams;lane++)for(const side of [-1,1]){
          const offset=.55+lane*.42+Math.sin(this.time*7+lane)*.12,flutter=Math.sin(this.time*11+side*lane)*.7;
          const x=position.x+this.right.x*side*offset,y=position.y+1.35+lane*.32+flutter*.15,z=position.z+this.right.z*side*offset;
          this.emit(this.air,x,y,z,-velocity.x*(.1+lane*.025)+this.right.x*flutter,-velocity.y*.14+flutter*.3,-velocity.z*(.1+lane*.025)+this.right.z*flutter,.48+lane*.12,-1.2-lane*.35);
        }
      }
    }else this.airClock=0;
    this.wasGrounded=grounded&&!flying;
    for(const pool of [this.dust,this.air]){
      pool.object.visible=allow;pool.material.uniforms.viewport.value=(globalThis.innerHeight||800)*Math.min(globalThis.devicePixelRatio||1,2)*.5;
      pool.items.forEach((p,i)=>{
        p.age+=dt;const active=allow&&p.age<p.life;const n=pool.line?i*2:i;
        const opacity=active?(1-p.age/p.life)*(pool.line?.68:.58):0;
        pool.alpha[n]=opacity;
        if(active){p.x+=p.vx*dt;p.y+=p.vy*dt;p.z+=p.vz*dt}
        pool.position.set([p.x,p.y,p.z],n*3);
        if(pool.line){pool.alpha[n+1]=opacity*.1;pool.position.set([p.ex,p.ey,p.ez],(n+1)*3)}
        else pool.size[n]=.46+p.age*.85;
      });
      for(const name of ['position','aAlpha','aSize'])pool.geometry.attributes[name].needsUpdate=true;
    }
  }
}
