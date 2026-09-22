import pytest

from pyflowsheet.core.enums import HorizontalLabelAlignment, VerticalLabelAlignment
from pyflowsheet.core.unitoperation import UnitOperation
from pyflowsheet.internals import (
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
from pyflowsheet.internals.baseinternal import BaseInternal
from pyflowsheet.schema.models import EquipmentSchema, InternalSchema, PortSchema, TextAnchorSchema
from pyflowsheet.schema.registry import (
    INTERNAL_REGISTRY,
    UNIT_REGISTRY,
    instantiate_internal,
    instantiate_unit,
    register_internal_type,
    register_unit_type,
)
from pyflowsheet.unitoperations import (
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


def test_instantiate_vessel_with_internals_ports_and_anchor():
    eq = EquipmentSchema(
        id="V-101",
        name="Flash Drum",
        type="Vessel",
        position=(150.0, 200.0),
        size=(50.0, 120.0),
        cap_length=18.0,
        rotation=90.0,
        internals=[InternalSchema(type="Tubes", tubes=4)],
        ports=[
            PortSchema(
                id="Feed",
                position=(0.0, 0.5),
                normal=(-1.0, 0.0),
                intent="in",
            )
        ],
        text_anchor=TextAnchorSchema(
            horizontal="LeftOuter",
            vertical="Center",
            offset=(-15.0, 0.0),
        ),
    )
    unit = instantiate_unit(eq)
    assert isinstance(unit, Vessel)
    assert unit.id == "V-101"
    assert unit.name == "Flash Drum"
    assert unit.position == (150.0, 200.0)
    assert unit.size == (50.0, 120.0)
    assert unit.capLength == 18.0
    assert unit.rotation == 90.0
    assert len(unit.internals) == 1
    assert "Feed" in unit.ports
    assert unit.horizontalLabelAlignment == HorizontalLabelAlignment.LeftOuter
    assert unit.verticalLabelAlignment == VerticalLabelAlignment.Center
    assert unit.textOffset == (-15.0, 0.0)


def test_instantiate_stream_flag():
    flag = EquipmentSchema(
        id="WaterFeed",
        name="Raw Water",
        type="StreamFlag",
        position=(50.0, 100.0),
    )
    unit = instantiate_unit(flag)
    assert isinstance(unit, StreamFlag)
    assert unit.id == "WaterFeed"


def test_custom_unit_type_registration():
    class CustomSeparator(UnitOperation):
        def __init__(self, id, name, position=(0, 0), size=(30, 30), description=""):
            super().__init__(id, name, position=position, size=size, description=description)

    register_unit_type("CustomSeparator", CustomSeparator)
    try:
        eq = EquipmentSchema(id="SEP-01", type="CustomSeparator")
        unit = instantiate_unit(eq)
        assert isinstance(unit, CustomSeparator)
        assert "CustomSeparator" in UNIT_REGISTRY
    finally:
        UNIT_REGISTRY.pop("CustomSeparator", None)


def test_custom_internal_type_registration():
    class CustomCoil(BaseInternal):
        def __init__(self, turns=5):
            self.turns = turns

    register_internal_type("CustomCoil", CustomCoil)
    try:
        internal = instantiate_internal(InternalSchema(type="CustomCoil"))
        assert isinstance(internal, CustomCoil)
        assert "CustomCoil" in INTERNAL_REGISTRY
    finally:
        INTERNAL_REGISTRY.pop("CustomCoil", None)


def test_unknown_unit_type_raises():
    eq = EquipmentSchema(id="X-1", type="NonExistentUnit")
    with pytest.raises(ValueError, match="Unknown unit operation type 'NonExistentUnit'"):
        instantiate_unit(eq)


def test_unknown_internal_type_raises():
    internal_schema = InternalSchema(type="NonExistentInternal")
    with pytest.raises(ValueError, match="Unknown internal type 'NonExistentInternal'"):
        instantiate_internal(internal_schema)


def test_instantiate_distillation_with_reboiler_condenser_and_trays():
    eq = EquipmentSchema(
        id="T-100",
        name="Depropanizer",
        type="Distillation",
        position=(200.0, 50.0),
        size=(40.0, 180.0),
        has_condenser=False,
        has_reboiler=True,
        internals=[
            InternalSchema(type="Trays", start=0.1, end=0.9, num_trays=20),
        ],
    )
    unit = instantiate_unit(eq)
    assert isinstance(unit, Distillation)
    assert unit.hasCondenser is False
    assert unit.hasReboiler is True
    assert len(unit.internals) == 1
    assert isinstance(unit.internals[0], Trays)
    assert unit.internals[0].numberOfTrays == 20


def test_instantiate_flips():
    eq = EquipmentSchema(
        id="P-101",
        type="Pump",
        flip_horizontal=True,
        flip_vertical=True,
    )
    unit = instantiate_unit(eq)
    assert isinstance(unit, Pump)
    assert unit.isFlippedHorizontal is True
    assert unit.isFlippedVertical is True


def test_instantiate_all_builtin_units():
    unit_types = [
        ("BlackBox", BlackBox),
        ("Compressor", Compressor),
        ("Distillation", Distillation),
        ("HeatExchanger", HeatExchanger),
        ("Mixer", Mixer),
        ("PlateHex", PlateHex),
        ("Pump", Pump),
        ("Splitter", Splitter),
        ("StreamFlag", StreamFlag),
        ("Valve", Valve),
        ("Vessel", Vessel),
    ]
    for type_name, expected_cls in unit_types:
        eq = EquipmentSchema(id=f"test_{type_name}", type=type_name)
        unit = instantiate_unit(eq)
        assert isinstance(unit, expected_cls)


def test_instantiate_builtin_internals():
    tubes = instantiate_internal(InternalSchema(type="Tubes", tubes=8))
    assert isinstance(tubes, Tubes)
    assert tubes.numberOfTubes == 8

    packing = instantiate_internal(InternalSchema(type="RandomPacking", start=0.2, end=0.8))
    assert isinstance(packing, RandomPacking)
    assert packing.start == 0.2
    assert packing.end == 0.8

    trays = instantiate_internal(InternalSchema(type="Trays", start=0.1, end=0.9, num_trays=15))
    assert isinstance(trays, Trays)
    assert trays.numberOfTrays == 15

    for itype, expected_cls in [
        ("Baffles", Baffles),
        ("CatalystBed", CatalystBed),
        ("DiscDonutBaffles", DiscDonutBaffles),
        ("DividingWall", DividingWall),
        ("Jacket", Jacket),
        ("LiquidRing", LiquidRing),
        ("Reciprocating", Reciprocating),
        ("Stirrer", Stirrer),
    ]:
        obj = instantiate_internal(InternalSchema(type=itype))
        assert isinstance(obj, expected_cls)
