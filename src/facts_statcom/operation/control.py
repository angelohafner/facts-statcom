"""Educational averaged voltage-regulation model for a STATCOM.

This is a voltage-sensitive surrogate and PI regulator, not EMT, switching,
PLL, dc-capacitor, or a calibrated real controller model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .physics import _finite, _finite_positive


def clamp(value: float, lo: float, hi: float) -> float:
    """Saturate a scalar between its physically defined limits."""
    return min(hi, max(lo, value))


@dataclass(frozen=True)
class GridVoltageEvent:
    """Change the open-circuit Thevenin grid voltage at a known instant."""

    time_s: float
    v_thevenin_pu: float

    def __post_init__(self) -> None:
        _finite(self.time_s, "time_s")
        _finite_positive(self.v_thevenin_pu, "v_thevenin_pu")
        if self.time_s < 0:
            raise ValueError("time_s must not be negative")


@dataclass(frozen=True)
class VoltageControlConfig:
    """Per-unit droop PI, measurement/inner-current lags and grid surrogate.

    The injected capacitive current Icap is positive when supplying Q.
    Grid surrogate: V_PCC = V_TH + X_TH * Icap (linearized, not an AC solver).
    PI error: e = Vref - V_measured - droop * Icap.
    Integrator uses back-calculation anti-windup at the current limits.
    """

    v_ref_pu: float = 1.0
    droop_pu_per_i_pu: float = 0.03
    current_limit_pu: float = 0.8
    grid_x_pu: float = 0.12
    kp: float = 7.0
    ki_per_s: float = 220.0
    antiwindup_per_s: float = 40.0
    current_time_constant_s: float = 0.012
    measurement_time_constant_s: float = 0.010

    def __post_init__(self) -> None:
        for name in ("v_ref_pu", "droop_pu_per_i_pu", "current_limit_pu",
                     "grid_x_pu", "kp", "ki_per_s", "antiwindup_per_s",
                     "current_time_constant_s", "measurement_time_constant_s"):
            _finite_positive(getattr(self, name), name)

    def droop_current_reference(self, measured_voltage_pu: float) -> float:
        """Ideal static characteristic; PI dynamics are modeled separately."""
        _finite_positive(measured_voltage_pu, "measured_voltage_pu")
        request = (self.v_ref_pu - measured_voltage_pu) / self.droop_pu_per_i_pu
        return clamp(request, -self.current_limit_pu, self.current_limit_pu)

    def equilibrium(self, v_thevenin_pu: float) -> tuple[float, float]:
        """Return (Icap, VPCC) after the idealized closed-loop PI has settled."""
        _finite_positive(v_thevenin_pu, "v_thevenin_pu")
        current = clamp(
            (self.v_ref_pu - v_thevenin_pu)
            / (self.grid_x_pu + self.droop_pu_per_i_pu),
            -self.current_limit_pu, self.current_limit_pu,
        )
        return current, v_thevenin_pu + self.grid_x_pu * current


@dataclass(frozen=True)
class VoltageControlTrace:
    """Time history of a deliberately low-order, averaged control surrogate."""

    time_s: tuple[float, ...]
    v_thevenin_pu: tuple[float, ...]
    v_pcc_pu: tuple[float, ...]
    v_measured_pu: tuple[float, ...]
    i_capacitive_pu: tuple[float, ...]
    i_reference_pu: tuple[float, ...]
    q_injected_pu: tuple[float, ...]
    e_required_pu: tuple[float, ...]


def simulate_voltage_control(
    settings: VoltageControlConfig,
    events: tuple[GridVoltageEvent, ...],
    *,
    coupling_x_pu: float,
    end_time_s: float = 0.75,
    time_step_s: float = 0.0005,
) -> VoltageControlTrace:
    """Euler integration of a saturated PI with current and measurement lags.

    Only the relationship between reactive current and small-signal PCC voltage
    is simulated. Converter modulation and finite dc-link energy are absent.
    """
    _finite_positive(coupling_x_pu, "coupling_x_pu")
    _finite_positive(end_time_s, "end_time_s")
    _finite_positive(time_step_s, "time_step_s")
    if not events or not all(isinstance(e, GridVoltageEvent) for e in events):
        raise ValueError("events must contain GridVoltageEvent objects")
    if abs(events[0].time_s) > 1e-12:
        raise ValueError("The first voltage event must be at t=0")
    if any(b.time_s <= a.time_s for a, b in zip(events, events[1:])):
        raise ValueError("Events must be in strictly increasing time order")
    if events[-1].time_s >= end_time_s:
        raise ValueError("Last event must occur before end_time_s")
    if time_step_s >= min(settings.current_time_constant_s,
                          settings.measurement_time_constant_s) / 5:
        raise ValueError("time_step_s must resolve the two control time constants")
    intervals = end_time_s / time_step_s
    if intervals > 100_000:
        raise ValueError("Simulation would generate more than 100001 samples")

    i, measured_voltage = settings.equilibrium(events[0].v_thevenin_pu)
    z = i
    time: list[float] = []
    thev: list[float] = []
    vpcc: list[float] = []
    vm: list[float] = []
    actual: list[float] = []
    target: list[float] = []
    q: list[float] = []
    econv: list[float] = []
    idx = 0
    n = math.ceil(intervals)
    for step in range(n + 1):
        t = min(step * time_step_s, end_time_s)
        while idx + 1 < len(events) and t >= events[idx + 1].time_s - 1e-12:
            idx += 1
        vth = events[idx].v_thevenin_pu
        pcc = vth + settings.grid_x_pu * i
        error = settings.v_ref_pu - measured_voltage - settings.droop_pu_per_i_pu * i
        unbounded = settings.kp * error + z
        command = clamp(unbounded, -settings.current_limit_pu,
                        settings.current_limit_pu)
        time.append(t)
        thev.append(vth)
        vpcc.append(pcc)
        vm.append(measured_voltage)
        actual.append(i)
        target.append(command)
        q.append(pcc * i)
        econv.append(pcc + coupling_x_pu * i)

        if step < n:
            step_size = min(time_step_s, end_time_s - t)
            z += step_size * (
                settings.ki_per_s * error
                + settings.antiwindup_per_s * (command - unbounded)
            )
            i += step_size * (command - i) / settings.current_time_constant_s
            measured_voltage += step_size * (pcc - measured_voltage) / settings.measurement_time_constant_s

    return VoltageControlTrace(
        tuple(time), tuple(thev), tuple(vpcc), tuple(vm),
        tuple(actual), tuple(target), tuple(q), tuple(econv),
    )
