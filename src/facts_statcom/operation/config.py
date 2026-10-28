"""Immutable JSON configuration for decoupled STATCOM operating-point figures."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .control import GridVoltageEvent, VoltageControlConfig
from .physics import CouplingModel, _finite_positive


@dataclass(frozen=True)
class OperationCase:
    """Validated inputs shared by pure numerical models and figure renderers."""

    coupling: CouplingModel = CouplingModel()
    control: VoltageControlConfig = VoltageControlConfig()
    converter_voltage_low_pu: float = 0.75
    converter_voltage_high_pu: float = 1.25
    nominal_e_pu: float = 1.06
    nominal_angle_deg: float = 0.0
    voltage_events: tuple[GridVoltageEvent, ...] = (
        GridVoltageEvent(0.0, 1.0),
        GridVoltageEvent(0.15, 0.88),
        GridVoltageEvent(0.42, 1.045),
    )
    end_time_s: float = 0.75
    time_step_s: float = 0.0005

    def __post_init__(self) -> None:
        if not isinstance(self.coupling, CouplingModel):
            raise TypeError("coupling must be a CouplingModel")
        if not isinstance(self.control, VoltageControlConfig):
            raise TypeError("control must be a VoltageControlConfig")
        for name in ("converter_voltage_low_pu", "converter_voltage_high_pu",
                     "nominal_e_pu", "end_time_s", "time_step_s"):
            _finite_positive(getattr(self, name), name)
        if self.converter_voltage_high_pu <= self.converter_voltage_low_pu:
            raise ValueError("converter voltage maximum must exceed minimum")
        if not math.isfinite(self.nominal_angle_deg):
            raise ValueError("nominal_angle_deg must be finite")
        if not isinstance(self.voltage_events, tuple) or not self.voltage_events:
            raise ValueError("voltage_events must be a nonempty tuple")
        if self.voltage_events[0].time_s != 0.0:
            raise ValueError("voltage_events must begin at t=0")
        if any(b.time_s <= a.time_s for a, b in
               zip(self.voltage_events, self.voltage_events[1:])):
            raise ValueError("voltage_events must be in increasing order")
        if self.voltage_events[-1].time_s >= self.end_time_s:
            raise ValueError("The last voltage event must precede end_time_s")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> OperationCase:
        if not isinstance(payload, Mapping):
            raise ValueError("Operation configuration must be a JSON object")
        extra = set(payload).difference(cls.__dataclass_fields__)
        if extra:
            raise ValueError(f"Unexpected fields: {sorted(extra)}")
        options = dict(payload)
        if "coupling" in options:
            options["coupling"] = CouplingModel(**options["coupling"])
        if "control" in options:
            options["control"] = VoltageControlConfig(**options["control"])
        if "voltage_events" in options:
            options["voltage_events"] = tuple(
                GridVoltageEvent(**entry) for entry in options["voltage_events"]
            )
        return cls(**options)

    @classmethod
    def from_json(cls, path: str | Path) -> OperationCase:
        with Path(path).open(encoding="utf-8") as stream:
            return cls.from_dict(json.load(stream))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
