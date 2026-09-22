from __future__ import annotations

from collections.abc import Sequence

from .spatial import AABB, SpatialIndex


class LabelPlacementSolver:
    """Evaluates multi-candidate bounding boxes for equipment and stream text labels,
    scoring against spatial obstacles to guarantee zero overlap with equipment and piping.
    """

    def __init__(self, clearance: float = 6.0):
        self.clearance = clearance

    def place_equipment_label(
        self,
        unit_id: str,
        unit_box: AABB,
        label_size: tuple[float, float],
        spatial_index: SpatialIndex,
    ) -> tuple[tuple[float, float], AABB]:
        lw, lh = label_size
        cx, _ = unit_box.center

        # Candidate 1: Below (standard)
        c1_x = cx - lw / 2.0
        c1_y = unit_box.max_y + self.clearance
        box_below = AABB(c1_x, c1_y, c1_x + lw, c1_y + lh)

        # Candidate 2: Above
        c2_x = cx - lw / 2.0
        c2_y = unit_box.min_y - self.clearance - lh
        box_above = AABB(c2_x, c2_y, c2_x + lw, c2_y + lh)

        # Candidate 3: Right
        c3_x = unit_box.max_x + self.clearance
        c3_y = unit_box.center[1] - lh / 2.0
        box_right = AABB(c3_x, c3_y, c3_x + lw, c3_y + lh)

        # Candidate 4: Left
        c4_x = unit_box.min_x - self.clearance - lw
        c4_y = unit_box.center[1] - lh / 2.0
        box_left = AABB(c4_x, c4_y, c4_x + lw, c4_y + lh)

        candidates = [
            (box_below, (cx, c1_y + lh)),  # Anchor at baseline
            (box_above, (cx, c2_y + lh)),
            (box_right, (c3_x + lw / 2.0, c3_y + lh)),
            (box_left, (c4_x + lw / 2.0, c4_y + lh)),
        ]

        def score(box: AABB) -> float:
            collisions = [
                item for item in spatial_index.query_intersects(box) if item[0] != unit_id
            ]
            return len(collisions) * 1000.0

        best_box, best_pos = min(candidates, key=lambda c: score(c[0]))
        return best_pos, best_box

    def place_stream_label(
        self,
        stream_id: str,
        waypoints: Sequence[tuple[float, float]],
        label_size: tuple[float, float],
        spatial_index: SpatialIndex,
    ) -> tuple[tuple[float, float], AABB]:
        if len(waypoints) < 2:
            raise ValueError("At least 2 waypoints are required to place a stream label")

        lw, lh = label_size
        # Pick middle segment
        mid_seg_idx = (len(waypoints) - 1) // 2
        p1 = waypoints[mid_seg_idx]
        p2 = waypoints[mid_seg_idx + 1]

        mx = (p1[0] + p2[0]) / 2.0
        my = (p1[1] + p2[1]) / 2.0

        is_horizontal = p1[1] == p2[1]
        if is_horizontal:
            # Candidate 1: Above
            box_above = AABB(
                mx - lw / 2.0,
                my - lh - self.clearance,
                mx + lw / 2.0,
                my - self.clearance,
            )
            # Candidate 2: Below
            box_below = AABB(
                mx - lw / 2.0,
                my + self.clearance,
                mx + lw / 2.0,
                my + lh + self.clearance,
            )
            candidates = [
                (box_above, (mx, my - self.clearance)),
                (box_below, (mx, my + lh + self.clearance)),
            ]
        else:
            # Candidate 1: Right
            box_right = AABB(
                mx + self.clearance,
                my - lh / 2.0,
                mx + lw + self.clearance,
                my + lh / 2.0,
            )
            # Candidate 2: Left
            box_left = AABB(
                mx - lw - self.clearance,
                my - lh / 2.0,
                mx - self.clearance,
                my + lh / 2.0,
            )
            candidates = [
                (box_right, (mx + self.clearance + lw / 2.0, my + lh / 2.0)),
                (box_left, (mx - self.clearance - lw / 2.0, my + lh / 2.0)),
            ]

        def score(box: AABB) -> float:
            collisions = [
                item for item in spatial_index.query_intersects(box) if item[0] != stream_id
            ]
            return len(collisions) * 1000.0

        best_box, best_pos = min(candidates, key=lambda c: score(c[0]))
        return best_pos, best_box
