from __future__ import annotations

from math import cos, pi, sin
from typing import Literal

from ..core import Port, UnitOperation
from .tag import ISATag, parse_isa_tag

BalloonShape = Literal["discrete", "shared_display", "computer_function", "plc"]
LocationLine = Literal["field", "control_room", "behind_panel", "secondary"]


class Instrument(UnitOperation):
    """ANSI/ISA-5.1 compliant instrumentation balloon element with standard symbol shapes,
    location divider lines, and centered functional tag lettering.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        tag: str | ISATag | None = None,
        balloon_type: BalloonShape = "discrete",
        location: LocationLine = "field",
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (28.0, 28.0),
        description: str = "",
    ):
        super().__init__(id, name or id, position=position, size=size, description=description)
        raw_tag = tag if tag is not None else id
        self.tag: ISATag = parse_isa_tag(raw_tag) if isinstance(raw_tag, str) else raw_tag
        self.balloon_type: BalloonShape = balloon_type
        self.location: LocationLine = location
        self.fontSize = 8
        self.lineSize = 1.5
        self.showTitle = False  # The tag itself is drawn inside the balloon
        self.updatePorts()

    def updatePorts(self) -> None:
        self.ports = {
            "In": Port("In", self, (0.0, 0.5), (-1, 0)),
            "Out": Port("Out", self, (1.0, 0.5), (1, 0), intent="out"),
            "Top": Port("Top", self, (0.5, 0.0), (0, -1)),
            "Bottom": Port("Bottom", self, (0.5, 1.0), (0, 1), intent="out"),
        }
        # Directional aliases
        self.ports["West"] = self.ports["In"]
        self.ports["East"] = self.ports["Out"]
        self.ports["North"] = self.ports["Top"]
        self.ports["South"] = self.ports["Bottom"]

    def _draw_outer_shape(self, ctx) -> None:
        x, y = self.position
        w, h = self.size
        cx = x + w / 2.0
        cy = y + h / 2.0

        if self.balloon_type == "discrete":
            ctx.circle(
                [self.position, (x + w, y + h)], self.fillColor, self.lineColor, self.lineSize
            )
        elif self.balloon_type == "shared_display":
            # Outer square
            ctx.rectangle(
                [self.position, (x + w, y + h)], self.fillColor, self.lineColor, self.lineSize
            )
            # Inner circle touching edges
            ctx.circle([self.position, (x + w, y + h)], None, self.lineColor, self.lineSize)
        elif self.balloon_type == "computer_function":
            # Regular Hexagon
            r = min(w, h) / 2.0
            points = [(cx + r * cos(i * pi / 3.0), cy + r * sin(i * pi / 3.0)) for i in range(6)]
            ctx.path(points, self.fillColor, self.lineColor, self.lineSize, close=True)
        elif self.balloon_type == "plc":
            # Diamond (Rhombus)
            points = [
                (cx, y),
                (x + w, cy),
                (cx, y + h),
                (x, cy),
            ]
            ctx.path(points, self.fillColor, self.lineColor, self.lineSize, close=True)

    def _draw_location_lines(self, ctx) -> None:
        x, y = self.position
        w, h = self.size
        cy = y + h / 2.0

        if self.location == "control_room":
            # Single solid horizontal line across the center
            ctx.line((x, cy), (x + w, cy), self.lineColor, self.lineSize)
        elif self.location == "behind_panel":
            # Dashed horizontal line across center
            ctx.path([(x, cy), (x + w, cy)], None, self.lineColor, self.lineSize, dashArray="3,2")
        elif self.location == "secondary":
            # Double solid horizontal lines
            gap = 2.0
            ctx.line((x, cy - gap), (x + w, cy - gap), self.lineColor, self.lineSize)
            ctx.line((x, cy + gap), (x + w, cy + gap), self.lineColor, self.lineSize)

    def draw(self, ctx) -> None:
        self._draw_outer_shape(ctx)
        self._draw_location_lines(ctx)
        super().draw(ctx)

    def drawTextLayer(self, ctx, showPorts: bool = False) -> None:
        if showPorts:
            seen = set()
            for p in self.ports.values():
                if p not in seen:
                    seen.add(p)
                    p.draw(ctx)

        x, y = self.position
        w, h = self.size
        cx = x + w / 2.0
        cy = y + h / 2.0

        # Top half lettering (Variable + Function e.g. 'FIT')
        if self.tag.display_top:
            top_y = cy - h * 0.12
            ctx.text(
                (cx, top_y),
                text=self.tag.display_top,
                fontFamily=self.fontFamily,
                textColor=self.textColor,
                fontSize=self.fontSize,
                textAnchor="middle",
            )

        # Bottom half lettering (Loop number e.g. '101')
        if self.tag.display_bottom:
            bot_y = cy + h * 0.36
            ctx.text(
                (cx, bot_y),
                text=self.tag.display_bottom,
                fontFamily=self.fontFamily,
                textColor=self.textColor,
                fontSize=self.fontSize,
                textAnchor="middle",
            )
