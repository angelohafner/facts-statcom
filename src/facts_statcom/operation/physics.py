"""Lossless fundamental-frequency STATCOM phasor model.

All values use a consistent three-phase power base, line-to-line voltage base,
and the corresponding phase current/impedance bases. The phasor current is
positive from the converter toward the point of common coupling (PCC).
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass


def _finite_positive(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite positive number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")


def _finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be finite")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


@dataclass(frozen=True)
class OperatingPoint:
    """Steady-state AC-port phasors and three-phase normalized P/Q injections."""

    v_pcc: complex
    e_converter: complex
    i_injected: complex
    p_injected_pu: float
    q_injected_pu: float
    i_capacitive_pu: float
    i_q_dq_pu: float
    current_within_rating: bool
    delta_deg: float

    @property
    def current_magnitude_pu(self) -> float:
        return abs(self.i_injected)

    @property
    def mode(self) -> str:
        if self.q_injected_pu > 1e-9:
            return "capacitive injection"
        if self.q_injected_pu < -1e-9:
            return "inductive absorption"
        return "no reactive exchange"


@dataclass(frozen=True)
class CouplingModel:
    """Ideal VSC fundamental-voltage source behind a pure coupling reactance.

    E is the converter-side fundamental phase RMS voltage phasor; V is the
    PCC phase RMS voltage. The pu values are consistent with a three-phase
    total-power base and the implied phase-voltage/current bases.

    I_inj = (E - V) / (j X), S_inj = V * conj(I_inj).
    Thus Q_inj > 0 means the converter supplies reactive power to the grid.
    A converter with no external DC energy supply cannot sustain arbitrary
    nonzero P_inj; nonzero delta is for a hypothetical instantaneous example.
    """

    v_pcc_pu: float = 1.0
    x_coupling_pu: float = 0.2
    i_limit_pu: float = 1.0
    frequency_hz: float = 60.0

    def __post_init__(self) -> None:
        for name in ("v_pcc_pu", "x_coupling_pu", "i_limit_pu", "frequency_hz"):
            _finite_positive(getattr(self, name), name)

    def operating_point(self, e_pu: float, delta_deg: float = 0.0) -> OperatingPoint:
        """Calculate injection into PCC, without silently clipping currents."""
        _finite_positive(e_pu, "e_pu")
        _finite(delta_deg, "delta_deg")
        voltage = complex(self.v_pcc_pu, 0)
        source = cmath.rect(e_pu, math.radians(delta_deg))
        current = (source - voltage) / (1j * self.x_coupling_pu)
        power = voltage * current.conjugate()
        return OperatingPoint(
            v_pcc=voltage, e_converter=source, i_injected=current,
            p_injected_pu=power.real,
            q_injected_pu=power.imag,
            i_capacitive_pu=-current.imag,
            i_q_dq_pu=current.imag,
            current_within_rating=abs(current) <= self.i_limit_pu + 1e-12,
            delta_deg=float(delta_deg),
        )

    def ideal_e_for_reactive_current(self, i_capacitive_pu: float) -> float:
        """Return E=V+X*Icap for the delta=0 (purely reactive) case."""
        _finite(i_capacitive_pu, "i_capacitive_pu")
        e_pu = self.v_pcc_pu + self.x_coupling_pu * i_capacitive_pu
        if e_pu <= 0:
            raise ValueError("Required E is nonpositive; the simple phasor model is invalid")
        return e_pu

    def instantaneous_fundamentals(
        self, times_s: list[float] | tuple[float, ...], e_pu: float,
        delta_deg: float = 0.0,
    ) -> tuple[list[float], list[float], list[float]]:
        """Return phase-a fundamental RMS-based waveforms (not PWM/EMT signals)."""
        op = self.operating_point(e_pu, delta_deg)
        theta_e = cmath.phase(op.e_converter)
        theta_i = cmath.phase(op.i_injected)
        omega = 2 * math.pi * self.frequency_hz
        scale = math.sqrt(2)
        volt = []
        conv = []
        curr = []
        for time in times_s:
            _finite(time, "time")
            phase = omega * time
            volt.append(scale * self.v_pcc_pu * math.sin(phase))
            conv.append(scale * e_pu * math.sin(phase + theta_e))
            curr.append(scale * op.current_magnitude_pu * math.sin(phase + theta_i))
        return volt, conv, curr
