from __future__ import annotations

from ..core import Port, UnitOperation


class BaseValve(UnitOperation):
    """Base class for all standards-compliant valve bodies."""

    def __init__(
        self,
        id: str,
        name: str = "",
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (30.0, 20.0),
        description: str = "",
    ):
        super().__init__(id, name or id, position=position, size=size, description=description)
        self.updatePorts()

    def updatePorts(self) -> None:
        self.ports = {
            "In": Port("In", self, (0.0, 0.5), (-1, 0)),
            "Out": Port("Out", self, (1.0, 0.5), (1, 0), intent="out"),
        }

    def _draw_opposing_triangles(self, ctx) -> None:
        """Draws standard opposing hourglass triangles."""
        x, y = self.position
        w, h = self.size
        cx, cy = x + w / 2.0, y + h / 2.0

        left_tri = [(x, y), (cx, cy), (x, y + h)]
        right_tri = [(x + w, y), (cx, cy), (x + w, y + h)]
        ctx.path(left_tri, self.fillColor, self.lineColor, self.lineSize, close=True)
        ctx.path(right_tri, self.fillColor, self.lineColor, self.lineSize, close=True)


class GateValve(BaseValve):
    """Standard Gate Valve (opposing triangles meeting at vertex)."""

    def draw(self, ctx) -> None:
        self._draw_opposing_triangles(ctx)
        super().draw(ctx)


class GlobeValve(BaseValve):
    """Globe Valve (opposing triangles with solid central disc)."""

    def draw(self, ctx) -> None:
        self._draw_opposing_triangles(ctx)
        x, y = self.position
        w, h = self.size
        cx, cy = x + w / 2.0, y + h / 2.0
        r = min(w, h) * 0.22
        ctx.circle(
            [(cx - r, cy - r), (cx + r, cy + r)],
            self.lineColor,
            self.lineColor,
            self.lineSize,
        )
        super().draw(ctx)


class BallValve(BaseValve):
    """Ball Valve (opposing triangles with central hollow/open circle)."""

    def draw(self, ctx) -> None:
        self._draw_opposing_triangles(ctx)
        x, y = self.position
        w, h = self.size
        cx, cy = x + w / 2.0, y + h / 2.0
        r = min(w, h) * 0.25
        ctx.circle(
            [(cx - r, cy - r), (cx + r, cy + r)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )
        super().draw(ctx)


class ButterflyValve(BaseValve):
    """Butterfly Valve (opposing triangles with diagonal bar across center)."""

    def draw(self, ctx) -> None:
        self._draw_opposing_triangles(ctx)
        x, y = self.position
        w, h = self.size
        cx, cy = x + w / 2.0, y + h / 2.0
        r = min(w, h) * 0.4
        ctx.line(
            (cx - r * 0.6, cy + r),
            (cx + r * 0.6, cy - r),
            self.lineColor,
            self.lineSize * 1.5,
        )
        super().draw(ctx)


class NeedleValve(BaseValve):
    """Needle Valve (opposing triangles with central vertical pointer/arrow)."""

    def draw(self, ctx) -> None:
        self._draw_opposing_triangles(ctx)
        x, y = self.position
        w, h = self.size
        cx, cy = x + w / 2.0, y + h / 2.0
        needle_top = (cx, y - h * 0.2)
        needle_tip = (cx, cy + h * 0.3)
        ctx.line(needle_top, needle_tip, self.lineColor, self.lineSize)
        ctx.line((cx - 3, cy + 2), needle_tip, self.lineColor, self.lineSize)
        ctx.line((cx + 3, cy + 2), needle_tip, self.lineColor, self.lineSize)
        super().draw(ctx)


class DiaphragmValve(BaseValve):
    """Diaphragm Valve (opposing triangles with dome/arch over center)."""

    def draw(self, ctx) -> None:
        self._draw_opposing_triangles(ctx)
        x, y = self.position
        w, h = self.size
        cx, cy = x + w / 2.0, y + h / 2.0
        # Draw arched dome
        ctx.chord(
            [(cx - w * 0.25, y - h * 0.2), (cx + w * 0.25, cy)],
            180,
            360,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=True,
        )
        super().draw(ctx)


class PlugValve(BaseValve):
    """Plug Valve (opposing triangles with central rectangular plug)."""

    def draw(self, ctx) -> None:
        self._draw_opposing_triangles(ctx)
        x, y = self.position
        w, h = self.size
        cx, cy = x + w / 2.0, y + h / 2.0
        pw, ph = w * 0.2, h * 0.7
        ctx.rectangle(
            [(cx - pw / 2.0, cy - ph / 2.0), (cx + pw / 2.0, cy + ph / 2.0)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )
        super().draw(ctx)


class CheckValve(BaseValve):
    """Check Valve (opposing triangles with check flap / flow direction)."""

    def draw(self, ctx) -> None:
        self._draw_opposing_triangles(ctx)
        x, y = self.position
        w, h = self.size
        cx = x + w / 2.0
        # Check flap line across center
        ctx.line((cx, y), (cx, y + h), self.lineColor, self.lineSize * 1.5)
        super().draw(ctx)
