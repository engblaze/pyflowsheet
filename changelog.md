# Versioning

The versioning scheme using in this project is based on Semantic Versioning, but adopts a different approach to handling pre-releases and build metadata.

The essence of semantic versioning is a 3-part MAJOR.MINOR.MAINTENANCE numbering scheme, where the project author increments:

* MAJOR version when they make incompatible API changes,

* MINOR version when they add functionality in a backwards-compatible manner, and

* MAINTENANCE version when they make backwards-compatible bug fixes.


# History

## Version 0.6.0 (22-09-2026)

**Milestone 4: ISO 10628 & ANSI/ISA-5.1 Standards Library**

* **ISO 10628 Unit Operations**:
  * **Vessels & Tanks**: `Vessel` enhanced with configurable `head_type` (`dished`, `conical`, `flat`), `HorizontalVessel` with saddles, `HorizontalSettler` with boot and weir, `JacketedVessel`.
  * **Separation**: `Hydrocyclone`, `FlotationCell` (DAF), `MembraneModule`, and `StructuredPacking` column internal.
  * **Heat Exchangers**: `ShellAndTubeExchanger` (TEMA type with tubes and baffles), `AirCooler` (fin-fan), `Reboiler` (kettle with vapor dome), `Condenser`, `FiredHeater` (furnace with radiant/convection coils and burner).
  * **Motive Equipment**: `ProgressiveCavityPump`, `PeristalticPump`, `ReciprocatingPump`, `Blower`.
* **Valves Library (`pyflowsheet.valves`)**:
  * **Standard Bodies**: `BaseValve`, `GlobeValve`, `GateValve`, `BallValve`, `ButterflyValve`, `NeedleValve`, `DiaphragmValve`, `PlugValve`, `CheckValve`.
  * **Actuators & Control**: `ControlValve` with actuators (`pneumatic`, `electric`, `solenoid`, `piston`, `manual`) and failure mode indicators (`fail_closed`, `fail_open`, `fail_locked`, `none`).
  * **Specialties**: `SafetyReliefValve`, `RuptureDisc`, `GrabSamplingTee`, `Strainer`, `SteamTrap`.
* **ANSI/ISA-5.1 Instrumentation (`pyflowsheet.instruments`)**:
  * **Tagging**: `ISATag` parser conforming to ANSI/ISA-5.1 letter designations, modifiers, functions, and loop numbers.
  * **Instrument Balloons**: `Instrument` supporting circle, square, diamond, and hexagon balloons with 4 location line types (discrete, shared display, computer function, PLC).
  * **Signal Lines**: `line_type` on `Stream` supporting `process`, `pneumatic` (`//`), `electric` (dashed), `digital` (dots), and `capillary` (crosses) periodic decorations.
* **Schema & Deserialization**:
  * Added `LineType`, `BalloonType`, `LocationModifier`, `ActuatorType`, `FailureMode`, `HeadType` to schema models.
  * Registered all 30+ new classes in `UNIT_REGISTRY` and exported in top-level `pyflowsheet`.
  * Bidirectional YAML/dict serialization roundtrip parity via `Flowsheet.to_dict()` and `from_dict()`.

## Version 0.5.0 (22-09-2026)

**Milestone 3: Two-Tier Automated Layout & Smart Routing Engine**

* **Two-Tier Auto-Layout Engine**: `Flowsheet.auto_layout()` computes clean positions for unpositioned units and expands inline components.
* **Macro Layout**: Topological sorting, rank assignment, and coordinate assignment along horizontal/vertical flow directions.
* **Inline Components**: Automatically spaces and places pumps, valves, and inline instruments along streams between major equipment.
* **Spatial Indexing & Collisions**: `SpatialIndex` utilizing 2D bounding boxes (AABB) to detect and resolve overlaps.
* **Orthogonal Routing & Crossovers**: Enhanced router with bend penalties and automated crossover bridge hops (`line_break` / `arc`) for crossing streams.

## Version 0.4.0 (22-09-2026)

**Milestone 2: Declarative Schema, Validation, and CLI**

* **Declarative Schema**: Pydantic v2 models for `FlowsheetSchema`, `EquipmentSchema`, `StreamSchema`, `TableSchema`, and layout hints.
* **Integrity Validation**: Topological verification (unique IDs, valid stream sources/targets, port resolution) via `validate_yaml_file` and `validate_dict`.
* **CLI Tool (`pyflowsheet`)**:
  * `pyflowsheet render`: Compiles YAML specifications into SVG diagrams with optional auto-layout (`--auto-layout`).
  * `pyflowsheet validate`: Validates schema integrity and reports diagnostics.
  * `pyflowsheet export-schema`: Emits the standard Flowsheet JSON Schema.
* **Bidirectional Serialization**: `Flowsheet.from_dict()`, `Flowsheet.from_yaml()`, `Flowsheet.to_dict()`, and `Flowsheet.to_yaml()`.

## Version 0.3.0 (22-09-2026)

**Milestone 1: Modernization, Pyproject, and QA Architecture**

* Modernized build configuration using `pyproject.toml` and `uv` package management.
* Extended Python compatibility to Python 3.10, 3.11, 3.12, and 3.13+.
* Enforced strict formatting and linting via Ruff.
* Comprehensive test suite using pytest with visual SVG snapshot regression testing.

## Version 0.2.1 (04-01-2021)

* Version 0.2.0 was not running after restructuring of source files. Restored package by adding all submodules correctly in setup.py

## Version 0.2.0 (03-01-2021)

**New Features**
* Added an "Internals" System. You can now add any instance derived from BaseInternal to the internals list of a unit operation. These internals can represent tubes in a heat exchanger, trays or packing in a column, or special realisations of pumps and compressors. 

  **Breaking Change**: It is not possible to define internals by a string anymore.
```python 
U3=pfd.unit(Vessel("Fermenter","Fermenter", position=(200,190), capLength=20, showCapLines=False, size=(80,140),internals=[Stirrer(type=StirrerType.Anchor), Jacket()] ))
```
* Changed how vertical/horizontal vessels work: Now every vessel is vertical by default, but can be rotated either with the rotate(angle) method or by passing the angle as parameter into the constructor.
```python
BA11=Vessel("DS10-BA11","Horizontal Vessel", angle=90, position=(560,400), size=(40,100), capLength=20,internals=[CatalystBed()] )
```
* Compressor unit operation

**Bugfixes**
* Multiple calls to .rotate(angle) do not rotate the ports anymore while keeping the unit itself at the same angle.
* Rotating a unit now influences the area that is blocked for pathfinding.



## Version 0.1.1 (27-12-2020)
* Alpha version
* Basic drawing functions implemented
* [svgwrite](https://github.com/mozman/svgwrite) backend for vector output
* Limited library of unit operations
  * Mixer / Splitter
  * Heat Exchanger
  * Vessel (vertical/horizontal)
  * Distillation Column (optional reboiler and condenser, some internals)
  * Pump
  * Stream flag / Feed / Product
  * Valve
  * BlackBox Unit Operation (catch all for non-implemented icons)
* Arbitary Rotation
* Horizontal Flipping
* Stream routing via Dykstra algorithm (using the  [python-pathfinding package](https://github.com/brean/python-pathfinding) )

