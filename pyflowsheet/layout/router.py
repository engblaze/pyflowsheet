from __future__ import annotations

import heapq
from collections.abc import Sequence
from math import hypot

from .spatial import AABB


def compress_orthogonal_path(points: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    """Removes redundant collinear points from an orthogonal path."""
    if len(points) <= 2:
        return list(points)

    compressed = [points[0]]
    for i in range(1, len(points) - 1):
        prev = compressed[-1]
        curr = points[i]
        nxt = points[i + 1]

        # Check if curr is collinear with prev and nxt
        dx1, dy1 = curr[0] - prev[0], curr[1] - prev[1]
        dx2, dy2 = nxt[0] - curr[0], nxt[1] - curr[1]

        if (dx1 == 0 and dx2 == 0) or (dy1 == 0 and dy2 == 0):
            continue  # Collinear point skipped
        compressed.append(curr)

    compressed.append(points[-1])
    return compressed


class OrthogonalRouter:
    """Manhattan orthogonal A* router avoiding obstacle bounding boxes with turn minimization."""

    def __init__(
        self,
        grid_size: float = 10.0,
        turn_penalty: float = 60.0,
        obstacle_margin: float = 10.0,
    ):
        self.grid_size = max(grid_size, 1.0)
        self.turn_penalty = turn_penalty
        self.obstacle_margin = obstacle_margin

    def _snap(self, val: float) -> float:
        return round(val / self.grid_size) * self.grid_size

    def route(
        self,
        start: tuple[float, float],
        start_normal: tuple[float, float],
        end: tuple[float, float],
        end_normal: tuple[float, float],
        obstacles: Sequence[AABB],
    ) -> list[tuple[float, float]]:
        # Fast path: direct horizontal or vertical connection with no obstacles
        expanded_obs = [obs.expanded(self.obstacle_margin) for obs in obstacles]

        lead_len = self.grid_size * 2
        p_start_lead = (
            self._snap(start[0] + start_normal[0] * lead_len),
            self._snap(start[1] + start_normal[1] * lead_len),
        )
        p_end_lead = (
            self._snap(end[0] + end_normal[0] * lead_len),
            self._snap(end[1] + end_normal[1] * lead_len),
        )

        def is_blocked(pt: tuple[float, float]) -> bool:
            for obs in expanded_obs:
                if obs.contains_point(pt):
                    return True
            return False

        # If lead points match and no obstacle, direct connect
        if p_start_lead == p_end_lead:
            return compress_orthogonal_path([start, p_start_lead, end])

        # Priority queue for A*: (cost_f, cost_g, (x, y), dir_x, dir_y, path)
        open_set: list[
            tuple[float, float, tuple[float, float], int, int, list[tuple[float, float]]]
        ] = []
        initial_dir = (int(start_normal[0]), int(start_normal[1]))

        heapq.heappush(
            open_set,
            (
                hypot(p_end_lead[0] - p_start_lead[0], p_end_lead[1] - p_start_lead[1]),
                0.0,
                p_start_lead,
                initial_dir[0],
                initial_dir[1],
                [start, p_start_lead],
            ),
        )

        visited: dict[tuple[tuple[float, float], int, int], float] = {}
        best_path = None

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        # Bounding box for search exploration
        all_xs = (
            [start[0], end[0]] + [b.min_x for b in expanded_obs] + [b.max_x for b in expanded_obs]
        )
        all_ys = (
            [start[1], end[1]] + [b.min_y for b in expanded_obs] + [b.max_y for b in expanded_obs]
        )
        min_bound_x = min(all_xs) - self.grid_size * 8
        max_bound_x = max(all_xs) + self.grid_size * 8
        min_bound_y = min(all_ys) - self.grid_size * 8
        max_bound_y = max(all_ys) + self.grid_size * 8

        max_iterations = 3000
        iterations = 0

        while open_set and iterations < max_iterations:
            iterations += 1
            f, g, curr, dx, dy, path = heapq.heappop(open_set)

            if curr == p_end_lead:
                best_path = path + [end]
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

                if nxt != p_end_lead and is_blocked(nxt):
                    continue

                turned = 1 if (dx, dy) != (ndx, ndy) and (dx != 0 or dy != 0) else 0
                step_cost = self.grid_size + turned * self.turn_penalty
                new_g = g + step_cost
                new_h = abs(nxt[0] - p_end_lead[0]) + abs(nxt[1] - p_end_lead[1])
                new_f = new_g + new_h

                heapq.heappush(open_set, (new_f, new_g, nxt, ndx, ndy, path + [nxt]))

        if best_path is None:
            # Fallback simple orthogonal step
            mid_x = (p_start_lead[0] + p_end_lead[0]) / 2.0
            best_path = [
                start,
                p_start_lead,
                (mid_x, p_start_lead[1]),
                (mid_x, p_end_lead[1]),
                p_end_lead,
                end,
            ]

        return compress_orthogonal_path(best_path)
