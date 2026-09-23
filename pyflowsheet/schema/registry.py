from inspect import Parameter, signature
from typing import Any

from ..core import Port, UnitOperation
from ..core.enums import HorizontalLabelAlignment, VerticalLabelAlignment
from ..instruments import Instrument
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
    StructuredPacking,
    Trays,
    Tubes,
)
from ..internals.baseinternal import BaseInternal
from ..unitoperations import (
    AirCooler,
    BlackBox,
    Blower,
    Compressor,
    Condenser,
    Distillation,
    FiredHeater,
    FlotationCell,
    HeatExchanger,
    HorizontalSettler,
    HorizontalVessel,
    Hydrocyclone,
    JacketedVessel,
    MembraneModule,
    Mixer,
    PeristalticPump,
    PlateHex,
    ProgressiveCavityPump,
    Pump,
    Reboiler,
    ReciprocatingPump,
    ShellAndTubeExchanger,
    Splitter,
    StreamFlag,
    Valve,
    Vessel,
)
from ..valves import (
    BallValve,
    ButterflyValve,
    CheckValve,
    ControlValve,
    DiaphragmValve,
    GateValve,
    GlobeValve,
    GrabSamplingTee,
    NeedleValve,
    PlugValve,
    RuptureDisc,
    SafetyReliefValve,
    SteamTrap,
    Strainer,
)
from .models import EquipmentSchema, InternalSchema

UNIT_REGISTRY: dict[str, type[UnitOperation]] = {
    "AirCooler": AirCooler,
    "BallValve": BallValve,
    "BlackBox": BlackBox,
    "Blower": Blower,
    "ButterflyValve": ButterflyValve,
    "CheckValve": CheckValve,
    "Compressor": Compressor,
    "Condenser": Condenser,
    "ControlValve": ControlValve,
    "DiaphragmValve": DiaphragmValve,
    "Distillation": Distillation,
    "DistillationColumn": Distillation,
    "FiredHeater": FiredHeater,
    "FlotationCell": FlotationCell,
    "GateValve": GateValve,
    "GlobeValve": GlobeValve,
    "GrabSamplingTee": GrabSamplingTee,
    "HeatExchanger": HeatExchanger,
    "HorizontalSettler": HorizontalSettler,
    "HorizontalVessel": HorizontalVessel,
    "Hydrocyclone": Hydrocyclone,
    "Instrument": Instrument,
    "JacketedVessel": JacketedVessel,
    "MembraneModule": MembraneModule,
    "Mixer": Mixer,
    "NeedleValve": NeedleValve,
    "PeristalticPump": PeristalticPump,
    "PlateHex": PlateHex,
    "PlugValve": PlugValve,
    "ProgressiveCavityPump": ProgressiveCavityPump,
    "Pump": Pump,
    "Reboiler": Reboiler,
    "ReciprocatingPump": ReciprocatingPump,
    "RuptureDisc": RuptureDisc,
    "SafetyReliefValve": SafetyReliefValve,
    "ShellAndTubeExchanger": ShellAndTubeExchanger,
    "Splitter": Splitter,
    "SteamTrap": SteamTrap,
    "Strainer": Strainer,
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
    "StructuredPacking": StructuredPacking,
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
    if itype == "StructuredPacking":
        start = extra.get("start", 0.0)
        end = extra.get("end", 1.0)
        spacing = extra.get("spacing", 10.0)
        return StructuredPacking(start=start, end=end, spacing=spacing)
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

    if eq.type == "ControlValve":
        kwargs["body_type"] = eq.valve_type or "globe"
        kwargs["actuator"] = eq.actuator or "pneumatic"
        kwargs["failure_mode"] = eq.failure_mode or "fail_closed"
    elif eq.type == "Instrument":
        kwargs["tag"] = eq.tag or eq.id
        kwargs["balloon_type"] = eq.balloon_type or "discrete"
        kwargs["location"] = eq.location or "field"
    elif eq.type == "Vessel":
        if eq.cap_length is not None:
            kwargs["capLength"] = eq.cap_length
        kwargs["internals"] = internals
        kwargs["head_type"] = eq.head_type or "dished"
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
        if "capLength" in init_params and eq.cap_length is not None:
            kwargs["capLength"] = eq.cap_length
        if "head_type" in init_params:
            kwargs["head_type"] = eq.head_type or "dished"
        has_internals_param = "internals" in init_params or any(
            p.kind == Parameter.VAR_KEYWORD for p in init_params.values()
        )
        if has_internals_param:
            kwargs["internals"] = internals
        if eq.model_extra:
            for k, v in eq.model_extra.items():
                if k in init_params and k not in kwargs:
                    kwargs[k] = v

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
    if eq.flip_horizontal and not getattr(unit, "isFlippedHorizontal", False):
        unit.flipHorizontal()
    if eq.flip_vertical and not getattr(unit, "isFlippedVertical", False):
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

    if getattr(eq, "fixed", False):
        unit.fixed = True

    return unit
