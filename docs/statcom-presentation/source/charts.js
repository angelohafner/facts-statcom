class ChartRenderer {
 static powerVsE(p,{compact=false}={}){
  const w=compact?560:900,h=compact?235:440;
  const emin=.65,emax=1.40;
  const points=Array.from({length:260},(_,i)=>{let e=emin+(emax-emin)*i/259,o=STATCOMModel.atE(p,e);return {e,q:o.q,within:o.feasible};});
  const current=STATCOMModel.at(p);
  const ym=Math.max(1.1,Math.ceil(Math.max(...points.map(pt=>Math.abs(pt.q)))/.5)*.5);
  const ax=setupPlot(w,h,emin,emax,-ym,ym,{xLabel:'Converter fundamental E (pu)',yLabel:'Q injected (pu)',compact});
  let s=ax.bg;
  // Physically permitted samples have solid strokes; violations remain visible but dashed.
  s+=pathSegments(points,pt=>pt.within,ax.x,ax.y,COLORS.teal,compact?2.6:3.6);
  s+=SVG.ln(ax.x(p.e),ax.t,ax.x(p.e),h-ax.b,COLORS.amber,1.7,'4 5');
  const mark=current.feasible?COLORS.amber:COLORS.red;
  s+=SVG.c(ax.x(p.e),ax.y(current.q),compact?5:7,mark,COLORS.white);
  s+=SVG.t(ax.x(p.e)-8,clamp(ax.y(current.q)-12,ax.t+15,h-ax.b-6),`Q=${posfmt(current.q,2)}`,compact?11:15,mark,'end',760);
  if(compact){s+=SVG.t(w-15,19,current.feasible?'within rating':'OUTSIDE RATING',10,current.feasible?COLORS.teal:COLORS.red,'end',760);}
  else{
   s+=SVG.t(w-30,29,'Q > 0: capacitive injection',14,COLORS.teal,'end',740);
   s+=SVG.t(w-30,h-53,'Q < 0: inductive absorption',14,COLORS.amber,'end',740);
   s+=SVG.ln(w-250,h-17,w-224,h-17,COLORS.teal,3)+SVG.t(w-213,h-13,'Within rating',12,COLORS.muted);
   s+=SVG.ln(w-118,h-17,w-92,h-17,COLORS.teal,3,'5 5')+SVG.t(w-81,h-13,'Not rated',12,COLORS.muted);
  }
  return SVG.open(w,h,s,'Injected reactive power versus VSC fundamental voltage');
 }
 static currentLimit(p){
  const w=940,h=460,ax=setupPlot(w,h,0,1.24,-1.65,1.65,{xLabel:'PCC voltage (pu)',yLabel:'Q limit (pu)'});
  const ps=Array.from({length:121},(_,i)=>i/100);
  const qplus=ps.map(v=>({v,q:v*p.imax})),qminus=ps.map(v=>({v,q:-v*p.imax})),qsvc=ps.map(v=>({v,q:v*v*p.imax}));
  let s=ax.bg;
  s+=SVG.path(sequencePath(qplus,d=>ax.x(d.v),d=>ax.y(d.q)),COLORS.teal,4);
  s+=SVG.path(sequencePath(qminus,d=>ax.x(d.v),d=>ax.y(d.q)),COLORS.amber,4);
  s+=SVG.path(sequencePath(qsvc,d=>ax.x(d.v),d=>ax.y(d.q)),COLORS.blue,2.4,'8 7');
  s+=SVG.c(ax.x(p.v),ax.y(p.v*p.imax),7,COLORS.teal,COLORS.white);
  s+=SVG.t(w-30,45,`I max = ${fmt(p.imax,2)} pu`,15,COLORS.white,'end',740);
  s+=SVG.t(w-35,82,'STATCOM +V Imax',14,COLORS.teal,'end');
  s+=SVG.t(w-35,104,'SVC +V² B (normalized)',14,COLORS.blue,'end');
  s+=SVG.t(w-35,126,'STATCOM −V Imax',14,COLORS.amber,'end');
  return SVG.open(w,h,s,'Idealized STATCOM current limit and SVC quadratic voltage dependence');
 }
 static waveforms(p,{compact=false}={}){
  const w=compact?560:960,h=compact?245:460;
  const op=STATCOMModel.at(p),timeCycles=2,tmax=timeCycles/p.freq ||2/60;
  const x0=compact?35:53,x1=w-(compact?11:20);
  const yTop=compact?27:36,yBot=compact?224:423,midH=(yBot-yTop-19)/2;
  const phases=[0,-2*Math.PI/3,2*Math.PI/3],col=[COLORS.teal,COLORS.blue,COLORS.amber];
  let s='';
  for(let pane=0;pane<2;pane++){
   const top=yTop+pane*(midH+19),center=top+midH/2,sca=midH/(compact?4.25:4.0);
   s+=SVG.r(x0,top,x1-x0,midH,'#101f34','#2c4259',3);
   s+=SVG.ln(x0,center,x1,center,'#60819b',1,'3 3');
   for(let j=1;j<4;j++){const xx=x0+j*(x1-x0)/4;s+=SVG.ln(xx,top,xx,top+midH,COLORS.grid,.8,'3 3');}
   const a=Array.from({length:180},(_,k)=>k/179);
   for(let ph=0;ph<3;ph++){
    const pts=a.map(z=>({z,val:Math.SQRT2*(pane===0?p.v:op.i)*Math.sin(z*timeCycles*Math.PI*2+phases[ph]+(pane===0?0:rad(op.angleI)))}));
    s+=SVG.path(sequencePath(pts,d=>x0+d.z*(x1-x0),d=>center-d.val*sca),col[ph],compact?1.8:2.8);
   }
   if(pane===0){
    const epts=a.map(z=>({z,val:Math.SQRT2*p.e*Math.sin(z*timeCycles*Math.PI*2+rad(p.delta))}));
    s+=SVG.path(sequencePath(epts,d=>x0+d.z*(x1-x0),d=>center-d.val*sca),COLORS.red,compact?1.1:1.7,'5 4');
   }
   s+=SVG.t(x0+7,top+17,pane===0?'PCC voltage (pu instantaneous)':'Injected current (pu instantaneous)',compact?10:13,COLORS.white,undefined,740);
  }
  s+=SVG.t((x0+x1)/2,h-4,'2 fundamental cycles   ·   phases A / B / C',compact?10:12,COLORS.muted,'middle');
  if(!compact){
   const xx=w-320,yy=15;
   s+=SVG.t(xx,yy,'A',12,COLORS.teal,undefined,780)+SVG.t(xx+40,yy,'B',12,COLORS.blue,undefined,780)+SVG.t(xx+80,yy,'C',12,COLORS.amber,undefined,780)+SVG.t(xx+127,yy,'Eₐ (dashed)',12,COLORS.red,undefined,750);
  }
  if(window.waveCursorOn){
   const z=(Date.now()/26)%1000/1000,xx=x0+z*(x1-x0);
   s+=SVG.ln(xx,yTop,xx,yBot,'#faf4b5',1.6,'4 3');
  }
  return SVG.open(w,h,s,'Balanced three-phase fundamental PCC voltage and converter-to-grid injected current');
 }
 static dynamic(p,kind){
  const {rows,events}=VoltageController.trace(p,kind);const w=980,h=505;
  const xLeft=67,xRight=951,top=25,panelH=129,gap=29;
  let s='';
  const panes=[
   {name:'PCC and Thevenin voltage (pu)',key:'vpcc',lo:.75,hi:1.12,with:'vth'},
   {name:'Capacitive reactive current (pu)',key:'i',lo:-1.5,hi:1.5,with:'cmd'},
   {name:'Required converter E (pu)',key:'eReq',lo:.68,hi:1.39},
  ];
  for(let pi=0;pi<3;pi++){
   const row=panes[pi],y0=top+pi*(panelH+gap);
   const xx=t=>xLeft+(xRight-xLeft)*(t/.75);
   const yy=v=>y0+panelH-(v-row.lo)/(row.hi-row.lo)*panelH;
   s+=SVG.r(xLeft,y0,xRight-xLeft,panelH,'#0e2135','#30475a',2);
   for(let m=1;m<4;m++){const v=row.lo+(row.hi-row.lo)*m/4;s+=SVG.ln(xLeft,yy(v),xRight,yy(v),COLORS.grid,.8,'2 4')+SVG.t(xLeft-9,yy(v)+4,fmt(v,2),11,COLORS.muted,'end');}
   for(const [ev] of events.slice(1))s+=SVG.ln(xx(ev),y0,xx(ev),y0+panelH,COLORS.amber,1.3,'4 5');
   const sampled=rows.filter((_,j)=>j%4===0);
   s+=SVG.path(sequencePath(sampled,d=>xx(d.t),d=>yy(d[row.key])),COLORS.teal,2.8);
   if(row.with)s+=SVG.path(sequencePath(sampled,d=>xx(d.t),d=>yy(d[row.with])),COLORS.blue,1.7,'5 4');
   s+=SVG.t(xLeft+13,y0+20,row.name,14,COLORS.white,undefined,730);
  }
  for(const t of [0,.15,.30,.45,.60,.75])s+=SVG.t(xLeft+(xRight-xLeft)*t/.75,h-4,fmt(t,2),11,COLORS.muted,'middle');
  s+=SVG.t(xRight-16,22,'solid: PCC / actual     dashed: grid / command',11,COLORS.muted,'end');
  return SVG.open(w,h,s,'Averaged voltage control response to Thevenin voltage steps');
 }
 static droop(p,{compact=false}={}){
  const w=compact?560:930,h=compact?232:465;
  const xmax=1.65,ax=setupPlot(w,h,-xmax,xmax,.70,1.25,{xLabel:'Icap injected (pu)',yLabel:'PCC voltage (pu)',compact,yticks:compact?3:5});
  const ds=Array.from({length:140},(_,k)=>({i:-xmax+k*2*xmax/139}));
  const eq=VoltageController.equilibrium(p.vth,p);
  let s=ax.bg;
  s+=SVG.path(sequencePath(ds,d=>ax.x(d.i),d=>ax.y(p.vref-p.droop*d.i)),COLORS.teal,compact?2.5:3.5);
  s+=SVG.path(sequencePath(ds,d=>ax.x(d.i),d=>ax.y(p.vth+p.gridX*d.i)),COLORS.blue,compact?1.6:2.6,'6 5');
  s+=SVG.ln(ax.x(-p.imax),ax.t,ax.x(-p.imax),h-ax.b,COLORS.red,1.4,'4 5');
  s+=SVG.ln(ax.x(p.imax),ax.t,ax.x(p.imax),h-ax.b,COLORS.red,1.4,'4 5');
  s+=SVG.c(ax.x(eq.i),ax.y(eq.v),compact?5:8,COLORS.amber,COLORS.white);
  s+=SVG.t(clamp(ax.x(eq.i)+9,ax.l+20,w-85),clamp(ax.y(eq.v)-11,ax.t+12,h-ax.b-5),`I = ${posfmt(eq.i,2)}`,compact?11:14,COLORS.amber,'start',760);
  if(!compact){s+=SVG.t(w-29,29,'Droop Vref − k Icap',14,COLORS.teal,'end')+SVG.t(w-29,49,'Grid Vth + Xth Icap',14,COLORS.blue,'end')+SVG.t(w-29,69,'Converter |Icap| limit',14,COLORS.red,'end');}
  return SVG.open(w,h,s,'Voltage droop and linearized Thevenin grid characteristic');
 }
}

const CONTROL_INFO={
 voltage:['PCC voltage regulation','The voltage reference, measured PCC voltage and droop form the voltage-loop error. A PI loop requests capacitive or inductive reactive current.'],
 pll:['Phase-locked loop','The PLL estimates the PCC voltage phase angle for the dq current reference frame. A real PLL has dynamics not modeled here.'],
 current:['Inner current control','Tracks requested d- and q-axis currents, limits magnitude and produces an AC converter voltage reference.'],
 pwm:['Modulation and gate signals','Converts voltage references to device switching commands. Actual PWM harmonics are outside the fundamental-frequency model.'],
 dc:['DC-link voltage loop','A separate regulator requests a small active-current component to cover losses and restore the capacitor energy.'],
 measure:['Measurements','Current, PCC voltage and DC-link measurements close the feedback loops.']
};
class ControlDiagram {
 static box(x,y,w,h,title,sub,id,focus){const active=id===focus,c=active?COLORS.teal:'#63849e';return `<g data-control="${id}" style="cursor:pointer">${SVG.r(x,y,w,h,active?'#1a514d':'#20354e',c,8)}${SVG.t(x+w/2,y+24,title,15,COLORS.white,'middle',770)}${SVG.t(x+w/2,y+44,sub,11,COLORS.muted,'middle')}</g>`;}
 static draw(focus='voltage'){
  const w=1170,h=363;let s='';
  s+=SVG.t(36,35,'Vref',15,COLORS.teal)+SVG.arrow(81,29,139,29,COLORS.muted,2);
  s+=ControlDiagram.box(140,8,165,68,'Voltage loop','Vref − Vmeas − droop Iq','voltage',focus);
  s+=SVG.arrow(306,41,349,41,COLORS.muted,2);
  s+=ControlDiagram.box(350,8,157,68,'PI + limits','Iq reference','voltage',focus);
  s+=SVG.arrow(508,41,549,41,COLORS.muted,2);
  s+=ControlDiagram.box(550,8,176,68,'Current controller','Id / Iq tracking','current',focus);
  s+=SVG.arrow(727,41,775,41,COLORS.muted,2);
  s+=ControlDiagram.box(776,8,148,68,'PWM','Gate patterns','pwm',focus);
  s+=SVG.arrow(924,41,966,41,COLORS.muted,2);
  s+=ControlDiagram.box(969,8,168,68,'VSC','Converter terminal E','pwm',focus);
  // Secondary active-current reference enters the same current controller.
  s+=ControlDiagram.box(251,151,200,69,'DC voltage loop','Vdc* − Vdc → Id*','dc',focus);
  s+=SVG.path('M451,186 L635,186 L635,76',COLORS.blue,2)+SVG.arrow(635,110,635,78,COLORS.blue,2);
  s+=ControlDiagram.box(17,151,194,69,'PLL','PCC phase → θ','pll',focus);
  s+=SVG.path('M211,186 L590,186 L590,76',COLORS.blue,2)+SVG.arrow(590,110,590,79,COLORS.blue,2);
  s+=ControlDiagram.box(808,157,259,70,'Measurements','Vpcc · Iabc · Vdc','measure',focus);
  s+=SVG.path('M1051,77 L1051,153',COLORS.amber,1.8,'4 4')+SVG.arrow(1051,130,1051,153,COLORS.amber,2);
  s+=SVG.path('M808,196 L478,196 L478,130 L224,130 L224,78',COLORS.amber,2,'5 4')+SVG.arrow(224,105,224,79,COLORS.amber,2);
  s+=SVG.path('M879,227 L879,296 L360,296 L360,221',COLORS.amber,1.7,'5 4')+SVG.arrow(360,243,360,222,COLORS.amber,1.8);
  s+=SVG.path('M927,227 L927,326 L117,326 L117,221',COLORS.amber,1.7,'5 4')+SVG.arrow(117,247,117,223,COLORS.amber,1.8);
  s+=SVG.t(495,285,'feedback signals',12,COLORS.amber,undefined,720);
  s+=SVG.t(1031,350,'Simplified functional structure (not actual control firmware)',12,COLORS.muted,'end');
  return SVG.open(w,h,s,'Functional STATCOM voltage current PLL and DC-link control system');
 }
}

const TECHNOLOGIES={
 'two-level':{name:'Two-level voltage-source converter',summary:'Three half-bridge legs, six controllable devices and antiparallel diodes. Each pole switches between DC rails.',bullet:['Compact conceptual baseline','Higher switching voltage steps at the AC terminals','PWM and filtering shape the fundamental output']},
 'npc':{name:'Three-level NPC converter',summary:'A split DC link and clamping diodes create three selectable pole voltage levels.',bullet:['Midpoint clamping is a real electrical connection','Neutral-point voltage balancing matters','Additional semiconductors improve voltage resolution']},
 'chb-star':{name:'CHB · star connection',summary:'Series-connected H-bridge cells synthesize multiple levels with isolated or floating DC capacitor energy.',bullet:['Each cell has its own DC capacitor','A star connection forms three phase arms','Cell voltage balancing and modulation are essential']},
 'chb-delta':{name:'CHB · delta connection',summary:'Cell arms form a closed delta across phase-to-phase AC terminals.',bullet:['Each branch is a phase-to-phase arm','Circulating currents must be managed','Different zero-sequence and energy-balancing options']},
 'mmc':{name:'MMC · double-star arrangement',summary:'A double-star MMC uses upper/lower arms, arm inductors and many submodules, rather than a simple CHB delta.',bullet:['Each arm contains energy-storing submodules','Upper/lower arm currents demand control','This example is not an HB-MMC switching simulation']}
};
function techFallback(name){
 const w=920,h=500,cm=TECHNOLOGIES[name];let s='';
 s+=SVG.r(35,35,850,430,'#fff','#d6e3eb',14);
 s+=SVG.t(460,80,cm.name,27,'#1b3448','middle',800);
 for(let k=0;k<3;k++){
  const x=220+k*245;
  s+=SVG.t(x,130,`PHASE ${'ABC'[k]}`,16,'#21587c','middle',760);
  for(let n=0;n<(name==='two-level'?2:name==='npc'?4:name==='mmc'?6:3);n++){
   const yy=162+n*(name==='mmc'?37:63);
   s+=SVG.r(x-35,yy,70,name==='mmc'?24:36,name==='mmc'?'#e4f3ef':'#edf3fa','#52849d',4);
   if(name==='mmc')s+=SVG.t(x,yy+17,'SM',11,'#385e76','middle',700);
  }
 }
 s+=SVG.t(460,458,'Illustrative simplified topology (full Python SVG available in repository)',16,'#6a7d8f','middle');
 return SVG.open(w,h,s,cm.name+' simplified topology');
}
