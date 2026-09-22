import xml.etree.ElementTree as ET
from pyflowsheet import (
    Flowsheet,
    BlackBox,
    Distillation,
    HeatExchanger,
    Mixer,
    Splitter,
    StreamFlag,
    Vessel,
    Port,
    SvgContext,
    VerticalLabelAlignment,
    HorizontalLabelAlignment,
)
from pyflowsheet.internals import Tubes, RandomPacking


def test_block_flow_diagram_svg_snapshot(tmp_path):
    pfd = Flowsheet("V100", "Block Flow Diagram", "Demo Flowsheet for showing block-flow diagram style")

    sp1 = BlackBox("Pretreatment", "Removal of catalyst poisons", position=(100, 180), size=(80, 60))
    sp2 = BlackBox("Reaction", "Catalytic reaction", position=(240, 180), size=(80, 60))
    feed = StreamFlag("Feed", "", position=(0, 190))
    product = StreamFlag("Product", "", position=(400, 190))

    pfd.addUnits([feed, product, sp1, sp2])
    pfd.connect("S01", feed["Out"], sp1["In"])
    pfd.connect("S02", sp1["Out"], sp2["In"])
    pfd.connect("S03", sp2["Out"], product["In"])

    out_file = str(tmp_path / "block_flow.svg")
    ctx = SvgContext(out_file)
    pfd.draw(ctx)
    svg_str = ctx.render(saveFile=True)

    # Validate well-formed XML
    root = ET.fromstring(svg_str)
    assert root.tag.endswith("svg")

    # Verify group IDs exist
    g_ids = [elem.attrib.get("id") for elem in root.iter() if "id" in elem.attrib]
    assert "Pretreatment" in g_ids
    assert "Reaction" in g_ids
    assert "S01" in g_ids
    assert "S02" in g_ids


def test_externalized_column_svg_snapshot(tmp_path):
    pfd = Flowsheet("V100-DS10", "Complex Distillation", "Demo Flowsheet")

    feed = StreamFlag("Feed", "Feed", position=(0, 250))
    hx1 = HeatExchanger("Preheater", "Pre-Heater", position=(160, 250))
    twr1 = Distillation(
        "Tower",
        "Distillation Tower",
        hasCondenser=False,
        hasReboiler=False,
        position=(300, 120),
        size=(40, 300),
        internals=[RandomPacking(start=0, end=0.4)],
    )

    pfd.addUnits([feed, hx1, twr1])
    pfd.connect("S01", feed["Out"], hx1["TIn"])
    pfd.connect("S02", hx1["TOut"], twr1["Feed"])

    out_file = str(tmp_path / "column.svg")
    ctx = SvgContext(out_file)
    pfd.draw(ctx)
    svg_str = ctx.render(saveFile=True)

    root = ET.fromstring(svg_str)
    assert root.tag.endswith("svg")
    g_ids = [elem.attrib.get("id") for elem in root.iter() if "id" in elem.attrib]
    assert "Tower" in g_ids
    assert "Preheater" in g_ids
    assert "S01" in g_ids
