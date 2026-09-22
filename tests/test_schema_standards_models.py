import pytest
from pydantic import ValidationError

from pyflowsheet.schema.models import (
    EquipmentSchema,
    FlowsheetSchema,
    StreamSchema,
)


def test_stream_schema_line_types():
    # Default is process
    s_default = StreamSchema(id="S1", from_port="V1:Out", to_port="V2:In")
    assert s_default.line_type == "process"

    # Supported signal line types
    for lt in ["process", "pneumatic", "electric", "digital", "capillary"]:
        s = StreamSchema(id="S1", from_port="V1:Out", to_port="V2:In", line_type=lt)
        assert s.line_type == lt

    # Invalid line type
    with pytest.raises(ValidationError):
        StreamSchema(id="S1", from_port="V1:Out", to_port="V2:In", line_type="hydraulic_invalid")


def test_equipment_schema_standards_attributes():
    # Valve configuration
    valve_data = {
        "id": "CV-101",
        "type": "ControlValve",
        "valve_type": "globe",
        "actuator": "pneumatic",
        "failure_mode": "fail_closed",
    }
    eq_valve = EquipmentSchema.model_validate(valve_data)
    assert eq_valve.valve_type == "globe"
    assert eq_valve.actuator == "pneumatic"
    assert eq_valve.failure_mode == "fail_closed"

    # Instrument configuration
    inst_data = {
        "id": "FIT-101",
        "type": "Instrument",
        "tag": "FIT-101",
        "balloon_type": "discrete",
        "location": "field",
    }
    eq_inst = EquipmentSchema.model_validate(inst_data)
    assert eq_inst.tag == "FIT-101"
    assert eq_inst.balloon_type == "discrete"
    assert eq_inst.location == "field"

    # Vessel head type
    vessel_data = {
        "id": "V-101",
        "type": "Vessel",
        "head_type": "conical",
    }
    eq_vessel = EquipmentSchema.model_validate(vessel_data)
    assert eq_vessel.head_type == "conical"


def test_flowsheet_schema_roundtrip_with_standards():
    raw = {
        "metadata": {"title": "P&ID Flowsheet", "version": "1.0"},
        "equipment": [
            {
                "id": "PCV-102",
                "type": "ControlValve",
                "valve_type": "globe",
                "actuator": "pneumatic",
                "failure_mode": "fail_open",
                "position": [100.0, 100.0],
            },
            {
                "id": "PIT-102",
                "type": "Instrument",
                "tag": "PIT-102",
                "balloon_type": "shared_display",
                "location": "control_room",
                "position": [100.0, 50.0],
            },
        ],
        "streams": [
            {
                "id": "SIG-1",
                "from": "PIT-102:Out",
                "to": "PCV-102:Actuator",
                "line_type": "pneumatic",
            }
        ],
    }
    model = FlowsheetSchema.model_validate(raw)
    assert model.equipment[0].actuator == "pneumatic"
    assert model.equipment[1].location == "control_room"
    assert model.streams[0].line_type == "pneumatic"
    dumped = model.model_dump(by_alias=True, exclude_none=True)
    assert dumped["streams"][0]["line_type"] == "pneumatic"
