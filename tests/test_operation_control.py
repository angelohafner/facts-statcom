"""STATCOM voltage-control low-order surrogate and event validation tests."""

from dataclasses import replace

import pytest

from facts_statcom.operation import (
    CouplingModel, GridVoltageEvent, OperationCase, VoltageControlConfig,
    simulate_voltage_control,
)


def _run(case):
    return simulate_voltage_control(
        case.control,case.voltage_events,
        coupling_x_pu=case.coupling.x_coupling_pu,
        end_time_s=case.end_time_s,time_step_s=case.time_step_s,
    )


def test_voltage_droop_characteristic_and_saturation():
    c=VoltageControlConfig(v_ref_pu=1,droop_pu_per_i_pu=.03,current_limit_pu=.8)
    assert c.droop_current_reference(1)==pytest.approx(0)
    assert c.droop_current_reference(.985)==pytest.approx(.5)
    assert c.droop_current_reference(1.015)==pytest.approx(-.5)
    assert c.droop_current_reference(.8)==pytest.approx(.8)
    assert c.droop_current_reference(1.2)==pytest.approx(-.8)


def test_static_network_surrogate_saturated_and_unsaturated():
    c=VoltageControlConfig(grid_x_pu=.12,droop_pu_per_i_pu=.03,current_limit_pu=.8)
    i,v=c.equilibrium(1.)
    assert i==pytest.approx(0)
    assert v==pytest.approx(1)
    i,v=c.equilibrium(.97)
    assert i==pytest.approx(.2)
    assert v==pytest.approx(.994)
    i,v=c.equilibrium(.8)
    assert i==pytest.approx(.8)
    assert v==pytest.approx(.896)
    i,v=c.equilibrium(1.045)
    assert i==pytest.approx(-.3)
    assert v==pytest.approx(1.009)


def test_time_trace_starts_at_equilibrium_and_reacts_to_sag_and_rise():
    case=OperationCase()
    t=_run(case)
    assert len(t.time_s)==len(t.q_injected_pu)==len(t.e_required_pu)
    assert t.time_s[0]==0
    assert t.time_s[-1]==pytest.approx(case.end_time_s)
    assert t.v_pcc_pu[0]==pytest.approx(1)
    sag=int(.40/case.time_step_s)
    assert t.i_capacitive_pu[sag]>.7
    assert t.v_pcc_pu[sag]>t.v_thevenin_pu[sag]
    assert t.q_injected_pu[sag]>0
    assert t.i_capacitive_pu[-1]<0
    assert t.q_injected_pu[-1]<0
    target_i, target_v=case.control.equilibrium(case.voltage_events[-1].v_thevenin_pu)
    assert t.i_capacitive_pu[-1]==pytest.approx(target_i, abs=.013)
    assert t.v_pcc_pu[-1]==pytest.approx(target_v,abs=.003)
    assert max(abs(i) for i in t.i_capacitive_pu)<=case.control.current_limit_pu+1e-12
    for v,i,q,e in zip(t.v_pcc_pu,t.i_capacitive_pu,
                       t.q_injected_pu,t.e_required_pu):
        assert q==pytest.approx(v*i)
        assert e==pytest.approx(v+case.coupling.x_coupling_pu*i)


def test_constant_voltage_remains_at_equilibrium():
    case=replace(OperationCase(),voltage_events=(GridVoltageEvent(0, .965),))
    t=_run(case)
    i,v=case.control.equilibrium(.965)
    assert max(abs(y-v) for y in t.v_pcc_pu)<1e-9
    assert max(abs(y-i) for y in t.i_capacitive_pu)<1e-9


def test_uncompensated_equivalent_voltage_is_thevenin():
    case=OperationCase()
    t=_run(case)
    for a,b,v in zip(t.v_thevenin_pu,t.i_capacitive_pu,t.v_pcc_pu):
        assert v==pytest.approx(a+case.control.grid_x_pu*b)


@pytest.mark.parametrize("events", [
    (), (GridVoltageEvent(.10,1.0),),
    (GridVoltageEvent(0,1),GridVoltageEvent(0,.9)),
    (GridVoltageEvent(0,1),GridVoltageEvent(.85,.9)),
    (GridVoltageEvent(0,1),GridVoltageEvent(.2,.9),GridVoltageEvent(.1,1)),
])
def test_bad_event_configuration(events):
    case=OperationCase()
    with pytest.raises(ValueError):
        simulate_voltage_control(case.control,events,coupling_x_pu=.2,end_time_s=.75)


def test_invalid_time_step_rejected():
    case=OperationCase()
    with pytest.raises(ValueError):
        simulate_voltage_control(case.control,case.voltage_events,
                                 coupling_x_pu=.2,time_step_s=.1)
    with pytest.raises(ValueError):
        simulate_voltage_control(case.control,case.voltage_events,
                                 coupling_x_pu=.2,time_step_s=1e-8)


def test_invalid_grid_voltage_event_and_controller():
    with pytest.raises(ValueError):
        GridVoltageEvent(-1,1)
    with pytest.raises(ValueError):
        GridVoltageEvent(0,-1)
    with pytest.raises(ValueError):
        replace(VoltageControlConfig(),droop_pu_per_i_pu=0)
