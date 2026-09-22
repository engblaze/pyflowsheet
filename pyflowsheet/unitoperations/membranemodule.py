from ..core import Port, UnitOperation


class MembraneModule(UnitOperation):
    """ISO 10628 crossflow membrane separation module (RO / UF / MF / NF)."""

    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(70, 30),
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
        self.ports["Feed"] = Port("Feed", self, (0.0, 0.3), (-1, 0))
        self.ports["Retentate"] = Port("Retentate", self, (1.0, 0.3), (1, 0), intent="out")
        self.ports["Permeate"] = Port("Permeate", self, (0.5, 1.0), (0, 1), intent="out")

        # Aliases
        self.ports["In"] = self.ports["Feed"]
        self.ports["Out"] = self.ports["Retentate"]
        self.ports["Concentrate"] = self.ports["Retentate"]
        self.ports["Reject"] = self.ports["Retentate"]
        self.ports["Perm"] = self.ports["Permeate"]
        self.ports["Filtrate"] = self.ports["Permeate"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        # Vessel housing dimensions: main body covers upper 85%, permeate nozzle extends to bottom
        vh = 0.85 * h

        # Main vessel rectangle
        ctx.rectangle(
            [(x, y), (x + w, y + vh)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # End caps / header plates
        cap_w = min(4.0, w * 0.08)
        ctx.line((x + cap_w, y), (x + cap_w, y + vh), self.lineColor, self.lineSize)
        ctx.line((x + w - cap_w, y), (x + w - cap_w, y + vh), self.lineColor, self.lineSize)

        # Diagonal dashed membrane line across vessel
        ctx.path(
            [(x, y + vh), (x + w, y)],
            fillColor=None,
            lineColor=self.lineColor,
            lineSize=self.lineSize,
            dashArray="4,4",
        )

        # Permeate nozzle stub and flange at (0.5, 1.0)
        cx = x + 0.5 * w
        ctx.line((cx, y + vh), (cx, y + h), self.lineColor, self.lineSize)
        ctx.line((cx - 3, y + h), (cx + 3, y + h), self.lineColor, self.lineSize)

        # Feed nozzle flange at (0.0, 0.3)
        feed_y = y + 0.3 * h
        ctx.line((x, feed_y - 3), (x, feed_y + 3), self.lineColor, self.lineSize)

        # Retentate nozzle flange at (1.0, 0.3)
        ret_y = y + 0.3 * h
        ctx.line((x + w, ret_y - 3), (x + w, ret_y + 3), self.lineColor, self.lineSize)

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
