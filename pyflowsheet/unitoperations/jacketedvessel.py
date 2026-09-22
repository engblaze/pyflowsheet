from ..core import Port, UnitOperation


class JacketedVessel(UnitOperation):
    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(60, 100),
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
        self.ports["In"] = Port("In", self, (0.5, 0), (0, -1))
        self.ports["Out"] = Port("Out", self, (0.5, 1), (0, 1), intent="out")
        self.ports["JIn"] = Port("JIn", self, (0, 0.75), (-1, 0))
        self.ports["JOut"] = Port("JOut", self, (1, 0.35), (1, 0), intent="out")

        # Aliases
        self.ports["Top"] = self.ports["In"]
        self.ports["Bottom"] = self.ports["Out"]
        self.ports["JacketIn"] = self.ports["JIn"]
        self.ports["JacketOut"] = self.ports["JOut"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        thickness = min(6.0, w * 0.1)
        inner_x = x + thickness
        inner_w = w - 2 * thickness

        if self.capLength is None:
            capLength = min(inner_w / 2, h / 4)
        else:
            capLength = self.capLength

        # Inner vessel top dished head
        ctx.chord(
            [
                (inner_x, y),
                (inner_x + inner_w, y + 2 * capLength),
            ],
            180,
            360,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=self.showCapLines,
        )

        # Inner vessel cylindrical body
        ctx.rectangle(
            [
                (inner_x, y + capLength),
                (inner_x + inner_w, y + h - capLength - thickness),
            ],
            self.fillColor,
            self.fillColor,
            self.lineSize,
        )

        ctx.line(
            (inner_x, y + capLength),
            (inner_x, y + h - capLength - thickness),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (inner_x + inner_w, y + capLength),
            (inner_x + inner_w, y + h - capLength - thickness),
            self.lineColor,
            self.lineSize,
        )

        # Inner vessel bottom dished head
        ctx.chord(
            [
                (inner_x, y + h - 2 * capLength - thickness),
                (inner_x + inner_w, y + h - thickness),
            ],
            0,
            180,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=self.showCapLines,
        )

        # Thermal jacket casing
        jacket_start_y = y + h * 0.35

        # Top closures of jacket
        ctx.line(
            (inner_x, jacket_start_y),
            (x, jacket_start_y),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (inner_x + inner_w, jacket_start_y),
            (x + w, jacket_start_y),
            self.lineColor,
            self.lineSize,
        )

        # Outer jacket vertical walls
        ctx.line(
            (x, jacket_start_y),
            (x, y + h - capLength),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (x + w, jacket_start_y),
            (x + w, y + h - capLength),
            self.lineColor,
            self.lineSize,
        )

        # Outer jacket bottom head
        ctx.chord(
            [
                (x, y + h - 2 * capLength),
                (x + w, y + h),
            ],
            0,
            180,
            None,
            self.lineColor,
            self.lineSize,
            closePath=False,
        )

        # Jacket nozzles
        jin_y = y + h * 0.75
        jout_y = y + h * 0.35
        ctx.line((x - 3, jin_y), (x, jin_y), self.lineColor, self.lineSize)
        ctx.line((x + w, jout_y), (x + w + 3, jout_y), self.lineColor, self.lineSize)

        # Process bottom outlet nozzle passing through jacket
        ctx.line(
            (x + w / 2, y + h - thickness),
            (x + w / 2, y + h),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (x + w / 2 - 3, y + h),
            (x + w / 2 + 3, y + h),
            self.lineColor,
            self.lineSize,
        )

        # Process top inlet flange
        ctx.line(
            (x + w / 2 - 3, y),
            (x + w / 2 + 3, y),
            self.lineColor,
            self.lineSize,
        )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
