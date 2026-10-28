"""Matplotlib teaching figures based only on operating-point numerical models.

This module never imports the circuit renderer, circuit symbols, or netlists.
All figures use one ordinary plot axis and editable SVG text where available.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..svg import Theme
from .config import OperationCase
from .control import simulate_voltage_control
from .physics import CouplingModel


FIGURE_NAMES = (
    "reactive-power-vs-e",
    "reactive-current-vs-e",
    "phasor-capacitive",
    "phasor-inductive",
    "power-angle",
    "v-i-droop",
    "reactive-current-limit",
    "waveforms-capacitive",
    "waveforms-inductive",
    "voltage-response",
    "current-response",
    "reactive-power-response",
    "converter-voltage-response",
)


@dataclass(frozen=True)
class PlotStyle:
    """Matplotlib-friendly colors following the existing STATCOM/SVC SVG theme."""

    ink: str = Theme().ink
    muted: str = Theme().muted
    accent: str = Theme().accent
    reactor: str = Theme().reactor
    capacitor: str = Theme().capacitor
    paper: str = Theme().paper
    border: str = Theme().border


class OperationFigureRenderer:
    """Render conceptual Matplotlib plots without touching circuit SVG layout."""

    def __init__(self, case: OperationCase | None = None,
                 style: PlotStyle | None = None):
        self.case = case or OperationCase()
        self.style = style or PlotStyle()

    def _setup(self, title: str, subtitle: str):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg
        except ImportError as exc:
            raise RuntimeError(
                "Operation plots require: pip install 'facts-statcom[plots]'"
            ) from exc
        fig = Figure(figsize=(9.8, 5.7), dpi=145, facecolor=self.style.paper)
        FigureCanvasAgg(fig)
        ax = fig.add_axes((.105, .23, .84, .59))
        ax.set_facecolor(self.style.paper)
        ax.set_title(title, loc="left", fontweight="bold", fontsize=16,
                     color=self.style.ink, pad=34)
        ax.text(0, 1.055, subtitle, fontsize=9.5, color=self.style.muted,
                transform=ax.transAxes, va="bottom")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for side in ("bottom", "left"):
            ax.spines[side].set_color(self.style.border)
        ax.grid(True, color=self.style.border, alpha=.65, linewidth=.8)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=10, colors=self.style.ink)
        return fig, ax

    def _note(self, fig, message: str):
        fig.text(.105, .085, message, fontsize=9.2, color=self.style.muted,
                 va="top", ha="left", linespacing=1.55)

    def _events(self, ax):
        for event in self.case.voltage_events[1:]:
            ax.axvline(event.time_s, color=self.style.muted, alpha=.5,
                       linewidth=1.1, linestyle=":")

    def _legend(self, ax):
        leg = ax.legend(loc="best", fontsize=9, frameon=True, fancybox=False,
                        facecolor=self.style.paper, edgecolor=self.style.border)
        if leg:
            for text in leg.get_texts():
                text.set_color(self.style.ink)

    def reactive_power_vs_e(self):
        fig, ax = self._setup("Reactive power versus converter voltage",
                              "Fundamental-only operation at zero phase shift")
        c = self.case.coupling
        e_low, e_high = self.case.converter_voltage_low_pu, self.case.converter_voltage_high_pu
        n = 301
        es = [e_low + (e_high-e_low)*i/(n-1) for i in range(n)]
        points = [c.operating_point(e) for e in es]
        qs = [p.q_injected_pu for p in points]
        feasible = [p.q_injected_pu if p.current_within_rating else math.nan
                    for p in points]
        ax.plot(es, qs, color=self.style.muted, ls="--", lw=1.7,
                label="Ideal, unrestricted $Q_{\\mathrm{inj}}$")
        ax.plot(es, feasible, color=self.style.accent, lw=3.0,
                label="Within converter current rating")
        ax.axvline(c.v_pcc_pu, color=self.style.ink, lw=1.1, ls=":")
        ax.axhline(0, color=self.style.ink, lw=1.0)
        ax.axhspan(0, max(qs)*1.07, facecolor=self.style.accent, alpha=.055)
        ax.axhspan(min(qs)*1.07, 0, facecolor=self.style.capacitor, alpha=.055)
        ax.text(.03, .93, "Capacitive | $Q_{\\mathrm{inj}}>0$", color=self.style.accent,
                transform=ax.transAxes, fontsize=10)
        ax.text(.03, .08, "Inductive | $Q_{\\mathrm{inj}}<0$", color=self.style.capacitor,
                transform=ax.transAxes, fontsize=10)
        ax.set_xlabel(r"Converter fundamental voltage $E$ (pu)", fontsize=11)
        ax.set_ylabel(r"Reactive power injected $Q_{\mathrm{inj}}$ (pu)", fontsize=11)
        ax.set_xlim(e_low,e_high)
        ax.set_ylim(min(qs)*1.07,max(qs)*1.07)
        self._legend(ax)
        self._note(fig, rf"$Q_{{\mathrm{{inj}}}} = V(E-V)/X$   |   $V={c.v_pcc_pu:.2f}$ pu, $X={c.x_coupling_pu:.2f}$ pu, $\delta=0$." +
                   "\nDashed sections exceed the current rating; clipping Q at fixed E is not a physical solution.")
        return fig

    def reactive_current_vs_e(self):
        fig, ax = self._setup("Reactive current versus converter voltage",
                              "Current positive when the STATCOM supplies capacitive support")
        c=self.case.coupling
        low, high=self.case.converter_voltage_low_pu,self.case.converter_voltage_high_pu
        es=[low+(high-low)*k/300 for k in range(301)]
        i_cap=[c.operating_point(e).i_capacitive_pu for e in es]
        valid=[i if abs(i) <= c.i_limit_pu+1e-10 else math.nan for i in i_cap]
        ax.plot(es,i_cap,color=self.style.muted,lw=1.6,ls="--",label="Ideal current (no rating limit)")
        ax.plot(es,valid,color=self.style.reactor,lw=3,label="Within current rating")
        ax.axhline(c.i_limit_pu,color=self.style.capacitor,ls=":",label="$+I_{\\max}$")
        ax.axhline(-c.i_limit_pu,color=self.style.capacitor,ls=":")
        ax.axhline(0,color=self.style.ink,lw=1.0)
        ax.axvline(c.v_pcc_pu,color=self.style.ink,lw=1.0,ls=":")
        ax.set_xlabel(r"Converter fundamental voltage $E$ (pu)",fontsize=11)
        ax.set_ylabel(r"Capacitive injection current $I_{\mathrm{cap}}$ (pu)",fontsize=11)
        ax.set_xlim(low,high)
        self._legend(ax)
        self._note(fig,r"$I_{\mathrm{cap}}=(E-V)/X$ for $\delta=0$; $Q_{\mathrm{inj}}=V I_{\mathrm{cap}}$."+
                   "\nBy convention the injected dq q-axis current is $i_q=-I_{\\mathrm{cap}}$ when $v_q=0$.")
        return fig

    def _phasor(self, capacitive: bool):
        c=self.case.coupling
        offset=min(.45*c.x_coupling_pu*c.i_limit_pu,.12)
        e = c.v_pcc_pu + (offset if capacitive else -offset)
        p=c.operating_point(e)
        title = "Capacitive STATCOM phasors" if capacitive else "Inductive STATCOM phasors"
        subtitle = "Converter-current reference direction: VSC  →  PCC"
        fig, ax = self._setup(title,subtitle)
        ax.set_aspect("equal",adjustable="box")
        ax.grid(False)
        ax.axhline(0,color=self.style.border,lw=1.1)
        ax.axvline(0,color=self.style.border,lw=1.1)
        # V and E are collinear for delta=0; draw E first and overlay V.
        ax.annotate("", xy=(e,0), xytext=(0,0),
                    arrowprops=dict(arrowstyle="-|>",color=self.style.capacitor,lw=4,mutation_scale=16))
        ax.annotate("",xy=(c.v_pcc_pu,0),xytext=(0,0),
                    arrowprops=dict(arrowstyle="-|>",color=self.style.reactor,lw=2.4,mutation_scale=12))
        ax.annotate("",xy=(0,p.i_injected.imag),xytext=(0,0),
                    arrowprops=dict(arrowstyle="-|>",color=self.style.accent,lw=2.6,mutation_scale=15))
        ax.scatter([e,c.v_pcc_pu],[0,0],s=29,
                   color=[self.style.capacitor,self.style.reactor],zorder=5)
        ax.text(c.v_pcc_pu,.085,r"$V$",color=self.style.reactor,fontsize=15,ha="center")
        ax.text(e,-.12,r"$E$",color=self.style.capacitor,fontsize=15,ha="center")
        ax.text(-.09,p.i_injected.imag*.58,r"$I_{\mathrm{inj}}$",
                ha="right",fontsize=12,color=self.style.accent,rotation=0)
        # The jXI arrow lies between the actual voltage phasor endpoints.
        ax.annotate("",xy=(e,-.18),xytext=(c.v_pcc_pu,-.18),
                    arrowprops=dict(arrowstyle="->",color=self.style.ink,lw=2.2))
        ax.text((c.v_pcc_pu+e)/2,-.23,r"$jXI$",ha="center",va="top",fontsize=12,
                color=self.style.ink)
        ax.set_xlim(-.12,1.24)
        if capacitive:
            ax.set_ylim(-.65, .20)
        else:
            ax.set_ylim(-.20, .65)
        ax.set_xlabel("Real axis (pu)",fontsize=11)
        ax.set_ylabel("Imaginary axis (pu)",fontsize=11)
        self._note(fig,"$E=V+jXI$; injected current positive from converter to PCC."
                   +f"  $Q_{{\\mathrm{{inj}}}}={p.q_injected_pu:+.3f}$ pu."
                   +"\nThe current arrow is $-90^\\circ$ for capacitive injection, $+90^\\circ$ for inductive absorption.\n"
                   +"This differs from current referenced from PCC into the compensator.")
        return fig

    def power_angle(self):
        fig,ax=self._setup("Active and reactive power versus phase angle",
                           "Hypothetical fundamental phasor transfer; not sustained DC operation")
        c=self.case.coupling
        e=self.case.nominal_e_pu
        # Choose a compact region and distinguish infeasible points explicitly.
        degrees=[-12+24*k/300 for k in range(301)]
        points=[c.operating_point(e,angle) for angle in degrees]
        ps=[p.p_injected_pu for p in points]
        qs=[p.q_injected_pu for p in points]
        ax.plot(degrees,ps,color=self.style.reactor,lw=2.7,
                label=r"Active power $P_{\mathrm{inj}}$")
        ax.plot(degrees,qs,color=self.style.accent,lw=2.7,
                label=r"Reactive power $Q_{\mathrm{inj}}$")
        if any(not p.current_within_rating for p in points):
            ax.scatter([d for d,p in zip(degrees,points) if not p.current_within_rating][::14],
                       [p.p_injected_pu for p in points if not p.current_within_rating][::14],
                       s=13,marker="x",color=self.style.capacitor,label="Current rating exceeded")
        ax.axvline(0,color=self.style.ink,ls=":",lw=1.0)
        ax.axhline(0,color=self.style.ink,lw=1.0)
        ax.set_xlabel(r"Converter angle $\delta$ relative to PCC (degrees)",fontsize=11)
        ax.set_ylabel("Three-phase injected power (pu)",fontsize=11)
        self._legend(ax)
        self._note(fig,r"$P_{\mathrm{inj}}=VE\sin\delta/X$, $Q_{\mathrm{inj}}=V(E\cos\delta-V)/X$."
                   "\nA STATCOM with only a DC capacitor cannot sustain nonzero $P$ (apart from small losses absorption).")
        return fig

    def vi_droop(self):
        fig,ax=self._setup("STATCOM voltage-control V–I characteristic",
                           "Injected capacitive current is positive; converter current is limited")
        u=self.case.control
        vs=[.93+.14*k/350 for k in range(351)]
        cmd=[u.droop_current_reference(v) for v in vs]
        ax.plot(vs,cmd,color=self.style.accent,lw=3.1,
                label="Voltage control with saturated current")
        ax.axvline(u.v_ref_pu,color=self.style.muted,ls="--",lw=1.2,label="$V_{\\mathrm{ref}}$")
        ax.axhline(u.current_limit_pu,color=self.style.capacitor,ls=":",lw=1.4)
        ax.axhline(-u.current_limit_pu,color=self.style.capacitor,ls=":",lw=1.4)
        ax.axhline(0,color=self.style.ink,lw=1.0)
        ax.text(.025,.965,"Capacitive support",transform=ax.transAxes,
                color=self.style.accent,fontsize=10)
        ax.text(.72,.045,"Inductive absorption",transform=ax.transAxes,
                color=self.style.capacitor,fontsize=10)
        ax.set_xlim(min(vs),max(vs))
        ax.set_ylim(-u.current_limit_pu*1.22,u.current_limit_pu*1.22)
        ax.set_xlabel(r"Measured PCC voltage $V_{\mathrm{PCC}}$ (pu)",fontsize=11)
        ax.set_ylabel(r"Injected capacitive current reference $I_{\mathrm{cap,ref}}$ (pu)",fontsize=10.3)
        self._legend(ax)
        self._note(fig,rf"$I_{{\mathrm{{cap,ref}}}}=\mathrm{{clip}}((V_{{\mathrm{{ref}}}}-V_{{\mathrm{{PCC}}}})/d,\pm I_{{\max}})$; $d={u.droop_pu_per_i_pu:.3f}$ pu/pu."
                   "\nUnlike SVC susceptance, the STATCOM current rating is approximately constant across voltage dips.")
        return fig

    def reactive_current_limit(self):
        fig,ax=self._setup("Reactive power available at the current limit",
                           "STATCOM power capability decreases with voltage even at constant rated current")
        u=self.case.control
        v=[.45+.65*k/280 for k in range(281)]
        cap=[val*u.current_limit_pu for val in v]
        induct=[-val*u.current_limit_pu for val in v]
        ax.plot(v,cap,color=self.style.accent,lw=3,
                label="STATCOM max capacitive injection")
        ax.plot(v,induct,color=self.style.capacitor,lw=3,
                label="STATCOM max inductive absorption")
        ax.axhline(0,color=self.style.ink,lw=.9)
        ax.set_xlabel(r"PCC voltage $V_{\mathrm{PCC}}$ (pu)",fontsize=11)
        ax.set_ylabel(r"Reactive power $Q_{\mathrm{inj}}$ (pu)",fontsize=11)
        self._legend(ax)
        self._note(fig,rf"$Q_{{\max}}=V I_{{\max}}$ with $I_{{\max}}={u.current_limit_pu:.2f}$ pu."
                   "\nOnly the AC current limit is represented; DC voltage and modulation headroom are assumed sufficient.")
        return fig

    def _waveform(self, capacitive: bool):
        c=self.case.coupling
        e=c.v_pcc_pu + (.10 if capacitive else -.10)
        p=c.operating_point(e)
        period=1/c.frequency_hz
        times=[2*period*k/800 for k in range(801)]
        grid,converter,current=c.instantaneous_fundamentals(times,e)
        title=("Capacitive injection: fundamental waveforms" if capacitive
               else "Inductive absorption: fundamental waveforms")
        fig,ax=self._setup(title,"One phase, instantaneous voltages and converter-to-grid current")
        t_ms=[1000*t for t in times]
        ax.plot(t_ms,grid,color=self.style.reactor,lw=2.15,label=r"PCC voltage $v(t)$")
        ax.plot(t_ms,converter,color=self.style.capacitor,lw=1.8,ls="--",
                label=r"Converter fundamental $e(t)$")
        ax.plot(t_ms,current,color=self.style.accent,lw=2.1,label=r"Injected current $i(t)$")
        ax.axhline(0,color=self.style.ink,lw=.8)
        ax.set_xlabel("Time (ms)",fontsize=11)
        ax.set_ylabel("Voltage / current on their own pu bases",fontsize=10.5)
        ax.set_xlim(0,t_ms[-1])
        self._legend(ax)
        angle=-90 if capacitive else 90
        self._note(fig,f"$E={e:.2f}$ pu, $V={c.v_pcc_pu:.2f}$ pu, $X={c.x_coupling_pu:.2f}$ pu, "
                   +rf"$Q_{{\mathrm{{inj}}}}={p.q_injected_pu:+.3f}$ pu. Current is {angle:+d}° relative to PCC voltage."
                   "\nFundamental sinusoids only; not switching/PWM, harmonics or real-time EMT simulation.")
        return fig

    def _history(self):
        return simulate_voltage_control(
            self.case.control, self.case.voltage_events,
            coupling_x_pu=self.case.coupling.x_coupling_pu,
            end_time_s=self.case.end_time_s,
            time_step_s=self.case.time_step_s,
        )

    def voltage_response(self):
        fig,ax=self._setup("Voltage regulation during grid disturbances",
                           "Low-order PI + droop + current-loop lag + weak-grid surrogate")
        history=self._history()
        ax.plot(history.time_s,history.v_thevenin_pu,color=self.style.muted,
                ls="--",lw=1.8,label=r"Uncompensated grid $V_{\mathrm{TH}}$")
        ax.plot(history.time_s,history.v_pcc_pu,color=self.style.reactor,
                lw=2.6,label=r"Controlled $V_{\mathrm{PCC}}$")
        ax.axhline(self.case.control.v_ref_pu,color=self.style.accent,
                   lw=1.45,ls=":",label=r"$V_{\mathrm{ref}}$")
        self._events(ax)
        ax.set_xlabel("Time (s)",fontsize=11)
        ax.set_ylabel("Voltage (pu)",fontsize=11)
        ax.set_xlim(0,self.case.end_time_s)
        self._legend(ax)
        self._note(fig,r"Grid surrogate: $V_{\mathrm{PCC}}\approx V_{\mathrm{TH}}+X_{\mathrm{TH}} I_{\mathrm{cap}}$."
                   "\nCurrent saturation can prevent exact voltage restoration; dynamics are illustrative, not EMT.")
        return fig

    def current_response(self):
        fig,ax=self._setup("Reactive current controller response",
                           "Positive current injects capacitive support; negative current absorbs reactive power")
        h=self._history()
        ax.plot(h.time_s,h.i_reference_pu,color=self.style.capacitor,
                ls="--",lw=1.6,label="Saturated PI current command")
        ax.plot(h.time_s,h.i_capacitive_pu,color=self.style.accent,
                lw=2.6,label="Injected current (first-order lag)")
        limit=self.case.control.current_limit_pu
        for val in (-limit,limit):
            ax.axhline(val,color=self.style.muted,ls=":",lw=1.1)
        self._events(ax)
        ax.axhline(0,color=self.style.ink,lw=.85)
        ax.set_xlabel("Time (s)",fontsize=11)
        ax.set_ylabel(r"Capacitive injected current $I_{\mathrm{cap}}$ (pu)",fontsize=11)
        ax.set_xlim(0,self.case.end_time_s)
        ax.set_ylim(-limit*1.15,limit*1.15)
        self._legend(ax)
        self._note(fig,"Outer voltage PI includes droop and anti-windup; inner current follows a first-order lag."
                   "\nNo PLL, dq cross-coupling, actual semiconductor gating or dc-link dynamics are simulated.")
        return fig

    def reactive_power_response(self):
        fig,ax=self._setup("Injected reactive power during voltage control",
                           "Converter supplies vars during the sag and absorbs vars during an overvoltage")
        h=self._history()
        ax.plot(h.time_s,h.q_injected_pu,color=self.style.accent,lw=2.8,
                label=r"$Q_{\mathrm{inj}}=V_{\mathrm{PCC}} I_{\mathrm{cap}}$")
        self._events(ax)
        ax.axhline(0,color=self.style.ink,lw=1)
        ax.set_xlabel("Time (s)",fontsize=11)
        ax.set_ylabel(r"Reactive power injected $Q_{\mathrm{inj}}$ (pu)",fontsize=11)
        ax.set_xlim(0,self.case.end_time_s)
        self._legend(ax)
        self._note(fig,"Q is measured at the PCC; positive = capacitive injection, negative = inductive absorption."
                   "\nThe control model uses a linearized grid; this is not a transient stability or EMT calculation.")
        return fig

    def converter_voltage_response(self):
        fig,ax=self._setup("Required converter fundamental voltage",
                           "Zero-angle estimate needed to support the injected reactive current")
        h=self._history()
        ax.plot(h.time_s,h.e_required_pu,color=self.style.capacitor,lw=2.7,
                label=r"Required $E=V_{\mathrm{PCC}}+X I_{\mathrm{cap}}$")
        ax.plot(h.time_s,h.v_pcc_pu,color=self.style.reactor,lw=2.0,
                label=r"PCC voltage $V_{\mathrm{PCC}}$")
        self._events(ax)
        ax.set_xlabel("Time (s)",fontsize=11)
        ax.set_ylabel("Fundamental phase RMS voltage (pu)",fontsize=11)
        ax.set_xlim(0,self.case.end_time_s)
        self._legend(ax)
        self._note(fig,"Shows the ideal voltage magnitude required by the reactive-current model at $\\delta=0$."
                   "\nDC-link and modulation voltage limits are not enforced; this is not a PWM command.")
        return fig

    def figure(self, name: str):
        """Return a fresh Matplotlib Figure for one named educational result."""
        builders: dict[str, Callable[[], object]] = {
            "reactive-power-vs-e": self.reactive_power_vs_e,
            "reactive-current-vs-e": self.reactive_current_vs_e,
            "phasor-capacitive": lambda: self._phasor(True),
            "phasor-inductive": lambda: self._phasor(False),
            "power-angle": self.power_angle,
            "v-i-droop": self.vi_droop,
            "reactive-current-limit": self.reactive_current_limit,
            "waveforms-capacitive": lambda: self._waveform(True),
            "waveforms-inductive": lambda: self._waveform(False),
            "voltage-response": self.voltage_response,
            "current-response": self.current_response,
            "reactive-power-response": self.reactive_power_response,
            "converter-voltage-response": self.converter_voltage_response,
        }
        if name not in builders:
            raise ValueError(f"Unknown figure: {name}")
        return builders[name]()

    def save(self, name: str, path: str | Path) -> Path:
        """Save editable SVG or high-resolution PNG using local figure drawing."""
        if name not in FIGURE_NAMES:
            raise ValueError(f"Unknown figure: {name}")
        path=Path(path)
        if path.suffix.lower() not in {".svg", ".png"}:
            raise ValueError("Operation output must be .svg or .png")
        try:
            import matplotlib as mpl
        except ImportError as exc:
            raise RuntimeError("Install with pip install 'facts-statcom[plots]'") from exc
        path.parent.mkdir(parents=True,exist_ok=True)
        with mpl.rc_context({
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "stix",
            "svg.fonttype": "none",
            "svg.hashsalt": "facts-statcom-operations-v1",
        }):
            fig=self.figure(name)
            try:
                fig.savefig(path,format=path.suffix[1:].lower(),dpi=175,
                            bbox_inches="tight",pad_inches=.25,
                            metadata=({"Creator":"facts-statcom operating-point figures",
                                       "Date":None} if path.suffix.lower()==".svg"
                                      else {"Software":"facts-statcom"}))
            finally:
                fig.clear()
        return path
