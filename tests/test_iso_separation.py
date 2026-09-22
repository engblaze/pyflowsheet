import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.internals import StructuredPacking
from pyflowsheet.internals.structuredPacking import StructuredPacking as StructuredPackingDirect
from pyflowsheet.unitoperations import (
    Distillation,
    FlotationCell,
    Hydrocyclone,
    MembraneModule,
)
from pyflowsheet.unitoperations.flotationcell import FlotationCell as FlotationCellDirect
from pyflowsheet.unitoperations.hydrocyclone import Hydrocyclone as HydrocycloneDirect
from pyflowsheet.unitoperations.membranemodule import MembraneModule as MembraneModuleDirect


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "separation_test.svg")
    return SvgContext(out_file)


def test_structured_packing_internal(svg_ctx):
    col = Distillation(
        "T-101",
        "Packed Tower",
        position=(10, 10),
        size=(40, 150),
        internals=[StructuredPacking(start=0.2, end=0.8)],
    )
    svg_ctx.startGroup(col.id)
    col.draw(svg_ctx)
    svg_ctx.endGroup()
    output = svg_ctx.render(saveFile=False)
    assert len(output) > 500


def test_hydrocyclone_ports_and_draw(svg_ctx):
    hc = Hydrocyclone("HC-101", "Cyclone", position=(10, 10), size=(30, 70))
    assert "Feed" in hc.ports
    assert "Overflow" in hc.ports
    assert "Underflow" in hc.ports

    # Verify positions and normals
    assert hc.ports["Feed"].relativePosition == (0.0, 0.25)
    assert hc.ports["Feed"].normal == (-1, 0)
    assert hc.ports["Overflow"].relativePosition == (0.5, 0.0)
    assert hc.ports["Overflow"].normal == (0, -1)
    assert hc.ports["Overflow"].intent == "out"
    assert hc.ports["Underflow"].relativePosition == (0.5, 1.0)
    assert hc.ports["Underflow"].normal == (0, 1)
    assert hc.ports["Underflow"].intent == "out"

    # Aliases
    assert hc.ports["In"] == hc.ports["Feed"]
    assert hc.ports["Top"] == hc.ports["Overflow"]
    assert hc.ports["Bottom"] == hc.ports["Underflow"]

    svg_ctx.startGroup(hc.id)
    hc.draw(svg_ctx)
    svg_ctx.endGroup()
    output = svg_ctx.render(saveFile=False)
    assert len(output) > 200


def test_flotation_cell_ports_and_draw(svg_ctx):
    daf = FlotationCell("DAF-101", "Flotation Cell", position=(50, 10), size=(80, 50))
    assert "Feed" in daf.ports
    assert "Air" in daf.ports
    assert "Float" in daf.ports
    assert "Effluent" in daf.ports

    # Verify port positions and intents
    assert daf.ports["Feed"].relativePosition == (0.0, 0.5)
    assert daf.ports["Air"].relativePosition == (0.2, 1.0)
    assert daf.ports["Float"].relativePosition == (1.0, 0.2)
    assert daf.ports["Float"].intent == "out"
    assert daf.ports["Effluent"].relativePosition == (1.0, 0.8)
    assert daf.ports["Effluent"].intent == "out"

    # Aliases
    assert daf.ports["In"] == daf.ports["Feed"]
    assert daf.ports["Out"] == daf.ports["Effluent"]
    assert daf.ports["Froth"] == daf.ports["Float"]

    svg_ctx.startGroup(daf.id)
    daf.draw(svg_ctx)
    svg_ctx.endGroup()
    output = svg_ctx.render(saveFile=False)
    assert len(output) > 300


def test_membrane_module_ports_and_draw(svg_ctx):
    mem = MembraneModule("MEM-101", "RO Membrane", position=(150, 10), size=(70, 30))
    assert "Feed" in mem.ports
    assert "Retentate" in mem.ports
    assert "Permeate" in mem.ports

    # Verify port positions and intents as specified in brief
    assert mem.ports["Feed"].relativePosition == (0.0, 0.3)
    assert mem.ports["Feed"].normal == (-1, 0)
    assert mem.ports["Retentate"].relativePosition == (1.0, 0.3)
    assert mem.ports["Retentate"].normal == (1, 0)
    assert mem.ports["Retentate"].intent == "out"
    assert mem.ports["Permeate"].relativePosition == (0.5, 1.0)
    assert mem.ports["Permeate"].normal == (0, 1)
    assert mem.ports["Permeate"].intent == "out"

    # Aliases
    assert mem.ports["In"] == mem.ports["Feed"]
    assert mem.ports["Out"] == mem.ports["Retentate"]
    assert mem.ports["Concentrate"] == mem.ports["Retentate"]
    assert mem.ports["Filtrate"] == mem.ports["Permeate"]

    svg_ctx.startGroup(mem.id)
    mem.draw(svg_ctx)
    svg_ctx.endGroup()
    output = svg_ctx.render(saveFile=False)
    assert len(output) > 200


def test_package_exports():
    assert StructuredPacking is StructuredPackingDirect
    assert Hydrocyclone is HydrocycloneDirect
    assert FlotationCell is FlotationCellDirect
    assert MembraneModule is MembraneModuleDirect


def test_transformations():
    # Verify transformations work cleanly on units with aliased ports
    hc = Hydrocyclone("HC-102", "Cyclone", position=(0, 0), size=(30, 70), angle=90)
    assert hc.rotation == 90

    mem = MembraneModule("MEM-102", "RO Membrane", position=(0, 0), size=(70, 30))
    mem.flipVertical()
    assert mem.isFlippedVertical
    # Permeate was (0.5, 1.0), after vertical flip becomes (0.5, 0.0)
    assert mem.ports["Permeate"].relativePosition == (0.5, 0.0)
    assert mem.ports["Filtrate"].relativePosition == (0.5, 0.0)
