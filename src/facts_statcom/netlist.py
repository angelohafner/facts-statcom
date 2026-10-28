"""Explicit electrical netlists for detailed educational converter drawings.

Power terminals and transistor gate terminals are distinct.  A symbol, wire or
net label is not used as a substitute for actual electrical connectivity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .model import STATCOMConfig, Topology, CHBConnection


@dataclass(frozen=True)
class Device:
    """A named component and its terminal-to-net associations."""

    name: str
    kind: str
    terminals: Mapping[str, str]


class CircuitGraph:
    """Minimal typed netlist without a simulation-engine dependency."""

    def __init__(self) -> None:
        self.devices: dict[str, Device] = {}

    def add(self, name: str, kind: str, **terminals: str) -> None:
        if not name or name in self.devices:
            raise ValueError(f"Duplicate or empty device: {name}")
        if not terminals or any(not net for net in terminals.values()):
            raise ValueError("Every terminal needs a nonempty net")
        if kind in {"igbt", "diode", "capacitor", "inductor"}:
            power = {k: v for k, v in terminals.items() if k != "G"}
            if len(set(power.values())) != len(power):
                raise ValueError(f"Component {name} shorts its own terminals")
        self.devices[name] = Device(name, kind, dict(terminals))

    def devices_of(self, kind: str) -> list[Device]:
        return [item for item in self.devices.values() if item.kind == kind]

    def nets(self) -> set[str]:
        return {net for device in self.devices.values() for net in device.terminals.values()}

    def add_switch(self, name: str, collector: str, emitter: str) -> None:
        """An IGBT and its separately modelled emitter-to-collector diode."""
        self.add(name, "igbt", C=collector, E=emitter, G=f"GATE_{name}")
        self.add(f"D_{name}", "diode", A=emitter, K=collector)


def _two_level(g: CircuitGraph) -> None:
    for phase in "ABC":
        g.add_switch(f"S{phase}1", "DC+", phase)
        g.add_switch(f"S{phase}2", phase, "DC-")
    g.add("Cdc", "capacitor", P="DC+", N="DC-")


def _npc(g: CircuitGraph) -> None:
    g.add("Cdc1", "capacitor", P="DC+", N="DCM")
    g.add("Cdc2", "capacitor", P="DCM", N="DC-")
    for p in "ABC":
        high, low = f"{p}_upper", f"{p}_lower"
        g.add_switch(f"S{p}1", "DC+", high)
        g.add_switch(f"S{p}2", high, p)
        g.add_switch(f"S{p}3", p, low)
        g.add_switch(f"S{p}4", low, "DC-")
        g.add(f"DCL{p}1", "diode", A="DCM", K=high)
        g.add(f"DCL{p}2", "diode", A=low, K="DCM")


def _bridge(g: CircuitGraph, ident: str, left: str, right: str) -> None:
    """A full bridge with isolated floating DC capacitor and two AC ports."""
    p, n = f"{ident}_P", f"{ident}_N"
    for side, ac in (("L", left), ("R", right)):
        g.add_switch(f"{ident}_{side}1", p, ac)
        g.add_switch(f"{ident}_{side}2", ac, n)
    g.add(f"{ident}_C", "capacitor", P=p, N=n)


def _chb(g: CircuitGraph, conf: STATCOMConfig) -> None:
    pairs = {"A": ("A", "B"), "B": ("B", "C"), "C": ("C", "A")}
    for phase in "ABC":
        start, end = ((phase, "STAR_N") if conf.chb_connection is CHBConnection.STAR
                      else pairs[phase])
        for i in range(1, conf.cells_per_phase + 1):
            left = start if i == 1 else f"{phase}_series_{i-1}"
            right = end if i == conf.cells_per_phase else f"{phase}_series_{i}"
            _bridge(g, f"{phase}_HB{i}", left, right)


def _halfbridge_sm(g: CircuitGraph, ident: str, a: str, b: str) -> None:
    """MMC half bridge: arm port A at switch midpoint; arm port B at C-."""
    cap_plus = f"{ident}_C+"
    g.add_switch(f"{ident}_S1", cap_plus, a)
    g.add_switch(f"{ident}_S2", a, b)
    g.add(f"{ident}_C", "capacitor", P=cap_plus, N=b)


def _mmc(g: CircuitGraph, conf: STATCOMConfig) -> None:
    for phase in "ABC":
        for side in ("U", "L"):
            size = conf.submodules_per_arm
            reactor_node = f"{phase}_{side}_reactor"
            if side == "U":
                first, last = "DC+", reactor_node
                g.add(f"L{phase}_U", "inductor", A=reactor_node, B=phase)
            else:
                first, last = reactor_node, "DC-"
                g.add(f"L{phase}_L", "inductor", A=phase, B=reactor_node)
            for i in range(1, size + 1):
                start = first if i == 1 else f"{phase}_{side}_port_{i-1}"
                end = last if i == size else f"{phase}_{side}_port_{i}"
                _halfbridge_sm(g, f"{phase}_{side}_SM{i}", start, end)


def build_netlist(config: STATCOMConfig) -> CircuitGraph:
    """Create power topology for schematics with internal switch detail.

    BASIC, COMPLETE and CONTROL are intentionally functional diagrams and do
    not promise detailed transistor-level connectivity.
    """
    g = CircuitGraph()
    if config.topology in (Topology.TWO_LEVEL, Topology.COMPLETE):
        _two_level(g)
    elif config.topology is Topology.NPC:
        _npc(g)
    elif config.topology is Topology.CHB:
        _chb(g, config)
    elif config.topology is Topology.MMC:
        _mmc(g, config)
    return g
