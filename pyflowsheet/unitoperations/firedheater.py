from __future__ import annotations

from ..core import Port, UnitOperation


class FiredHeater(UnitOperation):
    """ISO 10628 process furnace / fired heater.

    Features a refractory-lined radiant firebox, upper convection tube bank,
    exhaust flue gas stack with damper, bottom burner with flame symbol,
    and process inlet/outlet nozzles.
    """

    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(60, 90),
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
        self.ports["ProcessIn"] = Port("ProcessIn", self, (1.0, 0.25), (1, 0))
        self.ports["ProcessOut"] = Port("ProcessOut", self, (1.0, 0.75), (1, 0), intent="out")

        # Utility / combustion ports
        self.ports["Fuel"] = Port("Fuel", self, (0.5, 1.0), (0, 1))
        self.ports["Stack"] = Port("Stack", self, (0.5, 0.0), (0, -1), intent="out")

        # Aliases
        self.ports["In"] = self.ports["ProcessIn"]
        self.ports["Out"] = self.ports["ProcessOut"]
        self.ports["FuelIn"] = self.ports["Fuel"]
        self.ports["Burner"] = self.ports["Fuel"]
        self.ports["FlueGas"] = self.ports["Stack"]
        self.ports["FlueGasOut"] = self.ports["Stack"]
        self.ports["ProcessFeed"] = self.ports["ProcessIn"]
        self.ports["ProcessProduct"] = self.ports["ProcessOut"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size
        cx = x + 0.5 * w

        stack_w = min(14.0, 0.26 * w)
        conv_w = 0.60 * w

        # Key vertical levels
        y_stack_top = y
        y_stack_bot = y + 0.20 * h
        y_conv_top = y + 0.24 * h
        y_conv_bot = y + 0.38 * h
        y_rad_top = y + 0.42 * h
        y_rad_bot = y + 0.90 * h
        y_skirt_bot = y + 0.96 * h

        # 1. Furnace outer shell outline
        furnace_points = [
            # Stack top opening
            (cx - stack_w / 2, y_stack_top),
            (cx + stack_w / 2, y_stack_top),
            # Stack right wall
            (cx + stack_w / 2, y_stack_bot),
            # Breeching to convection section
            (cx + conv_w / 2, y_conv_top),
            # Convection right wall
            (cx + conv_w / 2, y_conv_bot),
            # Transition to radiant box
            (x + w, y_rad_top),
            # Radiant box right wall
            (x + w, y_rad_bot),
            # Skirt / bottom floor right
            (cx + 0.28 * w, y_skirt_bot),
            # Skirt / bottom floor left
            (cx - 0.28 * w, y_skirt_bot),
            # Radiant box left bottom
            (x, y_rad_bot),
            # Radiant box left wall
            (x, y_rad_top),
            # Transition from convection left
            (cx - conv_w / 2, y_conv_bot),
            # Convection left wall
            (cx - conv_w / 2, y_conv_top),
            # Breeching to stack left
            (cx - stack_w / 2, y_stack_bot),
        ]

        ctx.path(
            furnace_points,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            close=True,
        )

        # Stack top flange
        ctx.line(
            (cx - stack_w / 2 - 2, y_stack_top),
            (cx + stack_w / 2 + 2, y_stack_top),
            self.lineColor,
            self.lineSize,
        )

        # Stack damper
        ctx.line(
            (cx - stack_w / 2 + 2, y + 0.10 * h),
            (cx + stack_w / 2 - 2, y + 0.08 * h),
            self.lineColor,
            self.lineSize,
        )

        # 2. Convection section tube bank
        c_in_y = y + 0.25 * h
        # ProcessIn nozzle from furnace right wall to convection section
        ctx.line((cx + conv_w / 2, c_in_y), (x + w, c_in_y), self.lineColor, self.lineSize)
        ctx.line((x + w, c_in_y - 3), (x + w, c_in_y + 3), self.lineColor, self.lineSize)

        # Convection horizontal passes
        pass1_y = y + 0.28 * h
        pass2_y = y + 0.34 * h
        c_left = cx - conv_w / 2 + 3
        c_right = cx + conv_w / 2 - 3

        ctx.line(
            (c_right, pass1_y), (c_left, pass1_y), self.lineColor, max(1.0, self.lineSize * 0.7)
        )
        ctx.line(
            (c_left, pass1_y), (c_left, pass2_y), self.lineColor, max(1.0, self.lineSize * 0.7)
        )
        ctx.line(
            (c_left, pass2_y), (c_right, pass2_y), self.lineColor, max(1.0, self.lineSize * 0.7)
        )

        # Crossover downcomer along wall
        ctx.line(
            (c_left, pass2_y),
            (x + 0.15 * w, y_rad_top + 4),
            self.lineColor,
            max(1.0, self.lineSize * 0.7),
        )

        # 3. Radiant section tube coil
        r_top = y_rad_top + 6
        r_bot = y_rad_bot - 6
        p_out_y = y + 0.75 * h

        radiant_points = [
            (x + 0.15 * w, r_top),
            (x + 0.15 * w, r_bot),
            (x + 0.30 * w, r_bot),
            (x + 0.30 * w, r_top),
            (x + 0.70 * w, r_top),
            (x + 0.70 * w, r_bot),
            (x + 0.85 * w, r_bot),
            (x + 0.85 * w, p_out_y),
            (x + w, p_out_y),
        ]
        ctx.path(
            radiant_points,
            fillColor=None,
            lineColor=self.lineColor,
            lineSize=max(1.0, self.lineSize * 0.7),
            close=False,
        )

        # ProcessOut nozzle flange
        ctx.line((x + w, p_out_y - 3), (x + w, p_out_y + 3), self.lineColor, self.lineSize)

        # 4. Burner & flame
        # Burner nozzle
        ctx.line((cx, y_skirt_bot), (cx, y + h), self.lineColor, self.lineSize)
        ctx.line((cx - 3, y + h), (cx + 3, y + h), self.lineColor, self.lineSize)

        # Flame symbol pointing upward
        flame_pts = [
            (cx - 5, y_skirt_bot),
            (cx, y + 0.78 * h),
            (cx + 5, y_skirt_bot),
        ]
        ctx.path(
            flame_pts,
            fillColor=None,
            lineColor=self.lineColor,
            lineSize=max(1.0, self.lineSize * 0.8),
            close=True,
        )
        ctx.line(
            (cx, y_skirt_bot), (cx, y + 0.82 * h), self.lineColor, max(1.0, self.lineSize * 0.8)
        )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
