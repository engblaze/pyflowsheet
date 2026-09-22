from pyflowsheet import Flowsheet
from pyflowsheet.backends import SvgContext
from pyflowsheet.unitoperations import (
    DistillationColumn,
    HeatExchanger,
    Mixer,
    Pump,
    Splitter,
    StreamFlag,
    Vessel,
)


def test_e2e_recycle_flowsheet_auto_layout(tmp_path):
    fs = Flowsheet("RECYCLE_E2E", "Recycle Plant")
    feed = fs.unit(StreamFlag("Feed", "Feed", role="input"))
    vessel = fs.unit(Vessel("Reactor", "Reactor"))
    pump = fs.unit(Pump("Pump", "Pump"))
    column = fs.unit(DistillationColumn("Dist", "Column"))
    hx = fs.unit(HeatExchanger("Condenser", "Condenser"))
    prod = fs.unit(StreamFlag("Product", "Product", role="output"))

    fs.connect("S01", feed["Out"], vessel["In"])
    fs.connect("S02", vessel["Out"], pump["In"])
    fs.connect("S03", pump["Out"], column["Feed"])
    fs.connect("S04", column["Distillate"], hx["InTube"])
    fs.connect("S05", hx["OutTube"], prod["In"])
    # Recycle loop: bottom of column back to Reactor
    fs.connect("S_REC", column["Bottoms"], vessel["In2"])

    fs.auto_layout()

    out_file = tmp_path / "recycle_e2e.svg"
    ctx = SvgContext(str(out_file))
    fs.draw(ctx)
    ctx.dwg.save()

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "S_REC" in content
    assert "Reactor" in content
    assert "Dist" in content


def test_e2e_split_recombine_plant_auto_layout(tmp_path):
    fs = Flowsheet("SPLIT_E2E", "Split Recombine Plant")
    feed = fs.unit(StreamFlag("Feed", "Feed"))
    splitter = fs.unit(Splitter("SP1", "Splitter"))
    pump1 = fs.unit(Pump("P1", "Train 1 Pump"))
    pump2 = fs.unit(Pump("P2", "Train 2 Pump"))
    mixer = fs.unit(Mixer("MX1", "Mixer"))
    product = fs.unit(StreamFlag("Product", "Product"))

    fs.connect("S01", feed["Out"], splitter["In"])
    fs.connect("S02", splitter["Out1"], pump1["In"])
    fs.connect("S03", splitter["Out2"], pump2["In"])
    fs.connect("S04", pump1["Out"], mixer["In1"])
    fs.connect("S05", pump2["Out"], mixer["In2"])
    fs.connect("S06", mixer["Out"], product["In"])

    fs.auto_layout()

    # Stages should advance from feed to product
    assert feed.position[0] < splitter.position[0]
    assert splitter.position[0] < pump1.position[0]
    assert splitter.position[0] < pump2.position[0]
    assert pump1.position[0] < mixer.position[0]
    assert mixer.position[0] < product.position[0]

    out_file = tmp_path / "split_e2e.svg"
    ctx = SvgContext(str(out_file))
    fs.draw(ctx)
    ctx.dwg.save()

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "S01" in content
    assert "S06" in content
    assert "P1" in content
    assert "P2" in content
    assert "MX1" in content


def test_e2e_yaml_roundtrip_auto_layout(tmp_path):
    yaml_text = """
schema_version: "1.0"
metadata:
  id: "E2E_YAML_PLANT"
  name: "End to End YAML Plant"
components:
  stream_flags:
    - id: "Feed"
      name: "Feed"
      type: "StreamFlag"
    - id: "Prod"
      name: "Product"
      type: "StreamFlag"
  equipment:
    - id: "Reactor"
      name: "CSTR Reactor"
      type: "Vessel"
    - id: "HX"
      name: "Cooler"
      type: "HeatExchanger"
streams:
  - id: "STR01"
    from:
      unit: "Feed"
      port: "Out"
    to:
      unit: "Reactor"
      port: "In"
  - id: "STR02"
    from:
      unit: "Reactor"
      port: "Out"
    to:
      unit: "HX"
      port: "TIn"
  - id: "STR03"
    from:
      unit: "HX"
      port: "TOut"
    to:
      unit: "Prod"
      port: "In"
"""
    fs = Flowsheet.from_yaml(yaml_text)
    fs.auto_layout()

    out_file = tmp_path / "yaml_e2e.svg"
    ctx = SvgContext(str(out_file))
    fs.draw(ctx)
    ctx.dwg.save()

    assert out_file.exists()
    svg = out_file.read_text(encoding="utf-8")
    assert "<svg" in svg
    assert "Reactor" in svg
    assert "HX" in svg
    assert "STR01" in svg
    assert "STR02" in svg
    assert "STR03" in svg
