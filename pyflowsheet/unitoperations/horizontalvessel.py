from ..core import Port, UnitOperation


class HorizontalVessel(UnitOperation):
    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(100, 40),
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
        self.ports["In"] = Port("In", self, (0, 0.5), (-1, 0))
        self.ports["Out"] = Port("Out", self, (1, 0.5), (1, 0), intent="out")
        self.ports["Top"] = Port("Top", self, (0.5, 0), (0, -1))
        self.ports["Bottom"] = Port("Bottom", self, (0.5, 1), (0, 1), intent="out")

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        if self.capLength is None:
            capLength = min(h / 2, w / 4)
        else:
            capLength = self.capLength

        # Cylindrical body
        ctx.rectangle(
            [
                (x + capLength, y),
                (x + w - capLength, y + h),
            ],
            self.fillColor,
            self.fillColor,
            self.lineSize,
        )

        # Top and bottom shell lines
        ctx.line(
            (x + capLength, y),
            (x + w - capLength, y),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (x + capLength, y + h),
            (x + w - capLength, y + h),
            self.lineColor,
            self.lineSize,
        )

        # Left curved head (arc pointing left)
        ctx.chord(
            [
                (x, y),
                (x + 2 * capLength, y + h),
            ],
            90,
            270,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=self.showCapLines,
        )

        # Right curved head (arc pointing right)
        ctx.chord(
            [
                (x + w - 2 * capLength, y),
                (x + w, y + h),
            ],
            270,
            450,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=self.showCapLines,
        )

        # Saddle supports
        self._drawSaddles(ctx)

    def _drawSaddles(self, ctx):
        x, y = self.position
        w, h = self.size

        saddle_h = min(8.0, h * 0.2)
        saddle_w = min(14.0, w * 0.15)
        base_w = saddle_w * 1.4

        for frac in (0.25, 0.75):
            cx = x + w * frac
            p_tl = (cx - saddle_w / 2, y + h)
            p_tr = (cx + saddle_w / 2, y + h)
            p_br = (cx + base_w / 2, y + h + saddle_h)
            p_bl = (cx - base_w / 2, y + h + saddle_h)

            ctx.path(
                [p_tl, p_tr, p_br, p_bl],
                self.fillColor,
                self.lineColor,
                self.lineSize,
                close=True,
            )
            ctx.line(
                (cx - base_w / 2 - 2, y + h + saddle_h),
                (cx + base_w / 2 + 2, y + h + saddle_h),
                self.lineColor,
                self.lineSize,
            )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
