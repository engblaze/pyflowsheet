from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from .spatial import AABB


@dataclass
class InlinePlacement:
    component_id: str
    center: tuple[float, float]
    orientation: Literal["horizontal", "vertical"]
    knockout_box: AABB


class InlineSequencer:
    """Sequences and spaces inline pumps, valves, and specialty fittings along
    the primary straight segment of a stream with background knockout masks.
    """

    def __init__(self, knockout_padding: float = 4.0):
        self.knockout_padding = knockout_padding

    def _extract_id(self, item: Any) -> str:
        """Extracts component ID from string formats like 'P-101 (Influent Pump)' or dicts."""
        if isinstance(item, dict):
            return str(item.get("id") or item.get("component") or item.get("name") or "")
        match = re.match(r"^([a-zA-Z0-9_\-]+)", str(item).strip())
        return match.group(1) if match else str(item).strip()

    def sequence(
        self,
        route: list[tuple[float, float]],
        line_sequence: list[str | dict[str, Any]],
        component_sizes: dict[str, tuple[float, float]] | None = None,
    ) -> dict[str, InlinePlacement]:
        placements: dict[str, InlinePlacement] = {}
        if len(route) < 2 or not line_sequence:
            return placements

        sizes = component_sizes if component_sizes is not None else {}
        check_size_membership = component_sizes is not None

        # Extract only inline component IDs (excluding endpoints like Unit:Port)
        inline_ids: list[str] = []
        for entry in line_sequence:
            if isinstance(entry, dict):
                if "unit" in entry and "port" in entry:
                    continue
                cid = self._extract_id(entry)
                if ":" in cid:
                    continue
            else:
                cid = self._extract_id(entry)
                if ":" in entry:
                    continue

            if not cid:
                continue

            if not check_size_membership or cid in sizes:
                inline_ids.append(cid)

        if not inline_ids:
            return placements

        # Find the longest segment in the route
        longest_seg = None
        max_len = -1.0
        for i in range(len(route) - 1):
            p1, p2 = route[i], route[i + 1]
            seg_len = abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])
            if seg_len > max_len:
                max_len = seg_len
                longest_seg = (p1, p2)

        if longest_seg is None or max_len <= 0.0:
            return placements

        p1, p2 = longest_seg
        is_horizontal = abs(p1[1] - p2[1]) <= abs(p1[0] - p2[0])
        orientation: Literal["horizontal", "vertical"] = (
            "horizontal" if is_horizontal else "vertical"
        )

        n = len(inline_ids)
        step_fraction = 1.0 / (n + 1)

        for idx, cid in enumerate(inline_ids, start=1):
            t = idx * step_fraction
            cx = p1[0] + t * (p2[0] - p1[0])
            cy = p1[1] + t * (p2[1] - p1[1])

            size = sizes.get(cid, (20.0, 20.0))
            if orientation == "vertical":
                half_w = size[1] / 2.0 + self.knockout_padding
                half_h = size[0] / 2.0 + self.knockout_padding
            else:
                half_w = size[0] / 2.0 + self.knockout_padding
                half_h = size[1] / 2.0 + self.knockout_padding

            knockout = AABB(cx - half_w, cy - half_h, cx + half_w, cy + half_h)
            placements[cid] = InlinePlacement(
                component_id=cid,
                center=(cx, cy),
                orientation=orientation,
                knockout_box=knockout,
            )

        return placements
