import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.valves.actuators import (
    ActuatorKind,
    ActuatorType,
    ControlValve,
    FailureKind,
    FailureMode,
)


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "control_valves_test.svg")
    return SvgContext(out_file)


def test_control_valve_ports():
    cv = ControlValve("PCV-101", actuator="pneumatic", failure_mode="fail_closed")
    assert "In" in cv.ports
    assert "Out" in cv.ports
    assert "Actuator" in cv.ports or "Signal" in cv.ports
    signal_port = cv.ports.get("Actuator") or cv.ports.get("Signal")
    # Signal port should be at top of actuator
    assert signal_port.relativePosition[1] <= 0.1
    assert signal_port.normal == (0, -1)
    assert cv.ports["Signal"] is cv.ports["Actuator"]


def test_control_valve_rendering_all_combinations(svg_ctx):
    actuators = ["manual", "pneumatic", "electric", "solenoid", "piston"]
    failures = ["none", "fail_closed", "fail_open", "fail_locked", "fail_indeterminate"]

    for idx, act in enumerate(actuators):
        fail = failures[idx % len(failures)]
        cv = ControlValve(
            id=f"CV_{idx}",
            actuator=act,
            failure_mode=fail,
            position=(10 + idx * 60, 60),
            size=(30, 20),
            actuator_height=25.0,
        )
        svg_ctx.startGroup(cv.id)
        svg_ctx.startTransformedGroup(cv)
        cv.draw(svg_ctx)
        svg_ctx.endGroup()
        cv.drawTextLayer(svg_ctx)
        svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    assert len(output) > 1000


def test_control_valve_body_types(tmp_path):
    for body in ["globe", "ball", "butterfly", "needle", "gate"]:
        cv = ControlValve(
            id=f"CV_{body}",
            body_type=body,
            actuator="pneumatic",
            failure_mode="fail_open",
            position=(10, 10),
            size=(30, 20),
        )
        ctx = SvgContext(os.path.join(tmp_path, f"cv_{body}.svg"))
        ctx.startGroup(cv.id)
        ctx.startTransformedGroup(cv)
        cv.draw(ctx)
        ctx.endGroup()
        output = ctx.render(saveFile=False)
        assert "<path" in output


def test_control_valve_individual_svg_elements(tmp_path):
    # Test electric actuator has 'M'
    cv_elec = ControlValve("CV_E", actuator="electric", failure_mode="none")
    ctx_e = SvgContext(os.path.join(tmp_path, "cv_e.svg"))
    ctx_e.startGroup(cv_elec.id)
    cv_elec.draw(ctx_e)
    ctx_e.endGroup()
    out_e = ctx_e.render(saveFile=False)
    assert ">M<" in out_e

    # Test solenoid actuator has 'S'
    cv_sol = ControlValve("CV_S", actuator="solenoid", failure_mode="none")
    ctx_s = SvgContext(os.path.join(tmp_path, "cv_s.svg"))
    ctx_s.startGroup(cv_sol.id)
    cv_sol.draw(ctx_s)
    ctx_s.endGroup()
    out_s = ctx_s.render(saveFile=False)
    assert ">S<" in out_s

    # Test pneumatic actuator has path/chord
    cv_pneu = ControlValve("CV_P", actuator="pneumatic", failure_mode="fail_closed")
    ctx_p = SvgContext(os.path.join(tmp_path, "cv_p.svg"))
    ctx_p.startGroup(cv_pneu.id)
    cv_pneu.draw(ctx_p)
    ctx_p.endGroup()
    out_p = ctx_p.render(saveFile=False)
    assert "<path" in out_p

    # Test failure modes: fail_locked
    cv_lock = ControlValve("CV_L", actuator="pneumatic", failure_mode="fail_locked")
    ctx_l = SvgContext(os.path.join(tmp_path, "cv_l.svg"))
    ctx_l.startGroup(cv_lock.id)
    cv_lock.draw(ctx_l)
    ctx_l.endGroup()
    out_l = ctx_l.render(saveFile=False)
    assert "<line" in out_l


def test_actuator_type_definitions():
    assert ActuatorType is ActuatorKind
    assert FailureMode is FailureKind


def test_valves_package_actuator_exports():
    import pyflowsheet.valves as valves

    for name in ["ControlValve", "ActuatorKind", "FailureKind", "ActuatorType", "FailureMode"]:
        assert hasattr(valves, name)
        assert name in valves.__all__
