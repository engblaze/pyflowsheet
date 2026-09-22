from __future__ import annotations

from dataclasses import dataclass
from math import floor, hypot
from typing import Any


@dataclass(frozen=True)
class AABB:
    """Axis-Aligned Bounding Box representing a 2D rectangular spatial region."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center(self) -> tuple[float, float]:
        return ((self.min_x + self.max_x) / 2.0, (self.min_y + self.max_y) / 2.0)

    def intersects(self, other: AABB) -> bool:
        return not (
            self.max_x < other.min_x
            or self.min_x > other.max_x
            or self.max_y < other.min_y
            or self.min_y > other.max_y
        )

    def contains_point(self, point: tuple[float, float]) -> bool:
        x, y = point
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def expanded(self, margin: float) -> AABB:
        return AABB(
            self.min_x - margin,
            self.min_y - margin,
            self.max_x + margin,
            self.max_y + margin,
        )

    def distance_to_point(self, point: tuple[float, float]) -> float:
        x, y = point
        dx = max(self.min_x - x, 0.0, x - self.max_x)
        dy = max(self.min_y - y, 0.0, y - self.max_y)
        return hypot(dx, dy)


class SpatialIndex:
    """Pure-Python spatial grid index for fast 2D collision detection and bounding box queries."""

    def __init__(self, cell_size: float = 64.0):
        self.cell_size = max(cell_size, 1.0)
        self._grid: dict[tuple[int, int], list[tuple[str, AABB, Any]]] = {}
        self._items: dict[str, tuple[AABB, Any]] = {}

    def _cells_for_box(self, box: AABB) -> set[tuple[int, int]]:
        x0 = int(floor(box.min_x / self.cell_size))
        x1 = int(floor(box.max_x / self.cell_size))
        y0 = int(floor(box.min_y / self.cell_size))
        y1 = int(floor(box.max_y / self.cell_size))
        cells = set()
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                cells.add((x, y))
        return cells

    def insert(self, item_id: str, box: AABB, data: Any = None) -> None:
        if item_id in self._items:
            self.remove(item_id)
        self._items[item_id] = (box, data)
        for cell in self._cells_for_box(box):
            self._grid.setdefault(cell, []).append((item_id, box, data))

    def remove(self, item_id: str) -> None:
        if item_id not in self._items:
            return
        box, _ = self._items.pop(item_id)
        for cell in self._cells_for_box(box):
            bucket = self._grid.get(cell, [])
            self._grid[cell] = [entry for entry in bucket if entry[0] != item_id]
            if not self._grid[cell]:
                self._grid.pop(cell, None)

    def clear(self) -> None:
        self._grid.clear()
        self._items.clear()

    def query_intersects(self, box: AABB) -> list[tuple[str, AABB, Any]]:
        seen = set()
        results = []
        for cell in self._cells_for_box(box):
            for item_id, item_box, data in self._grid.get(cell, []):
                if item_id not in seen:
                    seen.add(item_id)
                    if box.intersects(item_box):
                        results.append((item_id, item_box, data))
        return results

    def query_point(self, point: tuple[float, float]) -> list[tuple[str, AABB, Any]]:
        cell = (
            int(floor(point[0] / self.cell_size)),
            int(floor(point[1] / self.cell_size)),
        )
        results = []
        for item_id, box, data in self._grid.get(cell, []):
            if box.contains_point(point):
                results.append((item_id, box, data))
        return results

    def nearest(
        self, point: tuple[float, float], max_distance: float | None = None
    ) -> tuple[str, AABB, Any] | None:
        best_dist = float("inf") if max_distance is None else max_distance
        best_item: tuple[str, AABB, Any] | None = None
        for item_id, (box, data) in self._items.items():
            dist = box.distance_to_point(point)
            if dist <= best_dist:
                best_dist = dist
                best_item = (item_id, box, data)
        return best_item

    def all_items(self) -> list[tuple[str, AABB, Any]]:
        return [(item_id, box, data) for item_id, (box, data) in self._items.items()]
