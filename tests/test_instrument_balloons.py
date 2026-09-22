import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.instruments.balloon import Instrument
from pyflowsheet.instruments.tag import ISATag


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "instrument_test.svg")
    return SvgContext(out_file)


def test_instrument_defaults_and_ports():
    inst = Instrument("FIT-101", tag="FIT-101", position=(50, 50), size=(28, 28))
    assert inst.tag.display_top == "FIT"
    assert inst.tag.display_bottom == "101"
    assert inst.balloon_type == "discrete"
    assert inst.location == "field"

    # Orthogonal ports
    assert "In" in inst.ports
    assert "Out" in inst.ports
    assert "Top" in inst.ports
    assert "Bottom" in inst.ports
    assert inst.ports["In"].relativePosition == (0, 0.5)
    assert inst.ports["Out"].relativePosition == (1, 0.5)
    assert inst.ports["Top"].relativePosition == (0.5, 0)
    assert inst.ports["Bottom"].relativePosition == (0.5, 1)

    # Directional aliases
    assert inst.ports["West"] is inst.ports["In"]
    assert inst.ports["East"] is inst.ports["Out"]
    assert inst.ports["North"] is inst.ports["Top"]
    assert inst.ports["South"] is inst.ports["Bottom"]


def test_instrument_drawing_all_types(svg_ctx):
    balloons = [
        Instrument(
            "I1", tag="FIT-101", balloon_type="discrete", location="field", position=(10, 10)
        ),
        Instrument(
            "I2", tag="LIC-102", balloon_type="discrete", location="control_room", position=(60, 10)
        ),
        Instrument(
            "I3",
            tag="PIC-103",
            balloon_type="discrete",
            location="behind_panel",
            position=(110, 10),
        ),
        Instrument(
            "I4", tag="TIC-104", balloon_type="discrete", location="secondary", position=(160, 10)
        ),
        Instrument(
            "I5",
            tag="DCS-105",
            balloon_type="shared_display",
            location="control_room",
            position=(210, 10),
        ),
        Instrument("I6", tag="PLC-106", balloon_type="plc", location="field", position=(260, 10)),
        Instrument(
            "I7",
            tag="CMP-107",
            balloon_type="computer_function",
            location="control_room",
            position=(310, 10),
        ),
    ]

    for inst in balloons:
        svg_ctx.startGroup(inst.id)
        svg_ctx.startTransformedGroup(inst)
        inst.draw(svg_ctx)
        svg_ctx.endGroup()
        inst.drawTextLayer(svg_ctx)
        svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    assert "FIT" in output
    assert "101" in output
    assert "DCS" in output


def test_instrument_tag_as_isatag_or_id_default():
    tag_obj = ISATag(raw="TIC-300", letters="TIC", loop_number="300")
    inst1 = Instrument("inst1", tag=tag_obj)
    assert inst1.tag is tag_obj
    assert inst1.tag.display_top == "TIC"
    assert inst1.tag.display_bottom == "300"

    inst2 = Instrument("PIC-400")
    assert inst2.tag.display_top == "PIC"
    assert inst2.tag.display_bottom == "400"


def test_instrument_location_lines_and_ports_rendering(svg_ctx):
    inst = Instrument(
        "PIC-103",
        tag="PIC-103",
        balloon_type="discrete",
        location="behind_panel",
        position=(10, 10),
    )
    svg_ctx.startGroup(inst.id)
    svg_ctx.startTransformedGroup(inst)
    inst.draw(svg_ctx)
    svg_ctx.endGroup()
    inst.drawTextLayer(svg_ctx, showPorts=True)
    svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    # stroke-dasharray is rendered for behind_panel
    assert "stroke-dasharray" in output
    assert "PIC" in output
    assert "103" in output
