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


def test_drawing_legend_process_streams_dicts(tmp_path):
    out_svg = tmp_path / "test_legend_streams_dict.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="P_STR", name="Process Streams")
    v1 = Vessel(id="V1", name="Vessel 1")
    pfd.unit(v1)

    streams = [
        {"id": "S01", "name": "Raw Wastewater Influent", "description": "1 gpm"},
        {"id": "S02", "name": "Flocculated Slurry"},
        {"id": "S03", "name": "Flotation Float"},
        {"id": "S04", "name": "Clarified Water"},
    ]
    legend = DrawingLegend(
        rect=((880.0, 58.0), (1260.0, 652.0)),
        process_streams=streams,
    )
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "5. PROCESS STREAMS" in content
    assert "S01" in content
    assert "Raw Wastewater Influent" in content
    assert "S02" in content
    assert "Flocculated Slurry" in content
    assert "S03" in content
    assert "S04" in content


def test_drawing_legend_process_streams_tuples_and_strings(tmp_path):
    out_svg = tmp_path / "test_legend_streams_tuples.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="TUP_STR", name="Tuple Streams")
    v1 = Vessel(id="V1", name="Feed")
    pfd.unit(v1)

    streams = [
        ("1", "Feed Stream", "100 kg/h"),
        "2: Product Stream",
        "3 - Offgas Stream",
        "4. Recycle Stream",
    ]
    legend = DrawingLegend(process_streams=streams)
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "5. PROCESS STREAMS" in content
    assert "Feed Stream (100 kg/h)" in content
    assert "Product Stream" in content
    assert "Offgas Stream" in content
    assert "Recycle Stream" in content


def test_drawing_legend_process_streams_from_settings(tmp_path):
    out_svg = tmp_path / "test_legend_streams_settings.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="SETT_STR", name="Settings Streams")
    v1 = Vessel(id="V1", name="Feed")
    pfd.unit(v1)
    pfd.settings = {
        "drawing_frame": {
            "process_streams": [
                {"id": "STR-01", "name": "Demineralized Water"},
                {"id": "STR-02", "name": "Blowdown Water"},
            ]
        }
    }

    legend = DrawingLegend()
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "5. PROCESS STREAMS" in content
    assert "STR-01" in content
    assert "Demineralized Water" in content
    assert "STR-02" in content
    assert "Blowdown Water" in content


def test_drawing_legend_process_streams_auto(tmp_path):
    out_svg = tmp_path / "test_legend_streams_auto.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="AUTO_STR", name="Auto Streams")
    v1 = Vessel(id="V1", name="Feed Vessel")
    p1 = Pump(id="P1", name="Feed Pump")
    pfd.unit(v1)
    pfd.unit(p1)
    pfd.connect(
        "S_FEED",
        v1.ports["Out"],
        p1.ports["In"],
        line_type="process",
        stream_name="Main Feed Stream",
    )
    pfd.settings = {"drawing_frame": {"show_process_streams": True}}

    legend = DrawingLegend()
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "5. PROCESS STREAMS" in content
    assert "S_FEED" in content
    assert "Main Feed Stream" in content


def test_drawing_legend_process_streams_custom_section(tmp_path):
    out_svg = tmp_path / "test_legend_custom_streams.svg"
    ctx = SvgContext(str(out_svg))

    custom = [
        {"section": "streams", "id": "1", "label": "Chilled Brine Loop"},
        {"section": 5, "id": "2", "label": "Steam Condensate"},
    ]
    legend = DrawingLegend(custom_entries=custom)
    legend.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "5. PROCESS STREAMS" in content
    assert "Chilled Brine Loop" in content
    assert "Steam Condensate" in content


def test_drawing_legend_single_column_toggle(tmp_path):
    out_svg = tmp_path / "test_legend_single_col.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="SINGLE_COL", name="Single Column")
    v1 = Vessel(id="V1", name="Feed")
    p1 = Pump(id="P1", name="Pump")
    pfd.unit(v1)
    pfd.unit(p1)

    legend = DrawingLegend(
        two_column_sections=False, process_streams=["S1: Stream 1", "S2: Stream 2"]
    )
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "5. PROCESS STREAMS" in content
    assert "Stream 1" in content
    assert "Stream 2" in content


def test_drawing_frame_with_process_streams(tmp_path):
    from pyflowsheet.drawing import DrawingFrame

    out_svg = tmp_path / "test_frame_streams.svg"
    ctx = SvgContext(str(out_svg))

    meta = {
        "title": "Frame Test",
        "drawing_number": "DWG-001",
        "sheet_size": "D",
    }
    settings = {
        "drawing_frame": {
            "process_streams": [
                {"id": "S1", "name": "Inlet Slurry"},
                {"id": "S2", "name": "Permeate Water"},
            ]
        }
    }
    frame = DrawingFrame.from_metadata(meta, settings=settings)
    frame.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="legend"' in content
    assert "5. PROCESS STREAMS" in content
    assert "Inlet Slurry" in content
    assert "Permeate Water" in content


def test_flowsheet_enable_drawing_frame_process_streams(tmp_path):
    out_svg = tmp_path / "test_enable_frame_streams.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="ENABLE_TEST", name="Enable Frame Test")
    v1 = Vessel(id="V1", name="Tank 1")
    pfd.unit(v1)
    pfd.enable_drawing_frame(
        drawing_number="DWG-100",
        process_streams=[
            {"id": "STR-A", "name": "Solvent Feed"},
            {"id": "STR-B", "name": "Purified Solute"},
        ],
    )
    pfd.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert 'id="legend"' in content
    assert "5. PROCESS STREAMS" in content
    assert "Solvent Feed" in content
    assert "Purified Solute" in content


def test_drawing_legend_enumerates_motive_equipment_types(tmp_path):
    from pyflowsheet.unitoperations import PeristalticPump, ProgressiveCavityPump

    out_svg = tmp_path / "test_legend_motive_types.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="PUMP_SYS", name="Pump System")
    p1 = Pump(id="P-101", name="Centrifugal Feed Pump")
    p2 = ProgressiveCavityPump(id="P-102", name="Dosing Screw Pump")
    p3 = PeristalticPump(id="P-103", name="Tubing Hose Pump")

    pfd.unit(p1)
    pfd.unit(p2)
    pfd.unit(p3)

    legend = DrawingLegend()
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "Centrifugal Pump (P-101)" in content
    assert "Progressive Cavity Pump (P-102)" in content
    assert "Peristaltic Pump (P-103)" in content


def test_drawing_legend_wt_pid_simple_pump_enumeration(tmp_path):
    from pyflowsheet.unitoperations import ProgressiveCavityPump

    out_svg = tmp_path / "test_legend_wt_pumps.svg"
    ctx = SvgContext(str(out_svg))

    pfd = Flowsheet(id="WT_PUMPS", name="Water Treatment Pumps")
    p101 = Pump(id="P-101", name="Influent Feed Pump")
    p102 = ProgressiveCavityPump(id="P-102", name="IONP Dosing Pump")
    p103 = Pump(id="P-103", name="Slurry Transfer Pump")
    p105 = ProgressiveCavityPump(id="P-105", name="Float Sludge Pump")
    p106 = Pump(id="P-106", name="NF Booster Pump")
    p107 = Pump(id="P-107", name="Regenerated IONP Pump")

    for p in (p101, p102, p103, p105, p106, p107):
        pfd.unit(p)

    legend = DrawingLegend()
    legend.draw(ctx, flowsheet=pfd)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "Centrifugal Pump (P-101, P-103, P-106, P-107)" in content
    assert "Progressive Cavity Pump (P-102, P-105)" in content
    assert "Centrifugal Pump (P-101 .. P-107)" not in content


def test_drawing_legend_custom_cavity_pump(tmp_path):
    out_svg = tmp_path / "test_legend_custom_cavity.svg"
    ctx = SvgContext(str(out_svg))

    custom = [
        {"section": 2, "symbol": "progressive_cavity_pump", "label": "Sludge Screw Pump"},
        {"section": 2, "symbol": "peristaltic_pump", "label": "Chemical Hose Pump"},
    ]
    legend = DrawingLegend(custom_entries=custom)
    legend.draw(ctx)
    ctx.render(saveFile=True)

    content = out_svg.read_text(encoding="utf-8")
    assert "Sludge Screw Pump" in content
    assert "Chemical Hose Pump" in content

