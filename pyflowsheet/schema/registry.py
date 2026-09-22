from inspect import Parameter, signature
from typing import Any

from ..core import Port, UnitOperation
from ..core.enums import HorizontalLabelAlignment, VerticalLabelAlignment
from ..internals import (
    Baffles,
    CatalystBed,
    DiscDonutBaffles,
    DividingWall,
    Jacket,
    LiquidRing,
    RandomPacking,
    Reciprocating,
    Stirrer,
    Trays,
    Tubes,
)
from ..internals.baseinternal import BaseInternal
from ..unitoperations import (
    BlackBox,
    Compressor,
    Distillation,
    HeatExchanger,
    Mixer,
    PlateHex,
    Pump,
    Splitter,
    StreamFlag,
    Valve,
    Vessel,
)
from .models import EquipmentSchema, InternalSchema

UNIT_REGISTRY: dict[str, type[UnitOperation]] = {
    "BlackBox": BlackBox,
    "Compressor": Compressor,
    "Distillation": Distillation,
    "DistillationColumn": Distillation,
    "HeatExchanger": HeatExchanger,
    "Mixer": Mixer,
    "PlateHex": PlateHex,
    "Pump": Pump,
    "Splitter": Splitter,
    "StreamFlag": StreamFlag,
    "Valve": Valve,
    "Vessel": Vessel,
}

INTERNAL_REGISTRY: dict[str, type[BaseInternal]] = {
    "Baffles": Baffles,
    "CatalystBed": CatalystBed,
    "DiscDonutBaffles": DiscDonutBaffles,
    "DividingWall": DividingWall,
    "Jacket": Jacket,
    "LiquidRing": LiquidRing,
    "RandomPacking": RandomPacking,
    "Reciprocating": Reciprocating,
    "Stirrer": Stirrer,
    "Trays": Trays,
    "Tubes": Tubes,
}

ALIGNMENT_MAP_H: dict[str, HorizontalLabelAlignment] = {
    "Center": HorizontalLabelAlignment.Center,
    "Left": HorizontalLabelAlignment.Left,
    "Right": HorizontalLabelAlignment.Right,
    "LeftOuter": HorizontalLabelAlignment.LeftOuter,
    "RightOuter": HorizontalLabelAlignment.RightOuter,
}

ALIGNMENT_MAP_V: dict[str, VerticalLabelAlignment] = {
    "Center": VerticalLabelAlignment.Center,
    "Top": VerticalLabelAlignment.Top,
    "Bottom": VerticalLabelAlignment.Bottom,
}


def register_unit_type(name: str, cls: type[UnitOperation]) -> None:
    """Registers or overrides a UnitOperation type for schema deserialization."""
    UNIT_REGISTRY[name] = cls


def register_internal_type(name: str, cls: type[BaseInternal]) -> None:
    """Registers or overrides an internal type for schema deserialization."""
    INTERNAL_REGISTRY[name] = cls


def instantiate_internal(internal_schema: InternalSchema) -> BaseInternal:
    """Creates an internal instance (e.g. Stirrer, Tubes) from its schema."""
    itype = internal_schema.type
    cls = INTERNAL_REGISTRY.get(itype)
    if cls is None:
        raise ValueError(
            f"Unknown internal type '{itype}'. Registered types: {list(INTERNAL_REGISTRY.keys())}"
        )

    extra = internal_schema.model_extra or {}
    if itype == "Tubes":
        tubes_count = extra.get("tubes", extra.get("numberOfTubes", 4))
        return Tubes(tubes=tubes_count)
    if itype == "RandomPacking":
        start = extra.get("start", 0.0)
        end = extra.get("end", 1.0)
        return RandomPacking(start=start, end=end)
    if itype == "Trays":
        start = extra.get("start", 0.0)
        end = extra.get("end", 1.0)
        num_trays = extra.get("num_trays", extra.get("numberOfTrays", 10))
        return Trays(start=start, end=end, numberOfTrays=num_trays)

    return cls()


def instantiate_unit(eq: EquipmentSchema) -> UnitOperation:
    """Instantiates and configures a UnitOperation from an EquipmentSchema."""
    cls = UNIT_REGISTRY.get(eq.type)
    if cls is None:
        raise ValueError(
            f"Unknown unit operation type '{eq.type}'. "
            f"Registered types: {list(UNIT_REGISTRY.keys())}"
        )

    internals = [instantiate_internal(i) for i in eq.internals]

    # Specific kwargs handling per unit operation type
    kwargs: dict[str, Any] = {
        "id": eq.id,
        "name": eq.get_name(),
        "position": eq.position,
        "size": eq.size,
        "description": eq.description,
    }

    if eq.type == "Vessel":
        if eq.cap_length is not None:
            kwargs["capLength"] = eq.cap_length
        kwargs["internals"] = internals
    elif eq.type in ("Compressor", "Pump"):
        kwargs["internals"] = internals
    elif eq.type == "Distillation":
        kwargs["internals"] = internals
        if eq.model_extra:
            if "has_condenser" in eq.model_extra:
                kwargs["hasCondenser"] = eq.model_extra["has_condenser"]
            elif "hasCondenser" in eq.model_extra:
                kwargs["hasCondenser"] = eq.model_extra["hasCondenser"]
            if "has_reboiler" in eq.model_extra:
                kwargs["hasReboiler"] = eq.model_extra["has_reboiler"]
            elif "hasReboiler" in eq.model_extra:
                kwargs["hasReboiler"] = eq.model_extra["hasReboiler"]
    else:
        init_params = signature(cls.__init__).parameters
        has_internals_param = "internals" in init_params or any(
            p.kind == Parameter.VAR_KEYWORD for p in init_params.values()
        )
        if has_internals_param:
            kwargs["internals"] = internals

    unit = cls(**kwargs)

    # Attach internals if constructor did not receive or handle them
    if internals and not unit.internals:
        unit.addInternals(internals)

    # If explicit ports are provided, override/augment ports
    if eq.ports:
        unit.ports = {}
        for p in eq.ports:
            unit.ports[p.id] = Port(
                name=p.id,
                parent=unit,
                rel_pos=p.position,
                normal=p.normal,
                intent=p.intent,
            )

    # Flips & Rotation
    if eq.flip_horizontal:
        unit.flipHorizontal()
    if eq.flip_vertical:
        unit.flipVertical()
    if eq.rotation != 0:
        unit.rotate(eq.rotation)

    # Text Anchor
    if eq.text_anchor is not None:
        if isinstance(eq.text_anchor.horizontal, HorizontalLabelAlignment):
            h = eq.text_anchor.horizontal
        else:
            h = ALIGNMENT_MAP_H.get(eq.text_anchor.horizontal, HorizontalLabelAlignment.Center)

        if isinstance(eq.text_anchor.vertical, VerticalLabelAlignment):
            v = eq.text_anchor.vertical
        else:
            v = ALIGNMENT_MAP_V.get(eq.text_anchor.vertical, VerticalLabelAlignment.Bottom)

        offset = eq.text_anchor.offset
        unit.setTextAnchor(h, v, offset)

    if eq.layout_hints is not None:
        unit.layout_hints = eq.layout_hints

    return unit
