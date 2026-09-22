import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.internals import Stirrer
from pyflowsheet.unitoperations import (
    HorizontalSettler,
    HorizontalVessel,
    JacketedVessel,
    Vessel,
)


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "vessels_test.svg")
    return SvgContext(out_file)


def test_vessel_head_types():
    v_default = Vessel("V0", "Default")
    assert v_default.head_type == "dished"

    v_dished = Vessel("V1", "Dished", head_type="dished")
    v_conical = Vessel("V2", "Conical", head_type="conical")
    v_flat = Vessel("V3", "Flat", head_type="flat")
    assert v_dished.head_type == "dished"
    assert v_conical.head_type == "conical"
    assert v_flat.head_type == "flat"

    with pytest.raises(ValueError, match="Unknown head_type"):
        Vessel("V4", "Invalid", head_type="torispherical_unsupported")


def test_vessel_backward_compatibility():
    # Test positional parameters: id, name, position, size, description,
    # capLength, internals, angle, showCapLines
    v = Vessel("V_LEGACY", "Legacy Vessel", (10, 20), (50, 120), "Description", 15, [], 0, False)
    assert v.id == "V_LEGACY"
    assert v.position == (10, 20)
    assert v.size == (50, 120)
    assert v.capLength == 15
    assert v.showCapLines is False
    assert v.head_type == "dished"
    assert "In" in v.ports
    assert "Out" in v.ports


def test_horizontal_vessel_and_ports():
    hv = HorizontalVessel("HV-101", "Storage Bullet", position=(10, 10), size=(100, 40))
    assert "In" in hv.ports
    assert "Out" in hv.ports
    assert "Top" in hv.ports
    assert "Bottom" in hv.ports

    assert hv.ports["In"].relativePosition == (0, 0.5)
    assert hv.ports["In"].normal == (-1, 0)
    assert hv.ports["Out"].relativePosition == (1, 0.5)
    assert hv.ports["Out"].normal == (1, 0)
    assert hv.ports["Out"].intent == "out"
    assert hv.ports["Top"].relativePosition == (0.5, 0)
    assert hv.ports["Top"].normal == (0, -1)
    assert hv.ports["Bottom"].relativePosition == (0.5, 1)
    assert hv.ports["Bottom"].normal == (0, 1)


def test_horizontal_settler_ports():
    hs = HorizontalSettler("S-101", "Oil Water Separator", position=(10, 10), size=(120, 50))
    assert "Feed" in hs.ports
    assert "LightOut" in hs.ports
    assert "HeavyOut" in hs.ports
    assert "Vent" in hs.ports

    assert hs.ports["Feed"].relativePosition == (0, 0.5)
    assert hs.ports["Feed"].normal == (-1, 0)
    assert hs.ports["Vent"].relativePosition == (0.5, 0)
    assert hs.ports["Vent"].normal == (0, -1)
    assert hs.ports["HeavyOut"].relativePosition == (0.35, 1)
    assert hs.ports["HeavyOut"].normal == (0, 1)
    assert hs.ports["LightOut"].relativePosition == (1, 0.5)
    assert hs.ports["LightOut"].normal == (1, 0)

    # Test port aliases
    assert hs["In"] == hs["Feed"]
    assert hs["Out"] == hs["LightOut"]
    assert hs["Top"] == hs["Vent"]
    assert hs["Bottom"] == hs["HeavyOut"]


def test_jacketed_vessel_ports():
    jv = JacketedVessel("R-101", "Jacketed Reactor", position=(10, 10), size=(60, 100))
    assert "In" in jv.ports
    assert "Out" in jv.ports
    assert "JIn" in jv.ports
    assert "JOut" in jv.ports

    assert jv.ports["In"].relativePosition == (0.5, 0)
    assert jv.ports["In"].normal == (0, -1)
    assert jv.ports["Out"].relativePosition == (0.5, 1)
    assert jv.ports["Out"].normal == (0, 1)
    assert jv.ports["JIn"].relativePosition == (0, 0.75)
    assert jv.ports["JIn"].normal == (-1, 0)
    assert jv.ports["JOut"].relativePosition == (1, 0.35)
    assert jv.ports["JOut"].normal == (1, 0)

    # Test port aliases
    assert jv["Top"] == jv["In"]
    assert jv["Bottom"] == jv["Out"]
    assert jv["JacketIn"] == jv["JIn"]
    assert jv["JacketOut"] == jv["JOut"]


def test_internals_and_transformations(svg_ctx):
    reactor = JacketedVessel(
        "R-102",
        "Stirred Jacketed Reactor",
        position=(50, 50),
        size=(60, 120),
        internals=[Stirrer()],
    )
    assert len(reactor.internals) == 1

    svg_ctx.startGroup(reactor.id)
    reactor.draw(svg_ctx)
    svg_ctx.endGroup()

    hv = HorizontalVessel("HV-102", "Rotated Bullet", position=(10, 10), size=(80, 30), angle=90)
    assert hv.rotation == 90

    output = svg_ctx.render(saveFile=False)
    assert len(output) > 500


def test_vessels_drawing(svg_ctx):
    units = [
        Vessel("V1", "Conical", head_type="conical", position=(10, 10), size=(40, 90)),
        Vessel("V2", "Flat", head_type="flat", position=(70, 10), size=(40, 90)),
        HorizontalVessel("HV1", "Bullet", position=(130, 30), size=(90, 40)),
        HorizontalSettler("HS1", "Settler", position=(240, 30), size=(100, 45)),
        JacketedVessel("JV1", "Reactor", position=(360, 10), size=(50, 90)),
    ]
    for u in units:
        svg_ctx.startGroup(u.id)
        svg_ctx.startTransformedGroup(u)
        u.draw(svg_ctx)
        svg_ctx.endGroup()
        u.drawTextLayer(svg_ctx)
        svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    assert len(output) > 1000
