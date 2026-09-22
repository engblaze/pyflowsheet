from __future__ import annotations

from ..core import Port, UnitOperation


class Condenser(UnitOperation):
    """ISO 10628 surface condenser.

    Features a cylindrical vessel shell with dished heads, internal cooling
    tube bundle, vapor distribution impingement baffle, top vapor inlet,
    bottom condensate drain, and cooling utility supply/return nozzles.
    """

    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(60, 40),
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
        # Process ports
        self.ports["VaporIn"] = Port("VaporIn", self, (0.5, 0.0), (0, -1))
        self.ports["CondensateOut"] = Port("CondensateOut", self, (0.5, 1.0), (0, 1), intent="out")

        # Cooling utility ports
        self.ports["CoolingIn"] = Port("CoolingIn", self, (0.0, 0.6), (-1, 0))
        self.ports["CoolingOut"] = Port("CoolingOut", self, (1.0, 0.4), (1, 0), intent="out")

        # Aliases
        self.ports["In"] = self.ports["VaporIn"]
        self.ports["Out"] = self.ports["CondensateOut"]
        self.ports["Condensate"] = self.ports["CondensateOut"]
        self.ports["LiquidOut"] = self.ports["CondensateOut"]
        self.ports["CoolingWaterIn"] = self.ports["CoolingIn"]
        self.ports["CoolingWaterOut"] = self.ports["CoolingOut"]
        self.ports["UtilityIn"] = self.ports["CoolingIn"]
        self.ports["UtilityOut"] = self.ports["CoolingOut"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        y_top = y + 0.12 * h
        y_bot = y + 0.88 * h
        cap_w = min(8.0, w * 0.15)
        shell_x1 = x + cap_w
        shell_x2 = x + w - cap_w

        # 1. Main vessel cylindrical body
        ctx.rectangle(
            [(shell_x1, y_top), (shell_x2, y_bot)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # Left dished head
        ctx.chord(
            [(x, y_top), (x + 2 * cap_w, y_bot)],
            90,
            270,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=True,
        )

        # Right dished head
        ctx.chord(
            [(x + w - 2 * cap_w, y_top), (x + w, y_bot)],
            270,
            450,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=True,
        )

        # 2. Impingement baffle below vapor nozzle
        baffle_y = y_top + 0.15 * (y_bot - y_top)
        ctx.line((x + 0.38 * w, baffle_y), (x + 0.62 * w, baffle_y), self.lineColor, self.lineSize)

        # 3. Cooling coil / tube passes
        c_in_y = y + 0.60 * h
        c_out_y = y + 0.40 * h
        turn_x = shell_x2 - 3
        turn_rad = (c_in_y - c_out_y) / 2

        # Lower cooling pass
        ctx.line(
            (shell_x1, c_in_y),
            (turn_x, c_in_y),
            self.lineColor,
            max(1.0, self.lineSize * 0.7),
        )
        # Upper cooling pass
        ctx.line(
            (shell_x1 + 4, c_out_y),
            (turn_x, c_out_y),
            self.lineColor,
            max(1.0, self.lineSize * 0.7),
        )
        # U-turn at right
        ctx.chord(
            [(turn_x - turn_rad, c_out_y), (turn_x + turn_rad, c_in_y)],
            270,
            450,
            fillColor=None,
            lineColor=self.lineColor,
            lineSize=max(1.0, self.lineSize * 0.7),
            closePath=False,
        )

        # Intermediate tube lines to indicate full bundle
        for frac in (0.47, 0.53, 0.69):
            ty = y + frac * h
            ctx.line(
                (shell_x1, ty),
                (shell_x2, ty),
                self.lineColor,
                max(1.0, self.lineSize * 0.5),
            )

        # 4. VaporIn nozzle at (0.5*w, 0)
        cx = x + 0.5 * w
        ctx.line((cx, y_top), (cx, y), self.lineColor, self.lineSize)
        ctx.line((cx - 3, y), (cx + 3, y), self.lineColor, self.lineSize)

        # 5. CondensateOut nozzle at (0.5*w, 1.0*h)
        ctx.line((cx, y_bot), (cx, y + h), self.lineColor, self.lineSize)
        ctx.line((cx - 3, y + h), (cx + 3, y + h), self.lineColor, self.lineSize)

        # 6. Cooling utility nozzle flanges
        ctx.line((x, c_in_y - 3), (x, c_in_y + 3), self.lineColor, self.lineSize)
        ctx.line((x + w, c_out_y - 3), (x + w, c_out_y + 3), self.lineColor, self.lineSize)

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
