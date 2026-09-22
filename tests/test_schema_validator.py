import pytest

from pyflowsheet.schema.models import FlowsheetSchema
from pyflowsheet.schema.validator import (
    FlowsheetValidationError,
    validate_dict,
    validate_flowsheet_integrity,
    validate_yaml_file,
    validate_yaml_string,
)


def test_duplicate_component_id_detected():
    data = {
        "schema_version": "1.0",
        "components": {
            "equipment": [
                {"id": "V-101", "name": "Vessel 1", "type": "Vessel"},
                {"id": "V-101", "name": "Duplicate Vessel", "type": "Vessel"},
            ]
        },
    }
    schema = FlowsheetSchema.model_validate(data)
    errors = validate_flowsheet_integrity(schema)
    assert any("duplicate component id 'v-101'" in e.lower() for e in errors)


def test_duplicate_stream_id_detected():
    data = {
        "schema_version": "1.0",
        "components": {
            "equipment": [
                {"id": "V-101", "name": "Vessel 1", "type": "Vessel"},
                {"id": "V-102", "name": "Vessel 2", "type": "Vessel"},
            ]
        },
        "streams": [
            {
                "id": "S01",
                "from": {"unit": "V-101", "port": "Out"},
                "to": {"unit": "V-102", "port": "In"},
            },
            {
                "id": "S01",
                "from": {"unit": "V-101", "port": "Out"},
                "to": {"unit": "V-102", "port": "In"},
            },
        ],
    }
    schema = FlowsheetSchema.model_validate(data)
    errors = validate_flowsheet_integrity(schema)
    assert any("duplicate stream id 's01'" in e.lower() for e in errors)


def test_missing_stream_source_unit_detected():
    data = {
        "schema_version": "1.0",
        "components": {"equipment": [{"id": "V-102", "name": "Vessel 2", "type": "Vessel"}]},
        "streams": [
            {
                "id": "S01",
                "from": {"unit": "V-MISSING", "port": "Out"},
                "to": {"unit": "V-102", "port": "In"},
            }
        ],
    }
    schema = FlowsheetSchema.model_validate(data)
    errors = validate_flowsheet_integrity(schema)
    assert any(
        "stream 's01' references non-existent source unit 'v-missing'" in e.lower() for e in errors
    )


def test_missing_stream_target_unit_detected():
    data = {
        "schema_version": "1.0",
        "components": {"equipment": [{"id": "V-101", "name": "Vessel 1", "type": "Vessel"}]},
        "streams": [
            {
                "id": "S01",
                "from": {"unit": "V-101", "port": "Out"},
                "to": {"unit": "V-GHOST", "port": "In"},
            }
        ],
    }
    schema = FlowsheetSchema.model_validate(data)
    errors = validate_flowsheet_integrity(schema)
    msg = "stream 's01' references non-existent destination unit 'v-ghost'"
    assert any(msg in e.lower() for e in errors)


def test_undeclared_port_on_custom_ports_unit():
    data = {
        "schema_version": "1.0",
        "components": {
            "equipment": [
                {
                    "id": "V-101",
                    "type": "Vessel",
                    "ports": [
                        {
                            "id": "P_OUT",
                            "position": [1.0, 0.5],
                            "normal": [1.0, 0.0],
                            "intent": "out",
                        }
                    ],
                },
                {"id": "V-102", "type": "Vessel"},
            ]
        },
        "streams": [
            {
                "id": "S01",
                "from": {"unit": "V-101", "port": "NON_EXISTENT_PORT"},
                "to": {"unit": "V-102", "port": "In"},
            }
        ],
    }
    schema = FlowsheetSchema.model_validate(data)
    errors = validate_flowsheet_integrity(schema)
    assert any("port 'NON_EXISTENT_PORT' does not exist on unit 'V-101'" in e for e in errors)


def test_undeclared_destination_port_on_custom_ports_unit():
    data = {
        "schema_version": "1.0",
        "components": {
            "equipment": [
                {"id": "V-101", "type": "Vessel"},
                {
                    "id": "V-102",
                    "type": "Vessel",
                    "ports": [
                        {
                            "id": "P_IN",
                            "position": [0.0, 0.5],
                            "normal": [-1.0, 0.0],
                            "intent": "in",
                        }
                    ],
                },
            ]
        },
        "streams": [
            {
                "id": "S01",
                "from": {"unit": "V-101", "port": "Out"},
                "to": {"unit": "V-102", "port": "NON_EXISTENT_IN_PORT"},
            }
        ],
    }
    schema = FlowsheetSchema.model_validate(data)
    errors = validate_flowsheet_integrity(schema)
    assert any("port 'NON_EXISTENT_IN_PORT' does not exist on unit 'V-102'" in e for e in errors)


def test_validate_dict_valid_and_invalid():
    valid_data = {
        "schema_version": "1.0",
        "components": {
            "equipment": [
                {"id": "V1", "type": "Vessel"},
                {"id": "V2", "type": "Vessel"},
            ]
        },
        "streams": [
            {
                "id": "S1",
                "from": {"unit": "V1", "port": "Out"},
                "to": {"unit": "V2", "port": "In"},
            }
        ],
    }
    schema = validate_dict(valid_data)
    assert len(schema.components.equipment) == 2
    assert len(schema.streams) == 1

    # Schema parse error (e.g. invalid type for equipment)
    with pytest.raises(FlowsheetValidationError) as excinfo:
        validate_dict({"schema_version": "1.0", "components": {"equipment": "not-a-list"}})
    assert "Schema parse error" in str(excinfo.value)


def test_validate_yaml_string_raises_on_error():
    bad_yaml = """
schema_version: "1.0"
components:
  equipment:
    - id: "V1"
      type: "Vessel"
streams:
  - id: "S1"
    from: { unit: "V1", port: "Out" }
    to: { unit: "V2", port: "In" }
"""
    with pytest.raises(FlowsheetValidationError) as excinfo:
        validate_yaml_string(bad_yaml)
    assert "references non-existent destination unit 'V2'" in str(excinfo.value)


def test_validate_yaml_string_syntax_error():
    invalid_yaml = "foo: [bar: baz"
    with pytest.raises(FlowsheetValidationError) as excinfo:
        validate_yaml_string(invalid_yaml)
    assert "Invalid YAML syntax" in str(excinfo.value)


def test_validate_yaml_string_non_dict_root():
    scalar_yaml = "hello world"
    with pytest.raises(FlowsheetValidationError) as excinfo:
        validate_yaml_string(scalar_yaml)
    assert "Root YAML document must be a key-value mapping" in str(excinfo.value)


def test_validate_yaml_file_not_found():
    with pytest.raises(FileNotFoundError):
        validate_yaml_file("non_existent_file_xyz.yaml")


def test_valid_water_treatment_yaml_passes_validation():
    schema = validate_yaml_file("examples/water_treatment_flowsheet_v2.yaml")
    assert schema.metadata.id == "WATER_TREATMENT_V2"
    assert len(schema.components.equipment) == 4
    assert len(schema.streams) == 9
