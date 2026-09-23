from typing import Any


class RevisionBlock:
    """ASME Y14.1 Revision History Table located at upper-right sheet border."""

    def __init__(
        self,
        rect: tuple[tuple[float, float], tuple[float, float]] = (
            (880.0, -20.0),
            (1260.0, 50.0),
        ),
        revisions: list[Any] | None = None,
    ):
        self.id = "revision_block"
        self.rect = rect
        norm_revisions = []
        for r in revisions or []:
            if hasattr(r, "model_dump"):
                norm_revisions.append(r.model_dump())
            elif isinstance(r, dict):
                norm_revisions.append(r)
            else:
                try:
                    norm_revisions.append(dict(r))
                except Exception:
                    norm_revisions.append({})
        self.revisions = norm_revisions

    def draw(self, ctx):
        ctx.startGroup(self.id)
        x0, y0 = self.rect[0]
        x1, y1 = self.rect[1]

        # Outer border
        ctx.rectangle(
            [(x0, y0), (x1, y1)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )

        # Header bar
        h_header = 18.0
        ctx.rectangle(
            [(x0, y0), (x1, y0 + h_header)],
            fillColor=(235, 240, 245, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.8,
        )

        ctx.text(
            ((x0 + x1) / 2.0, y0 + 12.0),
            text="REVISIONS",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.5,
            textAnchor="middle",
        )

        # Columns
        col_zone = x0 + 35.0
        col_rev = col_zone + 30.0
        col_desc = x1 - 130.0
        col_date = x1 - 65.0

        # Sub-header row
        h_sub = 14.0
        y_sub = y0 + h_header
        ctx.rectangle(
            [(x0, y_sub), (x1, y_sub + h_sub)],
            fillColor=(245, 245, 245, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.5,
        )
        ctx.text(
            (x0 + 17.5, y_sub + 9.5),
            text="ZONE",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=5.5,
            textAnchor="middle",
        )
        ctx.text(
            (col_zone + 15.0, y_sub + 9.5),
            text="REV",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=5.5,
            textAnchor="middle",
        )
        ctx.text(
            (col_rev + 10.0, y_sub + 9.5),
            text="DESCRIPTION",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=5.5,
            textAnchor="start",
        )
        ctx.text(
            (col_desc + 32.5, y_sub + 9.5),
            text="DATE",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=5.5,
            textAnchor="middle",
        )
        ctx.text(
            (col_date + 32.5, y_sub + 9.5),
            text="APPROVED",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=5.5,
            textAnchor="middle",
        )

        # Vertical column dividers
        for col_x in [col_zone, col_rev, col_desc, col_date]:
            ctx.line((col_x, y_sub), (col_x, y1), lineColor=(0, 0, 0, 255), lineSize=0.5)

        # Revision rows
        row_y = y_sub + h_sub
        row_h = (y1 - row_y) / max(len(self.revisions), 1)
        for i, rev in enumerate(self.revisions):
            ry = row_y + i * row_h
            if i > 0:
                ctx.line((x0, ry), (x1, ry), lineColor=(180, 180, 180, 255), lineSize=0.5)
            cy = ry + row_h / 2.0 + 2.0
            ctx.text(
                (x0 + 17.5, cy),
                text=str(rev.get("zone") or "-"),
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=6.0,
                textAnchor="middle",
            )
            ctx.text(
                (col_zone + 15.0, cy),
                text=str(rev.get("rev") or ""),
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=6.5,
                textAnchor="middle",
            )
            ctx.text(
                (col_rev + 6.0, cy),
                text=str(rev.get("description") or "")[:32],
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=5.5,
                textAnchor="start",
            )
            ctx.text(
                (col_desc + 32.5, cy),
                text=str(rev.get("date") or ""),
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=5.5,
                textAnchor="middle",
            )
            ctx.text(
                (col_date + 32.5, cy),
                text=str(rev.get("approved_by") or ""),
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=5.5,
                textAnchor="middle",
            )

        ctx.endGroup()
