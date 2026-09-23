from __future__ import annotations

import heapq
from collections.abc import Sequence
from math import hypot

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
    ) -> list[tuple[float, float]]:
        expanded_obs = [obs.expanded(self.obstacle_margin) for obs in obstacles]

        def is_blocked(pt: tuple[float, float]) -> bool:
            for obs in expanded_obs:
                if obs.contains_point(pt):
                    return True
            return False

        lead_len = self.grid_size * 2

        # 1. Calculate lead step from start along start_normal without changing
        # transverse coordinate
        if abs(start_normal[0]) >= abs(start_normal[1]) and start_normal[0] != 0:
            p_start_lead = (start[0] + start_normal[0] * lead_len, start[1])
            start_grid = (self._snap(p_start_lead[0]), self._snap(start[1]))
            start_lead_raw = [
                start,
                p_start_lead,
                (p_start_lead[0], start_grid[1]),
                start_grid,
            ]
        elif start_normal[1] != 0:
            p_start_lead = (start[0], start[1] + start_normal[1] * lead_len)
            start_grid = (self._snap(start[0]), self._snap(p_start_lead[1]))
            start_lead_raw = [
                start,
                p_start_lead,
                (start_grid[0], p_start_lead[1]),
                start_grid,
            ]
        else:
            p_start_lead = start
            start_grid = (self._snap(start[0]), self._snap(start[1]))
            start_lead_raw = [
                start,
                (start_grid[0], start[1]),
                start_grid,
            ]

        # 2. Calculate approach to end along end_normal
        if abs(end_normal[0]) >= abs(end_normal[1]) and end_normal[0] != 0:
            p_end_lead = (end[0] + end_normal[0] * lead_len, end[1])
            end_grid = (self._snap(p_end_lead[0]), self._snap(end[1]))
            end_lead_raw = [
                end_grid,
                (p_end_lead[0], end_grid[1]),
                p_end_lead,
                end,
            ]
        elif end_normal[1] != 0:
            p_end_lead = (end[0], end[1] + end_normal[1] * lead_len)
            end_grid = (self._snap(end[0]), self._snap(p_end_lead[1]))
            end_lead_raw = [
                end_grid,
                (end_grid[0], p_end_lead[1]),
                p_end_lead,
                end,
            ]
        else:
            p_end_lead = end
            end_grid = (self._snap(end[0]), self._snap(end[1]))
            end_lead_raw = [
                end_grid,
                (end_grid[0], end[1]),
                end,
            ]

        start_lead_path: list[tuple[float, float]] = []
        for pt in start_lead_raw:
            if not start_lead_path or pt != start_lead_path[-1]:
                start_lead_path.append(pt)

        end_lead_path: list[tuple[float, float]] = []
        for pt in end_lead_raw:
            if not end_lead_path or pt != end_lead_path[-1]:
                end_lead_path.append(pt)

        # Fast path: If lead points match and no obstacle, direct connect
        if (
            p_start_lead == p_end_lead
            and not is_blocked(p_start_lead)
            and not self._is_corner_occupied(p_start_lead)
            and not self._has_collinear_overlap(start, p_start_lead)
            and not self._has_collinear_overlap(p_start_lead, end)
        ):
            return compress_orthogonal_path([start, p_start_lead, end])

        if start_grid == end_grid:
            return compress_orthogonal_path(start_lead_path + end_lead_path[1:])

        # Priority queue for A*: (cost_f, cost_g, (x, y), dir_x, dir_y, path)
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
        return compress_orthogonal_path(full_path)
