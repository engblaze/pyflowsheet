from __future__ import annotations

from ..core import Port, UnitOperation


class Reboiler(UnitOperation):
    """ISO 10628 kettle reboiler (TEMA K-shell).

    Features an enlarged upper vapor dome, internal U-tube heating bundle,
    vertical overflow weir plate separating boiling pool from bottoms sump,
    top vapor outlet, bottom liquid feed, bottom overflow drain, and heating
    utility connections at the channel head.
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
        # Process ports
        self.ports["LiquidIn"] = Port("LiquidIn", self, (0.25, 1.0), (0, 1))
        self.ports["VaporOut"] = Port("VaporOut", self, (0.45, 0.0), (0, -1), intent="out")
        self.ports["BottomsOut"] = Port("BottomsOut", self, (0.90, 1.0), (0, 1), intent="out")

        # Heating utility ports
        self.ports["HeatingIn"] = Port("HeatingIn", self, (0.0, 0.55), (-1, 0))
        self.ports["HeatingOut"] = Port("HeatingOut", self, (0.0, 0.80), (-1, 0), intent="out")

        # Aliases
        self.ports["In"] = self.ports["LiquidIn"]
        self.ports["Feed"] = self.ports["LiquidIn"]
        self.ports["Vapor"] = self.ports["VaporOut"]
        self.ports["VOut"] = self.ports["VaporOut"]
        self.ports["Bottoms"] = self.ports["BottomsOut"]
        self.ports["BOut"] = self.ports["BottomsOut"]
        self.ports["SteamIn"] = self.ports["HeatingIn"]
        self.ports["SteamOut"] = self.ports["HeatingOut"]
        self.ports["Condensate"] = self.ports["HeatingOut"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        head_w = min(10.0, w * 0.12)
        shell_x1 = x + head_w
        shell_x2 = x + w - head_w
        y_bot = y + 0.88 * h

        # 1. Main kettle shell body
        body_points = [
            (shell_x1, y + 0.42 * h),
            (x + 0.24 * w, y + 0.12 * h),
            (x + 0.68 * w, y + 0.12 * h),
            (x + 0.80 * w, y + 0.38 * h),
            (shell_x2, y + 0.38 * h),
            (shell_x2, y_bot),
            (shell_x1, y_bot),
        ]
        ctx.path(
            body_points,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            close=True,
        )

        # 2. Left channel head (bonnet)
        ctx.chord(
            [(x, y + 0.42 * h), (x + 2 * head_w, y_bot)],
            90,
            270,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=True,
        )

        # Left tubesheet flange line
        ctx.line(
            (shell_x1, y + 0.42 * h - 2),
            (shell_x1, y_bot + 2),
            self.lineColor,
            self.lineSize,
        )

        # 3. Right dished head
        ctx.chord(
            [(x + w - 2 * head_w, y + 0.38 * h), (x + w, y_bot)],
            270,
            450,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=True,
        )

        # 4. Overflow weir plate
        weir_x = x + 0.74 * w
        weir_top = y + 0.52 * h
        ctx.line((weir_x, y_bot), (weir_x, weir_top), self.lineColor, self.lineSize)

        # Liquid level in boiling pool
        ctx.path(
            [(shell_x1, weir_top), (weir_x, weir_top)],
            fillColor=None,
            lineColor=self.lineColor,
            lineSize=1.0,
            dashArray="3,3",
        )

        # 5. U-tube bundle
        t_top = y + 0.62 * h
        t_bot = y + 0.74 * h
        u_end = x + 0.60 * w
        u_rad = (t_bot - t_top) / 2
        # Upper and lower legs
        ctx.line((shell_x1, t_top), (u_end, t_top), self.lineColor, max(1.0, self.lineSize * 0.7))
        ctx.line((shell_x1, t_bot), (u_end, t_bot), self.lineColor, max(1.0, self.lineSize * 0.7))
        # U-bend turn
        ctx.chord(
            [(u_end - u_rad, t_top), (u_end + u_rad, t_bot)],
            270,
            450,
            fillColor=None,
            lineColor=self.lineColor,
            lineSize=max(1.0, self.lineSize * 0.7),
            closePath=False,
        )
        # Center tube
        ctx.line(
            (shell_x1, y + 0.68 * h),
            (u_end - 4, y + 0.68 * h),
            self.lineColor,
            max(1.0, self.lineSize * 0.7),
        )

        # 6. Nozzles and flanges
        # VaporOut nozzle at (0.45*w, 0)
        v_x = x + 0.45 * w
        ctx.line((v_x, y + 0.12 * h), (v_x, y), self.lineColor, self.lineSize)
        ctx.line((v_x - 3, y), (v_x + 3, y), self.lineColor, self.lineSize)

        # LiquidIn nozzle at (0.25*w, 1.0*h)
        l_x = x + 0.25 * w
        ctx.line((l_x, y_bot), (l_x, y + h), self.lineColor, self.lineSize)
        ctx.line((l_x - 3, y + h), (l_x + 3, y + h), self.lineColor, self.lineSize)

        # BottomsOut nozzle at (0.90*w, 1.0*h)
        b_x = x + 0.90 * w
        ctx.line((b_x, y_bot), (b_x, y + h), self.lineColor, self.lineSize)
        ctx.line((b_x - 3, y + h), (b_x + 3, y + h), self.lineColor, self.lineSize)

        # HeatingIn flange at (0, 0.55*h)
        hin_y = y + 0.55 * h
        ctx.line((x, hin_y - 3), (x, hin_y + 3), self.lineColor, self.lineSize)

        # HeatingOut flange at (0, 0.80*h)
        hout_y = y + 0.80 * h
        ctx.line((x, hout_y - 3), (x, hout_y + 3), self.lineColor, self.lineSize)

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
