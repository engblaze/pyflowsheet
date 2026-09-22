from ..core import Port, UnitOperation


class Hydrocyclone(UnitOperation):
    """ISO 10628 Hydrocyclone separator with upper cylindrical body and lower conical section."""

    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(30, 70),
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
        self.ports["Feed"] = Port("Feed", self, (0.0, 0.25), (-1, 0))
        self.ports["Overflow"] = Port("Overflow", self, (0.5, 0.0), (0, -1), intent="out")
        self.ports["Underflow"] = Port("Underflow", self, (0.5, 1.0), (0, 1), intent="out")

        # Aliases
        self.ports["In"] = self.ports["Feed"]
        self.ports["Top"] = self.ports["Overflow"]
        self.ports["Bottom"] = self.ports["Underflow"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        top_y = y + h * 0.1
        cyl_y = y + h * 0.4
        cone_bot_y = y + h * 0.88

        cx = x + w / 2
        pipe_w = min(w * 0.3, 10.0)
        apex_w = min(w * 0.25, 8.0)

        # Outer casing: top overflow nozzle, cylindrical upper section,
        # conical lower section, and bottom underflow nozzle
        body_points = [
            (cx - pipe_w / 2, y),
            (cx + pipe_w / 2, y),
            (cx + pipe_w / 2, top_y),
            (x + w, top_y),
            (x + w, cyl_y),
            (cx + apex_w / 2, cone_bot_y),
            (cx + apex_w / 2, y + h),
            (cx - apex_w / 2, y + h),
            (cx - apex_w / 2, cone_bot_y),
            (x, cyl_y),
            (x, top_y),
            (cx - pipe_w / 2, top_y),
        ]

        ctx.path(
            body_points,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            close=True,
        )

        # Flanges on top overflow and bottom underflow nozzles
        ctx.line(
            (cx - pipe_w / 2 - 2, y),
            (cx + pipe_w / 2 + 2, y),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (cx - apex_w / 2 - 2, y + h),
            (cx + apex_w / 2 + 2, y + h),
            self.lineColor,
            self.lineSize,
        )

        # Tangential feed nozzle flange at (0.0, 0.25)
        feed_y = y + 0.25 * h
        ctx.line(
            (x, feed_y - 4),
            (x, feed_y + 4),
            self.lineColor,
            self.lineSize,
        )

        # Internal vortex finder extending into cylindrical section
        vf_bot = y + 0.32 * h
        ctx.line((cx - pipe_w / 2, top_y), (cx - pipe_w / 2, vf_bot), self.lineColor, self.lineSize)
        ctx.line((cx + pipe_w / 2, top_y), (cx + pipe_w / 2, vf_bot), self.lineColor, self.lineSize)
        ctx.line(
            (cx - pipe_w / 2, vf_bot), (cx + pipe_w / 2, vf_bot), self.lineColor, self.lineSize
        )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
