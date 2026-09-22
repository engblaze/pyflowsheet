from __future__ import annotations

from math import pi, sin

from ..core import Port, UnitOperation


class ProgressiveCavityPump(UnitOperation):
    """ISO 10628 Progressive Cavity Pump (eccentric screw pump).

    Features a horizontal stator casing with an inner sinusoidal helical rotor screw curve,
    suction inlet at the left, and discharge outlet at the right.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        position=(0, 0),
        size=(60, 25),
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
        cy = y + h * 0.5

        # Horizontal layout:
        # Suction chamber: x to stator_x1
        # Stator barrel: stator_x1 to stator_x2
        # Discharge neck: stator_x2 to x + w
        stator_x1 = x + w * 0.18
        stator_x2 = x + w * 0.82
        stator_top = y + h * 0.1
        stator_bot = y + h * 0.9

        neck_top = cy - h * 0.22
        neck_bot = cy + h * 0.22

        # 1. Outer casing outline (inlet housing, stator body, discharge horn)
        body_points = [
            (x, neck_top),
            (stator_x1, neck_top),
            (stator_x1, stator_top),
            (stator_x2, stator_top),
            (stator_x2, neck_top),
            (x + w, neck_top),
            (x + w, neck_bot),
            (stator_x2, neck_bot),
            (stator_x2, stator_bot),
            (stator_x1, stator_bot),
            (stator_x1, neck_bot),
            (x, neck_bot),
        ]

        ctx.path(
            body_points,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            close=True,
        )

        # 2. Stator casing transition / end flanges
        ctx.line((stator_x1, stator_top), (stator_x1, stator_bot), self.lineColor, self.lineSize)
        ctx.line((stator_x2, stator_top), (stator_x2, stator_bot), self.lineColor, self.lineSize)

        # 3. Flanges at suction (In) and discharge (Out)
        flange_h = h * 0.6
        ctx.line(
            (x, cy - flange_h * 0.5),
            (x, cy + flange_h * 0.5),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (x + w, cy - flange_h * 0.5),
            (x + w, cy + flange_h * 0.5),
            self.lineColor,
            self.lineSize,
        )

        # 4. Sinusoidal helical rotor screw curve inside stator
        num_steps = 48
        stator_len = stator_x2 - stator_x1
        amplitude = h * 0.26
        rotor_points = []
        cycles = 2.5
        for i in range(num_steps + 1):
            t = i / num_steps
            px = stator_x1 + t * stator_len
            py = cy + amplitude * sin(t * cycles * 2.0 * pi)
            rotor_points.append((px, py))

        ctx.path(rotor_points, None, self.lineColor, self.lineSize)

        # Stator internal cavity curve (interlocking dashed helix representing stator elastomer)
        stator_points = []
        for i in range(num_steps + 1):
            t = i / num_steps
            px = stator_x1 + t * stator_len
            py = cy - amplitude * sin(t * cycles * 2.0 * pi)
            stator_points.append((px, py))

        ctx.path(stator_points, None, self.lineColor, self.lineSize * 0.7, dashArray="3,2")

        # Drive shaft connection in suction housing
        ctx.line((x, cy), (stator_x1, cy), self.lineColor, self.lineSize)

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
