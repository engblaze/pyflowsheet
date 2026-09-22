import os
from pathlib import Path

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.core import Flowsheet

PID_YAML = """
metadata:
  title: "Hydrocarbon Treatment P&ID"
  version: "1.0"
equipment:
  - id: V-101
    name: "Feed Surge Drum"
    type: "HorizontalVessel"
    position: [60, 100]
    size: [90, 40]

  - id: P-101
    name: "Charge Pump"
    type: "ProgressiveCavityPump"
    position: [190, 105]
    size: [50, 30]

  - id: E-101
    name: "Feed Preheater"
    type: "ShellAndTubeExchanger"
    position: [280, 95]
    size: [70, 40]

  - id: S-101
    name: "Phase Separator"
    type: "HorizontalSettler"
    position: [390, 90]
    size: [100, 50]

  - id: PCV-101
    name: "Offgas Backpressure Valve"
    type: "ControlValve"
    valve_type: "globe"
    actuator: "pneumatic"
    failure_mode: "fail_closed"
    position: [420, 20]
    size: [28, 18]

  - id: PIT-101
    name: "Pressure Transmitter"
    type: "Instrument"
    tag: "PIT-101"
    balloon_type: "discrete"
    location: "field"
    position: [370, 20]
    size: [24, 24]

  - id: PSV-101
    name: "Vessel Relief Valve"
    type: "SafetyReliefValve"
    position: [470, 20]
    size: [24, 24]

streams:
  - id: S-01
    from: V-101:Out
    to: P-101:In
    line_type: process

  - id: S-02
    from: P-101:Out
    to: E-101:TubeIn
    line_type: process

  - id: S-03
    from: E-101:TubeOut
    to: S-101:Feed
    line_type: process

  - id: S-04
    from: S-101:Vent
    to: PCV-101:In
    line_type: process

  - id: SIG-01
    from: PIT-101:Out
    to: PCV-101:Actuator
    line_type: pneumatic
"""


def test_pid_yaml_loading_and_rendering(tmp_path):
    out_svg = os.path.join(tmp_path, "pid_flowsheet.svg")
    fs = Flowsheet.from_yaml(PID_YAML)
    ctx = SvgContext(out_svg)
    fs.draw(ctx)
    svg_content = ctx.render(saveFile=True)

    assert os.path.exists(out_svg)
    # Check all key equipment tags are present
    assert "V-101" in svg_content
    assert "P-101" in svg_content
    assert "E-101" in svg_content
    assert "S-101" in svg_content
    assert "PCV-101" in svg_content
    assert "PIT-101" in svg_content
    assert "PSV-101" in svg_content
    # Check signal line ID
    assert 'id="SIG-01"' in svg_content


def test_pid_auto_layout_compatibility():
    fs = Flowsheet.from_yaml(PID_YAML)
    # Auto layout should execute without crash across all new standards elements
    fs.auto_layout(force_reposition=False)
    for u in fs.unitOperations.values():
        assert u.position is not None
        assert u.size is not None


def test_complete_pid_flowsheet_example_file(tmp_path):
    yaml_path = Path("examples/complete_pid_flowsheet.yaml")
    assert yaml_path.exists()

    fs = Flowsheet.from_yaml(yaml_path)
    assert len(fs.unitOperations) == 7
    assert len(fs.streams) == 5

    out_svg = os.path.join(tmp_path, "example_pid.svg")
    ctx = SvgContext(out_svg)
    fs.draw(ctx)
    svg_content = ctx.render(saveFile=True)
    assert os.path.exists(out_svg)
    assert len(svg_content) > 0


def test_pid_flowsheet_to_dict_roundtrip():
    yaml_input = """
metadata:
  title: "Roundtrip Test P&ID"
equipment:
  - id: PCV-201
    type: "ControlValve"
    valve_type: "ball"
    actuator: "solenoid"
    failure_mode: "fail_open"
    position: [100, 50]
    size: [30, 20]

  - id: FIT-201
    type: "Instrument"
    tag: "FIT-201"
    balloon_type: "shared_display"
    location: "control_room"
    position: [50, 50]
    size: [28, 28]

  - id: V-201
    type: "Vessel"
    head_type: "flat"
    position: [0, 0]
    size: [40, 80]
streams: []
"""
    fs = Flowsheet.from_yaml(yaml_input)
    exported = fs.to_dict()

    # Verify serialization dictionary contains new equipment attributes
    eq_map = {eq["id"]: eq for eq in exported["components"]["equipment"]}

    assert eq_map["PCV-201"]["valve_type"] == "ball"
    assert eq_map["PCV-201"]["actuator"] == "solenoid"
    assert eq_map["PCV-201"]["failure_mode"] == "fail_open"

    assert eq_map["FIT-201"]["tag"] == "FIT-201"
    assert eq_map["FIT-201"]["balloon_type"] == "shared_display"
    assert eq_map["FIT-201"]["location"] == "control_room"

    assert eq_map["V-201"]["head_type"] == "flat"

    # Verify deserialization preserves attributes
    fs2 = Flowsheet.from_dict(exported)
    pcv2 = fs2.unitOperations["PCV-201"]
    assert getattr(pcv2, "valve_type", getattr(pcv2, "body_type", None)) == "ball"
    assert pcv2.actuator == "solenoid"
    assert pcv2.failure_mode == "fail_open"

    fit2 = fs2.unitOperations["FIT-201"]
    assert fit2.tag.raw == "FIT-201"
    assert fit2.balloon_type == "shared_display"
    assert fit2.location == "control_room"

    v2 = fs2.unitOperations["V-201"]
    assert v2.head_type == "flat"
