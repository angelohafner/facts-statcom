"""Vector schematics for STATCOM VSCs, NPC, CHB, MMC and dq control.

All figures are conceptual, not simulation results. Detailed converters use
explicit device/terminal conventions matching the independent circuit netlist.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from .model import STATCOMConfig, Topology, CHBConnection
from .svg import SVGCanvas, node
from .symbols import ElectricalSymbols, SwitchingCell, MMCSubmodule


class STATCOMRenderer:
    """Dispatch each validated topology to an independent SVG composition."""

    def __init__(self, config: STATCOMConfig):
        self.config = config
        self.c: SVGCanvas | None = None
        self.s: ElectricalSymbols | None = None

    def _start(self, width: int, height: int, subtitle: str, footnote: str) -> ET.Element:
        c = SVGCanvas(width, height)
        self.c = c
        self.s = ElectricalSymbols(c)
        c.metadata(self.config.title, subtitle + ". " + footnote)
        bg = c.layer("Background", "background")
        c.rect(bg, 0, 0, width, height, fill=c.theme.canvas)
        c.rect(bg, 26, 24, width-52, height-48, fill=c.theme.paper,
               stroke=c.theme.border, radius=18)
        t = c.layer("Titles and descriptions", "titles")
        c.text(t, 68, 78, self.config.title, size=32, bold=True)
        c.text(t, 68, 113, subtitle, size=17, color=c.theme.muted)
        c.line(t, 66, 135, width-66, 135, color=c.theme.border, width=2)
        c.line(t, 66, height-111, width-66, height-111,
               color=c.theme.border, width=2)
        c.text(t, 75, height-79, footnote, size=15, color=c.theme.muted)
        c.text(t, 75, height-51,
               "Editable SVG | vector symbols | conceptual illustration, not a switching or EMT simulation",
               size=14, color=c.theme.muted)
        return c.layer("Circuit and devices", "circuit")

    def _label(self, parent: ET.Element, x: float, y: float,
               name: str, *, anchor: str = "start", size: int = 18) -> None:
        assert self.c
        self.c.text(parent, x, y, name, size=size,
                    color=self.c.theme.muted, anchor=anchor)

    def _bus(self, parent: ET.Element, x1: float, x2: float, y: float,
             name: str) -> None:
        assert self.c
        c = self.c
        c.line(parent, x1, y, x2, y, width=5.1)
        c.circle(parent, x1, y, 5.5, fill=c.theme.ink)
        c.circle(parent, x2, y, 5.5, fill=c.theme.ink)
        c.text(parent, x1+8, y-19, name, bold=True, size=17)

    def _vsc_legs(self, parent: ET.Element, xs: tuple[int, int, int],
                  top: int, mid: int, bot: int, *, label: bool = True) -> None:
        assert self.c and self.s
        c, s = self.c, self.s
        self._bus(parent, xs[0]-100, xs[-1]+100, top, "DC+")
        self._bus(parent, xs[0]-100, xs[-1]+100, bot, "DC-")
        upper, lower = (top+105, mid-130), (mid+130, bot-105)
        for phase, x in zip("ABC", xs):
            c.line(parent, x, top, x, upper[0], width=3.2)
            s.igbt(parent, x, upper[0], upper[1], f"S{phase}1", label=label)
            c.line(parent, x, upper[1], x, mid, width=3.2)
            c.line(parent, x, mid, x, lower[0], width=3.2)
            s.igbt(parent, x, lower[0], lower[1], f"S{phase}2", label=label)
            c.line(parent, x, lower[1], x, bot, width=3.2)
            c.line(parent, x-115, mid, x, mid, width=3.2)
            s.terminal(parent, x, mid)
            self._label(parent, x-129, mid-15, f"Phase {phase}",
                        anchor="start", size=16)
            self._label(parent, x+55, mid+29, f"{phase} output", size=14)

    def _dc_cap(self, parent: ET.Element, x: float, top: float,
                bot: float, name: str = "dc") -> None:
        assert self.c and self.s
        c, s = self.c, self.s
        # The capacitor connects only the two actual DC rails.
        c.line(parent, x, top, x, top+90)
        s.capacitor(parent, x, top+90, bot-90, name)
        c.line(parent, x, bot-90, x, bot)
        s.terminal(parent, x, top)
        s.terminal(parent, x, bot)

    def _two_level(self, *, complete: bool = False) -> None:
        assert self.c is None
        if complete:
            width, height = 2300, 1230
            title = "Complete grid interface | six IGBTs and antiparallel diodes"
            note = "Labeled A/B/C terminals denote the same nodes in both panels; transformer winding connections are unspecified."
        else:
            width, height = 2060, 1180
            title = "Three converter legs, two IGBTs per leg, isolated gate drives and one common DC-link capacitor"
            note = "IGBT collector at top, emitter at bottom; each diode conducts from emitter to collector."
        g = self._start(width, height, title, note)
        assert self.c and self.s
        c, s = self.c, self.s
        if complete:
            # Physically connected grid-side lines end at explicit net labels.
            left = c.group(g, "grid-interface", data_device="grid-interface")
            c.rect(left, 90, 265, 850, 670, fill=c.theme.canvas,
                   radius=16, stroke=c.theme.border)
            c.text(left, 125, 316, "GRID AND COUPLING", size=23, bold=True)
            c.text(left, 129, 345, "Functional three-phase transformer + series reactors",
                   size=15, color=c.theme.muted)
            for k, p in enumerate("ABC"):
                y = 475+k*122
                c.line(left, 126, y, 245, y)
                c.circle(left, 126, y, 5, fill=c.theme.ink)
                c.text(left, 128, y-19, f"Grid {p}", size=15)
            if self.config.transformer:
                s.three_phase_transformer(left, 270, 385, width=230, height=425,
                                          phase_pitch=122, port_offset=90)
            else:
                # Bypass explicitly short links for the no-transformer option.
                for k in range(3):
                    y = 475+k*122
                    c.line(left, 250, y, 525, y)
                c.text(left, 290, 425, "Transformer omitted", size=15)
            for k, p in enumerate("ABC"):
                y = 475+k*122
                if self.config.transformer:
                    c.line(left, 525, y, 600, y)
                else:
                    c.line(left, 525, y, 600, y)
                s.horizontal_inductor(left, 600, 740, y, p)
                c.line(left, 740, y, 855, y)
                s.terminal(left, 855, y)
                c.text(left, 867, y+7, p, size=21, bold=True)
            c.text(left, 136, 861,
                   "Equal phase labels identify the same electrical net across panels.",
                   size=15, color=c.theme.muted)
            xs = (1160, 1560, 1960)
            top, mid, bot = 245, 637, 1050
        else:
            xs = (405, 855, 1305)
            top, mid, bot = 242, 607, 970
        self._vsc_legs(g, xs, top, mid, bot)
        cap_x = (2230 if complete else 1810)
        # DC capacitor is connected to the same + and - nets by explicit branches.
        c.line(g, xs[-1]+100, top, cap_x, top, width=3.4)
        c.line(g, xs[-1]+100, bot, cap_x, bot, width=3.4)
        self._dc_cap(g, cap_x, top, bot)
        c.text(g, cap_x-100, (top+bot)/2+5, "DC LINK", size=15,
               bold=True, color=c.theme.muted)

    def _basic(self) -> None:
        width, height = 1670, 950
        note = "Converter is a functional block; the DC capacitor is not a source of sustained active power."
        g = self._start(width, height,
                        "Grid | optional three-phase transformer | coupling reactors | VSC | DC-link capacitor",
                        note)
        assert self.c and self.s
        c, s = self.c, self.s
        if self.config.transformer:
            s.three_phase_transformer(g, 330, 294, width=235, height=290,
                                      phase_pitch=60, port_offset=71)
        for i, p in enumerate("ABC"):
            y = 365+i*60
            c.line(g, 150, y, 305, y)
            c.text(g, 135, y-12, p, size=17, bold=True)
            if self.config.transformer:
                c.line(g, 590, y, 685, y)
            else:
                c.line(g, 300, y, 685, y)
            s.horizontal_inductor(g, 685, 795, y, p)
            c.line(g, 795, y, 1040, y)
        if not self.config.transformer:
            c.text(g, 340, 314, "Direct connection (no transformer)", size=16)
        vsc = c.group(g, "vsc", data_device="VSC")
        c.rect(vsc, 1040, 290, 250, 310, fill=c.theme.canvas,
               radius=18, stroke=c.theme.reactor)
        c.text(vsc, 1165, 409, "VSC", size=35, bold=True, anchor="middle")
        c.text(vsc, 1165, 443, "self-commutated", size=15, anchor="middle")
        c.text(vsc, 1165, 470, "three-phase bridge", size=15, anchor="middle")
        c.line(g, 1290, 350, 1475, 350, width=3)
        c.line(g, 1290, 544, 1475, 544, width=3)
        c.text(g, 1308, 336, "+", size=22, bold=True)
        c.text(g, 1308, 566, "−", size=22, bold=True)
        s.capacitor(g, 1475, 350, 544, "dc")
        c.text(g, 1465, 625, "DC energy storage", anchor="middle", size=16)
        c.text(g, 149, 690, "PCC / AC grid", size=18, bold=True)
        c.text(g, 730, 588, "Coupling inductances", size=16, color=c.theme.muted)

    def _npc(self) -> None:
        width, height = 2260, 1700
        note = "NPC clamping: upper diode M→upper internal node; lower diode lower internal node→M."
        g = self._start(width, height,
                        "Per leg: 4 series IGBTs + 4 antiparallel diodes + 2 clamping diodes",
                        note)
        assert self.c and self.s
        c, s = self.c, self.s
        xs = (320, 820, 1320)
        top, mid, bot, middle = 278, 841, 1480, 770
        self._bus(g, xs[0]-95, 1970, top, "DC+")
        self._bus(g, xs[0]-95, 1970, bot, "DC-")
        for p, x in zip("ABC", xs):
            # Series order: DC+ -> S1 -> XU -> S2 -> AC -> S3 -> XL -> S4 -> DC-.
            spans = ((368, 460), (651, 743), (960, 1052), (1250, 1342))
            for i, (upper, lower) in enumerate(spans, start=1):
                s.igbt(g, x, upper, lower, f"S{p}{i}", label=True)
            c.line(g, x, top, x, spans[0][0])
            for i in range(3):
                c.line(g, x, spans[i][1], x, spans[i+1][0])
            c.line(g, x, spans[-1][1], x, bot)
            upper_node, lower_node = 555, 1155
            self._label(g, x-92, mid-20, p, size=21)
            c.line(g, x-103, mid, x, mid)
            s.terminal(g, x, mid)
            # Separate local M (DC midpoint) terminal. It is the same net as
            # the labeled midpoint of the split capacitor, not phase output.
            ua, la = x+143, x+245
            c.polyline(g, [(x, upper_node), (ua, upper_node), (ua, 603)])
            s.diode(g, ua, 603, 697, f"DCL{p}1", direction="up")
            c.line(g, ua, 697, ua, middle-3)
            c.polyline(g, [(la, middle-3), (la, 957)])
            s.diode(g, la, 957, 1045, f"DCL{p}2", direction="up")
            c.polyline(g, [(la, 1045), (la, lower_node), (x, lower_node)])
            c.line(g, ua, middle-3, la+46, middle-3)
            s.terminal(g, ua, middle-3)
            s.terminal(g, la, middle-3)
            self._label(g, la+50, middle+4, "M", size=21)
            s.terminal(g, x, upper_node)
            s.terminal(g, x, lower_node)
        xcap = 1970
        c.line(g, xcap, top, xcap, 493)
        s.capacitor(g, xcap, 493, 593, "dc1")
        c.line(g, xcap, 593, xcap, middle)
        c.line(g, xcap, middle, xcap, 1120)
        s.capacitor(g, xcap, 1120, 1220, "dc2")
        c.line(g, xcap, 1220, xcap, bot)
        s.terminal(g, xcap, middle)
        self._label(g, xcap+26, middle+6, "M (DC midpoint)", size=17)
        c.text(g, 1510, 1533, "M terminals on all legs share the split DC-link midpoint.",
               size=16, color=c.theme.muted)

    def _chb(self) -> None:
        assert self.s is None
        n = self.config.cells_per_phase
        width = max(1710, 360+n*480+260)
        height = 1290
        kind = self.config.chb_connection
        note = ("STAR: each phase arm ends on a common floating N node; DC capacitors are isolated per H-bridge."
                if kind is CHBConnection.STAR else
                "DELTA: branches A–B, B–C and C–A; matching terminal letters denote the same AC nodes.")
        g = self._start(width, height,
                        f"{n} full H-bridge cells per phase arm | 4 IGBTs and 4 antiparallel diodes per cell",
                        note)
        assert self.c and self.s
        c, s = self.c, self.s
        start_x, step, y0 = 247, 480, 257
        neutral_x = start_x+(n-1)*step+500
        joins = {"A": ("A", "B"), "B": ("B", "C"), "C": ("C", "A")}
        ys = []
        for k, phase in enumerate("ABC"):
            y = y0+k*324
            yp = y+116
            ys.append(yp)
            left_letter, right_letter = ((phase, "N") if kind is CHBConnection.STAR
                                         else joins[phase])
            c.line(g, 131, yp, start_x+9, yp, width=3.3)
            s.terminal(g, 131, yp)
            c.text(g, 113, yp-16, left_letter, size=23, bold=True)
            c.text(g, 94, yp+29, f"Arm {phase}", size=15, color=c.theme.muted)
            for index in range(n):
                xx = start_x+step*index
                left, right = SwitchingCell(f"{phase}_HB{index+1}").draw(s, g, xx, y)
                if index > 0:
                    previous_right = start_x+step*(index-1)+381
                    c.line(g, previous_right, yp, left.x, yp, width=3.2)
            final = start_x+step*(n-1)+381
            c.line(g, final, yp, neutral_x, yp, width=3.2)
            s.terminal(g, neutral_x, yp)
            if kind is CHBConnection.DELTA:
                c.text(g, neutral_x+21, yp+7, right_letter, size=23,
                       bold=True)
        if kind is CHBConnection.STAR:
            c.line(g, neutral_x, ys[0], neutral_x, ys[-1], width=4.0)
            for yy in ys:
                s.terminal(g, neutral_x, yy)
            c.text(g, neutral_x+24, ys[1]+8, "N", size=24, bold=True)

    def _mmc(self) -> None:
        n = self.config.submodules_per_arm
        stride, cellh = 247, 182
        top_bus, top_cell = 255, 291
        end_upper = top_cell+(n-1)*stride+cellh
        upper_L = (end_upper+60, end_upper+150)
        ac_y = upper_L[1]+65
        lower_L = (ac_y+58, ac_y+148)
        lower_cell = lower_L[1]+61
        end_lower = lower_cell+(n-1)*stride+cellh
        bot_bus = end_lower+68
        height = int(bot_bus+212)
        width = 2050
        note = "Floating DC rails, half-bridge SM capacitors and arm reactors; no external DC source is implied."
        g = self._start(width, height,
                        f"Double-star arrangement | {n} explicit half-bridge submodules per arm | 6 arms",
                        note)
        assert self.c and self.s
        c, s = self.c, self.s
        xs = (350, 905, 1460)
        self._bus(g, xs[0]-94, xs[-1]+94, top_bus, "P (floating)")
        self._bus(g, xs[0]-94, xs[-1]+94, bot_bus, "N (floating)")
        for phase, x in zip("ABC", xs):
            c.line(g, x, top_bus, x, top_cell)
            for i in range(n):
                y = top_cell+i*stride
                MMCSubmodule(f"{phase}_U_SM{i+1}").draw(s, g, x-22, y)
                if i > 0:
                    c.line(g, x, y-stride+cellh, x, y)
            c.line(g, x, end_upper, x, upper_L[0])
            s.inductor(g, x, *upper_L, f"{phase}U", label=False)
            c.line(g, x, upper_L[1], x, ac_y)
            c.line(g, x, ac_y, x, lower_L[0])
            s.terminal(g, x, ac_y)
            c.line(g, x-143, ac_y, x, ac_y, width=3.5)
            self._label(g, x-161, ac_y-15, f"Phase {phase}", size=17)
            s.inductor(g, x, *lower_L, f"{phase}L", label=False)
            c.line(g, x, lower_L[1], x, lower_cell)
            for i in range(n):
                y = lower_cell+i*stride
                MMCSubmodule(f"{phase}_L_SM{i+1}").draw(s, g, x-22, y)
                if i > 0:
                    c.line(g, x, y-stride+cellh, x, y)
            c.line(g, x, end_lower, x, bot_bus)
            self._label(g, x+29, (upper_L[0]+upper_L[1])/2+5, "L upper", size=14)
            self._label(g, x+29, (lower_L[0]+lower_L[1])/2+5, "L lower", size=14)
        c.text(g, 270, bot_bus+45,
               "SM arm-port A = switch midpoint; SM arm-port B = capacitor negative."
               " Each submodule stores its own energy.", size=17)

    def _control(self) -> None:
        width, height = 1980, 1160
        note = "PLL aligns d-axis with PCC voltage; i_d controls DC energy, i_q controls AC voltage/Q (sign convention dependent)."
        g = self._start(width, height,
                        "Illustrative cascaded dq control: voltage/reactive, DC energy and current regulation",
                        note)
        assert self.c
        c = self.c
        defs = node(c.root, "defs")
        marker = node(defs, "marker", id="arrow", viewBox="0 0 10 10",
                      refX=9, refY=5, markerWidth=7, markerHeight=7,
                      orient="auto-start-reverse")
        node(marker, "path", d="M 0,0 L 10,5 L 0,10 z", fill=c.theme.ink)
        def box(x: int, y: int, w: int, h: int, top: str, bottom: str = "") -> None:
            group = c.group(g, f"block-{top.lower().replace(' ', '-').replace('/', '-')}")
            c.rect(group, x, y, w, h, fill=c.theme.canvas,
                   radius=12, stroke=c.theme.border)
            c.text(group, x+w/2, y+h/2-(11 if bottom else -5),
                   top, anchor="middle", size=18, bold=True)
            if bottom:
                c.text(group, x+w/2, y+h/2+18, bottom, anchor="middle",
                       size=14, color=c.theme.muted)
        def wire(points: list[tuple[int,int]], label: str = "") -> None:
            p = c.polyline(g, points, width=2.6)
            p.set("marker-end", "url(#arrow)")
            if label:
                x, y = points[0]
                c.text(g, x+7, y-10, label, size=15, color=c.theme.muted)
        # Sensors feed PLL and synchronous reference frame measurements.
        box(75, 210, 240, 83, "PCC sensors", "vabc, iabc")
        box(420, 195, 225, 92, "PLL", "angle θ")
        box(420, 395, 225, 92, "abc → dq", "id, iq")
        wire([(315,249),(420,249)], "vabc")
        wire([(315,260),(355,260),(355,440),(420,440)])
        wire([(535,287),(535,355),(540,395)], "θ")
        box(80, 660, 235, 95, "DC-link sensors", "Vdc measured")
        box(415, 635, 240, 130, "DC-link PI", "i*d reference")
        box(415, 860, 240, 130, "PCC voltage / Q PI", "i*q reference")
        box(75, 880, 250, 91, "Setpoint", "V*pcc or Q*")
        wire([(315,710),(415,710)], "Vdc")
        wire([(325,920),(415,920)])
        # Matching signal names keep the feedback route unambiguous without
        # crossing the independent DC voltage sensor line.
        c.text(g, 327, 267, "Vpcc → voltage controller", size=13,
               color=c.theme.muted)
        wire([(340,835),(415,835),(415,860)], "Vpcc")
        box(875, 440, 272, 140, "dq current control", "PI + decoupling / limits")
        wire([(645,440),(875,480)], "id, iq")
        wire([(655,699),(780,699),(780,518),(875,518)], "i*d")
        wire([(655,924),(820,924),(820,554),(875,554)], "i*q")
        box(1300, 420, 236, 137, "dq → abc", "voltage references")
        wire([(1147,510),(1300,510)], "v*d, v*q")
        wire([(645,243),(1210,243),(1210,451),(1300,451)], "θ")
        box(1620, 425, 225, 111, "PWM / gate drive", "switch commands")
        wire([(1536,493),(1620,493)])
        box(1620, 730, 230, 115, "Three-phase VSC", "IGBT converter")
        wire([(1730,536),(1730,730)], "gating")
        # Feedback is routed along the outer margin, not through PLL blocks.
        wire([(1850,795),(1910,795),(1910,995),(55,995),(55,250),(75,250)],
             "PCC feedback")
        c.text(g, 80, 1037,
               "The drawing shows functional signal paths, not a tuned or validated controller."
               " Control polarity depends on dq sign conventions.",
               size=16, color=c.theme.muted)

    def render(self) -> SVGCanvas:
        if self.c is not None:
            raise RuntimeError("Create a new STATCOMRenderer for every rendering")
        dispatch = {
            Topology.BASIC: self._basic,
            Topology.TWO_LEVEL: self._two_level,
            Topology.NPC: self._npc,
            Topology.CHB: self._chb,
            Topology.MMC: self._mmc,
            Topology.COMPLETE: lambda: self._two_level(complete=True),
            Topology.CONTROL: self._control,
        }
        dispatch[self.config.topology]()
        assert self.c is not None
        return self.c

    def save(self, path: str | Path) -> Path:
        return self.render().save(path)


def render_svg(config: STATCOMConfig, path: str | Path) -> Path:
    return STATCOMRenderer(config).save(path)
