from __future__ import annotations

import math
import re
from typing import Any

from ..instruments.tag import parse_isa_tag

ISA_51_TAG_DESCRIPTIONS: dict[str, str] = {
    "FIT": "Flow Indicating Transmitter",
    "FT": "Flow Transmitter",
    "FE": "Flow Element",
    "FCV": "Flow Control Valve",
    "FIC": "Flow Indicating Controller",
    "FI": "Flow Indicator",
    "LIT": "Level Indicating Transmitter",
    "LT": "Level Transmitter",
    "LIC": "Level Indicating Controller",
    "LCV": "Level Control Valve",
    "LI": "Level Indicator",
    "LG": "Level Glass / Gauge",
    "PIT": "Pressure Indicating Transmitter",
    "PT": "Pressure Transmitter",
    "PIC": "Pressure Indicating Controller",
    "PCV": "Pressure Control Valve",
    "PI": "Pressure Indicator",
    "PG": "Pressure Gauge",
    "PSV": "Pressure Safety Valve",
    "PDIT": "Diff. Pressure Transmitter",
    "PDT": "Differential Pressure Transmitter",
    "PDIC": "Diff. Pressure Controller",
    "PDI": "Differential Pressure Indicator",
    "AIT": "Analytical Indicating Transmitter",
    "AT": "Analytical Transmitter",
    "AIC": "Analytical Indicating Controller",
    "AI": "Analytical Indicator",
    "TT": "Temperature Transmitter",
    "TIT": "Temperature Indicating Transmitter",
    "TE": "Temperature Element",
    "TIC": "Temperature Indicating Controller",
    "TCV": "Temperature Control Valve",
    "TI": "Temperature Indicator",
    "TW": "Thermowell",
    "ST": "Speed Transmitter",
    "VT": "Vibration Transmitter",
    "ZT": "Position Transmitter",
    "ZIC": "Position Indicating Controller",
}


def _format_id_list(ids: list[str]) -> str:
    """Format a list of component IDs into a concise string for legend labels.

    Examples:
        [] -> ""
        ["P-101"] -> "(P-101)"
        ["P-102", "P-105"] -> "(P-102, P-105)"
        ["CKV-101", "CKV-102", "CKV-103"] -> "(CKV-101 .. CKV-103)"
        ["P-101", "P-103", "P-106", "P-107"] -> "(P-101, P-103, P-106, P-107)"
        ["V-SMP-01", "V-SMP-02", "V-SMP-03", "V-SMP-06"] -> "(V-SMP-01 .. V-SMP-06)"
    """
    if not ids:
        return ""
    if len(ids) == 1:
        return f"({ids[0]})"
    if len(ids) == 2:
        return f"({ids[0]}, {ids[1]})"

    # Check for integer suffix
    parsed: list[tuple[str, int] | None] = []
    for item in ids:
        m = re.match(r"^(.*?)(\d+)$", item)
        if m:
            parsed.append((m.group(1), int(m.group(2))))
        else:
            parsed.append(None)

    # If all share the exact same prefix
    if all(p is not None for p in parsed):
        first = parsed[0]
        assert first is not None
        prefix0 = first[0]
        if all(p[0] == prefix0 for p in parsed if p is not None):
            nums = [p[1] for p in parsed if p is not None]
            # Strictly consecutive sequence: (e.g. CKV-101, CKV-102, CKV-103)
            if nums == list(range(nums[0], nums[0] + len(nums))):
                return f"({ids[0]} .. {ids[-1]})"
            # If monotonic and long total string length, summarize range to save space
            total_len = sum(len(x) for x in ids) + 2 * (len(ids) - 1)
            if total_len > 30 and nums == sorted(nums):
                return f"({ids[0]} .. {ids[-1]})"

    if len(ids) <= 4:
        return f"({', '.join(ids)})"

    return f"({ids[0]}, {ids[1]} .. {ids[-1]})"


def _draw_line_sample(ctx, x0: float, y: float, line_type: str = "process") -> None:
    if line_type == "process":
        ctx.line((x0 + 15, y), (x0 + 75, y), lineColor=(0, 0, 0, 255), lineSize=2.2)
    elif line_type == "recycle":
        ctx.line((x0 + 15, y), (x0 + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.5)
    elif line_type == "signal":
        ctx.line((x0 + 15, y), (x0 + 75, y), lineColor=(120, 120, 120, 255), lineSize=1.0)
    else:
        ctx.line((x0 + 15, y), (x0 + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.5)


def _draw_stream_flag_sample(ctx, x0: float, y: float, text: str = "FEED") -> None:
    flag_pts = [
        (x0 + 20, y - 7),
        (x0 + 60, y - 7),
        (x0 + 72, y),
        (x0 + 60, y + 7),
        (x0 + 20, y + 7),
    ]
    ctx.path(
        flag_pts,
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
        close=True,
    )
    ctx.text(
        (x0 + 43, y + 2.5),
        text=text,
        fontFamily="Arial",
        textColor=(0, 0, 0, 255),
        fontSize=5.5,
        textAnchor="middle",
    )


def _draw_pump_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw = 13.0
        r = 6.0
        ctx.line((cx - hw, y), (cx - r, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx, y - r), (cx, y - r - 4), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx, y - r - 4), (cx + hw, y - r - 4), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.circle(
            [(cx - r, y - r), (cx + r, y + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.1,
        )
    else:
        cx = x + 45.0
        ctx.line((x + 15, y), (cx - 7, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx, y - 7), (cx, y - 12), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx, y - 12), (x + 75, y - 12), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.circle(
            [(cx - 7, y - 7), (cx + 7, y + 7)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )


def _draw_progressive_cavity_pump_sample(
    ctx, x: float, y: float, compact: bool = False
) -> None:
    if compact:
        cx = x
        hw = 13.0
        ctx.line((cx - hw, y), (cx - 10.0, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx + 10.0, y), (cx + hw, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        casing = [
            (cx - 10.0, y - 3.5),
            (cx - 5.5, y - 3.5),
            (cx - 5.5, y - 5.0),
            (cx + 6.5, y - 5.0),
            (cx + 6.5, y - 3.0),
            (cx + 10.0, y - 3.0),
            (cx + 10.0, y + 3.0),
            (cx + 6.5, y + 3.0),
            (cx + 6.5, y + 5.0),
            (cx - 5.5, y + 5.0),
            (cx - 5.5, y + 3.5),
            (cx - 10.0, y + 3.5),
        ]
        ctx.path(
            casing,
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line(
            (cx - 10.0, y - 4.5), (cx - 10.0, y + 4.5), lineColor=(0, 0, 0, 255), lineSize=0.9
        )
        ctx.line(
            (cx + 10.0, y - 4.0), (cx + 10.0, y + 4.0), lineColor=(0, 0, 0, 255), lineSize=0.9
        )
        ctx.line((cx - 5.5, y - 5.0), (cx - 5.5, y + 5.0), lineColor=(0, 0, 0, 255), lineSize=0.8)
        ctx.line((cx + 6.5, y - 5.0), (cx + 6.5, y + 5.0), lineColor=(0, 0, 0, 255), lineSize=0.8)
        num_pts = 16
        stator_len = 12.0
        amp = 3.0
        rotor_pts = []
        for i in range(num_pts + 1):
            t = i / num_pts
            rx = (cx - 5.5) + t * stator_len
            ry = y + amp * math.sin(t * 2.0 * 2.0 * math.pi)
            rotor_pts.append((rx, ry))
        ctx.path(rotor_pts, None, lineColor=(0, 0, 0, 255), lineSize=0.9)
        ctx.line((cx - 10.0, y), (cx - 5.5, y), lineColor=(0, 0, 0, 255), lineSize=0.8)
    else:
        cx = x + 45.0
        ctx.line((x + 15, y), (cx - 16.0, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx + 16.0, y), (x + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        casing = [
            (cx - 16.0, y - 5.0),
            (cx - 9.0, y - 5.0),
            (cx - 9.0, y - 7.5),
            (cx + 10.0, y - 7.5),
            (cx + 10.0, y - 4.5),
            (cx + 16.0, y - 4.5),
            (cx + 16.0, y + 4.5),
            (cx + 10.0, y + 4.5),
            (cx + 10.0, y + 7.5),
            (cx - 9.0, y + 7.5),
            (cx - 9.0, y + 5.0),
            (cx - 16.0, y + 5.0),
        ]
        ctx.path(
            casing,
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.1,
            close=True,
        )
        ctx.line(
            (cx - 16.0, y - 6.5), (cx - 16.0, y + 6.5), lineColor=(0, 0, 0, 255), lineSize=1.1
        )
        ctx.line(
            (cx + 16.0, y - 5.5), (cx + 16.0, y + 5.5), lineColor=(0, 0, 0, 255), lineSize=1.1
        )
        ctx.line((cx - 9.0, y - 7.5), (cx - 9.0, y + 7.5), lineColor=(0, 0, 0, 255), lineSize=0.9)
        ctx.line((cx + 10.0, y - 7.5), (cx + 10.0, y + 7.5), lineColor=(0, 0, 0, 255), lineSize=0.9)
        num_pts = 24
        stator_len = 19.0
        amp = 4.5
        rotor_pts = []
        for i in range(num_pts + 1):
            t = i / num_pts
            rx = (cx - 9.0) + t * stator_len
            ry = y + amp * math.sin(t * 2.0 * 2.0 * math.pi)
            rotor_pts.append((rx, ry))
        ctx.path(rotor_pts, None, lineColor=(0, 0, 0, 255), lineSize=1.0)
        ctx.line((cx - 16.0, y), (cx - 9.0, y), lineColor=(0, 0, 0, 255), lineSize=1.0)


def _draw_peristaltic_pump_sample(
    ctx, x: float, y: float, compact: bool = False
) -> None:
    if compact:
        cx = x
        hw = 13.0
        r = 6.0
        ctx.line((cx - hw, y + 2.5), (cx - r + 1, y + 2.5), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx + r - 1, y - 2.5), (cx + hw, y - 2.5), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.circle(
            [(cx - r, y - r), (cx + r, y + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.1,
        )
        ctx.circle(
            [(cx - 2.8, y - 1.5), (cx - 0.8, y + 0.5)],
            fillColor=(0, 0, 0, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.5,
        )
        ctx.circle(
            [(cx + 0.8, y - 0.5), (cx + 2.8, y + 1.5)],
            fillColor=(0, 0, 0, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.5,
        )
    else:
        cx = x + 45.0
        r = 7.5
        ctx.line((x + 15, y + 3.0), (cx - r + 1, y + 3.0), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx + r - 1, y - 3.0), (x + 75, y - 3.0), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.circle(
            [(cx - r, y - r), (cx + r, y + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )
        ctx.circle(
            [(cx - 3.5, y - 2.0), (cx - 1.0, y + 0.5)],
            fillColor=(0, 0, 0, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.6,
        )
        ctx.circle(
            [(cx + 1.0, y - 0.5), (cx + 3.5, y + 2.0)],
            fillColor=(0, 0, 0, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.6,
        )


def _draw_reciprocating_pump_sample(
    ctx, x: float, y: float, compact: bool = False
) -> None:
    if compact:
        cx = x
        hw = 13.0
        ctx.line((cx - hw, y), (cx + hw, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.rect(
            [(cx - 4.5, y - 7.5), (cx + 4.5, y)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((cx, y - 7.5), (cx, y - 10.5), lineColor=(0, 0, 0, 255), lineSize=1.0)
    else:
        cx = x + 45.0
        ctx.line((x + 15, y), (x + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.rect(
            [(cx - 6.0, y - 10.0), (cx + 6.0, y)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.1,
        )
        ctx.line((cx, y - 10.0), (cx, y - 14.0), lineColor=(0, 0, 0, 255), lineSize=1.1)


def _draw_compressor_sample(
    ctx, x: float, y: float, compact: bool = False
) -> None:
    if compact:
        cx = x
        hw = 13.0
        r = 6.0
        ctx.line((cx - hw, y), (cx - r, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx + r, y), (cx + hw, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.circle(
            [(cx - r, y - r), (cx + r, y + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.1,
        )
        ctx.line(
            (cx - 3.5, y - 4.5), (cx + 4.5, y - 1.5), lineColor=(0, 0, 0, 255), lineSize=1.0
        )
        ctx.line(
            (cx - 3.5, y + 4.5), (cx + 4.5, y + 1.5), lineColor=(0, 0, 0, 255), lineSize=1.0
        )
    else:
        cx = x + 45.0
        r = 7.5
        ctx.line((x + 15, y), (cx - r, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx + r, y), (x + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.circle(
            [(cx - r, y - r), (cx + r, y + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )
        ctx.line(
            (cx - 4.5, y - 5.5), (cx + 5.5, y - 2.0), lineColor=(0, 0, 0, 255), lineSize=1.1
        )
        ctx.line(
            (cx - 4.5, y + 5.5), (cx + 5.5, y + 2.0), lineColor=(0, 0, 0, 255), lineSize=1.1
        )


def _draw_blower_sample(
    ctx, x: float, y: float, compact: bool = False
) -> None:
    if compact:
        cx = x
        hw = 13.0
        r = 6.0
        ctx.line((cx - hw, y), (cx - r, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx, y - r), (cx, y - r - 4), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx, y - r - 4), (cx + hw, y - r - 4), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.circle(
            [(cx - r, y - r), (cx + r, y + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.1,
        )
    else:
        _draw_pump_sample(ctx, x, y, compact=False)


def _draw_control_valve_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw = 13.0
        vw, vh = 6.5, 4.0
        ctx.line((cx - hw, y), (cx + hw, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.path(
            [(cx - vw, y - vh), (cx + vw, y + vh), (cx + vw, y - vh), (cx - vw, y + vh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line((cx, y - vh), (cx, y - vh - 4.0), lineColor=(0, 0, 0, 255), lineSize=1.0)
        ctx.path(
            [(cx - 4.5, y - vh - 4.0), (cx + 4.5, y - vh - 4.0), (cx, y - vh - 7.5)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
    else:
        cx = x + 45.0
        ctx.line((x + 15, y), (x + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx - 8, y - 5),
                (cx + 8, y + 5),
                (cx + 8, y - 5),
                (cx - 8, y + 5),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line((cx, y - 5), (cx, y - 11), lineColor=(0, 0, 0, 255), lineSize=1.0)
        ctx.path(
            [(cx - 6, y - 11), (cx + 6, y - 11), (cx, y - 15)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )


def _draw_check_valve_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw = 13.0
        vw, vh = 6.5, 4.0
        ctx.line((cx - hw, y), (cx + hw, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.path(
            [(cx - vw, y - vh), (cx + vw, y + vh), (cx + vw, y - vh), (cx - vw, y + vh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line((cx - 2.5, y - 2.5), (cx + 2.5, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx - 2.5, y + 2.5), (cx + 2.5, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
    else:
        cx = x + 45.0
        ctx.line((x + 15, y), (x + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx - 8, y - 5),
                (cx + 8, y + 5),
                (cx + 8, y - 5),
                (cx - 8, y + 5),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line((cx - 3, y - 3), (cx + 3, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx - 3, y + 3), (cx + 3, y), lineColor=(0, 0, 0, 255), lineSize=1.2)


def _draw_relief_valve_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw = 13.0
        vw, vh = 4.0, 6.0
        ctx.line((cx - hw, y), (cx, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx, y), (cx, y + 9), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.path(
            [(cx - vw, y - vh), (cx + vw, y + vh), (cx - vw, y + vh), (cx + vw, y - vh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line((cx, y - vh), (cx, y - vh - 3), lineColor=(0, 0, 0, 255), lineSize=1.0)
        ctx.rectangle(
            [(cx - 2.5, y - vh - 6), (cx + 2.5, y - vh - 3)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=0.9,
        )
    else:
        cx = x + 45.0
        ctx.line((x + 15, y), (cx, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx, y), (cx, y + 12), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx - 5, y - 8),
                (cx + 5, y + 8),
                (cx - 5, y + 8),
                (cx + 5, y - 8),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
        ctx.line((cx, y - 8), (cx, y - 12), lineColor=(0, 0, 0, 255), lineSize=1.0)
        ctx.rectangle(
            [(cx - 3, y - 16), (cx + 3, y - 12)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )


def _draw_sampling_valve_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw = 13.0
        vw, vh = 3.5, 2.5
        y_run = y - 5.0
        ctx.line((cx - hw, y_run), (cx + hw, y_run), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.line((cx, y_run), (cx, y + 6), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.path(
            [(cx - vw, y - vh), (cx + vw, y + vh), (cx + vw, y - vh), (cx - vw, y + vh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
    else:
        cx = x + 45.0
        ctx.line((x + 15, y - 8), (x + 75, y - 8), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.line((cx, y - 8), (cx, y + 8), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx - 4, y - 3),
                (cx + 4, y + 3),
                (cx + 4, y - 3),
                (cx - 4, y + 3),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )


def _draw_isolation_valve_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw = 13.0
        vw, vh = 6.5, 4.0
        ctx.line((cx - hw, y), (cx + hw, y), lineColor=(0, 0, 0, 255), lineSize=1.1)
        ctx.path(
            [(cx - vw, y - vh), (cx + vw, y + vh), (cx + vw, y - vh), (cx - vw, y + vh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )
    else:
        cx = x + 45.0
        ctx.line((x + 15, y), (x + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
        ctx.path(
            [
                (cx - 8, y - 5),
                (cx + 8, y + 5),
                (cx + 8, y - 5),
                (cx - 8, y + 5),
            ],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
            close=True,
        )


def _draw_balloon_sample(
    ctx, x: float, y: float, tag_text: str = "FIT", compact: bool = False
) -> None:
    if compact:
        cx = x
        r = 7.5
        ctx.line((cx - 12, y + 9), (cx, y), lineColor=(120, 120, 120, 255), lineSize=1.0)
        ctx.circle(
            [(cx - r, y - r), (cx + r, y + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.1,
        )
        ctx.text(
            (cx, y + 2.0),
            text=tag_text,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=5.0,
            textAnchor="middle",
        )
    else:
        cx = x + 45.0
        ctx.line((x + 20, y + 12), (cx, y), lineColor=(120, 120, 120, 255), lineSize=1.0)
        ctx.circle(
            [(cx - 9, y - 9), (cx + 9, y + 9)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.2,
        )
        ctx.text(
            (cx, y + 2.5),
            text=tag_text,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.0,
            textAnchor="middle",
        )


def _draw_mixer_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw, hh = 13.0, 8.0
        ctx.rectangle(
            [(cx - hw, y - hh), (cx + hw, y + hh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((cx, y - hh), (cx, y + 4.0), lineColor=(0, 0, 0, 255), lineSize=0.9)
        ctx.line((cx - 5, y + 4.0), (cx + 5, y + 4.0), lineColor=(0, 0, 0, 255), lineSize=1.1)
    else:
        cx = x + 45.0
        ctx.rectangle(
            [(x + 25, y - 12), (x + 65, y + 12)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((cx, y - 12), (cx, y + 6), lineColor=(0, 0, 0, 255), lineSize=1.0)
        ctx.line((cx - 8, y + 6), (cx + 8, y + 6), lineColor=(0, 0, 0, 255), lineSize=1.2)


def _draw_daf_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw, hh = 14.0, 6.5
        ctx.rectangle(
            [(cx - hw, y - hh), (cx + hw, y + hh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.text(
            (cx, y + 2.0),
            text="DAF",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=4.5,
            textAnchor="middle",
        )
    else:
        cx = x + 45.0
        ctx.rectangle(
            [(x + 20, y - 8), (x + 70, y + 8)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.text(
            (cx, y + 2.5),
            text="DAF",
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="middle",
        )


def _draw_membrane_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw, hh = 14.0, 6.5
        ctx.rectangle(
            [(cx - hw, y - hh), (cx + hw, y + hh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        for tx in [cx - 7, cx, cx + 7]:
            ctx.line((tx, y - hh), (tx, y + hh), lineColor=(150, 150, 150, 255), lineSize=0.6)
    else:
        ctx.rectangle(
            [(x + 20, y - 8), (x + 70, y + 8)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        for tx in [x + 32, x + 45, x + 58]:
            ctx.line((tx, y - 8), (tx, y + 8), lineColor=(150, 150, 150, 255), lineSize=0.7)


def _draw_vessel_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw, hh = 8.0, 8.5
        ctx.rectangle(
            [(cx - hw, y - hh), (cx + hw, y + hh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((cx - hw, y - 4), (cx + hw, y - 4), lineColor=(180, 180, 180, 255), lineSize=0.6)
        ctx.line((cx - hw, y + 4), (cx + hw, y + 4), lineColor=(180, 180, 180, 255), lineSize=0.6)
    else:
        ctx.rectangle(
            [(x + 33, y - 12), (x + 57, y + 12)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((x + 33, y - 7), (x + 57, y - 7), lineColor=(180, 180, 180, 255), lineSize=0.6)
        ctx.line((x + 33, y + 7), (x + 57, y + 7), lineColor=(180, 180, 180, 255), lineSize=0.6)


def _draw_horizontal_vessel_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw, hh = 14.0, 6.5
        ctx.rectangle(
            [(cx - hw, y - hh), (cx + hw, y + hh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((cx - 8, y - hh), (cx - 8, y + hh), lineColor=(180, 180, 180, 255), lineSize=0.6)
        ctx.line((cx + 8, y - hh), (cx + 8, y + hh), lineColor=(180, 180, 180, 255), lineSize=0.6)
    else:
        ctx.rectangle(
            [(x + 20, y - 8), (x + 70, y + 8)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((x + 28, y - 8), (x + 28, y + 8), lineColor=(180, 180, 180, 255), lineSize=0.6)
        ctx.line((x + 62, y - 8), (x + 62, y + 8), lineColor=(180, 180, 180, 255), lineSize=0.6)


def _draw_jacketed_vessel_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        ctx.rectangle(
            [(cx - 13, y - 7.5), (cx + 13, y + 7.5)],
            fillColor=None,
            lineColor=(0, 0, 0, 255),
            lineSize=0.8,
        )
        ctx.rectangle(
            [(cx - 9, y - 9), (cx + 9, y + 9)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
    else:
        ctx.rectangle(
            [(x + 30, y - 10), (x + 60, y + 10)],
            fillColor=None,
            lineColor=(0, 0, 0, 255),
            lineSize=0.8,
        )
        ctx.rectangle(
            [(x + 34, y - 13), (x + 56, y + 13)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )


def _draw_exchanger_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        r = 7.0
        ctx.circle(
            [(cx - r, y - r), (cx + r, y + r)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((cx - r, y), (cx + r, y), lineColor=(0, 0, 0, 255), lineSize=0.8)
    else:
        cx = x + 45.0
        ctx.circle(
            [(cx - 10, y - 10), (cx + 10, y + 10)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.line((cx - 10, y), (cx + 10, y), lineColor=(0, 0, 0, 255), lineSize=0.8)


def _draw_distillation_sample(ctx, x: float, y: float, compact: bool = False) -> None:
    if compact:
        cx = x
        hw, hh = 7.0, 9.0
        ctx.rectangle(
            [(cx - hw, y - hh), (cx + hw, y + hh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        for ty in [y - 4, y, y + 4]:
            ctx.line((cx - hw, ty), (cx + hw, ty), lineColor=(150, 150, 150, 255), lineSize=0.6)
    else:
        ctx.rectangle(
            [(x + 35, y - 14), (x + 55, y + 14)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        for ty in [y - 7, y, y + 7]:
            ctx.line((x + 35, ty), (x + 55, ty), lineColor=(150, 150, 150, 255), lineSize=0.6)


def _draw_generic_equipment_sample(
    ctx, x: float, y: float, label: str = "UNIT", compact: bool = False
) -> None:
    if compact:
        cx = x
        hw, hh = 14.0, 7.0
        ctx.rectangle(
            [(cx - hw, y - hh), (cx + hw, y + hh)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.text(
            (cx, y + 2.0),
            text=label[:8],
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=4.5,
            textAnchor="middle",
        )
    else:
        cx = x + 45.0
        ctx.rectangle(
            [(x + 22, y - 9), (x + 68, y + 9)],
            fillColor=(255, 255, 255, 255),
            lineColor=(0, 0, 0, 255),
            lineSize=1.0,
        )
        ctx.text(
            (cx, y + 2.5),
            text=label[:8],
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.0,
            textAnchor="middle",
        )


class DrawingLegend:
    """Standard PFD & P&ID Legend detailing symbols, lines, valves, pumps,
    instruments, equipment, and process streams. Supports dynamic introspection
    of Flowsheet units/streams and customizable schema entries.
    """

    def __init__(
        self,
        rect: tuple[tuple[float, float], tuple[float, float]] = (
            (880.0, 58.0),
            (1260.0, 652.0),
        ),
        custom_entries: list[dict[str, Any]] | None = None,
        process_streams: list[Any] | None = None,
        two_column_sections: bool = True,
    ):
        self.id = "legend"
        self.rect = rect
        self.custom_entries: list[dict[str, Any]] = (
            list(custom_entries) if custom_entries is not None else []
        )
        self.process_streams: list[Any] = (
            list(process_streams) if process_streams is not None else []
        )
        self.two_column_sections = two_column_sections

    def draw(self, ctx, flowsheet=None) -> None:
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

        if flowsheet is None:
            self._draw_fallback(ctx, x0, y0, x1, y1)
        else:
            self._draw_dynamic(ctx, flowsheet, x0, y0, x1, y1)

        ctx.endGroup()

    def _draw_fallback(self, ctx, x0: float, y0: float, x1: float, y1: float) -> None:
        """Renders standard complete symbology template when flowsheet is None."""
        # Partition custom entries
        custom_sec1 = []
        custom_sec2 = []
        custom_sec3 = []
        custom_sec4 = []
        custom_sec5 = []
        for e in self.custom_entries:
            sec = self._normalize_section(e.get("section") if isinstance(e, dict) else 4)
            if sec == 1:
                custom_sec1.append(e)
            elif sec == 2:
                custom_sec2.append(e)
            elif sec == 3:
                custom_sec3.append(e)
            elif sec == 5:
                custom_sec5.append(e)
            else:
                custom_sec4.append(e)

        y_curr = y0 + 24.0

        # Section 1: Piping & Stream Lines
        y_curr = self._render_section_header(ctx, x0, y_curr, x1, "1. PIPING & STREAM LINES")
        _draw_line_sample(ctx, x0, y_curr, line_type="process")
        ctx.text(
            (x0 + 85, y_curr + 3.0),
            text="Major Process Stream (100 m^3/h)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )
        y_curr += 19.0

        _draw_line_sample(ctx, x0, y_curr, line_type="recycle")
        ctx.text(
            (x0 + 85, y_curr + 3.0),
            text="Recycle / Return Stream",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )
        y_curr += 19.0

        _draw_line_sample(ctx, x0, y_curr, line_type="signal")
        ctx.text(
            (x0 + 85, y_curr + 3.0),
            text="Instrument Process Tap / Leader",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )
        y_curr += 19.0

        _draw_stream_flag_sample(ctx, x0, y_curr, text="FEED")
        ctx.text(
            (x0 + 85, y_curr + 3.0),
            text="Stream Inflow / Outflow Boundary",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )
        y_curr += 20.0

        for entry in custom_sec1:
            if y_curr > y1 - 15.0:
                break
            self._draw_custom_item(ctx, entry, x0, y_curr, self._get_entry_label(entry))
            y_curr += 19.0

        y_curr += 6.0

        # Section 2: Valves & Motive Equipment
        y_curr = self._render_section_header(ctx, x0, y_curr, x1, "2. VALVES & MOTIVE EQUIPMENT")
        sec2_items = [
            ("pump", "Centrifugal Pump (P-101 .. P-104)", None),
            ("progressive_cavity_pump", "Progressive Cavity Pump (P-105, P-106)", None),
            ("control_valve", "Control Valve with Actuator (FCV, PCV)", None),
            ("check_valve", "Check / Non-Return Valve (CKV)", None),
            ("relief_valve", "Safety Relief Valve (PSV)", None),
            ("sampling_valve", "In-Line Sampling Valve (V-SMP)", None),
        ] + [("custom", self._get_entry_label(e), e) for e in custom_sec2]

        if self.two_column_sections and len(sec2_items) > 1:
            y_curr = self._render_two_column_section(
                ctx, x0, y_curr, x1, y1, sec2_items, category="valves"
            )
        else:
            for kind, label, entry in sec2_items:
                if y_curr > y1 - 15.0:
                    break
                if kind == "custom":
                    self._draw_custom_item(ctx, entry, x0, y_curr, label)
                else:
                    self._draw_valve_motive_symbol(ctx, kind, x0, y_curr, compact=False)
                    ctx.text(
                        (x0 + 85, y_curr + 3.0),
                        text=label,
                        fontFamily="Arial",
                        textColor=(0, 0, 0, 255),
                        fontSize=6.5,
                        textAnchor="start",
                    )
                y_curr += 24.0

        y_curr += 6.0

        # Section 3: ISA-5.1 Instrumentation
        y_curr = self._render_section_header(ctx, x0, y_curr, x1, "3. INSTRUMENTATION (ISA-5.1)")
        _draw_balloon_sample(ctx, x0, y_curr, tag_text="FIT", compact=False)
        ctx.text(
            (x0 + 85, y_curr + 3.0),
            text="Field-Mounted Instrument Balloon",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )
        y_curr += 20.0

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
        col_w = (x1 - x0) / 2.0
        for idx in range(max(len(tags_col1), len(tags_col2))):
            if y_curr > y1 - 15.0:
                break
            if idx < len(tags_col1):
                tag, desc = tags_col1[idx]
                ctx.text(
                    (x0 + 16, y_curr),
                    text=f"• {tag}:",
                    fontFamily="Arial",
                    textColor=(0, 0, 0, 255),
                    fontSize=6.0,
                    textAnchor="start",
                )
                ctx.text(
                    (x0 + 46, y_curr),
                    text=desc,
                    fontFamily="Arial",
                    textColor=(70, 70, 70, 255),
                    fontSize=5.5,
                    textAnchor="start",
                )
            if idx < len(tags_col2):
                tag, desc = tags_col2[idx]
                ctx.text(
                    (x0 + col_w + 8, y_curr),
                    text=f"• {tag}:",
                    fontFamily="Arial",
                    textColor=(0, 0, 0, 255),
                    fontSize=6.0,
                    textAnchor="start",
                )
                ctx.text(
                    (x0 + col_w + 40, y_curr),
                    text=desc,
                    fontFamily="Arial",
                    textColor=(70, 70, 70, 255),
                    fontSize=5.5,
                    textAnchor="start",
                )
            y_curr += 15.0

        for entry in custom_sec3:
            if y_curr > y1 - 15.0:
                break
            self._draw_custom_item(ctx, entry, x0, y_curr, self._get_entry_label(entry))
            y_curr += 18.0

        y_curr += 6.0

        # Section 4: Equipment Models
        y_curr = self._render_section_header(ctx, x0, y_curr, x1, "4. MAJOR EQUIPMENT ICONS")
        sec4_items = [
            ("mixer", "Continuous Stirred Tank Mixer (Mixer)", None),
            ("daf", "Flotation Separator (DAF)", None),
            ("membrane", "Tubular Reactor / Membrane (UV/US, NF)", None),
        ] + [("custom", self._get_entry_label(e), e) for e in custom_sec4]

        if self.two_column_sections and len(sec4_items) > 1:
            y_curr = self._render_two_column_section(
                ctx, x0, y_curr, x1, y1, sec4_items, category="equipment"
            )
        else:
            for kind, label, entry in sec4_items:
                if y_curr > y1 - 15.0:
                    break
                if kind == "custom":
                    self._draw_custom_item(ctx, entry, x0, y_curr, label)
                else:
                    self._draw_equipment_symbol(ctx, kind, x0, y_curr, label=label, compact=False)
                    ctx.text(
                        (x0 + 85, y_curr + 3.0),
                        text=label,
                        fontFamily="Arial",
                        textColor=(0, 0, 0, 255),
                        fontSize=6.5,
                        textAnchor="start",
                    )
                y_curr += 24.0

        y_curr += 6.0

        # Section 5: Process Streams (if provided)
        if self.process_streams or custom_sec5:
            y_curr = self._render_process_streams_section(
                ctx, x0, y_curr, x1, y1, self.process_streams, custom_sec5, flowsheet=None
            )

    def _draw_dynamic(self, ctx, flowsheet, x0: float, y0: float, x1: float, y1: float) -> None:
        """Renders dynamic legend by introspecting flowsheet units, streams, and instruments."""
        # Merge custom entries
        all_custom = list(self.custom_entries)
        if hasattr(flowsheet, "settings") and isinstance(flowsheet.settings, dict):
            df_settings = flowsheet.settings.get("drawing_frame", {})
            if isinstance(df_settings, dict):
                from_settings = df_settings.get("custom_legend_entries", [])
                if from_settings and not all_custom:
                    all_custom.extend(from_settings)

        # Partition custom entries by section index (1..5)
        custom_sec1 = []
        custom_sec2 = []
        custom_sec3 = []
        custom_sec4 = []
        custom_sec5 = []

        for e in all_custom:
            sec_target = self._normalize_section(e.get("section") if isinstance(e, dict) else 4)
            if sec_target == 1:
                custom_sec1.append(e)
            elif sec_target == 2:
                custom_sec2.append(e)
            elif sec_target == 3:
                custom_sec3.append(e)
            elif sec_target == 5:
                custom_sec5.append(e)
            else:
                custom_sec4.append(e)

        # Check for process streams
        all_process_streams = list(self.process_streams)
        if hasattr(flowsheet, "settings") and isinstance(flowsheet.settings, dict):
            df_settings = flowsheet.settings.get("drawing_frame", {})
            if isinstance(df_settings, dict):
                from_settings = df_settings.get("process_streams", [])
                if from_settings and not all_process_streams:
                    all_process_streams.extend(from_settings)
            if not all_process_streams and "process_streams" in flowsheet.settings:
                from_settings = flowsheet.settings.get("process_streams", [])
                if from_settings:
                    all_process_streams.extend(from_settings)

        if not all_process_streams and hasattr(flowsheet, "metadata") and isinstance(
            flowsheet.metadata, dict
        ):
            from_meta = flowsheet.metadata.get("process_streams", [])
            if from_meta:
                all_process_streams.extend(from_meta)

        show_proc = False
        if hasattr(flowsheet, "settings") and isinstance(flowsheet.settings, dict):
            df_sett = flowsheet.settings.get("drawing_frame", {})
            if isinstance(df_sett, dict) and df_sett.get("show_process_streams"):
                show_proc = True
            elif flowsheet.settings.get("show_process_streams"):
                show_proc = True

        if not all_process_streams and show_proc and hasattr(flowsheet, "streams"):
            seen_ids = set()
            for s in flowsheet.streams.values():
                ltype = getattr(s, "line_type", "process")
                if ltype in ("process", "recycle") and s.id not in seen_ids:
                    seen_ids.add(s.id)
                    all_process_streams.append(s)

        units = (
            list(flowsheet.unitOperations.values()) if hasattr(flowsheet, "unitOperations") else []
        )
        streams = list(flowsheet.streams.values()) if hasattr(flowsheet, "streams") else []

        # ---------------- Section 1: Lines & Streams ----------------
        sec1_items: list[tuple[str, str]] = []  # (kind, label)
        sec1_items.append(("process", "Major Process Stream"))

        has_recycle = any(
            getattr(s, "line_type", "") == "recycle"
            or any(kw in s.id.lower() for kw in ("recycle", "return", "rec", "ret"))
            for s in streams
        )
        if not has_recycle and hasattr(flowsheet, "macro_graph"):
            mg_recycle = getattr(flowsheet.macro_graph, "recycle_streams", set())
            has_recycle = any(s.id in mg_recycle for s in streams)

        if has_recycle:
            sec1_items.append(("recycle", "Recycle / Return Stream"))

        signal_types = ("electric", "pneumatic", "digital", "capillary", "signal")
        has_signals = any(getattr(s, "line_type", "") in signal_types for s in streams) or any(
            getattr(u, "leader_line", None) is not None or u.__class__.__name__ == "Instrument"
            for u in units
        )
        if has_signals:
            sec1_items.append(("signal", "Instrument Process Tap / Leader"))

        has_stream_flags = any(
            u.__class__.__name__ == "StreamFlag" or "StreamFlag" in type(u).__name__ for u in units
        )
        if has_stream_flags:
            sec1_items.append(("flag", "Stream Inflow / Outflow Boundary"))

        # ---------------- Section 2: Valves & Motive Equipment ----------------
        sec2_items: list[tuple[str, str]] = []  # (kind, label)
        centrifugal_pumps: list[Any] = []
        cavity_pumps: list[Any] = []
        peristaltic_pumps: list[Any] = []
        reciprocating_pumps: list[Any] = []
        compressors: list[Any] = []
        blowers: list[Any] = []

        control_valves: list[Any] = []
        check_valves: list[Any] = []
        safety_valves: list[Any] = []
        sampling_valves: list[Any] = []
        other_valves: dict[str, list[Any]] = {}

        for u in units:
            cname = u.__class__.__name__
            cname_lower = cname.lower()
            uid = u.id.upper()
            uname = getattr(u, "name", "").lower()
            udesc = getattr(u, "description", "").lower()

            is_pump_id = (
                uid.startswith(("P-", "P_"))
                or (len(uid) >= 2 and uid[0] == "P" and uid[1:].isdigit())
            )

            # Motive equipment: progressive cavity / screw pump
            if (
                cname == "ProgressiveCavityPump"
                or "progressivecavity" in cname_lower
                or "screw" in cname_lower
                or "cavity" in cname_lower
                or (
                    (
                        "screw" in uname
                        or "cavity" in uname
                        or "screw" in udesc
                        or "cavity" in udesc
                    )
                    and ("pump" in cname_lower or is_pump_id)
                )
            ):
                cavity_pumps.append(u)
            # Motive equipment: peristaltic / hose pump
            elif (
                cname == "PeristalticPump"
                or "peristaltic" in cname_lower
                or "hose" in cname_lower
                or (
                    ("peristaltic" in uname or "hose" in uname)
                    and ("pump" in cname_lower or is_pump_id)
                )
            ):
                peristaltic_pumps.append(u)
            # Motive equipment: reciprocating / piston pump
            elif (
                cname == "ReciprocatingPump"
                or "reciprocating" in cname_lower
                or "piston" in cname_lower
                or "plunger" in cname_lower
                or (
                    ("reciprocating" in uname or "piston" in uname or "plunger" in uname)
                    and ("pump" in cname_lower or is_pump_id)
                )
            ):
                reciprocating_pumps.append(u)
            # Motive equipment: compressor
            elif (
                cname == "Compressor"
                or "compressor" in cname_lower
                or uid.startswith(("C-", "K-"))
            ):
                compressors.append(u)
            # Motive equipment: blower / fan
            elif (
                cname == "Blower"
                or "blower" in cname_lower
                or "fan" in cname_lower
                or uid.startswith("B-")
            ):
                blowers.append(u)
            # Motive equipment: centrifugal / general pump
            elif (
                cname == "Pump"
                or "pump" in cname_lower
                or is_pump_id
            ):
                centrifugal_pumps.append(u)

            # Valves: control valve
            elif (
                cname == "ControlValve"
                or (hasattr(u, "actuator") and u.actuator is not None)
                or uid.startswith(("FCV", "PCV", "TCV", "LCV"))
                or "control" in uname
            ):
                control_valves.append(u)
            # Valves: check valve
            elif cname == "CheckValve" or uid.startswith("CKV") or "check" in uname:
                check_valves.append(u)
            # Valves: safety relief valve
            elif (
                cname in ("SafetyReliefValve", "RuptureDisc")
                or uid.startswith(("PSV", "PRV", "SRV"))
                or "safety" in uname
                or "relief" in uname
            ):
                safety_valves.append(u)
            # Valves: sampling valve
            elif (
                cname in ("GrabSamplingTee", "NeedleValve")
                or uid.startswith(("SMP", "V-SMP", "SP"))
                or "sample" in uname
                or "sampling" in uname
            ):
                sampling_valves.append(u)
            # Valves: other process valves
            elif "valve" in cname_lower or uid.startswith(("V-", "V_")):
                other_valves.setdefault(cname, []).append(u)

        all_motive = (
            centrifugal_pumps
            + cavity_pumps
            + peristaltic_pumps
            + reciprocating_pumps
            + compressors
            + blowers
        )
        all_valves = (
            control_valves
            + check_valves
            + safety_valves
            + sampling_valves
            + [u for vlist in other_valves.values() for u in vlist]
        )

        if centrifugal_pumps:
            id_str = _format_id_list([p.id for p in centrifugal_pumps])
            lbl = f"Centrifugal Pump {id_str}".strip()
            sec2_items.append(("pump", lbl))

        if cavity_pumps:
            id_str = _format_id_list([p.id for p in cavity_pumps])
            lbl = f"Progressive Cavity Pump {id_str}".strip()
            sec2_items.append(("progressive_cavity_pump", lbl))

        if peristaltic_pumps:
            id_str = _format_id_list([p.id for p in peristaltic_pumps])
            lbl = f"Peristaltic Pump {id_str}".strip()
            sec2_items.append(("peristaltic_pump", lbl))

        if reciprocating_pumps:
            id_str = _format_id_list([p.id for p in reciprocating_pumps])
            lbl = f"Reciprocating Pump {id_str}".strip()
            sec2_items.append(("reciprocating_pump", lbl))

        if compressors:
            id_str = _format_id_list([p.id for p in compressors])
            lbl = f"Compressor {id_str}".strip()
            sec2_items.append(("compressor", lbl))

        if blowers:
            id_str = _format_id_list([p.id for p in blowers])
            lbl = f"Blower / Fan {id_str}".strip()
            sec2_items.append(("blower", lbl))

        if control_valves:
            id_str = _format_id_list([v.id for v in control_valves])
            lbl = f"Control Valve with Actuator {id_str}".strip()
            sec2_items.append(("control_valve", lbl))

        if check_valves:
            id_str = _format_id_list([v.id for v in check_valves])
            lbl = f"Check / Non-Return Valve {id_str}".strip()
            sec2_items.append(("check_valve", lbl))

        if safety_valves:
            id_str = _format_id_list([v.id for v in safety_valves])
            lbl = f"Safety Relief Valve {id_str}".strip()
            sec2_items.append(("relief_valve", lbl))

        if sampling_valves:
            id_str = _format_id_list([v.id for v in sampling_valves])
            lbl = f"In-Line Sampling Valve {id_str}".strip()
            sec2_items.append(("sampling_valve", lbl))

        for vclass, vlist in other_valves.items():
            id_str = _format_id_list([v.id for v in vlist])
            friendly = re.sub(r"([a-z])([A-Z])", r"\1 \2", vclass)
            lbl = f"{friendly} {id_str}".strip()
            sec2_items.append(("valve", lbl))

        # ---------------- Section 3: Instrumentation (ISA-5.1) ----------------
        instruments = [
            u
            for u in units
            if u.__class__.__name__ == "Instrument"
            or hasattr(u, "balloon_type")
            or hasattr(u, "tag")
        ]
        detected_tags: list[tuple[str, str]] = []
        sample_tag_prefix = "FIT"

        if instruments:
            unique_letters: set[str] = set()
            for inst in instruments:
                raw_tag = getattr(inst, "tag", None)
                if raw_tag is not None:
                    if hasattr(raw_tag, "letters"):
                        letters = raw_tag.letters.upper()
                    else:
                        parsed = parse_isa_tag(str(raw_tag))
                        letters = parsed.letters.upper()
                else:
                    match = re.match(r"^[A-Za-z]+", inst.id)
                    letters = match.group(0).upper() if match else ""

                if letters:
                    unique_letters.add(letters)

            sorted_letters = sorted(unique_letters)
            if sorted_letters:
                sample_tag_prefix = sorted_letters[0]

            for let in sorted_letters:
                desc = ISA_51_TAG_DESCRIPTIONS.get(
                    let, f"{let} Indicating / Transmitting Instrument"
                )
                detected_tags.append((let, desc))

        # ---------------- Section 4: Major Equipment Icons ----------------
        equipment_groups: dict[str, dict[str, Any]] = {}
        for u in units:
            cname = u.__class__.__name__
            uid = u.id.upper()
            uname = getattr(u, "name", "").lower()

            if (
                cname == "StreamFlag"
                or "StreamFlag" in type(u).__name__
                or u in all_motive
                or u in all_valves
                or u in instruments
            ):
                continue

            if "mixer" in cname.lower() or "mixer" in uname:
                cat_key = "Mixer"
                draw_type = "mixer"
                base_label = "Continuous Stirred Tank Mixer"
            elif "flotation" in cname.lower() or "daf" in uid or "daf" in uname:
                cat_key = "FlotationCell"
                draw_type = "daf"
                base_label = "Flotation Separator (DAF)"
            elif "membrane" in cname.lower() or "tubular" in cname.lower():
                cat_key = "MembraneModule"
                draw_type = "membrane"
                base_label = "Tubular Reactor / Membrane"
            elif cname == "HorizontalVessel":
                cat_key = "HorizontalVessel"
                draw_type = "horizontal_vessel"
                base_label = "Horizontal Process Vessel"
            elif cname == "JacketedVessel":
                cat_key = "JacketedVessel"
                draw_type = "jacketed_vessel"
                base_label = "Jacketed Process Vessel"
            elif cname == "Vessel":
                if "reactor" in uname:
                    cat_key = "ReactorVessel"
                    draw_type = "vessel"
                    base_label = "Process Reactor / Vessel"
                else:
                    cat_key = "Vessel"
                    draw_type = "vessel"
                    base_label = "Vertical Process Vessel"
            elif any(
                ex in cname
                for ex in (
                    "HeatExchanger",
                    "ShellAndTube",
                    "PlateHex",
                    "AirCooler",
                    "Condenser",
                    "Reboiler",
                )
            ):
                cat_key = cname
                draw_type = "exchanger"
                base_label = f"Heat Exchanger ({cname})"
            elif "distillation" in cname.lower():
                cat_key = "Distillation"
                draw_type = "distillation"
                base_label = "Distillation Column"
            else:
                cat_key = cname
                draw_type = "generic"
                friendly = re.sub(r"([a-z])([A-Z])", r"\1 \2", cname)
                base_label = friendly

            if cat_key not in equipment_groups:
                equipment_groups[cat_key] = {
                    "draw_type": draw_type,
                    "base_label": base_label,
                    "units": [],
                }
            equipment_groups[cat_key]["units"].append(u)

        sec4_items = []
        for cat_key, grp in equipment_groups.items():
            u_ids = [u.id for u in grp["units"]]
            id_str = _format_id_list(u_ids)
            base_lbl = grp["base_label"]
            if id_str:
                if base_lbl.endswith(")"):
                    inner = base_lbl[base_lbl.rfind("(") + 1 : -1]
                    if inner in u_ids and len(u_ids) == 1:
                        lbl = base_lbl
                    else:
                        lbl = f"{base_lbl} {id_str}"
                else:
                    lbl = f"{base_lbl} {id_str}"
            else:
                lbl = base_lbl
            sec4_items.append((grp["draw_type"], lbl))

        # ---------------- Dynamic Rendering Coordinates ----------------
        y_curr = y0 + 24.0

        # Draw Section 1 if items exist
        if sec1_items or custom_sec1:
            y_curr = self._render_section_header(ctx, x0, y_curr, x1, "1. PIPING & STREAM LINES")
            for kind, label in sec1_items:
                if y_curr > y1 - 15.0:
                    break
                if kind == "process":
                    _draw_line_sample(ctx, x0, y_curr, line_type="process")
                elif kind == "recycle":
                    _draw_line_sample(ctx, x0, y_curr, line_type="recycle")
                elif kind == "signal":
                    _draw_line_sample(ctx, x0, y_curr, line_type="signal")
                elif kind == "flag":
                    _draw_stream_flag_sample(ctx, x0, y_curr, text="FEED")
                ctx.text(
                    (x0 + 85, y_curr + 3.0),
                    text=label,
                    fontFamily="Arial",
                    textColor=(0, 0, 0, 255),
                    fontSize=6.5,
                    textAnchor="start",
                )
                y_curr += 19.0

            for entry in custom_sec1:
                if y_curr > y1 - 15.0:
                    break
                lbl = self._get_entry_label(entry)
                self._draw_custom_item(ctx, entry, x0, y_curr, lbl)
                y_curr += 19.0

            y_curr += 6.0

        # Draw Section 2 if items exist
        if sec2_items or custom_sec2:
            y_curr = self._render_section_header(
                ctx, x0, y_curr, x1, "2. VALVES & MOTIVE EQUIPMENT"
            )
            all_sec2: list[tuple[str, str, Any]] = [(k, lbl, None) for k, lbl in sec2_items] + [
                ("custom", self._get_entry_label(e), e) for e in custom_sec2
            ]

            if self.two_column_sections and len(all_sec2) > 1:
                y_curr = self._render_two_column_section(
                    ctx, x0, y_curr, x1, y1, all_sec2, category="valves"
                )
            else:
                for kind, label, entry in all_sec2:
                    if y_curr > y1 - 15.0:
                        break
                    if kind == "custom":
                        self._draw_custom_item(ctx, entry, x0, y_curr, label, compact=False)
                    else:
                        self._draw_valve_motive_symbol(ctx, kind, x0, y_curr, compact=False)
                        ctx.text(
                            (x0 + 85, y_curr + 3.0),
                            text=label,
                            fontFamily="Arial",
                            textColor=(0, 0, 0, 255),
                            fontSize=6.5,
                            textAnchor="start",
                        )
                    y_curr += 25.0

            y_curr += 6.0

        # Draw Section 3 if instruments or custom entries exist
        if instruments or custom_sec3:
            y_curr = self._render_section_header(
                ctx, x0, y_curr, x1, "3. INSTRUMENTATION (ISA-5.1)"
            )
            if instruments:
                _draw_balloon_sample(ctx, x0, y_curr, tag_text=sample_tag_prefix, compact=False)
                ctx.text(
                    (x0 + 85, y_curr + 3.0),
                    text="Field-Mounted Instrument Balloon",
                    fontFamily="Arial",
                    textColor=(0, 0, 0, 255),
                    fontSize=6.5,
                    textAnchor="start",
                )
                y_curr += 20.0

                # Render tag code table
                half = (len(detected_tags) + 1) // 2
                col1 = detected_tags[:half]
                col2 = detected_tags[half:]
                col_w = (x1 - x0) / 2.0

                for idx in range(max(len(col1), len(col2))):
                    if y_curr > y1 - 15.0:
                        break
                    if idx < len(col1):
                        tag, desc = col1[idx]
                        ctx.text(
                            (x0 + 16, y_curr),
                            text=f"• {tag}:",
                            fontFamily="Arial",
                            textColor=(0, 0, 0, 255),
                            fontSize=6.0,
                            textAnchor="start",
                        )
                        ctx.text(
                            (x0 + 46, y_curr),
                            text=desc,
                            fontFamily="Arial",
                            textColor=(70, 70, 70, 255),
                            fontSize=5.5,
                            textAnchor="start",
                        )
                    if idx < len(col2):
                        tag, desc = col2[idx]
                        ctx.text(
                            (x0 + col_w + 8, y_curr),
                            text=f"• {tag}:",
                            fontFamily="Arial",
                            textColor=(0, 0, 0, 255),
                            fontSize=6.0,
                            textAnchor="start",
                        )
                        ctx.text(
                            (x0 + col_w + 40, y_curr),
                            text=desc,
                            fontFamily="Arial",
                            textColor=(70, 70, 70, 255),
                            fontSize=5.5,
                            textAnchor="start",
                        )
                    y_curr += 15.0

            for entry in custom_sec3:
                if y_curr > y1 - 15.0:
                    break
                lbl = self._get_entry_label(entry)
                self._draw_custom_item(ctx, entry, x0, y_curr, lbl)
                y_curr += 18.0

            y_curr += 6.0

        # Draw Section 4 if equipment or custom entries exist
        if sec4_items or custom_sec4:
            y_curr = self._render_section_header(ctx, x0, y_curr, x1, "4. MAJOR EQUIPMENT ICONS")
            all_sec4: list[tuple[str, str, Any]] = [(k, lbl, None) for k, lbl in sec4_items] + [
                ("custom", self._get_entry_label(e), e) for e in custom_sec4
            ]

            if self.two_column_sections and len(all_sec4) > 1:
                y_curr = self._render_two_column_section(
                    ctx, x0, y_curr, x1, y1, all_sec4, category="equipment"
                )
            else:
                for kind, label, entry in all_sec4:
                    if y_curr > y1 - 15.0:
                        break
                    if kind == "custom":
                        self._draw_custom_item(ctx, entry, x0, y_curr, label, compact=False)
                    else:
                        self._draw_equipment_symbol(
                            ctx, kind, x0, y_curr, label=label, compact=False
                        )
                        ctx.text(
                            (x0 + 85, y_curr + 3.0),
                            text=label,
                            fontFamily="Arial",
                            textColor=(0, 0, 0, 255),
                            fontSize=6.5,
                            textAnchor="start",
                        )
                    y_curr += 25.0

            y_curr += 6.0

        # ---------------- Section 5: Process Streams ----------------
        if all_process_streams or custom_sec5:
            y_curr = self._render_process_streams_section(
                ctx, x0, y_curr, x1, y1, all_process_streams, custom_sec5, flowsheet=flowsheet
            )

    def _render_two_column_section(
        self,
        ctx,
        x0: float,
        y_curr: float,
        x1: float,
        y1: float,
        items: list[tuple[str, str, Any]],
        category: str = "valves",
    ) -> float:
        col_w = (x1 - x0) / 2.0
        half = (len(items) + 1) // 2
        col1 = items[:half]
        col2 = items[half:]
        num_rows = max(len(col1), len(col2))

        for r in range(num_rows):
            if y_curr > y1 - 15.0:
                break
            for col_idx, col_items in ((0, col1), (1, col2)):
                if r < len(col_items):
                    kind, label, entry = col_items[r]
                    col_x = x0 + col_idx * col_w
                    cx = col_x + 20.0
                    text_x = col_x + 40.0

                    if kind == "custom":
                        self._draw_custom_item(
                            ctx, entry, cx, y_curr, label, compact=True, text_x=text_x
                        )
                    elif category == "valves":
                        self._draw_valve_motive_symbol(ctx, kind, cx, y_curr, compact=True)
                        ctx.text(
                            (text_x, y_curr + 2.5),
                            text=label,
                            fontFamily="Arial",
                            textColor=(0, 0, 0, 255),
                            fontSize=5.5,
                            textAnchor="start",
                        )
                    else:  # equipment
                        self._draw_equipment_symbol(
                            ctx, kind, cx, y_curr, label=label, compact=True
                        )
                        ctx.text(
                            (text_x, y_curr + 2.5),
                            text=label,
                            fontFamily="Arial",
                            textColor=(0, 0, 0, 255),
                            fontSize=5.5,
                            textAnchor="start",
                        )
            y_curr += 21.0
        return y_curr

    def _render_process_streams_section(
        self,
        ctx,
        x0: float,
        y_curr: float,
        x1: float,
        y1: float,
        process_streams: list[Any],
        custom_sec5: list[Any],
        flowsheet: Any = None,
    ) -> float:
        stream_entries: list[tuple[str, str]] = []
        for entry in process_streams:
            sid, sdesc = self._normalize_stream_entry(entry, flowsheet)
            if sid or sdesc:
                stream_entries.append((sid, sdesc))

        for entry in custom_sec5:
            sid = str(entry.get("id", "")) if isinstance(entry, dict) else ""
            sdesc = self._get_entry_label(entry)
            stream_entries.append((sid, sdesc))

        if not stream_entries or y_curr > y1 - 20.0:
            return y_curr

        y_curr = self._render_section_header(ctx, x0, y_curr, x1, "5. PROCESS STREAMS")

        use_two_col = self.two_column_sections and len(stream_entries) > 2
        col_w = (x1 - x0) / 2.0

        if use_two_col:
            half = (len(stream_entries) + 1) // 2
            col1 = stream_entries[:half]
            col2 = stream_entries[half:]
            num_rows = max(len(col1), len(col2))

            for r in range(num_rows):
                if y_curr > y1 - 10.0:
                    break
                for col_idx, col_items in ((0, col1), (1, col2)):
                    if r < len(col_items):
                        sid, sdesc = col_items[r]
                        col_x = x0 + col_idx * col_w
                        disp_desc = sdesc if len(sdesc) <= 38 else sdesc[:35] + "..."
                        if sid:
                            tag_text = f"• {sid}:"
                            ctx.text(
                                (col_x + 14, y_curr),
                                text=tag_text,
                                fontFamily="Arial",
                                textColor=(0, 0, 0, 255),
                                fontSize=6.0,
                                textAnchor="start",
                            )
                            offset = max(30.0, len(tag_text) * 4.2 + 2.0)
                            ctx.text(
                                (col_x + 14 + offset, y_curr),
                                text=disp_desc,
                                fontFamily="Arial",
                                textColor=(70, 70, 70, 255),
                                fontSize=5.5,
                                textAnchor="start",
                            )
                        else:
                            ctx.text(
                                (col_x + 14, y_curr),
                                text=f"• {disp_desc}",
                                fontFamily="Arial",
                                textColor=(0, 0, 0, 255),
                                fontSize=5.5,
                                textAnchor="start",
                            )
                y_curr += 14.5
        else:
            for sid, sdesc in stream_entries:
                if y_curr > y1 - 10.0:
                    break
                disp_desc = sdesc if len(sdesc) <= 75 else sdesc[:72] + "..."
                if sid:
                    tag_text = f"• {sid}:"
                    ctx.text(
                        (x0 + 16, y_curr),
                        text=tag_text,
                        fontFamily="Arial",
                        textColor=(0, 0, 0, 255),
                        fontSize=6.0,
                        textAnchor="start",
                    )
                    offset = max(34.0, len(tag_text) * 4.2 + 3.0)
                    ctx.text(
                        (x0 + 16 + offset, y_curr),
                        text=disp_desc,
                        fontFamily="Arial",
                        textColor=(70, 70, 70, 255),
                        fontSize=5.5,
                        textAnchor="start",
                    )
                else:
                    ctx.text(
                        (x0 + 16, y_curr),
                        text=f"• {disp_desc}",
                        fontFamily="Arial",
                        textColor=(0, 0, 0, 255),
                        fontSize=5.5,
                        textAnchor="start",
                    )
                y_curr += 15.0

        return y_curr

    def _normalize_stream_entry(self, entry: Any, flowsheet: Any = None) -> tuple[str, str]:
        """Converts stream dict, tuple, Stream object, or string into (id, description)."""
        if isinstance(entry, dict):
            sid = str(
                entry.get("id")
                or entry.get("number")
                or entry.get("stream")
                or entry.get("tag")
                or ""
            ).strip()
            name = str(entry.get("name") or entry.get("label") or entry.get("title") or "").strip()
            desc = str(entry.get("description") or entry.get("desc") or "").strip()

            if sid and name:
                full_desc = f"{name} ({desc})" if desc else name
                return (sid, full_desc)
            if sid and desc:
                return (sid, desc)
            if name:
                return (sid, name)
            if sid:
                if (
                    flowsheet is not None
                    and hasattr(flowsheet, "streams")
                    and sid in flowsheet.streams
                ):
                    st = flowsheet.streams[sid]
                    s_name = getattr(st, "name", None) or getattr(st, "description", None) or ""
                    return (sid, s_name)
                return (sid, "")
            return ("", desc or "Stream")

        if isinstance(entry, (tuple, list)):
            if len(entry) >= 2:
                sid = str(entry[0]).strip()
                desc = str(entry[1]).strip()
                if len(entry) > 2 and entry[2]:
                    desc = f"{desc} ({entry[2]})"
                return (sid, desc)
            if len(entry) == 1:
                return ("", str(entry[0]).strip())
            return ("", "")

        if hasattr(entry, "id"):  # Stream object
            sid = str(entry.id)
            desc = (
                getattr(entry, "name", None)
                or getattr(entry, "description", None)
                or getattr(entry, "line_type", "")
                or ""
            )
            return (sid, desc)

        if isinstance(entry, str):
            s = entry.strip()
            if ":" in s:
                parts = s.split(":", 1)
                return (parts[0].strip(), parts[1].strip())
            if " - " in s:
                parts = s.split(" - ", 1)
                return (parts[0].strip(), parts[1].strip())
            if "." in s and s.split(".", 1)[0].strip().isdigit():
                parts = s.split(".", 1)
                return (parts[0].strip(), parts[1].strip())
            if flowsheet is not None and hasattr(flowsheet, "streams") and s in flowsheet.streams:
                st = flowsheet.streams[s]
                desc = getattr(st, "name", None) or getattr(st, "description", None) or s
                return (s, desc)
            return ("", s)

        return ("", str(entry))

    def _draw_valve_motive_symbol(
        self, ctx, kind: str, x: float, y: float, compact: bool = False
    ) -> None:
        if kind in ("pump", "centrifugal_pump"):
            _draw_pump_sample(ctx, x, y, compact=compact)
        elif kind in ("progressive_cavity_pump", "cavity_pump", "screw_pump"):
            _draw_progressive_cavity_pump_sample(ctx, x, y, compact=compact)
        elif kind in ("peristaltic_pump", "hose_pump"):
            _draw_peristaltic_pump_sample(ctx, x, y, compact=compact)
        elif kind in ("reciprocating_pump", "piston_pump", "plunger_pump"):
            _draw_reciprocating_pump_sample(ctx, x, y, compact=compact)
        elif kind == "compressor":
            _draw_compressor_sample(ctx, x, y, compact=compact)
        elif kind == "blower":
            _draw_blower_sample(ctx, x, y, compact=compact)
        elif kind == "control_valve":
            _draw_control_valve_sample(ctx, x, y, compact=compact)
        elif kind == "check_valve":
            _draw_check_valve_sample(ctx, x, y, compact=compact)
        elif kind == "relief_valve":
            _draw_relief_valve_sample(ctx, x, y, compact=compact)
        elif kind == "sampling_valve":
            _draw_sampling_valve_sample(ctx, x, y, compact=compact)
        else:
            _draw_isolation_valve_sample(ctx, x, y, compact=compact)

    def _draw_equipment_symbol(
        self, ctx, kind: str, x: float, y: float, label: str = "UNIT", compact: bool = False
    ) -> None:
        if kind == "mixer":
            _draw_mixer_sample(ctx, x, y, compact=compact)
        elif kind == "daf":
            _draw_daf_sample(ctx, x, y, compact=compact)
        elif kind == "membrane":
            _draw_membrane_sample(ctx, x, y, compact=compact)
        elif kind == "vessel":
            _draw_vessel_sample(ctx, x, y, compact=compact)
        elif kind == "horizontal_vessel":
            _draw_horizontal_vessel_sample(ctx, x, y, compact=compact)
        elif kind == "jacketed_vessel":
            _draw_jacketed_vessel_sample(ctx, x, y, compact=compact)
        elif kind == "exchanger":
            _draw_exchanger_sample(ctx, x, y, compact=compact)
        elif kind == "distillation":
            _draw_distillation_sample(ctx, x, y, compact=compact)
        else:
            _draw_generic_equipment_sample(ctx, x, y, label=label, compact=compact)

    def _render_section_header(self, ctx, x0: float, y: float, x1: float, title: str) -> float:
        ctx.text(
            (x0 + 10, y + 8.0),
            text=title,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.line(
            (x0 + 10, y + 11.0),
            (x1 - 10, y + 11.0),
            lineColor=(200, 200, 200, 255),
            lineSize=0.5,
        )
        return y + 21.0

    def _normalize_section(self, raw_section: Any) -> int:
        if raw_section in (1, "1", "lines", "piping"):
            return 1
        if raw_section in (2, "2", "valves", "motive"):
            return 2
        if raw_section in (3, "3", "instruments", "instrumentation"):
            return 3
        if raw_section in (4, "4", "equipment"):
            return 4
        if raw_section in (5, "5", "streams", "process_streams", "process"):
            return 5
        if isinstance(raw_section, str):
            s = raw_section.strip().upper()
            if "PIPING" in s or "LINE" in s:
                return 1
            if "VALVE" in s or "MOTIVE" in s or "PUMP" in s:
                return 2
            if "INSTRUMENT" in s or "ISA" in s:
                return 3
            if "EQUIPMENT" in s:
                return 4
            if "STREAM" in s or "PROCESS" in s:
                return 5
        return 4

    def _get_entry_label(self, entry: Any) -> str:
        if isinstance(entry, dict):
            return str(
                entry.get("label")
                or entry.get("text")
                or entry.get("name")
                or entry.get("description", "Custom Entry")
            )
        return str(entry)

    def _draw_custom_item(
        self,
        ctx,
        entry: Any,
        x: float,
        y: float,
        label: str,
        compact: bool = False,
        text_x: float | None = None,
    ) -> None:
        cx = x if compact else x + 45.0
        tx = text_x if text_x is not None else (x + 40.0 if compact else x + 85.0)
        font_size = 5.5 if compact else 6.5

        if isinstance(entry, dict) and callable(entry.get("draw")):
            entry["draw"](ctx, cx, y)
        else:
            sym = entry.get("symbol", "").lower() if isinstance(entry, dict) else ""
            if sym in ("line", "stream", "dashed"):
                _draw_line_sample(ctx, cx - 14.0 if compact else x, y, line_type="process")
            elif sym in ("valve",):
                _draw_isolation_valve_sample(ctx, x, y, compact=compact)
            elif sym in ("pump", "centrifugal_pump"):
                _draw_pump_sample(ctx, x, y, compact=compact)
            elif sym in ("progressive_cavity_pump", "cavity_pump", "screw_pump"):
                _draw_progressive_cavity_pump_sample(ctx, x, y, compact=compact)
            elif sym in ("peristaltic_pump", "hose_pump"):
                _draw_peristaltic_pump_sample(ctx, x, y, compact=compact)
            elif sym in ("reciprocating_pump", "piston_pump", "plunger_pump"):
                _draw_reciprocating_pump_sample(ctx, x, y, compact=compact)
            elif sym == "compressor":
                _draw_compressor_sample(ctx, x, y, compact=compact)
            elif sym == "blower":
                _draw_blower_sample(ctx, x, y, compact=compact)
            elif sym in ("circle", "balloon"):
                _draw_balloon_sample(ctx, x, y, tag_text="TAG", compact=compact)
            else:
                _draw_generic_equipment_sample(ctx, x, y, label=label, compact=compact)

        ctx.text(
            (tx, y + 2.5 if compact else y + 3.0),
            text=label,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=font_size,
            textAnchor="start",
        )
