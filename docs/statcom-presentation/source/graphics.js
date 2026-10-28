class SVG {
 static open(w,h,body,opts=''){return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${ESC(opts||'STATCOM technical visualization')}" xmlns="http://www.w3.org/2000/svg">${body}</svg>`;}
 static ln(x,y,x2,y2,c=COLORS.muted,width=2,dash=''){return `<line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${width}" stroke-linecap="round" ${dash?`stroke-dasharray="${dash}"`:''}/>`;}
 static r(x,y,w,h,fill='none',stroke=COLORS.grid,rx=7){return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="1.4"/>`;}
 static t(x,y,text,size=13,color=COLORS.muted,anchor='start',weight=500,italic=false){
  // Variables are italic; descriptive subscript labels and physical units stay upright.
  const symbols=/\b(?:Imax|Icap|Iinj|Qinj|Pinj|Vdc|Vref|Vpcc|Vth|Econv|Cdc|E|V|X|I|P|Q)\b|δ|θ/g;
  const fragments=[];let before=0,str=String(text),match;
  while((match=symbols.exec(str))!==null){
    fragments.push(ESC(str.slice(before,match.index)));
    const token=match[0],main=(token==='δ'||token==='θ')?token:token[0];
    const rest=token.slice(main.length);
    fragments.push(`<tspan font-style="italic">${ESC(main)}</tspan>`);
    if(rest)fragments.push(`<tspan font-style="normal" baseline-shift="sub" font-size="${(size*.71).toFixed(1)}">${ESC(rest)}</tspan>`);
    before=match.index+token.length;
  }
  fragments.push(ESC(str.slice(before)));
  return `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="${size}" font-style="${italic?'italic':'normal'}" font-weight="${weight}" fill="${color}">${fragments.join('')}</text>`;
 }
 static c(x,y,r,fill=COLORS.teal,stroke='none'){return `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" stroke="${stroke}"/>`;}
 static path(d,c,width=2,dash='',fill='none'){return `<path d="${d}" fill="${fill}" stroke="${c}" stroke-width="${width}" stroke-linejoin="round" stroke-linecap="round" ${dash?`stroke-dasharray="${dash}"`:''}/>`;}
 static arrow(x1,y1,x2,y2,c=COLORS.teal,width=3){const a=Math.atan2(y2-y1,x2-x1),sz=8;return SVG.ln(x1,y1,x2,y2,c,width)+SVG.path(`M${x2-sz*Math.cos(a-.5)},${y2-sz*Math.sin(a-.5)} L${x2},${y2} L${x2-sz*Math.cos(a+.5)},${y2-sz*Math.sin(a+.5)}`,c,width);}
 static cap(x,y,width=24){return SVG.ln(x-width/2,y-8,x+width/2,y-8,COLORS.amber,3.2)+SVG.ln(x-width/2,y+8,x+width/2,y+8,COLORS.amber,3.2);}
 static coil(x1,y,x2,c=COLORS.blue){let d=`M${x1},${y}`;const n=4, pitch=(x2-x1)/n;for(let i=0;i<n;i++){const x=x1+i*pitch;d+=` C${x+pitch*.15},${y-18} ${x+pitch*.85},${y-18} ${x+pitch},${y}`;}return SVG.path(d,c,3);}
}

function svgTo(target,svg){const el=document.getElementById(target);if(el)el.innerHTML=svg;}
function setupPlot(w,h,xmin,xmax,ymin,ymax,{xLabel='',yLabel='',xticks=5,yticks=4,compact=false}={}){
 const l=compact?38:57,r=compact?12:23,t=compact?12:22,b=compact?29:44;
 const x=v=>l+(v-xmin)/(xmax-xmin)*(w-l-r);
 const y=v=>h-b-(v-ymin)/(ymax-ymin)*(h-t-b);
 let bg='';
 for(let i=0;i<=xticks;i++){const v=xmin+(xmax-xmin)*i/xticks,px=x(v);bg+=SVG.ln(px,t,px,h-b,COLORS.grid,.8,'3 5')+SVG.t(px,h-b+17,fmt(v,compact?1:2),compact?10:11,COLORS.muted,'middle');}
 for(let j=0;j<=yticks;j++){const v=ymin+(ymax-ymin)*j/yticks,py=y(v);bg+=SVG.ln(l,py,w-r,py,COLORS.grid,.8,'3 5')+SVG.t(l-7,py+4,fmt(v,Math.abs(ymax-ymin)<1?2:1),compact?10:11,COLORS.muted,'end');}
 if(ymin<=0&&ymax>=0)bg+=SVG.ln(l,y(0),w-r,y(0),'#658396',1.3);
 if(xmin<=0&&xmax>=0)bg+=SVG.ln(x(0),t,x(0),h-b,'#658396',1.3);
 if(xLabel)bg+=SVG.t((w-r+l)/2,h-5,xLabel,compact?10:12,COLORS.white,'middle',550);
 if(yLabel)bg+=SVG.t(l+3,11,yLabel,compact?10:12,COLORS.white,'start',550);
 return {x,y,bg,l,r,t,b};
}
function sequencePath(data,fx,fy){return data.map((pt,j)=>`${j===0?'M':'L'}${fx(pt).toFixed(2)},${fy(pt).toFixed(2)}`).join(' ');}
function pathSegments(points,valid,xy,yy,color,thick=2.5){
 let out='',last=-1;
 for(let k=0;k<points.length;k++){
  let p=points[k];if(k>0&&valid(p)!==valid(points[k-1])){const seg=points.slice(last<0?0:last,k);}
 }
 let start=0;
 for(let i=1;i<=points.length;i++){
  if(i===points.length||valid(points[i])!==valid(points[i-1])){
   const slice=points.slice(Math.max(0,start-1),i);
   if(slice.length>=2)out+=SVG.path(sequencePath(slice,d=>xy(d.e),d=>yy(d.q)),color,thick,valid(points[Math.max(0,start)])?'':'5 5');
   start=i;
  }
 }
 return out;
}

class PhasorRenderer {
 static draw(op,p,{compact=false}={}){
  const w=compact?600:700,h=compact?230:405,ox=compact?215:273,oy=h*.52;
  const scale=compact?102:170,iscale=compact?83:130;
  const vx=ox+p.v*scale,ex=ox+op.eReal*scale,ey=oy-op.eImag*scale;
  const ix=ox+op.ir*iscale,iy=oy-op.ii*iscale;
  let s=SVG.ln(25,oy,w-25,oy,COLORS.grid,1.7)+SVG.ln(ox,14,ox,h-21,COLORS.grid,1.7);
  s+=SVG.t(w-19,oy-9,'Re',12,COLORS.muted,'end')+SVG.t(ox+8,20,'Im',12,COLORS.muted);
  s+=SVG.c(ox,oy,3.5,COLORS.white);
  // The current has a different visual scale, explicitly stated in the legend.
  s+=SVG.arrow(ox,oy,vx,oy,COLORS.blue,4);
  s+=SVG.arrow(ox,oy,ex,ey,COLORS.amber,4);
  if(op.i>1e-6)s+=SVG.arrow(ox,oy,ix,iy,op.feasible?COLORS.teal:COLORS.red,4);
  s+=SVG.t(Math.min(w-30,vx+8),oy+21,'V',compact?13:16,COLORS.blue,'middle',720,true);
  s+=SVG.t(Math.min(w-22,ex+8),Math.max(23,ey-13),'E',compact?13:16,COLORS.amber,'middle',720,true);
  if(op.i>1e-6)s+=SVG.t(clamp(ix+12,25,w-25),clamp(iy+(iy>oy?21:-10),24,h-24),'I',compact?14:17,op.feasible?COLORS.teal:COLORS.red,'middle',720,true);
  else s+=SVG.t(ox+12,oy-19,'I = 0',13,COLORS.teal);
  const labs=compact?`${fmt(op.angleI,0)}° current angle · I visual scale differs from V`:
   `δ = ${fmt(p.delta,1)}°    ∠I = ${fmt(op.angleI,1)}°    |I| = ${fmt(op.i,2)} pu`;
  s+=SVG.t(w*.50,h-8,labs,compact?10:13,COLORS.muted,'middle');
  s+=SVG.t(20,29,`E ${fmt(p.e,2)} pu`,compact?12:15,COLORS.amber)+SVG.t(20,47,`V ${fmt(p.v,2)} pu`,compact?12:15,COLORS.blue);
  return SVG.open(w,h,s,'Converter E, PCC V and injected I phasors');
 }
}

class CircuitRenderer {
 static equivalent(p,op,{compact=false}={}){
  const w=compact?650:650,h=compact?105:250,y=compact?52:116;
  let s='';
  s+=SVG.ln(40,y,135,y,COLORS.blue,4)+SVG.coil(135,y,250,COLORS.blue)+SVG.ln(250,y,330,y,COLORS.blue,4);
  s+=SVG.c(40,y,5,COLORS.blue)+SVG.c(330,y,5,COLORS.amber);
  s+=SVG.ln(330,y,385,y,COLORS.amber,4)+SVG.r(385,y-(compact?26:53),148,compact?52:108,'#203a4b','#73b3aa',13);
  s+=SVG.t(459,y+(compact?5:-6),'VSC',compact?15:25,COLORS.white,'middle',780);
  if(!compact)s+=SVG.t(459,y+21,'fundamental E',13,COLORS.amber,'middle');
  if(!compact){s+=SVG.ln(534,y,560,y,COLORS.amber,2)+SVG.ln(560,y,560,y+37,COLORS.amber,2)+SVG.cap(560,y+61,30)+SVG.ln(560,y+69,560,y+98,COLORS.amber,2)+SVG.t(580,y+66,'Cdc',12,COLORS.amber);}
  s+=SVG.t(39,y-(compact?15:29),`PCC  V=${fmt(p.v,2)}`,compact?12:17,COLORS.blue);
  s+=SVG.t(183,y-(compact?14:26),`X=${fmt(p.x,2)} pu`,compact?11:15,COLORS.blue,'middle');
  if(compact){s+=SVG.t(459,y+33,`E=${fmt(p.e,2)}`,10,COLORS.amber,'middle');}
  else s+=SVG.t(459,y-73,`E=${fmt(p.e,2)} ∠${fmt(p.delta,1)}°`,16,COLORS.amber,'middle');
  s+=SVG.arrow(295,y+(compact?13:21),246,y+(compact?13:21),op.q>=0?COLORS.teal:COLORS.amber,2.5);
  if(!compact){s+=SVG.t(273,y+54,'positive I injection ←',13,COLORS.teal,'middle');s+=SVG.t(39,y+80,`Qinj = ${posfmt(op.q,2)} pu`,17,op.q>=0?COLORS.teal:COLORS.amber);}
  return SVG.open(w,h,s,'STATCOM fundamental voltage source behind a reactor');
 }
 static components(selected){
  const w=710,h=420,y=180;
  let s='';
  const color=part=>part===selected?COLORS.teal:'#7796a9';
  const glow=part=>part===selected?'#22534d':'#1a3149';
  s+=`<g data-part="grid" style="cursor:pointer">${SVG.r(18,142,83,75,glow('grid'),color('grid'),12)}${SVG.t(60,175,'GRID',16,COLORS.white,'middle',780)}${SVG.t(60,193,'AC',12,COLORS.muted,'middle')}</g>`;
  s+=SVG.ln(101,y,141,y,COLORS.blue,3);
  s+=`<g data-part="pcc" style="cursor:pointer">${SVG.c(143,y,7,color('pcc'))}${SVG.t(142,154,'PCC',14,color('pcc'),'middle',740)}</g>`;
  s+=SVG.ln(150,y,190,y,COLORS.blue,3);
  s+=`<g data-part="transformer" style="cursor:pointer">${SVG.c(208,y,22,'none',color('transformer'))}${SVG.c(237,y,22,'none',color('transformer'))}${SVG.t(223,228,'Transformer',12,color('transformer'),'middle')}</g>`;
  s+=SVG.ln(258,y,287,y,COLORS.blue,3);
  s+=`<g data-part="reactor" style="cursor:pointer">${SVG.coil(287,y,377,color('reactor'))}${SVG.t(334,228,'Coupling L',12,color('reactor'),'middle')}</g>`;
  s+=SVG.ln(377,y,405,y,COLORS.blue,3);
  s+=`<g data-part="vsc" style="cursor:pointer">${SVG.r(405,133,151,95,glow('vsc'),color('vsc'),12)}${SVG.t(482,174,'VSC',26,COLORS.white,'middle',780)}${SVG.t(482,199,'AC / DC',13,COLORS.muted,'middle')}</g>`;
  s+=`<g data-part="capacitor" style="cursor:pointer">${SVG.ln(556,y,612,y,COLORS.amber,3)}${SVG.ln(612,y,612,224,COLORS.amber,3)}${SVG.cap(612,247,44)}${SVG.ln(612,255,612,305,COLORS.amber,3)}${SVG.t(643,253,'Cdc',14,color('capacitor'))}${SVG.t(612,339,'DC link',13,color('capacitor'),'middle')}</g>`;
  s+=`<g data-part="control" style="cursor:pointer">${SVG.r(235,325,234,65,glow('control'),color('control'),12)}${SVG.t(352,352,'Voltage / current control',16,COLORS.white,'middle',650)}${SVG.t(352,374,'PLL · PI · PWM',12,COLORS.muted,'middle')}${SVG.path('M352,325 L352,265 L481,265 L481,230',color('control'),2,'5 5')}</g>`;
  s+=SVG.t(23,29,'Click a component to focus',16,COLORS.muted);s+=SVG.t(23,56,'AC  →  coupling transformer / reactor  →  VSC + DC link',13,COLORS.muted);
  return SVG.open(w,h,s,'STATCOM components and their physical connections');
 }
 static switches(leg='a',topState=true){
   const w=825,h=480,ys=68,yb=419,xs=[178,413,648],phases=['A','B','C'];let s='';
   s+=SVG.ln(90,ys,743,ys,COLORS.red,3.5)+SVG.ln(90,yb,743,yb,COLORS.blue,3.5);
   s+=SVG.t(99,49,'+ DC',17,COLORS.red,undefined,750)+SVG.t(100,448,'− DC',17,COLORS.blue,undefined,750);
   s+=SVG.ln(739,ys,773,ys,COLORS.red,2.5)+SVG.ln(739,yb,773,yb,COLORS.blue,2.5)+SVG.ln(772,ys,772,197,COLORS.amber,2.2)+SVG.cap(772,244,35)+SVG.ln(772,252,772,yb,COLORS.amber,2.2)+SVG.t(798,244,'C',15,COLORS.amber,'end',720,true);
   for(let k=0;k<3;k++){
     const x=xs[k],isSel=phases[k].toLowerCase()===leg;
     const sc=isSel?COLORS.teal:'#69859b';
     s+=SVG.ln(x,ys,x,102,COLORS.blue,3)+SVG.ln(x,176,x,250,COLORS.blue,3)+SVG.ln(x,323,x,yb,COLORS.blue,3);
     for(let n=0;n<2;n++){
       const top=n===0,cy=top?141:286,on=isSel&&(top===topState);
       const ink=on?COLORS.teal:'#8aa2b5',fill=on?'#1b655d':'#1b334c';
       s+=SVG.r(x-28,cy-29,56,60,fill,ink,7)+SVG.t(x,cy+5,`T${k+1}${top?'U':'L'}`,13,COLORS.white,'middle',750);
       s+=SVG.ln(x-42,cy,x-29,cy,ink,2)+SVG.t(x-44,cy-6,'G',11,ink,'end');
       // Antiparallel diode bypass is drawn in its own loop, from lower terminal to upper.
       const dx=x+60,yt=cy-30,ylo=cy+30;
       s+=SVG.ln(x,yt,dx,yt,'#8aa2b5',1.8)+SVG.ln(x,ylo,dx,ylo,'#8aa2b5',1.8);
       s+=SVG.ln(dx,yt,dx,cy-14,'#8aa2b5',1.8)+SVG.ln(dx,cy+14,dx,ylo,'#8aa2b5',1.8);
       s+=SVG.path(`M${dx-11},${cy+6} L${dx+11},${cy+6} L${dx},${cy-9} Z`,ink,1,'',fill);
       s+=SVG.ln(dx-12,cy-11,dx+12,cy-11,ink,2.2);
     }
     const poleY=218;
     s+=SVG.ln(x,poleY,x-59,poleY,sc,3)+SVG.c(x,poleY,4,sc)+SVG.t(x-60,poleY-7,`${phases[k]} AC`,14,sc,'end',800);
     s+=SVG.t(x,465,`LEG ${phases[k]}`,14,sc,'middle',750);
   }
   s+=SVG.t(379,28,'Upper and lower devices of one leg must not conduct simultaneously.',14,COLORS.muted,'middle');
   return SVG.open(w,h,s,'Three-phase two-level VSC with IGBT switch blocks and antiparallel diodes');
 }
 static dcCap(p){
   let s='';const w=700,h=285;
   s+=SVG.r(65,58,300,188,'#172f44','#416a80',15);
   s+=SVG.t(217,88,'DC LINK',18,COLORS.muted,'middle',750);
   s+=SVG.ln(215,108,215,155,COLORS.amber,4)+SVG.cap(215,164,105)+SVG.ln(215,172,215,238,COLORS.amber,4);
   s+=SVG.t(285,155,'+',21,COLORS.red)+SVG.t(285,185,'−',21,COLORS.blue);
   s+=SVG.t(218,261,`${fmt(p.vdc,1)} kV`,18,COLORS.white,'middle',780);
   s+=SVG.t(481,100,'Finite energy',21,COLORS.teal,'middle',800);
   const e=DCLinkModel.energyKJ(p.cap,p.vdc),pct=clamp(e/190,0,1);
   s+=SVG.r(430,132,238,26,'#253b50','#385a6d',9);
   s+=SVG.r(432,134,234*pct,22,COLORS.teal,'none',7);
   s+=SVG.t(551,201,`${fmt(e,1)} kJ stored`,19,COLORS.white,'middle',760);
   s+=SVG.t(551,232,'E = ½ C Vdc²',15,COLORS.muted,'middle');
   return SVG.open(w,h,s,'DC capacitor and finite stored energy');
 }
}
