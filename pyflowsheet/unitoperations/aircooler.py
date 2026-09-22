from __future__ import annotations

from math import cos, pi, sin

from ..core import Port, UnitOperation


class AirCooler(UnitOperation):
    """ISO 10628 air-cooled heat exchanger (fin-fan cooler).

    Features a horizontal finned tube bundle at the top, a tapered plenum chamber,
    and a bottom forced-draft axial fan blade symbol.
    """

    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(70, 50),
        description: str = "",
        internals=None,
        angle=0,
    ):
        if internals is None:
            internals = []
        super().__init__(id, name, position=position, size=size, internals=internals)
        self.updatePorts()
        if angle != 0:
            self.rotate(angle)

    def updatePorts(self):
        self.ports = {}
        self.ports["In"] = Port("In", self, (0.0, 0.2), (-1, 0))
        self.ports["Out"] = Port("Out", self, (1.0, 0.2), (1, 0), intent="out")

        # Aliases
        self.ports["ProcessIn"] = self.ports["In"]
        self.ports["ProcessOut"] = self.ports["Out"]
        self.ports["TubeIn"] = self.ports["In"]
        self.ports["TubeOut"] = self.ports["Out"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        bundle_h = 0.38 * h
        plenum_bot_y = 0.68 * h
        fan_center_y = y + 0.84 * h
        fan_cx = x + 0.5 * w

        # 1. Finned tube bundle (top rectangle)
        ctx.rectangle(
            [(x, y), (x + w, y + bundle_h)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # Bundle headers / tube sheets at ends
        hdr_w = min(5.0, w * 0.08)
        ctx.line((x + hdr_w, y), (x + hdr_w, y + bundle_h), self.lineColor, self.lineSize)
        ctx.line((x + w - hdr_w, y), (x + w - hdr_w, y + bundle_h), self.lineColor, self.lineSize)

        # Horizontal tube passes
        t1_y = y + bundle_h * 0.35
        t2_y = y + bundle_h * 0.70
        ctx.line(
            (x + hdr_w, t1_y),
            (x + w - hdr_w, t1_y),
            self.lineColor,
            max(1.0, self.lineSize * 0.7),
        )
        ctx.line(
            (x + hdr_w, t2_y),
            (x + w - hdr_w, t2_y),
            self.lineColor,
            max(1.0, self.lineSize * 0.7),
        )

        # Vertical fin hatching lines
        num_fins = 7
        fin_spacing = (w - 2 * hdr_w) / (num_fins + 1)
        for i in range(1, num_fins + 1):
            fx = x + hdr_w + i * fin_spacing
            ctx.line((fx, y + 2), (fx, y + bundle_h - 2), self.lineColor, 1.0)

        # 2. Plenum chamber (trapezoid connecting bundle to fan ring)
        plenum_left_top = (x, y + bundle_h)
        plenum_right_top = (x + w, y + bundle_h)
        plenum_right_bot = (x + 0.78 * w, y + plenum_bot_y)
        plenum_left_bot = (x + 0.22 * w, y + plenum_bot_y)

        ctx.path(
            [plenum_left_top, plenum_right_top, plenum_right_bot, plenum_left_bot],
            fillColor=None,
            lineColor=self.lineColor,
            lineSize=self.lineSize,
            close=True,
        )

        # 3. Fan shroud & fan symbol
        fan_r = min(0.24 * w, 0.15 * h)
        ctx.circle(
            [
                (fan_cx - fan_r, fan_center_y - fan_r),
                (fan_cx + fan_r, fan_center_y + fan_r),
            ],
            fillColor=self.fillColor,
            lineColor=self.lineColor,
            lineSize=self.lineSize,
        )

        # Fan hub
        hub_r = max(2.0, fan_r * 0.25)
        ctx.circle(
            [
                (fan_cx - hub_r, fan_center_y - hub_r),
                (fan_cx + hub_r, fan_center_y + hub_r),
            ],
            fillColor=self.lineColor,
            lineColor=self.lineColor,
            lineSize=1.0,
        )

        # 4 Fan blades (propeller blades)
        for angle_deg in (45, 135, 225, 315):
            rad = angle_deg * pi / 180.0
            bx = fan_cx + fan_r * 0.88 * cos(rad)
            by = fan_center_y + fan_r * 0.88 * sin(rad)
            ctx.line(
                (fan_cx, fan_center_y),
                (bx, by),
                self.lineColor,
                max(1.5, self.lineSize * 0.8),
            )

        # Support legs
        ctx.line((x + 0.15 * w, y + bundle_h), (x + 0.15 * w, y + h), self.lineColor, self.lineSize)
        ctx.line((x + 0.85 * w, y + bundle_h), (x + 0.85 * w, y + h), self.lineColor, self.lineSize)

        # Inlet / outlet nozzle flanges at (0.0, 0.2) and (1.0, 0.2)
        in_y = y + 0.2 * h
        ctx.line((x, in_y - 3), (x, in_y + 3), self.lineColor, self.lineSize)
        ctx.line((x + w, in_y - 3), (x + w, in_y + 3), self.lineColor, self.lineSize)

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
