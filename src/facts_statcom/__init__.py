"""STATCOM/STATCON circuit diagrams and independent operation teaching models.

The legacy public API is lazily loaded, so importing the numeric operation
package never requires importing the schematic renderer or SVG symbols.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "CHBConnection", "CircuitGraph", "Device", "ElectricalSymbols",
    "MMCSubmodule", "PhysicalComponent", "Port", "STATCOMConfig",
    "STATCOMRenderer", "SVGCanvas", "SemiconductorDevice", "SwitchingCell",
    "Theme", "Topology", "build_netlist", "presets", "render_svg",
]
__version__ = "0.2.0"

_EXPORTS = {
    "CHBConnection": "model", "STATCOMConfig": "model",
    "Topology": "model", "presets": "model",
    "CircuitGraph": "netlist", "Device": "netlist", "build_netlist": "netlist",
    "STATCOMRenderer": "renderer", "render_svg": "renderer",
    "SVGCanvas": "svg", "Theme": "svg",
    "ElectricalSymbols": "symbols", "PhysicalComponent": "symbols",
    "Port": "symbols", "SemiconductorDevice": "symbols",
    "SwitchingCell": "symbols", "MMCSubmodule": "symbols",
}


def __getattr__(name: str) -> Any:
    """Resolve previous imports without loading schematic code for plot models."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    attribute = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = attribute
    return attribute


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
