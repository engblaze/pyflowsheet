from pyflowsheet import Flowsheet
from pyflowsheet.backends import SvgContext


def test_flowsheet_enable_drawing_frame(tmp_path):
    pfd = Flowsheet(id="WT_TEST", name="Water Treatment")
    pfd.enable_drawing_frame(
        title="WATER PURIFICATION",
        drawing_number="DWG-001",
        revision="B",
        sheet_size="D",
        notes=["TEST NOTE"],
    )
    assert pfd.drawing_frame is not None
    assert pfd.drawing_frame.enabled is True

    out_svg = tmp_path / "flowsheet_frame.svg"
    ctx = SvgContext(str(out_svg))
    pfd.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_border"' in content
    assert 'id="title_block"' in content
    assert "DWG-001" in content
    assert ctx.bounds == [-75.0, -55.0, 1295.0, 855.0]


def test_flowsheet_from_yaml_auto_frame(tmp_path):
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "AUTO_FRAME"
  title: "AUTOMATIC FRAME TEST"
  drawing_number: "DWG-AUTO-99"
  sheet_size: "D"
components:
  equipment: []
streams: []
"""
    pfd = Flowsheet.from_yaml(yaml_content)
    assert pfd.drawing_frame is not None
    assert pfd.drawing_frame.enabled is True


def test_flowsheet_default_no_frame(tmp_path):
    pfd = Flowsheet(id="NO_FRAME", name="Plain Flowsheet")
    assert pfd.drawing_frame is None

    out_svg = tmp_path / "plain.svg"
    ctx = SvgContext(str(out_svg))
    pfd.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_border"' not in content
    assert 'id="title_block"' not in content


def test_flowsheet_from_yaml_no_frame():
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "PLAIN_YAML"
  name: "Plain YAML Flowsheet"
components:
  equipment: []
streams: []
"""
    pfd = Flowsheet.from_yaml(yaml_content)
    assert pfd.drawing_frame is None


def test_flowsheet_from_yaml_settings_frame():
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "SETTINGS_FRAME"
  title: "SETTINGS FRAME TEST"
settings:
  drawing_frame:
    enabled: true
    sheet_size: "C"
components:
  equipment: []
streams: []
"""
    pfd = Flowsheet.from_yaml(yaml_content)
    assert pfd.drawing_frame is not None
    assert pfd.drawing_frame.enabled is True
    assert pfd.drawing_frame.sheet_size == "C"


def test_flowsheet_from_yaml_disabled_frame():
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "DISABLED_FRAME"
  drawing_number: "DWG-DISABLED"
settings:
  drawing_frame:
    enabled: false
components:
  equipment: []
streams: []
"""
    pfd = Flowsheet.from_yaml(yaml_content)
    assert pfd.drawing_frame is None or not pfd.drawing_frame.enabled


def test_flowsheet_from_yaml_boolean_disabled_frame(tmp_path):
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "BOOL_DISABLED_FRAME"
  drawing_number: "DWG-BOOL-DISABLED"
  sheet_size: "D"
settings:
  drawing_frame: false
components:
  equipment: []
streams: []
"""
    pfd = Flowsheet.from_yaml(yaml_content)
    assert pfd.drawing_frame is None or not pfd.drawing_frame.enabled

    out_svg = tmp_path / "bool_disabled.svg"
    ctx = SvgContext(str(out_svg))
    pfd.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_border"' not in content
    assert 'id="title_block"' not in content


def test_flowsheet_from_yaml_boolean_enabled_frame():
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "BOOL_ENABLED_FRAME"
  sheet_size: "C"
settings:
  drawing_frame: true
components:
  equipment: []
streams: []
"""
    pfd = Flowsheet.from_yaml(yaml_content)
    assert pfd.drawing_frame is not None
    assert pfd.drawing_frame.enabled is True
    assert pfd.drawing_frame.sheet_size == "C"
