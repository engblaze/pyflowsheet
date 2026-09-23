from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .spatial import AABB

INLINE_TYPE_KEYWORDS = {
    "valve",
    "tee",
    "sample",
    "pump",
    "blower",
    "compressor",
}


def is_inline_type(u_type: str | None) -> bool:
    """Returns True if the given unit operation type name represents an inline component."""
    if not u_type:
        return False
    t = str(u_type).lower().strip()
    return any(k in t for k in INLINE_TYPE_KEYWORDS)


class FlowsheetGraph:
    """Represents the equipment connectivity network to extract a DAG, detect cycles
    (recycle streams), and compute topological stage ranks.
    """

    def __init__(
        self,
        unit_ids: list[str] | list[dict[str, Any]],
        streams: list[tuple[str, str, str]],
        unit_types: dict[str, str] | None = None,
        primary_units: set[str] | None = None,
    ):
        """Args:
        unit_ids: List of unique unit operation IDs or unit dicts.
        streams: List of tuples `(stream_id, from_unit_id, to_unit_id)`.
        unit_types: Optional mapping of unit ID to equipment type name.
        primary_units: Optional set of unit IDs that are primary process units.
        """
        if unit_ids and isinstance(unit_ids[0], dict):
            raw_units: list[dict[str, Any]] = unit_ids  # type: ignore[assignment]
            self.unit_ids = [u["id"] for u in raw_units]
            if not unit_types:
                self.unit_types = {u["id"]: str(u.get("type") or "") for u in raw_units}
            else:
                self.unit_types = dict(unit_types)
        else:
            self.unit_ids = list(unit_ids)  # type: ignore[arg-type]
            self.unit_types = dict(unit_types) if unit_types else {}

        if primary_units is not None:
            self.primary_units = set(primary_units)
        elif self.unit_types:
            self.primary_units = {
                uid for uid in self.unit_ids if not is_inline_type(self.unit_types.get(uid))
            }
        else:
            self.primary_units = set(self.unit_ids)

        self.raw_streams = list(streams)

        # Adjacency
        self.adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.rev_adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for item in self.raw_streams:
            s_id, u_from, u_to = item[0], item[1], item[2]
            if u_from in self.unit_ids and u_to in self.unit_ids:
                self.adj[u_from].append((u_to, s_id))
                self.rev_adj[u_to].append((u_from, s_id))

        self.recycle_streams: set[str] = set()
        self.recycle_units: set[str] = set()
        self.recycle_chains: list[dict[str, Any]] = []
        self.forward_edges: list[tuple[str, str, str]] = []
        self._detect_cycles_and_extract_dag()

    def _detect_cycles_and_extract_dag(self) -> None:
        """DFS traversal identifying back-edges (cycles/recycle loops), extracting full
        feedback paths, tagging recycle units, and extracting the DAG.
        """
        # 0 = unvisited, 1 = visiting (in recursion stack), 2 = visited
        color: dict[str, int] = {u: 0 for u in self.unit_ids}
        back_edges: list[tuple[str, str, str]] = []

        def dfs(node: str) -> None:
            color[node] = 1
            for nxt, s_id in self.adj.get(node, []):
                if color[nxt] == 1:
                    # Back edge detected -> Recycle stream!
                    back_edges.append((s_id, node, nxt))
                elif color[nxt] == 0:
                    dfs(nxt)
            color[node] = 2

        # Start DFS from source nodes (in_degree == 0) first for deterministic forward traversal
        in_deg: dict[str, int] = {u: 0 for u in self.unit_ids}
        for item in self.raw_streams:
            u_from, u_to = item[1], item[2]
            if u_from in in_deg and u_to in in_deg:
                in_deg[u_to] += 1

        ordered_units = sorted(self.unit_ids, key=lambda u: in_deg.get(u, 0))
        for unit in ordered_units:
            if color[unit] == 0:
                dfs(unit)

        self.recycle_units = set()
        self.recycle_chains = []

        # Trace full recycle paths from each back-edge
        for s_id, u_from, u_to in back_edges:
            self.recycle_streams.add(s_id)
            target = u_to
            chain: list[str] = []
            chain_streams = [s_id]

            if u_from not in self.primary_units:
                self.recycle_units.add(u_from)
                chain.append(u_from)
                curr = u_from
                visited = {u_from, target}
                source_primary = None

                while True:
                    if len(chain) > len(self.unit_ids):
                        break
                    preds = [p for p in self.rev_adj.get(curr, []) if p[0] not in visited]
                    if not preds:
                        break

                    pred_unit, in_s_id = preds[0]
                    self.recycle_streams.add(in_s_id)
                    chain_streams.append(in_s_id)

                    if pred_unit in self.primary_units:
                        source_primary = pred_unit
                        break
                    else:
                        self.recycle_units.add(pred_unit)
                        chain.append(pred_unit)
                        visited.add(pred_unit)
                        curr = pred_unit

                self.recycle_chains.append(
                    {
                        "source": source_primary,
                        "target": target,
                        "units": list(reversed(chain)),
                        "streams": chain_streams,
                    }
                )
            else:
                self.recycle_chains.append(
                    {
                        "source": u_from,
                        "target": target,
                        "units": [],
                        "streams": chain_streams,
                    }
                )

        for item in self.raw_streams:
            s_id, u_from, u_to = item[0], item[1], item[2]
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
    inline train compaction, and reverse-corridor recycle placement.
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
        self.flipped_units: set[str] = set()
        self.stream_ports: dict[str, tuple[str | None, str | None]] = {}
        for s in self.streams:
            if isinstance(s, (tuple, list)) and len(s) >= 5:
                self.stream_ports[str(s[0])] = (
                    str(s[3]) if s[3] is not None else None,
                    str(s[4]) if s[4] is not None else None,
                )
            elif isinstance(s, dict):
                self.stream_ports[str(s.get("id", ""))] = (
                    s.get("from_port"),
                    s.get("to_port"),
                )

        unit_ids = list(self.units.keys())
        unit_types = {uid: self._get_unit_type(u) for uid, u in self.units.items()}
        primary_units = {uid for uid in unit_ids if not self._is_inline_unit(self.units[uid])}
        self.graph = FlowsheetGraph(
            unit_ids,
            self.streams,
            unit_types=unit_types,
            primary_units=primary_units,
        )

    @staticmethod
    def _get_unit_type(u_data: dict[str, Any]) -> str:
        u_type = u_data.get("type")
        if u_type:
            return str(u_type)
        u_obj = u_data.get("unit")
        if u_obj:
            return str(getattr(u_obj, "type", u_obj.__class__.__name__))
        return ""

    @classmethod
    def _is_inline_unit(cls, u_data: dict[str, Any]) -> bool:
        t = cls._get_unit_type(u_data).lower().strip()
        if not t:
            return False
        return any(k in t for k in INLINE_TYPE_KEYWORDS)

    def get_recycle_corridors(self) -> dict[str, str]:
        """Returns mapping of recycle stream ID to corridor assignment ('top' or 'bottom')."""
        return dict(self.recycle_corridors)

    def _get_ports_for_unit(self, uid: str) -> dict[str, dict[str, Any]]:
        u = self.units.get(uid, {})
        raw_ports = u.get("ports")
        if not raw_ports:
            u_obj = u.get("unit")
            if u_obj and hasattr(u_obj, "ports"):
                raw_ports = u_obj.ports

        if not raw_ports:
            return {}

        result: dict[str, dict[str, Any]] = {}
        if isinstance(raw_ports, dict):
            for pname, p in raw_ports.items():
                if isinstance(p, (tuple, list)):
                    rx, ry = float(p[0]), float(p[1])
                    if rx >= 0.9:
                        normal = (1.0, 0.0)
                        intent = "out"
                    elif rx <= 0.1:
                        normal = (-1.0, 0.0)
                        intent = "in"
                    elif ry <= 0.1:
                        normal = (0.0, -1.0)
                        intent = "in"
                    elif ry >= 0.9:
                        normal = (0.0, 1.0)
                        intent = "out"
                    else:
                        intent = "out" if "out" in str(pname).lower() else "in"
                        normal = (1.0, 0.0) if intent == "out" else (-1.0, 0.0)
                    result[str(pname)] = {
                        "name": str(pname),
                        "rel_pos": (rx, ry),
                        "normal": normal,
                        "intent": intent,
                    }
                elif isinstance(p, dict):
                    pos = (
                        p.get("rel_pos")
                        or p.get("relativePosition")
                        or (p.get("x", 0.0), p.get("y", 0.0))
                    )
                    rx, ry = float(pos[0]), float(pos[1])
                    norm = p.get("normal")
                    intent = p.get("intent")
                    if norm is None:
                        if rx >= 0.9:
                            norm = (1.0, 0.0)
                        elif rx <= 0.1:
                            norm = (-1.0, 0.0)
                        elif ry <= 0.1:
                            norm = (0.0, -1.0)
                        elif ry >= 0.9:
                            norm = (0.0, 1.0)
                        else:
                            norm = (
                                (1.0, 0.0)
                                if intent == "out" or "out" in str(pname).lower()
                                else (-1.0, 0.0)
                            )
                    if intent is None:
                        intent = (
                            "out"
                            if norm[0] > 0 or norm[1] > 0 or "out" in str(pname).lower()
                            else "in"
                        )
                    result[str(pname)] = {
                        "name": str(pname),
                        "rel_pos": (rx, ry),
                        "normal": (float(norm[0]), float(norm[1])),
                        "intent": str(intent),
                    }
                else:
                    pos = getattr(p, "relativePosition", (0.0, 0.0))
                    rx, ry = float(pos[0]), float(pos[1])
                    norm = getattr(p, "normal", None)
                    intent = getattr(p, "intent", None)
                    if norm is None:
                        norm = (1.0, 0.0) if rx >= 0.9 else (-1.0, 0.0)
                    if intent is None:
                        intent = "out" if norm[0] > 0 else "in"
                    result[str(pname)] = {
                        "name": str(pname),
                        "rel_pos": (rx, ry),
                        "normal": (float(norm[0]), float(norm[1])),
                        "intent": str(intent),
                    }
        return result

    def _find_out_port(self, uid: str, port_name: str | None = None) -> dict[str, Any] | None:
        ports = self._get_ports_for_unit(uid)
        if not ports:
            return None
        if port_name and port_name in ports:
            return ports[port_name]

        if self.flow_direction == "down":
            candidates = [
                p
                for p in ports.values()
                if (abs(p["normal"][0]) < 0.01 and abs(p["normal"][1] - 1.0) < 0.01)
                or p["rel_pos"][1] >= 0.9
            ]
            if candidates:
                for c in candidates:
                    if c["name"].lower() in {"out", "bottom", "bottoms"}:
                        return c
                return candidates[0]
        elif self.flow_direction == "left":
            candidates = [
                p
                for p in ports.values()
                if (abs(p["normal"][0] - (-1.0)) < 0.01 and abs(p["normal"][1]) < 0.01)
                or p["rel_pos"][0] <= 0.1
            ]
            if candidates:
                for c in candidates:
                    if c["name"].lower() == "out":
                        return c
                return candidates[0]
        else:  # "right"
            candidates = [
                p
                for p in ports.values()
                if (abs(p["normal"][0] - 1.0) < 0.01 and abs(p["normal"][1]) < 0.01)
                or p["rel_pos"][0] >= 0.9
                or p["intent"] == "out"
            ]
            if candidates:
                for c in candidates:
                    if c["name"].lower() == "out":
                        return c
                for c in candidates:
                    if abs(c["normal"][0] - 1.0) < 0.01 and abs(c["normal"][1]) < 0.01:
                        return c
                return candidates[0]
        return None

    def _find_in_port(self, uid: str, port_name: str | None = None) -> dict[str, Any] | None:
        ports = self._get_ports_for_unit(uid)
        if not ports:
            return None
        if port_name and port_name in ports:
            return ports[port_name]

        if self.flow_direction == "down":
            candidates = [
                p
                for p in ports.values()
                if (abs(p["normal"][0]) < 0.01 and abs(p["normal"][1] - (-1.0)) < 0.01)
                or p["rel_pos"][1] <= 0.1
            ]
            if candidates:
                for c in candidates:
                    if c["name"].lower() in {"in", "top", "feed"}:
                        return c
                return candidates[0]
        elif self.flow_direction == "left":
            candidates = [
                p
                for p in ports.values()
                if (abs(p["normal"][0] - 1.0) < 0.01 and abs(p["normal"][1]) < 0.01)
                or p["rel_pos"][0] >= 0.9
            ]
            if candidates:
                for c in candidates:
                    if c["name"].lower() == "in":
                        return c
                return candidates[0]
        else:  # "right"
            candidates = [
                p
                for p in ports.values()
                if (abs(p["normal"][0] - (-1.0)) < 0.01 and abs(p["normal"][1]) < 0.01)
                or p["rel_pos"][0] <= 0.1
                or p["intent"] == "in"
            ]
            if candidates:
                for c in candidates:
                    if c["name"].lower() == "in":
                        return c
                for c in candidates:
                    if abs(c["normal"][0] - (-1.0)) < 0.01 and abs(c["normal"][1]) < 0.01:
                        return c
                return candidates[0]
        return None

    def _align_port_elevations(
        self,
        positions: dict[str, tuple[float, float]],
        fixed_units: set[str],
    ) -> None:
        """Adjusts the positions of downstream components connected via opposing
        horizontal (or vertical) ports so that connection elevations match cleanly.
        """
        vertically_constrained: set[str] = set(fixed_units)
        for uid, u in self.units.items():
            hints = u.get("layout_hints")
            if hints:
                rel = (
                    hints.get("relative_to")
                    if isinstance(hints, dict)
                    else getattr(hints, "relative_to", None)
                )
                if rel:
                    direction = (
                        rel.get("direction")
                        if isinstance(rel, dict)
                        else getattr(rel, "direction", None)
                    )
                    if self.flow_direction == "down":
                        if direction in {"left", "right"}:
                            vertically_constrained.add(uid)
                    else:
                        if direction in {"above", "below"}:
                            vertically_constrained.add(uid)

        forward_incoming: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        for item in self.streams:
            s_id = str(item.get("id", "")) if isinstance(item, dict) else str(item[0])
            u_from = str(item.get("from", "")) if isinstance(item, dict) else str(item[1])
            u_to = str(item.get("to", "")) if isinstance(item, dict) else str(item[2])
            if (
                s_id not in self.graph.recycle_streams
                and u_from in self.units
                and u_to in self.units
            ):
                forward_incoming[u_to].append((s_id, u_from, u_to))

        primary_incoming_stream: dict[str, str] = {}
        for uid, inc_streams in forward_incoming.items():
            if len(inc_streams) == 1:
                primary_incoming_stream[uid] = inc_streams[0][0]
            elif len(inc_streams) > 1:

                def _score_stream(s_tuple: tuple[str, str, str]) -> int:
                    s_id, u_from, _ = s_tuple
                    score = 0
                    if u_from in self.graph.primary_units:
                        score += 100
                    _, to_p = self.stream_ports.get(s_id, (None, None))
                    in_port = self._find_in_port(uid, to_p)
                    if in_port:
                        pname = in_port["name"].lower()
                        if pname in {"in", "feed", "intube", "tin"}:
                            score += 50
                        elif pname == "in1":
                            score += 40
                        score += int((1.0 - abs(in_port["rel_pos"][1] - 0.5)) * 10)
                    return score

                best_stream = max(inc_streams, key=_score_stream)
                primary_incoming_stream[uid] = best_stream[0]

        dag_adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        in_deg: dict[str, int] = {u: 0 for u in self.units}
        for item in self.graph.forward_edges:
            s_id, u_from, u_to = str(item[0]), str(item[1]), str(item[2])
            if u_from in self.units and u_to in self.units:
                dag_adj[u_from].append((u_to, s_id))
                in_deg[u_to] += 1

        queue = deque([u for u in self.units if in_deg[u] == 0])
        topo_order: list[str] = []
        while queue:
            curr = queue.popleft()
            topo_order.append(curr)
            for nxt, _ in dag_adj[curr]:
                in_deg[nxt] -= 1
                if in_deg[nxt] == 0:
                    queue.append(nxt)

        for u in self.units:
            if u not in topo_order:
                topo_order.append(u)

        for u in topo_order:
            if u not in positions:
                continue
            for v, s_id in dag_adj.get(u, []):
                if v not in positions:
                    continue
                if v in vertically_constrained:
                    continue
                if primary_incoming_stream.get(v) != s_id:
                    continue

                from_p, to_p = self.stream_ports.get(s_id, (None, None))
                out_port = self._find_out_port(u, from_p)
                in_port = self._find_in_port(v, to_p)
                if not out_port or not in_port:
                    continue

                u_sz = self.units[u].get("size")
                v_sz = self.units[v].get("size")
                u_w = float(u_sz[0]) if u_sz is not None else 40.0
                u_h = float(u_sz[1]) if u_sz is not None else 40.0
                v_w = float(v_sz[0]) if v_sz is not None else 40.0
                v_h = float(v_sz[1]) if v_sz is not None else 40.0

                if self.flow_direction == "down":
                    if positions[v][1] <= positions[u][1]:
                        continue
                    if abs(positions[u][0] - positions[v][0]) >= self.bay_width * 0.75:
                        continue
                    if not (
                        abs(out_port["normal"][0]) < 0.01
                        and abs(out_port["normal"][1] - 1.0) < 0.01
                        and abs(in_port["normal"][0]) < 0.01
                        and abs(in_port["normal"][1] - (-1.0)) < 0.01
                    ):
                        continue
                    port_x_u = positions[u][0] + out_port["rel_pos"][0] * u_w
                    new_x_v = port_x_u - in_port["rel_pos"][0] * v_w
                    test_box = AABB(new_x_v, positions[v][1], new_x_v + v_w, positions[v][1] + v_h)
                    if not any(
                        other_u != v
                        and other_u not in self.graph.recycle_units
                        and test_box.intersects(
                            AABB(
                                other_pos[0],
                                other_pos[1],
                                other_pos[0] + float(self.units[other_u].get("size", (40, 40))[0]),
                                other_pos[1] + float(self.units[other_u].get("size", (40, 40))[1]),
                            )
                        )
                        for other_u, other_pos in positions.items()
                    ):
                        positions[v] = (new_x_v, positions[v][1])
                        vertically_constrained.add(v)
                elif self.flow_direction == "left":
                    if positions[v][0] >= positions[u][0]:
                        continue
                    if abs(positions[u][1] - positions[v][1]) >= self.bay_height * 0.75:
                        continue
                    if not (
                        abs(out_port["normal"][0] - (-1.0)) < 0.01
                        and abs(out_port["normal"][1]) < 0.01
                        and abs(in_port["normal"][0] - 1.0) < 0.01
                        and abs(in_port["normal"][1]) < 0.01
                    ):
                        continue
                    port_y_u = positions[u][1] + out_port["rel_pos"][1] * u_h
                    new_y_v = port_y_u - in_port["rel_pos"][1] * v_h
                    test_box = AABB(positions[v][0], new_y_v, positions[v][0] + v_w, new_y_v + v_h)
                    if not any(
                        other_u != v
                        and other_u not in self.graph.recycle_units
                        and test_box.intersects(
                            AABB(
                                other_pos[0],
                                other_pos[1],
                                other_pos[0] + float(self.units[other_u].get("size", (40, 40))[0]),
                                other_pos[1] + float(self.units[other_u].get("size", (40, 40))[1]),
                            )
                        )
                        for other_u, other_pos in positions.items()
                    ):
                        positions[v] = (positions[v][0], new_y_v)
                        vertically_constrained.add(v)
                else:  # "right"
                    if positions[v][0] <= positions[u][0]:
                        continue
                    if abs(positions[u][1] - positions[v][1]) >= self.bay_height * 0.75:
                        continue
                    if not (
                        abs(out_port["normal"][0] - 1.0) < 0.01
                        and abs(out_port["normal"][1]) < 0.01
                        and abs(in_port["normal"][0] - (-1.0)) < 0.01
                        and abs(in_port["normal"][1]) < 0.01
                    ):
                        continue
                    port_y_u = positions[u][1] + out_port["rel_pos"][1] * u_h
                    new_y_v = port_y_u - in_port["rel_pos"][1] * v_h
                    test_box = AABB(positions[v][0], new_y_v, positions[v][0] + v_w, new_y_v + v_h)
                    if not any(
                        other_u != v
                        and other_u not in self.graph.recycle_units
                        and test_box.intersects(
                            AABB(
                                other_pos[0],
                                other_pos[1],
                                other_pos[0] + float(self.units[other_u].get("size", (40, 40))[0]),
                                other_pos[1] + float(self.units[other_u].get("size", (40, 40))[1]),
                            )
                        )
                        for other_u, other_pos in positions.items()
                    ):
                        positions[v] = (positions[v][0], new_y_v)
                        vertically_constrained.add(v)

    def solve(self) -> dict[str, tuple[float, float]]:
        """Executes layout solving and returns dictionary mapping unit ID to (x, y)."""
        positions: dict[str, tuple[float, float]] = {}

        # 1. Collect manual fixed positions and manual stages
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

        # 2. Identify primary, inline, and recycle units
        primary_units = set(self.graph.primary_units)
        recycle_units = set(self.graph.recycle_units)

        # 3. Trace forward primary graph and inline chains between primary units
        forward_adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for s_id, u_from, u_to in self.graph.forward_edges:
            forward_adj[u_from].append((u_to, s_id))

        primary_adj: dict[str, list[str]] = defaultdict(list)
        primary_in_deg: dict[str, int] = {u: 0 for u in primary_units}
        # inline_chains: list of (from_primary, to_primary_or_empty, chain_units)
        inline_chains: list[tuple[str, str, list[str]]] = []

        for p_u in primary_units:
            for nxt, _ in forward_adj.get(p_u, []):
                if nxt in recycle_units:
                    continue
                if nxt in primary_units:
                    primary_adj[p_u].append(nxt)
                    primary_in_deg[nxt] += 1
                    inline_chains.append((p_u, nxt, []))
                else:
                    chain = [nxt]
                    curr = nxt
                    visited_inline = {nxt}
                    found_primary = None
                    while True:
                        successors = [
                            s[0]
                            for s in forward_adj.get(curr, [])
                            if s[0] not in visited_inline and s[0] not in recycle_units
                        ]
                        if not successors:
                            break
                        succ = successors[0]
                        if succ in primary_units:
                            found_primary = succ
                            break
                        else:
                            chain.append(succ)
                            visited_inline.add(succ)
                            curr = succ
                    if found_primary:
                        primary_adj[p_u].append(found_primary)
                        primary_in_deg[found_primary] += 1
                        inline_chains.append((p_u, found_primary, chain))
                    else:
                        inline_chains.append((p_u, "", chain))

        # 4. Compute primary topological stages
        q = deque([u for u in primary_units if primary_in_deg.get(u, 0) == 0])
        topo_order = []
        in_deg_copy = dict(primary_in_deg)
        while q:
            curr = q.popleft()
            topo_order.append(curr)
            for nxt in primary_adj.get(curr, []):
                in_deg_copy[nxt] -= 1
                if in_deg_copy[nxt] == 0:
                    q.append(nxt)

        for u in primary_units:
            if u not in topo_order:
                topo_order.append(u)

        primary_stages: dict[str, int] = {u: manual_stages.get(u, 0) for u in primary_units}
        for u in topo_order:
            curr_stage = primary_stages[u]
            for nxt in primary_adj.get(u, []):
                exp_nxt = curr_stage + 1
                if nxt in manual_stages:
                    primary_stages[nxt] = max(primary_stages[nxt], manual_stages[nxt])
                else:
                    primary_stages[nxt] = max(primary_stages[nxt], exp_nxt)

        # 5. Compute stage coordinates and assign positions to primary units
        max_stage = max(primary_stages.values()) if primary_stages else 0
        stage_coords: dict[int, float] = {
            0: self.origin[1] if self.flow_direction == "down" else self.origin[0]
        }

        for s in range(max_stage + 1):
            curr_coord = stage_coords.get(
                s,
                (self.origin[1] + s * self.bay_height)
                if self.flow_direction == "down"
                else (self.origin[0] + s * self.bay_width),
            )
            max_step_span = self.bay_height if self.flow_direction == "down" else self.bay_width
            for p_from, p_to, chain in inline_chains:
                if p_to and primary_stages.get(p_from) == s and primary_stages.get(p_to) == s + 1:
                    if chain:
                        k = len(chain)
                        sz_from = self.units[p_from].get("size")
                        if self.flow_direction == "down":
                            h_from = float(sz_from[1]) if sz_from is not None else 40.0
                            h_inline = sum(
                                float(self.units[u].get("size")[1])
                                if self.units[u].get("size") is not None
                                else 40.0
                                for u in chain
                            )
                            span_needed = h_from + 40.0 + (k + 1) * 35.0 + h_inline
                        else:
                            w_from = float(sz_from[0]) if sz_from is not None else 40.0
                            w_inline = sum(
                                float(self.units[u].get("size")[0])
                                if self.units[u].get("size") is not None
                                else 40.0
                                for u in chain
                            )
                            span_needed = w_from + 40.0 + (k + 1) * 35.0 + w_inline
                        max_step_span = max(max_step_span, span_needed)
            stage_coords[s + 1] = max(stage_coords.get(s + 1, 0.0), curr_coord + max_step_span)

        primary_bays: dict[int, list[str]] = defaultdict(list)
        for uid in self.units:
            if uid in primary_units and uid not in fixed_units:
                primary_bays[primary_stages[uid]].append(uid)

        for stage_idx, bay_units in sorted(primary_bays.items()):
            if self.flow_direction == "down":
                y = stage_coords[stage_idx]
                for idx, uid in enumerate(bay_units):
                    x = self.origin[0] + idx * self.bay_width
                    positions[uid] = (x, y)
            elif self.flow_direction == "left":
                x = self.origin[0] - (stage_coords[stage_idx] - self.origin[0])
                for idx, uid in enumerate(bay_units):
                    y = self.origin[1] + idx * self.bay_height
                    positions[uid] = (x, y)
            else:  # "right"
                x = stage_coords[stage_idx]
                for idx, uid in enumerate(bay_units):
                    y = self.origin[1] + idx * self.bay_height
                    positions[uid] = (x, y)

        # 6. Position inline units along spans between primary units
        for p_from, p_to, chain in inline_chains:
            if not chain:
                continue
            if p_from not in positions:
                continue
            pos_from = positions[p_from]
            sz_from = self.units[p_from].get("size")
            w_from = float(sz_from[0]) if sz_from is not None else 40.0
            h_from = float(sz_from[1]) if sz_from is not None else 40.0

            if p_to and p_to in positions:
                pos_to = positions[p_to]
                if self.flow_direction == "down":
                    start_y = pos_from[1] + h_from + 20.0
                    end_y = pos_to[1] - 20.0
                    avail = max(0.0, end_y - start_y)
                    total_h = sum(
                        float(self.units[u].get("size")[1])
                        if self.units[u].get("size") is not None
                        else 40.0
                        for u in chain
                    )
                    k = len(chain)
                    gap = (avail - total_h) / (k + 1) if avail > total_h else 35.0
                    curr_y = start_y + gap
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_h = float(u_sz[1]) if u_sz is not None else 40.0
                            positions[u] = (pos_from[0], curr_y)
                            curr_y += u_h + gap
                elif self.flow_direction == "left":
                    start_x = pos_from[0] - 20.0
                    sz_to = self.units[p_to].get("size")
                    w_to = float(sz_to[0]) if sz_to is not None else 40.0
                    end_x = pos_to[0] + w_to + 20.0
                    avail = max(0.0, start_x - end_x)
                    total_w = sum(
                        float(self.units[u].get("size")[0])
                        if self.units[u].get("size") is not None
                        else 40.0
                        for u in chain
                    )
                    k = len(chain)
                    gap = (avail - total_w) / (k + 1) if avail > total_w else 35.0
                    curr_x = start_x - gap
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_w = float(u_sz[0]) if u_sz is not None else 40.0
                            positions[u] = (curr_x - u_w, pos_from[1])
                            curr_x -= u_w + gap
                else:  # "right"
                    start_x = pos_from[0] + w_from + 20.0
                    end_x = pos_to[0] - 20.0
                    avail = max(0.0, end_x - start_x)
                    total_w = sum(
                        float(self.units[u].get("size")[0])
                        if self.units[u].get("size") is not None
                        else 40.0
                        for u in chain
                    )
                    k = len(chain)
                    gap = (avail - total_w) / (k + 1) if avail > total_w else 35.0
                    curr_x = start_x + gap
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_w = float(u_sz[0]) if u_sz is not None else 40.0
                            positions[u] = (curr_x, pos_from[1])
                            curr_x += u_w + gap
            else:
                # Terminal inline chain without downstream primary unit
                first_u = chain[0]
                from_port_name = None
                for s in self.streams:
                    u_f = str(s[1]) if isinstance(s, (tuple, list)) else str(s.get("from", ""))
                    u_t = str(s[2]) if isinstance(s, (tuple, list)) else str(s.get("to", ""))
                    if u_f == p_from and u_t == first_u:
                        from_port_name = (
                            str(s[3])
                            if isinstance(s, (tuple, list)) and len(s) > 3
                            else (s.get("from_port") if isinstance(s, dict) else None)
                        )
                        break

                p_ports = self._get_ports_for_unit(p_from)
                port_meta = p_ports.get(str(from_port_name)) if from_port_name else None
                port_rel = port_meta.get("rel_pos", (1.0, 0.5)) if port_meta else (1.0, 0.5)
                port_norm = port_meta.get("normal", (1.0, 0.0)) if port_meta else (1.0, 0.0)

                is_inlet_branch = port_norm[0] < -0.5 or (
                    abs(port_norm[0]) < 0.1 and port_rel[0] <= 0.2
                )
                is_top_branch = port_norm[1] < -0.5 or (
                    abs(port_norm[1]) < 0.1 and port_rel[1] <= 0.2
                )
                is_bottom_branch = port_norm[1] > 0.5 or (
                    abs(port_norm[1]) < 0.1 and port_rel[1] >= 0.8
                )

                if is_inlet_branch:
                    curr_x = pos_from[0] - 35.0
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_w = float(u_sz[0]) if u_sz is not None else 40.0
                            u_h = float(u_sz[1]) if u_sz is not None else 40.0
                            positions[u] = (curr_x - u_w, pos_from[1] - u_h - 20.0)
                            curr_x -= u_w + 35.0
                elif is_top_branch:
                    curr_y = pos_from[1] - 35.0
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_h = float(u_sz[1]) if u_sz is not None else 40.0
                            positions[u] = (pos_from[0] + port_rel[0] * w_from, curr_y - u_h)
                            curr_y -= u_h + 35.0
                elif is_bottom_branch:
                    curr_y = pos_from[1] + h_from + 35.0
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_h = float(u_sz[1]) if u_sz is not None else 40.0
                            positions[u] = (pos_from[0] + port_rel[0] * w_from, curr_y)
                            curr_y += u_h + 35.0
                elif self.flow_direction == "down":
                    curr_y = pos_from[1] + h_from + 35.0
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_h = float(u_sz[1]) if u_sz is not None else 40.0
                            positions[u] = (pos_from[0], curr_y)
                            curr_y += u_h + 35.0
                elif self.flow_direction == "left":
                    curr_x = pos_from[0] - 35.0
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_w = float(u_sz[0]) if u_sz is not None else 40.0
                            positions[u] = (curr_x - u_w, pos_from[1])
                            curr_x -= u_w + 35.0
                else:  # "right"
                    curr_x = pos_from[0] + w_from + 35.0
                    for u in chain:
                        if u not in fixed_units:
                            u_sz = self.units[u].get("size")
                            u_w = float(u_sz[0]) if u_sz is not None else 40.0
                            positions[u] = (curr_x, pos_from[1])
                            curr_x += u_w + 35.0

        # 7. Allocate corridors and position recycle units
        self.recycle_corridors = {}
        for c_idx, chain_info in enumerate(self.graph.recycle_chains):
            target = chain_info.get("target")
            target_port_name = None
            for s in self.streams:
                s_id = str(s[0]) if isinstance(s, (tuple, list)) else str(s.get("id", ""))
                u_to = str(s[2]) if isinstance(s, (tuple, list)) else str(s.get("to", ""))
                if s_id in chain_info.get("streams", []) and u_to == target:
                    target_port_name = (
                        str(s[4])
                        if isinstance(s, (tuple, list)) and len(s) > 4
                        else (s.get("to_port") if isinstance(s, dict) else None)
                    )
                    break

            tgt_ports = self._get_ports_for_unit(target) if target else {}
            port_data = tgt_ports.get(str(target_port_name)) if target_port_name else None

            chain_corridor = None
            if port_data:
                norm_y = port_data.get("normal", (0, 0))[1]
                rel_y = port_data.get("rel_pos", (0.5, 0.5))[1]
                if norm_y < -0.1 or rel_y < 0.4:
                    chain_corridor = "top"
                elif norm_y > 0.1 or rel_y > 0.6:
                    chain_corridor = "bottom"

            if not chain_corridor:
                source = chain_info.get("source")
                source_port_name = None
                for s in self.streams:
                    s_id = str(s[0]) if isinstance(s, (tuple, list)) else str(s.get("id", ""))
                    u_from = str(s[1]) if isinstance(s, (tuple, list)) else str(s.get("from", ""))
                    if s_id in chain_info.get("streams", []) and u_from == source:
                        source_port_name = (
                            str(s[3])
                            if isinstance(s, (tuple, list)) and len(s) > 3
                            else (s.get("from_port") if isinstance(s, dict) else None)
                        )
                        break
                src_ports = self._get_ports_for_unit(source) if source else {}
                src_port_data = src_ports.get(str(source_port_name)) if source_port_name else None
                if src_port_data:
                    norm_y = src_port_data.get("normal", (0, 0))[1]
                    rel_y = src_port_data.get("rel_pos", (0.5, 0.5))[1]
                    if norm_y < -0.1 or rel_y < 0.4:
                        chain_corridor = "top"
                    elif norm_y > 0.1 or rel_y > 0.6:
                        chain_corridor = "bottom"

            if not chain_corridor:
                chain_corridor = "bottom" if c_idx % 2 == 0 else "top"

            for s_id in chain_info.get("streams", []):
                self.recycle_corridors[s_id] = chain_corridor

            chain_units = [u for u in chain_info.get("units", []) if u not in fixed_units]
            if not chain_units:
                continue

            source = chain_info.get("source")
            target = chain_info.get("target")

            if source and source in positions:
                src_pos = positions[source]
            else:
                max_x = max(
                    (p[0] for uid, p in positions.items() if uid not in recycle_units),
                    default=self.origin[0],
                )
                src_pos = (max_x, self.origin[1])

            if target and target in positions:
                tgt_pos = positions[target]
            else:
                min_x = min(
                    (p[0] for uid, p in positions.items() if uid not in recycle_units),
                    default=self.origin[0],
                )
                tgt_pos = (min_x, self.origin[1])

            # If flow runs right-to-left along this corridor, mark units for horizontal flip
            if tgt_pos[0] < src_pos[0]:
                for u in chain_units:
                    self.flipped_units.add(u)

            if self.flow_direction == "down":
                corridor_offset = 60.0
                max_process_x = max(
                    (
                        p[0]
                        + (
                            float(self.units[uid].get("size")[0])
                            if self.units[uid].get("size") is not None
                            else 40.0
                        )
                        for uid, p in positions.items()
                        if uid not in recycle_units
                    ),
                    default=self.origin[0],
                )
                corr_x = max_process_x + corridor_offset
                k = len(chain_units)
                for idx, u in enumerate(chain_units):
                    frac = (idx + 1) / (k + 1)
                    y = src_pos[1] + frac * (tgt_pos[1] - src_pos[1])
                    positions[u] = (corr_x, y)
            else:
                corridor_offset = 60.0
                if chain_corridor == "bottom":
                    max_process_y = max(
                        (
                            p[1]
                            + (
                                float(self.units[uid].get("size")[1])
                                if self.units[uid].get("size") is not None
                                else 40.0
                            )
                            for uid, p in positions.items()
                            if uid not in recycle_units
                        ),
                        default=self.origin[1],
                    )
                    corr_y = max_process_y + corridor_offset
                else:
                    min_process_y = min(
                        (p[1] for uid, p in positions.items() if uid not in recycle_units),
                        default=self.origin[1],
                    )
                    corr_y = min_process_y - corridor_offset - 40.0

                k = len(chain_units)
                for idx, u in enumerate(chain_units):
                    frac = (idx + 1) / (k + 1)
                    x = src_pos[0] + frac * (tgt_pos[0] - src_pos[0])
                    positions[u] = (x, corr_y)

        # Allocate corridors for any unassigned recycle streams
        for idx, s_id in enumerate(sorted(self.graph.recycle_streams)):
            if s_id not in self.recycle_corridors:
                self.recycle_corridors[s_id] = "bottom" if idx % 2 == 0 else "top"

        # Fallback for any unplaced units
        stages_fallback = self.graph.compute_stages()
        for uid in self.units:
            if uid not in positions:
                st = stages_fallback.get(uid, 0)
                positions[uid] = (self.origin[0] + st * self.bay_width, self.origin[1])

        # 8. Resolve relative_to and align hints with convergence loop
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
                        (rel.get("offset") or 60.0)
                        if isinstance(rel, dict)
                        else (getattr(rel, "offset", None) or 60.0)
                    )

                    if target in positions:
                        tx, ty = positions[target]
                        t_size = self.units[target].get("size") or (40, 40)
                        u_size = u.get("size") or (40, 40)
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

        # 9. Port-to-port elevation alignment pass
        self._align_port_elevations(positions, fixed_units)

        return positions
