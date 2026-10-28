/* Synchronized SVG renderers. The electrical model is imported from model.js, not from any circuit renderer. */
'use strict';
const STATCOMViews = (() => {
  const COLOR=Object.freeze({blue:'#187cac',teal:'#088878',amber:'#b9762e',navy:'#173f55',muted:'#768d9a',grid:'#e7eef1',outside:'#8295a2'});
  const pnt=(x,y)=>`${x.toFixed(2)},${y.toFixed(2)}`;
  const f=(x,d=3)=>STATCOMPhysics.numeric(x,d);
  const signed=(x,d=3)=>STATCOMPhysics.numeric(x,d,true);
  const txt=(x,y,label,cls='',anchor='middle')=>`<text x="${x}" y="${y}" class="${cls}" text-anchor="${anchor}">${label}</text>`;
  // Preserve math typography across SVG panels: italic variables, upright numbers and subscripts.
  const mt=(x,y,tokens,cls='',anchor='middle')=>{
    let precedingSubscript=false;
    const spans=tokens.map(([value,kind])=>{
      if(!['var','roman','sub','prose'].includes(kind))throw Error(`Unknown math label role: ${kind}`);
      const vertical=kind==='sub'?' dy="3" font-size="70%"':precedingSubscript?' dy="-3"':'';
      precedingSubscript=kind==='sub';
      return `<tspan data-math-role="${kind}" font-style="${kind==='var'?'italic':'normal'}"${vertical}>${value}</tspan>`;
    }).join('');
    return `<text x="${x}" y="${y}" class="math-svg-label ${cls}" text-anchor="${anchor}">${spans}</text>`;
  };

  const safe=(x)=>Math.max(0,Math.min(1,x));
  const path=(pts)=>pts.map((point,i)=>`${i?'L':'M'}${pnt(point[0],point[1])}`).join(' ');
  function circuit(p){
    const op=STATCOMPhysics.point(p);
    const accent=op.mode==='capacitive'?COLOR.teal:op.mode==='inductive'?COLOR.amber:'#657c8a';
    const difference=op.voltageDifference;
    const state=op.mode==='neutral'?'Zero voltage difference':op.mode==='capacitive'?'Converter voltage > PCC voltage':'Converter voltage < PCC voltage';
    return `<defs><marker id="c-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="${accent}"/></marker></defs>
      <path class="svg-line" d="M75 80 H159 M310 80 H421 V129 M75 80 V129 M75 185 V241 H421 V185" />
      <path d="M159 80 Q174 48 189 80 Q204 48 219 80 Q234 48 249 80 Q264 48 279 80 Q294 48 309 80" fill="none" stroke="${COLOR.blue}" stroke-width="3.5"/>
      <circle cx="75" cy="157" r="28" fill="white" stroke="${COLOR.blue}" stroke-width="2.8" />
      <circle cx="421" cy="157" r="28" fill="white" stroke="${COLOR.blue}" stroke-width="2.8" />
      <path d="M57 157 Q66 136 75 157 T93 157 M403 157 Q412 136 421 157 T439 157" stroke="${COLOR.blue}" fill="none" stroke-width="2"/>
      <circle cx="75" cy="80" r="4.5" fill="${COLOR.navy}"/><circle cx="421" cy="80" r="4.5" fill="${COLOR.navy}"/>
      ${txt(229,35,'Coupling reactor','svg-small')}
      ${mt(231,116,[['X','var'],[` = ${f(p.X)} pu`,'roman']],'svg-small svg-numeric')}
      <path d="M319 60 H397" stroke="${accent}" stroke-width="2.5" marker-end="url(#c-arrow)" />
      ${mt(360,49,[['I','var'],['inj','sub'],[' reference','prose']],'svg-small')}
      ${mt(36,165,[['E','var']],'svg-txt')}${mt(464,165,[['V','var']],'svg-txt')}
      ${txt(113,205,'Converter AC','svg-small','start')}${txt(379,205,'Grid / PCC','svg-small','end')}
      ${txt(113,224,`${f(p.E)} pu`,'svg-small svg-numeric','start')}${txt(379,224,`${f(p.V)} pu`,'svg-small svg-numeric','end')}
      ${mt(244,269,[['E','var'],[' − ','roman'],['V','var'],[` = ${signed(difference)} pu`,'roman']],'svg-txt svg-numeric')}
      ${txt(244,290,state,'svg-small')}`;
  }
  function phasors(p){
    const op=STATCOMPhysics.point(p);
    const originX=117, originY=160;
    const scale=Math.min(185/Math.max(p.E,p.V,1.15),107/Math.max(op.Iabs,0.67));
    const xE=originX+p.E*scale,xV=originX+p.V*scale;
    const yI=originY-op.Iimag*scale;
    const iColor=op.mode==='capacitive'?COLOR.teal:op.mode==='inductive'?COLOR.amber:COLOR.muted;
    const lineI=(op.Iabs>1e-9)?`<line x1="${originX}" y1="${originY}" x2="${originX}" y2="${yI}" stroke="${iColor}" stroke-width="3.2" marker-end="url(#p-arrow-I)"/>`:'';
    const direction=op.mode==='capacitive'?'−90°':op.mode==='inductive'?'+90°':'not defined at zero current';
    return `<defs>
      <marker id="p-arrow-V" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="${COLOR.blue}"/></marker>
      <marker id="p-arrow-E" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="${COLOR.amber}"/></marker>
      <marker id="p-arrow-I" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="${iColor}"/></marker>
      </defs>
      <line x1="${originX-18}" y1="${originY}" x2="470" y2="${originY}" stroke="#d1dde3" stroke-width="1.6"/>
      <line x1="${originX}" y1="34" x2="${originX}" y2="278" stroke="#d1dde3" stroke-width="1.6"/>
      ${txt(464,153,'Re','svg-small')}${txt(originX+14,27,'Im','svg-small')}
      <line x1="${originX}" y1="${originY-6}" x2="${xV}" y2="${originY-6}" stroke="${COLOR.blue}" stroke-width="3" marker-end="url(#p-arrow-V)"/>
      <line x1="${originX}" y1="${originY+6}" x2="${xE}" y2="${originY+6}" stroke="${COLOR.amber}" stroke-width="3" stroke-dasharray="9 4" marker-end="url(#p-arrow-E)"/>
      ${mt(xV+12,originY-17,[['V','var']],'svg-txt','start')}
      ${mt(xE+12,originY+29,[['E','var']],'svg-txt','start')}
      ${lineI}
      ${(op.Iabs>1e-9)?mt(originX+14,Math.min(267,Math.max(46,(originY+yI)/2)),[['I','var'],['inj','sub'],[' = ','roman'],[`${op.Iimag<0?'−':'+'}`,'roman'],['j','var'],[`${f(Math.abs(op.Iimag,3))} pu`,'roman']],'svg-small svg-numeric','start'):mt(originX+10,210,[['I','var'],['inj','sub'],[' = 0 pu','roman']],'svg-small svg-numeric','start')}
      ${mt(300,originY+77,[['E','var'],[' − ','roman'],['V','var'],[` = ${signed(op.voltageDifference)} pu`,'roman']],'svg-small svg-numeric')}
      ${mt(465,277,[['∠','roman'],['I','var'],['inj','sub'],[` = ${direction}`,'roman']],'svg-small svg-numeric','end')}
      ${txt(463,291,'E, V are in phase (lines offset for clarity)','mode-qualifier','end')}`;
  }
  function waveforms(p,angle){
    const op=STATCOMPhysics.point(p),x0=49,x1=478,y0=58,y1=251,yCenter=(y0+y1)/2;
    const ampl=Math.max(1.82,Math.SQRT2*Math.max(p.E,p.V,op.Iabs)*1.10);
    const sy=(y)=>yCenter-(y/ampl)*((y1-y0)/2);
    const sx=(theta)=>x0+(theta/360)*(x1-x0);
    const axes=[];
    for(const deg of [0,90,180,270,360]){
      axes.push(`<line x1="${sx(deg)}" y1="${y0}" x2="${sx(deg)}" y2="${y1}" class="svg-grid"/>`);
      axes.push(txt(sx(deg),269,`${deg}°`,'svg-small svg-numeric'));
    }
    for(const frac of [-1,0,1]){
      const y=sy(frac*ampl*.75);
      axes.push(`<line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="${frac===0?'#b6c8d1':'#edf2f5'}" stroke-width="${frac===0?1.5:1}"/>`);
    }
    const points={v:[],e:[],i:[]};
    for(let k=0;k<=360;k+=3){const w=STATCOMPhysics.waveforms(p,k);for(const key of ['v','e','i'])points[key].push([sx(k),sy(w[key])]);}
    const sample=STATCOMPhysics.waveforms(p,angle),xp=sx(angle),xpText=Math.min(x1-65,xp+8);
    return `${axes.join('')}
      <path d="${path(points.v)}" fill="none" stroke="${COLOR.blue}" stroke-width="2.6" opacity=".9"/>
      <path d="${path(points.e)}" fill="none" stroke="${COLOR.amber}" stroke-width="2.7" stroke-dasharray="10 5" opacity=".84"/>
      <path d="${path(points.i)}" fill="none" stroke="${COLOR.teal}" stroke-width="2.7" stroke-dasharray="2 5" stroke-linecap="round" opacity=".87"/>
      <line x1="${xp}" y1="${y0}" x2="${xp}" y2="${y1}" stroke="#a45f48" stroke-dasharray="4 4" stroke-width="1.4" opacity=".8" />
      <circle cx="${xp}" cy="${sy(sample.v)}" r="4.2" fill="white" stroke="${COLOR.blue}" stroke-width="2"/>
      <circle cx="${xp}" cy="${sy(sample.e)}" r="4.2" fill="white" stroke="${COLOR.amber}" stroke-width="2"/>
      <circle cx="${xp}" cy="${sy(sample.i)}" r="4.2" fill="white" stroke="${COLOR.teal}" stroke-width="2"/>
      <g class="svg-legend">
        <path d="M51 23 H75" stroke="${COLOR.blue}" stroke-width="2.7"/>${mt(81,27,[['v','var'],['(','roman'],['t','var'],[')','roman']],'svg-legend','start')}
        <path d="M164 23 H188" stroke="${COLOR.amber}" stroke-width="2.7" stroke-dasharray="8 4"/>${mt(194,27,[['e','var'],['(','roman'],['t','var'],[')','roman']],'svg-legend','start')}
        <path d="M278 23 H302" stroke="${COLOR.teal}" stroke-width="2.7" stroke-dasharray="2 5"/>${mt(309,27,[['i','var'],['inj','sub'],['(','roman'],['t','var'],[')','roman']],'svg-legend','start')}
      </g>
      ${mt(475,292,[['θ','var'],[` = ${angle.toFixed(0)}° · `,'roman'],['i','var'],['inj','sub'],[` = ${signed(sample.i)} RMS-base pu`,'roman']],'svg-small svg-numeric','end')}`;
  }
  function trend(p,type){
    const op=STATCOMPhysics.point(p),min=.75,max=1.25;
    const x0=60,x1=567,top=27,bottom=188;
    const compute=(e)=>type==='Q'?p.V*(e-p.V)/p.X:(e-p.V)/p.X;
    const magnitude=Math.max(.6,Math.abs(compute(min)),Math.abs(compute(max)));
    const range=Math.ceil((magnitude*1.15)*2)/2;
    const x=e=>x0+(e-min)/(max-min)*(x1-x0);
    const y=v=>bottom-((v+range)/(2*range))*(bottom-top);
    const xNeutral=Math.max(x0,Math.min(x1,x(p.V)));
    const brackets=[min,max,op.limitLow,op.limitHigh].filter(e=>e>=min&&e<=max).sort((a,b)=>a-b);
    const knots=[...new Set(brackets)];
    let curves='';
    for(let k=0;k<knots.length-1;k++){
      const lo=knots[k],hi=knots[k+1],mid=(lo+hi)/2;
      if(hi-lo<1e-12)continue;
      const permitted=Math.abs((mid-p.V)/p.X)<=p.Imax+1e-9;
      curves+=`<path d="M${pnt(x(lo),y(compute(lo)))} L${pnt(x(hi),y(compute(hi)))}" fill="none" stroke="${permitted?(type==='Q'?COLOR.teal:COLOR.blue):COLOR.outside}" stroke-width="${permitted?3.4:2.8}" stroke-dasharray="${permitted?'none':'8 5'}" opacity="${permitted?.92:.62}"/>`;
    }
    const zero=y(0);
    const color=type==='Q'?COLOR.teal:COLOR.blue;
    const label=type==='Q'?'Reactive power Qinj (pu)':'Capacitive current Icap (pu)';
    const hlines=[-range,-range/2,0,range/2,range].map(v=>`<line x1="${x0}" x2="${x1}" y1="${y(v)}" y2="${y(v)}" stroke="${v===0?'#9eb8c4':'#e7eff2'}" stroke-width="${v===0?1.5:.8}"/>${txt(x0-8,y(v)+4,f(v,1),'svg-small svg-numeric','end')}`).join('');
    const xaxis=[.75,.85,1,1.15,1.25].map(v=>`<line x1="${x(v)}" y1="${top}" x2="${x(v)}" y2="${bottom}" stroke="#e6eff1" stroke-width=".8"/>${txt(x(v),205,f(v,2),'svg-small svg-numeric')}`).join('');
    const value=compute(p.E),xp=x(p.E),yp=y(value);
    const rating=op.withinRating?'Within rating':'Outside rating';
    return `<rect x="${x0}" y="${top}" width="${xNeutral-x0}" height="${bottom-top}" fill="#e8f0f8" opacity=".65"/>
      <rect x="${xNeutral}" y="${top}" width="${x1-xNeutral}" height="${bottom-top}" fill="#e5f4ee" opacity=".65"/>
      ${hlines}${xaxis}
      <line x1="${xNeutral}" x2="${xNeutral}" y1="${top}" y2="${bottom}" stroke="#849ea8" stroke-dasharray="4 4" stroke-width="1.4"/>
      ${curves}
      <line x1="${xp}" x2="${xp}" y1="${top}" y2="${bottom}" stroke="#2e718d" stroke-dasharray="4 4" stroke-width="1.4" opacity=".85"/>
      <circle cx="${xp}" cy="${yp}" r="5" stroke="${rating==='Within rating'?color:COLOR.amber}" stroke-width="2.3" fill="#fff"/>
      ${mt(x0+3,18,type==='Q'?[['Reactive power ','prose'],['Q','var'],['inj','sub'],[' (pu)','roman']]:[['Capacitive current ','prose'],['I','var'],['cap','sub'],[' (pu)','roman']],'svg-small','start')}
      ${mt(567,220,[['E','var'],[` = ${f(p.E)} pu · ${signed(value)} pu`,'roman']],'svg-small svg-numeric','end')}
      ${txt(88,42,'INDUCTIVE','mode-qualifier','start')}${txt(559,42,'CAPACITIVE','mode-qualifier','end')}`;
  }
  return Object.freeze({circuit,phasors,waveforms,trend});
})();
