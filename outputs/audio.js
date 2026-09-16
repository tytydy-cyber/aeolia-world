// Browser-native synthesis: no downloads, audio service, or autoplay before a gesture.
export class WorldAudio {
  constructor(Context=globalThis.AudioContext||globalThis.webkitAudioContext){
    this.Context=Context;this.ctx=null;this.volume=.35;this.muted=false;this.paused=true;
    this.voices=new Set();this.distance=0;this.nextMix=0;this.nextChord=0;
  }
  async start(){
    if(!this.Context)return false;
    try{
      if(!this.ctx){
        this.ctx=new this.Context();const c=this.ctx;
        this.master=c.createGain();this.master.gain.value=0;
        this.limiter=c.createDynamicsCompressor();this.limiter.threshold.value=-6;this.limiter.knee.value=3;this.limiter.ratio.value=12;this.limiter.attack.value=.003;this.limiter.release.value=.25;
        this.master.connect(this.limiter);this.limiter.connect(c.destination);
        this.noise=c.createBuffer(2,c.sampleRate*3,c.sampleRate);
        for(let channel=0;channel<2;channel++){
          const data=this.noise.getChannelData(channel);let smooth=0;
          for(let i=0;i<data.length;i++){smooth=(smooth+(Math.random()*2-1)*.07)/1.07;data[i]=Math.tanh(smooth*2)}
        }
        this.wind=c.createBufferSource();this.wind.buffer=this.noise;this.wind.loop=true;
        this.filter=c.createBiquadFilter();this.filter.type='lowpass';this.filter.frequency.value=450;
        this.windGain=c.createGain();this.windGain.gain.value=.11;
        this.wind.connect(this.filter);this.filter.connect(this.windGain);this.windGain.connect(this.master);this.wind.start();
        this.musicGain=c.createGain();this.musicGain.gain.value=.055;this.musicFilter=c.createBiquadFilter();this.musicFilter.type='lowpass';this.musicFilter.frequency.value=900;
        this.musicGain.connect(this.musicFilter);this.musicFilter.connect(this.master);this.pads=[0,7,14].map((step,i)=>{const osc=c.createOscillator(),gain=c.createGain();osc.type=i===2?'sine':'triangle';osc.frequency.value=174.61*Math.pow(2,step/12);gain.gain.value=[.22,.13,.07][i];osc.connect(gain);gain.connect(this.musicGain);osc.start();return osc});
      }
      await this.ctx.resume();this.paused=false;this.applyVolume();return true;
    }catch(error){console.warn('Audio could not start',error);return false}
  }
  applyVolume(){
    if(this.ctx)this.master.gain.setTargetAtTime(this.muted||this.paused?0:this.volume,this.ctx.currentTime,.03);
  }
  setVolume(value){this.volume=Number.isFinite(value)?Math.max(0,Math.min(1,value)):.35;this.applyVolume()}
  setMuted(value){this.muted=Boolean(value);this.applyVolume()}
  pause(){
    this.paused=true;this.distance=0;this.applyVolume();
    if(this.ctx)this.ctx.suspend().catch(()=>{});
  }
  get audible(){return this.ctx?.state==='running'&&!this.paused&&!this.muted&&this.volume>0}
  voice(source,nodes){
    if(this.voices.size>=24){source.disconnect();nodes.forEach(n=>n.disconnect());return false}
    this.voices.add(source);
    source.onended=()=>{source.disconnect();nodes.forEach(n=>n.disconnect());this.voices.delete(source)};
    return true;
  }
  step(wood=false){
    if(!this.audible)return;
    const c=this.ctx,t=c.currentTime,source=c.createBufferSource(),filter=c.createBiquadFilter(),gain=c.createGain();
    source.buffer=this.noise;source.playbackRate.value=.8+Math.random()*.35;
    filter.type='lowpass';filter.frequency.value=wood?700:1800;
    gain.gain.setValueAtTime(.0001,t);gain.gain.linearRampToValueAtTime(wood?.21:.17,t+.006);gain.gain.exponentialRampToValueAtTime(.0001,t+.11);
    source.connect(filter);filter.connect(gain);gain.connect(this.master);
    if(this.voice(source,[filter,gain])){source.start(t,Math.random()*2);source.stop(t+.13)}
  }
  chime(){
    if(!this.audible)return;
    const c=this.ctx;
    for(const [note,delay] of [[392,0],[587.33,.24]])for(const [ratio,level] of [[1,.055],[2.76,.017],[5.4,.005]]){
      const t=c.currentTime+delay,osc=c.createOscillator(),gain=c.createGain();osc.type='sine';osc.frequency.value=note*ratio;
      gain.gain.setValueAtTime(.0001,t);gain.gain.linearRampToValueAtTime(level,t+.008);gain.gain.exponentialRampToValueAtTime(.0001,t+2.5/ratio);
      osc.connect(gain);gain.connect(this.master);
      if(this.voice(osc,[gain])){osc.start(t);osc.stop(t+2.5/ratio+.03)}
    }
  }
  flightCue(takeoff=true){
    if(!this.audible)return;
    const c=this.ctx,t=c.currentTime,osc=c.createOscillator(),gain=c.createGain();osc.type='sine';osc.frequency.setValueAtTime(takeoff?220:520,t);osc.frequency.exponentialRampToValueAtTime(takeoff?880:180,t+.55);gain.gain.setValueAtTime(.0001,t);gain.gain.linearRampToValueAtTime(.07,t+.025);gain.gain.exponentialRampToValueAtTime(.0001,t+.65);osc.connect(gain);gain.connect(this.master);if(this.voice(osc,[gain])){osc.start(t);osc.stop(t+.7)}
  }
  update(dt,speed,flying,grounded,onBridge){
    if(!this.audible){this.distance=0;return}
    const t=this.ctx.currentTime;
    if(t>=this.nextMix){
      const movement=Math.min(1,speed/35),breeze=.1+Math.sin(t*.31)*.025;
      this.windGain.gain.setTargetAtTime(breeze+(flying?.2*movement:.015*movement),t,.3);
      this.filter.frequency.setTargetAtTime(350+(flying?1100*movement:150),t,.3);this.nextMix=t+.05;
    }
    if(t>=this.nextChord){
      const roots=[174.61,146.83,196,164.81],root=roots[Math.floor(t/8)%roots.length];
      this.pads.forEach((osc,i)=>osc.frequency.setTargetAtTime(root*Math.pow(2,[0,7,14][i]/12),t,1.8));this.nextChord=t+8;
    }
    if(!flying&&grounded&&speed>.6){
      this.distance+=Math.min(dt,.05)*speed;
      // Keep steps in the same phase as the avatar's capped walking cycle.
      const stride=Math.max(2.1,speed*Math.PI/16.5);
      if(this.distance>=stride){this.distance%=stride;this.step(onBridge)}
    }else this.distance=0;
  }
}
