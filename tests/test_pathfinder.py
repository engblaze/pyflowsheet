from pathfinding.core.grid import Grid

from pyflowsheet.core.flowsheet import Flowsheet
from pyflowsheet.core.pathfinder import compressPath
from pyflowsheet.unitoperations import BlackBox, StreamFlag


def test_compress_path():
    # Straight collinear horizontal line with multiple segments
    raw_path = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)]
    compressed = compressPath(raw_path)
    # Collinear points (1, 0) and (2, 0) should be removed; (3, 1) should be removed
    assert compressed == [(0, 0), (3, 0), (3, 2)]


def test_flowsheet_grid_calculation():
    pfd = Flowsheet("F1", "Test Flowsheet")
    u1 = BlackBox("B1", "Unit 1", position=(100, 100), size=(60, 40))
    u2 = BlackBox("B2", "Unit 2", position=(250, 100), size=(60, 40))
    pfd.addUnits([u1, u2])

    grid_matrix, minx, miny = pfd._calcGrid()
    assert len(grid_matrix) > 0
    assert len(grid_matrix[0]) > 0

    # Grid point inside B1 should be impassable (0)
    grid = Grid(matrix=grid_matrix)
    # Unit 1 center is (130, 120). Map to grid index:
    gx = round((130 - minx) / 10)
    gy = round((120 - miny) / 10)
    assert grid_matrix[gy][gx] == 0
    assert not grid.walkable(gx, gy)


def test_flowsheet_connect_and_draw(tmp_path):
    pfd = Flowsheet("F2", "Connection Test")
    feed = StreamFlag("Feed", "Feed", position=(50, 100), size=(40, 40))
    dest = StreamFlag("Prod", "Product", position=(200, 100), size=(40, 40))
    pfd.addUnits([feed, dest])

    pfd.connect("S01", feed["Out"], dest["In"])
    assert "S01" in pfd.streams

    from pyflowsheet.backends.svgcontext import SvgContext

    ctx = SvgContext(str(tmp_path / "conn.svg"))
    pfd.draw(ctx)
    svg_str = ctx.render(saveFile=True)

    assert "<path" in svg_str
    assert 'id="S01"' in svg_str
