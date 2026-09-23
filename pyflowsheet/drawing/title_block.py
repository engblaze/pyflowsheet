from typing import Any


class TitleBlock:
    """ASME Y14.1 Standard Engineering Title Block populated from metadata."""

    def __init__(
        self,
        metadata: Any = None,
        rect: tuple[tuple[float, float], tuple[float, float]] = (
            (880.0, 660.0),
            (1260.0, 820.0),
        ),
    ):
        self.id = "title_block"
        self.rect = rect
        if metadata is None:
            self.meta = {}
        elif hasattr(metadata, "model_dump"):
            self.meta = metadata.model_dump()
        elif isinstance(metadata, dict):
            self.meta = dict(metadata)
        else:
            try:
                self.meta = dict(metadata)
            except Exception:
                self.meta = {}

    def _get(self, key: str, default: Any = None) -> Any:
        val = self.meta.get(key)
        return default if val is None else val

    def draw(self, ctx):
        ctx.startGroup(self.id)
        x0, y0 = self.rect[0]
        x1, y1 = self.rect[1]

        # Background and outer frame
        ctx.rectangle(
            [(x0, y0), (x1, y1)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.5,
        )

        # 1. Organization & CAGE Header (y0 to y0 + 32)
        h_org = 32.0
        y_org = y0 + h_org
        ctx.line((x0, y_org), (x1, y_org), lineColor=(0, 0, 0, 255), lineSize=1.0)

        # CAGE code column at x1 - 95
        x_cage = x1 - 95.0
        ctx.line((x_cage, y0), (x_cage, y_org), lineColor=(0, 0, 0, 255), lineSize=0.8)

        org_name = self._get("organization") or self._get(
            "company", "ADVANCED WATER SYSTEMS ENGINEERING"
        )
        ctx.text(
            (x0 + 10, y0 + 19),
            text=str(org_name),
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=8.5,
            textAnchor="start",
        )

        cage_code = str(self._get("cage_code") or "1A2B3")
        ctx.text(
            (x_cage + 6, y0 + 11),
            text="CAGE CODE",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x_cage + 6, y0 + 24),
            text=cage_code,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=8.0,
            textAnchor="start",
        )

        # 2. Drawing Title Section (y_org to y_org + 42)
        h_title = 42.0
        y_title = y_org + h_title
        ctx.line((x0, y_title), (x1, y_title), lineColor=(0, 0, 0, 255), lineSize=1.0)

        title_text = self._get("title") or self._get("name", "WATER TREATMENT PROCESS FLOW DIAGRAM")
        subtitle = self._get("subtitle") or "PROCESS FLOW DIAGRAM & P&ID SPECIFICATION"

        ctx.text(
            (x0 + 8, y_org + 10),
            text="TITLE / SYSTEM DESCRIPTION:",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x0 + 8, y_org + 23),
            text=str(title_text)[:42],
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=9.0,
            textAnchor="start",
        )
        ctx.text(
            (x0 + 8, y_org + 34),
            text=str(subtitle)[:50],
            fontFamily="Arial",
            textColor=(50, 50, 50, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # 3. Sign-off / Approval Block (y_title to y_title + 38)
        h_appr = 38.0
        y_appr = y_title + h_appr
        ctx.line((x0, y_appr), (x1, y_appr), lineColor=(0, 0, 0, 255), lineSize=1.0)

        col1_w = 126.0
        col2_w = 126.0
        x_appr1 = x0 + col1_w
        x_appr2 = x_appr1 + col2_w
        ctx.line(
            (x_appr1, y_title),
            (x_appr1, y_appr),
            lineColor=(0, 0, 0, 255),
            lineSize=0.6,
        )
        ctx.line(
            (x_appr2, y_title),
            (x_appr2, y_appr),
            lineColor=(0, 0, 0, 255),
            lineSize=0.6,
        )

        drawn_by = str(self._get("drawn_by") or "E. Vance")
        drawn_date = str(self._get("drawn_date") or "2026-09-20")
        checked_by = str(self._get("checked_by") or "M. Roberts")
        checked_date = str(self._get("checked_date") or "2026-09-21")
        approved_by = str(self._get("approved_by") or "H. Green")
        approved_date = str(self._get("approved_date") or "2026-09-22")

        # Drawn
        ctx.text(
            (x0 + 6, y_title + 10),
            text="DRAWN BY / DATE",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x0 + 6, y_title + 22),
            text=drawn_by,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.text(
            (x0 + 6, y_title + 32),
            text=drawn_date,
            fontFamily="Arial",
            textColor=(80, 80, 80, 255),
            fontSize=6.0,
            textAnchor="start",
        )

        # Checked
        ctx.text(
            (x_appr1 + 6, y_title + 10),
            text="CHECKED BY / DATE",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x_appr1 + 6, y_title + 22),
            text=checked_by,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.text(
            (x_appr1 + 6, y_title + 32),
            text=checked_date,
            fontFamily="Arial",
            textColor=(80, 80, 80, 255),
            fontSize=6.0,
            textAnchor="start",
        )

        # Approved
        ctx.text(
            (x_appr2 + 6, y_title + 10),
            text="APPROVED BY / DATE",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x_appr2 + 6, y_title + 22),
            text=approved_by,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.text(
            (x_appr2 + 6, y_title + 32),
            text=approved_date,
            fontFamily="Arial",
            textColor=(80, 80, 80, 255),
            fontSize=6.0,
            textAnchor="start",
        )

        # 4. Identification & Control Strip (y_appr to y_appr + 32)
        h_id = 32.0
        y_id = y_appr + h_id
        ctx.line((x0, y_id), (x1, y_id), lineColor=(0, 0, 0, 255), lineSize=1.0)

        x_size = x0 + 38.0
        x_dwg = x_size + 155.0
        x_rev = x_dwg + 38.0
        x_scale = x_rev + 75.0

        ctx.line((x_size, y_appr), (x_size, y_id), lineColor=(0, 0, 0, 255), lineSize=0.6)
        ctx.line((x_dwg, y_appr), (x_dwg, y_id), lineColor=(0, 0, 0, 255), lineSize=0.6)
        ctx.line((x_rev, y_appr), (x_rev, y_id), lineColor=(0, 0, 0, 255), lineSize=0.6)
        ctx.line(
            (x_scale, y_appr),
            (x_scale, y_id),
            lineColor=(0, 0, 0, 255),
            lineSize=0.6,
        )

        sheet_size = str(self._get("sheet_size") or "D")
        dwg_no = str(
            self._get("drawing_number")
            or self._get("dwg_no")
            or self._get("id")
            or "DWG-PFD-WT-002"
        )
        rev_id = str(self._get("revision") or self._get("rev") or "B")
        scale_val = str(self._get("scale") or "NTS")
        sheet_val = str(self._get("sheet") or "1 OF 1")

        # Size
        ctx.text(
            (x0 + 4, y_appr + 10),
            text="SIZE",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x0 + 19, y_appr + 24),
            text=sheet_size,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=8.5,
            textAnchor="middle",
        )

        # Dwg No
        ctx.text(
            (x_size + 6, y_appr + 10),
            text="DWG NO. / DOCUMENT ID",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x_size + 6, y_appr + 24),
            text=dwg_no,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=8.5,
            textAnchor="start",
        )

        # Rev
        ctx.text(
            (x_dwg + 4, y_appr + 10),
            text="REV",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x_dwg + 19, y_appr + 24),
            text=rev_id,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=8.5,
            textAnchor="middle",
        )

        # Scale
        ctx.text(
            (x_rev + 6, y_appr + 10),
            text="SCALE",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x_rev + 6, y_appr + 24),
            text=scale_val,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.5,
            textAnchor="start",
        )

        # Sheet
        ctx.text(
            (x_scale + 6, y_appr + 10),
            text="SHEET",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="start",
        )
        ctx.text(
            (x_scale + 6, y_appr + 24),
            text=sheet_val,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.5,
            textAnchor="start",
        )

        # 5. Technical Note & Projection Strip (y_id to y1)
        ctx.rectangle(
            [(x0, y_id), (x1, y1)],
            fillColor=(248, 248, 248, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.5,
        )
        status_val = self._get("status") or "ISSUED FOR CONSTRUCTION"
        units_val = self._get("units") or "MILLIMETERS [MM]"
        proj_val = self._get("projection") or "THIRD ANGLE"
        std_val = self._get("code_standard") or "ANSI/ASME Y14.1 / ISA-5.1"
        footer_note = f"STATUS: {status_val} | {units_val} | {proj_val} PROJECTION | {std_val}"
        ctx.text(
            (x0 + 8, y_id + 11),
            text=footer_note,
            fontFamily="Arial",
            textColor=(60, 60, 60, 255),
            fontSize=5.5,
            textAnchor="start",
        )

        ctx.endGroup()
