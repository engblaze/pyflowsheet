import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.valves.specialties import (
    GrabSamplingTee,
    RuptureDisc,
    SafetyReliefValve,
    SteamTrap,
    Strainer,
)


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "specialties_test.svg")
    return SvgContext(out_file)


def test_specialties_ports():
    # PSV: angle valve with inlet at bottom, outlet at right
    psv = SafetyReliefValve("PSV-101", position=(10, 10), size=(30, 30))
    assert "In" in psv.ports and "Out" in psv.ports
    assert psv.ports["In"].relativePosition == (0.5, 1.0)
    assert psv.ports["In"].normal == (0, 1)
    assert psv.ports["Out"].relativePosition == (1.0, 0.5)
    assert psv.ports["Out"].normal == (1, 0)

    # Rupture disc
    pse = RuptureDisc("PSE-102", position=(50, 10), size=(20, 20))
    assert "In" in pse.ports and "Out" in pse.ports
    assert pse.ports["In"].relativePosition == (0.0, 0.5)
    assert pse.ports["In"].normal == (-1, 0)
    assert pse.ports["Out"].relativePosition == (1.0, 0.5)
    assert pse.ports["Out"].normal == (1, 0)

    # Sampling tee: has In, Out, and Sample ports
    sample = GrabSamplingTee("SMP-103", position=(90, 10), size=(25, 25))
    assert "In" in sample.ports and "Out" in sample.ports and "Sample" in sample.ports
    assert sample.ports["In"].relativePosition == (0.0, 0.5)
    assert sample.ports["In"].normal == (-1, 0)
    assert sample.ports["Out"].relativePosition == (1.0, 0.5)
    assert sample.ports["Out"].normal == (1, 0)
    assert sample.ports["Sample"].relativePosition == (0.5, 1.0)
    assert sample.ports["Sample"].normal == (0, 1)

    # Strainer: has In, Out, and Blowdown ports
    strn = Strainer("STR-104", position=(130, 10), size=(30, 20))
    assert "In" in strn.ports and "Out" in strn.ports and "Blowdown" in strn.ports
    assert strn.ports["In"].relativePosition == (0.0, 0.5)
    assert strn.ports["In"].normal == (-1, 0)
    assert strn.ports["Out"].relativePosition == (1.0, 0.5)
    assert strn.ports["Out"].normal == (1, 0)
    assert strn.ports["Blowdown"].relativePosition == (0.75, 1.0)
    assert strn.ports["Blowdown"].normal == (0, 1)

    # Steam trap: has In and Out ports
    trap = SteamTrap("ST-105", position=(170, 10), size=(25, 25))
    assert "In" in trap.ports and "Out" in trap.ports
    assert trap.ports["In"].relativePosition == (0.0, 0.5)
    assert trap.ports["In"].normal == (-1, 0)
    assert trap.ports["Out"].relativePosition == (1.0, 0.5)
    assert trap.ports["Out"].normal == (1, 0)


def test_specialties_draw(svg_ctx):
    items = [
        SafetyReliefValve("PSV-101", position=(10, 50), size=(30, 30)),
        RuptureDisc("PSE-102", position=(60, 50), size=(20, 20)),
        GrabSamplingTee("SMP-103", position=(100, 50), size=(25, 25)),
        Strainer("STR-104", position=(140, 50), size=(30, 20)),
        SteamTrap("ST-105", position=(190, 50), size=(25, 25)),
    ]
    for it in items:
        svg_ctx.startGroup(it.id)
        svg_ctx.startTransformedGroup(it)
        it.draw(svg_ctx)
        svg_ctx.endGroup()
        it.drawTextLayer(svg_ctx)
        svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    assert len(output) > 800


def test_package_exports():
    from pyflowsheet.valves import (
        GrabSamplingTee as GST,
    )
    from pyflowsheet.valves import (
        RuptureDisc as RD,
    )
    from pyflowsheet.valves import (
        SafetyReliefValve as SRV,
    )
    from pyflowsheet.valves import (
        SteamTrap as ST,
    )
    from pyflowsheet.valves import (
        Strainer as S,
    )

    assert GST is GrabSamplingTee
    assert RD is RuptureDisc
    assert SRV is SafetyReliefValve
    assert ST is SteamTrap
    assert S is Strainer
