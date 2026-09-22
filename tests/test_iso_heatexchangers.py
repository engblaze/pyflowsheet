import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.unitoperations import (
    AirCooler,
    Condenser,
    FiredHeater,
    HeatExchanger,
    PlateHex,
    Reboiler,
    ShellAndTubeExchanger,
)
from pyflowsheet.unitoperations.aircooler import AirCooler as AirCoolerDirect
from pyflowsheet.unitoperations.condenser import Condenser as CondenserDirect
from pyflowsheet.unitoperations.firedheater import FiredHeater as FiredHeaterDirect
from pyflowsheet.unitoperations.reboiler import Reboiler as ReboilerDirect
from pyflowsheet.unitoperations.shellandtube import (
    ShellAndTubeExchanger as ShellAndTubeExchangerDirect,
)


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "heatex_test.svg")
    return SvgContext(out_file)


def test_shell_and_tube_ports():
    hex_unit = ShellAndTubeExchanger("E-101", "TEMA Exchanger", position=(10, 10), size=(80, 40))
    assert "TubeIn" in hex_unit.ports
    assert "TubeOut" in hex_unit.ports
    assert "ShellIn" in hex_unit.ports
    assert "ShellOut" in hex_unit.ports

    # Verify positions and normals
    assert hex_unit.ports["TubeIn"].relativePosition == (0.0, 0.5)
    assert hex_unit.ports["TubeIn"].normal == (-1, 0)
    assert hex_unit.ports["TubeOut"].relativePosition == (1.0, 0.5)
    assert hex_unit.ports["TubeOut"].normal == (1, 0)
    assert hex_unit.ports["TubeOut"].intent == "out"
    assert hex_unit.ports["ShellIn"].relativePosition == (0.25, 0.0)
    assert hex_unit.ports["ShellIn"].normal == (0, -1)
    assert hex_unit.ports["ShellOut"].relativePosition == (0.75, 1.0)
    assert hex_unit.ports["ShellOut"].normal == (0, 1)
    assert hex_unit.ports["ShellOut"].intent == "out"

    # Aliases
    assert hex_unit.ports["In"] == hex_unit.ports["TubeIn"]
    assert hex_unit.ports["Out"] == hex_unit.ports["TubeOut"]
    assert hex_unit.ports["TIn"] == hex_unit.ports["TubeIn"]
    assert hex_unit.ports["TOut"] == hex_unit.ports["TubeOut"]
    assert hex_unit.ports["SIn"] == hex_unit.ports["ShellIn"]
    assert hex_unit.ports["SOut"] == hex_unit.ports["ShellOut"]


def test_air_cooler_ports():
    ac = AirCooler("AC-101", "Fin Fan Cooler", position=(10, 10), size=(70, 50))
    assert "In" in ac.ports
    assert "Out" in ac.ports

    # Verify positions and normals
    assert ac.ports["In"].relativePosition == (0.0, 0.2)
    assert ac.ports["In"].normal == (-1, 0)
    assert ac.ports["Out"].relativePosition == (1.0, 0.2)
    assert ac.ports["Out"].normal == (1, 0)
    assert ac.ports["Out"].intent == "out"

    # Aliases
    assert ac.ports["ProcessIn"] == ac.ports["In"]
    assert ac.ports["ProcessOut"] == ac.ports["Out"]


def test_reboiler_ports():
    reb = Reboiler("E-102", "Kettle Reboiler", position=(10, 10), size=(70, 50))
    assert "LiquidIn" in reb.ports
    assert "VaporOut" in reb.ports
    assert "BottomsOut" in reb.ports
    assert "HeatingIn" in reb.ports
    assert "HeatingOut" in reb.ports

    # Verify positions and normals
    assert reb.ports["LiquidIn"].relativePosition == (0.25, 1.0)
    assert reb.ports["LiquidIn"].normal == (0, 1)
    assert reb.ports["VaporOut"].relativePosition == (0.45, 0.0)
    assert reb.ports["VaporOut"].normal == (0, -1)
    assert reb.ports["VaporOut"].intent == "out"
    assert reb.ports["BottomsOut"].relativePosition == (0.9, 1.0)
    assert reb.ports["BottomsOut"].normal == (0, 1)
    assert reb.ports["BottomsOut"].intent == "out"
    assert reb.ports["HeatingIn"].relativePosition == (0.0, 0.55)
    assert reb.ports["HeatingIn"].normal == (-1, 0)
    assert reb.ports["HeatingOut"].relativePosition == (0.0, 0.8)
    assert reb.ports["HeatingOut"].normal == (-1, 0)
    assert reb.ports["HeatingOut"].intent == "out"

    # Aliases
    assert reb.ports["In"] == reb.ports["LiquidIn"]
    assert reb.ports["Vapor"] == reb.ports["VaporOut"]
    assert reb.ports["Bottoms"] == reb.ports["BottomsOut"]
    assert reb.ports["SteamIn"] == reb.ports["HeatingIn"]
    assert reb.ports["SteamOut"] == reb.ports["HeatingOut"]


def test_condenser_ports():
    c = Condenser("E-103", "Surface Condenser", position=(10, 10), size=(60, 40))
    assert "VaporIn" in c.ports
    assert "CondensateOut" in c.ports
    assert "CoolingIn" in c.ports
    assert "CoolingOut" in c.ports

    # Verify positions and normals
    assert c.ports["VaporIn"].relativePosition == (0.5, 0.0)
    assert c.ports["VaporIn"].normal == (0, -1)
    assert c.ports["CondensateOut"].relativePosition == (0.5, 1.0)
    assert c.ports["CondensateOut"].normal == (0, 1)
    assert c.ports["CondensateOut"].intent == "out"
    assert c.ports["CoolingIn"].relativePosition == (0.0, 0.6)
    assert c.ports["CoolingIn"].normal == (-1, 0)
    assert c.ports["CoolingOut"].relativePosition == (1.0, 0.4)
    assert c.ports["CoolingOut"].normal == (1, 0)
    assert c.ports["CoolingOut"].intent == "out"

    # Aliases
    assert c.ports["In"] == c.ports["VaporIn"]
    assert c.ports["Out"] == c.ports["CondensateOut"]
    assert c.ports["CoolingWaterIn"] == c.ports["CoolingIn"]
    assert c.ports["CoolingWaterOut"] == c.ports["CoolingOut"]


def test_fired_heater_ports():
    fh = FiredHeater("H-101", "Process Furnace", position=(10, 10), size=(60, 90))
    assert "ProcessIn" in fh.ports
    assert "ProcessOut" in fh.ports
    assert "Fuel" in fh.ports
    assert "Stack" in fh.ports

    # Verify positions and normals
    assert fh.ports["ProcessIn"].relativePosition == (1.0, 0.25)
    assert fh.ports["ProcessIn"].normal == (1, 0)
    assert fh.ports["ProcessOut"].relativePosition == (1.0, 0.75)
    assert fh.ports["ProcessOut"].normal == (1, 0)
    assert fh.ports["ProcessOut"].intent == "out"
    assert fh.ports["Fuel"].relativePosition == (0.5, 1.0)
    assert fh.ports["Fuel"].normal == (0, 1)
    assert fh.ports["Stack"].relativePosition == (0.5, 0.0)
    assert fh.ports["Stack"].normal == (0, -1)
    assert fh.ports["Stack"].intent == "out"

    # Aliases
    assert fh.ports["In"] == fh.ports["ProcessIn"]
    assert fh.ports["Out"] == fh.ports["ProcessOut"]
    assert fh.ports["FlueGas"] == fh.ports["Stack"]


def test_heat_exchangers_drawing(svg_ctx):
    units = [
        ShellAndTubeExchanger("E1", "TEMA", position=(10, 10), size=(70, 35)),
        AirCooler("AC1", "FinFan", position=(90, 10), size=(60, 45)),
        Reboiler("R1", "Kettle", position=(160, 10), size=(65, 45)),
        Condenser("C1", "Condenser", position=(235, 10), size=(50, 40)),
        FiredHeater("H1", "Furnace", position=(295, 10), size=(55, 80)),
    ]
    for u in units:
        svg_ctx.startGroup(u.id)
        svg_ctx.startTransformedGroup(u)
        u.draw(svg_ctx)
        svg_ctx.endGroup()
        u.drawTextLayer(svg_ctx)
        svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    assert len(output) > 1200


def test_package_exports():
    assert ShellAndTubeExchanger is ShellAndTubeExchangerDirect
    assert AirCooler is AirCoolerDirect
    assert Reboiler is ReboilerDirect
    assert Condenser is CondenserDirect
    assert FiredHeater is FiredHeaterDirect
    # Backward compatibility
    assert HeatExchanger is not None
    assert PlateHex is not None


def test_transformations():
    # Verify horizontal and vertical flip on units
    st = ShellAndTubeExchanger("E102", "TEMA", position=(0, 0), size=(80, 40))
    st.flipHorizontal()
    assert st.isFlippedHorizontal
    assert st.ports["TubeIn"].relativePosition == (1.0, 0.5)
    assert st.ports["TubeOut"].relativePosition == (0.0, 0.5)

    fh = FiredHeater("H102", "Furnace", position=(0, 0), size=(60, 90))
    fh.flipVertical()
    assert fh.isFlippedVertical
    assert fh.ports["Fuel"].relativePosition == (0.5, 0.0)
    assert fh.ports["Stack"].relativePosition == (0.5, 1.0)
