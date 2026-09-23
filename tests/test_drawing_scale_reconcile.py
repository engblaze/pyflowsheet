import re
import xml.etree.ElementTree as ET
from pathlib import Path

from pyflowsheet import BlackBox, Flowsheet, SvgContext
from pyflowsheet.cli import main
from pyflowsheet.drawing.frame import DrawingFrame


def test_drawing_frame_get_drawable_rect_presets():
    """Verify get_drawable_rect() calculation across standard sheet sizes A through E."""
    expected_rects = {
        "A": ((5.0, 10.0), (310.0, 225.0)),
        "B": ((0.0, 10.0), (430.0, 320.0)),
        "C": ((-10.0, 5.0), (610.0, 450.0)),
        "D": ((-20.0, 0.0), (860.0, 640.0)),
        "E": ((-40.0, -10.0), (1230.0, 920.0)),
    }

    for size, expected in expected_rects.items():
        frame = DrawingFrame(sheet_size=size)
        rect = frame.get_drawable_rect(padding=20.0)
        assert rect == expected, f"Mismatch for sheet size {size}: {rect} vs {expected}"


def test_drawing_frame_get_drawable_rect_custom_padding():
    """Verify get_drawable_rect() adjusts correctly with custom padding."""
    frame = DrawingFrame(sheet_size="D")
    rect_pad10 = frame.get_drawable_rect(padding=10.0)
    assert rect_pad10 == ((-30.0, -10.0), (870.0, 650.0))

    rect_pad0 = frame.get_drawable_rect(padding=0.0)
    assert rect_pad0 == ((-40.0, -20.0), (880.0, 660.0))


def test_drawing_frame_get_drawable_rect_dynamic_expansion():
    """Verify printable rectangle expands when frame blocks are hidden."""
    # When legend, revision block, and title block are hidden, right edge extends to inner border
    frame_no_right = DrawingFrame(
        sheet_size="D",
        show_legend=False,
        show_revision_block=False,
        show_title_block=False,
    )
    rect = frame_no_right.get_drawable_rect(padding=20.0)
    # inner_rect is ((-40, -20), (1260, 820)), so x_max expands to 1260 - 20 = 1240
    assert rect[1][0] == 1240.0

    # When notes and title block are hidden, bottom edge extends to inner border
    frame_no_bottom = DrawingFrame(
        sheet_size="D",
        show_notes=False,
        show_title_block=False,
    )
    rect_bot = frame_no_bottom.get_drawable_rect(padding=20.0)
    # y_max expands to 820 - 20 = 800
    assert rect_bot[1][1] == 800.0


def test_flowsheet_get_content_bounds_empty():
    """Verify get_content_bounds() returns None when flowsheet has no elements."""
    fs = Flowsheet("EMPTY", "Empty Flowsheet")
    assert fs.get_content_bounds() is None


def test_flowsheet_get_content_bounds_units_and_streams():
    """Verify get_content_bounds() correctly aggregates units, streams, and leader lines."""
    fs = Flowsheet("BOUNDS_TEST", "Bounds Test")
    u1 = BlackBox("U1", "Unit 1", position=(100.0, 150.0), size=(60.0, 40.0))
    u2 = BlackBox("U2", "Unit 2", position=(300.0, 250.0), size=(80.0, 50.0))
    fs.addUnits([u1, u2])

    u1.leader_line = [(100.0, 150.0), (50.0, 80.0)]
    stream = fs.connect("S1", u1["Out"], u2["In"])
    stream.calculated_route = [(160.0, 170.0), (200.0, 170.0), (200.0, 275.0), (300.0, 275.0)]

    bounds = fs.get_content_bounds()
    assert bounds is not None
    (x_min, y_min), (x_max, y_max) = bounds
    # Leader line reaches x=50, y=80; u2 extends to x=380, y=300
    assert x_min == 50.0
    assert y_min == 80.0
    assert x_max == 380.0
    assert y_max == 300.0


def test_in_bounds_diagram_maintains_identity_scale(tmp_path):
    """Verify that a diagram that fits cleanly inside the printable area has no transform."""
    fs = Flowsheet("IN_BOUNDS", "In Bounds Test")
    fs.enable_drawing_frame(sheet_size="D")

    # Units well within printable area ((-20, 0), (860, 640))
    u1 = BlackBox("U1", "Unit 1", position=(100.0, 100.0), size=(80.0, 60.0))
    u2 = BlackBox("U2", "Unit 2", position=(300.0, 100.0), size=(80.0, 60.0))
    fs.addUnits([u1, u2])
    fs.connect("S1", u1["Out"], u2["In"])

    out_file = str(tmp_path / "in_bounds.svg")
    ctx = SvgContext(out_file)
    fs.draw(ctx)
    svg_str = ctx.render(saveFile=True)

    root = ET.fromstring(svg_str)
    ns = "{http://www.w3.org/2000/svg}"
    diagram_group = None
    for g in root.findall(f"{ns}g"):
        if g.get("id") == "flowsheet_diagram":
            diagram_group = g
            break

    assert diagram_group is not None
    # No transform applied because it already fits cleanly
    assert "transform" not in diagram_group.attrib


def test_out_of_bounds_diagram_shrink_to_fit_and_centering(tmp_path):
    """Verify out-of-bounds diagram receives uniform scale (s <= 1.0) and centering."""
    yaml_path = Path("examples/water_treatment_pid.yaml")
    assert yaml_path.exists()

    fs = Flowsheet.from_yaml(yaml_path)
    fs.auto_layout(force_reposition=True)

    content_bounds = fs.get_content_bounds()
    assert content_bounds is not None
    (cx0, cy0), (cx1, cy1) = content_bounds
    # Auto-layout pushed content beyond X=880 (into legend)
    assert cx1 > 880.0

    out_file = str(tmp_path / "scaled_diagram.svg")
    ctx = SvgContext(out_file)
    fs.draw(ctx)
    svg_str = ctx.render(saveFile=True)

    root = ET.fromstring(svg_str)
    ns = "{http://www.w3.org/2000/svg}"
    diagram_group = None
    for g in root.findall(f"{ns}g"):
        if g.get("id") == "flowsheet_diagram":
            diagram_group = g
            break

    assert diagram_group is not None
    transform = diagram_group.get("transform")
    assert transform is not None

    match = re.search(r"translate\(([^,]+),\s*([^)]+)\)\s*scale\(([^)]+)\)", transform)
    assert match is not None
    dx = float(match.group(1))
    dy = float(match.group(2))
    s = float(match.group(3))

    # Assert uniform scale factor s <= 1.0
    assert 0.0 < s <= 1.0

    # Calculate transformed bounds of content
    tx0 = cx0 * s + dx
    tx1 = cx1 * s + dx
    ty0 = cy0 * s + dy
    ty1 = cy1 * s + dy

    (px0, py0), (px1, py1) = fs.drawing_frame.get_drawable_rect()

    # Verify zero spill beyond printable area
    assert tx0 >= px0 - 0.5, f"Spilled left: {tx0} < {px0}"
    assert tx1 <= px1 + 0.5, f"Spilled right into legend: {tx1} > {px1}"
    assert ty0 >= py0 - 0.5, f"Spilled top over border: {ty0} < {py0}"
    assert ty1 <= py1 + 0.5, f"Spilled bottom into notes/title: {ty1} > {py1}"


def test_compact_sheet_size_scaling(tmp_path):
    """Verify flowsheet automatically shrinks to fit compact sheet sizes like A, B, C."""
    yaml_path = Path("examples/water_treatment_pid.yaml")
    for compact_size in ["A", "B", "C"]:
        fs = Flowsheet.from_yaml(yaml_path)
        fs.drawing_frame.sheet_size = compact_size
        fs.drawing_frame.cfg = fs.drawing_frame.cfg.__class__(
            **fs.drawing_frame.cfg.__dict__
        )  # or get preset
        from pyflowsheet.drawing.sheet_sizes import get_sheet_size_config

        fs.drawing_frame.cfg = get_sheet_size_config(compact_size)

        out_file = str(tmp_path / f"scaled_{compact_size}.svg")
        ctx = SvgContext(out_file)
        fs.draw(ctx)
        svg_str = ctx.render(saveFile=True)

        root = ET.fromstring(svg_str)
        ns = "{http://www.w3.org/2000/svg}"
        dg = next((g for g in root.findall(f"{ns}g") if g.get("id") == "flowsheet_diagram"), None)
        assert dg is not None
        assert "transform" in dg.attrib
        match = re.search(r"scale\(([^)]+)\)", dg.get("transform"))
        assert match is not None
        scale = float(match.group(1))
        # Size A should scale down more than Size B, which scales down more than Size C
        assert 0.0 < scale < 1.0


def test_cli_render_water_treatment_pid_auto_layout_force_reposition(tmp_path):
    """End-to-end CLI regression test verifying zero spill with --auto-layout --force-reposition."""
    yaml_path = Path("examples/water_treatment_pid.yaml")
    out_svg = tmp_path / "water_treatment_autolayout_reconciled.svg"

    ret = main([
        "render",
        str(yaml_path),
        "-o",
        str(out_svg),
        "--auto-layout",
        "--force-reposition",
    ])
    assert ret == 0
    assert out_svg.exists()

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="flowsheet_diagram"' in content
    assert 'id="drawing_border"' in content
    assert 'id="legend"' in content
    assert 'id="title_block"' in content
    assert 'id="drawing_notes"' in content

    root = ET.fromstring(content)
    ns = "{http://www.w3.org/2000/svg}"
    dg = next((g for g in root.findall(f"{ns}g") if g.get("id") == "flowsheet_diagram"), None)
    assert dg is not None
    assert "transform" in dg.attrib
    assert "scale(" in dg.get("transform")
