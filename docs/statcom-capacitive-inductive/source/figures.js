/* Synchronized SVG renderers. The electrical model is imported from model.js, not from any circuit renderer. */
'use strict';
const STATCOMViews = (() => {
  const COLOR=Object.freeze({blue:'#176F98',teal:'#087D82',amber:'#BD7532',navy:'#123547',muted:'#6B8390',grid:'#E6EDF0',outside:'#9AAEB9'});
  // Immutable scales cover the complete advertised laboratory slider ranges.
  // Voltage phasors use the horizontal voltage axis; reactive current uses a
  // separate vertical axis because current and voltage have different bases.
  const AXIS_LIMITS=Object.freeze({
    phasorVoltage:1.5, phasorCurrent:4.0,
    waveformVoltage:2.0, waveformCurrent:6.0,
    trendEmin:0.75, trendEmax:1.25, trendMagnitude:5.0
  });
  const pnt=(x,y)=>`${x.toFixed(2)},${y.toFixed(2)}`;
  const f=(x,d=3)=>STATCOMPhysics.numeric(x,d);
  const signed=(x,d=3)=>STATCOMPhysics.numeric(x,d,true);
  const txt=(x,y,label,cls='',anchor='middle')=>`<text x="${x}" y="${y}" class="${cls}" text-anchor="${anchor}">${label}</text>`;
  // Preserve math typography across SVG panels: italic variables, upright numbers and subscripts.
  const mt=(x,y,tokens,cls='',anchor='middle')=>{
    let precedingSubscript=false;
    const spans=tokens.map(([value,kind])=>{
      if(!['var','roman','sub','prose'].includes(kind))throw Error(`Unknown math label role: ${kind}`);
      const vertical=kind==='sub'?' dy="3.5" font-size="74%"':precedingSubscript?' dy="-3.5"':'';
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
    const originX=117, originY=158;
    // Fixed, independent scales: V/E 0..1.5 pu horizontally, I -4..4 pu vertically.
    const voltageScale=208;
    const currentScale=27;
    const xE=originX+p.E*voltageScale,xV=originX+p.V*voltageScale;
    const yI=originY-op.Iimag*currentScale;
    const iColor=op.mode==='capacitive'?COLOR.teal:op.mode==='inductive'?COLOR.amber:COLOR.muted;
    const lineI=(op.Iabs>1e-9)?`<line data-vector="I" x1="${originX}" y1="${originY}" x2="${originX}" y2="${yI}" stroke="${iColor}" stroke-width="3.2" marker-end="url(#p-arrow-I)"/>`:'';
    const direction=op.mode==='capacitive'?'−90°':op.mode==='inductive'?'+90°':'not defined at zero current';
    const vTicks=[0.5,1.0,1.5].map(voltage=>{
      const x=originX+voltage*voltageScale;
      return `<line x1="${x}" x2="${x}" y1="${originY-4}" y2="${originY+4}" stroke="#b5c9d2" stroke-width="1.1"/>${txt(x,213,f(voltage,1),'svg-small svg-numeric')}`;
    }).join('');
    const iTicks=[-4,-2,0,2,4].map(current=>{
      const y=originY-current*currentScale;
      return `<line x1="${originX-5}" x2="${originX+5}" y1="${y}" y2="${y}" stroke="#b5c9d2" stroke-width="1.1"/>${txt(originX-11,y+4,(current>0?'+':'')+current,'svg-small svg-numeric','end')}`;
    }).join('');
    return `<defs>
      <marker id="p-arrow-V" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="${COLOR.blue}"/></marker>
      <marker id="p-arrow-E" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="${COLOR.amber}"/></marker>
      <marker id="p-arrow-I" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="${iColor}"/></marker>
      </defs>
      <g data-fixed-axis="phasor-voltage" data-min="0" data-max="${AXIS_LIMITS.phasorVoltage}">
        <line x1="${originX-18}" y1="${originY}" x2="470" y2="${originY}" stroke="#d1dde3" stroke-width="1.6"/>
        ${vTicks}
      </g>
      <g data-fixed-axis="phasor-current" data-min="-${AXIS_LIMITS.phasorCurrent}" data-max="${AXIS_LIMITS.phasorCurrent}">
        <line x1="${originX}" y1="34" x2="${originX}" y2="278" stroke="#d1dde3" stroke-width="1.6"/>
        ${iTicks}
      </g>
      ${txt(464,151,'Re','svg-small')}${txt(originX+16,27,'Im','svg-small')}
      <line data-vector="V" x1="${originX}" y1="${originY-6}" x2="${xV}" y2="${originY-6}" stroke="${COLOR.blue}" stroke-width="3" marker-end="url(#p-arrow-V)"/>
      <line data-vector="E" x1="${originX}" y1="${originY+6}" x2="${xE}" y2="${originY+6}" stroke="${COLOR.amber}" stroke-width="3" stroke-dasharray="9 4" marker-end="url(#p-arrow-E)"/>
      ${mt(xV+12,originY-19,[['V','var']],'svg-txt','start')}
      ${mt(xE+12,originY+30,[['E','var']],'svg-txt','start')}
      ${lineI}
      ${(op.Iabs>1e-9)?mt(originX+17,op.mode==='capacitive'?235:83,[['I','var'],['inj','sub'],[' = ','roman'],[`${op.Iimag<0?'−':'+'}`,'roman'],['j','var'],[`${f(Math.abs(op.Iimag,3))} pu`,'roman']],'svg-small svg-numeric','start'):mt(originX+14,244,[['I','var'],['inj','sub'],[' = 0 pu','roman']],'svg-small svg-numeric','start')}
      ${mt(300,250,[['E','var'],[' − ','roman'],['V','var'],[` = ${signed(op.voltageDifference)} pu`,'roman']],'svg-small svg-numeric')}
      ${mt(466,279,[['∠','roman'],['I','var'],['inj','sub'],[` = ${direction}`,'roman']],'svg-small svg-numeric','end')}
      ${txt(466,299,'Fixed axes: E,V 0–1.5 pu · I −4…+4 pu','mode-qualifier','end')}`;
  }
  function waveforms(p,angle){
    const x0=55,x1=438,y0=61,y1=247,yCenter=(y0+y1)/2;
    // Voltage and current have separate, clearly identified fixed vertical axes.
    // Both use the same RMS-based per-unit convention as the Python model.
    const syV=value=>yCenter-value/AXIS_LIMITS.waveformVoltage*((y1-y0)/2);
    const syI=value=>yCenter-value/AXIS_LIMITS.waveformCurrent*((y1-y0)/2);
    const sx=theta=>x0+(theta/360)*(x1-x0);
    const axes=[];
    for(const deg of [0,90,180,270,360]){
      axes.push(`<line x1="${sx(deg)}" y1="${y0}" x2="${sx(deg)}" y2="${y1}" class="svg-grid"/>`);
      axes.push(txt(sx(deg),267,`${deg}°`,'svg-small svg-numeric'));
    }
    for(const voltage of [-2,-1,0,1,2]){
      const y=syV(voltage);
      axes.push(`<line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="${voltage===0?'#9fb8c4':'#edf2f5'}" stroke-width="${voltage===0?1.5:1}"/>`);
      axes.push(txt(x0-8,y+4,f(voltage,0),'svg-small svg-numeric','end'));
    }
    for(const current of [-6,-3,0,3,6]){
      axes.push(txt(x1+8,syI(current)+4,f(current,0),'svg-small svg-numeric','start'));
    }
    const points={v:[],e:[],i:[]};
    for(let k=0;k<=360;k+=3){
      const w=STATCOMPhysics.waveforms(p,k);
      points.v.push([sx(k),syV(w.v)]);
      points.e.push([sx(k),syV(w.e)]);
      points.i.push([sx(k),syI(w.i)]);
    }
    const sample=STATCOMPhysics.waveforms(p,angle),xp=sx(angle);
    return `<g data-fixed-axis="voltage-waveform" data-min="-${AXIS_LIMITS.waveformVoltage}" data-max="${AXIS_LIMITS.waveformVoltage}"></g>
      <g data-fixed-axis="current-waveform" data-min="-${AXIS_LIMITS.waveformCurrent}" data-max="${AXIS_LIMITS.waveformCurrent}"></g>
      ${axes.join('')}
      ${txt(x0,45,'Voltage (pu)','mode-qualifier','start')}
      ${txt(x1+37,45,'Current (pu)','mode-qualifier','end')}
      <path data-signal="v" d="${path(points.v)}" fill="none" stroke="${COLOR.blue}" stroke-width="2.6" opacity=".9"/>
      <path data-signal="e" d="${path(points.e)}" fill="none" stroke="${COLOR.amber}" stroke-width="2.7" stroke-dasharray="10 5" opacity=".84"/>
      <path data-signal="i" d="${path(points.i)}" fill="none" stroke="${COLOR.teal}" stroke-width="2.7" stroke-dasharray="2 5" stroke-linecap="round" opacity=".87"/>
      <line x1="${xp}" y1="${y0}" x2="${xp}" y2="${y1}" stroke="#a45f48" stroke-dasharray="4 4" stroke-width="1.4" opacity=".8" />
      <circle data-cursor-signal="v" cx="${xp}" cy="${syV(sample.v)}" r="4.2" fill="white" stroke="${COLOR.blue}" stroke-width="2"/>
      <circle data-cursor-signal="e" cx="${xp}" cy="${syV(sample.e)}" r="4.2" fill="white" stroke="${COLOR.amber}" stroke-width="2"/>
      <circle data-cursor-signal="i" cx="${xp}" cy="${syI(sample.i)}" r="4.2" fill="white" stroke="${COLOR.teal}" stroke-width="2"/>
      <g class="svg-legend">
        <path d="M51 23 H75" stroke="${COLOR.blue}" stroke-width="2.7"/>${mt(81,27,[['v','var'],['(','roman'],['t','var'],[')','roman']],'svg-legend','start')}
        <path d="M164 23 H188" stroke="${COLOR.amber}" stroke-width="2.7" stroke-dasharray="8 4"/>${mt(194,27,[['e','var'],['(','roman'],['t','var'],[')','roman']],'svg-legend','start')}
        <path d="M278 23 H302" stroke="${COLOR.teal}" stroke-width="2.7" stroke-dasharray="2 5"/>${mt(309,27,[['i','var'],['inj','sub'],['(','roman'],['t','var'],[')','roman']],'svg-legend','start')}
      </g>
      ${mt(475,293,[['θ','var'],[` = ${angle.toFixed(0)}° · `,'roman'],['i','var'],['inj','sub'],[` = ${signed(sample.i)} RMS-base pu`,'roman']],'svg-small svg-numeric','end')}`;
  }
  function trend(p,type){
    const op=STATCOMPhysics.point(p);
    // No autorange: these bounds cover all E, V and X slider combinations.
    // Icap is between -4 and +4 pu, and Qinj between -4.6 and +3.4 pu.
    const min=AXIS_LIMITS.trendEmin,max=AXIS_LIMITS.trendEmax;
    const range=AXIS_LIMITS.trendMagnitude;
    const x0=60,x1=567,top=27,bottom=188;
    const compute=e=>type==='Q'?p.V*(e-p.V)/p.X:(e-p.V)/p.X;
    const x=e=>x0+(e-min)/(max-min)*(x1-x0);
    const y=value=>bottom-((value+range)/(2*range))*(bottom-top);
    const xNeutral=Math.max(x0,Math.min(x1,x(p.V)));
    const brackets=[min,max,op.limitLow,op.limitHigh].filter(e=>e>=min&&e<=max).sort((a,b)=>a-b);
    const knots=[...new Set(brackets)];
    let curves='';
    for(let k=0;k<knots.length-1;k++){
      const lo=knots[k],hi=knots[k+1],mid=(lo+hi)/2;
      if(hi-lo<1e-12)continue;
      const permitted=Math.abs((mid-p.V)/p.X)<=p.Imax+1e-9;
      curves+=`<path data-rating="${permitted?'within':'outside'}" d="M${pnt(x(lo),y(compute(lo)))} L${pnt(x(hi),y(compute(hi)))}" fill="none" stroke="${permitted?(type==='Q'?COLOR.teal:COLOR.blue):COLOR.outside}" stroke-width="${permitted?3.4:2.8}" stroke-dasharray="${permitted?'none':'8 5'}" opacity="${permitted?.92:.62}"/>`;
    }
    const color=type==='Q'?COLOR.teal:COLOR.blue;
    const hlines=[-range,-range/2,0,range/2,range].map(value=>`<line x1="${x0}" x2="${x1}" y1="${y(value)}" y2="${y(value)}" stroke="${value===0?'#9eb8c4':'#e7eff2'}" stroke-width="${value===0?1.5:.8}"/>${txt(x0-8,y(value)+4,f(value,1),'svg-small svg-numeric','end')}`).join('');
    const xaxis=[.75,.85,1,1.15,1.25].map(value=>`<line x1="${x(value)}" y1="${top}" x2="${x(value)}" y2="${bottom}" stroke="#e6eff1" stroke-width=".8"/>${txt(x(value),205,f(value,2),'svg-small svg-numeric')}`).join('');
    const value=compute(p.E),xp=x(p.E),yp=y(value);
    const rating=op.withinRating?'Within rating':'Outside rating';
    return `<g data-fixed-axis="${type==='Q'?'reactive-power':'capacitive-current'}" data-min-x="${min}" data-max-x="${max}" data-min-y="${-range}" data-max-y="${range}">
        <rect x="${x0}" y="${top}" width="${xNeutral-x0}" height="${bottom-top}" fill="#e8f0f8" opacity=".65"/>
        <rect x="${xNeutral}" y="${top}" width="${x1-xNeutral}" height="${bottom-top}" fill="#e5f4ee" opacity=".65"/>
        ${hlines}${xaxis}
        <line x1="${xNeutral}" x2="${xNeutral}" y1="${top}" y2="${bottom}" stroke="#849ea8" stroke-dasharray="4 4" stroke-width="1.4"/>
        ${curves}
        <line x1="${xp}" x2="${xp}" y1="${top}" y2="${bottom}" stroke="#2e718d" stroke-dasharray="4 4" stroke-width="1.4" opacity=".85"/>
        <circle data-operating-marker="${type}" cx="${xp}" cy="${yp}" r="5" stroke="${rating==='Within rating'?color:COLOR.amber}" stroke-width="2.3" fill="#fff"/>
      </g>
      ${mt(x0+3,18,type==='Q'?[['Reactive power ','prose'],['Q','var'],['inj','sub'],[' (pu)','roman']]:[['Capacitive current ','prose'],['I','var'],['cap','sub'],[' (pu)','roman']],'svg-small','start')}
      ${mt(567,220,[['E','var'],[` = ${f(p.E)} pu · ${signed(value)} pu`,'roman']],'svg-small svg-numeric','end')}
      ${txt(88,42,'INDUCTIVE','mode-qualifier','start')}${txt(559,42,'CAPACITIVE','mode-qualifier','end')}`;
  }
  return Object.freeze({circuit,phasors,waveforms,trend,AXIS_LIMITS});
})();

