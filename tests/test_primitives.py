import pytest

from pyflowsheet.core.enums import HorizontalLabelAlignment, VerticalLabelAlignment
from pyflowsheet.core.port import Port
from pyflowsheet.core.unitoperation import UnitOperation


def test_port_position_and_relative_coordinates():
    unit = UnitOperation("U1", "Test Unit", position=(100, 200), size=(80, 40))
    port = Port("In1", unit, (0.0, 0.5), (-1, 0), intent="in")
    unit.addPort(port)

    # Relative (0.0, 0.5) on size (80, 40) at (100, 200) => (100 + 0, 200 + 20) = (100, 220)
    pos = port.get_position()
    assert pos == (100.0, 220.0)
    assert port.normal == (-1, 0)
    assert unit["In1"] == port


def test_unit_operation_flip_horizontal():
    unit = UnitOperation("U1", "Test Unit", position=(100, 200), size=(80, 40))
    port = Port("In1", unit, (0.2, 0.5), (-1, 0))
    unit.addPort(port)

    unit.flipHorizontal()
    assert unit.isFlippedHorizontal is True
    # Horizontally flipped relative x: 1 - 0.2 = 0.8
    assert pytest.approx(unit["In1"].relativePosition[0]) == 0.8
    assert unit["In1"].normal == (1, 0)


def test_unit_operation_flip_vertical():
    unit = UnitOperation("U1", "Test Unit", position=(100, 200), size=(80, 40))
    port = Port("In1", unit, (0.2, 0.3), (0, -1))
    unit.addPort(port)

    unit.flipVertical()
    assert unit.isFlippedVertical is True
    # Vertically flipped relative y: 1 - 0.3 = 0.7
    assert pytest.approx(unit["In1"].relativePosition[1]) == 0.7
    assert unit["In1"].normal == (0, 1)


def test_unit_operation_rotation():
    unit = UnitOperation("U1", "Test Unit", position=(100, 100), size=(40, 40))
    port = Port("Out", unit, (1.0, 0.5), (1, 0))
    unit.addPort(port)

    unit.rotate(90)
    assert unit.rotation == 90
    pos = port.get_position()
    # Rotated 90 degrees clockwise around center (120, 120):
    # Original point (140, 120) rotates to (120, 140)
    assert pytest.approx(pos[0], abs=1e-2) == 120.0
    assert pytest.approx(pos[1], abs=1e-2) == 140.0


def test_unit_operation_intersects_point():
    unit = UnitOperation("U1", "Test Unit", position=(100, 100), size=(50, 50))
    assert unit.intersectsPoint((110, 110)) is True
    assert unit.intersectsPoint((90, 110)) is False
    assert unit.intersectsPoint((160, 110)) is False


def test_text_anchor_calculation():
    unit = UnitOperation("U1", "Test Unit", position=(100, 200), size=(100, 60))
    unit.setTextAnchor(
        HorizontalLabelAlignment.Center, VerticalLabelAlignment.Bottom, offset=(0, 15)
    )
    anchor, align = unit.getTextAnchor()

    # Center x: 100 + 50 + 0 = 150
    # Bottom y: 200 + 60 + 15 = 275
    assert anchor == (150.0, 275.0)
    assert align == "middle"
