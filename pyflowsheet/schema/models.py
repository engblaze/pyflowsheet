from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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
    organization: str | None = None
    project: str | None = None
    status: str | None = None
    units: str | None = None
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


class EquipmentSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str | None = None
    type: str = "Vessel"
    description: str = ""
    position: tuple[float, float] = (0.0, 0.0)
    size: tuple[float, float] = (40.0, 40.0)
    rotation: float = 0.0
    flip_horizontal: bool = False
    flip_vertical: bool = False
    cap_length: float | None = None
    internals: list[InternalSchema] = Field(default_factory=list)
    ports: list[PortSchema] = Field(default_factory=list)
    text_anchor: TextAnchorSchema | None = None

    def get_name(self) -> str:
        return self.name if self.name is not None else self.id


class StreamEndpointSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    unit: str
    port: str


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
    manual_routing: list[tuple[float, float]] = Field(default_factory=list)
    label_offset: tuple[float, float] = (0.0, 10.0)
    associated_components: StreamAssociatedComponentsSchema | dict[str, Any] | None = None


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
    streams: list[StreamSchema] = Field(default_factory=list)
    tables: list[TableSchema] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)
