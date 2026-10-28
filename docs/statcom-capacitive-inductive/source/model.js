/* Standalone fundamental-frequency equations, aligned with facts_statcom.operation.physics. */
'use strict';
const STATCOMPhysics = (() => {
  const DEFAULT = Object.freeze({E:1.10, V:1.00, X:0.20, Imax:1.00});
  const EPS = 1e-10;
  function check(parameters) {
    for (const name of ['E','V','X','Imax']) {
      const value=parameters[name];
      if (typeof value!=='number' || !Number.isFinite(value) || value<=0) throw Error(`${name} must be positive and finite`);
    }
    return parameters;
  }
  function point(parameters) {
    const p=check(parameters);
    // For delta = 0, I_inj = (E-V)/(jX) = -j(E-V)/X, and S = V*conj(I_inj).
    const Icap=(p.E-p.V)/p.X;
    const Iimag=-Icap;
    const Q=p.V*Icap;
    const withinRating=Math.abs(Icap)<=p.Imax+1e-9;
    const mode=Icap>EPS?'capacitive':Icap<-EPS?'inductive':'neutral';
    return {Icap,Ireal:0,Iimag,Iabs:Math.abs(Icap),P:0,Q,withinRating,mode,
      voltageDifference:p.E-p.V,limitLow:p.V-p.X*p.Imax,limitHigh:p.V+p.X*p.Imax};
  }
  function waveforms(parameters, angleDegrees) {
    const p=check(parameters);
    if(!Number.isFinite(angleDegrees)) throw Error('Angle must be finite');
    const theta=angleDegrees*Math.PI/180;
    const result=point(p);
    const root2=Math.SQRT2;
    return {v:root2*p.V*Math.sin(theta),e:root2*p.E*Math.sin(theta),
      i:root2*result.Iimag*Math.cos(theta)};
  }
  function numeric(value, digits=3, showPlus=false) {
    if(!Number.isFinite(value)) return '—';
    if(Math.abs(value)<0.5*10**(-digits)) value=0;
    return (showPlus && value>0?'+':'')+value.toFixed(digits);
  }
  return Object.freeze({DEFAULT,point,waveforms,numeric});
})();
