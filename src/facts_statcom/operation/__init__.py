"""STATCOM operating-point and voltage-control teaching models.

The numerical models do not import the schematic drawing engine or plotting
libraries. Matplotlib is loaded only for the separate figure-rendering layer.
"""

from .config import OperationCase
from .control import (
    GridVoltageEvent, VoltageControlConfig, VoltageControlTrace,
    simulate_voltage_control,
)
from .physics import CouplingModel, OperatingPoint

__all__ = [
    "CouplingModel", "GridVoltageEvent", "OperatingPoint", "OperationCase",
    "VoltageControlConfig", "VoltageControlTrace", "simulate_voltage_control",
]
