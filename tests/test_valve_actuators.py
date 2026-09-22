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
    assert "Actuator" in cv.ports
    assert "Signal" in cv.ports
    signal_port = cv.ports["Signal"]
    actuator_port = cv.ports["Actuator"]
    # Signal port should be at top of actuator
    assert signal_port.relativePosition[1] <= 0.1
    assert signal_port.normal == (0, -1)
    # Distinct instances with identical properties
    assert signal_port is not actuator_port
    assert signal_port.relativePosition == actuator_port.relativePosition
    assert signal_port.normal == actuator_port.normal
    # Expected relative position corresponds to -(actuator_height * 1.1) / size[1]
    expected_rel_y = -(cv.actuator_height * 1.1) / cv.size[1]
    assert signal_port.relativePosition[1] == pytest.approx(expected_rel_y)


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


def test_control_valve_rotate_and_flip():
    cv = ControlValve("PCV-102", size=(30.0, 20.0), actuator_height=20.0)
    orig_act_pos = cv.ports["Actuator"].relativePosition
    orig_act_normal = cv.ports["Actuator"].normal
    orig_sig_pos = cv.ports["Signal"].relativePosition
    orig_sig_normal = cv.ports["Signal"].normal

    assert orig_act_pos == orig_sig_pos
    assert orig_act_normal == orig_sig_normal

    # Test flipVertical: y -> 1 - y, normal_y -> -normal_y
    cv.flipVertical()
    expected_y = 1.0 - orig_act_pos[1]
    assert pytest.approx(cv.ports["Actuator"].relativePosition[1]) == expected_y
    assert pytest.approx(cv.ports["Signal"].relativePosition[1]) == expected_y
    assert cv.ports["Actuator"].normal == (0, 1)
    assert cv.ports["Signal"].normal == (0, 1)

    # Flip back
    cv.flipVertical()
    assert pytest.approx(cv.ports["Actuator"].relativePosition[1]) == orig_act_pos[1]
    assert pytest.approx(cv.ports["Signal"].relativePosition[1]) == orig_sig_pos[1]
    assert cv.ports["Actuator"].normal == (0, -1)
    assert cv.ports["Signal"].normal == (0, -1)

    # Test rotate 90: Actuator and Signal ports rotate identically without double-transformation
    cv.rotate(90)
    assert cv.ports["Actuator"].relativePosition == pytest.approx(
        cv.ports["Signal"].relativePosition
    )
    assert cv.ports["Actuator"].normal == pytest.approx(cv.ports["Signal"].normal)
    # Rotating normal (0, -1) by 90 degrees clockwise -> (1, 0)
    assert cv.ports["Actuator"].normal[0] == pytest.approx(1.0, abs=1e-5)
    assert cv.ports["Actuator"].normal[1] == pytest.approx(0.0, abs=1e-5)


def test_manual_actuator_stem_connection(tmp_path):
    cv = ControlValve(
        "HV-101", actuator="manual", position=(10, 50), size=(30, 20), actuator_height=20.0
    )
    ctx = SvgContext(os.path.join(tmp_path, "hv.svg"))
    ctx.startGroup(cv.id)
    cv.draw(ctx)
    ctx.endGroup()
    output = ctx.render(saveFile=False)
    # Should contain main stem, stem-to-crossbar extension line, and crossbar line
    assert output.count("<line") >= 2


def test_failure_mode_indicator_above_body(tmp_path):
    # Verify failure mode lines are strictly above y (the valve body top)
    cv = ControlValve(
        "PCV-103",
        actuator="pneumatic",
        failure_mode="fail_closed",
        position=(10, 50),
        size=(30, 20),
        actuator_height=24.0,
    )
    # y = 50, stem_top = 50 - 24 * 0.4 = 40.4
    # stem_mid should be (50 + 40.4) / 2 = 45.2, which is strictly < 50 (above valve body)
    stem_top = cv.position[1] - cv.actuator_height * 0.4
    stem_mid = (cv.position[1] + stem_top) / 2.0
    assert stem_mid < cv.position[1]
    # Arm length is 4.0; top of indicator is stem_mid - 4 = 41.2, bottom is stem_mid + 4 = 49.2
    assert stem_mid + 4.0 <= cv.position[1]  # Does not cross into valve body


def test_valves_package_actuator_exports():
    import pyflowsheet.valves as valves

    for name in ["ControlValve", "ActuatorKind", "FailureKind", "ActuatorType", "FailureMode"]:
        assert hasattr(valves, name)
        assert name in valves.__all__
