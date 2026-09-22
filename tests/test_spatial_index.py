from pyflowsheet.layout.spatial import AABB, SpatialIndex


def test_aabb_properties_and_intersection():
    box1 = AABB(10.0, 10.0, 50.0, 50.0)
    assert box1.center == (30.0, 30.0)
    assert box1.width == 40.0
    assert box1.height == 40.0

    box2 = AABB(40.0, 40.0, 80.0, 80.0)
    assert box1.intersects(box2)
    assert box2.intersects(box1)

    box3 = AABB(60.0, 60.0, 100.0, 100.0)
    assert not box1.intersects(box3)


def test_aabb_contains_point_and_expanded():
    box = AABB(10.0, 10.0, 50.0, 50.0)
    assert box.contains_point((20.0, 30.0))
    assert not box.contains_point((5.0, 30.0))

    expanded = box.expanded(10.0)
    assert expanded.min_x == 0.0
    assert expanded.min_y == 0.0
    assert expanded.max_x == 60.0
    assert expanded.max_y == 60.0


def test_aabb_distance_to_point():
    box = AABB(10.0, 10.0, 50.0, 50.0)
    # Point inside box -> distance 0
    assert box.distance_to_point((20.0, 30.0)) == 0.0
    # Point on boundary -> distance 0
    assert box.distance_to_point((10.0, 20.0)) == 0.0
    # Point directly to the left
    assert box.distance_to_point((5.0, 20.0)) == 5.0
    # Point directly to the right
    assert box.distance_to_point((55.0, 20.0)) == 5.0
    # Point directly above
    assert box.distance_to_point((20.0, 60.0)) == 10.0
    # Point diagonally: (6.0, 7.0) -> dx = 4, dy = 3 -> dist = 5.0
    assert box.distance_to_point((6.0, 7.0)) == 5.0


def test_spatial_index_insert_query():
    idx = SpatialIndex(cell_size=50.0)
    idx.insert("unit1", AABB(10.0, 10.0, 40.0, 40.0), data={"type": "Vessel"})
    idx.insert("unit2", AABB(100.0, 100.0, 150.0, 150.0), data={"type": "Pump"})

    # Query overlapping unit1
    results = idx.query_intersects(AABB(30.0, 30.0, 60.0, 60.0))
    assert len(results) == 1
    assert results[0][0] == "unit1"

    # Query point
    pt_results = idx.query_point((120.0, 120.0))
    assert len(pt_results) == 1
    assert pt_results[0][0] == "unit2"

    # Clear
    idx.clear()
    assert len(idx.query_intersects(AABB(0.0, 0.0, 200.0, 200.0))) == 0


def test_spatial_index_remove_and_update():
    idx = SpatialIndex(cell_size=50.0)
    idx.insert("unit1", AABB(10.0, 10.0, 40.0, 40.0), data="first")

    # Update item
    idx.insert("unit1", AABB(60.0, 60.0, 80.0, 80.0), data="updated")
    old_query = idx.query_intersects(AABB(10.0, 10.0, 40.0, 40.0))
    assert len(old_query) == 0
    new_query = idx.query_intersects(AABB(50.0, 50.0, 70.0, 70.0))
    assert len(new_query) == 1
    assert new_query[0][0] == "unit1"
    assert new_query[0][2] == "updated"

    # Remove item
    idx.remove("unit1")
    assert len(idx.query_intersects(AABB(50.0, 50.0, 70.0, 70.0))) == 0
    # Removing non-existent item should not raise
    idx.remove("unit1")


def test_spatial_index_nearest():
    idx = SpatialIndex(cell_size=50.0)
    idx.insert("unit1", AABB(10.0, 10.0, 40.0, 40.0))
    idx.insert("unit2", AABB(100.0, 100.0, 150.0, 150.0))

    # Nearest to (45.0, 40.0) -> unit1 (distance 5.0 vs unit2 > 60)
    nearest = idx.nearest((45.0, 40.0))
    assert nearest is not None
    assert nearest[0] == "unit1"

    # Nearest to (95.0, 100.0) -> unit2 (distance 5.0)
    nearest2 = idx.nearest((95.0, 100.0))
    assert nearest2 is not None
    assert nearest2[0] == "unit2"

    # With max_distance threshold that is exceeded
    assert idx.nearest((0.0, 0.0), max_distance=5.0) is None
    # With max_distance threshold that is met
    assert idx.nearest((0.0, 10.0), max_distance=15.0) is not None

    # Empty index
    idx.clear()
    assert idx.nearest((10.0, 10.0)) is None


def test_spatial_index_all_items():
    idx = SpatialIndex(cell_size=50.0)
    idx.insert("u1", AABB(0.0, 0.0, 10.0, 10.0), "data1")
    idx.insert("u2", AABB(20.0, 20.0, 30.0, 30.0), "data2")

    items = idx.all_items()
    assert len(items) == 2
    item_ids = {item[0] for item in items}
    assert item_ids == {"u1", "u2"}
