import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.core import Port, Stream, UnitOperation


class DummyUnit(UnitOperation):
    def __init__(self, id, pos):
        super().__init__(id, id, position=pos, size=(20, 20))
        self.ports["P"] = Port("P", self, (0.5, 0.5), (1, 0))


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "signal_test.svg")
    return SvgContext(out_file)


def test_stream_line_type_default():
    u1 = DummyUnit("U1", (0, 0))
    u2 = DummyUnit("U2", (100, 0))
    s = Stream("S1", u1["P"], u2["P"])
    assert s.line_type == "process"


def test_render_all_signal_types(svg_ctx):
    u1 = DummyUnit("U1", (10, 50))
    u2 = DummyUnit("U2", (150, 50))

    signals = ["process", "pneumatic", "electric", "digital", "capillary"]
    for idx, st in enumerate(signals):
        stream = Stream(f"SIG_{st}", u1["P"], u2["P"], line_type=st)
        stream.calculated_route = [(10, 50 + idx * 30), (150, 50 + idx * 30)]
        svg_ctx.startGroup(stream.id)
        stream.draw(svg_ctx)
        svg_ctx.endGroup()

    svg_content = svg_ctx.render(saveFile=False)
    # Check that electric has dasharray
    assert "stroke-dasharray" in svg_content
    # Check that pneumatic has tick marks
    assert 'id="SIG_pneumatic"' in svg_content
    # Check that digital has circle or dot elements
    assert 'id="SIG_digital"' in svg_content
    # Check that capillary has cross lines
    assert 'id="SIG_capillary"' in svg_content


def test_signal_short_segments(svg_ctx):
    u1 = DummyUnit("U1", (10, 10))
    u2 = DummyUnit("U2", (15, 10))  # Length = 5 (< 10 and < 12)

    for st in ["pneumatic", "digital", "capillary"]:
        s = Stream(f"SHORT_{st}", u1["P"], u2["P"], line_type=st)
        s.calculated_route = [(10, 10), (15, 10)]
        svg_ctx.startGroup(s.id)
        s.draw(svg_ctx)
        svg_ctx.endGroup()

    svg_content = svg_ctx.render(saveFile=False)
    assert 'id="SHORT_pneumatic"' in svg_content
    assert 'id="SHORT_digital"' in svg_content
    assert 'id="SHORT_capillary"' in svg_content


def test_electric_custom_dash(svg_ctx):
    u1 = DummyUnit("U1", (0, 0))
    u2 = DummyUnit("U2", (100, 0))
    s = Stream("E_CUSTOM", u1["P"], u2["P"], line_type="electric")
    s.dashArray = "12,6"
    s.calculated_route = [(0, 0), (100, 0)]
    svg_ctx.startGroup(s.id)
    s.draw(svg_ctx)
    svg_ctx.endGroup()

    svg_content = svg_ctx.render(saveFile=False)
    assert (
        "stroke-dasharray:12,6" in svg_content
        or 'stroke-dasharray="12,6"' in svg_content
        or "12,6" in svg_content
    )


def test_signal_with_crossover_bridges(svg_ctx):
    from pyflowsheet.layout.crossover import CrossoverBridge

    u1 = DummyUnit("U1", (0, 50))
    u2 = DummyUnit("U2", (100, 50))
    s = Stream("SIG_XOVER", u1["P"], u2["P"], line_type="pneumatic")
    s.calculated_route = [(0, 50), (100, 50)]
    s.crossover_bridges = [
        CrossoverBridge(
            base_stream="S_OTHER",
            bridging_stream="SIG_XOVER",
            intersection=(50, 50),
            direction="horizontal",
            radius=6.0,
            style="arc",
        )
    ]

    svg_ctx.startGroup(s.id)
    s.draw(svg_ctx)
    svg_ctx.endGroup()

    svg_content = svg_ctx.render(saveFile=False)
    assert 'id="SIG_XOVER"' in svg_content
    assert " A " in svg_content  # Arc command from crossover bridge
