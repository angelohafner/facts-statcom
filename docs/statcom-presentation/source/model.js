'use strict';
// These per-unit conventions mirror facts_statcom.operation.physics.CouplingModel.
const DEFAULT = Object.freeze({v:1,e:1.10,x:.20,delta:0,imax:.8,vref:1,droop:.03,gridX:.12,vth:.92,cap:10,vdc:2});
const state = {...DEFAULT};
const clamp = (a,lo,hi)=>Math.min(hi,Math.max(lo,a));
const rad = degrees=>degrees*Math.PI/180;
const fmt = (a,d=2)=>(Math.abs(a)<0.0000001?0:a).toFixed(d);
const posfmt = (a,d=2)=>`${a>1e-7?'+':''}${fmt(a,d)}`;

class STATCOMModel {
  static at(p) {
    if (![p.e,p.v,p.x,p.delta,p.imax].every(Number.isFinite)||p.e<=0||p.v<=0||p.x<=0||p.imax<=0) throw new Error('Invalid operating point');
    const a = rad(p.delta), eReal=p.e*Math.cos(a), eImag=p.e*Math.sin(a);
    // Iinj = (E - V)/(jX) = E*sin(delta)/X + j*(V - E*cos(delta))/X.
    const ir=eImag/p.x, ii=(p.v-eReal)/p.x;
    const i=Math.hypot(ir,ii), pInj=p.v*ir, qInj=-p.v*ii;
    const iCap=-ii, feasible=i<=p.imax+1e-9;
    const mode=qInj>1e-7?'CAPACITIVE':qInj< -1e-7?'INDUCTIVE':'Q ≈ 0';
    return {ir,ii,i,p:pInj,q:qInj,icap:iCap, eReal,eImag,mode,feasible,angleI:i<1e-10?0:Math.atan2(ii,ir)*180/Math.PI};
  }
  static atE(p,e) {return STATCOMModel.at({...p,e});}
}

class VoltageController {
  // The same low-order surrogate as operation.control.simulate_voltage_control.
  static equilibrium(vth,p) {
    const i=clamp((p.vref-vth)/(p.droop+p.gridX),-p.imax,p.imax);
    return {i,v:vth+p.gridX*i};
  }
  static trace(p,kind='both') {
    const events=kind==='sag'?[[0,1],[.15,.88]]:
      kind==='swell'?[[0,1],[.15,1.045]]:[[0,1],[.15,.88],[.42,1.045]];
    const dt=.0005,end=.75,steps=Math.round(end/dt);
    let idx=0;
    let {i,v:meas}=VoltageController.equilibrium(events[0][1],p);
    let z=i;
    const rows=[];
    for(let k=0;k<=steps;k++) {
      const t=k*dt;
      while(idx+1<events.length && t+1e-12>=events[idx+1][0]) idx++;
      const vth=events[idx][1];
      const vpcc=vth+p.gridX*i;
      const error=p.vref-meas-p.droop*i;
      const raw=7*error+z;
      const cmd=clamp(raw,-p.imax,p.imax);
      rows.push({t,vth,vpcc,meas,i,cmd,q:vpcc*i,eReq:vpcc+p.x*i});
      if(k<steps){
        z+=dt*(220*error+40*(cmd-raw));
        i+=dt*(cmd-i)/.012;
        meas+=dt*(vpcc-meas)/.010;
      }
    }
    return {rows,events};
  }
}

class DCLinkModel {
  static energyKJ(c_mF,v_kV){return .5*c_mF*v_kV*v_kV;}
  static energyFrom10PercentSag(c_mF,v_kV){return .19*DCLinkModel.energyKJ(c_mF,v_kV);}
}

// The graphics below deliberately do not import either Python schematic modules or the control model.
const ESC = s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const COLORS={teal:'#4adac2',blue:'#72b3fa',amber:'#ffc078',red:'#ff8491',muted:'#8fa9bc',white:'#eff8ff',grid:'#2a4057',ink:'#15283d',dark:'#0d1b2e'};
