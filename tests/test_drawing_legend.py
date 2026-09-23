from pyflowsheet import Flowsheet, StreamFlag, Vessel
from pyflowsheet.backends import SvgContext
from pyflowsheet.drawing.legend import DrawingLegend
from pyflowsheet.instruments import Instrument
from pyflowsheet.unitoperations import Pump
from pyflowsheet.valves import CheckValve, ControlValve, GrabSamplingTee, SafetyReliefValve


def test_drawing_legend_default_render(tmp_path):
    out_svg = tmp_path / "test_legend_default.svg"
    ctx = SvgContext(str(out_svg))
    legend = DrawingLegend(rect=((880.0, 58.0), (1260.0, 652.0)))
    legend.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="legend"' in content
    assert "FLOWSHEET &amp; P&amp;ID LEGEND" in content
    assert "PIPING &amp; STREAM LINES" in content
    assert "VALVES &amp; MOTIVE EQUIPMENT" in content
    assert "INSTRUMENTATION (ISA-5.1)" in content
    assert "MAJOR EQUIPMENT ICONS" in content


def test_drawing_legend_flowsheet_introspection(tmp_path):
    out_svg = tmp_path / "test_legend_dynamic.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="TEST", name="Test")
    v1 = Vessel(id="V1", name="Vessel 1")
    p1 = Pump(id="P1", name="Feed Pump")
    pfd.unit(v1)
    pfd.unit(p1)

    legend = DrawingLegend(rect=((880.0, 58.0), (1260.0, 652.0)))
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="legend"' in content
    assert "Pump" in content
    assert "Vessel" in content


def test_drawing_legend_with_instruments_and_streams(tmp_path):
    out_svg = tmp_path / "test_legend_inst_streams.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="TEST_INST", name="Test Instruments")
    v1 = Vessel(id="V1", name="Feed Vessel")
    p1 = Pump(id="P1", name="Pump 1")
    sf1 = StreamFlag(id="SF1", name="FEED")
    pfd.unit(v1)
    pfd.unit(p1)
    pfd.unit(sf1)

    pfd.connect("S1", sf1.ports["Out"], v1.ports["In"], line_type="process")
    pfd.connect("S2_REC", p1.ports["Out"], v1.ports["In"], line_type="recycle")

    inst1 = Instrument(id="FIT-101", name="Flow Transmitter", tag="FIT-101")
    inst2 = Instrument(id="LIT-102", name="Level Transmitter", tag="LIT-102")
    pfd.unit(inst1)
    pfd.unit(inst2)

    legend = DrawingLegend(rect=((880.0, 58.0), (1260.0, 652.0)))
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="legend"' in content
    assert "Major Process Stream" in content
    assert "Recycle / Return Stream" in content
    assert "Stream Inflow / Outflow Boundary" in content
    assert "INSTRUMENTATION (ISA-5.1)" in content
    assert "FIT" in content
    assert "Flow Indicating Transmitter" in content
    assert "LIT" in content
    assert "Level Indicating Transmitter" in content


def test_drawing_legend_with_valves(tmp_path):
    out_svg = tmp_path / "test_legend_valves.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="TEST_VALVES", name="Test Valves")
    cv = ControlValve(id="FCV-101", name="Flow Control Valve")
    ckv = CheckValve(id="CKV-101", name="Check Valve")
    psv = SafetyReliefValve(id="PSV-101", name="Safety Relief Valve")
    smp = GrabSamplingTee(id="SMP-101", name="Sampling Point")

    pfd.unit(cv)
    pfd.unit(ckv)
    pfd.unit(psv)
    pfd.unit(smp)

    legend = DrawingLegend(rect=((880.0, 58.0), (1260.0, 652.0)))
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="legend"' in content
    assert "Control Valve" in content
    assert "Check / Non-Return Valve" in content
    assert "Safety Relief Valve" in content
    assert "Sampling Valve" in content


def test_drawing_legend_custom_entries(tmp_path):
    out_svg = tmp_path / "test_legend_custom.svg"
    ctx = SvgContext(str(out_svg))

    custom = [
        {"section": "PIPING & STREAM LINES", "label": "Nitrogen Blanketing Line"},
        {"section": "MAJOR EQUIPMENT ICONS", "label": "Centrifugal Separator Skid"},
    ]
    legend = DrawingLegend(rect=((880.0, 58.0), (1260.0, 652.0)), custom_entries=custom)
    legend.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "Nitrogen Blanketing Line" in content
    assert "Centrifugal Separator Skid" in content


def test_drawing_legend_from_flowsheet_settings(tmp_path):
    out_svg = tmp_path / "test_legend_settings.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="TEST_SETTINGS", name="Test Settings")
    pfd.settings = {
        "drawing_frame": {
            "custom_legend_entries": [{"section": 4, "label": "Reverse Osmosis Rack (RO)"}]
        }
    }

    legend = DrawingLegend(rect=((880.0, 58.0), (1260.0, 652.0)))
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "Reverse Osmosis Rack (RO)" in content


def test_drawing_legend_custom_callable_draw(tmp_path):
    out_svg = tmp_path / "test_legend_callable.svg"
    ctx = SvgContext(str(out_svg))

    called = False

    def draw_my_symbol(ctx, x, y):
        nonlocal called
        called = True
        ctx.line((x - 10, y), (x + 10, y), lineColor=(255, 0, 0, 255), lineSize=2.0)

    custom = [{"section": "valves", "label": "Pinch Valve", "draw": draw_my_symbol}]
    legend = DrawingLegend(rect=((880.0, 58.0), (1260.0, 652.0)), custom_entries=custom)
    legend.draw(ctx)
    ctx.render(saveFile=True)

    assert called is True
    content = out_svg.read_text(encoding="utf-8")
    assert "Pinch Valve" in content


def test_drawing_legend_all_major_equipment_types(tmp_path):
    from pyflowsheet.unitoperations import (
        Distillation,
        FlotationCell,
        HeatExchanger,
        HorizontalVessel,
        MembraneModule,
        Mixer,
    )

    out_svg = tmp_path / "test_legend_all_eq.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="EQ_SYS", name="Equipment System")
    m1 = Mixer(id="M1", name="Flash Mixer")
    daf = FlotationCell(id="DAF-101", name="DAF Unit")
    mem = MembraneModule(id="NF-101", name="NF Membrane")
    hv = HorizontalVessel(id="HV-101", name="Decanter Drum")
    hx = HeatExchanger(id="E-101", name="Cooler")
    col = Distillation(id="T-101", name="Stripper")

    pfd.unit(m1)
    pfd.unit(daf)
    pfd.unit(mem)
    pfd.unit(hv)
    pfd.unit(hx)
    pfd.unit(col)

    legend = DrawingLegend(rect=((880.0, 58.0), (1260.0, 652.0)))
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "Mixer" in content
    assert "Flotation Separator (DAF)" in content
    assert "Tubular Reactor / Membrane" in content
    assert "Horizontal Process Vessel" in content
    assert "Heat Exchanger" in content
    assert "Distillation Column" in content


def test_drawing_legend_empty_flowsheet(tmp_path):
    out_svg = tmp_path / "test_legend_empty.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="EMPTY", name="Empty")
    legend = DrawingLegend()
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="legend"' in content
    assert "FLOWSHEET &amp; P&amp;ID LEGEND" in content
