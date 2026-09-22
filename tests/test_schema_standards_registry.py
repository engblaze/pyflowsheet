from pyflowsheet.core import Flowsheet
from pyflowsheet.instruments import Instrument
from pyflowsheet.internals import StructuredPacking
from pyflowsheet.schema.models import EquipmentSchema, InternalSchema
from pyflowsheet.schema.registry import (
    INTERNAL_REGISTRY,
    UNIT_REGISTRY,
    instantiate_internal,
    instantiate_unit,
)
from pyflowsheet.unitoperations import (
    AirCooler,
    Blower,
    Condenser,
    FiredHeater,
    FlotationCell,
    HorizontalSettler,
    HorizontalVessel,
    Hydrocyclone,
    JacketedVessel,
    MembraneModule,
    PeristalticPump,
    ProgressiveCavityPump,
    Reboiler,
    ReciprocatingPump,
    ShellAndTubeExchanger,
    Vessel,
)
from pyflowsheet.valves import (
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


def test_registry_contains_all_new_classes():
    expected_units = {
        "ControlValve": ControlValve,
        "GlobeValve": GlobeValve,
        "GateValve": GateValve,
        "BallValve": BallValve,
        "ButterflyValve": ButterflyValve,
        "NeedleValve": NeedleValve,
        "DiaphragmValve": DiaphragmValve,
        "PlugValve": PlugValve,
        "CheckValve": CheckValve,
        "SafetyReliefValve": SafetyReliefValve,
        "RuptureDisc": RuptureDisc,
        "GrabSamplingTee": GrabSamplingTee,
        "Strainer": Strainer,
        "SteamTrap": SteamTrap,
        "Instrument": Instrument,
        "HorizontalVessel": HorizontalVessel,
        "HorizontalSettler": HorizontalSettler,
        "JacketedVessel": JacketedVessel,
        "Hydrocyclone": Hydrocyclone,
        "FlotationCell": FlotationCell,
        "MembraneModule": MembraneModule,
        "ShellAndTubeExchanger": ShellAndTubeExchanger,
        "AirCooler": AirCooler,
        "Reboiler": Reboiler,
        "Condenser": Condenser,
        "FiredHeater": FiredHeater,
        "ProgressiveCavityPump": ProgressiveCavityPump,
        "PeristalticPump": PeristalticPump,
        "ReciprocatingPump": ReciprocatingPump,
        "Blower": Blower,
    }
    for name, cls in expected_units.items():
        assert name in UNIT_REGISTRY, f"Missing {name} in UNIT_REGISTRY"
        assert UNIT_REGISTRY[name] is cls, f"Class mismatch for {name} in UNIT_REGISTRY"

    assert "StructuredPacking" in INTERNAL_REGISTRY
    assert INTERNAL_REGISTRY["StructuredPacking"] is StructuredPacking


def test_instantiate_control_valve():
    eq = EquipmentSchema(
        id="PCV-101",
        type="ControlValve",
        valve_type="globe",
        actuator="pneumatic",
        failure_mode="fail_closed",
    )
    cv = instantiate_unit(eq)
    assert isinstance(cv, ControlValve)
    assert cv.actuator == "pneumatic"
    assert cv.failure_mode == "fail_closed"


def test_instantiate_instrument():
    eq = EquipmentSchema(
        id="FIT-101",
        type="Instrument",
        tag="FIT-101",
        balloon_type="discrete",
        location="control_room",
    )
    inst = instantiate_unit(eq)
    assert isinstance(inst, Instrument)
    assert inst.tag.letters == "FIT"
    assert inst.location == "control_room"


def test_instantiate_vessel_head_type():
    eq = EquipmentSchema(
        id="V-102",
        type="Vessel",
        head_type="conical",
    )
    vessel = instantiate_unit(eq)
    assert isinstance(vessel, Vessel)
    assert vessel.head_type == "conical"


def test_instantiate_structured_packing():
    internal_schema = InternalSchema(
        type="StructuredPacking",
        start=0.2,
        end=0.8,
    )
    sp = instantiate_internal(internal_schema)
    assert isinstance(sp, StructuredPacking)
    assert sp.start == 0.2
    assert sp.end == 0.8


def test_flowsheet_from_yaml_standards():
    yaml_text = """
metadata:
  title: Standards Flowsheet
equipment:
  - id: V-101
    type: JacketedVessel
    position: [50, 50]
  - id: P-101
    type: ProgressiveCavityPump
    position: [150, 50]
  - id: PCV-101
    type: ControlValve
    actuator: pneumatic
    failure_mode: fail_open
    position: [250, 50]
  - id: FIT-101
    type: Instrument
    tag: FIT-101
    position: [250, 10]
streams:
  - id: S1
    from: V-101:Out
    to: P-101:In
    line_type: process
  - id: SIG-1
    from: FIT-101:Bottom
    to: PCV-101:Actuator
    line_type: pneumatic
"""
    fs = Flowsheet.from_yaml(yaml_text)
    assert len(fs.unitOperations) == 4
    assert len(fs.streams) == 2
    assert fs.streams["SIG-1"].line_type == "pneumatic"


def test_top_level_exports():
    import pyflowsheet

    # Verify modules exported
    assert hasattr(pyflowsheet, "valves")
    assert hasattr(pyflowsheet, "instruments")

    # Verify primary new classes exported
    assert hasattr(pyflowsheet, "ControlValve")
    assert hasattr(pyflowsheet, "GlobeValve")
    assert hasattr(pyflowsheet, "Instrument")
    assert hasattr(pyflowsheet, "AirCooler")
    assert hasattr(pyflowsheet, "JacketedVessel")
    assert hasattr(pyflowsheet, "ProgressiveCavityPump")
    assert hasattr(pyflowsheet, "ShellAndTubeExchanger")
