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


def test_grab_sampling_tee_orientation():
    from pyflowsheet.core import Flowsheet

    # Default orientation is down
    tee_down = GrabSamplingTee("SMP-DN", position=(10, 10), size=(16, 48))
    assert tee_down.isFlippedVertical is False
    assert tee_down.ports["Sample"].relativePosition == (0.5, 1.0)
    assert tee_down.ports["Sample"].normal == (0, 1)

    # Orientation up via constructor argument
    tee_up = GrabSamplingTee("SMP-UP", position=(10, 10), size=(16, 48), orientation="up")
    assert tee_up.isFlippedVertical is True
    assert tee_up.ports["Sample"].relativePosition == (0.5, 0.0)
    assert tee_up.ports["Sample"].normal == (0, -1)
    assert tee_up.ports["In"].relativePosition == (0.0, 0.5)
    assert tee_up.ports["Out"].relativePosition == (1.0, 0.5)

    # Orientation up via flipVertical method
    tee_flipped = GrabSamplingTee("SMP-FLIP", position=(10, 10), size=(16, 48))
    tee_flipped.flipVertical()
    assert tee_flipped.isFlippedVertical is True
    assert tee_flipped.ports["Sample"].relativePosition == (0.5, 0.0)
    assert tee_flipped.ports["Sample"].normal == (0, -1)

    # Flowsheet YAML with orientation: "up"
    yaml_orientation = """
flowsheet:
  id: test_smp_orient
  name: Test Sampling Orientation
equipment:
  - id: V-SMP-UP
    type: GrabSamplingTee
    position: [100, 100]
    size: [14, 48]
    orientation: "up"
streams: []
"""
    fs_orient = Flowsheet.from_yaml(yaml_orientation)
    unit_orient = fs_orient.unitOperations["V-SMP-UP"]
    assert unit_orient.isFlippedVertical is True
    assert unit_orient.ports["Sample"].relativePosition == (0.5, 0.0)
    assert unit_orient.ports["Sample"].normal == (0, -1)

    # Flowsheet YAML with standard flip_vertical: true
    yaml_flip = """
flowsheet:
  id: test_smp_flip
  name: Test Sampling Flip
equipment:
  - id: V-SMP-FLIP
    type: GrabSamplingTee
    position: [100, 100]
    size: [14, 48]
    flip_vertical: true
streams: []
"""
    fs_flip = Flowsheet.from_yaml(yaml_flip)
    unit_flip = fs_flip.unitOperations["V-SMP-FLIP"]
    assert unit_flip.isFlippedVertical is True
    assert unit_flip.ports["Sample"].relativePosition == (0.5, 0.0)
    assert unit_flip.ports["Sample"].normal == (0, -1)
