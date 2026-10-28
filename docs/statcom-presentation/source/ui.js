class SlideManager {
 constructor(){this.slides=[...document.querySelectorAll('.slide')];this.index=0;this.bind();this.goto(Number(location.hash.replace('#slide-',''))||1,false);}
 bind(){
  document.querySelector('#prev-slide').addEventListener('click',()=>this.goto(this.index));
  document.querySelector('#next-slide').addEventListener('click',()=>this.goto(this.index+2));
  document.querySelector('#go-lab').addEventListener('click',()=>this.goto(15));
  document.querySelector('#go-full').addEventListener('click',()=>{if(!document.fullscreenElement){document.documentElement.requestFullscreen?.();}else{document.exitFullscreen?.();}});
  document.querySelector('#progress-track').addEventListener('click',e=>{const b=e.currentTarget.getBoundingClientRect();this.goto(1+Math.floor((e.clientX-b.left)/b.width*this.slides.length));});
  document.addEventListener('click',e=>{const b=e.target.closest('[data-jump]');if(b)this.goto(Number(b.dataset.jump));});
  window.addEventListener('keydown',e=>{
   const el=document.activeElement,tag=el?.tagName;
   if(['INPUT','SELECT','TEXTAREA'].includes(tag)||el?.isContentEditable)return;
   if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' '){e.preventDefault();this.goto(this.index+2);}
   if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();this.goto(this.index);}
   if(e.key==='Home'){e.preventDefault();this.goto(1);}
   if(e.key==='End'){e.preventDefault();this.goto(15);}
  });
  window.addEventListener('resize',SlideManager.fit);
  document.addEventListener('fullscreenchange',SlideManager.fit);
  SlideManager.fit();
 }
 static fit(){const factor=Math.min(innerWidth/1440,innerHeight/810)*.982;document.documentElement.style.setProperty('--stage-scale',factor.toFixed(4));}
 goto(slide,updateHash=true){
  const index=clamp(slide-1,0,this.slides.length-1);this.index=index;
  this.slides.forEach((el,i)=>{el.classList.toggle('active',index===i);el.setAttribute('aria-hidden',String(index!==i));});
  document.querySelector('#slide-counter').textContent=`${String(index+1).padStart(2,'0')} / ${String(this.slides.length).padStart(2,'0')}`;
  document.querySelector('#slide-section').textContent=this.slides[index].dataset.title.toUpperCase();
  document.querySelector('#progress-fill').style.width=`${(index+1)/this.slides.length*100}%`;
  document.querySelector('#prev-slide').disabled=index===0;
  document.querySelector('#next-slide').disabled=index===this.slides.length-1;
  if(updateHash)history.replaceState(null,'',`#slide-${index+1}`);
 }
}

class InteractiveControls {
 static definitions={
  e:['Converter E','E',.75,1.25,.005,'pu'],
  v:['PCC V','V',.82,1.12,.005,'pu'],
  x:['Coupling X','X',.12,.40,.005,'pu'],
  delta:['Angle δ','δ',-8,8,.5,'°'],
  imax:['Current rating','Imax',.2,1.5,.05,'pu']
 };
 static build(){
  for(const holder of document.querySelectorAll('[data-controls]')){
   const name=holder.dataset.controls;const names=name==='lab'?['e','v','x','delta','imax']:name==='basic'?['e','v','x']:['e','v','x','delta'];
   holder.innerHTML=names.map(key=>{
    const [human,sym,min,max,step,units]=InteractiveControls.definitions[key];
    return `<div class="control-row"><label for="${name}-${key}" title="${human}"><var>${sym}</var></label><input id="${name}-${key}" type="range" aria-label="${human}" data-param="${key}" min="${min}" max="${max}" step="${step}"><output data-readout="${key}" for="${name}-${key}"></output></div>`;
   }).join('');
  }
  document.addEventListener('input',event=>{
   const inp=event.target.closest('input[data-param]');if(!inp)return;
   const val=Number(inp.value);if(Number.isFinite(val)){state[inp.dataset.param]=val;InteractiveControls.schedule();}
  });
  document.addEventListener('click',event=>{
   const preset=event.target.closest('[data-preset]');if(preset){const name=preset.dataset.preset;state.v=1;state.x=.2;state.delta=0;state.imax=.8;state.e=name==='capacitive'?1.1:name==='inductive'?.9:1;InteractiveControls.schedule();}
   const reset=event.target.closest('[data-reset]');if(reset){if(reset.dataset.reset==='all')Object.assign(state,DEFAULT);else Object.assign(state,{e:DEFAULT.e,v:DEFAULT.v,x:DEFAULT.x,delta:0});InteractiveControls.schedule();}
  });
 }
 static format(key){return ['delta'].includes(key)?`${fmt(state[key],1)}°`:[ 'cap'].includes(key)?`${fmt(state[key],0)} mF`:[ 'vdc'].includes(key)?`${fmt(state[key],1)} kV`:`${fmt(state[key],['droop','gridX'].includes(key)?3:2)} pu`;}
 static sync(){
  for(const inp of document.querySelectorAll('input[data-param]'))inp.value=String(state[inp.dataset.param]);
  for(const out of document.querySelectorAll('[data-readout]'))out.textContent=InteractiveControls.format(out.dataset.readout);
 }
 static schedule(){if(InteractiveControls.scheduled)return;InteractiveControls.scheduled=true;requestAnimationFrame(()=>{InteractiveControls.scheduled=false;renderEverything();});}
}
InteractiveControls.scheduled=false;

let selectedPart='grid',selectedLeg='a',topOn=true,selectedBlock='voltage',tech='two-level',eventMode='both';
let switchTimer=null,waveTimer=null;window.waveCursorOn=false;
function componentSelect(name){
 selectedPart=name;
 document.querySelectorAll('.component-pick').forEach(b=>b.classList.toggle('selected',b.dataset.part===name));
 const content={
  grid:['AC grid','The Thevenin network being supported. Grid strength influences how much injected reactive current changes PCC voltage.'],
  pcc:['Point of common coupling','The node where voltage is monitored and power exchange is defined: positive Q means injection into the PCC.'],
  transformer:['Coupling transformer','Provides voltage matching, isolation and leakage impedance. Winding phase shift is omitted in the simplified model.'],
  reactor:['Coupling reactor','Limits current and links the difference between converter and PCC fundamental voltages: I = (E − V) / (jX).'],
  vsc:['Voltage-source converter','Synthesizes a controllable fundamental AC voltage by modulating self-commutated semiconductor switches.'],
  capacitor:['DC-link capacitor','Stores finite DC energy, supports Vdc and absorbs/relinquishes transient active-power mismatch.'],
  control:['Control system','Voltage regulation, PLL, inner dq current loops, PWM and DC-link voltage regulation coordinate the converter.']
 };
 const [title,note]=content[name];
 document.querySelector('#component-note').innerHTML=`<h3>${ESC(title)}</h3><p>${ESC(note)}</p>`;
 svgTo('component-diagram',CircuitRenderer.components(name));
}
function drawSwitch(){
 svgTo('switch-diagram',CircuitRenderer.switches(selectedLeg,topOn));
 document.querySelectorAll('[data-leg]').forEach(b=>b.classList.toggle('active',b.dataset.leg===selectedLeg));
 document.querySelector('#pole-value').innerHTML=(topOn?'+V<sub>dc</sub>/2':'−V<sub>dc</sub>/2');
}
function controlSelect(name){
 selectedBlock=name;
 const [title,note]=CONTROL_INFO[name];
 document.querySelector('#control-block-name').textContent=title;
 document.querySelector('#control-block-note').textContent=note;
 svgTo('control-block-diagram',ControlDiagram.draw(name));
}
function technologySelect(name){
 tech=name;const info=TECHNOLOGIES[name];
 document.querySelectorAll('[data-tech]').forEach(x=>x.classList.toggle('active',x.dataset.tech===name));
 document.querySelector('#tech-name').textContent=info.name;
 document.querySelector('#tech-description').innerHTML=`<p>${ESC(info.summary)}</p>${info.bullet.map(v=>`<div class="bullet">${ESC(v)}</div>`).join('')}`;
 const target=document.querySelector('#tech-canvas');target.innerHTML='';
 const source=document.querySelector(`#asset-${name}`);
 if(source && source.content.querySelector('svg'))target.appendChild(source.content.cloneNode(true));
 else target.innerHTML=techFallback(name);
}
function bindSelections(){
 document.querySelector('#component-buttons').addEventListener('click',e=>{const v=e.target.closest('[data-part]');if(v)componentSelect(v.dataset.part);});
 document.querySelector('#component-diagram').addEventListener('click',e=>{const v=e.target.closest('[data-part]');if(v)componentSelect(v.dataset.part);});
 document.querySelectorAll('[data-leg]').forEach(b=>b.addEventListener('click',()=>{selectedLeg=b.dataset.leg;drawSwitch();}));
 document.querySelector('#switch-step').addEventListener('click',()=>{topOn=!topOn;drawSwitch();});
 document.querySelector('#switch-play').addEventListener('click',()=>{
  const b=document.querySelector('#switch-play');
  if(switchTimer){clearInterval(switchTimer);switchTimer=null;b.textContent='▶ Animate';}
  else{switchTimer=setInterval(()=>{topOn=!topOn;drawSwitch();},800);b.textContent='Ⅱ Pause';}
 });
 document.querySelector('#wave-play').addEventListener('click',()=>{
  const b=document.querySelector('#wave-play');
  if(waveTimer){clearInterval(waveTimer);waveTimer=null;window.waveCursorOn=false;b.textContent='▶ Move time cursor';}
  else{window.waveCursorOn=true;waveTimer=setInterval(()=>svgTo('waveforms-large',ChartRenderer.waveforms(state)),90);b.textContent='Ⅱ Pause';}
  svgTo('waveforms-large',ChartRenderer.waveforms(state));
 });
 document.querySelector('#control-block-diagram').addEventListener('click',e=>{const hit=e.target.closest('[data-control]');if(hit)controlSelect(hit.dataset.control);});
 document.querySelector('#technology-tabs').addEventListener('click',e=>{const b=e.target.closest('[data-tech]');if(b)technologySelect(b.dataset.tech);});
 document.querySelectorAll('[data-event]').forEach(b=>b.addEventListener('click',()=>{eventMode=b.dataset.event;document.querySelectorAll('[data-event]').forEach(x=>x.classList.toggle('active',x.dataset.event===eventMode));InteractiveControls.schedule();}));
}
function renderEverything(){
 InteractiveControls.sync();
 const op=STATCOMModel.at(state),lim=state.imax;
 for(const el of document.querySelectorAll('[data-live]')){
  const key=el.dataset.live;
  if(key==='q'){el.innerHTML=`${posfmt(op.q,2)} <span class="m-unit">pu</span>`;el.style.color=op.q>=0?COLORS.teal:COLORS.amber;}
  if(key==='p'){el.innerHTML=`${posfmt(op.p,2)} <span class="m-unit">pu</span>`;el.style.color=COLORS.white;}
  if(key==='i'){el.innerHTML=`${fmt(op.i,2)} <span class="m-unit">pu</span>`;el.style.color=op.feasible?COLORS.white:COLORS.red;}
  if(key==='mode'){el.textContent=op.feasible?op.mode:'OUTSIDE RATING';el.style.color=!op.feasible?COLORS.red:op.q>=0?COLORS.teal:COLORS.amber;}
 }
 for(const badge of document.querySelectorAll('[data-mode-label]')){
  badge.className=`mode-badge ${!op.feasible?'unsafe':op.q>0?'cap':op.q<0?'ind':'neutral'}`;
  badge.textContent=op.feasible?`${op.mode}  |  I ≤ ${fmt(lim,2)} pu`:'OUTSIDE CURRENT RATING';
 }
 document.querySelectorAll('[data-overlimit]').forEach(x=>x.hidden=op.feasible);
 const limitText=op.feasible?`Within current rating: |I| = ${fmt(op.i,3)} pu ≤ ${fmt(lim,2)} pu.`:
   `OUTSIDE CURRENT RATING: |I| = ${fmt(op.i,3)} pu > ${fmt(lim,2)} pu. E is not silently clipped.`;
 document.querySelector('#lab-status').textContent=limitText+(Math.abs(state.delta)>1e-4?' Nonzero δ implies active-power exchange; DC energy balance is not simulated.':'');
 svgTo('hero-circuit',CircuitRenderer.equivalent(state,op));
 svgTo('equivalent-circuit',CircuitRenderer.equivalent(state,op));
 svgTo('lab-circuit',CircuitRenderer.equivalent(state,op,{compact:true}));
 svgTo('lab-phasor',PhasorRenderer.draw(op,state,{compact:true}));
 svgTo('power-curve',ChartRenderer.powerVsE(state));
 svgTo('lab-q-curve',ChartRenderer.powerVsE(state,{compact:true}));
 svgTo('limit-curve',ChartRenderer.currentLimit(state));
 if(!waveTimer)svgTo('waveforms-large',ChartRenderer.waveforms(state));
 svgTo('lab-waveforms',ChartRenderer.waveforms(state,{compact:true}));
 svgTo('dynamic-response',ChartRenderer.dynamic(state,eventMode));
 svgTo('droop-chart',ChartRenderer.droop(state));
 svgTo('lab-droop',ChartRenderer.droop(state,{compact:true}));
 svgTo('dc-cap-diagram',CircuitRenderer.dcCap(state));
 document.querySelector('#dc-energy').innerHTML=`${fmt(DCLinkModel.energyKJ(state.cap,state.vdc),1)} <span class="m-unit">kJ</span>`;
 document.querySelector('#dc-release').innerHTML=`${fmt(DCLinkModel.energyFrom10PercentSag(state.cap,state.vdc),1)} <span class="m-unit">kJ</span>`;
 const eq=VoltageController.equilibrium(state.vth,state);
 document.querySelector('#droop-current').textContent=`${posfmt(eq.i,3)} pu`;
 document.querySelector('#droop-vpcc').textContent=`${fmt(eq.v,3)} pu`;
}
function initialize(){
 InteractiveControls.build();
 bindSelections();
 componentSelect('grid');drawSwitch();controlSelect('voltage');technologySelect('two-level');
 const capState={...DEFAULT,e:1.1},indState={...DEFAULT,e:.9};
 svgTo('capacitive-phasor',PhasorRenderer.draw(STATCOMModel.at(capState),capState));
 svgTo('inductive-phasor',PhasorRenderer.draw(STATCOMModel.at(indState),indState));
 renderEverything();new SlideManager();
}
initialize();
