from __future__ import annotations

from collections import defaultdict, deque


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
