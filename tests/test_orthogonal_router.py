from pyflowsheet.layout.router import OrthogonalRouter, compress_orthogonal_path
from pyflowsheet.layout.spatial import AABB


def test_straight_horizontal_route():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=50.0)
    # Start at (10, 50) heading right (1, 0), End at (110, 50) heading right (1, 0)
    path = router.route(
        start=(10.0, 50.0),
        start_normal=(1.0, 0.0),
        end=(110.0, 50.0),
        end_normal=(-1.0, 0.0),
        obstacles=[],
    )
    # Direct straight line path
    assert len(path) == 2
    assert path[0] == (10.0, 50.0)
    assert path[-1] == (110.0, 50.0)


def test_straight_vertical_route():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=50.0)
    path = router.route(
        start=(50.0, 10.0),
        start_normal=(0.0, 1.0),
        end=(50.0, 110.0),
        end_normal=(0.0, -1.0),
        obstacles=[],
    )
    assert len(path) == 2
    assert path[0] == (50.0, 10.0)
    assert path[-1] == (50.0, 110.0)


def test_obstacle_avoidance_routing():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=50.0)
    # An obstacle directly blocking the straight path between (0, 50) and (200, 50)
    obstacle = AABB(50.0, 20.0, 150.0, 80.0)

    path = router.route(
        start=(0.0, 50.0),
        start_normal=(1.0, 0.0),
        end=(200.0, 50.0),
        end_normal=(-1.0, 0.0),
        obstacles=[obstacle],
    )
    assert len(path) >= 4
    # Ensure no segment passes through the obstacle interior
    for i in range(len(path) - 1):
        p1, p2 = path[i], path[i + 1]
        mid = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
        assert not obstacle.contains_point(mid)


def test_turn_minimization_prevents_staircasing():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=100.0)
    # Path from (0, 0) to (100, 100) should have at most 2 turns (L-shape or Z-shape)
    path = router.route(
        start=(0.0, 0.0),
        start_normal=(1.0, 0.0),
        end=(100.0, 100.0),
        end_normal=(0.0, -1.0),
        obstacles=[],
    )
    # A staircased path would have many segments; turn penalty keeps bends <= 2
    assert len(path) <= 4


def test_u_turn_routing():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=50.0)
    # Start at (50, 50) pointing right, End at (50, 150) pointing right (end_normal=(1, 0))
    path = router.route(
        start=(50.0, 50.0),
        start_normal=(1.0, 0.0),
        end=(50.0, 150.0),
        end_normal=(1.0, 0.0),
        obstacles=[],
    )
    # Should find an orthogonal route with bends connecting the two ports
    assert len(path) >= 3
    assert path[0] == (50.0, 50.0)
    assert path[-1] == (50.0, 150.0)
    # Every segment should be strictly horizontal or vertical
    for i in range(len(path) - 1):
        p1, p2 = path[i], path[i + 1]
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[1] - p1[1])
        assert dx == 0 or dy == 0


def test_compress_orthogonal_path():
    points = [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0), (20.0, 10.0), (20.0, 20.0)]
    compressed = compress_orthogonal_path(points)
    assert compressed == [(0.0, 0.0), (20.0, 0.0), (20.0, 20.0)]

    # Short path edge cases
    assert compress_orthogonal_path([]) == []
    assert compress_orthogonal_path([(0.0, 0.0)]) == [(0.0, 0.0)]
    assert compress_orthogonal_path([(0.0, 0.0), (10.0, 0.0)]) == [(0.0, 0.0), (10.0, 0.0)]


def test_lead_points_match_direct_route():
    router = OrthogonalRouter(grid_size=10.0)
    # Start and end such that lead points match
    # start = (10, 50), normal = (1, 0) -> lead = (30, 50)
    # end = (50, 50), normal = (-1, 0) -> lead = (30, 50)
    path = router.route(
        start=(10.0, 50.0),
        start_normal=(1.0, 0.0),
        end=(50.0, 50.0),
        end_normal=(-1.0, 0.0),
        obstacles=[],
    )
    assert path == [(10.0, 50.0), (50.0, 50.0)]


def test_fallback_when_path_fully_blocked():
    router = OrthogonalRouter(grid_size=10.0)
    # Completely encircle the end lead point with obstacles
    obstacles = [
        AABB(-50.0, -50.0, 250.0, 250.0)  # Huge obstacle covering everything
    ]
    path = router.route(
        start=(0.0, 50.0),
        start_normal=(1.0, 0.0),
        end=(200.0, 50.0),
        end_normal=(-1.0, 0.0),
        obstacles=obstacles,
    )
    # Should fallback cleanly to an orthogonal step path without crashing
    assert len(path) >= 2
    assert path[0] == (0.0, 50.0)
    assert path[-1] == (200.0, 50.0)


def test_matching_lead_points_with_obstacle():
    router = OrthogonalRouter(grid_size=10.0)
    # Lead points match at (30.0, 50.0)
    start = (10.0, 50.0)
    start_normal = (1.0, 0.0)
    end = (50.0, 50.0)
    end_normal = (-1.0, 0.0)
    # Obstacle directly covering the lead point (30.0, 50.0)
    obstacle = AABB(25.0, 45.0, 35.0, 55.0)

    path = router.route(
        start=start,
        start_normal=start_normal,
        end=end,
        end_normal=end_normal,
        obstacles=[obstacle],
    )
    assert len(path) >= 2
    assert path[0] == start
    assert path[-1] == end


def test_off_grid_ports_strictly_orthogonal():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=50.0)
    # Start and end have fractional/off-grid coordinates with non-aligned Y
    path = router.route(
        start=(125.0, 249.0),
        start_normal=(1.0, 0.0),
        end=(155.0, 246.0),
        end_normal=(-1.0, 0.0),
        obstacles=[],
    )
    assert len(path) >= 2
    assert path[0] == (125.0, 249.0)
    assert path[-1] == (155.0, 246.0)

    for i in range(len(path) - 1):
        p1, p2 = path[i], path[i + 1]
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[1] - p1[1])
        assert dx == 0 or dy == 0, f"Segment {p1} -> {p2} is diagonal (dx={dx}, dy={dy})"


def test_off_grid_vertical_ports_strictly_orthogonal():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=50.0)
    path = router.route(
        start=(249.0, 125.0),
        start_normal=(0.0, 1.0),
        end=(246.0, 155.0),
        end_normal=(0.0, -1.0),
        obstacles=[],
    )
    assert len(path) >= 2
    assert path[0] == (249.0, 125.0)
    assert path[-1] == (246.0, 155.0)

    for i in range(len(path) - 1):
        p1, p2 = path[i], path[i + 1]
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[1] - p1[1])
        assert dx == 0 or dy == 0, f"Segment {p1} -> {p2} is diagonal (dx={dx}, dy={dy})"


def test_compress_orthogonal_path_breaks_diagonal():
    points = [(0.0, 0.0), (10.0, 10.0), (20.0, 10.0)]
    compressed = compress_orthogonal_path(points)
    # Diagonal (0, 0) -> (10, 10) must be broken into (0, 0) -> (10, 0) -> (10, 10)
    assert compressed == [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (20.0, 10.0)]
    for i in range(len(compressed) - 1):
        p1, p2 = compressed[i], compressed[i + 1]
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[1] - p1[1])
        assert dx == 0 or dy == 0


def test_avoid_shared_corner_vertices():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=50.0)
    # Stream 1 turns at (100.0, 100.0)
    path1 = router.route(
        start=(50.0, 100.0),
        start_normal=(1.0, 0.0),
        end=(100.0, 150.0),
        end_normal=(0.0, 1.0),
        obstacles=[],
    )
    router.register_route("S1", path1)

    # Stream 2 traverses the same junction
    path2 = router.route(
        start=(40.0, 100.0),
        start_normal=(1.0, 0.0),
        end=(110.0, 150.0),
        end_normal=(0.0, 1.0),
        obstacles=[],
    )

    # Corners of S1 and S2 must not share vertices
    corners1 = set(path1[1:-1])
    corners2 = set(path2[1:-1])
    assert len(corners1.intersection(corners2)) == 0, (
        f"Shared corners detected: {corners1.intersection(corners2)}"
    )


def test_collinear_segment_overlap_avoidance():
    router = OrthogonalRouter(grid_size=10.0, turn_penalty=50.0)
    # Stream 1 occupies the line segment from (70, 100) to (130, 100)
    path1 = router.route(
        start=(70.0, 100.0),
        start_normal=(1.0, 0.0),
        end=(130.0, 100.0),
        end_normal=(-1.0, 0.0),
        obstacles=[],
    )
    router.register_route("S1", path1)

    # Stream 2 starts at (40, 100) and wants to reach (160, 100)
    # Because (70, 100) -> (130, 100) is occupied, Stream 2 should detour to a parallel channel
    path2 = router.route(
        start=(40.0, 100.0),
        start_normal=(1.0, 0.0),
        end=(160.0, 100.0),
        end_normal=(-1.0, 0.0),
        obstacles=[],
    )

    # Ensure Stream 2 does not overlap collinear with Stream 1 along y=100
    for i in range(len(path2) - 1):
        p1, p2 = path2[i], path2[i + 1]
        if abs(p1[1] - 100.0) < 1e-4 and abs(p2[1] - 100.0) < 1e-4:
            overlap = min(max(p1[0], p2[0]), 130.0) - max(min(p1[0], p2[0]), 70.0)
            assert overlap <= 1e-4, f"Collinear overlap detected on segment {p1} -> {p2}"


def test_occupied_corners_and_segments_init():
    occupied_corners = {(100.0, 100.0)}
    occupied_segments = [((50.0, 100.0), (100.0, 100.0))]
    router = OrthogonalRouter(
        grid_size=10.0,
        turn_penalty=50.0,
        occupied_corners=occupied_corners,
        occupied_segments=occupied_segments,
    )
    assert (100.0, 100.0) in router.occupied_corners
    assert len(router.occupied_segments) == 1
