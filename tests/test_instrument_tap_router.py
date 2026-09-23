from pyflowsheet.layout.instruments import InstrumentTapPlacement, InstrumentTapRouter
from pyflowsheet.layout.spatial import AABB, SpatialIndex


def test_tap_routes_to_uncongested_side():
    spatial_index = SpatialIndex()
    # Populate congestion/obstacles below the pipe at (100, 100)
    spatial_index.insert("OBSTACLE", AABB(80.0, 110.0, 120.0, 160.0))

    router = InstrumentTapRouter(leader_length=40.0, balloon_radius=12.0)
    placement = router.place_and_route(
        tap=(100.0, 100.0),
        pipe_orientation="horizontal",
        spatial_index=spatial_index,
    )

    # Balloon placed ABOVE because below is congested
    assert placement.balloon_center[0] == 100.0
    assert placement.balloon_center[1] < 100.0
    assert placement.leader_line == [(100.0, 100.0), placement.balloon_center]
    assert isinstance(placement, InstrumentTapPlacement)
    assert placement.balloon_box == AABB(88.0, 48.0, 112.0, 72.0)


def test_tap_routes_below_when_above_congested():
    spatial_index = SpatialIndex()
    # Populate congestion/obstacles above the pipe at (100, 100)
    spatial_index.insert("OBSTACLE", AABB(80.0, 40.0, 120.0, 80.0))

    router = InstrumentTapRouter(leader_length=40.0, balloon_radius=12.0)
    placement = router.place_and_route(
        tap=(100.0, 100.0),
        pipe_orientation="horizontal",
        spatial_index=spatial_index,
    )

    # Balloon placed BELOW because above is congested
    assert placement.balloon_center[0] == 100.0
    assert placement.balloon_center[1] == 140.0
    assert placement.leader_line == [(100.0, 100.0), (100.0, 140.0)]
    assert placement.balloon_box == AABB(88.0, 128.0, 112.0, 152.0)


def test_vertical_pipe_tap_placement():
    spatial_index = SpatialIndex()
    router = InstrumentTapRouter(leader_length=40.0, balloon_radius=12.0)
    placement = router.place_and_route(
        tap=(100.0, 100.0),
        pipe_orientation="vertical",
        spatial_index=spatial_index,
    )

    # By default, routes to the right of vertical pipe
    assert placement.balloon_center[1] == 100.0
    assert placement.balloon_center[0] > 100.0
    assert placement.balloon_center == (140.0, 100.0)
    assert placement.balloon_box == AABB(128.0, 88.0, 152.0, 112.0)


def test_vertical_pipe_tap_routes_left_when_right_congested():
    spatial_index = SpatialIndex()
    # Populate congestion to the right of (100, 100)
    spatial_index.insert("OBSTACLE", AABB(120.0, 80.0, 160.0, 120.0))

    router = InstrumentTapRouter(leader_length=30.0, balloon_radius=10.0)
    placement = router.place_and_route(
        tap=(100.0, 100.0),
        pipe_orientation="vertical",
        spatial_index=spatial_index,
    )

    # Balloon placed LEFT because right is congested
    assert placement.balloon_center == (70.0, 100.0)
    assert placement.leader_line == [(100.0, 100.0), (70.0, 100.0)]
    assert placement.balloon_box == AABB(60.0, 90.0, 80.0, 110.0)


def test_instrument_host_resolution_and_tap_placement():
    from pyflowsheet import Flowsheet
    from pyflowsheet.instruments import Instrument
    from pyflowsheet.unitoperations import ControlValve

    fs = Flowsheet("INST_TEST", "Instrument Test")
    v = fs.unit(ControlValve("FCV-101", "Flow Valve", position=(200, 100), size=(24, 16)))
    inst = fs.unit(Instrument("FIT-101", "Flow Transmitter", position=(0, 0), size=(24, 24)))
    fs.connect("SIG1", inst["Bottom"], v["Actuator"], line_type="pneumatic")

    fs.auto_layout(force_reposition=True)

    # FIT-101 should be placed near FCV-101 (not left at (60, 220))
    assert abs(inst.position[0] - v.position[0]) <= 50.0
    assert hasattr(inst, "leader_line") and len(inst.leader_line) >= 2


def test_instrument_host_resolution_tier1_explicit_hints():
    from pyflowsheet import Flowsheet
    from pyflowsheet.instruments import Instrument
    from pyflowsheet.unitoperations import Vessel

    fs = Flowsheet("TIER1_TEST", "Tier 1 Test")
    tk = fs.unit(Vessel("TK-201", "Feed Tank", position=(300, 200), size=(50, 70)))
    inst = fs.unit(Instrument("LIT-999", "Tank Level", position=(0, 0), size=(24, 24)))
    inst.layout_hints = {"relative_to": "TK-201"}

    fs.auto_layout(force_reposition=True)

    # Placed directly adjacent to TK-201
    assert abs(inst.position[0] - tk.position[0]) <= 70.0
    assert hasattr(inst, "leader_line") and len(inst.leader_line) >= 2


def test_instrument_host_resolution_tier3_loop_matching():
    from pyflowsheet import Flowsheet
    from pyflowsheet.instruments import Instrument
    from pyflowsheet.unitoperations import Pump

    fs = Flowsheet("TIER3_TEST", "Tier 3 Test")
    p = fs.unit(Pump("P-102", "Transfer Pump", position=(350, 150), size=(30, 20)))
    inst = fs.unit(Instrument("FIT-102", "Flow Indicator", position=(0, 0), size=(24, 24)))

    fs.auto_layout(force_reposition=True)

    # FIT-102 matches P-102 via loop 102
    assert abs(inst.position[0] - p.position[0]) <= 50.0
    assert hasattr(inst, "leader_line") and len(inst.leader_line) >= 2


def test_instrument_leader_line_svg_rendering():
    from pyflowsheet import Flowsheet
    from pyflowsheet.backends import SvgContext
    from pyflowsheet.instruments import Instrument
    from pyflowsheet.unitoperations import ControlValve

    fs = Flowsheet("DRAW_TEST", "Leader Line SVG Test")
    v = fs.unit(ControlValve("FCV-101", "Flow Valve", position=(200, 100), size=(24, 16)))
    inst = fs.unit(Instrument("FIT-101", "Flow Transmitter", position=(0, 0), size=(24, 24)))
    fs.connect("SIG1", inst["Bottom"], v["Actuator"], line_type="pneumatic")

    fs.auto_layout(force_reposition=True)

    ctx = SvgContext("scratch_inst_leader.svg")
    fs.draw(ctx)
    svg_str = ctx.dwg.tostring()

    # Verify leader line path is rendered inside FIT-101 group
    assert 'id="FIT-101"' in svg_str
    assert f"M {inst.leader_line[0][0]}" in svg_str
