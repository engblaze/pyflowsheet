from __future__ import annotations

import heapq
from collections.abc import Sequence
from math import ceil, floor, hypot

from .spatial import AABB


def compress_orthogonal_path(points: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    """Removes redundant collinear points from an orthogonal path and ensures
    strict orthogonality.
    """
    if len(points) <= 1:
        return list(points)

    eps = 1e-6

    def _dedup(pts: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
        deduped: list[tuple[float, float]] = []
        for p in pts:
            if not deduped or (
                abs(p[0] - deduped[-1][0]) > eps or abs(p[1] - deduped[-1][1]) > eps
            ):
                deduped.append(p)
        return deduped

    def _remove_collinear(pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
        if len(pts) <= 2:
            return pts
        compressed = [pts[0]]
        for i in range(1, len(pts) - 1):
            prev = compressed[-1]
            curr = pts[i]
            nxt = pts[i + 1]

            dx1, dy1 = curr[0] - prev[0], curr[1] - prev[1]
            dx2, dy2 = nxt[0] - curr[0], nxt[1] - curr[1]

            if (abs(dx1) <= eps and abs(dx2) <= eps) or (abs(dy1) <= eps and abs(dy2) <= eps):
                continue  # Collinear point skipped
            compressed.append(curr)

        compressed.append(pts[-1])
        return compressed

    # 1. Dedup consecutive duplicates
    pts = _dedup(points)
    if len(pts) <= 1:
        return pts

    # 2. Compress collinear segments
    pts = _remove_collinear(pts)

    # 3. Post-validation: ensure strictly orthogonal segments
    orthogonalized: list[tuple[float, float]] = [pts[0]]
    for i in range(len(pts) - 1):
        p1 = orthogonalized[-1]
        p2 = pts[i + 1]
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[1] - p1[1])
        if dx > eps and dy > eps:
            # Diagonal segment: break into horizontal then vertical step
            orthogonalized.append((p2[0], p1[1]))
        orthogonalized.append(p2)

    # 4. Final dedup and collinear compression
    orthogonalized = _dedup(orthogonalized)
    orthogonalized = _remove_collinear(orthogonalized)

    return orthogonalized


def seg_intersects_box(
    p1: tuple[float, float],
    p2: tuple[float, float],
    box: AABB,
    margin: float = 0.0,
    eps: float = 1e-4,
) -> bool:
    """Checks if orthogonal segment p1->p2 intersects the interior of an AABB."""
    min_x = box.min_x - margin
    max_x = box.max_x + margin
    min_y = box.min_y - margin
    max_y = box.max_y + margin

    x1, y1 = p1
    x2, y2 = p2
    seg_min_x, seg_max_x = min(x1, x2), max(x1, x2)
    seg_min_y, seg_max_y = min(y1, y2), max(y1, y2)

    if seg_max_x <= min_x + eps or seg_min_x >= max_x - eps:
        return False
    if seg_max_y <= min_y + eps or seg_min_y >= max_y - eps:
        return False

    if abs(y1 - y2) <= eps:  # horizontal segment
        return (
            min_y + eps < y1 < max_y - eps
            and seg_max_x > min_x + eps
            and seg_min_x < max_x - eps
        )
    else:  # vertical segment
        return (
            min_x + eps < x1 < max_x - eps
            and seg_max_y > min_y + eps
            and seg_min_y < max_y - eps
        )


def is_route_clear(
    pts: Sequence[tuple[float, float]],
    obstacles: Sequence[AABB],
    source_box: AABB | None = None,
    target_box: AABB | None = None,
    margin: float = 4.0,
) -> bool:
    """Validates that all segments in an orthogonal path do not penetrate obstacles."""
    if not obstacles:
        return True
    for i in range(len(pts) - 1):
        p1, p2 = pts[i], pts[i + 1]
        for obs in obstacles:
            m = 0.0 if (obs is source_box or obs is target_box) else margin
            if seg_intersects_box(p1, p2, obs, margin=m):
                return False
    return True


def remove_self_intersections(points: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    """Detects and cuts out self-intersecting loops and crossings from an orthogonal path."""
    eps = 1e-4

    def _seg_intersection(
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        p4: tuple[float, float],
    ) -> tuple[float, float] | None:
        dx1, dy1 = p2[0] - p1[0], p2[1] - p1[1]
        dx2, dy2 = p4[0] - p3[0], p4[1] - p3[1]
        h1 = abs(dy1) <= eps
        h2 = abs(dy2) <= eps
        if h1 and not h2:
            y = p1[1]
            x = p3[0]
            if (
                min(p1[0], p2[0]) - eps <= x <= max(p1[0], p2[0]) + eps
                and min(p3[1], p4[1]) - eps <= y <= max(p3[1], p4[1]) + eps
            ):
                return (x, y)
        elif not h1 and h2:
            x = p1[0]
            y = p3[1]
            if (
                min(p1[1], p2[1]) - eps <= y <= max(p1[1], p2[1]) + eps
                and min(p3[0], p4[0]) - eps <= x <= max(p3[0], p4[0]) + eps
            ):
                return (x, y)
        elif h1 and h2:
            if abs(p1[1] - p3[1]) <= eps:
                ov_min = max(min(p1[0], p2[0]), min(p3[0], p4[0]))
                ov_max = min(max(p1[0], p2[0]), max(p3[0], p4[0]))
                if ov_max - ov_min > eps:
                    return (ov_min, p1[1])
        else:
            if abs(p1[0] - p3[0]) <= eps:
                ov_min = max(min(p1[1], p2[1]), min(p3[1], p4[1]))
                ov_max = min(max(p1[1], p2[1]), max(p3[1], p4[1]))
                if ov_max - ov_min > eps:
                    return (p1[0], ov_min)
        return None

    pts = compress_orthogonal_path(points)
    changed = True
    while changed:
        changed = False
        pts = compress_orthogonal_path(pts)
        n = len(pts)
        if n < 4:
            break
        for i in range(n - 1):
            p1, p2 = pts[i], pts[i + 1]
            for j in range(i + 2, n - 1):
                p3, p4 = pts[j], pts[j + 1]
                pt = _seg_intersection(p1, p2, p3, p4)
                if pt is not None:
                    new_pts = pts[: i + 1] + [pt] + pts[j + 1 :]
                    pts = compress_orthogonal_path(new_pts)
                    changed = True
                    break
            if changed:
                break
    return pts


def simplify_orthogonal_path(
    points: Sequence[tuple[float, float]],
    obstacles: Sequence[AABB] | None = None,
    start_normal: tuple[float, float] | None = None,
    end_normal: tuple[float, float] | None = None,
    source_box: AABB | None = None,
    target_box: AABB | None = None,
    router: OrthogonalRouter | None = None,
) -> list[tuple[float, float]]:
    """Simplifies an orthogonal path by eliminating loops, self-crossings, and
    redundant small jogs / doglegs while respecting port normal constraints,
    obstacle collision avoidance, and registered stream overlaps.
    """
    eps = 1e-4
    pts = compress_orthogonal_path(points)
    if len(pts) <= 2:
        return pts
    pts = remove_self_intersections(pts)

    def _matches_start_normal(p_from: tuple[float, float], p_to: tuple[float, float]) -> bool:
        if start_normal is None:
            return True
        dx = p_to[0] - p_from[0]
        dy = p_to[1] - p_from[1]
        if abs(start_normal[0]) >= abs(start_normal[1]) and start_normal[0] != 0:
            return dx * start_normal[0] > 0 and abs(dy) <= eps
        elif start_normal[1] != 0:
            return dy * start_normal[1] > 0 and abs(dx) <= eps
        return True

    def _matches_end_normal(p_from: tuple[float, float], p_to: tuple[float, float]) -> bool:
        if end_normal is None:
            return True
        dx = p_to[0] - p_from[0]
        dy = p_to[1] - p_from[1]
        if abs(end_normal[0]) >= abs(end_normal[1]) and end_normal[0] != 0:
            return dx * (-end_normal[0]) > 0 and abs(dy) <= eps
        elif end_normal[1] != 0:
            return dy * (-end_normal[1]) > 0 and abs(dx) <= eps
        return True

    def _is_seg_valid(p_a: tuple[float, float], p_b: tuple[float, float]) -> bool:
        if not is_route_clear([p_a, p_b], obs_list, source_box, target_box):
            return False
        if router is not None and router._has_collinear_overlap(p_a, p_b):
            return False
        return True

    obs_list = obstacles or []
    changed = True
    while changed:
        changed = False
        pts = compress_orthogonal_path(pts)
        n = len(pts)
        if n <= 2:
            break

        # 1. Collinear shortcut across multiple points (U-detours / collinear skips)
        for i in range(n):
            for j in range(n - 1, i + 1, -1):
                if j == i + 1:
                    continue
                p_start = pts[i]
                p_end = pts[j]
                dx = abs(p_start[0] - p_end[0])
                dy = abs(p_start[1] - p_end[1])
                if dx <= eps or dy <= eps:
                    if i == 0 and not _matches_start_normal(p_start, p_end):
                        continue
                    if j == n - 1 and not _matches_end_normal(p_start, p_end):
                        continue
                    if _is_seg_valid(p_start, p_end):
                        new_pts = pts[: i + 1] + pts[j:]
                        pts = compress_orthogonal_path(new_pts)
                        changed = True
                        break
            if changed:
                break

        if changed:
            continue

        # 2. Dogleg / Z-jog reduction: shift segments to align and eliminate small jogs
        n = len(pts)
        for i in range(n - 3):
            p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
            is_start_seg = i == 0
            is_end_seg = i + 3 == n - 1

            if abs(p1[0] - p0[0]) <= eps:  # p0->p1 is vertical, p1->p2 is horizontal
                # Option 1: shift horizontal segment p1->p2 to y = p0[1]
                test_p2 = (p2[0], p0[1])
                if (
                    (not is_start_seg or _matches_start_normal(p0, test_p2))
                    and _is_seg_valid(p0, test_p2)
                    and _is_seg_valid(test_p2, p3)
                ):
                    new_pts = pts[: i + 1] + [test_p2] + pts[i + 3 :]
                    pts = compress_orthogonal_path(new_pts)
                    changed = True
                    break

                # Option 2: shift horizontal segment p1->p2 to y = p3[1]
                test_p1 = (p1[0], p3[1])
                if (
                    (not is_end_seg or _matches_end_normal(test_p1, p3))
                    and _is_seg_valid(p0, test_p1)
                    and _is_seg_valid(test_p1, p3)
                ):
                    new_pts = pts[: i + 1] + [test_p1] + pts[i + 3 :]
                    pts = compress_orthogonal_path(new_pts)
                    changed = True
                    break
            else:  # p0->p1 is horizontal, p1->p2 is vertical
                # Option 1: shift vertical segment to x = p0[0]
                test_p2 = (p0[0], p2[1])
                if (
                    (not is_start_seg or _matches_start_normal(p0, test_p2))
                    and _is_seg_valid(p0, test_p2)
                    and _is_seg_valid(test_p2, p3)
                ):
                    new_pts = pts[: i + 1] + [test_p2] + pts[i + 3 :]
                    pts = compress_orthogonal_path(new_pts)
                    changed = True
                    break

                # Option 2: shift vertical segment to x = p3[0]
                test_p1 = (p3[0], p1[1])
                if (
                    (not is_end_seg or _matches_end_normal(test_p1, p3))
                    and _is_seg_valid(p0, test_p1)
                    and _is_seg_valid(test_p1, p3)
                ):
                    new_pts = pts[: i + 1] + [test_p1] + pts[i + 3 :]
                    pts = compress_orthogonal_path(new_pts)
                    changed = True
                    break

    return pts


class OrthogonalRouter:
    """Manhattan orthogonal A* router avoiding obstacle bounding boxes with turn minimization."""

    def __init__(
        self,
        grid_size: float = 10.0,
        turn_penalty: float = 60.0,
        obstacle_margin: float = 10.0,
        occupied_corners: set[tuple[float, float]] | None = None,
        occupied_segments: list[tuple[tuple[float, float], tuple[float, float]]] | None = None,
        corner_penalty: float = 500.0,
        collinear_penalty: float = 50.0,
    ):
        self.grid_size = max(grid_size, 1.0)
        self.turn_penalty = turn_penalty
        self.obstacle_margin = obstacle_margin
        self.occupied_corners: set[tuple[float, float]] = (
            set(occupied_corners) if occupied_corners is not None else set()
        )
        self.occupied_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
        self._h_segments: list[tuple[float, float, float]] = []
        self._v_segments: list[tuple[float, float, float]] = []
        self.corner_penalty = corner_penalty
        self.collinear_penalty = collinear_penalty

        if occupied_segments:
            for seg in occupied_segments:
                self._add_segment(seg[0], seg[1])

    def _snap(self, val: float) -> float:
        return round(val / self.grid_size) * self.grid_size

    def _add_segment(
        self, p1: tuple[float, float], p2: tuple[float, float], eps: float = 1e-4
    ) -> None:
        self.occupied_segments.append((p1, p2))
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[1] - p1[1])
        if dy <= eps and dx > eps:
            self._h_segments.append((p1[1], min(p1[0], p2[0]), max(p1[0], p2[0])))
        elif dx <= eps and dy > eps:
            self._v_segments.append((p1[0], min(p1[1], p2[1]), max(p1[1], p2[1])))

    def _rebuild_segment_index(self, eps: float = 1e-4) -> None:
        self._h_segments.clear()
        self._v_segments.clear()
        for p1, p2 in self.occupied_segments:
            dx = abs(p2[0] - p1[0])
            dy = abs(p2[1] - p1[1])
            if dy <= eps and dx > eps:
                self._h_segments.append((p1[1], min(p1[0], p2[0]), max(p1[0], p2[0])))
            elif dx <= eps and dy > eps:
                self._v_segments.append((p1[0], min(p1[1], p2[1]), max(p1[1], p2[1])))

    def _is_corner_occupied(self, pt: tuple[float, float], eps: float = 1e-4) -> bool:
        if pt in self.occupied_corners:
            return True
        for cx, cy in self.occupied_corners:
            if abs(cx - pt[0]) <= eps and abs(cy - pt[1]) <= eps:
                return True
        return False

    def _has_collinear_overlap(
        self, p1: tuple[float, float], p2: tuple[float, float], eps: float = 1e-4
    ) -> bool:
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[1] - p1[1])
        if dy <= eps and dx > eps:
            y = p1[1]
            min_x = min(p1[0], p2[0])
            max_x = max(p1[0], p2[0])
            for seg_y, seg_min_x, seg_max_x in self._h_segments:
                if abs(seg_y - y) <= eps:
                    if min(max_x, seg_max_x) - max(min_x, seg_min_x) > eps:
                        return True
        elif dx <= eps and dy > eps:
            x = p1[0]
            min_y = min(p1[1], p2[1])
            max_y = max(p1[1], p2[1])
            for seg_x, seg_min_y, seg_max_y in self._v_segments:
                if abs(seg_x - x) <= eps:
                    if min(max_y, seg_max_y) - max(min_y, seg_min_y) > eps:
                        return True
        return False

    def register_route(self, stream_id: str, path: Sequence[tuple[float, float]]) -> None:
        """Register the waypoints of a routed stream to avoid shared corners
        and collinear segment overlaps in subsequent routes.
        """
        compressed = compress_orthogonal_path(path)
        if len(compressed) >= 3:
            for pt in compressed[1:-1]:
                self.occupied_corners.add(pt)

        for i in range(len(compressed) - 1):
            self._add_segment(compressed[i], compressed[i + 1])

    def route(
        self,
        start: tuple[float, float],
        start_normal: tuple[float, float],
        end: tuple[float, float],
        end_normal: tuple[float, float],
        obstacles: Sequence[AABB],
        source_box: AABB | None = None,
        target_box: AABB | None = None,
    ) -> list[tuple[float, float]]:
        eps = 1e-4

        # Fast path 0: Collinear facing ports with direct unblocked line-of-sight
        is_h_collinear = abs(start[1] - end[1]) <= eps and (
            (start_normal[0] > 0 and end_normal[0] < 0 and start[0] < end[0])
            or (start_normal[0] < 0 and end_normal[0] > 0 and start[0] > end[0])
        )
        is_v_collinear = abs(start[0] - end[0]) <= eps and (
            (start_normal[1] > 0 and end_normal[1] < 0 and start[1] < end[1])
            or (start_normal[1] < 0 and end_normal[1] > 0 and start[1] > end[1])
        )
        if (is_h_collinear or is_v_collinear) and not self._has_collinear_overlap(start, end):
            if is_route_clear([start, end], obstacles, source_box, target_box, margin=0.0):
                return [start, end]

        # Fast path 1: Facing ports 2-turn Z/S-bend with direct unblocked line-of-sight
        if (
            start_normal[0] != 0
            and end_normal[0] != 0
            and start_normal[0] * end_normal[0] < 0
            and (end[0] - start[0]) * start_normal[0] > self.grid_size
        ):
            x_mid = round(((start[0] + end[0]) / 2.0) / self.grid_size) * self.grid_size
            candidate = compress_orthogonal_path(
                [start, (x_mid, start[1]), (x_mid, end[1]), end]
            )
            if not any(
                self._has_collinear_overlap(candidate[i], candidate[i + 1])
                for i in range(len(candidate) - 1)
            ):
                if is_route_clear(candidate, obstacles, source_box, target_box, margin=0.0):
                    return candidate

        if (
            start_normal[1] != 0
            and end_normal[1] != 0
            and start_normal[1] * end_normal[1] < 0
            and (end[1] - start[1]) * start_normal[1] > self.grid_size
        ):
            y_mid = round(((start[1] + end[1]) / 2.0) / self.grid_size) * self.grid_size
            candidate = compress_orthogonal_path(
                [start, (start[0], y_mid), (end[0], y_mid), end]
            )
            if not any(
                self._has_collinear_overlap(candidate[i], candidate[i + 1])
                for i in range(len(candidate) - 1)
            ):
                if is_route_clear(candidate, obstacles, source_box, target_box, margin=0.0):
                    return candidate

        lead_len = self.grid_size * 2
        grid = self.grid_size

        # 1. Calculate clean lead step from start along start_normal to grid line
        if abs(start_normal[0]) >= abs(start_normal[1]) and start_normal[0] != 0:
            dx = 1 if start_normal[0] > 0 else -1
            x_g = (
                ceil((start[0] + lead_len) / grid) * grid
                if dx > 0
                else floor((start[0] - lead_len) / grid) * grid
            )
            y_g = round(start[1] / grid) * grid
            start_grid = (x_g, y_g)
            start_lead_raw = [start, (x_g, start[1]), start_grid]
        elif start_normal[1] != 0:
            dy = 1 if start_normal[1] > 0 else -1
            y_g = (
                ceil((start[1] + lead_len) / grid) * grid
                if dy > 0
                else floor((start[1] - lead_len) / grid) * grid
            )
            x_g = round(start[0] / grid) * grid
            start_grid = (x_g, y_g)
            start_lead_raw = [start, (start[0], y_g), start_grid]
        else:
            start_grid = (self._snap(start[0]), self._snap(start[1]))
            start_lead_raw = [start, (start_grid[0], start[1]), start_grid]

        # 2. Calculate clean approach to end along end_normal from grid line
        if abs(end_normal[0]) >= abs(end_normal[1]) and end_normal[0] != 0:
            dx = 1 if end_normal[0] > 0 else -1
            x_ge = (
                ceil((end[0] + lead_len) / grid) * grid
                if dx > 0
                else floor((end[0] - lead_len) / grid) * grid
            )
            y_ge = round(end[1] / grid) * grid
            end_grid = (x_ge, y_ge)
            end_lead_raw = [end_grid, (x_ge, end[1]), end]
        elif end_normal[1] != 0:
            dy = 1 if end_normal[1] > 0 else -1
            y_ge = (
                ceil((end[1] + lead_len) / grid) * grid
                if dy > 0
                else floor((end[1] - lead_len) / grid) * grid
            )
            x_ge = round(end[0] / grid) * grid
            end_grid = (x_ge, y_ge)
            end_lead_raw = [end_grid, (end[0], y_ge), end]
        else:
            end_grid = (self._snap(end[0]), self._snap(end[1]))
            end_lead_raw = [end_grid, (end_grid[0], end[1]), end]

        start_lead_path = compress_orthogonal_path(start_lead_raw)
        end_lead_path = compress_orthogonal_path(end_lead_raw)

        if start_grid == end_grid:
            raw = start_lead_path + end_lead_path[1:]
            return simplify_orthogonal_path(
                raw,
                obstacles,
                start_normal,
                end_normal,
                source_box,
                target_box,
                router=self,
            )

        # 3. A* Search
        expanded_obs = [
            obs.expanded(self.obstacle_margin)
            for obs in obstacles
            if obs is not source_box and obs is not target_box
        ]

        def is_blocked(pt: tuple[float, float]) -> bool:
            for obs in expanded_obs:
                if obs.contains_point(pt):
                    return True
            return False

        open_set: list[
            tuple[float, float, tuple[float, float], int, int, list[tuple[float, float]]]
        ] = []
        initial_dir = (int(start_normal[0]), int(start_normal[1]))

        heapq.heappush(
            open_set,
            (
                hypot(end_grid[0] - start_grid[0], end_grid[1] - start_grid[1]),
                0.0,
                start_grid,
                initial_dir[0],
                initial_dir[1],
                [start_grid],
            ),
        )

        visited: dict[tuple[tuple[float, float], int, int], float] = {}
        best_path = None

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        # Bounding box for search exploration
        all_xs = (
            [start[0], end[0], start_grid[0], end_grid[0]]
            + [b.min_x for b in expanded_obs]
            + [b.max_x for b in expanded_obs]
        )
        all_ys = (
            [start[1], end[1], start_grid[1], end_grid[1]]
            + [b.min_y for b in expanded_obs]
            + [b.max_y for b in expanded_obs]
        )
        min_bound_x = min(all_xs) - self.grid_size * 8
        max_bound_x = max(all_xs) + self.grid_size * 8
        min_bound_y = min(all_ys) - self.grid_size * 8
        max_bound_y = max(all_ys) + self.grid_size * 8

        if len(self.occupied_segments) != len(self._h_segments) + len(self._v_segments):
            self._rebuild_segment_index()

        max_iterations = 3000
        iterations = 0

        while open_set and iterations < max_iterations:
            iterations += 1
            f, g, curr, dx, dy, path = heapq.heappop(open_set)

            if curr == end_grid:
                best_path = path
                break

            state = (curr, dx, dy)
            if state in visited and visited[state] <= g:
                continue
            visited[state] = g

            for ndx, ndy in directions:
                # Disallow immediate 180-degree reversal
                if ndx == -dx and ndy == -dy and (dx != 0 or dy != 0):
                    continue

                nxt = (curr[0] + ndx * self.grid_size, curr[1] + ndy * self.grid_size)

                if not (
                    min_bound_x <= nxt[0] <= max_bound_x and min_bound_y <= nxt[1] <= max_bound_y
                ):
                    continue

                if nxt != end_grid and is_blocked(nxt):
                    continue

                if target_box is not None and seg_intersects_box(curr, nxt, target_box, margin=0.0):
                    continue

                if source_box is not None and seg_intersects_box(curr, nxt, source_box, margin=0.0):
                    continue

                turned = 1 if (dx, dy) != (ndx, ndy) and (dx != 0 or dy != 0) else 0
                step_cost = self.grid_size + turned * self.turn_penalty

                if turned and (self._is_corner_occupied(curr) or self._is_corner_occupied(nxt)):
                    step_cost += self.corner_penalty

                if self._has_collinear_overlap(curr, nxt):
                    step_cost += self.collinear_penalty

                new_g = g + step_cost
                new_h = abs(nxt[0] - end_grid[0]) + abs(nxt[1] - end_grid[1])
                new_f = new_g + new_h

                heapq.heappush(open_set, (new_f, new_g, nxt, ndx, ndy, path + [nxt]))

        if best_path is None:
            # Fallback simple orthogonal step
            mid_x = self._snap((start_grid[0] + end_grid[0]) / 2.0)
            best_path = [
                start_grid,
                (mid_x, start_grid[1]),
                (mid_x, end_grid[1]),
                end_grid,
            ]

        full_path = start_lead_path[:-1] + best_path + end_lead_path[1:]
        return simplify_orthogonal_path(
            full_path,
            obstacles,
            start_normal,
            end_normal,
            source_box,
            target_box,
            router=self,
        )
