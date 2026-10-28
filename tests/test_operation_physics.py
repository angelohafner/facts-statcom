"""Independent phasor-model regression tests with explicit injection signs."""

import cmath
import math
from dataclasses import replace

import pytest

from facts_statcom.operation import CouplingModel, OperationCase


def test_default_zero_angle_capacitive_and_inductive():
    c = CouplingModel(v_pcc_pu=1, x_coupling_pu=.2, i_limit_pu=.8)
    supplied = c.operating_point(1.10)
    absorbed = c.operating_point(.90)
    assert supplied.q_injected_pu == pytest.approx(.5)
    assert supplied.p_injected_pu == pytest.approx(0)
    assert supplied.i_capacitive_pu == pytest.approx(.5)
    assert supplied.i_q_dq_pu == pytest.approx(-.5)
    assert cmath.phase(supplied.i_injected) == pytest.approx(-math.pi/2)
    assert supplied.mode == "capacitive injection"
    assert absorbed.q_injected_pu == pytest.approx(-.5)
    assert absorbed.i_capacitive_pu == pytest.approx(-.5)
    assert cmath.phase(absorbed.i_injected) == pytest.approx(math.pi/2)
    assert absorbed.mode == "inductive absorption"


def test_complex_power_consistent_with_phasor_current():
    c = CouplingModel(v_pcc_pu=.96, x_coupling_pu=.15, i_limit_pu=2)
    p = c.operating_point(1.04, 6)
    expected = p.v_pcc * p.i_injected.conjugate()
    assert expected.real == pytest.approx(p.p_injected_pu)
    assert expected.imag == pytest.approx(p.q_injected_pu)
    assert p.p_injected_pu == pytest.approx(.96*1.04*math.sin(math.radians(6))/.15)
    assert p.q_injected_pu == pytest.approx(.96*(1.04*math.cos(math.radians(6))-.96)/.15)
    assert p.e_converter == pytest.approx(p.v_pcc+1j*c.x_coupling_pu*p.i_injected)


def test_active_power_is_odd_and_reactive_power_even_in_angle():
    c=CouplingModel()
    pos, neg = c.operating_point(1.05, 8), c.operating_point(1.05, -8)
    assert pos.p_injected_pu == pytest.approx(-neg.p_injected_pu)
    assert pos.q_injected_pu == pytest.approx(neg.q_injected_pu)


def test_zero_reactive_transfer_when_e_equals_v():
    c=CouplingModel(v_pcc_pu=.93)
    p=c.operating_point(.93)
    assert p.i_injected == 0j
    assert p.p_injected_pu == 0
    assert p.q_injected_pu == 0
    assert p.mode == "no reactive exchange"


def test_current_limit_status_flags_not_silent_clipping():
    c=CouplingModel(x_coupling_pu=.1, i_limit_pu=.5)
    p=c.operating_point(1.2)
    assert p.current_within_rating is False
    assert p.current_magnitude_pu == pytest.approx(2)


def test_inverse_converter_voltage_at_delta_zero():
    c=CouplingModel(v_pcc_pu=1.02, x_coupling_pu=.18)
    for i_cap in (-.4,0,.25,.8):
        e=c.ideal_e_for_reactive_current(i_cap)
        op=c.operating_point(e)
        assert op.i_capacitive_pu == pytest.approx(i_cap)
    with pytest.raises(ValueError):
        c.ideal_e_for_reactive_current(-10)


def test_fundamental_waves_and_converter_kvl():
    c=CouplingModel(frequency_hz=60)
    t=[k/60/200 for k in range(201)]
    v,e,i=c.instantaneous_fundamentals(t,1.08)
    assert len(v)==len(t)
    assert v[0]==pytest.approx(0)
    assert e[0]==pytest.approx(0)
    assert i[0]==pytest.approx(-math.sqrt(2)*.4)
    assert i[50]==pytest.approx(0,abs=1e-12)
    assert i[100]==pytest.approx(math.sqrt(2)*.4)


@pytest.mark.parametrize("changes", [
    {"v_pcc_pu": 0}, {"x_coupling_pu": -1},
    {"frequency_hz": float('nan')}, {"i_limit_pu": True},
])
def test_invalid_coupling_parameters(changes):
    with pytest.raises(ValueError):
        replace(CouplingModel(),**changes)


def test_invalid_operating_point():
    c=CouplingModel()
    with pytest.raises(ValueError):
        c.operating_point(-1)
    with pytest.raises(ValueError):
        c.operating_point(1.0,float('inf'))


def test_operation_configuration_round_trip_and_validation():
    case=OperationCase()
    assert OperationCase.from_dict(case.to_dict())==case
    assert case.coupling.v_pcc_pu>0
    with pytest.raises(ValueError):
        OperationCase.from_dict({"unknown_field":5})
    with pytest.raises(ValueError):
        replace(case,converter_voltage_low_pu=1.5)
