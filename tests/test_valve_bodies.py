import os

import pytest

from pyflowsheet.backends.svgcontext import SvgContext
from pyflowsheet.valves.bodies import (
    BallValve,
    BaseValve,
    ButterflyValve,
    CheckValve,
    DiaphragmValve,
    GateValve,
    GlobeValve,
    NeedleValve,
    PlugValve,
)


@pytest.fixture
def svg_ctx(tmp_path):
    out_file = os.path.join(tmp_path, "valves_test.svg")
    return SvgContext(out_file)


def test_valve_bodies_instantiation_and_ports():
    valve_classes = [
        GlobeValve,
        GateValve,
        BallValve,
        ButterflyValve,
        NeedleValve,
        DiaphragmValve,
        PlugValve,
        CheckValve,
    ]
    for cls in valve_classes:
        v = cls(id=f"V_{cls.__name__}", name="Valve", position=(10, 10), size=(30, 20))
        assert "In" in v.ports
        assert "Out" in v.ports
        assert v.ports["In"].relativePosition == (0.0, 0.5)
        assert v.ports["Out"].relativePosition == (1.0, 0.5)
        assert v.ports["In"].normal == (-1, 0)
        assert v.ports["Out"].normal == (1, 0)
        assert v.ports["Out"].intent == "out"


def test_base_valve():
    bv = BaseValve("BV1")
    assert bv.id == "BV1"
    assert bv.name == "BV1"
    assert bv.size == (30.0, 20.0)
    assert bv.position == (0.0, 0.0)
    assert "In" in bv.ports
    assert "Out" in bv.ports
    assert bv.ports["In"].relativePosition == (0.0, 0.5)
    assert bv.ports["Out"].relativePosition == (1.0, 0.5)


def test_valve_package_exports():
    import pyflowsheet.valves as valves

    expected_exports = [
        "BaseValve",
        "GlobeValve",
        "GateValve",
        "BallValve",
        "ButterflyValve",
        "NeedleValve",
        "DiaphragmValve",
        "PlugValve",
        "CheckValve",
    ]
    for name in expected_exports:
        assert hasattr(valves, name)
        assert name in valves.__all__


def test_valve_bodies_draw(svg_ctx):
    valve_classes = [
        GlobeValve,
        GateValve,
        BallValve,
        ButterflyValve,
        NeedleValve,
        DiaphragmValve,
        PlugValve,
        CheckValve,
    ]
    for idx, cls in enumerate(valve_classes):
        v = cls(id=f"V_{idx}", name=cls.__name__, position=(10 + idx * 40, 50), size=(30, 20))
        svg_ctx.startGroup(v.id)
        svg_ctx.startTransformedGroup(v)
        v.draw(svg_ctx)
        svg_ctx.endGroup()
        v.drawTextLayer(svg_ctx)
        svg_ctx.endGroup()

    output = svg_ctx.render(saveFile=False)
    assert len(output) > 500


def test_valve_individual_svg_elements(tmp_path):
    valve_types = {
        "gate": GateValve("VG", position=(10, 10), size=(30, 20)),
        "globe": GlobeValve("VGL", position=(10, 10), size=(30, 20)),
        "ball": BallValve("VB", position=(10, 10), size=(30, 20)),
        "butterfly": ButterflyValve("VBF", position=(10, 10), size=(30, 20)),
        "needle": NeedleValve("VN", position=(10, 10), size=(30, 20)),
        "diaphragm": DiaphragmValve("VD", position=(10, 10), size=(30, 20)),
        "plug": PlugValve("VP", position=(10, 10), size=(30, 20)),
        "check": CheckValve("VC", position=(10, 10), size=(30, 20)),
    }

    for key, v in valve_types.items():
        ctx = SvgContext(os.path.join(tmp_path, f"{key}.svg"))
        ctx.startGroup(v.id)
        ctx.startTransformedGroup(v)
        v.draw(ctx)
        ctx.endGroup()
        svg_str = ctx.render(saveFile=False)

        # All valves should draw the opposing triangles (path elements)
        assert "<path" in svg_str

        if key in ("globe", "ball"):
            assert "<circle" in svg_str
        elif key == "plug":
            assert "<rect" in svg_str
        elif key in ("butterfly", "needle", "check"):
            assert "<line" in svg_str


def test_backward_compatibility():
    from pyflowsheet.unitoperations import Valve as LegacyValve

    lv = LegacyValve("LV1", "Legacy Valve")
    assert lv.id == "LV1"
    assert lv.size == (40, 20)
    assert "In" in lv.ports
    assert "Out" in lv.ports
