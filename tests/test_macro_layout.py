from pyflowsheet.layout.macro import FlowsheetGraph, MacroLayoutSolver
from pyflowsheet.schema.models import AlignSchema, LayoutHintsSchema, RelativeToSchema


def test_macro_solver_basic_bay_positioning():
    units = [
        {"id": "FEED", "size": [40, 40]},
        {"id": "MIXER", "size": [60, 80]},
        {"id": "PRODUCT", "size": [40, 40]},
    ]
    streams = [
        ("S01", "FEED", "MIXER"),
        ("S02", "MIXER", "PRODUCT"),
    ]
    solver = MacroLayoutSolver(
        units=units,
        streams=streams,
        origin=(50.0, 100.0),
        bay_width=160.0,
        bay_height=120.0,
    )
    positions = solver.solve()

    assert positions["FEED"][0] < positions["MIXER"][0] < positions["PRODUCT"][0]
    assert positions["FEED"][0] == 50.0
    assert positions["MIXER"][0] == 210.0
    assert positions["PRODUCT"][0] == 370.0


def test_macro_solver_relative_to_and_align_hints():
    units = [
        {"id": "V-100", "size": [50, 50], "position": [100.0, 100.0]},
        {
            "id": "P-100",
            "size": [40, 40],
            "layout_hints": {
                "relative_to": {"target": "V-100", "direction": "below", "offset": 50.0},
                "align": {"with": "V-100", "axis": "vertical"},
            },
        },
    ]
    streams = [("S01", "V-100", "P-100")]
    solver = MacroLayoutSolver(units=units, streams=streams)
    positions = solver.solve()

    assert positions["V-100"] == (100.0, 100.0)
    # P-100 aligned vertically with V-100 (same X) and below V-100 (Y = 100 + 50 + 50 = 200)
    assert positions["P-100"][0] == 100.0
    assert positions["P-100"][1] >= 150.0


def test_macro_solver_fixed_position_precedence():
    units = [
        {"id": "TK-1", "size": [40, 40], "position": [300.0, 400.0]},
        {"id": "TK-2", "size": [40, 40]},
    ]
    streams = [("S01", "TK-1", "TK-2")]
    solver = MacroLayoutSolver(units=units, streams=streams)
    positions = solver.solve()

    # Manual fixed coordinate is preserved
    assert positions["TK-1"] == (300.0, 400.0)


def test_macro_solver_recycle_corridors():
    units = [
        {"id": "FEED", "size": [40, 40]},
        {"id": "MIXER", "size": [60, 80]},
        {"id": "REACTOR", "size": [60, 80]},
        {"id": "SEPARATOR", "size": [60, 80]},
        {"id": "PRODUCT", "size": [40, 40]},
    ]
    streams = [
        ("S01", "FEED", "MIXER"),
        ("S02", "MIXER", "REACTOR"),
        ("S03", "REACTOR", "SEPARATOR"),
        ("S04", "SEPARATOR", "PRODUCT"),
        ("S05", "SEPARATOR", "MIXER"),
    ]
    solver = MacroLayoutSolver(units=units, streams=streams)
    positions = solver.solve()

    assert len(positions) == 5
    assert "S05" in solver.recycle_corridors
    assert solver.recycle_corridors["S05"] in {"top", "bottom"}
    assert solver.get_recycle_corridors() == solver.recycle_corridors


def test_macro_solver_flow_direction_down():
    units = [
        {"id": "FEED", "size": [40, 40]},
        {"id": "COLUMN", "size": [60, 120]},
        {"id": "REBOILER", "size": [40, 40]},
    ]
    streams = [
        ("S01", "FEED", "COLUMN"),
        ("S02", "COLUMN", "REBOILER"),
    ]
    solver = MacroLayoutSolver(
        units=units,
        streams=streams,
        origin=(100.0, 50.0),
        bay_width=150.0,
        bay_height=200.0,
        flow_direction="down",
    )
    positions = solver.solve()

    assert positions["FEED"][1] < positions["COLUMN"][1] < positions["REBOILER"][1]
    assert positions["FEED"][1] == 50.0
    assert positions["COLUMN"][1] == 250.0
    assert positions["REBOILER"][1] == 450.0


def test_macro_solver_relative_directions_and_pydantic_hints():
    units = [
        {"id": "BASE", "size": [100, 100], "position": [200.0, 200.0]},
        {
            "id": "U_RIGHT",
            "size": [50, 50],
            "layout_hints": LayoutHintsSchema(
                relative_to=RelativeToSchema(target="BASE", direction="right", offset=20.0),
                align=AlignSchema(axis="horizontal", **{"with": "BASE"}),
            ),
        },
        {
            "id": "U_LEFT",
            "size": [50, 50],
            "layout_hints": LayoutHintsSchema(
                relative_to=RelativeToSchema(target="BASE", direction="left", offset=30.0),
            ),
        },
        {
            "id": "U_ABOVE",
            "size": [50, 50],
            "layout_hints": LayoutHintsSchema(
                relative_to=RelativeToSchema(target="BASE", direction="above", offset=40.0),
            ),
        },
    ]
    streams = []
    solver = MacroLayoutSolver(units=units, streams=streams)
    positions = solver.solve()

    # BASE at 200, 200 (size 100x100)
    # U_RIGHT: x = 200 + 100 + 20 = 320, aligned horizontal with BASE -> y = 200
    assert positions["U_RIGHT"] == (320.0, 200.0)
    # U_LEFT: x = 200 - 50 - 30 = 120, y = BASE.y = 200
    assert positions["U_LEFT"] == (120.0, 200.0)
    # U_ABOVE: x = BASE.x = 200, y = 200 - 50 - 40 = 110
    assert positions["U_ABOVE"] == (200.0, 110.0)


def test_flowsheet_graph_extract_dag_alias():
    units = ["A", "B", "C"]
    streams = [("S1", "A", "B"), ("S2", "B", "C"), ("S3", "C", "A")]
    graph = FlowsheetGraph(units, streams)

    dag_edges = graph.extract_dag()
    assert ("S1", "A", "B") in dag_edges
    assert ("S2", "B", "C") in dag_edges
    assert ("S3", "C", "A") not in dag_edges
    assert "S3" in graph.recycle_streams


def test_macro_solver_explicit_none_size_and_offset():
    units = [
        {"id": "TARGET", "position": [100.0, 100.0], "size": None},
        {
            "id": "DEP",
            "size": None,
            "layout_hints": {
                "relative_to": {"target": "TARGET", "direction": "right", "offset": None}
            },
        },
    ]
    solver = MacroLayoutSolver(units=units, streams=[])
    positions = solver.solve()

    assert positions["TARGET"] == (100.0, 100.0)
    # Default target size (40, 40) + default offset 60.0 -> 100 + 40 + 60 = 200.0
    assert positions["DEP"] == (200.0, 100.0)


def test_inline_train_compaction():
    # Chain: Feed -> P1 -> CKV1 -> FCV1 -> Tank
    units = [
        {"id": "Feed", "size": (40, 40), "position": (0, 0), "type": "StreamFlag"},
        {"id": "P1", "size": (30, 30), "position": (0, 0), "type": "Pump"},
        {"id": "CKV1", "size": (18, 10), "position": (0, 0), "type": "CheckValve"},
        {"id": "FCV1", "size": (24, 16), "position": (0, 0), "type": "ControlValve"},
        {"id": "Tank", "size": (60, 90), "position": (0, 0), "type": "Vessel"},
    ]
    streams = [
        ("S1", "Feed", "P1"),
        ("S2", "P1", "CKV1"),
        ("S3", "CKV1", "FCV1"),
        ("S4", "FCV1", "Tank"),
    ]
    solver = MacroLayoutSolver(units=units, streams=streams, origin=(50, 100), bay_width=160.0)
    positions = solver.solve()

    # The entire span from Feed to Tank should be compacted (< 350px), not 4 full 160px bays (640px)
    feed_x = positions["Feed"][0]
    tank_x = positions["Tank"][0]
    assert (tank_x - feed_x) <= 350.0


def test_full_recycle_chain_placed_in_reverse_order():
    # Loop: Mixer -> NF -> PCV -> CKV -> Mixer
    units = [
        {"id": "Mixer", "size": (60, 90), "position": (0, 0), "type": "Vessel"},
        {"id": "NF", "size": (60, 40), "position": (0, 0), "type": "MembraneModule"},
        {"id": "PCV", "size": (24, 16), "position": (0, 0), "type": "ControlValve"},
        {"id": "CKV", "size": (18, 10), "position": (0, 0), "type": "CheckValve"},
    ]
    streams = [
        ("S1", "Mixer", "NF"),
        ("S2", "NF", "PCV"),
        ("S3", "PCV", "CKV"),
        ("S4", "CKV", "Mixer"),
    ]
    solver = MacroLayoutSolver(units=units, streams=streams, origin=(50, 100), bay_width=160.0)
    positions = solver.solve()

    # PCV and CKV should be below the process line and flow right-to-left towards Mixer
    assert positions["PCV"][1] > positions["NF"][1]
    assert positions["CKV"][0] < positions["PCV"][0]


def test_port_elevation_alignment():
    # Wastewater (size 40x40, port at (1.0, 0.5) -> y=20)
    # P-101 (size 30x30, port at (0.0, 0.5) -> y=15)
    units = [
        {
            "id": "Wastewater",
            "size": (40, 40),
            "position": (0, 0),
            "type": "StreamFlag",
            "ports": {"Out": (1.0, 0.5)},
        },
        {
            "id": "P-101",
            "size": (30, 30),
            "position": (0, 0),
            "type": "Pump",
            "ports": {"In": (0.0, 0.5)},
        },
    ]
    streams = [("S1", "Wastewater", "P-101")]
    solver = MacroLayoutSolver(units=units, streams=streams, origin=(50, 100))
    positions = solver.solve()

    # The Y-coordinate of P-101 should be adjusted so its In port matches Wastewater's Out port:
    # Wastewater Out port Y = 100 + 20 = 120
    # P-101 In port Y = P_y + 15 -> P_y must be 105
    assert positions["P-101"][1] == 105.0


def test_port_elevation_alignment_chained():
    units = [
        {
            "id": "A",
            "size": (40, 40),
            "position": (0, 0),
            "type": "StreamFlag",
            "ports": {"Out": (1.0, 0.5)},
        },
        {
            "id": "B",
            "size": (30, 30),
            "position": (0, 0),
            "type": "Pump",
            "ports": {"In": (0.0, 0.5), "Out": (1.0, 0.5)},
        },
        {
            "id": "C",
            "size": (50, 50),
            "position": (0, 0),
            "type": "Vessel",
            "ports": {"In": (0.0, 0.5)},
        },
    ]
    streams = [("S1", "A", "B"), ("S2", "B", "C")]
    solver = MacroLayoutSolver(units=units, streams=streams, origin=(50, 100))
    positions = solver.solve()

    assert positions["A"][1] == 100.0
    assert positions["B"][1] == 105.0
    assert positions["C"][1] == 95.0


def test_port_elevation_alignment_multiport_conflict():
    units = [
        {
            "id": "Feed",
            "size": (40, 40),
            "position": (0, 0),
            "type": "StreamFlag",
            "ports": {"Out": (1.0, 0.5)},
        },
        {
            "id": "Additive",
            "size": (40, 40),
            "position": (0, 0),
            "type": "StreamFlag",
            "ports": {"Out": (1.0, 0.5)},
        },
        {
            "id": "Mixer",
            "size": (60, 60),
            "position": (0, 0),
            "type": "Mixer",
            "ports": {
                "In1": {"rel_pos": (0.0, 0.5), "normal": (-1.0, 0.0), "intent": "in"},
                "In2": {"rel_pos": (0.0, 0.8), "normal": (-1.0, 0.0), "intent": "in"},
            },
        },
    ]
    streams = [
        ("S1", "Feed", "Mixer", "Out", "In1"),
        ("S2", "Additive", "Mixer", "Out", "In2"),
    ]
    solver = MacroLayoutSolver(units=units, streams=streams, origin=(50, 100))
    positions = solver.solve()

    assert positions["Mixer"][1] == 90.0
