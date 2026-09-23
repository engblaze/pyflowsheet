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


def test_flowsheet_to_dict_deduplicates_aliased_ports():
    from pyflowsheet.unitoperations import AirCooler, HorizontalSettler
    from pyflowsheet.valves import ControlValve

    fs = Flowsheet("TEST_DEDUP", "Test Port Deduplication")
    cv = ControlValve("CV-1", "Control Valve")
    settler = HorizontalSettler("S-1", "Horizontal Settler")
    cooler = AirCooler("AC-1", "Air Cooler")

    fs.addUnits([cv, settler, cooler])
    d = fs.to_dict()

    eq_map = {eq["id"]: eq for eq in d["components"]["equipment"]}

    # ControlValve has Actuator and Signal aliased to the same port object, plus In and Out.
    # Total unique ports for ControlValve should be 3: In, Out, Actuator
    cv_ports = eq_map["CV-1"]["ports"]
    assert len(cv_ports) == 3
    cv_port_ids = [p["id"] for p in cv_ports]
    assert "Actuator" in cv_port_ids
    assert "Signal" not in cv_port_ids

    # HorizontalSettler:
    # ports are Feed, LightOut, HeavyOut, Vent
    # aliases: In -> Feed, Out -> LightOut, Top -> Vent, Bottom -> HeavyOut
    # Total unique ports should be 4: Feed, LightOut, HeavyOut, Vent
    settler_ports = eq_map["S-1"]["ports"]
    assert len(settler_ports) == 4
    settler_port_ids = [p["id"] for p in settler_ports]
    assert set(settler_port_ids) == {"Feed", "LightOut", "HeavyOut", "Vent"}

    # AirCooler:
    # In, Out
    # aliases: ProcessIn -> In, ProcessOut -> Out, TubeIn -> In, TubeOut -> Out
    # Total unique ports should be 2: In, Out
    cooler_ports = eq_map["AC-1"]["ports"]
    assert len(cooler_ports) == 2
    cooler_port_ids = [p["id"] for p in cooler_ports]
    assert set(cooler_port_ids) == {"In", "Out"}


def test_water_treatment_pid_autolayout_invariants():
    from pyflowsheet import Flowsheet

    fs = Flowsheet.from_yaml("examples/water_treatment_pid.yaml")
    fs.auto_layout(force_reposition=True)

    # 1. Invariant: Every routed segment must be strictly orthogonal (dx==0 or dy==0)
    for sid, s in fs.streams.items():
        assert len(s.calculated_route) >= 2, f"Stream {sid} missing route"
        for i in range(len(s.calculated_route) - 1):
            p1, p2 = s.calculated_route[i], s.calculated_route[i + 1]
            dx = abs(p2[0] - p1[0])
            dy = abs(p2[1] - p1[1])
            assert dx == 0 or dy == 0, f"Stream {sid} segment {p1}->{p2} is diagonal"

    # 2. Invariant: S05_1 and S06_1 must not share any corner vertices
    s05_corners = set(fs.streams["S05_1"].calculated_route[1:-1])
    s06_corners = set(fs.streams["S06_1"].calculated_route[1:-1])
    assert len(s05_corners.intersection(s06_corners)) == 0

    # 3. Invariant: All instruments must have X >= 120 (not stacked at X=60)
    inst_ids = [
        "FIT-101",
        "AIT-101",
        "LIT-101",
        "FIT-102",
        "LIT-102",
        "AIT-103",
        "PIT-101",
        "PDIT-101",
        "FIT-106",
        "TT-101",
        "FIT-108",
    ]
    for inst_id in inst_ids:
        assert fs.unitOperations[inst_id].position[0] > 100.0, (
            f"Instrument {inst_id} left on margin"
        )

    # 4. Invariant: Leader lines exist for contextually routed instruments
    for inst_id in [
        "FIT-101",
        "AIT-101",
        "LIT-101",
        "FIT-102",
        "LIT-102",
        "AIT-103",
        "PIT-101",
        "PDIT-101",
        "FIT-106",
        "TT-101",
    ]:
        inst = fs.unitOperations[inst_id]
        assert hasattr(inst, "leader_line") and inst.leader_line is not None
        assert len(inst.leader_line) >= 2, f"Instrument {inst_id} missing leader line"

    # 5. Collinear streams must be direct 2-point connections without jogs
    assert len(fs.streams["S02_1"].calculated_route) == 2
    assert len(fs.streams["S02_2"].calculated_route) == 2
    assert len(fs.streams["S02_3"].calculated_route) == 2
    assert len(fs.streams["S06_2"].calculated_route) == 2
    assert len(fs.streams["S06_3"].calculated_route) == 2

    # 6. S05 recycle stream routes cleanly in bottom corridor without looping to the top
    s05_3 = fs.streams["S05_3"].calculated_route
    for pt in s05_3:
        assert pt[1] >= 165.0, f"S05_3 waypoint {pt} looped into top corridor"
    assert s05_3[-1][0] < s05_3[0][0]

    # 7. No equipment bounding boxes overlap
    from pyflowsheet.layout.spatial import AABB

    units = list(fs.unitOperations.values())
    for i in range(len(units)):
        u1 = units[i]
        b1 = AABB(
            u1.position[0],
            u1.position[1],
            u1.position[0] + u1.size[0],
            u1.position[1] + u1.size[1],
        )
        for j in range(i + 1, len(units)):
            u2 = units[j]
            b2 = AABB(
                u2.position[0],
                u2.position[1],
                u2.position[0] + u2.size[0],
                u2.position[1] + u2.size[1],
            )
            assert not b1.intersects(b2), f"Collision detected between {u1.id} and {u2.id}"
