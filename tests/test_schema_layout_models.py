import pytest
from pydantic import ValidationError

from pyflowsheet.schema.models import (
    AlignSchema,
    EquipmentSchema,
    FlowsheetSchema,
    LayoutHintsSchema,
    RelativeToSchema,
)


def test_layout_hints_schema_defaults():
    hints = LayoutHintsSchema()
    assert hints.stage is None
    assert hints.flow_direction == "right"
    assert hints.relative_to is None
    assert hints.align is None


def test_layout_hints_parsing_relative_and_align():
    data = {
        "id": "V-101",
        "type": "Vessel",
        "layout_hints": {
            "stage": 2,
            "flow_direction": "down",
            "relative_to": {
                "target": "V-100",
                "direction": "right",
                "offset": 80.0,
            },
            "align": {
                "with": "V-100",
                "axis": "horizontal",
            },
        },
    }
    eq = EquipmentSchema.model_validate(data)
    assert eq.layout_hints is not None
    assert eq.layout_hints.stage == 2
    assert eq.layout_hints.flow_direction == "down"
    assert isinstance(eq.layout_hints.relative_to, RelativeToSchema)
    assert eq.layout_hints.relative_to.target == "V-100"
    assert eq.layout_hints.relative_to.direction == "right"
    assert eq.layout_hints.relative_to.offset == 80.0
    assert isinstance(eq.layout_hints.align, AlignSchema)
    assert eq.layout_hints.align.with_unit == "V-100"
    assert eq.layout_hints.align.axis == "horizontal"


def test_layout_hints_invalid_flow_direction():
    with pytest.raises(ValidationError):
        LayoutHintsSchema(flow_direction="diagonal")


def test_flowsheet_schema_roundtrip_with_layout_hints():
    raw = {
        "metadata": {"id": "TEST_FS"},
        "components": {
            "equipment": [
                {
                    "id": "P-101",
                    "type": "Pump",
                    "layout_hints": {
                        "stage": 1,
                        "relative_to": {"target": "TK-101", "direction": "below"},
                    },
                }
            ]
        },
    }
    schema = FlowsheetSchema.model_validate(raw)
    assert schema.components.equipment[0].layout_hints.stage == 1
    dumped = schema.model_dump(by_alias=True)
    assert dumped["components"]["equipment"][0]["layout_hints"]["stage"] == 1
