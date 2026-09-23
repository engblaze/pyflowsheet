from pyflowsheet.layout.macro import FlowsheetGraph


def test_linear_flowsheet_stages():
    # S01: FEED -> MIXER
    # S02: MIXER -> REACTOR
    # S03: REACTOR -> PRODUCT
    units = ["FEED", "MIXER", "REACTOR", "PRODUCT"]
    streams = [
        ("S01", "FEED", "MIXER"),
        ("S02", "MIXER", "REACTOR"),
        ("S03", "REACTOR", "PRODUCT"),
    ]
    graph = FlowsheetGraph(units, streams)
    stages = graph.compute_stages()

    assert stages["FEED"] == 0
    assert stages["MIXER"] == 1
    assert stages["REACTOR"] == 2
    assert stages["PRODUCT"] == 3
    assert len(graph.recycle_streams) == 0


def test_recycle_loop_detection():
    # S01: FEED -> MIXER
    # S02: MIXER -> REACTOR
    # S03: REACTOR -> SEPARATOR
    # S04: SEPARATOR -> PRODUCT
    # S05: SEPARATOR -> MIXER (Recycle!)
    units = ["FEED", "MIXER", "REACTOR", "SEPARATOR", "PRODUCT"]
    streams = [
        ("S01", "FEED", "MIXER"),
        ("S02", "MIXER", "REACTOR"),
        ("S03", "REACTOR", "SEPARATOR"),
        ("S04", "SEPARATOR", "PRODUCT"),
        ("S05", "SEPARATOR", "MIXER"),
    ]
    graph = FlowsheetGraph(units, streams)
    stages = graph.compute_stages()

    assert "S05" in graph.recycle_streams
    assert stages["FEED"] == 0
    assert stages["MIXER"] == 1
    assert stages["REACTOR"] == 2
    assert stages["SEPARATOR"] == 3
    assert stages["PRODUCT"] == 4


def test_branching_and_merging_stages():
    # FEED -> SPLITTER -> (BRANCH1, BRANCH2) -> COMBINER -> PRODUCT
    units = ["FEED", "SPLITTER", "B1", "B2", "COMBINER", "PRODUCT"]
    streams = [
        ("S01", "FEED", "SPLITTER"),
        ("S02", "SPLITTER", "B1"),
        ("S03", "SPLITTER", "B2"),
        ("S04", "B1", "COMBINER"),
        ("S05", "B2", "COMBINER"),
        ("S06", "COMBINER", "PRODUCT"),
    ]
    graph = FlowsheetGraph(units, streams)
    stages = graph.compute_stages()

    assert stages["FEED"] == 0
    assert stages["SPLITTER"] == 1
    assert stages["B1"] == 2
    assert stages["B2"] == 2
    assert stages["COMBINER"] == 3
    assert stages["PRODUCT"] == 4


def test_layout_package_export():
    from pyflowsheet.layout import FlowsheetGraph as ExportedGraph

    assert ExportedGraph is FlowsheetGraph


def test_manual_stage_hints():
    units = ["U1", "U2", "U3"]
    streams = [("S01", "U1", "U2"), ("S02", "U2", "U3")]
    graph = FlowsheetGraph(units, streams)

    # Force U2 to stage 5
    stages = graph.compute_stages(manual_stage_hints={"U2": 5})
    assert stages["U1"] == 0
    assert stages["U2"] == 5
    assert stages["U3"] == 6


def test_disconnected_units_and_invalid_streams():
    units = ["U1", "U2", "ISOLATED"]
    streams = [
        ("S01", "U1", "U2"),
        ("S_INVALID_1", "U1", "UNKNOWN"),
        ("S_INVALID_2", "UNKNOWN", "U2"),
    ]
    graph = FlowsheetGraph(units, streams)
    stages = graph.compute_stages()

    assert stages["U1"] == 0
    assert stages["U2"] == 1
    assert stages["ISOLATED"] == 0
    assert len(graph.recycle_streams) == 0
    assert len(graph.forward_edges) == 1


def test_flowsheet_graph_recycle_chains():
    units = ["FEED", "MIXER", "REACTOR", "SEPARATOR", "PUMP", "PRODUCT"]
    unit_types = {
        "FEED": "Feed",
        "MIXER": "Mixer",
        "REACTOR": "Vessel",
        "SEPARATOR": "DistillationColumn",
        "PUMP": "Pump",
        "PRODUCT": "Product",
    }
    streams = [
        ("S01", "FEED", "MIXER"),
        ("S02", "MIXER", "REACTOR"),
        ("S03", "REACTOR", "SEPARATOR"),
        ("S04", "SEPARATOR", "PRODUCT"),
        ("S05", "SEPARATOR", "PUMP"),
        ("S06", "PUMP", "MIXER"),
    ]
    graph = FlowsheetGraph(units, streams, unit_types=unit_types)

    assert "PUMP" in graph.recycle_units
    assert "FEED" not in graph.recycle_units
    assert "MIXER" not in graph.recycle_units
    assert "REACTOR" not in graph.recycle_units
    assert "SEPARATOR" not in graph.recycle_units
    assert "PRODUCT" not in graph.recycle_units

    assert "S06" in graph.recycle_streams
    assert "S05" in graph.recycle_streams

    assert len(graph.recycle_chains) == 1
    chain = graph.recycle_chains[0]
    assert chain["source"] == "SEPARATOR"
    assert chain["target"] == "MIXER"
    assert chain["units"] == ["PUMP"]
    assert "S06" in chain["streams"]
    assert "S05" in chain["streams"]

    # Also verify direct primary-to-primary recycle
    units_direct = ["FEED", "MIXER", "REACTOR", "SEPARATOR", "PRODUCT"]
    streams_direct = [
        ("S01", "FEED", "MIXER"),
        ("S02", "MIXER", "REACTOR"),
        ("S03", "REACTOR", "SEPARATOR"),
        ("S04", "SEPARATOR", "PRODUCT"),
        ("S05", "SEPARATOR", "MIXER"),
    ]
    graph_direct = FlowsheetGraph(units_direct, streams_direct)
    assert len(graph_direct.recycle_units) == 0
    assert "S05" in graph_direct.recycle_streams
    assert len(graph_direct.recycle_chains) == 1
    chain_direct = graph_direct.recycle_chains[0]
    assert chain_direct["source"] == "SEPARATOR"
    assert chain_direct["target"] == "MIXER"
    assert chain_direct["units"] == []
    assert chain_direct["streams"] == ["S05"]
