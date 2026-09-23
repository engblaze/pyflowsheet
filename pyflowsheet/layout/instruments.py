from __future__ import annotations

import re
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

        inst_text = f"{inst.id} {getattr(inst, 'name', '')}".lower()
        inst_tokens = set(re.findall(r"\w+", inst_text))

        # Tier 2.5: Direct equipment ID or name match in instrument text
        named_matches: list[tuple[float, Any]] = []
        for u in macro_units:
            uid_lower = u.id.lower()
            uname_lower = getattr(u, "name", "").lower()
            utype_lower = (getattr(u, "type", None) or u.__class__.__name__).lower()

            if uid_lower in inst_tokens:
                named_matches.append((len(uid_lower) + 100.0, u))
            if uname_lower:
                u_name_tokens = set(re.findall(r"\w+", uname_lower)) - {
                    "module",
                    "cell",
                    "pump",
                    "valve",
                    "point",
                    "unit",
                    "system",
                }
                if u_name_tokens and u_name_tokens.issubset(inst_tokens):
                    named_matches.append((len(uname_lower) + 50.0, u))
            if "membrane" in inst_tokens and "membrane" in utype_lower:
                named_matches.append((80.0, u))
            if "reactor" in inst_tokens and "reactor" in uname_lower:
                named_matches.append((90.0, u))
            if "reactor" in inst_tokens and ("stirred" in uname_lower or "mixer" in uid_lower):
                named_matches.append((80.0, u))

        if named_matches:
            named_matches.sort(key=lambda m: m[0], reverse=True)
            return named_matches[0][1]

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

                def candidate_score(c: Any) -> float:
                    c_name = getattr(c, "name", "").lower()
                    c_type = c.__class__.__name__.lower()
                    c_tokens = set(re.findall(r"\w+", c_name))
                    shared = (inst_tokens & c_tokens) - {"unit", "valve", "point", "feed"}
                    score = len(shared) * 50.0

                    is_passive = "checkvalve" in c_type or "sampling" in c_type
                    is_relief = "safetyrelief" in c_type or "rupturedisc" in c_type

                    if is_passive or is_relief:
                        score -= 60.0

                    if var == "F":
                        if "pump" in c_type or "controlvalve" in c_type:
                            score += 30.0
                    elif var == "L":
                        if any(
                            k in c_type for k in ["vessel", "cell", "tank", "flotation", "mixer"]
                        ):
                            score += 40.0
                    elif var == "P":
                        if "controlvalve" in c_type or "pump" in c_type:
                            score += 20.0
                    return score

                return max(candidates, key=candidate_score)

        # Name / description substring matching fallback
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
            leader_len = max(leader_len, hh / 2.0 + act_h * 1.1 + r + 12.0)
        elif hh > 40.0 and orientation == "horizontal":
            leader_len = max(leader_len, hh / 2.0 + r + 10.0)
        elif hw > 40.0 and orientation == "vertical":
            leader_len = max(leader_len, hw / 2.0 + r + 10.0)

        return tap, orientation, leader_len

    def place_and_route(
        self,
        tap: tuple[float, float],
        pipe_orientation: Literal["horizontal", "vertical"],
        spatial_index: SpatialIndex,
        host: Any | None = None,
        inst: Any | None = None,
        port_keepouts: list[tuple[str, AABB, set[str]]] | None = None,
        diagram_bounds: AABB | None = None,
    ) -> InstrumentTapPlacement:
        tx, ty = tap
        r = self.balloon_radius
        d = self.leader_length

        SQRT2_2 = 0.7071067811865476

        if pipe_orientation == "horizontal":
            candidates = [
                ("up", 0.0, -1.0, 0.0),
                ("down", 0.0, 1.0, 5.0),
                ("up-right", SQRT2_2, -SQRT2_2, 40.0),
                ("up-left", -SQRT2_2, -SQRT2_2, 45.0),
                ("down-right", SQRT2_2, SQRT2_2, 50.0),
                ("down-left", -SQRT2_2, SQRT2_2, 55.0),
            ]
        else:
            candidates = [
                ("right", 1.0, 0.0, 0.0),
                ("left", -1.0, 0.0, 5.0),
                ("up-right", SQRT2_2, -SQRT2_2, 40.0),
                ("down-right", SQRT2_2, SQRT2_2, 45.0),
                ("up-left", -SQRT2_2, -SQRT2_2, 50.0),
                ("down-left", -SQRT2_2, SQRT2_2, 55.0),
            ]

        # Extract host dimensions if available
        half_w = host.size[0] / 2.0 if host is not None and hasattr(host, "size") else 0.0
        half_h = host.size[1] / 2.0 if host is not None and hasattr(host, "size") else 0.0
        act_h = (
            getattr(host, "actuator_height", 24.0)
            if (host is not None and hasattr(host, "actuator_height"))
            else 0.0
        )
        host_id = getattr(host, "id", None) if host is not None else None

        # Build local port keepouts if none provided but host has ports
        if port_keepouts is None and host is not None and hasattr(host, "ports") and host.ports:
            port_keepouts = []
            for pname, p in host.ports.items():
                pos = p.get_position()
                nx, ny = p.normal
                c_len = 35.0
                c_w = 14.0
                if abs(nx) > 0.5:
                    min_x = min(pos[0], pos[0] + nx * c_len)
                    max_x = max(pos[0], pos[0] + nx * c_len)
                    min_y = pos[1] - c_w
                    max_y = pos[1] + c_w
                    port_keepouts.append(
                        (f"{host_id}:{pname}", AABB(min_x, min_y, max_x, max_y), set())
                    )
                elif abs(ny) > 0.5:
                    min_x = pos[0] - c_w
                    max_x = pos[0] + c_w
                    min_y = min(pos[1], pos[1] + ny * c_len)
                    max_y = max(pos[1], pos[1] + ny * c_len)
                    port_keepouts.append(
                        (f"{host_id}:{pname}", AABB(min_x, min_y, max_x, max_y), set())
                    )

        scored_candidates = []
        for cname, ux, uy, base_penalty in candidates:
            # Distance from tap to balloon center
            if host is not None and (half_w > 0.0 or half_h > 0.0):
                h_eff = half_h + act_h if (uy < -0.1 and act_h > 0.0) else half_h
                tx_dist = half_w / abs(ux) if abs(ux) > 1e-4 else 1e9
                ty_dist = h_eff / abs(uy) if abs(uy) > 1e-4 else 1e9
                t_box = min(tx_dist, ty_dist)
                cand_dist = max(d, t_box + r + 16.0)
            else:
                cand_dist = d

            cx = tx + ux * cand_dist
            cy = ty + uy * cand_dist
            cand_box = AABB(cx - r, cy - r, cx + r, cy + r)

            cost = base_penalty

            # Diagram bounds
            if diagram_bounds is not None and not diagram_bounds.contains_point((cx, cy)):
                cost += 1_000_000.0

            # Obstacle checks from spatial_index
            for item in spatial_index.all_items():
                iid, ibox = item[0], item[1]
                if host_id is not None and iid == host_id:
                    continue
                # Hard obstacle collision
                if cand_box.intersects(ibox):
                    cost += 100_000.0
                # Obstacle proximity / clearance penalty (8px margin)
                expanded = cand_box.expanded(8.0)
                if expanded.intersects(ibox):
                    cost += 5_000.0
                # Leader line penetration through another equipment
                if ibox.intersects_segment(tap, (cx, cy)):
                    cost += 80_000.0

            # Port keepout corridor checks
            if port_keepouts:
                inst_id = getattr(inst, "id", None) if inst is not None else None
                for pid, pkbox, conn_uids in port_keepouts:
                    if inst_id is not None and inst_id in conn_uids:
                        continue
                    if cand_box.intersects(pkbox):
                        cost += 50_000.0
                    if pkbox.intersects_segment(tap, (cx, cy)):
                        cost += 20_000.0

            scored_candidates.append((cost, (cx, cy), cand_box))

        scored_candidates.sort(key=lambda item: item[0])
        best_cost, chosen_center, chosen_box = scored_candidates[0]

        return InstrumentTapPlacement(
            tap=tap,
            balloon_center=chosen_center,
            leader_line=[tap, chosen_center],
            balloon_box=chosen_box,
        )
