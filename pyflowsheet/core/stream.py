import math
from typing import Any

from .pathfinder import Pathfinder, compressPath


class Stream:
    def __init__(
        self,
        id,
        fromPort,
        toPort,
        line_type: str = "process",
        name: str | None = None,
        description: str = "",
    ):
        self.id = id
        self.name = name
        self.description = description
        self.lineColor = (0, 0, 0, 255)
        self.textColor = (0, 0, 0, 255)
        self.lineSize = 2
        self.fromPort = fromPort
        self.toPort = toPort
        self.showTitle = True
        self.fontFamily = "Arial"
        self.dashArray = None
        self.manualRouting = []
        self.showPoints = False
        self.labelOffset = (0, 10)
        self.calculated_route: list[tuple[float, float]] = []
        self.crossover_bridges: list[Any] = []
        self.knockout_masks: list[Any] = []
        self.line_type: str = line_type

    def draw(self, ctx, grid=None, minx=0, miny=0):
        if self.calculated_route:
            points = self.calculated_route
            startAnchor = points[0]
        elif len(self.manualRouting) == 0 and grid is not None:
            points, startAnchor = self._calculateAutoRoute(minx, miny, grid)
        else:
            points = []
            points.append(self.fromPort.get_position())
            for step in self.manualRouting:
                p = (points[-1][0] + step[0], points[-1][1] + step[1])
                points.append(p)
            points.append(self.toPort.get_position())
            startAnchor = points[0]

        effective_dash = self.dashArray
        effective_size = self.lineSize
        if self.line_type == "electric" and effective_dash is None:
            effective_dash = "6,4"
            effective_size = 1.5
        elif self.line_type in ("pneumatic", "digital", "capillary"):
            effective_size = 1.5

        if hasattr(ctx, "raw_path") and self.crossover_bridges:
            from ..layout.crossover import CrossoverDetector

            detector = CrossoverDetector()
            d_str = detector.build_svg_path_commands(points, self.crossover_bridges)
            ctx.raw_path(
                d_str,
                fillColor=None,
                lineColor=self.lineColor,
                lineSize=effective_size,
                dashArray=effective_dash,
                endMarker=True,
            )
        else:
            ctx.path(points, None, self.lineColor, effective_size, False, effective_dash, True)

        if self.line_type != "process":
            self._draw_signal_decorations(ctx, points)

        # Draw knockout masks if any
        for box in self.knockout_masks:
            ctx.rectangle(
                [(box.min_x, box.min_y), (box.max_x, box.max_y)],
                fillColor=(255, 255, 255, 255),
                lineColor=(255, 255, 255, 0),
                lineSize=0,
            )

        if self.showPoints:
            for p in points:
                ctx.circle(
                    [(p[0] - 2, p[1] - 2), (p[0] + 2, p[1] + 2)],
                    None,
                    (64, 64, 64, 255),
                    1,
                )

        if self.showTitle:
            textAnchor = (
                startAnchor[0] + self.labelOffset[0],
                startAnchor[1] + self.labelOffset[1],
            )
            ctx.text(
                textAnchor,
                text=self.id,
                fontFamily=self.fontFamily,
                textColor=self.textColor,
                fontSize="10",
            )

        if grid is not None:
            grid.cleanup()

        return

    def _draw_signal_decorations(self, ctx, points: list[tuple[float, float]]) -> None:
        """Renders ANSI/ISA-5.1 line decorations (pneumatic slashes, digital dots,
        capillary crosses) along straight route segments.
        """
        if not points or len(points) < 2:
            return

        if self.line_type == "pneumatic":
            # Draw double slash // marks periodically
            spacing = 24.0
            slash_len = 6.0
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                seg_len = math.hypot(dx, dy)
                if seg_len < 12.0:
                    continue
                ux, uy = dx / seg_len, dy / seg_len
                # Normal perpendicular to segment
                nx, ny = -uy, ux

                num_marks = max(1, int(seg_len / spacing))
                step = seg_len / (num_marks + 1)
                for k in range(1, num_marks + 1):
                    dist = k * step
                    cx, cy = p1[0] + ux * dist, p1[1] + uy * dist
                    # Draw pair of oblique slashes slanted at ~60 deg
                    for offset in (-2.5, 2.5):
                        sx, sy = cx + ux * offset, cy + uy * offset
                        # Tick segment with 60 deg slant
                        slant_x = ux * 3.0 + nx * slash_len
                        slant_y = uy * 3.0 + ny * slash_len
                        ctx.line(
                            (sx - slant_x / 2.0, sy - slant_y / 2.0),
                            (sx + slant_x / 2.0, sy + slant_y / 2.0),
                            self.lineColor,
                            1.0,
                        )

        elif self.line_type == "digital":
            # Periodic open dots along the line
            spacing = 20.0
            r = 2.0
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                seg_len = math.hypot(dx, dy)
                if seg_len < 10.0:
                    continue
                ux, uy = dx / seg_len, dy / seg_len
                num_marks = max(1, int(seg_len / spacing))
                step = seg_len / (num_marks + 1)
                for k in range(1, num_marks + 1):
                    cx, cy = p1[0] + ux * k * step, p1[1] + uy * k * step
                    ctx.circle(
                        [(cx - r, cy - r), (cx + r, cy + r)],
                        fillColor=(255, 255, 255, 255),
                        lineColor=self.lineColor,
                        lineSize=1.0,
                    )

        elif self.line_type == "capillary":
            # Periodic crosses (-x-x-)
            spacing = 24.0
            arm = 3.5
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                seg_len = math.hypot(dx, dy)
                if seg_len < 12.0:
                    continue
                ux, uy = dx / seg_len, dy / seg_len
                nx, ny = -uy, ux
                num_marks = max(1, int(seg_len / spacing))
                step = seg_len / (num_marks + 1)
                for k in range(1, num_marks + 1):
                    cx, cy = p1[0] + ux * k * step, p1[1] + uy * k * step
                    # Diagonal X cross
                    d1_start = (cx - ux * arm - nx * arm, cy - uy * arm - ny * arm)
                    d1_end = (cx + ux * arm + nx * arm, cy + uy * arm + ny * arm)
                    d2_start = (cx - ux * arm + nx * arm, cy - uy * arm + ny * arm)
                    d2_end = (cx + ux * arm - nx * arm, cy + uy * arm - ny * arm)
                    ctx.line(d1_start, d1_end, self.lineColor, 1.0)
                    ctx.line(d2_start, d2_end, self.lineColor, 1.0)

    def _calculateAutoRoute(self, minx, miny, grid):
        normalLength = 10
        points = []
        gridsize = 10
        startAnchor = (
            self.fromPort.get_position()[0] + self.fromPort.normal[0] * normalLength,
            self.fromPort.get_position()[1] + self.fromPort.normal[1] * normalLength,
        )
        endAnchor = (
            self.toPort.get_position()[0] + self.toPort.normal[0] * normalLength,
            self.toPort.get_position()[1] + self.toPort.normal[1] * normalLength,
        )

        startAnchor2 = (
            self.fromPort.get_position()[0],
            self.fromPort.get_position()[1],
        )
        endAnchor2 = (
            self.toPort.get_position()[0],
            self.toPort.get_position()[1],
        )

        startAnchor = (
            round(startAnchor[0] / gridsize) * gridsize,
            round(startAnchor[1] / gridsize) * gridsize,
        )
        endAnchor = (
            round(endAnchor[0] / gridsize) * gridsize,
            round(endAnchor[1] / gridsize) * gridsize,
        )

        startAnchor2 = (
            round(startAnchor2[0] / gridsize) * gridsize,
            round(startAnchor2[1] / gridsize) * gridsize,
        )
        endAnchor2 = (
            round(endAnchor2[0] / gridsize) * gridsize,
            round(endAnchor2[1] / gridsize) * gridsize,
        )
        sx = round((startAnchor[0] - minx) / gridsize)
        sy = round((startAnchor[1] - miny) / gridsize)

        ex = round((endAnchor[0] - minx) / gridsize)
        ey = round((endAnchor[1] - miny) / gridsize)

        scx = round((startAnchor2[0] - minx) / gridsize)
        scy = round((startAnchor2[1] - miny) / gridsize)

        ecx = round((endAnchor2[0] - minx) / gridsize)
        ecy = round((endAnchor2[1] - miny) / gridsize)

        start = grid.node(scx, scy)
        end = grid.node(ecx, ecy)

        grid.node(sx, sy).walkable = True
        grid.node(ex, ey).walkable = True
        grid.node(scx, scy).walkable = True
        grid.node(ecx, ecy).walkable = True

        finder = Pathfinder()
        path, _ = finder.find_path(start, end, grid)

        w = 10

        for step in path:
            grid.node(step[0], step[1]).weight += w

        path = compressPath(path)

        points.append(self.fromPort.get_position())
        for step in path:
            p = (step[0] * gridsize + minx, step[1] * gridsize + miny)
            points.append(p)

        realendpoint = self.toPort.get_position()
        if realendpoint[0] != points[-1][0] or realendpoint[1] != points[-1][1]:
            points.append(realendpoint)
        return points, startAnchor
