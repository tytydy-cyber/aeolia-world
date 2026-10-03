// Emotes play once over the flight loop, then hand it back. Shared by every stage.
export const EMOTE_KEYS={Digit1:'Wave',Digit2:'Bow',Digit3:'Spin'};
const IDLE_FIRST=12,IDLE_REPEAT=30;

export class Emotes{
  constructor(THREE){this.THREE=THREE;this.actions=null;this.active=null;this.idle=0;this.idleAfter=IDLE_FIRST}
  attach(mixer,actions){
    this.actions=actions;
    for(const name of Object.values(EMOTE_KEYS)){const action=actions[name];if(action){action.setLoop(this.THREE.LoopOnce,1);action.clampWhenFinished=true}}
    mixer.addEventListener('finished',e=>{if(this.active&&e.action===actions[this.active])this.active=null});
  }
  // Returns the clip to start, or null when the traveler model has no such clip or an emote is still playing.
  request(name){
    if(!this.actions?.[name]||this.active)return null;
    this.active=name;this.idle=0;return name;
  }
  // After a while without input or movement the traveler waves; later waves come less often.
  idleTick(dt,busy){
    if(busy){this.idle=0;this.idleAfter=IDLE_FIRST;return null}
    if(this.active)return null;
    this.idle+=dt;if(this.idle<this.idleAfter)return null;
    this.idleAfter=IDLE_REPEAT;return this.request('Wave');
  }
}
