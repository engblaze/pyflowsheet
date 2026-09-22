from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.layout.crossover import CrossoverBridge, CrossoverDetector


def test_detect_orthogonal_crossover():
    # S1 is horizontal from (0, 50) to (100, 50)
    # S2 is vertical from (50, 0) to (50, 100)
    streams = {
        "S1": [(0.0, 50.0), (100.0, 50.0)],
        "S2": [(50.0, 0.0), (50.0, 100.0)],
    }
    detector = CrossoverDetector(bridge_radius=6.0)
    crossings = detector.find_crossings(streams)

    assert len(crossings) == 1
    crossing = crossings[0]
    assert crossing.intersection == (50.0, 50.0)
    assert crossing.base_stream == "S1"
    assert crossing.bridging_stream == "S2"
    assert crossing.style in ("arc", "gap")


def test_no_crossing_for_collinear_or_non_intersecting_streams():
    streams = {
        "S1": [(0.0, 50.0), (100.0, 50.0)],
        "S2": [(0.0, 80.0), (100.0, 80.0)],
        "S3": [(150.0, 0.0), (150.0, 100.0)],
    }
    detector = CrossoverDetector()
    crossings = detector.find_crossings(streams)
    assert len(crossings) == 0


def test_shared_endpoints_excluded():
    # S1 terminates at (50, 50) where S2 passes through
    streams = {
        "S1": [(0.0, 50.0), (50.0, 50.0)],
        "S2": [(50.0, 0.0), (50.0, 100.0)],
    }
    detector = CrossoverDetector()
    crossings = detector.find_crossings(streams)
    assert len(crossings) == 0


def test_generate_path_with_jumper_arcs():
    detector = CrossoverDetector(bridge_radius=5.0)
    # Vertical path crossing a horizontal stream at (50, 50)
    raw_path = [(50.0, 0.0), (50.0, 100.0)]
    bridges = [
        CrossoverBridge(
            base_stream="S1",
            bridging_stream="S2",
            intersection=(50.0, 50.0),
            direction="vertical",
            radius=5.0,
            style="arc",
        )
    ]
    commands = detector.build_svg_path_commands(raw_path, bridges)
    # Must contain M, L, and arc command A
    assert "M 50.0 0.0" in commands
    assert "A 5.0 5.0" in commands
    assert "L 50.0 100.0" in commands


def test_generate_path_with_gap_break():
    detector = CrossoverDetector(bridge_radius=5.0)
    raw_path = [(50.0, 0.0), (50.0, 100.0)]
    bridges = [
        CrossoverBridge(
            base_stream="S1",
            bridging_stream="S2",
            intersection=(50.0, 50.0),
            direction="vertical",
            radius=5.0,
            style="gap",
        )
    ]
    commands = detector.build_svg_path_commands(raw_path, bridges)
    assert "M 50.0 0.0" in commands
    assert "L 50.0 45.0" in commands
    assert "M 50.0 55.0" in commands
    assert "L 50.0 100.0" in commands


def test_generate_path_horizontal_bridge():
    detector = CrossoverDetector(bridge_radius=4.0)
    raw_path = [(0.0, 30.0), (100.0, 30.0)]
    bridges = [
        CrossoverBridge(
            base_stream="S2",
            bridging_stream="S1",
            intersection=(40.0, 30.0),
            direction="horizontal",
            radius=4.0,
            style="arc",
        )
    ]
    commands = detector.build_svg_path_commands(raw_path, bridges)
    assert "M 0.0 30.0" in commands
    assert "L 36.0 30.0" in commands
    assert "A 4.0 4.0 0 0 1 44.0 30.0" in commands
    assert "L 100.0 30.0" in commands


def test_empty_or_single_point_path():
    detector = CrossoverDetector()
    assert detector.build_svg_path_commands([], []) == ""
    assert detector.build_svg_path_commands([(10.0, 10.0)], []) == ""


def test_multiple_crossings_and_reversed_directions():
    detector = CrossoverDetector(bridge_radius=5.0)

    # Upward vertical segment crossing at y=70 and y=30
    raw_v_up = [(50.0, 100.0), (50.0, 0.0)]
    bridges_v = [
        CrossoverBridge(
            base_stream="S1",
            bridging_stream="S2",
            intersection=(50.0, 70.0),
            direction="vertical",
            radius=5.0,
        ),
        CrossoverBridge(
            base_stream="S3",
            bridging_stream="S2",
            intersection=(50.0, 30.0),
            direction="vertical",
            radius=5.0,
        ),
    ]
    cmd_v = detector.build_svg_path_commands(raw_v_up, bridges_v)
    assert "M 50.0 100.0" in cmd_v
    assert "L 50.0 75.0" in cmd_v
    assert "A 5.0 5.0 0 0 0 50.0 65.0" in cmd_v
    assert "L 50.0 35.0" in cmd_v
    assert "A 5.0 5.0 0 0 0 50.0 25.0" in cmd_v
    assert "L 50.0 0.0" in cmd_v

    # Leftward horizontal segment crossing at x=60
    raw_h_left = [(100.0, 40.0), (0.0, 40.0)]
    bridges_h = [
        CrossoverBridge(
            base_stream="S4",
            bridging_stream="S5",
            intersection=(60.0, 40.0),
            direction="horizontal",
            radius=5.0,
        )
    ]
    cmd_h = detector.build_svg_path_commands(raw_h_left, bridges_h)
    assert "M 100.0 40.0" in cmd_h
    assert "L 65.0 40.0" in cmd_h
    assert "A 5.0 5.0 0 0 0 55.0 40.0" in cmd_h
    assert "L 0.0 40.0" in cmd_h


def test_base_stream_unbroken_while_bridging_stream_jumps():
    streams = {
        "S_main": [(0.0, 50.0), (100.0, 50.0)],
        "S_cross": [(50.0, 0.0), (50.0, 100.0)],
    }
    detector = CrossoverDetector(bridge_radius=6.0)
    crossings = detector.find_crossings(streams)
    assert len(crossings) == 1

    # Base stream (horizontal) should remain flat without arc
    main_cmd = detector.build_svg_path_commands(streams["S_main"], crossings)
    assert "A" not in main_cmd
    assert main_cmd == "M 0.0 50.0 L 100.0 50.0"

    # Bridging stream (vertical) should contain the jumper arc
    cross_cmd = detector.build_svg_path_commands(streams["S_cross"], crossings)
    assert "A 6.0 6.0" in cross_cmd


def test_svg_context_raw_path(tmp_path):
    output_path = tmp_path / "test_raw_path.svg"
    ctx = SvgContext(str(output_path))
    ctx.raw_path(
        "M 0.0 0.0 L 50.0 0.0",
        fillColor=(255, 0, 0, 255),
        lineColor=(0, 0, 255, 255),
        lineSize=2.5,
        dashArray="4,4",
        endMarker=True,
    )
    svg_str = ctx.render(saveFile=True)
    assert output_path.exists()
    assert 'd="M 0.0 0.0 L 50.0 0.0"' in svg_str
    assert 'stroke="rgb(0, 0, 255)"' in svg_str
    assert 'stroke-dasharray="4,4"' in svg_str
    assert "marker-end" in svg_str


def test_arc_endpoints_clamped_near_segment_corners():
    detector = CrossoverDetector(bridge_radius=6.0)

    # 1. Vertical downward segment: y from 10.0 to 30.0
    # Crossing near start corner at iy = 12.0 (< 10.0 + 6.0)
    raw_v = [(50.0, 10.0), (50.0, 30.0)]
    bridges_v_start = [
        CrossoverBridge(
            base_stream="S1",
            bridging_stream="S2",
            intersection=(50.0, 12.0),
            direction="vertical",
            radius=6.0,
            style="arc",
        )
    ]
    cmd_v_start = detector.build_svg_path_commands(raw_v, bridges_v_start)
    # start_y clamped to 10.0 instead of 6.0
    assert "L 50.0 10.0" in cmd_v_start
    assert "A 6.0 6.0 0 0 1 50.0 18.0" in cmd_v_start

    # Crossing near end corner at iy = 28.0 (> 30.0 - 6.0)
    bridges_v_end = [
        CrossoverBridge(
            base_stream="S1",
            bridging_stream="S2",
            intersection=(50.0, 28.0),
            direction="vertical",
            radius=6.0,
            style="arc",
        )
    ]
    cmd_v_end = detector.build_svg_path_commands(raw_v, bridges_v_end)
    # end_y clamped to 30.0 instead of 34.0
    assert "A 6.0 6.0 0 0 1 50.0 30.0" in cmd_v_end

    # 2. Horizontal rightward segment: x from 10.0 to 30.0
    raw_h = [(10.0, 50.0), (30.0, 50.0)]
    bridges_h_start = [
        CrossoverBridge(
            base_stream="S1",
            bridging_stream="S2",
            intersection=(12.0, 50.0),
            direction="horizontal",
            radius=6.0,
            style="arc",
        )
    ]
    cmd_h_start = detector.build_svg_path_commands(raw_h, bridges_h_start)
    # start_x clamped to 10.0 instead of 6.0
    assert "L 10.0 50.0" in cmd_h_start
    assert "A 6.0 6.0 0 0 1 18.0 50.0" in cmd_h_start

    bridges_h_end = [
        CrossoverBridge(
            base_stream="S1",
            bridging_stream="S2",
            intersection=(28.0, 50.0),
            direction="horizontal",
            radius=6.0,
            style="arc",
        )
    ]
    cmd_h_end = detector.build_svg_path_commands(raw_h, bridges_h_end)
    # end_x clamped to 30.0 instead of 34.0
    assert "A 6.0 6.0 0 0 1 30.0 50.0" in cmd_h_end
