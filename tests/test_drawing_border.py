from pyflowsheet.backends import SvgContext
from pyflowsheet.drawing.border import DrawingBorder
from pyflowsheet.drawing.sheet_sizes import SheetSizeConfig, get_sheet_size_config


def test_sheet_size_config_d():
    cfg = get_sheet_size_config("D")
    assert cfg.inner_rect == ((-40.0, -20.0), (1260.0, 820.0))
    assert cfg.margin == 15.0
    assert cfg.outer_rect == ((-55.0, -35.0), (1275.0, 835.0))
    assert cfg.bounds == [-75.0, -55.0, 1295.0, 855.0]


def test_sheet_size_config_presets_and_fallback():
    for name in ["A", "B", "C", "D", "E"]:
        cfg = get_sheet_size_config(name)
        assert cfg.name == name
        assert cfg.inner_rect is not None
        assert cfg.outer_rect is not None
        assert len(cfg.bounds) == 4

    # Case insensitivity and whitespace stripping
    assert get_sheet_size_config("  d  ").name == "D"
    assert get_sheet_size_config("c").name == "C"

    # Fallback to D for None or unknown preset
    assert get_sheet_size_config(None).name == "D"
    assert get_sheet_size_config("UNKNOWN").name == "D"
    assert get_sheet_size_config("").name == "D"


def test_sheet_size_config_sub_blocks():
    cfg = get_sheet_size_config("D")
    assert cfg.revision_block_rect == ((880.0, -20.0), (1260.0, 50.0))
    assert cfg.legend_rect == ((880.0, 58.0), (1260.0, 652.0))
    assert cfg.title_block_rect == ((880.0, 660.0), (1260.0, 820.0))
    assert cfg.notes_rect == ((-30.0, 660.0), (860.0, 820.0))


def test_drawing_border_render(tmp_path):
    out_svg = tmp_path / "test_border.svg"
    ctx = SvgContext(str(out_svg))
    cfg = get_sheet_size_config("D")
    border = DrawingBorder(cfg=cfg)
    border.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_border"' in content
    assert "REVISIONS" not in content  # Border only
    assert ">1<" in content
    assert ">8<" in content
    assert ">A<" in content
    assert ">D<" in content


def test_drawing_border_default_and_custom_preset(tmp_path):
    border_default = DrawingBorder()
    assert border_default.cfg.name == "D"
    assert border_default.id == "drawing_border"

    cfg_custom = SheetSizeConfig(
        name="CUSTOM",
        inner_rect=((0.0, 0.0), (500.0, 400.0)),
        margin=10.0,
        canvas_margin=15.0,
        num_zones_x=4,
        zone_labels_y=("A", "B"),
    )
    border_custom = DrawingBorder(cfg=cfg_custom)
    assert border_custom.cfg.name == "CUSTOM"

    out_svg = tmp_path / "test_border_custom.svg"
    ctx = SvgContext(str(out_svg))
    border_custom.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="drawing_border"' in content
    assert ">4<" in content
    assert ">5<" not in content
    assert ">B<" in content
    assert ">C<" not in content
