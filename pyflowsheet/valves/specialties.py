from __future__ import annotations

from ..core import Port, UnitOperation


class SafetyReliefValve(UnitOperation):
    """Pressure Safety / Relief Valve (PSV / PRV).
    Angle body with inlet at bottom, discharge at right, and spring cap at top.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (30.0, 30.0),
        description: str = "",
    ):
        super().__init__(id, name or id, position=position, size=size, description=description)
        self.updatePorts()

    def updatePorts(self) -> None:
        self.ports = {
            "In": Port("In", self, (0.5, 1.0), (0, 1)),
            "Out": Port("Out", self, (1.0, 0.5), (1, 0), intent="out"),
        }

    def draw(self, ctx) -> None:
        x, y = self.position
        w, h = self.size
        cx, cy = x + w * 0.5, y + h * 0.5

        # Bottom inlet triangle
        tri_bot = [(cx - w * 0.25, y + h), (cx, cy), (cx + w * 0.25, y + h)]
        # Right outlet triangle
        tri_right = [(x + w, cy - h * 0.25), (cx, cy), (x + w, cy + h * 0.25)]
        ctx.path(tri_bot, self.fillColor, self.lineColor, self.lineSize, close=True)
        ctx.path(tri_right, self.fillColor, self.lineColor, self.lineSize, close=True)

        # Spring bonnet housing on top
        bonnet = [(cx - w * 0.2, y), (cx + w * 0.2, y + h * 0.3)]
        ctx.rectangle(
            bonnet,
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )
        ctx.line((cx, y + h * 0.3), (cx, cy), self.lineColor, self.lineSize)
        super().draw(ctx)


class RuptureDisc(UnitOperation):
    """Pressure Safety Element (PSE) / Rupture Disc.
    Flanged spool with concave rupture membrane.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (20.0, 20.0),
        description: str = "",
    ):
        super().__init__(id, name or id, position=position, size=size, description=description)
        self.updatePorts()

    def updatePorts(self) -> None:
        self.ports = {
            "In": Port("In", self, (0.0, 0.5), (-1, 0)),
            "Out": Port("Out", self, (1.0, 0.5), (1, 0), intent="out"),
        }

    def draw(self, ctx) -> None:
        x, y = self.position
        w, h = self.size
        # Flange lines
        ctx.line((x, y), (x, y + h), self.lineColor, self.lineSize * 1.5)
        ctx.line((x + w, y), (x + w, y + h), self.lineColor, self.lineSize * 1.5)
        # Pipe section
        ctx.line((x, y + h / 2.0), (x + w, y + h / 2.0), self.lineColor, 1.0)
        # Curved rupture membrane
        ctx.chord(
            [(x + w * 0.2, y + h * 0.1), (x + w * 0.8, y + h * 0.9)],
            270,
            90,
            None,
            self.lineColor,
            self.lineSize,
            closePath=False,
        )
        super().draw(ctx)


class GrabSamplingTee(UnitOperation):
    """Inline grab sampling tap with small sampling needle valve."""

    def __init__(
        self,
        id: str,
        name: str = "",
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (25.0, 25.0),
        description: str = "",
    ):
        super().__init__(id, name or id, position=position, size=size, description=description)
        self.updatePorts()

    def updatePorts(self) -> None:
        self.ports = {
            "In": Port("In", self, (0.0, 0.5), (-1, 0)),
            "Out": Port("Out", self, (1.0, 0.5), (1, 0), intent="out"),
            "Sample": Port("Sample", self, (0.5, 1.0), (0, 1), intent="out"),
        }

    def draw(self, ctx) -> None:
        x, y = self.position
        w, h = self.size
        cx, cy = x + w / 2.0, y + h * 0.5
        # Main pipe line
        ctx.line((x, cy), (x + w, cy), self.lineColor, self.lineSize)
        # Sampling branch down
        ctx.line((cx, cy), (cx, y + h), self.lineColor, self.lineSize)
        # Small sample valve symbol on branch
        vw, vh = w * 0.35, h * 0.25
        vy = y + h * 0.65
        ctx.path(
            [
                (cx - vw / 2.0, vy),
                (cx + vw / 2.0, vy + vh),
                (cx - vw / 2.0, vy + vh),
                (cx + vw / 2.0, vy),
            ],
            self.fillColor,
            self.lineColor,
            1.0,
            close=True,
        )
        super().draw(ctx)


class Strainer(UnitOperation):
    """Pipeline Strainer (Y-strainer or inline basket strainer)."""

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
            "Blowdown": Port("Blowdown", self, (0.75, 1.0), (0, 1), intent="out"),
        }

    def draw(self, ctx) -> None:
        x, y = self.position
        w, h = self.size
        cy = y + h * 0.5
        # Straight pipe body
        ctx.line((x, cy), (x + w, cy), self.lineColor, self.lineSize)
        # Angled strainer leg
        bx, by = x + w * 0.75, y + h
        ctx.line((x + w * 0.35, cy), (bx, by), self.lineColor, self.lineSize)
        ctx.line((x + w * 0.55, cy), (bx + w * 0.15, by), self.lineColor, self.lineSize)
        # Perforated screen hatching (dashed line across leg)
        ctx.path([(x + w * 0.35, cy + 2), (bx + 2, by)], None, self.lineColor, 1.0, dashArray="2,2")
        super().draw(ctx)


class SteamTrap(UnitOperation):
    """Steam Trap (condensate discharge trap)."""

    def __init__(
        self,
        id: str,
        name: str = "",
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (25.0, 25.0),
        description: str = "",
    ):
        super().__init__(id, name or id, position=position, size=size, description=description)
        self.updatePorts()

    def updatePorts(self) -> None:
        self.ports = {
            "In": Port("In", self, (0.0, 0.5), (-1, 0)),
            "Out": Port("Out", self, (1.0, 0.5), (1, 0), intent="out"),
        }

    def draw(self, ctx) -> None:
        x, y = self.position
        w, h = self.size
        # Outer circle
        ctx.circle([(x, y), (x + w, y + h)], self.fillColor, self.lineColor, self.lineSize)
        # Internal semi-circle / bucket barrier
        cx, cy = x + w / 2.0, y + h / 2.0
        r = min(w, h) / 2.0
        # Lower filled half or horizontal dividing line
        ctx.line((x, cy), (x + w, cy), self.lineColor, self.lineSize)
        ctx.chord(
            [(cx - r, cy - r), (cx + r, cy + r)],
            0,
            180,
            self.lineColor,
            self.lineColor,
            1.0,
            closePath=True,
        )
        super().draw(ctx)
