from __future__ import annotations

from ..core import Port, UnitOperation


class ShellAndTubeExchanger(UnitOperation):
    """ISO 10628 shell-and-tube heat exchanger (TEMA style).

    Features a horizontal cylindrical shell with left and right channel heads,
    tubesheet flange lines, internal longitudinal tube passes, segmental baffles,
    and shell/tube nozzle connections.
    """

    def __init__(
        self,
        id: str,
        name: str,
        position=(0, 0),
        size=(80, 40),
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
        # Tube-side ports (channel heads)
        self.ports["TubeIn"] = Port("TubeIn", self, (0.0, 0.5), (-1, 0))
        self.ports["TubeOut"] = Port("TubeOut", self, (1.0, 0.5), (1, 0), intent="out")

        # Shell-side ports
        self.ports["ShellIn"] = Port("ShellIn", self, (0.25, 0.0), (0, -1))
        self.ports["ShellOut"] = Port("ShellOut", self, (0.75, 1.0), (0, 1), intent="out")

        # Aliases
        self.ports["In"] = self.ports["TubeIn"]
        self.ports["Out"] = self.ports["TubeOut"]
        self.ports["TIn"] = self.ports["TubeIn"]
        self.ports["TOut"] = self.ports["TubeOut"]
        self.ports["SIn"] = self.ports["ShellIn"]
        self.ports["SOut"] = self.ports["ShellOut"]
        self.ports["InTube"] = self.ports["TubeIn"]
        self.ports["OutTube"] = self.ports["TubeOut"]
        self.ports["InShell"] = self.ports["ShellIn"]
        self.ports["OutShell"] = self.ports["ShellOut"]

    def _drawBasicShape(self, ctx):
        x, y = self.position
        w, h = self.size

        # Channel head width
        head_w = min(12.0, w * 0.15)
        shell_x1 = x + head_w
        shell_x2 = x + w - head_w
        shell_w = shell_x2 - shell_x1

        # Main shell cylindrical body
        ctx.rectangle(
            [(shell_x1, y), (shell_x2, y + h)],
            self.fillColor,
            self.lineColor,
            self.lineSize,
        )

        # Left channel head (bonnet)
        ctx.chord(
            [(x, y), (x + 2 * head_w, y + h)],
            90,
            270,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=True,
        )

        # Right channel head (bonnet)
        ctx.chord(
            [(x + w - 2 * head_w, y), (x + w, y + h)],
            270,
            450,
            self.fillColor,
            self.lineColor,
            self.lineSize,
            closePath=True,
        )

        # Tubesheet flanges (slight extension beyond shell OD)
        flange_ext = min(2.0, h * 0.06)
        ctx.line(
            (shell_x1, y - flange_ext),
            (shell_x1, y + h + flange_ext),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (shell_x2, y - flange_ext),
            (shell_x2, y + h + flange_ext),
            self.lineColor,
            self.lineSize,
        )

        # Longitudinal tube bundle lines
        for frac in (0.32, 0.44, 0.56, 0.68):
            ty = y + frac * h
            ctx.line(
                (shell_x1, ty),
                (shell_x2, ty),
                self.lineColor,
                max(1.0, self.lineSize * 0.6),
            )

        # Segmental baffles (alternating from top and bottom)
        baffle_x_fracs = [0.22, 0.40, 0.60, 0.78]
        for i, bfrac in enumerate(baffle_x_fracs):
            bx = shell_x1 + bfrac * shell_w
            if i % 2 == 0:
                # Top down baffle (leaves window at bottom)
                ctx.line((bx, y), (bx, y + 0.7 * h), self.lineColor, self.lineSize)
            else:
                # Bottom up baffle (leaves window at top)
                ctx.line((bx, y + 0.3 * h), (bx, y + h), self.lineColor, self.lineSize)

        # Shell nozzles
        # ShellIn nozzle at 0.25*w, y
        sin_x = x + 0.25 * w
        ctx.line((sin_x - 3, y), (sin_x + 3, y), self.lineColor, self.lineSize)

        # ShellOut nozzle at 0.75*w, y + h
        sout_x = x + 0.75 * w
        ctx.line(
            (sout_x - 3, y + h),
            (sout_x + 3, y + h),
            self.lineColor,
            self.lineSize,
        )

        # Tube nozzles
        ctx.line(
            (x, y + 0.5 * h - 3),
            (x, y + 0.5 * h + 3),
            self.lineColor,
            self.lineSize,
        )
        ctx.line(
            (x + w, y + 0.5 * h - 3),
            (x + w, y + 0.5 * h + 3),
            self.lineColor,
            self.lineSize,
        )

    def draw(self, ctx):
        self._drawBasicShape(ctx)
        super().draw(ctx)
