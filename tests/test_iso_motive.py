import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.unitoperations import (
    Blower,
    PeristalticPump,
    ProgressiveCavityPump,
    ReciprocatingPump,
)
from pyflowsheet.unitoperations.blower import Blower as BlowerDirect
from pyflowsheet.unitoperations.peristalticpump import PeristalticPump as PeristalticPumpDirect
from pyflowsheet.unitoperations.progressivecavitypump import (
    ProgressiveCavityPump as ProgressiveCavityPumpDirect,
)
from pyflowsheet.unitoperations.reciprocatingpump import (
    ReciprocatingPump as ReciprocatingPumpDirect,
)


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "motive_test.svg")
    return SvgContext(out_file)


def test_motive_imports():
    assert Blower is BlowerDirect
    assert PeristalticPump is PeristalticPumpDirect
    assert ProgressiveCavityPump is ProgressiveCavityPumpDirect
    assert ReciprocatingPump is ReciprocatingPumpDirect


def test_motive_ports():
    pcp = ProgressiveCavityPump("P-101", position=(10, 10), size=(60, 25))
    assert "In" in pcp.ports and "Out" in pcp.ports
    assert pcp.ports["In"].relativePosition == (0.0, 0.5)
    assert pcp.ports["In"].normal == (-1, 0)
    assert pcp.ports["Out"].relativePosition == (1.0, 0.5)
    assert pcp.ports["Out"].normal == (1, 0)
    assert pcp.ports["Out"].intent == "out"

    peri = PeristalticPump("P-102", position=(80, 10), size=(35, 35))
    assert "In" in peri.ports and "Out" in peri.ports
    assert peri.ports["In"].normal == (-1, 0)
    assert peri.ports["Out"].normal == (1, 0)
    assert peri.ports["Out"].intent == "out"

    recip = ReciprocatingPump("P-103", position=(130, 10), size=(45, 30))
    assert "In" in recip.ports and "Out" in recip.ports
    assert recip.ports["In"].normal == (-1, 0)
    assert recip.ports["Out"].normal == (1, 0)
    assert recip.ports["Out"].intent == "out"

    blower = Blower("B-101", position=(190, 10), size=(40, 40))
    assert "In" in blower.ports and "Out" in blower.ports
    assert blower.ports["In"].normal == (-1, 0)
    assert blower.ports["Out"].normal == (1, 0)
    assert blower.ports["Out"].intent == "out"


def test_description_forwarding():
    pcp = ProgressiveCavityPump("P1", "PC Pump", description="Progressive Cavity")
    assert pcp.description == "Progressive Cavity"

    peri = PeristalticPump("P2", "Hose Pump", description="Peristaltic Hose")
    assert peri.description == "Peristaltic Hose"

    recip = ReciprocatingPump("P3", "Piston Pump", description="Reciprocating Piston")
    assert recip.description == "Reciprocating Piston"

    blower = Blower("B1", "Blower", description="Centrifugal Blower")
    assert blower.description == "Centrifugal Blower"


def test_motive_drawing(svg_ctx):
    units = [
        ProgressiveCavityPump("P1", "PC Pump", position=(10, 10), size=(60, 25)),
        PeristalticPump("P2", "Hose Pump", position=(80, 10), size=(35, 35)),
        ReciprocatingPump("P3", "Piston Pump", position=(130, 10), size=(45, 30)),
        Blower("B1", "Centrifugal Blower", position=(190, 10), size=(40, 40)),
    ]
    for u in units:
        svg_ctx.startGroup(u.id)
        svg_ctx.startTransformedGroup(u)
        u.draw(svg_ctx)
        svg_ctx.endGroup()
        u.drawTextLayer(svg_ctx)
        svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    assert len(output) > 800


def test_motive_aliases():
    units = [
        ProgressiveCavityPump("P1"),
        PeristalticPump("P2"),
        ReciprocatingPump("P3"),
        Blower("B1"),
    ]
    for u in units:
        assert "Suction" in u.ports
        assert "Discharge" in u.ports
        assert u.ports["Suction"] is u.ports["In"]
        assert u.ports["Discharge"] is u.ports["Out"]
        assert u["Suction"] is u["In"]
        assert u["Discharge"] is u["Out"]


def test_motive_rotation_and_flip(svg_ctx):
    units = [
        ProgressiveCavityPump("P1", angle=90),
        PeristalticPump("P2", angle=180),
        ReciprocatingPump("P3", angle=270),
        Blower("B1", angle=45),
    ]
    for u in units:
        u.flip("horizontal")
        u.flip("vertical")
        svg_ctx.startGroup(u.id)
        svg_ctx.startTransformedGroup(u)
        u.draw(svg_ctx)
        svg_ctx.endGroup()
        u.drawTextLayer(svg_ctx)
        svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    assert len(output) > 800
