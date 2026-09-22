from .baseinternal import BaseInternal


class StructuredPacking(BaseInternal):
    """Structured packing internal for column vessels representing dense corrugated packing."""

    def __init__(self, start: float = 0.0, end: float = 1.0, spacing: float = 10.0):
        self.parent = None
        self.start = start
        self.end = end
        self.spacing = spacing

    def draw(self, ctx):
        if self.parent is None:
            Warning("Internal has no parent set!")
            return

        unit = self.parent

        if getattr(unit, "capLength", None) is None:
            capLength = unit.size[0] / 2
        else:
            capLength = unit.capLength

        availableHeight = unit.size[1] - 2 * capLength
        y_top = unit.position[1] + capLength + availableHeight * self.start
        y_bottom = unit.position[1] + capLength + availableHeight * self.end
        x_left = unit.position[0]
        x_right = unit.position[0] + unit.size[0]

        line_color = unit.lineColor
        line_size = unit.lineSize

        # Boundary lines (support grids)
        ctx.line((x_left, y_top), (x_right, y_top), line_color, line_size)
        ctx.line((x_left, y_bottom), (x_right, y_bottom), line_color, line_size)

        spacing = max(2.0, float(self.spacing))

        # Downward-right corrugated diagonals: y - x = c
        c_start = (y_top - x_right) // spacing * spacing
        c_end = y_bottom - x_left
        c = c_start
        while c <= c_end:
            y1 = max(y_top, x_left + c)
            y2 = min(y_bottom, x_right + c)
            if y1 < y2:
                x1 = y1 - c
                x2 = y2 - c
                ctx.line((x1, y1), (x2, y2), line_color, line_size)
            c += spacing

        # Upward-right corrugated diagonals: y + x = c
        c_start = (y_top + x_left) // spacing * spacing
        c_end = y_bottom + x_right
        c = c_start
        while c <= c_end:
            y1 = max(y_top, c - x_right)
            y2 = min(y_bottom, c - x_left)
            if y1 < y2:
                x1 = c - y1
                x2 = c - y2
                ctx.line((x1, y1), (x2, y2), line_color, line_size)
            c += spacing
