from ..core import Port, UnitOperation


class FlotationCell(UnitOperation):
    """ISO 10628 Dissolved Air Flotation (DAF) cell / flotation separator basin."""

    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(80, 50),
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
        self.ports["Feed"] = Port("Feed", self, (0.0, 0.5), (-1, 0))
        self.ports["Air"] = Port("Air", self, (0.2, 1.0), (0, 1))
        self.ports["Float"] = Port("Float", self, (1.0, 0.2), (1, 0), intent="out")
        self.ports["Effluent"] = Port("Effluent", self, (1.0, 0.8), (1, 0), intent="out")

        # Aliases
        self.ports["In"] = self.ports["Feed"]
        self.ports["Out"] = self.ports["Effluent"]
        self.ports["Froth"] = self.ports["Float"]
        self.ports["Scum"] = self.ports["Float"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        rim_y = y + 0.15 * h
        bot_y = y + h

        # Main rectangular basin body
        ctx.rectangle(
            [(x, rim_y), (x + w, bot_y)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # Influent contact chamber vertical weir baffle
        weir_x = x + 0.25 * w
        ctx.line((weir_x, bot_y), (weir_x, y + 0.45 * h), self.lineColor, self.lineSize)

        # Bottom aeration header (Air) at (0.2, 1.0)
        air_x = x + 0.2 * w
        ctx.line((air_x, bot_y), (air_x, y + 0.85 * h), self.lineColor, self.lineSize)
        ctx.line(
            (x + 0.08 * w, y + 0.85 * h),
            (x + 0.23 * w, y + 0.85 * h),
            self.lineColor,
            self.lineSize,
        )
        ctx.line((air_x - 3, bot_y), (air_x + 3, bot_y), self.lineColor, self.lineSize)

        # Rising microbubbles representation
        for bx, by in (
            (air_x - 4, y + 0.72 * h),
            (air_x + 2, y + 0.65 * h),
            (air_x - 2, y + 0.55 * h),
        ):
            ctx.line((bx, by), (bx, by - 2), self.lineColor, 1)

        # Inclined lamella plates in clarification zone
        for i in range(4):
            plate_x = x + (0.34 + i * 0.09) * w
            ctx.line(
                (plate_x, bot_y - 0.12 * h),
                (plate_x + 0.08 * w, y + 0.38 * h),
                self.lineColor,
                self.lineSize,
            )

        # Froth trough / skimmer weir at upper right
        trough_x = x + 0.82 * w
        ctx.line((trough_x, y + 0.28 * h), (x + w, y + 0.28 * h), self.lineColor, self.lineSize)
        ctx.line((trough_x, y + 0.28 * h), (trough_x, rim_y), self.lineColor, self.lineSize)

        # Underflow baffle for clarified effluent
        baffle_x = x + 0.80 * w
        ctx.line((baffle_x, rim_y), (baffle_x, bot_y - 0.25 * h), self.lineColor, self.lineSize)

        # Nozzle flange markers
        # Feed flange at (0.0, 0.5)
        feed_y = y + 0.5 * h
        ctx.line((x, feed_y - 3), (x, feed_y + 3), self.lineColor, self.lineSize)

        # Float flange at (1.0, 0.2)
        float_y = y + 0.2 * h
        ctx.line((x + w, float_y - 3), (x + w, float_y + 3), self.lineColor, self.lineSize)

        # Effluent flange at (1.0, 0.8)
        effluent_y = y + 0.8 * h
        ctx.line((x + w, effluent_y - 3), (x + w, effluent_y + 3), self.lineColor, self.lineSize)

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
