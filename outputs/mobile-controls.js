function emit(code,type){window.dispatchEvent(new KeyboardEvent(type,{code,bubbles:true,cancelable:true}))}
function button(code,label,extra='',aria=label){return `<button type="button" data-key="${code}" class="${extra}" aria-label="${aria}">${label}</button>`}

const root=document.createElement('div');root.id='mobileControls';root.innerHTML=`<div class="mobile-pad">${button('ArrowUp','↑','up')}${button('ArrowLeft','←','left')}${button('ArrowRight','→','right')}${button('ArrowDown','↓','down')}</div><div class="mobile-actions">${button('Space','上昇')}${button('ShiftLeft','下降')}</div><div class="mobile-emotes">${button('Digit1','振る','','手を振る')}${button('Digit2','礼','','お辞儀')}${button('Digit3','回る','','空中で回転')}</div>`;document.body.append(root);
const held=new Map();
for(const el of root.querySelectorAll('[data-key]')){
  const down=e=>{e.preventDefault();const code=el.dataset.key;if(held.has(e.pointerId))return;held.set(e.pointerId,code);el.setPointerCapture(e.pointerId);emit(code,'keydown');el.classList.add('held')};
  const up=e=>{e.stopPropagation();const code=held.get(e.pointerId);if(!code)return;held.delete(e.pointerId);emit(code,'keyup');el.classList.remove('held')};
  // A finger on a button must not turn the camera or end another finger's camera drag: the stages listen on window.
  el.addEventListener('pointerdown',down);el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up);el.addEventListener('pointermove',e=>e.stopPropagation());
}
addEventListener('blur',()=>{for(const code of held.values())emit(code,'keyup');held.clear()});

const style=document.createElement('style');style.textContent=`
canvas{touch-action:none}#mobileControls{display:none;position:fixed;inset:0;z-index:14;pointer-events:none;user-select:none;-webkit-user-select:none}#mobileControls button{pointer-events:auto;width:54px;height:54px;border-radius:50%;border:1px solid #f5dfaa99;background:#17313dbb;color:#fff;font:700 17px system-ui;backdrop-filter:blur(6px);touch-action:none}#mobileControls button.held{background:#e7ca86;color:#17313d}.mobile-pad{position:absolute;left:18px;bottom:22px;width:164px;height:164px}.mobile-pad button{position:absolute}.mobile-pad .up{left:55px;top:0}.mobile-pad .left{left:0;top:55px}.mobile-pad .right{right:0;top:55px}.mobile-pad .down{left:55px;bottom:0}.mobile-actions{position:absolute;right:18px;bottom:28px;display:grid;grid-template-columns:repeat(2,54px);gap:10px}.mobile-emotes{position:absolute;right:18px;bottom:96px;display:grid;grid-template-columns:repeat(3,44px);gap:8px}#mobileControls .mobile-emotes button{width:44px;height:44px;font:700 12px system-ui}@media(pointer:coarse),(max-width:760px){#mobileControls{display:block}#help,.help{display:none!important}.return{left:auto!important;right:18px!important;top:auto!important;bottom:166px!important}#pace,#effectsControl{display:none!important}#characterControl{left:18px!important;top:82px!important;bottom:auto!important}#soundControls{display:flex!important;left:18px!important;top:120px!important;bottom:auto!important}#soundControls label,#soundNotice{display:none!important}}
`;document.head.append(style);
