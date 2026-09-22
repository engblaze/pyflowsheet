from pyflowsheet import Flowsheet
from pyflowsheet.backends import SvgContext
from pyflowsheet.unitoperations import DistillationColumn, Valve, Vessel


def test_flowsheet_auto_layout_positions_units_and_routes_streams():
    fs = Flowsheet("AUTO_TEST", "Auto Layout Test")
    v1 = fs.unit(Vessel("V1", "Feed Tank", position=(0, 0), size=(40, 60)))
    col = fs.unit(DistillationColumn("COL", "Fractionator", position=(0, 0), size=(50, 120)))
    v2 = fs.unit(Vessel("V2", "Product Tank", position=(0, 0), size=(40, 60)))

    fs.connect("S01", v1["Out"], col["Feed"])
    fs.connect("S02", col["Distillate"], v2["In"])

    # Run auto layout
    fs.auto_layout()

    # Units must have non-zero, distinct X positions in topological order
    assert v1.position[0] < col.position[0] < v2.position[0]
    assert v1.position[0] >= 50.0

    # Streams must have calculated routes
    ctx = SvgContext("scratch_autolayout.svg")
    fs.draw(ctx)
    svg_content = ctx.dwg.tostring()
    assert 'id="S01"' in svg_content
    assert 'id="S02"' in svg_content


def test_flowsheet_auto_layout_crossover_bridges():
    fs = Flowsheet("CROSS_TEST", "Crossover Test")
    # Set up 4 units whose orthogonal stream routes cross:
    # S1 flows horizontally: (100, 150) -> (300, 150)
    # S2 flows vertically:   (200, 50) -> (200, 250)
    fs.unit(Vessel("U1", "U1", position=(100, 150), size=(20, 20)))
    fs.unit(Vessel("U2", "U2", position=(300, 150), size=(20, 20)))
    fs.unit(Vessel("U3", "U3", position=(200, 50), size=(20, 20)))
    fs.unit(Vessel("U4", "U4", position=(200, 250), size=(20, 20)))

    s1 = fs.connect("S1", fs.unitOperations["U1"]["Out"], fs.unitOperations["U2"]["In"])
    s2 = fs.connect("S2", fs.unitOperations["U3"]["Out"], fs.unitOperations["U4"]["In"])

    # Directly assign crossing orthogonal calculated routes
    s1.calculated_route = [(100.0, 150.0), (300.0, 150.0)]
    s2.calculated_route = [(200.0, 50.0), (200.0, 250.0)]

    # Run auto layout with fixed positions
    for u in fs.unitOperations.values():
        u.fixed = True

    fs.auto_layout()

    # Bridges should be detected on bridging stream
    bridging_streams = [s for s in fs.streams.values() if s.crossover_bridges]
    assert len(bridging_streams) == 1
    bridge = bridging_streams[0].crossover_bridges[0]
    assert len(bridge.intersection) == 2
    assert isinstance(bridge.intersection[0], float)
    assert isinstance(bridge.intersection[1], float)

    # Draw to SvgContext and verify jumper arc 'A ' is generated
    ctx = SvgContext("scratch_crossover.svg")
    fs.draw(ctx)
    svg_str = ctx.dwg.tostring()
    assert "A " in svg_str or "a " in svg_str


def test_flowsheet_auto_layout_inline_sequencing_and_knockout_masks():
    fs = Flowsheet("INLINE_TEST", "Inline Test")
    v1 = fs.unit(Vessel("TK1", "Source Tank", position=(50, 100), size=(40, 40)))
    v2 = fs.unit(Vessel("TK2", "Dest Tank", position=(350, 100), size=(40, 40)))
    valv = fs.unit(Valve("V101", "Control Valve", position=(0, 0), size=(20, 20)))

    s = fs.connect("S01", v1["Out"], v2["In"])
    s.line_sequence = ["V101"]

    for u in (v1, v2):
        u.fixed = True

    fs.auto_layout()

    # V101 must be positioned along the stream route
    assert valv.position[0] > v1.position[0]
    assert valv.position[0] < v2.position[0]

    # Stream should have knockout masks
    assert len(s.knockout_masks) == 1
    mask = s.knockout_masks[0]
    assert mask.width >= 20.0
    assert mask.height >= 20.0

    # Draw and verify knockout mask rendered in SVG
    ctx = SvgContext("scratch_inline.svg")
    fs.draw(ctx)
    svg_str = ctx.dwg.tostring()
    assert 'fill="rgb(255, 255, 255)"' in svg_str


def test_flowsheet_auto_layout_manual_routing_preserved():
    fs = Flowsheet("MANUAL_TEST", "Manual Route Test")
    v1 = fs.unit(Vessel("V1", "V1", position=(50, 100), size=(40, 40)))
    v2 = fs.unit(Vessel("V2", "V2", position=(250, 100), size=(40, 40)))

    s = fs.connect("S01", v1["Out"], v2["In"])
    s.manualRouting = [(0, 50), (150, 0), (0, -50)]

    for u in (v1, v2):
        u.fixed = True

    fs.auto_layout()

    # Calculated route must match the manual routing steps
    assert len(s.calculated_route) == 5
    p_start = s.fromPort.get_position()
    assert s.calculated_route[0] == p_start
    assert s.calculated_route[1] == (p_start[0], p_start[1] + 50)


def test_flowsheet_auto_layout_force_reposition():
    fs = Flowsheet("FORCE_TEST", "Force Reposition Test")
    v1 = fs.unit(Vessel("V1", "V1", position=(500, 500), size=(40, 40)))
    v2 = fs.unit(Vessel("V2", "V2", position=(600, 500), size=(40, 40)))
    fs.connect("S01", v1["Out"], v2["In"])

    # Without force_reposition, non-zero positions are preserved
    fs.auto_layout(origin=(60, 100), force_reposition=False)
    assert v1.position == (500, 500)

    # With force_reposition, non-zero positions are re-laid out
    fs.auto_layout(origin=(60, 100), force_reposition=True)
    assert v1.position[0] < v2.position[0]
    assert v1.position[0] == 60.0


def test_flowsheet_auto_layout_empty_flowsheet():
    fs = Flowsheet("EMPTY_TEST", "Empty Flowsheet")
    # Should run cleanly with no units or streams
    fs.auto_layout()
    ctx = SvgContext("scratch_empty.svg")
    fs.draw(ctx)
    svg_str = ctx.dwg.tostring()
    assert "<svg" in svg_str


def test_flowsheet_auto_layout_stream_label_placement():
    fs = Flowsheet("LABEL_TEST", "Label Placement Test")
    v1 = fs.unit(Vessel("V1", "V1", position=(0, 0), size=(40, 40)))
    v2 = fs.unit(Vessel("V2", "V2", position=(0, 0), size=(40, 40)))
    s = fs.connect("S_LONG_LABEL", v1["Out"], v2["In"])

    fs.auto_layout()

    # labelOffset should have been updated by label solver from default (0, 10)
    assert s.labelOffset != (0, 10)
