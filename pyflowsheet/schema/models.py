from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

LineType = Literal["process", "pneumatic", "electric", "digital", "capillary"]
BalloonType = Literal["discrete", "shared_display", "computer_function", "plc"]
LocationModifier = Literal["field", "control_room", "behind_panel", "secondary"]
ActuatorType = Literal["manual", "pneumatic", "electric", "solenoid", "piston"]
FailureMode = Literal["none", "fail_closed", "fail_open", "fail_locked", "fail_indeterminate"]
HeadType = Literal["dished", "conical", "flat"]


class MetadataRevisionSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    rev: str
    description: str = ""
    zone: str = "-"
    date: str = ""
    approved_by: str = ""


class MetadataSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = "FLOWSHEET"
    name: str = "Process Flow Diagram"
    title: str | None = None
    subtitle: str | None = None
    description: str = ""
    drawing_number: str | None = None
    revision: str | None = None
    sheet_size: str | None = None
    scale: str | None = None
    sheet: str | None = None
    cage_code: str | None = None
    organization: str | None = None
    project: str | None = None
    contract_no: str | None = None
    status: str | None = None
    units: str | None = None
    projection: str = "THIRD ANGLE"
    code_standard: str = "ANSI/ASME Y14.1 / ISA-5.1"
    drawn_by: str | None = None
    drawn_date: str | None = None
    checked_by: str | None = None
    checked_date: str | None = None
    approved_by: str | None = None
    approved_date: str | None = None
    qa_by: str | None = None
    qa_date: str | None = None
    notes: list[str] = Field(default_factory=list)
    revisions: list[MetadataRevisionSchema] = Field(default_factory=list)


class DrawingFrameSettingsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = True
    sheet_size: str = "D"
    show_border: bool = True
    show_title_block: bool = True
    show_revision_block: bool = True
    show_legend: bool = True
    show_notes: bool = True
    custom_legend_entries: list[dict[str, Any]] = Field(default_factory=list)


class PortSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    position: tuple[float, float]
    normal: tuple[float, float]
    intent: Literal["in", "out"] = "in"
    description: str = ""


class InternalSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str


class TextAnchorSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    horizontal: Literal["Center", "Left", "Right", "LeftOuter", "RightOuter"] = "Center"
    vertical: Literal["Center", "Top", "Bottom"] = "Bottom"
    offset: tuple[float, float] = (0.0, 20.0)


class RelativeToSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    target: str
    direction: Literal["right", "left", "above", "below"] = "right"
    offset: float = 60.0


class AlignSchema(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    with_unit: str = Field(alias="with")
    axis: Literal["horizontal", "vertical"] = "horizontal"


class LayoutHintsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    stage: int | None = None
    flow_direction: Literal["right", "left", "down"] = "right"
    relative_to: RelativeToSchema | None = None
    align: AlignSchema | None = None


class EquipmentSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str | None = None
    type: str = "Vessel"
    description: str = ""
    position: tuple[float, float] = (0.0, 0.0)
    size: tuple[float, float] | None = None
    rotation: float = 0.0
    flip_horizontal: bool = False
    flip_vertical: bool = False
    fixed: bool = False
    cap_length: float | None = None
    valve_type: str | None = Field(
        default=None, description="Valve body type (globe, gate, ball, etc.)"
    )
    actuator: ActuatorType | None = Field(
        default=None, description="Actuator type for control valves"
    )
    failure_mode: FailureMode | None = Field(
        default=None, description="Actuator failure mode position"
    )
    tag: str | None = Field(
        default=None, description="ANSI/ISA-5.1 tag identifier (e.g. 'FIT-101')"
    )
    balloon_type: BalloonType | None = Field(
        default=None, description="Instrument balloon symbol type"
    )
    location: LocationModifier | None = Field(
        default=None, description="Instrument location modifier"
    )
    head_type: HeadType | None = Field(
        default=None, description="Vessel head type (dished, conical, flat)"
    )
    internals: list[InternalSchema] = Field(default_factory=list)
    ports: list[PortSchema] = Field(default_factory=list)
    text_anchor: TextAnchorSchema | None = None
    layout_hints: LayoutHintsSchema | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_layout_hints(cls, data: Any) -> Any:
        if isinstance(data, dict):
            hints_to_lift = ("relative_to", "align", "stage", "flow_direction")
            found = {k: data[k] for k in hints_to_lift if k in data}
            if found:
                hints = data.get("layout_hints")
                if hints is None:
                    data["layout_hints"] = found
                elif isinstance(hints, dict):
                    for k, v in found.items():
                        if k not in hints:
                            hints[k] = v
        return data

    def get_name(self) -> str:
        return self.name if self.name is not None else self.id


class StreamEndpointSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    unit: str
    port: str

    @model_validator(mode="before")
    @classmethod
    def _parse_endpoint(cls, data: Any) -> Any:
        if isinstance(data, str):
            if ":" in data:
                unit, port = data.split(":", 1)
                return {"unit": unit, "port": port}
            return {"unit": data, "port": ""}
        return data


class StreamAssociatedComponentsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    pumps: list[str] = Field(default_factory=list)
    valves: list[str] = Field(default_factory=list)
    instruments: list[str] = Field(default_factory=list)
    line_sequence: list[str] = Field(default_factory=list)


class StreamSchema(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    name: str | None = None
    description: str = ""
    from_endpoint: StreamEndpointSchema = Field(alias="from")
    to_endpoint: StreamEndpointSchema = Field(alias="to")
    line_type: LineType = Field(
        default="process",
        description=(
            "ANSI/ISA-5.1 line type ('process', 'pneumatic', 'electric', 'digital', 'capillary')"
        ),
    )
    manual_routing: list[tuple[float, float]] = Field(default_factory=list)
    label_offset: tuple[float, float] = (0.0, 10.0)
    associated_components: StreamAssociatedComponentsSchema | dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_endpoints(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "from_port" in data and "from" not in data and "from_endpoint" not in data:
                data["from"] = data.pop("from_port")
            if "to_port" in data and "to" not in data and "to_endpoint" not in data:
                data["to"] = data.pop("to_port")
        return data

    @property
    def from_port(self) -> str:
        return f"{self.from_endpoint.unit}:{self.from_endpoint.port}"

    @property
    def to_port(self) -> str:
        return f"{self.to_endpoint.unit}:{self.to_endpoint.port}"


class TableSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str | None = None
    position: tuple[float, float] = (0.0, 0.0)
    size: tuple[float, float] = (40.0, 20.0)
    columns: list[str] = Field(default_factory=list)
    data: list[list[Any]] = Field(default_factory=list)
    figsize: tuple[float, float] = (5.0, 5.0)


class ComponentsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    equipment: list[EquipmentSchema] = Field(default_factory=list)
    stream_flags: list[EquipmentSchema] = Field(default_factory=list)
    units: list[EquipmentSchema] = Field(default_factory=list)
    pumps: list[dict[str, Any]] = Field(default_factory=list)
    valves: list[dict[str, Any]] = Field(default_factory=list)
    instrumentation: list[dict[str, Any]] = Field(default_factory=list)

    def all_units(self) -> list[EquipmentSchema]:
        """Returns all drawable unit operation definitions aggregated across equipment,
        stream_flags, and units.
        """
        return list(self.equipment) + list(self.stream_flags) + list(self.units)


class FlowsheetSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: str = "1.0"
    metadata: MetadataSchema = Field(default_factory=MetadataSchema)
    components: ComponentsSchema = Field(default_factory=ComponentsSchema)
    equipment: list[EquipmentSchema] = Field(default_factory=list)
    streams: list[StreamSchema] = Field(default_factory=list)
    tables: list[TableSchema] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _sync_equipment(self) -> "FlowsheetSchema":
        if self.equipment and not self.components.equipment:
            self.components.equipment = list(self.equipment)
        elif self.components.equipment and not self.equipment:
            self.equipment = list(self.components.equipment)
        return self
