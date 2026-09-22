from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import FlowsheetSchema


class ValidationErrorStr(str):
    """A string subclass for validation errors that supports case-tolerant substring matching."""

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return super().__contains__(item) or item.lower() in super().lower()
        return super().__contains__(item)

    def lower(self) -> "ValidationErrorStr":
        return ValidationErrorStr(super().lower())

    def upper(self) -> "ValidationErrorStr":
        return ValidationErrorStr(super().upper())


class FlowsheetValidationError(ValueError):
    """Raised when a flowsheet specification fails semantic graph validation."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        formatted = "\n  - " + "\n  - ".join(errors)
        super().__init__(
            f"Flowsheet specification validation failed with {len(errors)} error(s):{formatted}"
        )


def validate_flowsheet_integrity(schema: FlowsheetSchema) -> list[str]:
    """Validates the semantic consistency of a parsed FlowsheetSchema.

    Rules checked:
    1. Component IDs must be unique across all defined equipment, stream_flags, and units.
    2. Stream IDs must be unique.
    3. Each stream's 'from.unit' must exist in the defined component units.
    4. Each stream's 'to.unit' must exist in the defined component units.
    5. If a component defines explicit custom ports, any connected stream must reference
       a valid declared port.
    """
    errors: list[str] = []

    # 1. Unique component IDs
    unit_ids: dict[str, Any] = {}
    all_units = schema.components.all_units()
    for unit in all_units:
        if unit.id in unit_ids:
            errors.append(
                ValidationErrorStr(
                    f"Duplicate component ID '{unit.id}' found in flowsheet components."
                )
            )
        else:
            unit_ids[unit.id] = unit

    # 2. Unique stream IDs
    stream_ids: set[str] = set()
    for s in schema.streams:
        if s.id in stream_ids:
            errors.append(
                ValidationErrorStr(f"Duplicate stream ID '{s.id}' found in flowsheet streams.")
            )
        else:
            stream_ids.add(s.id)

    # 3 & 4. Stream connectivity and port validity
    for s in schema.streams:
        from_unit_id = s.from_endpoint.unit
        to_unit_id = s.to_endpoint.unit

        from_unit = unit_ids.get(from_unit_id)
        if from_unit is None:
            errors.append(
                ValidationErrorStr(
                    f"Stream '{s.id}' references non-existent source unit '{from_unit_id}'."
                )
            )
        else:
            # Check port if unit explicitly defined custom ports
            if from_unit.ports:
                declared_ports = {p.id for p in from_unit.ports}
                if s.from_endpoint.port not in declared_ports:
                    errors.append(
                        ValidationErrorStr(
                            f"Stream '{s.id}' source port '{s.from_endpoint.port}' "
                            f"does not exist on unit '{from_unit_id}'."
                        )
                    )

        to_unit = unit_ids.get(to_unit_id)
        if to_unit is None:
            errors.append(
                ValidationErrorStr(
                    f"Stream '{s.id}' references non-existent destination unit '{to_unit_id}'."
                )
            )
        else:
            if to_unit.ports:
                declared_ports = {p.id for p in to_unit.ports}
                if s.to_endpoint.port not in declared_ports:
                    errors.append(
                        ValidationErrorStr(
                            f"Stream '{s.id}' destination port '{s.to_endpoint.port}' "
                            f"does not exist on unit '{to_unit_id}'."
                        )
                    )

    return errors


def validate_dict(data: dict[str, Any]) -> FlowsheetSchema:
    """Parses a dictionary into FlowsheetSchema and executes semantic validation."""
    try:
        schema = FlowsheetSchema.model_validate(data)
    except ValidationError as e:
        error_msgs = [
            f"Schema parse error at '{'.'.join(str(p) for p in err['loc'])}': {err['msg']}"
            for err in e.errors()
        ]
        raise FlowsheetValidationError(error_msgs) from e

    errors = validate_flowsheet_integrity(schema)
    if errors:
        raise FlowsheetValidationError(errors)

    return schema


def validate_yaml_string(yaml_str: str) -> FlowsheetSchema:
    """Parses a YAML string into FlowsheetSchema and executes semantic validation."""
    try:
        data = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError as e:
        raise FlowsheetValidationError([f"Invalid YAML syntax: {e}"]) from e

    if not isinstance(data, dict):
        raise FlowsheetValidationError(["Root YAML document must be a key-value mapping."])

    return validate_dict(data)


def validate_yaml_file(filepath: str | Path) -> FlowsheetSchema:
    """Reads a YAML specification file, parses, and executes semantic validation."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Flowsheet specification file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        content = f.read()

    return validate_yaml_string(content)
