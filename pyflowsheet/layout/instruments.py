from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .spatial import AABB, SpatialIndex


@dataclass
class InstrumentTapPlacement:
    tap: tuple[float, float]
    balloon_center: tuple[float, float]
    leader_line: list[tuple[float, float]]
    balloon_box: AABB


class InstrumentTapRouter:
    """Evaluates lowest-congestion side along a pipe segment and routes standard leader
    lines from taps to ISA-5.1 instrument balloons.
    """

    def __init__(self, leader_length: float = 40.0, balloon_radius: float = 12.0):
        self.leader_length = leader_length
        self.balloon_radius = balloon_radius

    def place_and_route(
        self,
        tap: tuple[float, float],
        pipe_orientation: Literal["horizontal", "vertical"],
        spatial_index: SpatialIndex,
    ) -> InstrumentTapPlacement:
        tx, ty = tap
        r = self.balloon_radius
        d = self.leader_length

        if pipe_orientation == "horizontal":
            # Candidates: Above (ty - d) or Below (ty + d)
            cand_above = (tx, ty - d)
            cand_below = (tx, ty + d)

            box_above = AABB(tx - r, ty - d - r, tx + r, ty - d + r)
            box_below = AABB(tx - r, ty + d - r, tx + r, ty + d + r)

            cost_above = len(spatial_index.query_intersects(box_above))
            cost_below = len(spatial_index.query_intersects(box_below))

            if cost_above <= cost_below:
                chosen_center = cand_above
                chosen_box = box_above
            else:
                chosen_center = cand_below
                chosen_box = box_below
        else:
            # Candidates: Right (tx + d) or Left (tx - d)
            cand_right = (tx + d, ty)
            cand_left = (tx - d, ty)

            box_right = AABB(tx + d - r, ty - r, tx + d + r, ty + r)
            box_left = AABB(tx - d - r, ty - r, tx - d + r, ty + r)

            cost_right = len(spatial_index.query_intersects(box_right))
            cost_left = len(spatial_index.query_intersects(box_left))

            if cost_right <= cost_left:
                chosen_center = cand_right
                chosen_box = box_right
            else:
                chosen_center = cand_left
                chosen_box = box_left

        return InstrumentTapPlacement(
            tap=tap,
            balloon_center=chosen_center,
            leader_line=[tap, chosen_center],
            balloon_box=chosen_box,
        )
