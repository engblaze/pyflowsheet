from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


class FlowsheetGraph:
    """Represents the equipment connectivity network to extract a DAG, detect cycles
    (recycle streams), and compute topological stage ranks.
    """

    def __init__(self, unit_ids: list[str], streams: list[tuple[str, str, str]]):
        """Args:
        unit_ids: List of unique unit operation IDs.
        streams: List of tuples `(stream_id, from_unit_id, to_unit_id)`.
        """
        self.unit_ids = list(unit_ids)
        self.raw_streams = list(streams)

        # Adjacency
        self.adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.rev_adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for s_id, u_from, u_to in self.raw_streams:
            if u_from in self.unit_ids and u_to in self.unit_ids:
                self.adj[u_from].append((u_to, s_id))
                self.rev_adj[u_to].append((u_from, s_id))

        self.recycle_streams: set[str] = set()
        self.forward_edges: list[tuple[str, str, str]] = []
        self._detect_cycles_and_extract_dag()

    def _detect_cycles_and_extract_dag(self) -> None:
        """DFS traversal identifying back-edges (cycles/recycle loops) and extracting the DAG."""
        # 0 = unvisited, 1 = visiting (in recursion stack), 2 = visited
        color: dict[str, int] = {u: 0 for u in self.unit_ids}

        def dfs(node: str) -> None:
            color[node] = 1
            for nxt, s_id in self.adj.get(node, []):
                if color[nxt] == 1:
                    # Back edge detected -> Recycle stream!
                    self.recycle_streams.add(s_id)
                elif color[nxt] == 0:
                    dfs(nxt)
            color[node] = 2

        for unit in self.unit_ids:
            if color[unit] == 0:
                dfs(unit)

        for s_id, u_from, u_to in self.raw_streams:
            if (
                u_from in self.unit_ids
                and u_to in self.unit_ids
                and s_id not in self.recycle_streams
            ):
                self.forward_edges.append((s_id, u_from, u_to))

    def extract_dag(self) -> list[tuple[str, str, str]]:
        """Returns list of forward DAG stream edges `(stream_id, from_unit, to_unit)`."""
        return list(self.forward_edges)

    def compute_stages(self, manual_stage_hints: dict[str, int] | None = None) -> dict[str, int]:
        """Calculates topological column/bay stages (0, 1, 2, ...) using longest path ranking
        on the extracted forward DAG, respecting manual stage hints.
        """
        manual = manual_stage_hints or {}
        dag_adj: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {u: 0 for u in self.unit_ids}

        for _, u_from, u_to in self.forward_edges:
            if u_from in self.unit_ids and u_to in self.unit_ids:
                dag_adj[u_from].append(u_to)
                in_degree[u_to] += 1

        queue = deque([u for u in self.unit_ids if in_degree[u] == 0])
        stages: dict[str, int] = {u: manual.get(u, 0) for u in self.unit_ids}

        topological_order = []
        while queue:
            curr = queue.popleft()
            topological_order.append(curr)
            for nxt in dag_adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        # Compute longest paths
        for u in topological_order:
            curr_stage = stages[u]
            for nxt in dag_adj[u]:
                expected_nxt_stage = curr_stage + 1
                if nxt in manual:
                    stages[nxt] = max(stages[nxt], manual[nxt])
                else:
                    stages[nxt] = max(stages[nxt], expected_nxt_stage)

        return stages


class MacroLayoutSolver:
    """Computes 2D placement coordinates for equipment using topological stages,
    PlantUML-style layout hints (stage, relative_to, align, flow_direction),
    and manual position overrides.
    """

    def __init__(
        self,
        units: list[dict[str, Any]],
        streams: list[tuple[str, str, str]],
        origin: tuple[float, float] = (50.0, 100.0),
        bay_width: float = 160.0,
        bay_height: float = 120.0,
        flow_direction: str = "right",
    ):
        self.units = {u["id"]: u for u in units}
        self.streams = list(streams)
        self.origin = origin
        self.bay_width = bay_width
        self.bay_height = bay_height
        self.flow_direction = flow_direction
        self.recycle_corridors: dict[str, str] = {}

        unit_ids = list(self.units.keys())
        self.graph = FlowsheetGraph(unit_ids, self.streams)

    def get_recycle_corridors(self) -> dict[str, str]:
        """Returns mapping of recycle stream ID to corridor assignment ('top' or 'bottom')."""
        return dict(self.recycle_corridors)

    def solve(self) -> dict[str, tuple[float, float]]:
        """Executes layout solving and returns dictionary mapping unit ID to (x, y)."""
        positions: dict[str, tuple[float, float]] = {}

        # 1. Collect manual fixed positions
        fixed_units: set[str] = set()
        manual_stages: dict[str, int] = {}
        for uid, u in self.units.items():
            pos = u.get("position")
            if pos is not None and (
                pos[0] != 0.0 or pos[1] != 0.0 or u.get("fixed") or u.get("is_fixed")
            ):
                positions[uid] = (float(pos[0]), float(pos[1]))
                fixed_units.add(uid)
            hints = u.get("layout_hints")
            if hints:
                st = (
                    hints.get("stage") if isinstance(hints, dict) else getattr(hints, "stage", None)
                )
                if st is not None:
                    manual_stages[uid] = int(st)

        # 2. Compute topological stages
        stages = self.graph.compute_stages(manual_stages)

        # Group non-fixed units by stage
        bays: dict[int, list[str]] = defaultdict(list)
        for uid in self.units:
            if uid not in fixed_units:
                bays[stages[uid]].append(uid)

        # 3. Assign default bay coordinates
        for stage_idx, bay_units in sorted(bays.items()):
            if self.flow_direction == "down":
                y = self.origin[1] + stage_idx * self.bay_height
                for idx, uid in enumerate(bay_units):
                    x = self.origin[0] + idx * self.bay_width
                    positions[uid] = (x, y)
            elif self.flow_direction == "left":
                x = self.origin[0] - stage_idx * self.bay_width
                for idx, uid in enumerate(bay_units):
                    y = self.origin[1] + idx * self.bay_height
                    positions[uid] = (x, y)
            else:  # "right" (default)
                x = self.origin[0] + stage_idx * self.bay_width
                for idx, uid in enumerate(bay_units):
                    y = self.origin[1] + idx * self.bay_height
                    positions[uid] = (x, y)

        # 4. Resolve relative_to and align hints with convergence loop
        num_units = max(1, len(self.units))
        for _ in range(num_units):
            changed = False
            for uid, u in self.units.items():
                if uid in fixed_units:
                    continue
                hints = u.get("layout_hints")
                if not hints:
                    continue

                rel = (
                    hints.get("relative_to")
                    if isinstance(hints, dict)
                    else getattr(hints, "relative_to", None)
                )
                if rel:
                    target = (
                        rel.get("target") if isinstance(rel, dict) else getattr(rel, "target", None)
                    )
                    direction = (
                        rel.get("direction", "right")
                        if isinstance(rel, dict)
                        else getattr(rel, "direction", "right")
                    )
                    offset = float(
                        rel.get("offset", 60.0)
                        if isinstance(rel, dict)
                        else getattr(rel, "offset", 60.0)
                    )

                    if target in positions:
                        tx, ty = positions[target]
                        t_size = self.units[target].get("size", (40, 40))
                        u_size = u.get("size", (40, 40))
                        new_pos = positions[uid]

                        if direction == "right":
                            new_pos = (tx + t_size[0] + offset, ty)
                        elif direction == "left":
                            new_pos = (tx - u_size[0] - offset, ty)
                        elif direction == "below":
                            new_pos = (tx, ty + t_size[1] + offset)
                        elif direction == "above":
                            new_pos = (tx, ty - u_size[1] - offset)

                        if new_pos != positions[uid]:
                            positions[uid] = new_pos
                            changed = True

                align = (
                    hints.get("align") if isinstance(hints, dict) else getattr(hints, "align", None)
                )
                if align:
                    with_u = (
                        align.get("with") or align.get("with_unit")
                        if isinstance(align, dict)
                        else getattr(align, "with_unit", None)
                    )
                    axis = (
                        align.get("axis", "horizontal")
                        if isinstance(align, dict)
                        else getattr(align, "axis", "horizontal")
                    )
                    if with_u in positions:
                        wx, wy = positions[with_u]
                        curr_x, curr_y = positions[uid]
                        new_pos = (curr_x, wy) if axis == "horizontal" else (wx, curr_y)
                        if new_pos != positions[uid]:
                            positions[uid] = new_pos
                            changed = True

            if not changed:
                break

        # 5. Allocate recycle corridors for recycle streams
        self.recycle_corridors = {}
        for idx, s_id in enumerate(sorted(self.graph.recycle_streams)):
            self.recycle_corridors[s_id] = "top" if idx % 2 == 0 else "bottom"

        return positions
