import importlib.util

from ..core import UnitOperation

package_name = "matplotlib"
spec = importlib.util.find_spec(package_name)

if spec is None:
    Warning(
        "Matplotlib is not installed. You cannot render tables. Please install matplotlib first!"
    )
    PYFLOWSHEET_MATPLOTLIB_MISSING = True
else:
    import base64
    from io import BytesIO

    import matplotlib.pyplot as plt

    plt.ioff()
    PYFLOWSHEET_MATPLOTLIB_MISSING = False


class Figure(UnitOperation):
    def __init__(
        self,
        id: str,
        name: str,
        fig,
        position=(0, 0),
        size=(40, 20),
        description: str = "",
    ):
        super().__init__(id, name, position=position, size=size)
        self.fig = fig
        self.drawBoundingBox = False

        return

    def draw(self, ctx):
        if not PYFLOWSHEET_MATPLOTLIB_MISSING:
            tmpfile = BytesIO()
            self.fig.savefig(tmpfile, format="png")
            encoded = base64.b64encode(tmpfile.getvalue()).decode("utf-8")
            data = f"data:image/png;base64,{encoded}"
            ctx.image(data, self.position, self.size)
        else:
            start = (self.position[0], self.position[1])
            end = (
                self.position[0] + self.size[0],
                self.position[1] + self.size[1],
            )
            ctx.line(start, end, (255, 0, 0), self.lineSize)

            start = (self.position[0] + self.size[0], self.position[1])
            end = (self.position[0], self.position[1] + self.size[1])
            ctx.line(start, end, (255, 0, 0), self.lineSize)

        ctx.rectangle(
            [
                self.position,
                (self.position[0] + self.size[0], self.position[1] + self.size[1]),
            ],
            None,
            self.lineColor,
            self.lineSize,
        )

        super().draw(ctx)

        return
