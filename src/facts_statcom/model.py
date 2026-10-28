"""Validated, immutable STATCOM schematic configurations.

Models express circuit structure; rendering is deliberately separated.
No topology here constitutes a steady-state or switching simulation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class Topology(str, Enum):
    BASIC = "basic"
    TWO_LEVEL = "two-level"
    NPC = "npc"
    CHB = "chb"
    MMC = "mmc"
    COMPLETE = "complete"
    CONTROL = "control"


class CHBConnection(str, Enum):
    STAR = "star"
    DELTA = "delta"


@dataclass(frozen=True)
class STATCOMConfig:
    """Immutable configuration shared by renderers, CLI and topology checker."""

    title: str
    topology: Topology
    transformer: bool = True
    cells_per_phase: int = 2
    submodules_per_arm: int = 2
    chb_connection: CHBConnection = CHBConnection.STAR

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a nonempty string")
        if not isinstance(self.topology, Topology):
            object.__setattr__(self, "topology", Topology(self.topology))
        if not isinstance(self.chb_connection, CHBConnection):
            object.__setattr__(self, "chb_connection", CHBConnection(self.chb_connection))
        if not isinstance(self.transformer, bool):
            raise ValueError("transformer must be a boolean")
        for name in ("cells_per_phase", "submodules_per_arm"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 3:
                raise ValueError(f"{name} must be an integer from 1 to 3")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> STATCOMConfig:
        if not isinstance(data, Mapping):
            raise ValueError("configuration must be a JSON object")
        return cls(
            title=data["title"],
            topology=Topology(data["topology"]),
            transformer=data.get("transformer", True),
            cells_per_phase=data.get("cells_per_phase", 2),
            submodules_per_arm=data.get("submodules_per_arm", 2),
            chb_connection=CHBConnection(data.get("chb_connection", "star")),
        )

    @classmethod
    def from_json(cls, file: str | Path) -> STATCOMConfig:
        with Path(file).open("r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title, "topology": self.topology.value,
            "transformer": self.transformer,
            "cells_per_phase": self.cells_per_phase,
            "submodules_per_arm": self.submodules_per_arm,
            "chb_connection": self.chb_connection.value,
        }


def presets() -> dict[str, STATCOMConfig]:
    """Provide one reproducible diagram per supported topology / connection."""
    return {
        "basic": STATCOMConfig("Basic STATCOM connection", Topology.BASIC),
        "two-level": STATCOMConfig("Three-phase two-level VSC", Topology.TWO_LEVEL),
        "npc": STATCOMConfig("Three-level diode-clamped NPC VSC", Topology.NPC),
        "chb-star": STATCOMConfig("CHB STATCOM | star-connected phase arms", Topology.CHB),
        "chb-delta": STATCOMConfig("CHB STATCOM | delta-connected phase arms", Topology.CHB,
                                    chb_connection=CHBConnection.DELTA),
        "mmc": STATCOMConfig("Double-star MMC-type STATCOM", Topology.MMC),
        "complete": STATCOMConfig("STATCOM connected to a three-phase grid", Topology.COMPLETE),
        "control": STATCOMConfig("STATCOM dq control architecture", Topology.CONTROL),
    }
