import os
import re
from types import SimpleNamespace

from pyflowsheet.backends.svgcontext import SvgContext


def test_svg_group_id_sanitization(tmp_path):
    output_path = os.path.join(tmp_path, "test_ids.svg")
    ctx = SvgContext(output_path)

    # These IDs normally fail or cause issues in svgwrite without sanitization
    problematic_ids = ["UV/US", "Recovered IONP", "P&ID Tag #1", "100% Flow"]

    for gid in problematic_ids:
        ctx.startGroup(gid)
        ctx.circle([(10, 10), (30, 30)], fillColor=(255, 255, 255), lineColor=(0, 0, 0), lineSize=1)
        ctx.endGroup()

    svg_str = ctx.render(saveFile=True)

    assert os.path.exists(output_path)
    assert 'id="UV_US"' in svg_str
    assert 'id="Recovered_IONP"' in svg_str
    assert 'id="P_ID_Tag__1"' in svg_str or 'id="P_ID_Tag__1"' in svg_str.replace(" ", "_")
    # Verify no un-sanitized spaces or slashes exist inside group IDs
    assert not re.search(r'<g\s+id="[^"]*[\s/][^"]*"', svg_str)


def test_svg_transformed_group_id_sanitization(tmp_path):
    output_path = os.path.join(tmp_path, "test_transformed_ids.svg")
    ctx = SvgContext(output_path)

    element = SimpleNamespace(
        id="UV/US 100%",
        isFlippedHorizontal=False,
        isFlippedVertical=False,
        rotation=0,
        position=(10, 10),
        size=(50, 50),
    )

    ctx.startTransformedGroup(element)
    ctx.circle([(10, 10), (30, 30)], fillColor=(255, 255, 255), lineColor=(0, 0, 0), lineSize=1)
    ctx.endGroup()

    svg_str = ctx.render(saveFile=True)
    assert os.path.exists(output_path)
    assert 'id="UV_US_100__T"' in svg_str
    assert not re.search(r'<g\s+id="[^"]*[\s/][^"]*"', svg_str)
