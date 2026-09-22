from __future__ import annotations

from math import cos, pi, sin

from ..core import Port, UnitOperation


class Blower(UnitOperation):
    """ISO 10628 Centrifugal Blower (fan / centrifugal compressor).

    Features a centrifugal spiral/scroll casing with a central suction eye indication
    and a tangential discharge horn.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        position=(0, 0),
        size=(40, 40),
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
        cx = x + w * 0.42
        cy = y + h * 0.5

        r_top = h * 0.42
        r_left = w * 0.34
        r_bottom = h * 0.42

        horn_top = cy - h * 0.20
        horn_bot = cy + h * 0.20

        # 1. Scroll casing outer contour with tangential discharge horn
        # Points: Horn top right -> Horn top tangent -> Volute arc
        # -> Horn bottom transition -> Horn bottom right
        casing_points = [
            (x + w, horn_top),
            (cx, cy - r_top),
        ]

        # Smooth arc around top -> left -> bottom
        num_arc = 20
        for i in range(1, num_arc):
            t = i / num_arc
            # Angle sweeps clockwise in Cartesian (counter-clockwise in SVG coordinates)
            # from -pi/2 to -3pi/2
            theta = -pi * 0.5 - pi * t
            px = cx + r_left * cos(theta)
            py = cy + (r_top if sin(theta) < 0 else r_bottom) * sin(theta)
            casing_points.append((px, py))

        casing_points.append((cx, cy + r_bottom))
        # Transition from bottom of scroll to bottom edge of discharge horn
        casing_points.append((cx + w * 0.22, horn_bot))
        casing_points.append((x + w, horn_bot))

        ctx.path(
            casing_points,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            close=True,
        )

        # 2. Tangential discharge horn flange at (Out)
        ctx.line(
            (x + w, horn_top - 2),
            (x + w, horn_bot + 2),
            self.lineColor,
            self.lineSize,
        )

        # 3. Central suction eye
        r_eye = min(w, h) * 0.18
        ctx.circle(
            [(cx - r_eye, cy - r_eye), (cx + r_eye, cy + r_eye)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # Impeller blade indication inside suction eye
        b_len = r_eye * 0.65
        ctx.line((cx - b_len, cy), (cx + b_len, cy), self.lineColor, self.lineSize)
        ctx.line((cx, cy - b_len), (cx, cy + b_len), self.lineColor, self.lineSize)

        # 4. Suction inlet nozzle from (In) to suction eye
        ctx.line((x, cy), (cx - r_eye, cy), self.lineColor, self.lineSize)

        # Suction nozzle flange at (In)
        flange_h = h * 0.38
        ctx.line(
            (x, cy - flange_h * 0.5),
            (x, cy + flange_h * 0.5),
            self.lineColor,
            self.lineSize,
        )

        # 5. Volute cutwater / tongue indication
        ctx.line(
            (cx + r_eye * 1.3, cy + r_eye * 0.3),
            (cx + w * 0.22, horn_bot),
            self.lineColor,
            self.lineSize * 0.8,
        )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
