from dataclasses import dataclass


@dataclass
class SheetSizeConfig:
    name: str
    inner_rect: tuple[tuple[float, float], tuple[float, float]]
    margin: float = 15.0
    canvas_margin: float = 20.0
    num_zones_x: int = 8
    zone_labels_y: tuple[str, ...] = ("A", "B", "C", "D")
    revision_block_rect: tuple[tuple[float, float], tuple[float, float]] = (
        (880.0, -20.0),
        (1260.0, 50.0),
    )
    legend_rect: tuple[tuple[float, float], tuple[float, float]] = (
        (880.0, 58.0),
        (1260.0, 652.0),
    )
    title_block_rect: tuple[tuple[float, float], tuple[float, float]] = (
        (880.0, 660.0),
        (1260.0, 820.0),
    )
    notes_rect: tuple[tuple[float, float], tuple[float, float]] = (
        (-30.0, 660.0),
        (860.0, 820.0),
    )

    @property
    def outer_rect(self) -> tuple[tuple[float, float], tuple[float, float]]:
        return (
            (self.inner_rect[0][0] - self.margin, self.inner_rect[0][1] - self.margin),
            (self.inner_rect[1][0] + self.margin, self.inner_rect[1][1] + self.margin),
        )

    @property
    def bounds(self) -> list[float]:
        ox0, oy0 = self.outer_rect[0]
        ox1, oy1 = self.outer_rect[1]
        return [
            ox0 - self.canvas_margin,
            oy0 - self.canvas_margin,
            ox1 + self.canvas_margin,
            oy1 + self.canvas_margin,
        ]


_SHEET_PRESETS: dict[str, SheetSizeConfig] = {
    "D": SheetSizeConfig(
        name="D",
        inner_rect=((-40.0, -20.0), (1260.0, 820.0)),
        margin=15.0,
        canvas_margin=20.0,
    ),
    "C": SheetSizeConfig(
        name="C",
        inner_rect=((-30.0, -15.0), (900.0, 580.0)),
        margin=12.0,
        canvas_margin=15.0,
        revision_block_rect=((630.0, -15.0), (900.0, 40.0)),
        legend_rect=((630.0, 45.0), (900.0, 460.0)),
        title_block_rect=((630.0, 470.0), (900.0, 580.0)),
        notes_rect=((-20.0, 470.0), (620.0, 580.0)),
    ),
    "B": SheetSizeConfig(
        name="B",
        inner_rect=((-20.0, -10.0), (650.0, 420.0)),
        margin=10.0,
        canvas_margin=12.0,
        revision_block_rect=((450.0, -10.0), (650.0, 30.0)),
        legend_rect=((450.0, 35.0), (650.0, 330.0)),
        title_block_rect=((450.0, 340.0), (650.0, 420.0)),
        notes_rect=((-15.0, 340.0), (440.0, 420.0)),
    ),
    "A": SheetSizeConfig(
        name="A",
        inner_rect=((-15.0, -10.0), (480.0, 310.0)),
        margin=8.0,
        canvas_margin=10.0,
        revision_block_rect=((330.0, -10.0), (480.0, 25.0)),
        legend_rect=((330.0, 30.0), (480.0, 240.0)),
        title_block_rect=((330.0, 245.0), (480.0, 310.0)),
        notes_rect=((-10.0, 245.0), (320.0, 310.0)),
    ),
    "E": SheetSizeConfig(
        name="E",
        inner_rect=((-60.0, -30.0), (1800.0, 1180.0)),
        margin=20.0,
        canvas_margin=25.0,
        revision_block_rect=((1250.0, -30.0), (1800.0, 70.0)),
        legend_rect=((1250.0, 80.0), (1800.0, 930.0)),
        title_block_rect=((1250.0, 940.0), (1800.0, 1180.0)),
        notes_rect=((-45.0, 940.0), (1230.0, 1180.0)),
    ),
}


def get_sheet_size_config(name: str | None) -> SheetSizeConfig:
    key = str(name).strip().upper() if name else "D"
    return _SHEET_PRESETS.get(key, _SHEET_PRESETS["D"])
