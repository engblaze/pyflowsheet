from ..core import Port, UnitOperation


class Vessel(UnitOperation):
    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(40, 100),
        description: str = "",
        capLength=None,
        internals=None,
        angle=0,
        showCapLines=True,
        head_type: str = "dished",
    ):
        if internals is None:
            internals = []
        super().__init__(id, name, position=position, size=size, internals=internals)

        valid_heads = ("dished", "conical", "flat")
        if head_type.lower() not in valid_heads:
            raise ValueError(f"Unknown head_type: {head_type}. Must be one of {valid_heads}.")

        self.head_type = head_type.lower()
        self.capLength = capLength
        self.showCapLines = showCapLines
        self.updatePorts()
        self.rotate(angle)

    def updatePorts(self):
        self.ports = {}

        self.ports["In"] = Port("In", self, (0.5, 1), (0, 1))
        self.ports["In2"] = Port("In2", self, (0.2, 1), (0, 1))
        self.ports["Out"] = Port("Out", self, (0.5, 0), (0, -1), intent="out")
        self.ports["Out2"] = Port("Out2", self, (0.8, 0), (0, -1), intent="out")

    def _drawBasicShape(self, ctx):
        if self.head_type == "flat":
            ctx.rectangle(
                [
                    self.position,
                    (
                        self.position[0] + self.size[0],
                        self.position[1] + self.size[1],
                    ),
                ],
                self.fillColor,
                self.lineColor,
                self.lineSize,
            )
            return

        if self.capLength is None:
            capLength = self.size[0] / 2
        else:
            capLength = self.capLength

        if self.head_type == "conical":
            coneLength = capLength

            # Top dished head
            ctx.chord(
                [
                    (self.position[0], self.position[1]),
                    (self.position[0] + self.size[0], self.position[1] + 2 * capLength),
                ],
                180,
                360,
                self.fillColor,
                self.lineColor,
                self.lineSize,
                closePath=self.showCapLines,
            )

            # Cylindrical shell body
            ctx.rectangle(
                [
                    (self.position[0], self.position[1] + capLength),
                    (
                        self.position[0] + self.size[0],
                        self.position[1] + self.size[1] - coneLength,
                    ),
                ],
                self.fillColor,
                self.fillColor,
                self.lineSize,
            )

            ctx.line(
                (self.position[0], self.position[1] + capLength),
                (
                    self.position[0],
                    self.position[1] + self.size[1] - coneLength,
                ),
                self.lineColor,
                self.lineSize,
            )
            ctx.line(
                (self.position[0] + self.size[0], self.position[1] + capLength),
                (
                    self.position[0] + self.size[0],
                    self.position[1] + self.size[1] - coneLength,
                ),
                self.lineColor,
                self.lineSize,
            )

            # Conical bottom
            p1 = (self.position[0], self.position[1] + self.size[1] - coneLength)
            p2 = (
                self.position[0] + self.size[0] / 2,
                self.position[1] + self.size[1],
            )
            p3 = (
                self.position[0] + self.size[0],
                self.position[1] + self.size[1] - coneLength,
            )

            ctx.path(
                [p1, p2, p3],
                self.fillColor,
                self.lineColor,
                self.lineSize,
                close=self.showCapLines,
            )
            return

        # Default "dished" heads
        ctx.rectangle(
            [
                (self.position[0], self.position[1] + capLength),
                (
                    self.position[0] + self.size[0],
                    self.position[1] + self.size[1] - capLength,
                ),
            ],
            self.fillColor,
            self.fillColor,
            self.lineSize,
        )

        ctx.line(
            (self.position[0], self.position[1] + capLength),
            (
                self.position[0],
                self.position[1] + self.size[1] - capLength,
            ),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (self.position[0] + self.size[0], self.position[1] + capLength),
            (
                self.position[0] + self.size[0],
                self.position[1] + self.size[1] - capLength,
            ),
            self.lineColor,
            self.lineSize,
        )

        ctx.chord(
            [
                (self.position[0], self.position[1]),
                (self.position[0] + self.size[0], self.position[1] + 2 * capLength),
            ],
            180,
            360,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=self.showCapLines,
        )

        ctx.chord(
            [
                (self.position[0], self.position[1] + self.size[1] - 2 * capLength),
                (self.position[0] + self.size[0], self.position[1] + self.size[1]),
            ],
            0,
            180,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=self.showCapLines,
        )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
