"""Reusable, dependency-free SVG drawing primitives compatible with facts-svc.

Compatibility contract: Theme, SVGCanvas, node and scientific typography are
kept aligned with facts_svc.svg for future extraction to a shared package.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
ET.register_namespace("", SVG_NS)
ET.register_namespace("inkscape", INK_NS)


@dataclass(frozen=True)
class Theme:
    ink: str = "#24364A"
    muted: str = "#697B90"
    accent: str = "#137F78"
    reactor: str = "#356B9A"
    capacitor: str = "#A65C26"
    paper: str = "#FFFFFF"
    canvas: str = "#F4F7FB"
    border: str = "#D9E3ED"
    font: str = "DejaVu Sans, Arial, sans-serif"
    math_font: str = "STIX Math, Cambria Math, DejaVu Serif, serif"


def node(parent: ET.Element, name: str, **attributes: object) -> ET.Element:
    """Create an SVG element, skipping null attributes and escaping text safely."""
    obj = ET.SubElement(parent, f"{{{SVG_NS}}}{name}")
    for key, value in attributes.items():
        if value is not None:
            obj.set(key.replace("_", "-"), str(value))
    return obj


class SVGCanvas:
    """Editable, layered SVG canvas with reusable scientific typography."""

    def __init__(self, width: int, height: int, *, theme: Theme | None = None):
        self.width, self.height = width, height
        self.theme = theme or Theme()
        self.root = ET.Element(f"{{{SVG_NS}}}svg", {
            "version": "1.1", "viewBox": f"0 0 {width} {height}",
            "width": str(width), "height": str(height),
        })

    def metadata(self, title: str, description: str) -> None:
        node(self.root, "title").text = title
        node(self.root, "desc").text = description

    def layer(self, name: str, identifier: str) -> ET.Element:
        layer = node(self.root, "g", id=identifier)
        layer.set(f"{{{INK_NS}}}groupmode", "layer")
        layer.set(f"{{{INK_NS}}}label", name)
        return layer

    def group(self, parent: ET.Element, identifier: str, **attrs: object) -> ET.Element:
        return node(parent, "g", id=identifier, **attrs)

    def rect(self, parent: ET.Element, x: float, y: float, width: float,
             height: float, *, fill: str, radius: float = 0,
             stroke: str | None = None) -> ET.Element:
        return node(parent, "rect", x=x, y=y, width=width, height=height,
                    rx=radius, fill=fill, stroke=stroke)

    def circle(self, parent: ET.Element, x: float, y: float, radius: float, *,
               fill: str = "none", stroke: str | None = None,
               stroke_width: float = 3) -> ET.Element:
        return node(parent, "circle", cx=x, cy=y, r=radius, fill=fill,
                    stroke=stroke or self.theme.ink, stroke_width=stroke_width)

    def line(self, parent: ET.Element, x1: float, y1: float, x2: float, y2: float,
             *, color: str | None = None, width: float = 3.4) -> ET.Element:
        return node(parent, "line", x1=x1, y1=y1, x2=x2, y2=y2,
                    stroke=color or self.theme.ink, stroke_width=width,
                    stroke_linecap="round")

    def polyline(self, parent: ET.Element, points: Iterable[tuple[float, float]],
                 *, color: str | None = None, width: float = 3.4) -> ET.Element:
        return node(parent, "polyline",
                    points=" ".join(f"{x:.3f},{y:.3f}" for x, y in points),
                    fill="none", stroke=color or self.theme.ink,
                    stroke_width=width, stroke_linejoin="round",
                    stroke_linecap="round")

    def path(self, parent: ET.Element, d: str, *, color: str | None = None,
             width: float = 3.4, fill: str = "none") -> ET.Element:
        return node(parent, "path", d=d, fill=fill,
                    stroke=color or self.theme.ink, stroke_width=width,
                    stroke_linecap="round", stroke_linejoin="round")

    def text(self, parent: ET.Element, x: float, y: float, label: str,
             *, size: float = 20, color: str | None = None,
             anchor: str = "start", bold: bool = False) -> ET.Element:
        result = node(parent, "text", x=x, y=y, fill=color or self.theme.ink,
                      font_family=self.theme.font, font_size=size,
                      font_weight="700" if bold else "400", text_anchor=anchor)
        result.text = label
        return result

    def math(self, parent: ET.Element, x: float, y: float,
             tokens: Iterable[tuple[str, str]], *, size: float = 18,
             color: str | None = None, anchor: str = "start") -> ET.Element:
        """Draw italic variables, upright units, and bold upright matrices.

        No whitespace is inserted between text spans, preserving typesetting.
        """
        styles = {
            "variable": ("italic", "400", None),
            "roman": ("normal", "400", None),
            "unit": ("normal", "400", None),
            "matrix": ("normal", "700", None),
            "subscript-variable": ("italic", "400", "sub"),
            "subscript-roman": ("normal", "400", "sub"),
        }
        t = node(parent, "text", x=x, y=y, fill=color or self.theme.ink,
                 font_family=self.theme.math_font, font_size=size,
                 text_anchor=anchor, data_math_notation="mixed")
        for value, role in tokens:
            if role not in styles:
                raise ValueError(f"Unrecognized math typography role: {role}")
            if not value:
                continue
            italic, weight, shift = styles[role]
            span = node(t, "tspan", font_style=italic,
                        font_weight=weight,
                        font_size=size * 0.67 if shift else size,
                        baseline_shift=shift, data_math_role=role)
            span.text = value
        return t

    def save(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(self.root).write(output, encoding="utf-8",
                                        xml_declaration=True)
        return output

    def as_svg_bytes(self) -> bytes:
        return ET.tostring(self.root, encoding="utf-8", xml_declaration=True)
