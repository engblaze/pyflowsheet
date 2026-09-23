from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..instruments.tag import parse_isa_tag
from .spatial import AABB, SpatialIndex


def is_instrument(u: Any) -> bool:
    if u is None:
        return False
    return (
        getattr(u, "type", "") == "Instrument"
        or u.__class__.__name__ == "Instrument"
        or hasattr(u, "balloon_type")
    )


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

    @classmethod
    def resolve_host(
        cls,
        inst: Any,
        unit_operations: dict[str, Any],
        streams: dict[str, Any] | list[Any] | None = None,
        visited: set[str] | None = None,
    ) -> Any | None:
        """3-tier host resolution hierarchy for an instrument:
        - Tier 1: Explicit layout_hints.relative_to
        - Tier 2: Outgoing (or incoming) signal stream target
        - Tier 3: ISA loop number matching against equipment IDs/tags, then equipment
          name substring.
        """
        if visited is None:
            visited = set()
        if inst.id in visited:
            return None
        visited.add(inst.id)

        macro_units = [u for u in unit_operations.values() if not is_instrument(u)]

        # Tier 1: Explicit layout_hints
        hints = getattr(inst, "layout_hints", None)
        if hints:
            rel_id = None
            if isinstance(hints, dict):
                rel_id = hints.get("relative_to") or hints.get("host") or hints.get("parent")
            else:
                rel_id = (
                    getattr(hints, "relative_to", None)
                    or getattr(hints, "host", None)
                    or getattr(hints, "parent", None)
                )
            if rel_id and rel_id in unit_operations:
                target = unit_operations[rel_id]
                if not is_instrument(target):
                    return target
                sub_target = cls.resolve_host(target, unit_operations, streams, visited)
                if sub_target is not None:
                    return sub_target

        # Tier 2: Signal stream target
        stream_list: list[Any] = (
            list(streams.values()) if isinstance(streams, dict) else list(streams or [])
        )

        # Check outgoing streams first
        for s in stream_list:
            u_from = getattr(s.fromPort, "unitoperation", getattr(s.fromPort, "parent", None))
            u_to = getattr(s.toPort, "unitoperation", getattr(s.toPort, "parent", None))
            if u_from == inst and u_to is not None and u_to != inst:
                if not is_instrument(u_to) and u_to.id in unit_operations:
                    return u_to
                elif is_instrument(u_to):
                    sub_host = cls.resolve_host(u_to, unit_operations, stream_list, visited)
                    if sub_host is not None:
                        return sub_host

        # Check incoming streams
        for s in stream_list:
            u_from = getattr(s.fromPort, "unitoperation", getattr(s.fromPort, "parent", None))
            u_to = getattr(s.toPort, "unitoperation", getattr(s.toPort, "parent", None))
            if u_to == inst and u_from is not None and u_from != inst:
                if not is_instrument(u_from) and u_from.id in unit_operations:
                    return u_from
                elif is_instrument(u_from):
                    sub_host = cls.resolve_host(u_from, unit_operations, stream_list, visited)
                    if sub_host is not None:
                        return sub_host

        # Tier 3: ISA loop number matching
        tag_obj = getattr(inst, "tag", None)
        if not tag_obj or isinstance(tag_obj, str):
            tag_obj = parse_isa_tag(str(tag_obj or inst.id))
        loop_num = getattr(tag_obj, "loop_number", "")
        if not loop_num:
            loop_num = parse_isa_tag(inst.id).loop_number

        if loop_num:
            exact_matches = []
            contains_matches = []
            for u in macro_units:
                u_tag = parse_isa_tag(u.id)
                if getattr(u_tag, "loop_number", None) == loop_num:
                    exact_matches.append(u)
                elif loop_num in u.id or loop_num in getattr(u, "name", ""):
                    contains_matches.append(u)

            candidates = exact_matches or contains_matches
            if candidates:
                var = getattr(tag_obj, "measured_variable", "") or (
                    tag_obj.letters[:1] if tag_obj.letters else ""
                )
                var_matches = [
                    c
                    for c in candidates
                    if c.id.upper().startswith(var) or parse_isa_tag(c.id).letters.startswith(var)
                ]
                if var_matches:
                    return var_matches[0]

                valves = [
                    c
                    for c in candidates
                    if "valve" in c.__class__.__name__.lower() or "valve" in c.id.lower()
                ]
                if valves:
                    return valves[0]

                return candidates[0]

        # Name / description substring matching fallback
        inst_text = f"{inst.id} {getattr(inst, 'name', '')}".lower()
        for u in macro_units:
            if u.id.lower() in inst_text or (
                getattr(u, "name", "") and u.name.lower() in inst_text
            ):
                return u

        return None

    @staticmethod
    def get_tap_and_orientation(
        host: Any,
        inst: Any | None = None,
    ) -> tuple[tuple[float, float], Literal["horizontal", "vertical"], float]:
        """Calculates the tap coordinate, orientation, and clearance leader length
        for a host unit.
        """
        hx, hy = host.position
        hw, hh = host.size
        tx = hx + hw / 2.0
        ty = hy + hh / 2.0
        tap = (tx, ty)

        orientation: Literal["horizontal", "vertical"] = "horizontal"
        if hasattr(host, "ports") and "In" in host.ports and "Out" in host.ports:
            pin = host.ports["In"].get_position()
            pout = host.ports["Out"].get_position()
            if abs(pout[1] - pin[1]) > abs(pout[0] - pin[0]):
                orientation = "vertical"
        elif hh > hw * 1.5:
            orientation = "vertical"

        inst_size = getattr(inst, "size", (24.0, 24.0)) if inst is not None else (24.0, 24.0)
        r = inst_size[0] / 2.0
        leader_len = 40.0
        if hasattr(host, "actuator_height"):
            act_h = getattr(host, "actuator_height", 24.0)
            leader_len = max(leader_len, hh / 2.0 + act_h * 1.1 + r + 8.0)
        elif hh > 40.0 and orientation == "horizontal":
            leader_len = max(leader_len, hh / 2.0 + r + 8.0)
        elif hw > 40.0 and orientation == "vertical":
            leader_len = max(leader_len, hw / 2.0 + r + 8.0)

        return tap, orientation, leader_len

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
