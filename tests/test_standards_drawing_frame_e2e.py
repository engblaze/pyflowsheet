import html
import xml.etree.ElementTree as ET
from pathlib import Path

from pyflowsheet.cli import main
from pyflowsheet.core import Flowsheet


def test_water_treatment_pid_yaml_renders_complete_frame(tmp_path):
    yaml_path = Path("examples/water_treatment_pid.yaml")
    assert yaml_path.exists()

    out_svg = tmp_path / "water_treatment_pid.svg"
    ret = main(["render", str(yaml_path), "-o", str(out_svg)])
    assert ret == 0

    svg_content = out_svg.read_text(encoding="utf-8")
    for group_id in [
        "drawing_border",
        "revision_block",
        "legend",
        "title_block",
        "drawing_notes",
    ]:
        assert f'id="{group_id}"' in svg_content

    # Unescape XML entities (e.g. &amp; -> &) for textual metadata assertions
    unescaped_svg = html.unescape(svg_content)
    assert ("DWG-PFD-WT-002" in unescaped_svg or "PFAS-PFD-WT-002" in unescaped_svg)
    assert "ADVANCED WATER SYSTEMS & RESOURCE RECOVERY" in unescaped_svg
    assert "1A2B3" in unescaped_svg
    assert "E. Vance" in unescaped_svg
    assert ("H. Green" in unescaped_svg or "K. Azevedo" in unescaped_svg)

    # XML validation & viewBox / bounds
    root = ET.fromstring(svg_content)
    assert root.tag.endswith("svg")
    assert root.attrib.get("viewBox") == "-75.0,-55.0,1370.0,910.0"

    # Verify group elements in XML tree
    group_ids = {el.attrib.get("id") for el in root.iter() if el.tag.endswith("g")}
    for gid in [
        "drawing_border",
        "revision_block",
        "legend",
        "title_block",
        "drawing_notes",
    ]:
        assert gid in group_ids


def test_water_treatment_pid_flowsheet_object_model():
    yaml_path = Path("examples/water_treatment_pid.yaml")
    flowsheet = Flowsheet.from_yaml(yaml_path)
    assert flowsheet.drawing_frame is not None
    assert flowsheet.drawing_frame.enabled is True
    assert flowsheet.drawing_frame.sheet_size == "D"
    assert flowsheet.drawing_frame.title_block is not None
    assert flowsheet.drawing_frame.legend is not None
    assert flowsheet.drawing_frame.revision_block is not None
    assert flowsheet.drawing_frame.notes_block is not None
    assert flowsheet.drawing_frame.border is not None
