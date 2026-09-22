from __future__ import annotations

from ..core import Port, UnitOperation


class ReciprocatingPump(UnitOperation):
    """ISO 10628 Reciprocating Pump (piston/plunger pump).

    Features a cylinder barrel with an internal reciprocating piston/plunger and connecting rod,
    integrated with suction and discharge check valves along a horizontal flow manifold.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        position=(0, 0),
        size=(45, 30),
        description: str = "",
        internals=None,
        angle=0,
    ):
        if internals is None:
            internals = []
        super().__init__(
            id,
            name,
            position=position,
            size=size,
            description=description,
            internals=internals,
        )
        self.updatePorts()
        if angle != 0:
            self.rotate(angle)

    def updatePorts(self):
        self.ports = {}
        self.ports["In"] = Port("In", self, (0.0, 0.5), (-1, 0))
        self.ports["Out"] = Port("Out", self, (1.0, 0.5), (1, 0), intent="out")

        # Aliases
        self.ports["Suction"] = self.ports["In"]
        self.ports["Discharge"] = self.ports["Out"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size
        cx = x + w * 0.5
        cy = y + h * 0.5

        # 1. Horizontal flow manifold line connecting In -> Check Valves -> Cylinder -> Out
        ctx.line((x, cy), (x + w, cy), self.lineColor, self.lineSize)

        # 2. Suction check valve (left of cylinder)
        sx = x + w * 0.22
        r_ball = min(w, h) * 0.12
        # Check valve housing circle
        ctx.circle(
            [(sx - r_ball * 1.5, cy - r_ball * 1.5), (sx + r_ball * 1.5, cy + r_ball * 1.5)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )
        # Check valve seat (vertical barrier line on suction side)
        ctx.line(
            (sx - r_ball * 0.8, cy - r_ball * 1.2),
            (sx - r_ball * 0.8, cy + r_ball * 1.2),
            self.lineColor,
            self.lineSize,
        )
        # Check valve ball
        ctx.circle(
            [(sx - r_ball, cy - r_ball), (sx + r_ball, cy + r_ball)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # 3. Discharge check valve (right of cylinder)
        dx = x + w * 0.78
        # Check valve housing circle
        ctx.circle(
            [(dx - r_ball * 1.5, cy - r_ball * 1.5), (dx + r_ball * 1.5, cy + r_ball * 1.5)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )
        # Check valve seat (vertical barrier line on suction side of valve)
        ctx.line(
            (dx - r_ball * 0.8, cy - r_ball * 1.2),
            (dx - r_ball * 0.8, cy + r_ball * 1.2),
            self.lineColor,
            self.lineSize,
        )
        # Check valve ball
        ctx.circle(
            [(dx - r_ball, cy - r_ball), (dx + r_ball, cy + r_ball)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # 4. Vertical cylinder barrel in center
        cyl_w = w * 0.32
        cyl_left = cx - cyl_w * 0.5
        cyl_right = cx + cyl_w * 0.5
        cyl_top = y + h * 0.1
        cyl_bottom = cy

        # Cylinder body
        ctx.rectangle(
            [(cyl_left, cyl_top), (cyl_right, cyl_bottom)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )
        # Cylinder head flange / cap at top
        ctx.line((cyl_left - 2, cyl_top), (cyl_right + 2, cyl_top), self.lineColor, self.lineSize)

        # 5. Piston / plunger inside cylinder
        piston_h = h * 0.14
        piston_y = y + h * 0.26
        ctx.rectangle(
            [(cyl_left + 2, piston_y - piston_h * 0.5), (cyl_right - 2, piston_y + piston_h * 0.5)],
            self.lineColor,
            self.lineColor,
            1,
        )

        # 6. Connecting rod extending upward from piston through cylinder head
        rod_top = y
        ctx.line(
            (cx, piston_y - piston_h * 0.5),
            (cx, rod_top),
            self.lineColor,
            self.lineSize * 1.2,
        )
        # Crosshead / rod handle at top
        ctx.line((cx - 4, rod_top), (cx + 4, rod_top), self.lineColor, self.lineSize)

        # 7. Flanges at suction (In) and discharge (Out)
        flange_h = h * 0.45
        ctx.line((x, cy - flange_h * 0.5), (x, cy + flange_h * 0.5), self.lineColor, self.lineSize)
        ctx.line(
            (x + w, cy - flange_h * 0.5),
            (x + w, cy + flange_h * 0.5),
            self.lineColor,
            self.lineSize,
        )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
