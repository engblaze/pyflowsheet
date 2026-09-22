import os
import pytest
from pyflowsheet.unitoperations import (
    BlackBox,
    Distillation,
    HeatExchanger,
    Mixer,
    PlateHex,
    Pump,
    Splitter,
    StreamFlag,
    Valve,
    Vessel,
    Compressor,
)
from pyflowsheet.internals import (
    Baffles,
    CatalystBed,
    DiscDonutBaffles,
    DividingWall,
    Jacket,
    LiquidRing,
    RandomPacking,
    ReciprocatingInternals,
    Stirrer,
    Trays,
    Tubes,
)
from pyflowsheet.backends.svgcontext import SvgContext


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "unit_op_test.svg")
    return SvgContext(out_file)


def test_all_unit_operations_instantiation_and_drawing(svg_ctx):
    units = [
        BlackBox("BB1", "Black Box Step", position=(10, 10), size=(60, 40)),
        Distillation("T1", "Tower", position=(80, 10), size=(40, 120)),
        HeatExchanger("HX1", "Exchanger", position=(130, 10), size=(40, 40)),
        Mixer("MX1", "Mixer", position=(180, 10), size=(30, 30)),
        PlateHex("PHX1", "Plate Hex", position=(220, 10), size=(40, 40)),
        Pump("P1", "Pump", position=(270, 10), size=(30, 30)),
        Splitter("SP1", "Splitter", position=(310, 10), size=(30, 30)),
        StreamFlag("SF1", "Feed", position=(350, 10), size=(30, 30)),
        Valve("V1", "Control Valve", position=(390, 10), size=(20, 20)),
        Vessel("V101", "Storage Vessel", position=(420, 10), size=(40, 80)),
        Compressor("C1", "Compressor", position=(470, 10), size=(40, 40)),
    ]

    for unit in units:
        svg_ctx.startGroup(unit.id)
        svg_ctx.startTransformedGroup(unit)
        unit.draw(svg_ctx)
        svg_ctx.endGroup()
        unit.drawTextLayer(svg_ctx, showPorts=True)
        svg_ctx.endGroup()

        # Each unit must have at least one port or ports dictionary
        assert isinstance(unit.ports, dict)


def test_vessel_with_internals(svg_ctx):
    internals = [
        Stirrer(),
        Tubes(tubes=5),
        Baffles(),
        CatalystBed(),
        Jacket(),
    ]
    vessel = Vessel("V102", "Reactor Vessel", position=(100, 100), size=(60, 120), internals=internals)
    assert len(vessel.internals) == 5

    svg_ctx.startGroup(vessel.id)
    vessel.draw(svg_ctx)
    svg_ctx.endGroup()


def test_distillation_column_with_internals(svg_ctx):
    internals = [
        Trays(5),
        RandomPacking(start=0.2, end=0.6),
    ]
    col = Distillation("T102", "Packed Column", position=(50, 50), size=(40, 200), internals=internals)
    assert len(col.internals) == 2

    svg_ctx.startGroup(col.id)
    col.draw(svg_ctx)
    svg_ctx.endGroup()
