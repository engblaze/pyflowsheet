from .sheet_sizes import SheetSizeConfig, get_sheet_size_config


class DrawingBorder:
    """ASME Y14.1 Standard Drawing Border with neatline, inner margin, and zone grid."""

    def __init__(self, cfg: SheetSizeConfig | None = None):
        self.id = "drawing_border"
        self.cfg = cfg or get_sheet_size_config("D")
        self.inner_rect = self.cfg.inner_rect
        self.outer_rect = self.cfg.outer_rect

    def draw(self, ctx):
        ctx.startGroup(self.id)

        # Outer neatline
        ctx.rectangle(
            self.outer_rect,
            fillColor=None,
            lineColor=(60, 60, 60, 255),
            lineSize=0.75,
        )
        # Inner margin border
        ctx.rectangle(
            self.inner_rect,
            fillColor=None,
            lineColor=(0, 0, 0, 255),
            lineSize=1.5,
        )

        ix0, iy0 = self.inner_rect[0]
        ix1, iy1 = self.inner_rect[1]
        ox0, oy0 = self.outer_rect[0]
        ox1, oy1 = self.outer_rect[1]

        # Horizontal zones (numbered 1 to num_zones_x)
        num_zones_x = self.cfg.num_zones_x
        zone_w = (ix1 - ix0) / num_zones_x
        zone_labels_x = [str(i) for i in range(1, num_zones_x + 1)]
        for i in range(1, num_zones_x):
            x = ix0 + i * zone_w
            ctx.line((x, oy0), (x, iy0), lineColor=(0, 0, 0, 255), lineSize=0.75)
            ctx.line((x, iy1), (x, oy1), lineColor=(0, 0, 0, 255), lineSize=0.75)

        for i, lbl in enumerate(zone_labels_x):
            cx = ix0 + (i + 0.5) * zone_w
            ctx.text(
                (cx, oy0 + 10.5),
                text=lbl,
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=7.0,
                textAnchor="middle",
            )
            ctx.text(
                (cx, iy1 + 11.0),
                text=lbl,
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=7.0,
                textAnchor="middle",
            )

        # Vertical zones (e.g. A, B, C, D)
        zone_labels_y = list(self.cfg.zone_labels_y)
        num_zones_y = len(zone_labels_y)
        zone_h = (iy1 - iy0) / num_zones_y
        for j in range(1, num_zones_y):
            y = iy0 + j * zone_h
            ctx.line((ox0, y), (ix0, y), lineColor=(0, 0, 0, 255), lineSize=0.75)
            ctx.line((ix1, y), (ox1, y), lineColor=(0, 0, 0, 255), lineSize=0.75)

        for j, lbl in enumerate(zone_labels_y):
            cy = iy0 + (j + 0.5) * zone_h + 2.5
            ctx.text(
                (ox0 + 7.5, cy),
                text=lbl,
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=7.0,
                textAnchor="middle",
            )
            ctx.text(
                (ix1 + 7.5, cy),
                text=lbl,
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=7.0,
                textAnchor="middle",
            )

        # Centering marks
        mid_x = (ix0 + ix1) / 2.0
        mid_y = (iy0 + iy1) / 2.0
        ctx.line((mid_x, oy0 - 4), (mid_x, oy0), lineColor=(0, 0, 0, 255), lineSize=1.5)
        ctx.line((mid_x, oy1), (mid_x, oy1 + 4), lineColor=(0, 0, 0, 255), lineSize=1.5)
        ctx.line((ox0 - 4, mid_y), (ox0, mid_y), lineColor=(0, 0, 0, 255), lineSize=1.5)
        ctx.line((ox1, mid_y), (ox1 + 4, mid_y), lineColor=(0, 0, 0, 255), lineSize=1.5)

        ctx.endGroup()
