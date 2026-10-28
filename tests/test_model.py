"""Validation and JSON contracts for an independent future FACTS family."""

import json
from dataclasses import replace

import pytest

from facts_statcom.model import CHBConnection, STATCOMConfig, Topology, presets


def test_all_presets_and_serialization():
    cfg = presets()
    assert set(cfg) == {"basic", "two-level", "npc", "chb-star", "chb-delta",
                        "mmc", "complete", "control"}
    for name, model in cfg.items():
        assert STATCOMConfig.from_dict(model.to_dict()) == model, name


@pytest.mark.parametrize("config", [
    {"title": "", "topology": "mmc"},
    {"title": "x", "topology": "not-a-topology"},
    {"title": "x", "topology": "chb", "cells_per_phase": True},
    {"title": "x", "topology": "chb", "cells_per_phase": 4},
    {"title": "x", "topology": "mmc", "submodules_per_arm": 0},
    {"title": "x", "topology": "chb", "chb_connection": "square"},
    {"title": "x", "topology": "basic", "transformer": "true"},
])
def test_invalid_configuration(config):
    with pytest.raises((ValueError, TypeError)):
        STATCOMConfig.from_dict(config)


def test_json_round_trip(tmp_path):
    cfg = replace(presets()["chb-delta"], cells_per_phase=3)
    fp = tmp_path / "topology.json"
    fp.write_text(json.dumps(cfg.to_dict()), encoding="utf-8")
    assert STATCOMConfig.from_json(fp) == cfg


def test_star_and_delta_are_separate_topologies():
    a, b = presets()["chb-star"], presets()["chb-delta"]
    assert a.chb_connection is CHBConnection.STAR
    assert b.chb_connection is CHBConnection.DELTA
    assert a.topology is b.topology is Topology.CHB
