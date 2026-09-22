import pytest

from pyflowsheet.layout import LabelPlacementSolver
from pyflowsheet.layout.spatial import AABB, SpatialIndex


def test_label_avoids_overlapping_obstacle():
    spatial_index = SpatialIndex()
    # Unit operation box at (100, 100) to (160, 160)
    unit_box = AABB(100.0, 100.0, 160.0, 160.0)
    spatial_index.insert("UNIT", unit_box)

    # Obstacle placed directly below unit where standard bottom label would sit
    spatial_index.insert("PIPE", AABB(90.0, 165.0, 170.0, 195.0))

    solver = LabelPlacementSolver()
    # Desired label of size 50x15
    placed_pos, placed_box = solver.place_equipment_label(
        unit_id="UNIT",
        unit_box=unit_box,
        label_size=(50.0, 15.0),
        spatial_index=spatial_index,
    )

    # Label should not collide with PIPE
    assert not placed_box.intersects(AABB(90.0, 165.0, 170.0, 195.0))
    # Label should sit above or to the side
    assert placed_box.max_y <= unit_box.min_y or placed_box.min_x >= unit_box.max_x


def test_stream_label_horizontal_avoids_obstacle():
    spatial_index = SpatialIndex()
    spatial_index.insert("STR1", AABB(0.0, 100.0, 200.0, 100.0))
    # Obstacle above middle segment
    spatial_index.insert("BLOCKER", AABB(80.0, 70.0, 120.0, 100.0))

    solver = LabelPlacementSolver(clearance=6.0)
    waypoints = [(0.0, 100.0), (200.0, 100.0)]
    placed_pos, placed_box = solver.place_stream_label(
        stream_id="STR1",
        waypoints=waypoints,
        label_size=(40.0, 12.0),
        spatial_index=spatial_index,
    )

    # Label should be placed below the line, avoiding blocker above
    assert not placed_box.intersects(AABB(80.0, 70.0, 120.0, 100.0))
    assert placed_box.min_y >= 100.0


def test_stream_label_vertical_avoids_obstacle():
    spatial_index = SpatialIndex()
    spatial_index.insert("STR2", AABB(100.0, 0.0, 100.0, 200.0))
    # Obstacle on the right side of middle segment
    spatial_index.insert("BLOCKER", AABB(100.0, 80.0, 140.0, 120.0))

    solver = LabelPlacementSolver(clearance=6.0)
    waypoints = [(100.0, 0.0), (100.0, 200.0)]
    placed_pos, placed_box = solver.place_stream_label(
        stream_id="STR2",
        waypoints=waypoints,
        label_size=(30.0, 10.0),
        spatial_index=spatial_index,
    )

    # Label should be placed to the left
    assert not placed_box.intersects(AABB(100.0, 80.0, 140.0, 120.0))
    assert placed_box.max_x <= 100.0


def test_equipment_label_default_placement_below():
    spatial_index = SpatialIndex()
    unit_box = AABB(100.0, 100.0, 160.0, 160.0)
    spatial_index.insert("UNIT", unit_box)

    solver = LabelPlacementSolver(clearance=6.0)
    placed_pos, placed_box = solver.place_equipment_label(
        unit_id="UNIT",
        unit_box=unit_box,
        label_size=(50.0, 15.0),
        spatial_index=spatial_index,
    )

    # Candidate 1 (below) is first, so with 0 collision score it should be chosen
    assert placed_box.min_y >= unit_box.max_y + 6.0
    assert placed_pos[0] == unit_box.center[0]


def test_equipment_label_falls_back_to_left():
    spatial_index = SpatialIndex()
    unit_box = AABB(100.0, 100.0, 160.0, 160.0)
    spatial_index.insert("UNIT", unit_box)

    # Block below, above, and right
    spatial_index.insert("BLOCK_BELOW", AABB(90.0, 161.0, 170.0, 200.0))
    spatial_index.insert("BLOCK_ABOVE", AABB(90.0, 60.0, 170.0, 99.0))
    spatial_index.insert("BLOCK_RIGHT", AABB(161.0, 90.0, 220.0, 170.0))

    solver = LabelPlacementSolver(clearance=6.0)
    placed_pos, placed_box = solver.place_equipment_label(
        unit_id="UNIT",
        unit_box=unit_box,
        label_size=(40.0, 15.0),
        spatial_index=spatial_index,
    )

    # Candidate 4 (left) should be chosen
    assert placed_box.max_x <= unit_box.min_x - 6.0
    assert not placed_box.intersects(AABB(90.0, 161.0, 170.0, 200.0))
    assert not placed_box.intersects(AABB(90.0, 60.0, 170.0, 99.0))
    assert not placed_box.intersects(AABB(161.0, 90.0, 220.0, 170.0))


def test_stream_label_requires_at_least_two_waypoints():
    solver = LabelPlacementSolver()
    spatial_index = SpatialIndex()
    with pytest.raises(ValueError, match="At least 2 waypoints are required"):
        solver.place_stream_label(
            stream_id="STR",
            waypoints=[(10.0, 10.0)],
            label_size=(20.0, 10.0),
            spatial_index=spatial_index,
        )


def test_stream_label_multi_segment():
    spatial_index = SpatialIndex()
    # 3-segment orthogonal path
    waypoints = [(0.0, 0.0), (50.0, 0.0), (50.0, 100.0), (100.0, 100.0)]
    # Middle segment is index 1: (50.0, 0.0) to (50.0, 100.0) - vertical
    # Block right side of middle segment
    spatial_index.insert("BLOCK_RIGHT", AABB(50.0, 30.0, 100.0, 70.0))

    solver = LabelPlacementSolver(clearance=5.0)
    placed_pos, placed_box = solver.place_stream_label(
        stream_id="STR_MULTI",
        waypoints=waypoints,
        label_size=(30.0, 10.0),
        spatial_index=spatial_index,
    )

    # Should place on left of vertical middle segment
    assert placed_box.max_x <= 50.0 - 5.0
    assert not placed_box.intersects(AABB(50.0, 30.0, 100.0, 70.0))
