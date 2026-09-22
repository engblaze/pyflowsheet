from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class CrossoverBridge:
    base_stream: str
    bridging_stream: str
    intersection: tuple[float, float]
    direction: Literal["horizontal", "vertical"]
    radius: float = 6.0
    style: Literal["arc", "gap"] = "arc"


class CrossoverDetector:
    """Detects 2D orthogonal segment intersections between non-intersecting streams
    and computes ISO jumper arcs or knockout gap breaks.
    """

    def __init__(
        self,
        bridge_radius: float = 6.0,
        default_style: Literal["arc", "gap"] = "arc",
    ):
        self.bridge_radius = bridge_radius
        self.default_style = default_style

    def find_crossings(
        self, streams: dict[str, list[tuple[float, float]]]
    ) -> list[CrossoverBridge]:
        bridges = []
        stream_items = list(streams.items())

        for i in range(len(stream_items)):
            s1_id, s1_pts = stream_items[i]
            for j in range(i + 1, len(stream_items)):
                s2_id, s2_pts = stream_items[j]

                # Check all segments of s1 against s2
                for s1_idx in range(len(s1_pts) - 1):
                    p1, p2 = s1_pts[s1_idx], s1_pts[s1_idx + 1]
                    s1_is_h = abs(p1[1] - p2[1]) < 1e-6 and abs(p1[0] - p2[0]) > 1e-6
                    s1_is_v = abs(p1[0] - p2[0]) < 1e-6 and abs(p1[1] - p2[1]) > 1e-6

                    for s2_idx in range(len(s2_pts) - 1):
                        q1, q2 = s2_pts[s2_idx], s2_pts[s2_idx + 1]
                        s2_is_h = abs(q1[1] - q2[1]) < 1e-6 and abs(q1[0] - q2[0]) > 1e-6
                        s2_is_v = abs(q1[0] - q2[0]) < 1e-6 and abs(q1[1] - q2[1]) > 1e-6

                        # Only orthogonal intersections (one horizontal, one vertical)
                        if s1_is_h and s2_is_v:
                            h_seg = (p1, p2)
                            v_seg = (q1, q2)
                            base_id = s1_id
                            bridge_id = s2_id
                        elif s1_is_v and s2_is_h:
                            h_seg = (q1, q2)
                            v_seg = (p1, p2)
                            base_id = s2_id
                            bridge_id = s1_id
                        else:
                            continue

                        hx_min = min(h_seg[0][0], h_seg[1][0])
                        hx_max = max(h_seg[0][0], h_seg[1][0])
                        vy_min = min(v_seg[0][1], v_seg[1][1])
                        vy_max = max(v_seg[0][1], v_seg[1][1])

                        h_y = h_seg[0][1]
                        v_x = v_seg[0][0]

                        # Strict interior crossing (exclude shared endpoints/terminals)
                        if (hx_min < v_x < hx_max) and (vy_min < h_y < vy_max):
                            bridges.append(
                                CrossoverBridge(
                                    base_stream=base_id,
                                    bridging_stream=bridge_id,
                                    intersection=(v_x, h_y),
                                    direction="vertical",
                                    radius=self.bridge_radius,
                                    style=self.default_style,
                                )
                            )
        return bridges

    def build_svg_path_commands(
        self,
        points: list[tuple[float, float]],
        bridges: list[CrossoverBridge],
    ) -> str:
        """Formats an SVG path `d` string incorporating jumper arcs or line gap breaks."""
        if len(points) < 2:
            return ""

        commands = [f"M {points[0][0]} {points[0][1]}"]

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            is_v = abs(p1[0] - p2[0]) < 1e-6
            is_h = abs(p1[1] - p2[1]) < 1e-6

            # Find bridges intersecting segment (p1, p2)
            seg_bridges = []
            for b in bridges:
                ix, iy = b.intersection
                if (
                    is_v
                    and getattr(b, "direction", "vertical") == "vertical"
                    and abs(p1[0] - ix) < 1e-6
                    and min(p1[1], p2[1]) < iy < max(p1[1], p2[1])
                ):
                    dist = abs(iy - p1[1])
                    seg_bridges.append((dist, b))
                elif (
                    is_h
                    and getattr(b, "direction", "horizontal") == "horizontal"
                    and abs(p1[1] - iy) < 1e-6
                    and min(p1[0], p2[0]) < ix < max(p1[0], p2[0])
                ):
                    dist = abs(ix - p1[0])
                    seg_bridges.append((dist, b))

            seg_bridges.sort(key=lambda item: item[0])

            for _, b in seg_bridges:
                ix, iy = b.intersection
                r = b.radius
                if is_v:  # Vertical segment
                    downward = p2[1] > p1[1]
                    start_y = iy - r if downward else iy + r
                    end_y = iy + r if downward else iy - r
                    commands.append(f"L {ix} {start_y}")
                    if b.style == "arc":
                        sweep = 1 if downward else 0
                        commands.append(f"A {r} {r} 0 0 {sweep} {ix} {end_y}")
                    else:  # gap break
                        commands.append(f"M {ix} {end_y}")
                else:  # Horizontal segment
                    rightward = p2[0] > p1[0]
                    start_x = ix - r if rightward else ix + r
                    end_x = ix + r if rightward else ix - r
                    commands.append(f"L {start_x} {iy}")
                    if b.style == "arc":
                        sweep = 1 if rightward else 0
                        commands.append(f"A {r} {r} 0 0 {sweep} {end_x} {iy}")
                    else:  # gap break
                        commands.append(f"M {end_x} {iy}")

            commands.append(f"L {p2[0]} {p2[1]}")

        return " ".join(commands)
