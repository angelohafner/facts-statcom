"""Reusable electrical SVG symbols and composable semiconductor cells.

The canvas and typography API follow facts-svc. Device symbols expose stable
terminal coordinates and an explicit orientation; switch body and antiparallel
diodes remain independent, identifiable SVG groups.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET

from .svg import SVGCanvas, node


@dataclass(frozen=True)
class Port:
    x: float
    y: float


@dataclass(frozen=True)
class PhysicalComponent:
    """Minimal reusable component protocol for future shared FACTS graphics."""
    name: str

    def draw(self, symbols: ElectricalSymbols, parent: ET.Element, x: float,
             y: float) -> object:
        raise NotImplementedError


@dataclass(frozen=True)
class SemiconductorDevice(PhysicalComponent):
    """A controllable device drawn with specified vertical power terminals."""
    height: float = 76

    def draw(self, symbols: ElectricalSymbols, parent: ET.Element, x: float,
             y: float) -> tuple[Port, Port]:
        return symbols.igbt(parent, x, y, y + self.height, self.name)


@dataclass(frozen=True)
class SwitchingCell(PhysicalComponent):
    """Reusable full H-bridge cell with one electrically floating DC capacitor."""
    width: float = 390
    height: float = 232

    def draw(self, symbols: ElectricalSymbols, parent: ET.Element, x: float,
             y: float) -> tuple[Port, Port]:
        return symbols.h_bridge(parent, x, y, self.name)


@dataclass(frozen=True)
class MMCSubmodule(PhysicalComponent):
    """Two-switch half-bridge submodule; upper arm port is switch midpoint."""

    def draw(self, symbols: ElectricalSymbols, parent: ET.Element, x: float,
             y: float) -> tuple[Port, Port]:
        return symbols.half_bridge_submodule(parent, x, y, self.name)


class ElectricalSymbols:
    """Coordinate-exact symbols with visually separate electrical junctions."""

    def __init__(self, canvas: SVGCanvas):
        self.c = canvas

    def terminal(self, parent: ET.Element, x: float, y: float,
                 name: str = "") -> None:
        c = self.c
        c.circle(parent, x, y, 5, fill=c.theme.ink, stroke=c.theme.ink,
                 stroke_width=1)
        if name:
            node(parent, "title").text = name

    def inductor(self, parent: ET.Element, x: float, top: float, bottom: float,
                 name: str, *, label: bool = True) -> tuple[Port, Port]:
        if bottom - top < 75:
            raise ValueError("Inductor vertical span must be at least 75")
        c = self.c
        g = c.group(parent, f"inductor-{name}", data_device="inductor",
                    data_name=name)
        start = (top + bottom) / 2 - 34
        c.line(g, x, top, x, start, color=c.theme.reactor)
        d = f"M {x},{start}"
        for i in range(4):
            y = start + 17 * i
            d += f" C {x-15},{y+3} {x-15},{y+14} {x},{y+17}"
        c.path(g, d, color=c.theme.reactor)
        c.line(g, x, start + 68, x, bottom, color=c.theme.reactor)
        if label:
            c.math(g, x+25, (top+bottom)/2+5,
                   [("L", "variable"), (name, "subscript-roman")],
                   size=17, color=c.theme.reactor)
        return Port(x, top), Port(x, bottom)

    def horizontal_inductor(self, parent: ET.Element, x1: float, x2: float,
                            y: float, name: str, *, label: bool = True) -> None:
        """Draw a coil across a horizontal conductor with intact endpoints."""
        if x2-x1 < 80:
            raise ValueError("Horizontal inductor span must be >= 80")
        c = self.c
        g = c.group(parent, f"inductor-{name}", data_device="inductor",
                    data_name=name)
        start = (x1+x2)/2-34
        c.line(g, x1, y, start, y, color=c.theme.reactor)
        d = f"M {start},{y}"
        for i in range(4):
            xx = start+17*i
            d += f" C {xx+3},{y-15} {xx+14},{y-15} {xx+17},{y}"
        c.path(g, d, color=c.theme.reactor)
        c.line(g, start+68, y, x2, y, color=c.theme.reactor)
        if label:
            c.math(g, (x1+x2)/2, y-24, [("L", "variable"),
                    (name, "subscript-roman")], anchor="middle", size=16,
                    color=c.theme.reactor)

    def capacitor(self, parent: ET.Element, x: float, top: float, bottom: float,
                  name: str, *, label: bool = True) -> tuple[Port, Port]:
        if bottom - top < 31:
            raise ValueError("Capacitor vertical span must be at least 31")
        c = self.c
        g = c.group(parent, f"capacitor-{name}", data_device="capacitor",
                    data_name=name)
        cy = (top+bottom)/2
        c.line(g, x, top, x, cy-9, color=c.theme.capacitor)
        c.line(g, x-20, cy-9, x+20, cy-9, color=c.theme.capacitor)
        c.line(g, x-20, cy+9, x+20, cy+9, color=c.theme.capacitor)
        c.line(g, x, cy+9, x, bottom, color=c.theme.capacitor)
        if label:
            c.math(g, x+26, cy+4,
                   [("C", "variable"), (name, "subscript-roman")],
                   size=15, color=c.theme.capacitor)
        return Port(x, top), Port(x, bottom)

    def diode(self, parent: ET.Element, x: float, top: float, bottom: float,
              name: str, *, direction: str = "up", label: bool = False) -> None:
        """The triangle points from anode to cathode; the line is cathode."""
        if bottom - top < 26 or direction not in {"up", "down"}:
            raise ValueError("Invalid diode geometry or orientation")
        c = self.c
        g = c.group(parent, f"diode-{name}", data_device="diode",
                    data_direction=direction, data_name=name)
        cy = (top+bottom)/2
        c.line(g, x, top, x, cy-12, width=2.5)
        c.line(g, x, cy+12, x, bottom, width=2.5)
        if direction == "up":
            pts = [(x-9, cy+10), (x+9, cy+10), (x, cy-10)]
            bar = cy-11
        else:
            pts = [(x-9, cy-10), (x+9, cy-10), (x, cy+10)]
            bar = cy+11
        node(g, "polygon", points=" ".join(f"{a},{b}" for a,b in pts),
             fill=c.theme.paper, stroke=c.theme.ink, stroke_width=2)
        c.line(g, x-11, bar, x+11, bar, width=2.5)
        if label:
            c.text(g, x+18, cy-9, name, size=13, color=c.theme.muted)

    def igbt(self, parent: ET.Element, x: float, top: float, bottom: float,
             name: str, *, diode: bool = True, label: bool = False,
             compact: bool = False) -> tuple[Port, Port]:
        """Vertical N-channel IGBT: C at top, E at bottom, G insulated left.

        The antiparallel diode has anode at E and cathode at C.  A switching
        state is *not* inferred from the decorative arrow in the symbol.
        """
        if bottom - top < 33:
            raise ValueError("IGBT vertical span must be >= 33")
        c = self.c
        g = c.group(parent, f"igbt-{name}", data_device="IGBT",
                    data_name=name, data_collector="top", data_emitter="bottom")
        h = bottom-top
        cy = (top+bottom)/2
        gap = max(7, min(13, h*0.21))
        body_top, body_bottom = cy-gap, cy+gap
        c.line(g, x, top, x, body_top-8, width=2.8)
        c.line(g, x, body_top-8, x+7, body_top, width=2.8)
        c.line(g, x+7, body_top, x+7, body_bottom, width=3.4)
        c.line(g, x+7, body_bottom, x, body_bottom+8, width=2.8)
        c.line(g, x, body_bottom+8, x, bottom, width=2.8)
        # Parallel insulated gate plate is intentionally separated from channel.
        gate_x = x-7
        c.line(g, gate_x, body_top-4, gate_x, body_bottom+4, width=2.8)
        c.line(g, x-(22 if compact else 34), cy, gate_x, cy, width=2.5)
        # IGBT emitter current arrow at the collector/emitter channel edge.
        c.polyline(g, [(x+4, body_bottom-4), (x+12, body_bottom+5),
                       (x+12, body_bottom)], width=1.8)
        if diode:
            dx = x+(32 if compact else 49)
            c.line(g, x, top, dx, top, width=2.5)
            c.line(g, dx, bottom, x, bottom, width=2.5)
            self.diode(g, dx, top, bottom, f"D_{name}", direction="up")
        if label:
            c.text(g, x-(42 if compact else 53), top-8,
                   name, size=14, color=c.theme.muted)
        return Port(x, top), Port(x, bottom)

    def three_phase_transformer(self, parent: ET.Element, x: float, y: float,
                                *, width: float = 225, height: float = 245,
                                phase_pitch: float = 58,
                                port_offset: float = 65) -> None:
        """Symbolic three-phase multiport transformer, without winding claims."""
        c = self.c
        g = c.group(parent, "three-phase-transformer", data_device="transformer")
        c.rect(g, x, y, width, height, fill=c.theme.paper,
               radius=14, stroke=c.theme.border)
        for k, phase in enumerate("ABC"):
            py = y+port_offset+k*phase_pitch
            c.line(g, x-25, py, x+43, py, width=3)
            c.circle(g, x+65, py, 23, stroke=c.theme.reactor, stroke_width=2.7)
            c.circle(g, x+100, py, 23, stroke=c.theme.capacitor, stroke_width=2.7)
            c.line(g, x+123, py, x+width+25, py, width=3)
        c.text(g, x+width/2, y+32, "3-phase transformer", anchor="middle",
               size=17, bold=True)
        c.text(g, x+width/2, y+height-20, "winding groups unspecified",
               anchor="middle", size=12, color=c.theme.muted)

    def h_bridge(self, parent: ET.Element, x: float, y: float,
                 name: str) -> tuple[Port, Port]:
        """Full bridge: two switch legs, one floating DC capacitor, two AC ports."""
        c = self.c
        g = c.group(parent, f"hbridge-{name}", data_device="H-bridge",
                    data_name=name)
        c.rect(g, x, y, 390, 232, fill=c.theme.paper,
               radius=10, stroke=c.theme.border)
        c.text(g, x+18, y+24, name, size=15, bold=True)
        plus, minus, ac = y+39, y+192, y+116
        xl, xr, xc = x+125, x+268, x+203
        c.line(g, xl, plus, xr, plus, width=3)
        c.line(g, xl, minus, xr, minus, width=3)
        for suffix, xx in (("L", xl), ("R", xr)):
            self.igbt(g, xx, plus+8, ac-13, f"{name}_{suffix}1", compact=True)
            self.igbt(g, xx, ac+13, minus-8, f"{name}_{suffix}2", compact=True)
            c.line(g, xx, plus, xx, plus+8)
            c.line(g, xx, ac-13, xx, ac+13)
            c.line(g, xx, minus-8, xx, minus)
            self.terminal(g, xx, ac)
        c.line(g, xl, ac, x+9, ac, width=3.2)
        c.line(g, xr, ac, x+381, ac, width=3.2)
        c.line(g, xc, plus, xc, plus+9)
        self.capacitor(g, xc, plus+9, minus-9, name, label=False)
        c.line(g, xc, minus-9, xc, minus)
        # Explicit DC capacitor label, placed in the space between switch legs.
        c.math(g, xc+13, y+130, [("C", "variable")],
               size=14, color=c.theme.capacitor)
        return Port(x+9, ac), Port(x+381, ac)

    def half_bridge_submodule(self, parent: ET.Element, x: float, y: float,
                              name: str) -> tuple[Port, Port]:
        """An MMC half-bridge module; A is switch midpoint and B is C-."""
        c = self.c
        g = c.group(parent, f"sm-{name}", data_device="MMC-submodule",
                    data_name=name, data_top_port="A", data_bottom_port="B")
        c.rect(g, x, y, 230, 182, fill=c.theme.paper,
               radius=9, stroke=c.theme.border)
        c.text(g, x+115, y+18, name, size=13, bold=True, anchor="middle")
        xa, xs, xc = x+22, x+95, x+176
        yt, ym, yb = y+32, y+92, y+151
        c.line(g, xs, yt, xc, yt)
        c.line(g, xs, yb, xc, yb)
        self.igbt(g, xs, yt+7, ym-10, f"{name}_S1", compact=True)
        self.igbt(g, xs, ym+10, yb-7, f"{name}_S2", compact=True)
        c.line(g, xs, yt, xs, yt+7)
        c.line(g, xs, ym-10, xs, ym+10)
        c.line(g, xs, yb-7, xs, yb)
        self.capacitor(g, xc, yt+9, yb-9, name, label=False)
        c.line(g, xc, yt, xc, yt+9)
        c.line(g, xc, yb-9, xc, yb)
        # A (top external port) reaches the midpoint without touching C+.
        c.polyline(g, [(xa, y), (xa, ym), (xs, ym)], width=2.7)
        # B (bottom external port) reaches C- without touching midpoint A.
        c.polyline(g, [(xa, y+182), (xa, yb), (xs, yb)], width=2.7)
        c.math(g, x+195, y+105, [("C", "variable")],
               size=13, color=c.theme.capacitor)
        return Port(xa, y), Port(xa, y+182)
