"""Device-level checks including power-polarity and floating capacitors."""

from dataclasses import replace

import pytest

from facts_statcom.model import presets
from facts_statcom.netlist import CircuitGraph, build_netlist


def test_two_level_six_igbts_and_antiparallel_diodes():
    g = build_netlist(presets()["two-level"])
    assert len(g.devices_of("igbt")) == 6
    assert len(g.devices_of("diode")) == 6
    assert len(g.devices_of("capacitor")) == 1
    for s in g.devices_of("igbt"):
        d = g.devices[f"D_{s.name}"]
        assert d.terminals == {"A": s.terminals["E"],
                               "K": s.terminals["C"]}
        assert s.terminals["G"].startswith("GATE_")
    for p in "ABC":
        assert g.devices[f"S{p}1"].terminals["E"] == p
        assert g.devices[f"S{p}2"].terminals["C"] == p
    assert g.devices["Cdc"].terminals == {"P": "DC+", "N": "DC-"}


def test_npc_series_and_clamp_polarities():
    g = build_netlist(presets()["npc"])
    assert len(g.devices_of("igbt")) == 12
    assert len(g.devices_of("diode")) == 18  # 12 reverse diodes + 6 clamp diodes
    assert len(g.devices_of("capacitor")) == 2
    assert g.devices["Cdc1"].terminals["N"] == "DCM"
    assert g.devices["Cdc2"].terminals["P"] == "DCM"
    for p in "ABC":
        assert g.devices[f"DCL{p}1"].terminals == {"A": "DCM", "K": f"{p}_upper"}
        assert g.devices[f"DCL{p}2"].terminals == {"A": f"{p}_lower", "K": "DCM"}
        assert g.devices[f"S{p}2"].terminals["E"] == p
        assert g.devices[f"S{p}3"].terminals["C"] == p


@pytest.mark.parametrize("n", [1, 2, 3])
def test_chb_isolated_capacitors_and_star_delta(n):
    for name in ("chb-star", "chb-delta"):
        g = build_netlist(replace(presets()[name], cells_per_phase=n))
        assert len(g.devices_of("igbt")) == 3*n*4
        assert len(g.devices_of("diode")) == 3*n*4
        assert len(g.devices_of("capacitor")) == 3*n
        dc_caps = g.devices_of("capacitor")
        assert len({x.terminals["P"] for x in dc_caps}) == len(dc_caps)
        assert len({x.terminals["N"] for x in dc_caps}) == len(dc_caps)
        assert not ({"DC+", "DC-"} & g.nets())
        for d in dc_caps:
            assert d.terminals["P"] != d.terminals["N"]
    delta = build_netlist(replace(presets()["chb-delta"], cells_per_phase=n))
    star = build_netlist(replace(presets()["chb-star"], cells_per_phase=n))
    assert "STAR_N" in star.nets() and "STAR_N" not in delta.nets()
    for p, q in (("A", "B"), ("B", "C"), ("C", "A")):
        assert delta.devices[f"{p}_HB{n}_R2"].terminals["C"] == q


@pytest.mark.parametrize("n", [1,2,3])
def test_mmc_submodule_capacitors_and_arm_connectivity(n):
    g = build_netlist(replace(presets()["mmc"], submodules_per_arm=n))
    assert len(g.devices_of("igbt")) == 6*n*2
    assert len(g.devices_of("diode")) == 6*n*2
    assert len(g.devices_of("capacitor")) == 6*n
    assert len(g.devices_of("inductor")) == 6
    for p in "ABC":
        u = f"{p}_U_SM1"
        lower = f"{p}_L_SM1"
        assert g.devices[f"{u}_S1"].terminals["E"] == "DC+"
        assert g.devices[f"L{p}_U"].terminals["B"] == p
        assert g.devices[f"L{p}_L"].terminals["A"] == p
        assert g.devices[f"{lower}_S1"].terminals["E"] == f"{p}_L_reactor"
        for side in ("U", "L"):
            for i in range(1,n+1):
                ident = f"{p}_{side}_SM{i}"
                cap = g.devices[f"{ident}_C"]
                assert g.devices[f"{ident}_S1"].terminals["C"] == cap.terminals["P"]
                assert g.devices[f"{ident}_S2"].terminals["E"] == cap.terminals["N"]


def test_graph_rejects_component_self_short_and_duplicate():
    g = CircuitGraph()
    with pytest.raises(ValueError):
        g.add("C", "capacitor", P="same", N="same")
    g.add("D", "diode", A="x", K="y")
    with pytest.raises(ValueError):
        g.add("D", "diode", A="a", K="b")
