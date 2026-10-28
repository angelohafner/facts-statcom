/* Lesson navigation and interactive lab controller. All calculations go through STATCOMPhysics. */
'use strict';
(() => {
  const $=(id)=>document.getElementById(id);
  const sections=[...document.querySelectorAll('.lesson-section')];
  const labels=['STEP 01 / 04 — Equivalent circuit','STEP 02 / 04 — Capacitive injection','STEP 03 / 04 — Inductive absorption','STEP 04 / 04 — Transition','INTERACTIVE LABORATORY — Synchronized views'];
  const state={...STATCOMPhysics.DEFAULT,theta:45};
  let currentSection=0,playing=false,frameHandle=0,previousTime=0,queued=false;
  const f=(x,d=3)=>STATCOMPhysics.numeric(x,d);
  const plus=(x,d=3)=>STATCOMPhysics.numeric(x,d,true);
  const listen=(id,fn)=>$(id).addEventListener('input',fn);
  function section(index){
    currentSection=Math.max(0,Math.min(sections.length-1,index));
    for(let i=0;i<sections.length;i++){
      const active=i===currentSection;
      sections[i].classList.toggle('active',active);
      sections[i].hidden=!active;
    }
    document.querySelectorAll('.nav-step').forEach((node,i)=>{
      const active=i===currentSection;
      node.classList.toggle('active',active);
      if(active)node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');
    });
    $('footer-caption').textContent=labels[currentSection];
    $('footer-count').textContent=`${currentSection+1} / ${sections.length}`;
    $('progress-meter').style.width=`${(currentSection+1)*100/sections.length}%`;
    $('previous').disabled=currentSection===0;
    $('next').textContent=currentSection===sections.length-1?'Back to first step ↺':'Next →';
    if(currentSection===sections.length-1)requestRender();
    window.scrollTo({top:0,behavior:'instant'});
  }
  function modeLabel(op){
    if(!op.withinRating)return 'OUTSIDE CURRENT RATING';
    if(op.mode==='capacitive')return 'CAPACITIVE SUPPORT';
    if(op.mode==='inductive')return 'INDUCTIVE ABSORPTION';
    return 'ZERO REACTIVE EXCHANGE';
  }
  function setPresets(op){
    document.querySelectorAll('[data-preset]').forEach(button=>{
      const selected=(button.dataset.preset==='cap'&&Math.abs(state.E-1.10)<1e-10)
        ||(button.dataset.preset==='ind'&&Math.abs(state.E-.90)<1e-10)
        ||(button.dataset.preset==='zero'&&Math.abs(state.E-state.V)<1e-10);
      button.classList.toggle('selected',selected);
      button.setAttribute('aria-pressed',String(selected));
    });
  }
  function render(){
    queued=false;
    const op=STATCOMPhysics.point(state);
    $('out-E').textContent=f(state.E);
    $('out-V').textContent=`${f(state.V)} pu`;
    $('out-X').textContent=`${f(state.X)} pu`;
    $('out-Imax').textContent=`${f(state.Imax,2)} pu`;
    $('out-theta').textContent=`${f(state.theta,0)}°`;
    $('metric-Q').innerHTML=`${plus(op.Q)} <span class="unit">pu</span>`;
    $('metric-I').innerHTML=`${f(op.Iabs)} <span class="unit">pu</span>`;
    const imag=(op.Iabs<1e-10?'0.000':(op.Iimag<0?'−j':' +j').trim()+f(Math.abs(op.Iimag)));
    $('metric-Iph').innerHTML=`${imag} <span class="unit">pu</span>`;
    $('metric-rating').textContent=op.withinRating?'Within limit':`Above ${f(state.Imax,2)} pu`;
    $('metric-rating').style.color=op.withinRating?'#087f75':'#98600f';
    const badge=$('mode-indicator');badge.textContent=modeLabel(op);
    badge.className=`mode-pill ${!op.withinRating?'outside':op.mode}`;
    $('circuit-caption').textContent=op.mode==='neutral'?'E = V · no reactive exchange':op.mode==='capacitive'?'E > V · capacitive':'E < V · inductive';
    $('phasor-caption').textContent=`Iinj = ${imag} pu`;
    $('lab-circuit').innerHTML=STATCOMViews.circuit(state);
    $('lab-phasors').innerHTML=STATCOMViews.phasors(state);
    $('lab-waveforms').innerHTML=STATCOMViews.waveforms(state,state.theta);
    $('lab-q-curve').innerHTML=STATCOMViews.trend(state,'Q');
    $('lab-i-curve').innerHTML=STATCOMViews.trend(state,'I');
    setPresets(op);
    const note=$('rating-note');
    if(op.withinRating){
      note.className='lab-note';
      note.innerHTML='Lossless fundamental model; <span class="var">δ</span> = 0°. Positive <span class="var">Q</span><sub>inj</sub> means reactive injection into the PCC. Current reference: converter → grid. Green/blue solid curves indicate points within the selected current rating.';
    }else{
      note.className='lab-note warning';
      note.innerHTML=`<b>Outside nominal current rating.</b> The ideal model requests ${f(op.Iabs)} pu, above the ${f(state.Imax)} pu limit. The point is mathematical only; current limiting requires a different achievable converter voltage. Additional DC-link / modulation limits are not modeled.`;
    }
  }
  function requestRender(){if(queued)return;queued=true;requestAnimationFrame(render);}
  function readSliders(){
    state.E=Number($('slider-E').value);
    state.V=Number($('slider-V').value);
    state.X=Number($('slider-X').value);
    state.Imax=Number($('slider-Imax').value);
    state.theta=Number($('slider-theta').value);
    requestRender();
  }
  function setVoltage(value){
    state.E=Math.max(.75,Math.min(1.25,value));
    $('slider-E').value=String(state.E);
    requestRender();
  }
  function pause(){playing=false;cancelAnimationFrame(frameHandle);frameHandle=0;$('btn-play').textContent='▶ Animate';$('btn-play').setAttribute('aria-label','Animate electrical angle');}
  function animate(now){
    if(!playing)return;
    if(previousTime){state.theta=(state.theta+(now-previousTime)*.10)%360;$('slider-theta').value=String(state.theta);requestRender();}
    previousTime=now;frameHandle=requestAnimationFrame(animate);
  }
  function togglePlay(){
    if(playing){pause();return;}
    playing=true;previousTime=0;$('btn-play').textContent='Ⅱ Pause';$('btn-play').setAttribute('aria-label','Pause electrical angle animation');frameHandle=requestAnimationFrame(animate);
  }
  document.querySelectorAll('[data-section]').forEach(el=>{if(el.classList.contains('nav-step'))el.addEventListener('click',()=>section(Number(el.dataset.section)));});
  document.querySelectorAll('[data-next]').forEach(el=>el.addEventListener('click',()=>section(Number(el.dataset.next))));
  $('previous').addEventListener('click',()=>section(currentSection-1));
  $('next').addEventListener('click',()=>section(currentSection===sections.length-1?0:currentSection+1));
  $('btn-fullscreen').addEventListener('click',()=>{
    if(document.fullscreenElement){document.exitFullscreen?.();}
    else document.documentElement.requestFullscreen?.();
  });
  $('btn-reset').addEventListener('click',()=>{
    pause();Object.assign(state,STATCOMPhysics.DEFAULT,{theta:45});
    for(const [key,id] of [['E','slider-E'],['V','slider-V'],['X','slider-X'],['Imax','slider-Imax'],['theta','slider-theta']])$(id).value=String(state[key]);
    requestRender();
  });
  document.querySelectorAll('[data-preset]').forEach(button=>button.addEventListener('click',()=>{
    const chosen=button.dataset.preset;
    setVoltage(chosen==='cap'?1.10:chosen==='ind'?.90:state.V);
  }));
  for(const id of ['slider-E','slider-V','slider-X','slider-Imax','slider-theta'])listen(id,readSliders);
  $('btn-play').addEventListener('click',togglePlay);
  document.addEventListener('keydown',(event)=>{
    if(event.altKey||event.ctrlKey||event.metaKey)return;
    const tag=(event.target?.tagName||'').toLowerCase();
    if(['input','textarea','select','button','summary'].includes(tag))return;
    if(event.key==='ArrowRight' || event.key==='PageDown'){event.preventDefault();section(currentSection+1)}
    if(event.key==='ArrowLeft'||event.key==='PageUp'){event.preventDefault();section(currentSection-1)}
    if(event.key.toLowerCase()==='l'){event.preventDefault();section(4)}
    if(event.key==='Escape'&&playing)pause();
  });
  document.addEventListener('visibilitychange',()=>{if(document.hidden && playing)pause();});
  render();section(0);
  // Public read-only test bridge for offline browser and Python cross-checks.
  Object.defineProperty(window,'STATCOMLessonDebug',{value:Object.freeze({point:STATCOMPhysics.point,waveforms:STATCOMPhysics.waveforms,getState:()=>({...state}),goto:section}),writable:false});
})();
