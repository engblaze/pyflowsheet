from pyflowsheet.layout.inline import InlineSequencer


def test_inline_sequencing_horizontal_segment():
    # Stream route from (0, 100) to (300, 100)
    route = [(0.0, 100.0), (300.0, 100.0)]
    line_sequence = [
        "FEED:Out",
        "P-101 (Influent Pump)",
        "CKV-101 (Check Valve)",
        "FCV-101 (Control Valve)",
        "MIXER:In",
    ]
    component_sizes = {
        "P-101": (30.0, 30.0),
        "CKV-101": (20.0, 15.0),
        "FCV-101": (20.0, 20.0),
    }
    sequencer = InlineSequencer()
    placements = sequencer.sequence(route, line_sequence, component_sizes)

    assert "P-101" in placements
    assert "CKV-101" in placements
    assert "FCV-101" in placements

    # Check strict left-to-right order
    assert (
        placements["P-101"].center[0]
        < placements["CKV-101"].center[0]
        < placements["FCV-101"].center[0]
    )
    assert placements["P-101"].center[1] == 100.0
    assert placements["P-101"].orientation == "horizontal"
    # Verify knockout mask covers component size with padding
    assert placements["P-101"].knockout_box.width >= 30.0
    assert placements["P-101"].knockout_box.height >= 30.0


def test_inline_sequencing_vertical_segment():
    # Stream route from (100, 0) to (100, 200)
    route = [(100.0, 0.0), (100.0, 200.0)]
    line_sequence = ["TK-1:Out", "V-101", "TK-2:In"]
    component_sizes = {"V-101": (20.0, 20.0)}

    sequencer = InlineSequencer()
    placements = sequencer.sequence(route, line_sequence, component_sizes)

    assert placements["V-101"].center[0] == 100.0
    assert 0.0 < placements["V-101"].center[1] < 200.0
    assert placements["V-101"].orientation == "vertical"


def test_inline_sequencing_multisegment_longest_segment():
    # Route: short horizontal (0,0)->(20,0), long vertical (20,0)->(20,200),
    # short horizontal (20,200)->(50,200)
    route = [(0.0, 0.0), (20.0, 0.0), (20.0, 200.0), (50.0, 200.0)]
    line_sequence = ["P1:Out", "V-101", "P2:In"]
    component_sizes = {"V-101": (10.0, 10.0)}

    sequencer = InlineSequencer(knockout_padding=2.0)
    placements = sequencer.sequence(route, line_sequence, component_sizes)

    assert "V-101" in placements
    p = placements["V-101"]
    assert p.orientation == "vertical"
    assert p.center[0] == 20.0
    assert p.center[1] == 100.0  # midpoint of (20,0) to (20,200)
    assert p.knockout_box.width == 10.0 + 2 * 2.0
    assert p.knockout_box.height == 10.0 + 2 * 2.0


def test_inline_sequencing_reversed_flow_direction():
    # Route flowing right-to-left: (300, 50) -> (0, 50)
    route = [(300.0, 50.0), (0.0, 50.0)]
    line_sequence = ["UnitA:Out", "V-1", "V-2", "UnitB:In"]
    component_sizes = {"V-1": (20.0, 20.0), "V-2": (20.0, 20.0)}

    sequencer = InlineSequencer()
    placements = sequencer.sequence(route, line_sequence, component_sizes)

    # V-1 should appear before V-2 along the stream direction (higher X to lower X)
    assert placements["V-1"].center[0] > placements["V-2"].center[0]
    assert placements["V-1"].center[1] == 50.0
    assert placements["V-2"].center[1] == 50.0


def test_inline_sequencing_empty_and_invalid_inputs():
    sequencer = InlineSequencer()
    # Route too short
    assert sequencer.sequence([(0.0, 0.0)], ["V-1"], {"V-1": (20.0, 20.0)}) == {}
    # Empty line sequence
    assert sequencer.sequence([(0.0, 0.0), (100.0, 0.0)], [], {"V-1": (20.0, 20.0)}) == {}
    # Line sequence contains only endpoints
    assert (
        sequencer.sequence(
            [(0.0, 0.0), (100.0, 0.0)],
            ["TK1:Out", "TK2:In"],
            {"V-1": (20.0, 20.0)},
        )
        == {}
    )
    # Inline component not in component_sizes
    assert (
        sequencer.sequence(
            [(0.0, 0.0), (100.0, 0.0)],
            ["TK1:Out", "V-999", "TK2:In"],
            {"V-1": (20.0, 20.0)},
        )
        == {}
    )


def test_inline_sequencing_vertical_non_square_knockout():
    sequencer = InlineSequencer(knockout_padding=2.0)
    sizes = {"VALVE": (30.0, 10.0)}

    # Vertical pipe
    v_placements = sequencer.sequence(
        route=[(50.0, 0.0), (50.0, 100.0)],
        line_sequence=["U1:Out", "VALVE", "U2:In"],
        component_sizes=sizes,
    )
    assert "VALVE" in v_placements
    v_box = v_placements["VALVE"].knockout_box
    # Swapped: width uses size[1] (10 + 2*2 = 14), height uses size[0] (30 + 2*2 = 34)
    assert v_box.width == 14.0
    assert v_box.height == 34.0

    # Horizontal pipe for comparison
    h_placements = sequencer.sequence(
        route=[(0.0, 50.0), (100.0, 50.0)],
        line_sequence=["U1:Out", "VALVE", "U2:In"],
        component_sizes=sizes,
    )
    assert "VALVE" in h_placements
    h_box = h_placements["VALVE"].knockout_box
    # Standard: width uses size[0] (30 + 4 = 34), height uses size[1] (10 + 4 = 14)
    assert h_box.width == 34.0
    assert h_box.height == 14.0
