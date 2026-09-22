from pyflowsheet.layout.instruments import InstrumentTapPlacement, InstrumentTapRouter
from pyflowsheet.layout.spatial import AABB, SpatialIndex


def test_tap_routes_to_uncongested_side():
    spatial_index = SpatialIndex()
    # Populate congestion/obstacles below the pipe at (100, 100)
    spatial_index.insert("OBSTACLE", AABB(80.0, 110.0, 120.0, 160.0))

    router = InstrumentTapRouter(leader_length=40.0, balloon_radius=12.0)
    placement = router.place_and_route(
        tap=(100.0, 100.0),
        pipe_orientation="horizontal",
        spatial_index=spatial_index,
    )

    # Balloon placed ABOVE because below is congested
    assert placement.balloon_center[0] == 100.0
    assert placement.balloon_center[1] < 100.0
    assert placement.leader_line == [(100.0, 100.0), placement.balloon_center]
    assert isinstance(placement, InstrumentTapPlacement)
    assert placement.balloon_box == AABB(88.0, 48.0, 112.0, 72.0)


def test_tap_routes_below_when_above_congested():
    spatial_index = SpatialIndex()
    # Populate congestion/obstacles above the pipe at (100, 100)
    spatial_index.insert("OBSTACLE", AABB(80.0, 40.0, 120.0, 80.0))

    router = InstrumentTapRouter(leader_length=40.0, balloon_radius=12.0)
    placement = router.place_and_route(
        tap=(100.0, 100.0),
        pipe_orientation="horizontal",
        spatial_index=spatial_index,
    )

    # Balloon placed BELOW because above is congested
    assert placement.balloon_center[0] == 100.0
    assert placement.balloon_center[1] == 140.0
    assert placement.leader_line == [(100.0, 100.0), (100.0, 140.0)]
    assert placement.balloon_box == AABB(88.0, 128.0, 112.0, 152.0)


def test_vertical_pipe_tap_placement():
    spatial_index = SpatialIndex()
    router = InstrumentTapRouter(leader_length=40.0, balloon_radius=12.0)
    placement = router.place_and_route(
        tap=(100.0, 100.0),
        pipe_orientation="vertical",
        spatial_index=spatial_index,
    )

    # By default, routes to the right of vertical pipe
    assert placement.balloon_center[1] == 100.0
    assert placement.balloon_center[0] > 100.0
    assert placement.balloon_center == (140.0, 100.0)
    assert placement.balloon_box == AABB(128.0, 88.0, 152.0, 112.0)


def test_vertical_pipe_tap_routes_left_when_right_congested():
    spatial_index = SpatialIndex()
    # Populate congestion to the right of (100, 100)
    spatial_index.insert("OBSTACLE", AABB(120.0, 80.0, 160.0, 120.0))

    router = InstrumentTapRouter(leader_length=30.0, balloon_radius=10.0)
    placement = router.place_and_route(
        tap=(100.0, 100.0),
        pipe_orientation="vertical",
        spatial_index=spatial_index,
    )

    # Balloon placed LEFT because right is congested
    assert placement.balloon_center == (70.0, 100.0)
    assert placement.leader_line == [(100.0, 100.0), (70.0, 100.0)]
    assert placement.balloon_box == AABB(60.0, 90.0, 80.0, 110.0)
