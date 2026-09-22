from __future__ import annotations

from math import cos, pi, radians, sin

from ..core import Port, UnitOperation


class PeristalticPump(UnitOperation):
    """ISO 10628 Peristaltic Pump (hose pump).

    Features a circular casing containing a flexible hose arc and a central
    rotor with roller wheels that compress the tube.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        position=(0, 0),
        size=(35, 35),
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
        r = min(w, h) * 0.46

        # 1. Circular casing
        ctx.circle(
            [(cx - r, cy - r), (cx + r, cy + r)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # 2. Flexible hose arc along lower casing perimeter
        # From left suction (x, cy) entering at angle pi, sweeping through pi/2 (bottom)
        # to 0 (right discharge) and exiting at (x + w, cy)
        r_hose = r * 0.72
        num_arc = 24
        hose_points = [(x, cy), (cx - r, cy)]
        for i in range(num_arc + 1):
            theta = pi * (1.0 - i / num_arc)
            px = cx + r_hose * cos(theta)
            py = cy + r_hose * sin(theta)
            hose_points.append((px, py))
        hose_points.extend([(cx + r, cy), (x + w, cy)])

        ctx.path(
            hose_points,
            fillColor=None,
            lineColor=self.lineColor,
            lineSize=self.lineSize * 1.6,
        )

        # 3. Flanges at suction (In) and discharge (Out)
        flange_h = min(w, h) * 0.35
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

        # 4. Central rotor hub
        r_hub = r * 0.18
        ctx.circle(
            [(cx - r_hub, cy - r_hub), (cx + r_hub, cy + r_hub)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # 5. Rotor arms and roller wheels
        # 3 rollers spaced 120 degrees apart (at 90° compressing the lower hose, 210°, 330°)
        arm_len = r * 0.48
        r_roller = r * 0.18
        roller_angles = [90, 210, 330]

        for deg in roller_angles:
            rad = radians(deg)
            rx = cx + arm_len * cos(rad)
            ry = cy + arm_len * sin(rad)
            # Arm
            ctx.line((cx, cy), (rx, ry), self.lineColor, self.lineSize)
            # Roller wheel
            ctx.circle(
                [(rx - r_roller, ry - r_roller), (rx + r_roller, ry + r_roller)],
                self.fillColor,
                self.lineColor,
                self.lineSize,
            )
            # Roller center pin
            ctx.circle(
                [(rx - 1.5, ry - 1.5), (rx + 1.5, ry + 1.5)],
                self.lineColor,
                self.lineColor,
                1,
            )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
