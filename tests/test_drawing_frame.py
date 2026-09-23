from pyflowsheet import (
    DrawingBorder,
    DrawingFrame,
    DrawingLegend,
    Flowsheet,
    GeneralNotes,
    Pump,
    RevisionBlock,
    SheetSizeConfig,
    TitleBlock,
    Vessel,
    get_sheet_size_config,
)
from pyflowsheet.backends import SvgContext
from pyflowsheet.drawing import DrawingFrame as DrawingFrameFromDrawing
from pyflowsheet.schema.models import DrawingFrameSettingsSchema, MetadataSchema


def test_public_exports():
    """Verify all drawing frame components are exported from top-level and pyflowsheet.drawing."""
    assert DrawingFrame is DrawingFrameFromDrawing
    assert DrawingBorder is not None
    assert TitleBlock is not None
    assert RevisionBlock is not None
    assert DrawingLegend is not None
    assert GeneralNotes is not None
    assert SheetSizeConfig is not None
    assert callable(get_sheet_size_config)

    import pyflowsheet

    for name in [
        "DrawingFrame",
        "DrawingBorder",
        "TitleBlock",
        "RevisionBlock",
        "DrawingLegend",
        "GeneralNotes",
        "SheetSizeConfig",
        "get_sheet_size_config",
    ]:
        assert hasattr(pyflowsheet, name)
        assert name in pyflowsheet.__all__


def test_drawing_frame_full(tmp_path):
    out_svg = tmp_path / "test_frame.svg"
    ctx = SvgContext(str(out_svg))

    meta = {
        "title": "FULL SYSTEM",
        "drawing_number": "DWG-ALL-001",
        "revision": "C",
        "sheet_size": "D",
        "notes": ["NOTE 1"],
        "revisions": [
            {
                "zone": "-",
                "rev": "A",
                "description": "INIT",
                "date": "2026-09-01",
                "approved_by": "HG",
            }
        ],
    }

    frame = DrawingFrame.from_metadata(meta)
    assert frame.enabled is True
    assert frame.sheet_size == "D"
    bounds = frame.get_bounds()
    assert bounds == [-75.0, -55.0, 1295.0, 855.0]

    frame.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_border"' in content
    assert 'id="revision_block"' in content
    assert 'id="legend"' in content
    assert 'id="title_block"' in content
    assert 'id="drawing_notes"' in content


def test_drawing_frame_sheet_sizes():
    frame_c = DrawingFrame.from_metadata({"sheet_size": "C"})
    assert frame_c.sheet_size == "C"
    assert frame_c.get_bounds() == [-57.0, -42.0, 927.0, 607.0]

    frame_b = DrawingFrame(sheet_size="B")
    assert frame_b.sheet_size == "B"
    assert frame_b.get_bounds() == [-42.0, -32.0, 672.0, 442.0]


def test_drawing_frame_toggle_sub_blocks(tmp_path):
    out_svg = tmp_path / "test_partial_frame.svg"
    ctx = SvgContext(str(out_svg))

    settings = {
        "drawing_frame": {
            "enabled": True,
            "show_border": True,
            "show_title_block": True,
            "show_revision_block": False,
            "show_legend": False,
            "show_notes": False,
        }
    }
    meta = {"title": "PARTIAL SYSTEM", "drawing_number": "DWG-PART-01"}

    frame = DrawingFrame.from_metadata(meta, settings=settings)
    assert frame.show_revision_block is False
    assert frame.show_legend is False
    assert frame.show_notes is False

    frame.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_border"' in content
    assert 'id="title_block"' in content
    assert 'id="revision_block"' not in content
    assert 'id="legend"' not in content
    assert 'id="drawing_notes"' not in content


def test_drawing_frame_disabled(tmp_path):
    out_svg = tmp_path / "test_disabled_frame.svg"
    ctx = SvgContext(str(out_svg))

    frame = DrawingFrame.from_metadata(
        {"title": "DISABLED FRAME"},
        settings={"drawing_frame": {"enabled": False}},
    )
    assert frame.enabled is False

    frame.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_border"' not in content
    assert 'id="title_block"' not in content


def test_drawing_frame_from_pydantic_schema():
    meta = MetadataSchema(
        title="SCHEMA SYSTEM",
        drawing_number="DWG-SCHEMA-001",
        sheet_size="C",
        notes=["Pydantic note"],
    )
    settings = DrawingFrameSettingsSchema(
        enabled=True,
        sheet_size="C",
        show_notes=True,
    )
    frame = DrawingFrame.from_metadata(meta, settings=settings)
    assert frame.sheet_size == "C"
    assert frame.enabled is True
    assert frame.notes_block.notes == ["Pydantic note"]


def test_drawing_frame_dynamic_flowsheet(tmp_path):
    out_svg = tmp_path / "test_dynamic_frame.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="PUMP_SYS", name="Pump System")
    pfd.unit(Vessel(id="V-101", name="Feed Drum"))
    pfd.unit(Pump(id="P-101", name="Booster Pump"))

    frame = DrawingFrame(sheet_size="D")
    frame.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="legend"' in content
    assert "Booster Pump" in content or "Pump" in content
