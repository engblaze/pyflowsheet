#!/usr/bin/env python3
"""
Process Flow Diagram (v2 with Physical Equipment Models) for Wastewater Treatment with IONP Recovery
Built using pyflowsheet (https://github.com/Nukleon84/pyflowsheet) and defined via YAML specification.

This script loads a standardized YAML flowsheet specification defining:
  - Equipment (Vessels with internals: Stirrer, Tubes)
  - Input & Output Stream Flags
  - Complete stream network connecting units, products, and recycle loops
  - Supporting P&ID components (Pumps, Valves, Sampling Valves, Instrumentation)
"""

import argparse
import os

import yaml

import pyflowsheet.backends.svgcontext as sc
from pyflowsheet import (
    Flowsheet,
    HorizontalLabelAlignment,
    Port,
    StreamFlag,
    SvgContext,
    VerticalLabelAlignment,
    Vessel,
)
from pyflowsheet.internals import Stirrer, Tubes

# ---------------------------------------------------------------------------
# Compatibility fix for pyflowsheet:
# pyflowsheet passes unit/stream IDs directly to SVG <g id="...">.
# SVG IDs cannot contain spaces or slashes, which otherwise triggers svgwrite
# validation errors for labels like 'Recovered IONP' or 'UV/US'.
# ---------------------------------------------------------------------------
_orig_startGroup = sc.SvgContext.startGroup
_orig_startTransformedGroup = sc.SvgContext.startTransformedGroup


def _safe_startGroup(self, group_id):
    safe_id = str(group_id).replace(" ", "_").replace("/", "_")
    return _orig_startGroup(self, safe_id)


def _safe_startTransformedGroup(self, element):
    orig_id = element.id
    try:
        element.id = str(orig_id).replace(" ", "_").replace("/", "_")
        return _orig_startTransformedGroup(self, element)
    finally:
        element.id = orig_id


sc.SvgContext.startGroup = _safe_startGroup
sc.SvgContext.startTransformedGroup = _safe_startTransformedGroup

ALIGNMENT_MAP_H = {
    "Center": HorizontalLabelAlignment.Center,
    "Left": HorizontalLabelAlignment.Left,
    "Right": HorizontalLabelAlignment.Right,
    "LeftOuter": HorizontalLabelAlignment.LeftOuter,
    "RightOuter": HorizontalLabelAlignment.RightOuter,
}

ALIGNMENT_MAP_V = {
    "Center": VerticalLabelAlignment.Center,
    "Top": VerticalLabelAlignment.Top,
    "Bottom": VerticalLabelAlignment.Bottom,
}


def _create_internal(internal_cfg: dict):
    itype = internal_cfg.get("type")
    if itype == "Stirrer":
        return Stirrer()
    elif itype == "Tubes":
        count = internal_cfg.get("tubes", 4)
        return Tubes(count)
    else:
        raise ValueError(f"Unknown internal type: {itype}")


# ---------------------------------------------------------------------------
# P&ID Component Graphical Annotations
# ---------------------------------------------------------------------------
class PidPump:
    """Renders a centrifugal or positive-displacement pump symbol onto the flowsheet."""

    def __init__(
        self,
        pid: str,
        center: tuple,
        orientation: str = "right",
        label_pos: str = "bottom",
    ):
        self.id = pid
        self.center = center
        self.orientation = orientation
        self.label_pos = label_pos

    def draw(self, ctx):
        cx, cy = self.center
        r = 10.0
        # White background circle to mask underlying stream path
        ctx.circle(
            [(cx - r, cy - r), (cx + r, cy + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.5,
        )
        # Flow direction triangle
        if self.orientation == "right":
            pts = [
                (cx - r * 0.35, cy - r * 0.65),
                (cx + r, cy),
                (cx - r * 0.35, cy + r * 0.65),
            ]
        elif self.orientation == "left":
            pts = [
                (cx + r * 0.35, cy - r * 0.65),
                (cx - r, cy),
                (cx + r * 0.35, cy + r * 0.65),
            ]
        elif self.orientation == "down":
            pts = [
                (cx - r * 0.65, cy - r * 0.35),
                (cx, cy + r),
                (cx + r * 0.65, cy - r * 0.35),
            ]
        else:  # up
            pts = [
                (cx - r * 0.65, cy + r * 0.35),
                (cx, cy - r),
                (cx + r * 0.65, cy + r * 0.35),
            ]
        ctx.path(
            pts,
            fillColor=(0, 0, 0, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )

    def drawTextLayer(self, ctx):
        cx, cy = self.center
        if self.label_pos == "bottom":
            pos = (cx, cy + 18)
            align = "middle"
        elif self.label_pos == "top":
            pos = (cx, cy - 14)
            align = "middle"
        elif self.label_pos == "left":
            pos = (cx - 14, cy + 3)
            align = "end"
        else:  # right
            pos = (cx + 14, cy + 3)
            align = "start"
        ctx.text(
            pos,
            text=self.id,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=8.0,
            textAnchor=align,
        )


class PidValve:
    """Renders control valves, check valves, and safety relief valves."""

    def __init__(
        self,
        vid: str,
        center: tuple,
        valve_type: str = "Valve",
        orientation: str = "horizontal",
        label_pos: str = "bottom",
    ):
        self.id = vid
        self.center = center
        self.valve_type = valve_type
        self.orientation = orientation
        self.label_pos = label_pos

    def draw(self, ctx):
        cx, cy = self.center
        w, h = 8.0, 5.0
        # Bowtie path
        if self.orientation in ("horizontal", "right", "left"):
            pts = [
                (cx - w, cy - h),
                (cx + w, cy + h),
                (cx + w, cy - h),
                (cx - w, cy + h),
            ]
        else:
            pts = [
                (cx - h, cy - w),
                (cx + h, cy + w),
                (cx - h, cy + w),
                (cx + h, cy - w),
            ]
        ctx.path(
            pts,
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
            close=True,
        )

        # Control valve actuator hat
        if "Control" in self.valve_type:
            ctx.line(
                (cx, cy - h),
                (cx, cy - h - 6),
                lineColor=(0, 0, 0, 255),
                lineSize=1.0,
            )
            ctx.path(
                [(cx - 6, cy - h - 6), (cx + 6, cy - h - 6), (cx, cy - h - 10)],
                fillColor=(255, 255, 255, 255),
                lineColor=(0, 0, 0, 255),
                lineSize=1.0,
                close=True,
            )
        # Check valve directional arrow
        elif "Check" in self.valve_type:
            if self.orientation == "left":
                ctx.line(
                    (cx + 3, cy - 3),
                    (cx - 3, cy),
                    lineColor=(0, 0, 0, 255),
                    lineSize=1.2,
                )
                ctx.line(
                    (cx + 3, cy + 3),
                    (cx - 3, cy),
                    lineColor=(0, 0, 0, 255),
                    lineSize=1.2,
                )
            else:
                ctx.line(
                    (cx - 3, cy - 3),
                    (cx + 3, cy),
                    lineColor=(0, 0, 0, 255),
                    lineSize=1.2,
                )
                ctx.line(
                    (cx - 3, cy + 3),
                    (cx + 3, cy),
                    lineColor=(0, 0, 0, 255),
                    lineSize=1.2,
                )
        # Safety Relief valve
        elif "Safety" in self.valve_type or "Relief" in self.valve_type:
            ctx.line(
                (cx, cy - h),
                (cx, cy - h - 5),
                lineColor=(0, 0, 0, 255),
                lineSize=1.0,
            )
            ctx.rectangle(
                [(cx - 3, cy - h - 10), (cx + 3, cy - h - 5)],
                fillColor=(255, 255, 255, 255),
                lineColor=(0, 0, 0, 255),
                lineSize=1.0,
            )

    def drawTextLayer(self, ctx):
        cx, cy = self.center
        if self.label_pos == "bottom":
            pos = (cx, cy + 15)
            align = "middle"
        elif self.label_pos == "top":
            offset_y = -18 if "Control" in self.valve_type else -15
            pos = (cx, cy + offset_y)
            align = "middle"
        elif self.label_pos == "left":
            pos = (cx - 12, cy + 3)
            align = "end"
        else:  # right
            pos = (cx + 12, cy + 3)
            align = "start"
        ctx.text(
            pos,
            text=self.id,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.5,
            textAnchor=align,
        )


class PidSampleValve:
    """Renders sampling tee takeoff line, miniature sampling valve, and tag."""

    def __init__(self, sid: str, tap: tuple, branch: tuple, label_pos: str = "bottom"):
        self.id = sid
        self.tap = tap
        self.branch = branch
        self.label_pos = label_pos

    def draw(self, ctx):
        # Branch line
        ctx.line(self.tap, self.branch, lineColor=(0, 0, 0, 255), lineSize=1.2)
        # Midpoint of branch line for sample valve
        mx = (self.tap[0] + self.branch[0]) / 2.0
        my = (self.tap[1] + self.branch[1]) / 2.0
        w, h = 4.0, 3.0
        if abs(self.branch[1] - self.tap[1]) > abs(self.branch[0] - self.tap[0]):
            pts = [
                (mx - w, my - h),
                (mx + w, my + h),
                (mx + w, my - h),
                (mx - w, my + h),
            ]
        else:
            pts = [
                (mx - h, my - w),
                (mx + h, my + w),
                (mx - h, my + w),
                (mx + h, my - w),
            ]
        ctx.path(
            pts,
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )

    def drawTextLayer(self, ctx):
        bx, by = self.branch
        if self.label_pos == "bottom":
            pos = (bx, by + 10)
            align = "middle"
        elif self.label_pos == "top":
            pos = (bx, by - 4)
            align = "middle"
        elif self.label_pos == "left":
            pos = (bx - 4, by + 3)
            align = "end"
        else:  # right
            pos = (bx + 4, by + 3)
            align = "start"
        ctx.text(
            pos,
            text=self.id,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor=align,
        )


class PidInstrument:
    """Renders ISA-5.1 circular instrument balloon with tag and process tap leader line."""

    def __init__(self, tag: str, center: tuple, tap: tuple):
        self.id = tag
        self.center = center
        self.tap = tap

    def draw(self, ctx):
        # Leader line from tap point to balloon center
        ctx.line(self.tap, self.center, lineColor=(120, 120, 120, 255), lineSize=1.0)
        # Instrument balloon circle
        cx, cy = self.center
        r = 10.0
        ctx.circle(
            [(cx - r, cy - r), (cx + r, cy + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )

    def drawTextLayer(self, ctx):
        cx, cy = self.center
        ctx.text(
            (cx, cy + 2.5),
            text=self.id,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="middle",
        )


# ---------------------------------------------------------------------------
# ANSI/ASME Y14.1 Drawing Sheet Layout (Border, Title Block, Legend, Notes)
# ---------------------------------------------------------------------------
class DrawingBorder:
    """ASME Y14.1 Standard Drawing Border with neatline, inner margin, and zone grid."""

    def __init__(self, inner_rect=((-40, -20), (1260, 820)), margin=15):
        self.id = "drawing_border"
        self.inner_rect = inner_rect
        self.margin = margin
        self.outer_rect = (
            (inner_rect[0][0] - margin, inner_rect[0][1] - margin),
            (inner_rect[1][0] + margin, inner_rect[1][1] + margin),
        )

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

        # Horizontal zones (8 zones per ASME Y14.1, numbered 1 to 8)
        num_zones_x = 8
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

        # Vertical zones (4 zones: A, B, C, D)
        zone_labels_y = ["A", "B", "C", "D"]
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


class RevisionBlock:
    """ASME Y14.1 Revision History Table located at upper-right sheet border."""

    def __init__(self, rect=((880, -20), (1260, 50)), revisions=None):
        self.id = "revision_block"
        self.rect = rect
        self.revisions = revisions or []

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
        col_zone = x0 + 35
        col_rev = col_zone + 30
        col_desc = x1 - 130
        col_date = x1 - 65

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
            (col_zone + 15, y_sub + 9.5),
            text="REV",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=5.5,
            textAnchor="middle",
        )
        ctx.text(
            (col_rev + 10, y_sub + 9.5),
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
                text=str(rev.get("zone", "-")),
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=6.0,
                textAnchor="middle",
            )
            ctx.text(
                (col_zone + 15, cy),
                text=str(rev.get("rev", "")),
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=6.5,
                textAnchor="middle",
            )
            ctx.text(
                (col_rev + 6, cy),
                text=str(rev.get("description", ""))[:32],
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=5.5,
                textAnchor="start",
            )
            ctx.text(
                (col_desc + 32.5, cy),
                text=str(rev.get("date", "")),
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=5.5,
                textAnchor="middle",
            )
            ctx.text(
                (col_date + 32.5, cy),
                text=str(rev.get("approved_by", "")),
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=5.5,
                textAnchor="middle",
            )

        ctx.endGroup()


class TitleBlock:
    """ASME Y14.1 Standard Engineering Title Block populated from YAML metadata."""

    def __init__(self, metadata: dict, rect=((880, 660), (1260, 820))):
        self.id = "title_block"
        self.meta = metadata or {}
        self.rect = rect

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

        org_name = self.meta.get("organization") or self.meta.get(
            "company", "ADVANCED WATER SYSTEMS ENGINEERING"
        )
        ctx.text(
            (x0 + 10, y0 + 19),
            text=org_name,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=8.5,
            textAnchor="start",
        )

        cage_code = str(self.meta.get("cage_code", "1A2B3"))
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

        title_text = self.meta.get("title") or self.meta.get(
            "name", "WATER TREATMENT PROCESS FLOW DIAGRAM"
        )
        subtitle = self.meta.get("subtitle") or "PROCESS FLOW DIAGRAM & P&ID SPECIFICATION"

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
            text=title_text[:42],
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=9.0,
            textAnchor="start",
        )
        ctx.text(
            (x0 + 8, y_org + 34),
            text=subtitle[:50],
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
        ctx.line((x_appr1, y_title), (x_appr1, y_appr), lineColor=(0, 0, 0, 255), lineSize=0.6)
        ctx.line((x_appr2, y_title), (x_appr2, y_appr), lineColor=(0, 0, 0, 255), lineSize=0.6)

        drawn_by = self.meta.get("drawn_by", "E. Vance")
        drawn_date = self.meta.get("drawn_date", "2026-09-20")
        checked_by = self.meta.get("checked_by", "M. Roberts")
        checked_date = self.meta.get("checked_date", "2026-09-21")
        approved_by = self.meta.get("approved_by", "H. Green")
        approved_date = self.meta.get("approved_date", "2026-09-22")

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
        ctx.line((x_scale, y_appr), (x_scale, y_id), lineColor=(0, 0, 0, 255), lineSize=0.6)

        sheet_size = self.meta.get("sheet_size", "D")
        dwg_no = (
            self.meta.get("drawing_number")
            or self.meta.get("dwg_no")
            or self.meta.get("id", "DWG-PFD-WT-002")
        )
        rev_id = self.meta.get("revision") or self.meta.get("rev", "B")
        scale_val = self.meta.get("scale", "NTS")
        sheet_val = self.meta.get("sheet", "1 OF 1")

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

        # 5. Technical Note & Projection Strip (y_id to y1 = 16px)
        ctx.rectangle(
            [(x0, y_id), (x1, y1)],
            fillColor=(248, 248, 248, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.5,
        )
        status_val = self.meta.get("status", "ISSUED FOR CONSTRUCTION")
        units_val = self.meta.get("units", "MILLIMETERS [MM]")
        proj_val = self.meta.get("projection", "THIRD ANGLE")
        std_val = self.meta.get("code_standard", "ANSI/ASME Y14.1 / ISA-5.1")
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


class DrawingLegend:
    """Standard PFD & P&ID Legend detailing symbols, lines, valves, pumps, instruments, and equipment."""

    def __init__(self, rect=((880, 58), (1260, 652))):
        self.id = "legend"
        self.rect = rect

    def draw(self, ctx):
        ctx.startGroup(self.id)
        x0, y0 = self.rect[0]
        x1, y1 = self.rect[1]

        # Background and outer frame
        ctx.rectangle(
            [(x0, y0), (x1, y1)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )

        # Header banner
        h_head = 20.0
        ctx.rectangle(
            [(x0, y0), (x1, y0 + h_head)],
            fillColor=(235, 240, 245, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.8,
        )
        ctx.text(
            ((x0 + x1) / 2.0, y0 + 13.5),
            text="FLOWSHEET & P&ID LEGEND",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=8.0,
            textAnchor="middle",
        )

        # Section 1: Piping & Stream Lines (y: y0 + 26 to y0 + 136)
        y_sec1 = y0 + 26.0
        ctx.text(
            (x0 + 10, y_sec1 + 9.0),
            text="1. PIPING & STREAM LINES",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.line(
            (x0 + 10, y_sec1 + 12.0),
            (x1 - 10, y_sec1 + 12.0),
            lineColor=(200, 200, 200, 255),
            lineSize=0.5,
        )

        # Major Process Stream
        y_item1 = y_sec1 + 24.0
        ctx.line((x0 + 15, y_item1), (x0 + 75, y_item1), lineColor=(0, 0, 0, 255), lineSize=2.2)
        ctx.text(
            (x0 + 85, y_item1 + 3.0),
            text="Major Process Stream (100 m^3/h)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Recycle Stream
        y_item2 = y_item1 + 20.0
        ctx.line((x0 + 15, y_item2), (x0 + 75, y_item2), lineColor=(0, 0, 0, 255), lineSize=1.5)
        ctx.text(
            (x0 + 85, y_item2 + 3.0),
            text="Recycle / Return Stream",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Instrument Tap / Leader Line
        y_item3 = y_item2 + 20.0
        ctx.line(
            (x0 + 15, y_item3), (x0 + 75, y_item3), lineColor=(120, 120, 120, 255), lineSize=1.0
        )
        ctx.text(
            (x0 + 85, y_item3 + 3.0),
            text="Instrument Process Tap / Leader",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Stream Boundary Flag
        y_item4 = y_item3 + 22.0
        flag_pts = [
            (x0 + 20, y_item4 - 7),
            (x0 + 60, y_item4 - 7),
            (x0 + 72, y_item4),
            (x0 + 60, y_item4 + 7),
            (x0 + 20, y_item4 + 7),
        ]
        ctx.path(
            flag_pts,
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.text(
            (x0 + 43, y_item4 + 2.5),
            text="FEED",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=5.5,
            textAnchor="middle",
        )
        ctx.text(
            (x0 + 85, y_item4 + 3.0),
            text="Stream Inflow / Outflow Boundary",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Section 2: Valves & Motive Equipment (y: y0 + 140 to y0 + 300)
        y_sec2 = y0 + 138.0
        ctx.text(
            (x0 + 10, y_sec2 + 9.0),
            text="2. VALVES & MOTIVE EQUIPMENT",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.line(
            (x0 + 10, y_sec2 + 12.0),
            (x1 - 10, y_sec2 + 12.0),
            lineColor=(200, 200, 200, 255),
            lineSize=0.5,
        )

        # Centrifugal Pump
        y_pmp = y_sec2 + 25.0
        cx_pmp = x0 + 45
        ctx.line((x0 + 15, y_pmp), (cx_pmp - 7, y_pmp), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx_pmp, y_pmp - 7), (cx_pmp, y_pmp - 12), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line(
            (cx_pmp, y_pmp - 12), (x0 + 75, y_pmp - 12), lineColor=(0, 0, 0, 255), lineSize=1.2
        )
        ctx.circle(
            [(cx_pmp - 7, y_pmp - 7), (cx_pmp + 7, y_pmp + 7)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )
        ctx.text(
            (x0 + 85, y_pmp + 3.0),
            text="Centrifugal Pump (P-101 .. P-107)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Control Valve
        y_cv = y_pmp + 30.0
        cx_cv = x0 + 45
        ctx.line((x0 + 15, y_cv), (x0 + 75, y_cv), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx_cv - 8, y_cv - 5),
                (cx_cv + 8, y_cv + 5),
                (cx_cv + 8, y_cv - 5),
                (cx_cv - 8, y_cv + 5),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line((cx_cv, y_cv - 5), (cx_cv, y_cv - 11), lineColor=(0, 0, 0, 255), lineSize=1.0)
        ctx.path(
            [(cx_cv - 6, y_cv - 11), (cx_cv + 6, y_cv - 11), (cx_cv, y_cv - 15)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.text(
            (x0 + 85, y_cv + 3.0),
            text="Control Valve with Actuator (FCV, PCV)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Check Valve
        y_ckv = y_cv + 26.0
        cx_ckv = x0 + 45
        ctx.line((x0 + 15, y_ckv), (x0 + 75, y_ckv), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx_ckv - 8, y_ckv - 5),
                (cx_ckv + 8, y_ckv + 5),
                (cx_ckv + 8, y_ckv - 5),
                (cx_ckv - 8, y_ckv + 5),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line(
            (cx_ckv - 3, y_ckv - 3), (cx_ckv + 3, y_ckv), lineColor=(0, 0, 0, 255), lineSize=1.2
        )
        ctx.line(
            (cx_ckv - 3, y_ckv + 3), (cx_ckv + 3, y_ckv), lineColor=(0, 0, 0, 255), lineSize=1.2
        )
        ctx.text(
            (x0 + 85, y_ckv + 3.0),
            text="Check / Non-Return Valve (CKV)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Pressure Safety Valve
        y_psv = y_ckv + 26.0
        cx_psv = x0 + 45
        ctx.line((x0 + 15, y_psv), (cx_psv, y_psv), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx_psv, y_psv), (cx_psv, y_psv + 12), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx_psv - 5, y_psv - 8),
                (cx_psv + 5, y_psv + 8),
                (cx_psv - 5, y_psv + 8),
                (cx_psv + 5, y_psv - 8),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line((cx_psv, y_psv - 8), (cx_psv, y_psv - 12), lineColor=(0, 0, 0, 255), lineSize=1.0)
        ctx.rectangle(
            [(cx_psv - 3, y_psv - 16), (cx_psv + 3, y_psv - 12)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.text(
            (x0 + 85, y_psv + 3.0),
            text="Safety Relief Valve (PSV)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Sampling Point
        y_smp = y_psv + 26.0
        cx_smp = x0 + 45
        ctx.line((x0 + 15, y_smp - 8), (x0 + 75, y_smp - 8), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx_smp, y_smp - 8), (cx_smp, y_smp + 8), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx_smp - 4, y_smp - 3),
                (cx_smp + 4, y_smp + 3),
                (cx_smp + 4, y_smp - 3),
                (cx_smp - 4, y_smp + 3),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.text(
            (x0 + 85, y_smp + 3.0),
            text="In-Line Sampling Valve (V-SMP)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Section 3: ISA-5.1 Instrumentation (y: y0 + 310 to y0 + 420)
        y_sec3 = y0 + 310.0
        ctx.text(
            (x0 + 10, y_sec3 + 9.0),
            text="3. INSTRUMENTATION (ISA-5.1)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.line(
            (x0 + 10, y_sec3 + 12.0),
            (x1 - 10, y_sec3 + 12.0),
            lineColor=(200, 200, 200, 255),
            lineSize=0.5,
        )

        # Instrument Balloon Symbol
        y_inst = y_sec3 + 26.0
        cx_inst = x0 + 45
        ctx.line(
            (x0 + 20, y_inst + 12), (cx_inst, y_inst), lineColor=(120, 120, 120, 255), lineSize=1.0
        )
        ctx.circle(
            [(cx_inst - 9, y_inst - 9), (cx_inst + 9, y_inst + 9)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )
        ctx.text(
            (cx_inst, y_inst + 2.5),
            text="FIT",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.0,
            textAnchor="middle",
        )
        ctx.text(
            (x0 + 85, y_inst + 3.0),
            text="Field-Mounted Instrument Balloon",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # ISA-5.1 Letter Code Table (2 columns)
        tags_col1 = [
            ("FIT", "Flow Indicating Transmitter"),
            ("LIT", "Level Indicating Transmitter"),
            ("PIT", "Pressure Indicating Transmitter"),
        ]
        tags_col2 = [
            ("PDIT", "Diff. Pressure Transmitter"),
            ("AIT", "Analytical Transmitter (pH/IONP)"),
            ("TT", "Temperature Transmitter"),
        ]

        y_tag_start = y_inst + 20.0
        for idx, (tag, desc) in enumerate(tags_col1):
            yt = y_tag_start + idx * 16.0
            ctx.text(
                (x0 + 18, yt),
                text=f"• {tag}:",
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=6.0,
                textAnchor="start",
            )
            ctx.text(
                (x0 + 48, yt),
                text=desc,
                fontFamily="Arial",
                textColor=(70, 70, 70, 255),
                fontSize=5.5,
                textAnchor="start",
            )

        for idx, (tag, desc) in enumerate(tags_col2):
            yt = y_tag_start + idx * 16.0
            ctx.text(
                (x0 + 190, yt),
                text=f"• {tag}:",
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=6.0,
                textAnchor="start",
            )
            ctx.text(
                (x0 + 225, yt),
                text=desc,
                fontFamily="Arial",
                textColor=(70, 70, 70, 255),
                fontSize=5.5,
                textAnchor="start",
            )

        # Section 4: Equipment Models (y: y0 + 430 to y1 - 10)
        y_sec4 = y0 + 430.0
        ctx.text(
            (x0 + 10, y_sec4 + 9.0),
            text="4. MAJOR EQUIPMENT ICONS",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.line(
            (x0 + 10, y_sec4 + 12.0),
            (x1 - 10, y_sec4 + 12.0),
            lineColor=(200, 200, 200, 255),
            lineSize=0.5,
        )

        # Mixer (stirred tank)
        y_eq1 = y_sec4 + 28.0
        ctx.rectangle(
            [(x0 + 25, y_eq1 - 12), (x0 + 65, y_eq1 + 12)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line(
            (x0 + 45, y_eq1 - 12), (x0 + 45, y_eq1 + 6), lineColor=(0, 0, 0, 255), lineSize=1.0
        )
        ctx.line((x0 + 37, y_eq1 + 6), (x0 + 53, y_eq1 + 6), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.text(
            (x0 + 85, y_eq1 + 3.0),
            text="Continuous Stirred Tank Mixer (Mixer)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # DAF Separator
        y_eq2 = y_eq1 + 30.0
        ctx.rectangle(
            [(x0 + 20, y_eq2 - 8), (x0 + 70, y_eq2 + 8)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.text(
            (x0 + 45, y_eq2 + 2.5),
            text="DAF",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="middle",
        )
        ctx.text(
            (x0 + 85, y_eq2 + 3.0),
            text="Flotation Separator (DAF)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Tubular Modules
        y_eq3 = y_eq2 + 28.0
        ctx.rectangle(
            [(x0 + 20, y_eq3 - 8), (x0 + 70, y_eq3 + 8)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        for tx in [x0 + 32, x0 + 45, x0 + 58]:
            ctx.line((tx, y_eq3 - 8), (tx, y_eq3 + 8), lineColor=(150, 150, 150, 255), lineSize=0.7)
        ctx.text(
            (x0 + 85, y_eq3 + 3.0),
            text="Tubular Reactor / Membrane (UV/US, NF)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        ctx.endGroup()


class GeneralNotes:
    """ASME General Notes Block in lower drawing field."""

    def __init__(self, notes=None, rect=((-30, 660), (860, 820))):
        self.id = "drawing_notes"
        self.rect = rect
        self.notes = notes or [
            "ALL PROCESS PIPING SIZED FOR 100 M^3/HR NOMINAL LIQUID THROUGHPUT.",
            "INSTRUMENTATION TAGGING PER ISA-5.1 IDENTIFICATION STANDARD.",
            "SUPERPARAMAGNETIC IRON OXIDE NANOPARTICLES (IONP) FUNCTIONALIZED FOR RECYCLING.",
            "INTERMEDIATE SAMPLE VALVES V-SMP-01 TO V-SMP-09 ARE 1/2-INCH NEEDLE VALVES.",
            "DO NOT SCALE DRAWING. WORK TO STATED DIMENSIONS.",
        ]

    def draw(self, ctx):
        ctx.startGroup(self.id)
        x0, y0 = self.rect[0]
        x1, y1 = self.rect[1]

        # Border box
        ctx.rectangle(
            [(x0, y0), (x1, y1)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )

        # Header bar
        h_head = 18.0
        ctx.rectangle(
            [(x0, y0), (x1, y0 + h_head)],
            fillColor=(245, 245, 245, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.6,
        )
        ctx.text(
            (x0 + 10, y0 + 12.5),
            text="GENERAL PROCESS NOTES & SPECIFICATIONS",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )

        # Numbered notes
        y_text = y0 + 30.0
        for idx, note in enumerate(self.notes[:5]):
            ny = y_text + idx * 16.0
            ctx.text(
                (x0 + 12, ny),
                text=f"{idx + 1}.",
                fontFamily="Arial",
                textColor=(0, 0, 0, 255),
                fontSize=6.5,
                textAnchor="start",
            )
            ctx.text(
                (x0 + 26, ny),
                text=note,
                fontFamily="Arial",
                textColor=(50, 50, 50, 255),
                fontSize=6.0,
                textAnchor="start",
            )

        # Reference standards notice along bottom
        ctx.text(
            (x0 + 12, y1 - 8.0),
            text="STANDARDS APPLICABLE: ANSI/ASME Y14.1 (FORMAT), ISA-5.1 (INSTRUMENTATION), ASME B31.3 (PROCESS PIPING).",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.5,
            textAnchor="start",
        )

        ctx.endGroup()


# ---------------------------------------------------------------------------
# Boundary Box Collision Detection & Position Adjustment
# ---------------------------------------------------------------------------
class BoundingBox:
    """Axis-aligned 2D bounding box for graphical components and labels."""

    def __init__(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        name: str = "",
        kind: str = "",
        obj: object = None,
    ):
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
        self.name = name
        self.kind = kind
        self.obj = obj

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def intersects(self, other: "BoundingBox", padding: float = 0.0) -> bool:
        """Returns True if this bounding box intersects with other, including padding."""
        return not (
            self.x2 + padding < other.x1
            or other.x2 + padding < self.x1
            or self.y2 + padding < other.y1
            or other.y2 + padding < self.y1
        )

    def overlap_area(self, other: "BoundingBox", padding: float = 0.0) -> float:
        """Returns the overlapping area with another bounding box."""
        ox = max(
            0.0,
            min(self.x2 + padding, other.x2 + padding) - max(self.x1 - padding, other.x1 - padding),
        )
        oy = max(
            0.0,
            min(self.y2 + padding, other.y2 + padding) - max(self.y1 - padding, other.y1 - padding),
        )
        return ox * oy

    def __repr__(self) -> str:
        return f"BoundingBox({self.name}, [{self.x1:.1f}, {self.y1:.1f}, {self.x2:.1f}, {self.y2:.1f}])"


def get_bounding_boxes(pfd: Flowsheet) -> list[BoundingBox]:
    """Calculates axis-aligned bounding boxes for all graphical elements in the flowsheet.

    Includes:
      - Unit operation bodies and text labels (accounting for rotations)
      - Stream labels
      - P&ID pump symbols and labels
      - P&ID valve symbols and labels
      - P&ID sampling valve takeoff/symbols and labels
      - P&ID instrumentation balloons and tags
    """
    boxes = []

    # 1. Unit operations (Equipment & Stream Flags)
    for uid, u in pfd.unitOperations.items():
        if u.rotation == 90:
            cx = u.position[0] + u.size[0] / 2.0
            cy = u.position[1] + u.size[1] / 2.0
            bx1 = cx - u.size[1] / 2.0
            bx2 = cx + u.size[1] / 2.0
            by1 = cy - u.size[0] / 2.0
            by2 = cy + u.size[0] / 2.0
        else:
            bx1 = u.position[0]
            by1 = u.position[1]
            bx2 = bx1 + u.size[0]
            by2 = by1 + u.size[1]
        boxes.append(BoundingBox(bx1, by1, bx2, by2, name=f"{uid}:body", kind="unit_body", obj=u))

        insert, align = u.getTextAnchor()
        text = u.name
        fs = 12.0
        w = len(text) * fs * 0.62
        if align == "middle":
            lx1 = insert[0] - w / 2.0
        elif align == "end":
            lx1 = insert[0] - w
        else:
            lx1 = insert[0]
        lx2 = lx1 + w
        ly1 = insert[1] - fs * 0.85
        ly2 = insert[1] + fs * 0.25
        boxes.append(
            BoundingBox(
                lx1,
                ly1,
                lx2,
                ly2,
                name=f"{uid}:label",
                kind="unit_label",
                obj=u,
            )
        )

    # 2. Streams
    for sid, s in pfd.streams.items():
        if len(s.manualRouting) == 0:
            norm_len = 10
            start_anchor = (
                s.fromPort.get_position()[0] + s.fromPort.normal[0] * norm_len,
                s.fromPort.get_position()[1] + s.fromPort.normal[1] * norm_len,
            )
        else:
            start_anchor = s.fromPort.get_position()
        tx = start_anchor[0] + s.labelOffset[0]
        ty = start_anchor[1] + s.labelOffset[1]
        fs = 10.0
        w = len(sid) * fs * 0.65
        lx1 = tx - w / 2.0
        lx2 = tx + w / 2.0
        ly1 = ty - fs * 0.85
        ly2 = ty + fs * 0.25
        boxes.append(
            BoundingBox(
                lx1,
                ly1,
                lx2,
                ly2,
                name=f"{sid}:label",
                kind="stream_label",
                obj=s,
            )
        )

    # 3. P&ID Annotations
    for a in pfd.annotations:
        if isinstance(a, PidPump):
            cx, cy = a.center
            boxes.append(
                BoundingBox(
                    cx - 10,
                    cy - 10,
                    cx + 10,
                    cy + 10,
                    name=f"{a.id}:symbol",
                    kind="pump_symbol",
                    obj=a,
                )
            )
            w = len(a.id) * 8.0 * 0.65
            if a.label_pos == "bottom":
                lx1, ly1 = cx - w / 2, cy + 18 - 7
            elif a.label_pos == "top":
                lx1, ly1 = cx - w / 2, cy - 14 - 7
            elif a.label_pos == "left":
                lx1, ly1 = cx - 14 - w, cy + 3 - 7
            else:
                lx1, ly1 = cx + 14, cy + 3 - 7
            boxes.append(
                BoundingBox(
                    lx1,
                    ly1,
                    lx1 + w,
                    ly1 + 10,
                    name=f"{a.id}:label",
                    kind="pump_label",
                    obj=a,
                )
            )

        elif isinstance(a, PidValve):
            cx, cy = a.center
            if a.orientation in ("horizontal", "right", "left"):
                w, h = 8.0, 5.0
            else:
                w, h = 5.0, 8.0
            y_top = (
                cy
                - h
                - (
                    10.0
                    if (
                        "Control" in a.valve_type
                        or "Safety" in a.valve_type
                        or "Relief" in a.valve_type
                    )
                    else 0.0
                )
            )
            boxes.append(
                BoundingBox(
                    cx - w,
                    y_top,
                    cx + w,
                    cy + h,
                    name=f"{a.id}:symbol",
                    kind="valve_symbol",
                    obj=a,
                )
            )
            lw = len(a.id) * 7.5 * 0.65
            if a.label_pos == "bottom":
                lx1, ly1 = cx - lw / 2, cy + 15 - 6.5
            elif a.label_pos == "top":
                offset_y = -18 if "Control" in a.valve_type else -15
                lx1, ly1 = cx - lw / 2, cy + offset_y - 6.5
            elif a.label_pos == "left":
                lx1, ly1 = cx - 12 - lw, cy + 3 - 6.5
            else:
                lx1, ly1 = cx + 12, cy + 3 - 6.5
            boxes.append(
                BoundingBox(
                    lx1,
                    ly1,
                    lx1 + lw,
                    ly1 + 9,
                    name=f"{a.id}:label",
                    kind="valve_label",
                    obj=a,
                )
            )

        elif isinstance(a, PidSampleValve):
            tx, ty = a.tap
            bx, by = a.branch
            mx, my = (tx + bx) / 2.0, (ty + by) / 2.0
            boxes.append(
                BoundingBox(
                    mx - 5,
                    my - 5,
                    mx + 5,
                    my + 5,
                    name=f"{a.id}:symbol",
                    kind="smp_symbol",
                    obj=a,
                )
            )
            lw = len(a.id) * 7.0 * 0.65
            if a.label_pos == "bottom":
                lx1, ly1 = bx - lw / 2, by + 10 - 6
            elif a.label_pos == "top":
                lx1, ly1 = bx - lw / 2, by - 4 - 6
            elif a.label_pos == "left":
                lx1, ly1 = bx - 4 - lw, by + 3 - 6
            else:
                lx1, ly1 = bx + 4, by + 3 - 6
            boxes.append(
                BoundingBox(
                    lx1,
                    ly1,
                    lx1 + lw,
                    ly1 + 8.5,
                    name=f"{a.id}:label",
                    kind="smp_label",
                    obj=a,
                )
            )

        elif isinstance(a, PidInstrument):
            cx, cy = a.center
            r = 10.0
            lw = len(a.id) * 6.5 * 0.65
            hw = max(r, lw / 2.0 + 1.0)
            boxes.append(
                BoundingBox(
                    cx - hw,
                    cy - r,
                    cx + hw,
                    cy + r,
                    name=f"{a.id}:balloon",
                    kind="inst_balloon",
                    obj=a,
                )
            )

    return boxes


def check_collisions(pfd: Flowsheet, padding: float = 1.0) -> list[tuple[BoundingBox, BoundingBox]]:
    """Checks the boundary boxes of graphical components in the flowsheet and returns collisions.

    Args:
        pfd: The Flowsheet instance.
        padding: Safety clearance margin in pixels around bounding boxes.

    Returns:
        List of tuples containing colliding (BoundingBox, BoundingBox) pairs.
    """
    boxes = get_bounding_boxes(pfd)
    collisions = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            b1 = boxes[i]
            b2 = boxes[j]
            # Ignore same entity (e.g. symbol vs label of the same pump)
            if b1.name.split(":")[0] == b2.name.split(":")[0]:
                continue
            if b1.name.startswith(b2.name.split(":")[0]) or b2.name.startswith(
                b1.name.split(":")[0]
            ):
                continue
            if b1.intersects(b2, padding=padding):
                collisions.append((b1, b2))
    return collisions


def adjust_positions_to_avoid_collisions(
    pfd: Flowsheet,
    max_iterations: int = 15,
    padding: float = 1.0,
    verbose: bool = False,
) -> list[str]:
    """Iteratively checks boundary boxes of graphical components and adjusts positions to avoid collisions.

    Adjustments include:
      - Changing label positions (top, bottom, left, right) for valves, pumps, and sampling points.
      - Adjusting stream label offsets along/perpendicular to stream lines.
      - Shifting instrument balloon centers (staggering vertical/horizontal offsets from process lines).
      - Nudging component symbols along pipe lines if overlapping with adjacent units or components.
      - Adjusting unit operation label offsets.

    Args:
        pfd: The Flowsheet instance.
        max_iterations: Maximum relaxation iterations.
        padding: Safety clearance margin in pixels.
        verbose: If True, prints iteration and adjustment details.

    Returns:
        List of adjustment log descriptions performed.
    """
    history = []

    for iteration in range(max_iterations):
        collisions = check_collisions(pfd, padding=padding)
        if verbose:
            print(f"[Collision Check] Iteration {iteration}: {len(collisions)} collisions found")
        if not collisions:
            if verbose:
                print(
                    f"[Collision Check] All collisions successfully resolved in {iteration} iterations."
                )
            break

        adjusted_this_round = set()

        for b1, b2 in collisions:
            # 1. Unit label collision
            unit_lbl = b1 if b1.kind == "unit_label" else (b2 if b2.kind == "unit_label" else None)
            if unit_lbl and unit_lbl.name not in adjusted_this_round:
                u = unit_lbl.obj
                cur_off = list(u.textOffset)
                best_off = cur_off
                min_c = 999
                for dx, dy in [(0, -25), (0, 25), (0, -40), (0, 40), (-25, 0), (25, 0)]:
                    test_off = (cur_off[0] + dx, cur_off[1] + dy)
                    u.textOffset = test_off
                    t_boxes = get_bounding_boxes(pfd)
                    target = [bx for bx in t_boxes if bx.name == unit_lbl.name][0]
                    c = sum(
                        1
                        for ob in t_boxes
                        if ob.name.split(":")[0] != u.id and target.intersects(ob, padding=padding)
                    )
                    if c < min_c:
                        min_c = c
                        best_off = test_off
                u.textOffset = best_off
                adjusted_this_round.add(unit_lbl.name)
                history.append(f"Adjusted unit label {u.id} textOffset to {best_off}")
                continue

            # 2. Stream label collision
            stream_lbl = (
                b1 if b1.kind == "stream_label" else (b2 if b2.kind == "stream_label" else None)
            )
            if stream_lbl and stream_lbl.name not in adjusted_this_round:
                s = stream_lbl.obj
                cur_off = list(s.labelOffset)
                best_off = cur_off
                min_c = 999
                candidates = [
                    (0, -20),
                    (0, 20),
                    (25, 0),
                    (-25, 0),
                    (20, -15),
                    (20, 15),
                    (-20, -15),
                    (-20, 15),
                    (35, 0),
                    (-35, 0),
                    (0, -35),
                    (0, 35),
                ]
                for dx, dy in candidates:
                    test_off = (cur_off[0] + dx, cur_off[1] + dy)
                    s.labelOffset = test_off
                    t_boxes = get_bounding_boxes(pfd)
                    target = [bx for bx in t_boxes if bx.name == stream_lbl.name][0]
                    c = sum(
                        1
                        for ob in t_boxes
                        if ob.name.split(":")[0] != s.id and target.intersects(ob, padding=padding)
                    )
                    if c < min_c:
                        min_c = c
                        best_off = test_off
                s.labelOffset = best_off
                adjusted_this_round.add(stream_lbl.name)
                history.append(f"Adjusted stream {s.id} labelOffset to {best_off}")
                continue

            # 3. Valve / Pump / Sample Valve label collision
            lbl_box = None
            for b in (b1, b2):
                if b.kind in ("valve_label", "pump_label", "smp_label"):
                    lbl_box = b
                    break
            if lbl_box and lbl_box.name not in adjusted_this_round:
                obj = lbl_box.obj
                cur_pos = obj.label_pos
                best_pos = cur_pos
                min_c = 999
                for pos in ["top", "bottom", "left", "right"]:
                    obj.label_pos = pos
                    t_boxes = get_bounding_boxes(pfd)
                    target = [bx for bx in t_boxes if bx.name == lbl_box.name][0]
                    c = sum(
                        1
                        for ob in t_boxes
                        if ob.name.split(":")[0] != obj.id
                        and target.intersects(ob, padding=padding)
                    )
                    if c < min_c:
                        min_c = c
                        best_pos = pos
                        if c == 0:
                            break
                obj.label_pos = best_pos

                # If still colliding and object has a center position, shift center along pipe
                if min_c > 0 and hasattr(obj, "center"):
                    orig_c = obj.center
                    best_center = orig_c
                    for ddx, ddy in [(10, 0), (-10, 0), (20, 0), (-20, 0), (0, 10), (0, -10)]:
                        obj.center = (orig_c[0] + ddx, orig_c[1] + ddy)
                        for pos in ["top", "bottom", "left", "right"]:
                            obj.label_pos = pos
                            t_boxes = get_bounding_boxes(pfd)
                            target = [bx for bx in t_boxes if bx.name == lbl_box.name][0]
                            sym_targets = [
                                bx
                                for bx in t_boxes
                                if bx.name.startswith(obj.id) and bx.kind.endswith("symbol")
                            ]
                            sym_target = sym_targets[0] if sym_targets else None
                            c = sum(
                                1
                                for ob in t_boxes
                                if ob.name.split(":")[0] != obj.id
                                and (
                                    target.intersects(ob, padding=padding)
                                    or (sym_target and sym_target.intersects(ob, padding=padding))
                                )
                            )
                            if c < min_c:
                                min_c = c
                                best_center = obj.center
                                best_pos = pos
                                if c == 0:
                                    break
                        if min_c == 0:
                            break
                    obj.center = best_center
                    obj.label_pos = best_pos

                adjusted_this_round.add(lbl_box.name)
                history.append(f"Adjusted {obj.id} label_pos to {best_pos}")
                continue

            # 4. Instrument balloon collision
            inst_box = (
                b1 if b1.kind == "inst_balloon" else (b2 if b2.kind == "inst_balloon" else None)
            )
            if inst_box and inst_box.name not in adjusted_this_round:
                inst = inst_box.obj
                cx, cy = inst.center
                best_c = (cx, cy)
                min_c = 999
                candidates = [
                    (cx, cy - 30),
                    (cx, cy + 30),
                    (cx - 20, cy - 25),
                    (cx + 20, cy - 25),
                    (cx - 20, cy + 25),
                    (cx + 20, cy + 25),
                    (cx - 25, cy),
                    (cx + 25, cy),
                    (cx, cy - 40),
                    (cx, cy + 40),
                    (cx, cy - 50),
                    (cx, cy + 50),
                    (cx, cy - 60),
                    (cx, cy + 60),
                    (cx - 35, cy),
                    (cx + 35, cy),
                ]
                for ncx, ncy in candidates:
                    inst.center = (ncx, ncy)
                    t_boxes = get_bounding_boxes(pfd)
                    target = [bx for bx in t_boxes if bx.name == inst_box.name][0]
                    c = sum(
                        1
                        for ob in t_boxes
                        if ob.name.split(":")[0] != inst.id
                        and target.intersects(ob, padding=padding)
                    )
                    if c < min_c:
                        min_c = c
                        best_c = (ncx, ncy)
                        if c == 0:
                            break
                inst.center = best_c
                adjusted_this_round.add(inst_box.name)
                history.append(f"Adjusted instrument {inst.id} center to {best_c}")
                continue

            # 5. Component Symbol collision (e.g. pump/valve overlapping with another symbol or unit body)
            if b1.kind in ("pump_symbol", "valve_symbol") or b2.kind in (
                "pump_symbol",
                "valve_symbol",
            ):
                sym_box = b1 if b1.kind in ("pump_symbol", "valve_symbol") else b2
                other = b2 if sym_box is b1 else b1
                obj = sym_box.obj
                if hasattr(obj, "center") and sym_box.name not in adjusted_this_round:
                    cx, cy = obj.center
                    r = 12.0
                    candidates = [
                        (other.x2 + r + 2, cy),
                        (other.x1 - r - 2, cy),
                        (cx, other.y2 + r + 2),
                        (cx, other.y1 - r - 2),
                        (cx + 15, cy),
                        (cx - 15, cy),
                        (cx + 25, cy),
                        (cx - 25, cy),
                        (cx, cy + 15),
                        (cx, cy - 15),
                    ]
                    best_c = (cx, cy)
                    min_c = 999
                    for scx, scy in candidates:
                        obj.center = (scx, scy)
                        t_boxes = get_bounding_boxes(pfd)
                        target = [bx for bx in t_boxes if bx.name == sym_box.name][0]
                        c = sum(
                            1
                            for ob in t_boxes
                            if ob.name.split(":")[0] != obj.id
                            and target.intersects(ob, padding=padding)
                        )
                        if c < min_c:
                            min_c = c
                            best_c = (scx, scy)
                            if c == 0:
                                break
                    obj.center = best_c
                    adjusted_this_round.add(sym_box.name)
                    history.append(f"Adjusted {obj.id} center to {best_c}")

    return history


# Alias for intuitive discovery
check_and_adjust_collisions = adjust_positions_to_avoid_collisions


# ---------------------------------------------------------------------------
# Flowsheet Builder
# ---------------------------------------------------------------------------
def load_flowsheet_from_yaml(
    yaml_path: str,
    output_filename: str = "water_treatment_diagram_v2.svg",
    include_supporting: bool = False,
    adjust_collisions: bool = True,
    include_border: bool = True,
    include_title_block: bool = True,
    include_legend: bool = True,
    include_notes: bool = True,
    include_revisions: bool = True,
) -> Flowsheet:
    """Loads flowsheet components and streams from a YAML file and renders SVG.

    Args:
        yaml_path: Path to standardized flowsheet YAML file.
        output_filename: Target SVG output filename.
        include_supporting: If True, renders supporting P&ID components (pumps, valves,
                            sampling points, and instrumentation). If False, renders
                            major components only (clean PFD mode).
        adjust_collisions: If True, checks boundary boxes of graphical components
                           and labels, and automatically adjusts positions to prevent
                           overlapping and collisions.
        include_border: If True, renders ASME Y14.1 drawing border with neatline and zone grid.
        include_title_block: If True, renders standard ASME Y14.1 title block using YAML metadata.
        include_legend: If True, renders flowsheet and P&ID symbology legend.
        include_notes: If True, renders general process notes block.
        include_revisions: If True, renders ASME revision table at upper right border.
    """
    with open(yaml_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    meta = spec.get("metadata", {})
    pfd = Flowsheet(
        id=meta.get("id", "WATER_TREATMENT_V2"),
        name=meta.get("name", "Detailed Process Flow Diagram"),
        description=meta.get("description", ""),
    )

    components_cfg = spec.get("components", {})
    all_units = []

    # 1. Physical Equipment
    for eq in components_cfg.get("equipment", []):
        internals = [_create_internal(i) for i in eq.get("internals", [])]
        unit = Vessel(
            id=eq["id"],
            name=eq.get("name", eq["id"]),
            position=tuple(eq["position"]),
            size=tuple(eq["size"]),
            description=eq.get("description", ""),
            capLength=eq.get("cap_length", 15),
            internals=internals,
            angle=0,
        )

        for p in eq.get("ports", []):
            unit.ports[p["id"]] = Port(
                p["id"],
                unit,
                tuple(p["position"]),
                tuple(p["normal"]),
                intent=p.get("intent", "in"),
            )

        if "rotation" in eq:
            unit.rotate(eq["rotation"])

        if "text_anchor" in eq:
            ta = eq["text_anchor"]
            h = ALIGNMENT_MAP_H.get(ta.get("horizontal"), HorizontalLabelAlignment.Center)
            v = ALIGNMENT_MAP_V.get(ta.get("vertical"), VerticalLabelAlignment.Bottom)
            offset = tuple(ta.get("offset", (0, 0)))
            unit.setTextAnchor(h, v, offset)

        all_units.append(unit)

    # 2. Stream Flags (Boundaries)
    for flag in components_cfg.get("stream_flags", []):
        flag_unit = StreamFlag(
            id=flag["id"],
            name=flag.get("name", flag["id"]),
            position=tuple(flag["position"]),
            size=tuple(flag["size"]),
            description=flag.get("description", ""),
        )

        if "rotation" in flag:
            flag_unit.rotate(flag["rotation"])

        if "text_anchor" in flag:
            ta = flag["text_anchor"]
            h = ALIGNMENT_MAP_H.get(ta.get("horizontal"), HorizontalLabelAlignment.Center)
            v = ALIGNMENT_MAP_V.get(ta.get("vertical"), VerticalLabelAlignment.Bottom)
            offset = tuple(ta.get("offset", (0, 0)))
            flag_unit.setTextAnchor(h, v, offset)

        all_units.append(flag_unit)

    pfd.addUnits(all_units)

    # 3. Stream Connections
    for s in spec.get("streams", []):
        sid = s["id"]
        from_unit = pfd.unitOperations[s["from"]["unit"]]
        from_port = from_unit[s["from"]["port"]]
        to_unit = pfd.unitOperations[s["to"]["unit"]]
        to_port = to_unit[s["to"]["port"]]
        pfd.connect(sid, from_port, to_port)

        if "manual_routing" in s:
            pfd.streams[sid].manualRouting = [tuple(pt) for pt in s["manual_routing"]]
        if "label_offset" in s:
            pfd.streams[sid].labelOffset = tuple(s["label_offset"])

    # 4. Optional Supporting P&ID Components (Pumps, Valves, Sampling, Sensors)
    if include_supporting:
        annotations = []

        # Pumps
        for p in components_cfg.get("pumps", []):
            layout = p.get("layout", {})
            if "center" in layout:
                annotations.append(
                    PidPump(
                        pid=p["id"],
                        center=tuple(layout["center"]),
                        orientation=layout.get("orientation", "right"),
                        label_pos=layout.get("label_pos", "bottom"),
                    )
                )

        # Valves
        for v in components_cfg.get("valves", []):
            layout = v.get("layout", {})
            vtype = v.get("type", "Valve")
            if vtype == "SamplingValve" and "tap" in layout and "branch" in layout:
                annotations.append(
                    PidSampleValve(
                        sid=v["id"],
                        tap=tuple(layout["tap"]),
                        branch=tuple(layout["branch"]),
                        label_pos=layout.get("label_pos", "bottom"),
                    )
                )
            elif "center" in layout:
                annotations.append(
                    PidValve(
                        vid=v["id"],
                        center=tuple(layout["center"]),
                        valve_type=vtype,
                        orientation=layout.get("orientation", "horizontal"),
                        label_pos=layout.get("label_pos", "bottom"),
                    )
                )

        # Instrumentation & Sensors
        for inst in components_cfg.get("instrumentation", []):
            layout = inst.get("layout", {})
            if "center" in layout and "tap" in layout:
                annotations.append(
                    PidInstrument(
                        tag=inst["tag"],
                        center=tuple(layout["center"]),
                        tap=tuple(layout["tap"]),
                    )
                )

        pfd.addAnnotations(annotations)

    # 5. Collision Detection & Position Adjustment
    if adjust_collisions:
        adjust_positions_to_avoid_collisions(pfd, verbose=False)

    # 6. Render Diagram
    ctx = SvgContext(output_filename)

    border = DrawingBorder()
    if include_border:
        border.draw(ctx)

    if include_revisions:
        rev_block = RevisionBlock(revisions=meta.get("revisions", []))
        rev_block.draw(ctx)

    if include_legend:
        legend = DrawingLegend()
        legend.draw(ctx)

    if include_title_block:
        title_block = TitleBlock(meta)
        title_block.draw(ctx)

    if include_notes:
        notes_block = GeneralNotes(notes=meta.get("notes", []))
        notes_block.draw(ctx)

    pfd.draw(ctx)

    if include_border:
        margin = 20
        ox0, oy0 = border.outer_rect[0]
        ox1, oy1 = border.outer_rect[1]
        ctx.bounds = [ox0 - margin, oy0 - margin, ox1 + margin, oy1 + margin]

    ctx.render()

    abs_path = os.path.abspath(output_filename)
    mode_str = (
        "Full P&ID (with supporting components)"
        if include_supporting
        else "PFD (major components only)"
    )
    frame_details = []
    if include_border:
        frame_details.append("ASME Y14.1 Border")
    if include_title_block:
        frame_details.append("Title Block")
    if include_legend:
        frame_details.append("Legend")
    frame_str = f" with {', '.join(frame_details)}" if frame_details else ""
    print(f"[OK] Diagram successfully rendered [{mode_str}{frame_str}] to: {abs_path}")
    return pfd


def build_flowsheet(
    output_filename: str = "water_treatment_diagram_v2.svg",
    yaml_path: str | None = None,
    include_supporting: bool = False,
    adjust_collisions: bool = True,
    include_border: bool = True,
    include_title_block: bool = True,
    include_legend: bool = True,
    include_notes: bool = True,
    include_revisions: bool = True,
) -> Flowsheet:
    """Builds and renders the flowsheet from standardized YAML specification."""
    if yaml_path is None:
        yaml_path = os.path.join(os.path.dirname(__file__), "water_treatment_flowsheet_v2.yaml")
    return load_flowsheet_from_yaml(
        yaml_path,
        output_filename=output_filename,
        include_supporting=include_supporting,
        adjust_collisions=adjust_collisions,
        include_border=include_border,
        include_title_block=include_title_block,
        include_legend=include_legend,
        include_notes=include_notes,
        include_revisions=include_revisions,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Render Water Treatment Process Flow / P&ID Diagram"
    )
    parser.add_argument(
        "--pid",
        "--full",
        dest="pid",
        action="store_true",
        help="Render full P&ID diagram including pumps, valves, sampling points, and sensors",
    )
    parser.add_argument(
        "--no-collision-adjust",
        dest="adjust_collisions",
        action="store_false",
        default=True,
        help="Disable automatic boundary box collision checking and position adjustment",
    )
    parser.add_argument(
        "--no-border",
        dest="include_border",
        action="store_false",
        default=True,
        help="Disable drawing border and zone coordinate frame",
    )
    parser.add_argument(
        "--no-title-block",
        dest="include_title_block",
        action="store_false",
        default=True,
        help="Disable ANSI/ASME Y14.1 title block",
    )
    parser.add_argument(
        "--no-legend",
        dest="include_legend",
        action="store_false",
        default=True,
        help="Disable flowsheet and P&ID symbology legend",
    )
    parser.add_argument(
        "--no-notes",
        dest="include_notes",
        action="store_false",
        default=True,
        help="Disable general process notes block",
    )
    parser.add_argument(
        "--no-revisions",
        dest="include_revisions",
        action="store_false",
        default=True,
        help="Disable revision history table",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output SVG filename (defaults to water_treatment_diagram_v2.svg or water_treatment_diagram_v2_pid.svg)",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help="Path to YAML configuration file (defaults to water_treatment_flowsheet_v2.yaml)",
    )

    args = parser.parse_args()

    default_output = (
        "water_treatment_diagram_v2_pid.svg" if args.pid else "water_treatment_diagram_v2.svg"
    )
    out_file = args.output or default_output

    pfd = build_flowsheet(
        output_filename=out_file,
        yaml_path=args.config,
        include_supporting=args.pid,
        adjust_collisions=args.adjust_collisions,
        include_border=args.include_border,
        include_title_block=args.include_title_block,
        include_legend=args.include_legend,
        include_notes=args.include_notes,
        include_revisions=args.include_revisions,
    )

    remaining_colls = check_collisions(pfd, padding=1.0)
    if remaining_colls:
        print(
            f"\n[Layout Check] {len(remaining_colls)} potential component/label overlap(s) detected."
        )
    else:
        print("\n[Layout Check] 0 component/label collisions detected (clean layout).")

    yaml_file = args.config or os.path.join(
        os.path.dirname(__file__), "water_treatment_flowsheet_v2.yaml"
    )
    with open(yaml_file, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    meta = spec.get("metadata", {})
    print("\n--- Drawing Title Block (ANSI/ASME Y14.1) ---")
    print(f"  Title:      {meta.get('title', meta.get('name', ''))}")
    print(
        f"  Dwg No:     {meta.get('drawing_number', meta.get('id', ''))} (Rev {meta.get('revision', 'A')})"
    )
    print(
        f"  Size/Scale: Size {meta.get('sheet_size', 'D')} | Scale {meta.get('scale', 'NTS')} | Sheet {meta.get('sheet', '1 OF 1')}"
    )
    print(
        f"  Company:    {meta.get('organization', meta.get('company', ''))} [CAGE: {meta.get('cage_code', '')}]"
    )
    print(
        f"  Approvals:  Drawn: {meta.get('drawn_by', '')} | Checked: {meta.get('checked_by', '')} | Approved: {meta.get('approved_by', '')}"
    )
    print(f"  Status:     {meta.get('status', 'ISSUED FOR CONSTRUCTION')}")

    print("\n--- Stream Table & Associated Line Components ---")
    for s in spec.get("streams", []):
        sid = s["id"]
        desc = s.get("description", s.get("name", ""))
        assoc = s.get("associated_components", {})
        pumps = assoc.get("pumps", [])
        valves = assoc.get("valves", [])
        instruments = assoc.get("instruments", [])
        print(f"  {sid}: {desc}")
        if pumps or valves or instruments:
            details = []
            if pumps:
                details.append(f"Pumps: {', '.join(pumps)}")
            if valves:
                details.append(f"Valves: {', '.join(valves)}")
            if instruments:
                details.append(f"Sensors: {', '.join(instruments)}")
            print(f"       -> {' | '.join(details)}")

    pumps_cfg = spec.get("components", {}).get("pumps", [])
    valves_cfg = spec.get("components", {}).get("valves", [])
    inst_cfg = spec.get("components", {}).get("instrumentation", [])

    print("\n--- P&ID Components Inventory ---")
    print(f"  Pumps ({len(pumps_cfg)}): {', '.join(p['id'] for p in pumps_cfg)}")
    print(
        f"  Valves ({len(valves_cfg)}): {', '.join(v['id'] for v in valves_cfg if not v['id'].startswith('V-SMP'))}"
    )
    print(
        f"  Sampling Valves ({len([v for v in valves_cfg if v['id'].startswith('V-SMP')])}): {', '.join(v['id'] for v in valves_cfg if v['id'].startswith('V-SMP'))}"
    )
    print(f"  Instrumentation ({len(inst_cfg)}): {', '.join(i['tag'] for i in inst_cfg)}")


if __name__ == "__main__":
    main()
