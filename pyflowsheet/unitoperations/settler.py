from ..core import Port, UnitOperation


class HorizontalSettler(UnitOperation):
    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(120, 50),
        description: str = "",
        capLength=None,
        internals=None,
        angle=0,
        showCapLines=True,
    ):
        if internals is None:
            internals = []
        super().__init__(id, name, position=position, size=size, internals=internals)

        self.capLength = capLength
        self.showCapLines = showCapLines
        self.updatePorts()
        if angle != 0:
            self.rotate(angle)

    def updatePorts(self):
        self.ports = {}
        self.ports["Feed"] = Port("Feed", self, (0, 0.5), (-1, 0))
        self.ports["LightOut"] = Port("LightOut", self, (1, 0.5), (1, 0), intent="out")
        self.ports["HeavyOut"] = Port("HeavyOut", self, (0.35, 1), (0, 1), intent="out")
        self.ports["Vent"] = Port("Vent", self, (0.5, 0), (0, -1), intent="out")

        # Aliases
        self.ports["In"] = self.ports["Feed"]
        self.ports["Out"] = self.ports["LightOut"]
        self.ports["Top"] = self.ports["Vent"]
        self.ports["Bottom"] = self.ports["HeavyOut"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        boot_h = min(8.0, h * 0.16)
        cyl_top = y + boot_h
        cyl_bot = y + h - boot_h
        cyl_h = cyl_bot - cyl_top

        if self.capLength is None:
            capLength = min(cyl_h / 2, w / 4)
        else:
            capLength = self.capLength

        # Cylindrical body
        ctx.rectangle(
            [
                (x + capLength, cyl_top),
                (x + w - capLength, cyl_bot),
            ],
            self.fillColor,
            self.fillColor,
            self.lineSize,
        )

        # Top and bottom shell lines
        ctx.line(
            (x + capLength, cyl_top),
            (x + w - capLength, cyl_top),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (x + capLength, cyl_bot),
            (x + w - capLength, cyl_bot),
            self.lineColor,
            self.lineSize,
        )

        # Left curved head
        ctx.chord(
            [
                (x, cyl_top),
                (x + 2 * capLength, cyl_bot),
            ],
            90,
            270,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=self.showCapLines,
        )

        # Right curved head
        ctx.chord(
            [
                (x + w - 2 * capLength, cyl_top),
                (x + w, cyl_bot),
            ],
            270,
            450,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=self.showCapLines,
        )

        # Internal overflow weir plate
        weir_x = x + 0.7 * w
        weir_top = cyl_top + cyl_h * 0.4
        ctx.line((weir_x, cyl_bot), (weir_x, weir_top), self.lineColor, self.lineSize)

        # Liquid boot sump
        boot_cx = x + 0.35 * w
        boot_w = min(14.0, w * 0.12)
        ctx.rectangle(
            [
                (boot_cx - boot_w / 2, cyl_bot),
                (boot_cx + boot_w / 2, y + h),
            ],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (boot_cx - boot_w / 2 - 2, y + h),
            (boot_cx + boot_w / 2 + 2, y + h),
            self.lineColor,
            self.lineSize,
        )

        # Top vent nozzle
        ctx.line(
            (x + 0.5 * w, cyl_top),
            (x + 0.5 * w, y),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (x + 0.5 * w - 3, y),
            (x + 0.5 * w + 3, y),
            self.lineColor,
            self.lineSize,
        )

        # Saddle supports
        self._drawSaddles(ctx, cyl_bot, y + h)

    def _drawSaddles(self, ctx, y_top, y_bot):
        x, _ = self.position
        w, _ = self.size

        saddle_w = min(10.0, w * 0.1)
        base_w = saddle_w * 1.4

        for frac in (0.18, 0.85):
            cx = x + w * frac
            p_tl = (cx - saddle_w / 2, y_top)
            p_tr = (cx + saddle_w / 2, y_top)
            p_br = (cx + base_w / 2, y_bot)
            p_bl = (cx - base_w / 2, y_bot)

            ctx.path(
                [p_tl, p_tr, p_br, p_bl],
                self.fillColor,
                self.lineColor,
                self.lineSize,
                close=True,
            )
            ctx.line(
                (cx - base_w / 2 - 2, y_bot),
                (cx + base_w / 2 + 2, y_bot),
                self.lineColor,
                self.lineSize,
            )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
