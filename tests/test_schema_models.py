import pytest
from pydantic import ValidationError

from pyflowsheet.schema.models import (
    ComponentsSchema,
    EquipmentSchema,
    FlowsheetSchema,
    InternalSchema,
    MetadataRevisionSchema,
    MetadataSchema,
    PortSchema,
    StreamAssociatedComponentsSchema,
    StreamEndpointSchema,
    StreamSchema,
    TableSchema,
    TextAnchorSchema,
)


def test_minimal_flowsheet_schema():
    data = {
        "schema_version": "1.0",
        "metadata": {
            "id": "MINIMAL_PFD",
            "name": "Minimal Flowsheet",
        },
        "components": {
            "equipment": [
                {
                    "id": "V-101",
                    "name": "Feed Vessel",
                    "type": "Vessel",
                    "position": [100.0, 150.0],
                    "size": [40.0, 80.0],
                }
            ]
        },
        "streams": [
            {
                "id": "S01",
                "from": {"unit": "V-101", "port": "Out"},
                "to": {"unit": "V-102", "port": "In"},
            }
        ],
    }
    schema = FlowsheetSchema.model_validate(data)
    assert schema.schema_version == "1.0"
    assert schema.metadata.id == "MINIMAL_PFD"
    assert len(schema.components.equipment) == 1
    assert schema.components.equipment[0].id == "V-101"
    assert schema.streams[0].from_endpoint.unit == "V-101"
    assert schema.streams[0].to_endpoint.port == "In"


def test_full_equipment_schema_with_ports_and_internals():
    eq_data = {
        "id": "MX-101",
        "name": "Stirred Mixer",
        "type": "Vessel",
        "position": [200.0, 200.0],
        "size": [60.0, 90.0],
        "cap_length": 15.0,
        "rotation": 90.0,
        "internals": [{"type": "Stirrer"}],
        "ports": [
            {
                "id": "In1",
                "position": [0.0, 0.5],
                "normal": [-1.0, 0.0],
                "intent": "in",
            }
        ],
        "text_anchor": {
            "horizontal": "Center",
            "vertical": "Bottom",
            "offset": [0.0, 25.0],
        },
    }
    eq = EquipmentSchema.model_validate(eq_data)
    assert eq.id == "MX-101"
    assert eq.get_name() == "Stirred Mixer"
    assert eq.cap_length == 15.0
    assert eq.internals[0].type == "Stirrer"
    assert eq.ports[0].id == "In1"
    assert eq.text_anchor.horizontal == "Center"


def test_equipment_schema_default_name():
    eq = EquipmentSchema.model_validate({"id": "E-101"})
    assert eq.id == "E-101"
    assert eq.name is None
    assert eq.get_name() == "E-101"


def test_table_schema_validation():
    tbl_data = {
        "id": "TBL-01",
        "name": "Stream Data Table",
        "position": [500.0, 50.0],
        "size": [300.0, 150.0],
        "columns": ["Stream", "Temp [C]", "Pressure [bar]"],
        "data": [
            ["S01", 25.0, 1.0],
            ["S02", 85.0, 4.2],
        ],
    }
    tbl = TableSchema.model_validate(tbl_data)
    assert tbl.id == "TBL-01"
    assert len(tbl.columns) == 3
    assert len(tbl.data) == 2


def test_components_schema_aggregation():
    comp_data = {
        "equipment": [{"id": "E1", "name": "Eq1", "type": "Vessel"}],
        "stream_flags": [{"id": "F1", "name": "Feed", "type": "StreamFlag"}],
        "units": [{"id": "U1", "name": "Unit1"}],
        "pumps": [{"id": "P1", "name": "Pump1"}],
        "valves": [{"id": "V1", "name": "Valve1"}],
        "instrumentation": [{"tag": "FIT-101", "name": "Flow Transmitter"}],
    }
    comps = ComponentsSchema.model_validate(comp_data)
    all_units = comps.all_units()
    assert len(all_units) == 3
    assert {u.id for u in all_units} == {"E1", "F1", "U1"}


def test_metadata_and_revisions():
    meta_data = {
        "id": "TEST_ID",
        "name": "Test Diagram",
        "revisions": [{"rev": "A", "description": "Initial draft", "date": "2026-09-22"}],
    }
    meta = MetadataSchema.model_validate(meta_data)
    assert meta.id == "TEST_ID"
    assert len(meta.revisions) == 1
    assert meta.revisions[0].rev == "A"
    assert meta.revisions[0].zone == "-"


def test_stream_schema_associated_components():
    stream_data = {
        "id": "S10",
        "from": {"unit": "E1", "port": "Out"},
        "to": {"unit": "E2", "port": "In"},
        "associated_components": {
            "pumps": ["P-101"],
            "valves": ["V-101"],
            "instruments": ["TI-101"],
            "line_sequence": ["P-101", "V-101"],
        },
    }
    st = StreamSchema.model_validate(stream_data)
    assert isinstance(st.associated_components, StreamAssociatedComponentsSchema)
    assert st.associated_components.pumps == ["P-101"]
    assert st.associated_components.line_sequence == ["P-101", "V-101"]


def test_direct_submodel_instantiation():
    rev = MetadataRevisionSchema(rev="0")
    assert rev.rev == "0"
    assert rev.zone == "-"

    port = PortSchema(id="In", position=(0.0, 0.5), normal=(-1.0, 0.0), intent="in")
    assert port.id == "In"
    assert port.intent == "in"

    internal = InternalSchema(type="Baffles")
    assert internal.type == "Baffles"

    anchor = TextAnchorSchema(horizontal="Left", vertical="Top", offset=(5.0, 5.0))
    assert anchor.horizontal == "Left"

    endpoint = StreamEndpointSchema(unit="U1", port="Out")
    assert endpoint.unit == "U1"
    assert endpoint.port == "Out"


def test_schema_validation_errors():
    with pytest.raises(ValidationError):
        # Port with invalid intent
        PortSchema.model_validate(
            {"id": "P1", "position": [0, 0], "normal": [1, 0], "intent": "invalid"}
        )

    with pytest.raises(ValidationError):
        # TextAnchor with invalid horizontal
        TextAnchorSchema.model_validate({"horizontal": "Diagonal"})

    with pytest.raises(ValidationError):
        # Stream missing required 'from' endpoint
        StreamSchema.model_validate({"id": "S1", "to": {"unit": "U1", "port": "In"}})


def test_schema_module_reexports_layout_models():
    import pyflowsheet.schema as ps

    assert hasattr(ps, "LayoutHintsSchema")
    assert hasattr(ps, "RelativeToSchema")
    assert hasattr(ps, "AlignSchema")
    assert "LayoutHintsSchema" in ps.__all__
    assert "RelativeToSchema" in ps.__all__
    assert "AlignSchema" in ps.__all__

    rel = ps.RelativeToSchema(target="TK-1", direction="below", offset=40.0)
    assert rel.target == "TK-1"
    align = ps.AlignSchema(**{"with": "TK-1", "axis": "vertical"})
    assert align.with_unit == "TK-1"
    hints = ps.LayoutHintsSchema(relative_to=rel, align=align)
    assert hints.relative_to == rel
    assert hints.align == align
