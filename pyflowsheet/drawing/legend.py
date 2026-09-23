from __future__ import annotations

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
    "AIT": "Analytical Transmitter (pH/IONP)",
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


def _draw_pump_sample(ctx, x0: float, y: float) -> None:
    cx = x0 + 45
    ctx.line((x0 + 15, y), (cx - 7, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
    ctx.line((cx, y - 7), (cx, y - 12), lineColor=(0, 0, 0, 255), lineSize=1.2)
    ctx.line((cx, y - 12), (x0 + 75, y - 12), lineColor=(0, 0, 0, 255), lineSize=1.2)
    ctx.circle(
        [(cx - 7, y - 7), (cx + 7, y + 7)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.2,
    )


def _draw_control_valve_sample(ctx, x0: float, y: float) -> None:
    cx = x0 + 45
    ctx.line((x0 + 15, y), (x0 + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
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


def _draw_check_valve_sample(ctx, x0: float, y: float) -> None:
    cx = x0 + 45
    ctx.line((x0 + 15, y), (x0 + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
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


def _draw_relief_valve_sample(ctx, x0: float, y: float) -> None:
    cx = x0 + 45
    ctx.line((x0 + 15, y), (cx, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
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


def _draw_sampling_valve_sample(ctx, x0: float, y: float) -> None:
    cx = x0 + 45
    ctx.line((x0 + 15, y - 8), (x0 + 75, y - 8), lineColor=(0, 0, 0, 255), lineSize=1.2)
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


def _draw_isolation_valve_sample(ctx, x0: float, y: float) -> None:
    cx = x0 + 45
    ctx.line((x0 + 15, y), (x0 + 75, y), lineColor=(0, 0, 0, 255), lineSize=1.2)
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


def _draw_balloon_sample(ctx, x0: float, y: float, tag_text: str = "FIT") -> None:
    cx = x0 + 45
    ctx.line((x0 + 20, y + 12), (cx, y), lineColor=(120, 120, 120, 255), lineSize=1.0)
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


def _draw_mixer_sample(ctx, x0: float, y: float) -> None:
    ctx.rectangle(
        [(x0 + 25, y - 12), (x0 + 65, y + 12)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )
    ctx.line((x0 + 45, y - 12), (x0 + 45, y + 6), lineColor=(0, 0, 0, 255), lineSize=1.0)
    ctx.line((x0 + 37, y + 6), (x0 + 53, y + 6), lineColor=(0, 0, 0, 255), lineSize=1.2)


def _draw_daf_sample(ctx, x0: float, y: float) -> None:
    ctx.rectangle(
        [(x0 + 20, y - 8), (x0 + 70, y + 8)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )
    ctx.text(
        (x0 + 45, y + 2.5),
        text="DAF",
        fontFamily="Arial",
        textColor=(100, 100, 100, 255),
        fontSize=5.0,
        textAnchor="middle",
    )


def _draw_membrane_sample(ctx, x0: float, y: float) -> None:
    ctx.rectangle(
        [(x0 + 20, y - 8), (x0 + 70, y + 8)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )
    for tx in [x0 + 32, x0 + 45, x0 + 58]:
        ctx.line((tx, y - 8), (tx, y + 8), lineColor=(150, 150, 150, 255), lineSize=0.7)


def _draw_vessel_sample(ctx, x0: float, y: float) -> None:
    ctx.rectangle(
        [(x0 + 33, y - 12), (x0 + 57, y + 12)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )
    ctx.line((x0 + 33, y - 7), (x0 + 57, y - 7), lineColor=(180, 180, 180, 255), lineSize=0.6)
    ctx.line((x0 + 33, y + 7), (x0 + 57, y + 7), lineColor=(180, 180, 180, 255), lineSize=0.6)


def _draw_horizontal_vessel_sample(ctx, x0: float, y: float) -> None:
    ctx.rectangle(
        [(x0 + 20, y - 8), (x0 + 70, y + 8)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )
    ctx.line((x0 + 28, y - 8), (x0 + 28, y + 8), lineColor=(180, 180, 180, 255), lineSize=0.6)
    ctx.line((x0 + 62, y - 8), (x0 + 62, y + 8), lineColor=(180, 180, 180, 255), lineSize=0.6)


def _draw_jacketed_vessel_sample(ctx, x0: float, y: float) -> None:
    ctx.rectangle(
        [(x0 + 30, y - 10), (x0 + 60, y + 10)],
        fillColor=None,
        lineColor=(0, 0, 0, 255),
        lineSize=0.8,
    )
    ctx.rectangle(
        [(x0 + 34, y - 13), (x0 + 56, y + 13)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )


def _draw_exchanger_sample(ctx, x0: float, y: float) -> None:
    cx = x0 + 45
    ctx.circle(
        [(cx - 10, y - 10), (cx + 10, y + 10)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )
    ctx.line((cx - 10, y), (cx + 10, y), lineColor=(0, 0, 0, 255), lineSize=0.8)


def _draw_distillation_sample(ctx, x0: float, y: float) -> None:
    ctx.rectangle(
        [(x0 + 35, y - 14), (x0 + 55, y + 14)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )
    for ty in [y - 7, y, y + 7]:
        ctx.line((x0 + 35, ty), (x0 + 55, ty), lineColor=(150, 150, 150, 255), lineSize=0.6)


def _draw_generic_equipment_sample(ctx, x0: float, y: float, label: str = "UNIT") -> None:
    ctx.rectangle(
        [(x0 + 22, y - 9), (x0 + 68, y + 9)],
        fillColor=(255, 255, 255, 255),
        lineColor=(0, 0, 0, 255),
        lineSize=1.0,
    )
    ctx.text(
        (x0 + 45, y + 2.5),
        text=label[:8],
        fontFamily="Arial",
        textColor=(100, 100, 100, 255),
        fontSize=5.0,
        textAnchor="middle",
    )


class DrawingLegend:
    """Standard PFD & P&ID Legend detailing symbols, lines, valves, pumps,
    instruments, and equipment. Supports dynamic introspection of Flowsheet
    units/streams and customizable schema entries.
    """

    def __init__(
        self,
        rect: tuple[tuple[float, float], tuple[float, float]] = (
            (880.0, 58.0),
            (1260.0, 652.0),
        ),
        custom_entries: list[dict[str, Any]] | None = None,
    ):
        self.id = "legend"
        self.rect = rect
        self.custom_entries: list[dict[str, Any]] = (
            list(custom_entries) if custom_entries is not None else []
        )

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
        # Section 1: Piping & Stream Lines
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

        y_item1 = y_sec1 + 24.0
        _draw_line_sample(ctx, x0, y_item1, line_type="process")
        ctx.text(
            (x0 + 85, y_item1 + 3.0),
            text="Major Process Stream (100 m^3/h)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_item2 = y_item1 + 20.0
        _draw_line_sample(ctx, x0, y_item2, line_type="recycle")
        ctx.text(
            (x0 + 85, y_item2 + 3.0),
            text="Recycle / Return Stream",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_item3 = y_item2 + 20.0
        _draw_line_sample(ctx, x0, y_item3, line_type="signal")
        ctx.text(
            (x0 + 85, y_item3 + 3.0),
            text="Instrument Process Tap / Leader",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_item4 = y_item3 + 22.0
        _draw_stream_flag_sample(ctx, x0, y_item4, text="FEED")
        ctx.text(
            (x0 + 85, y_item4 + 3.0),
            text="Stream Inflow / Outflow Boundary",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Section 2: Valves & Motive Equipment
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

        y_pmp = y_sec2 + 25.0
        _draw_pump_sample(ctx, x0, y_pmp)
        ctx.text(
            (x0 + 85, y_pmp + 3.0),
            text="Centrifugal Pump (P-101 .. P-107)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_cv = y_pmp + 30.0
        _draw_control_valve_sample(ctx, x0, y_cv)
        ctx.text(
            (x0 + 85, y_cv + 3.0),
            text="Control Valve with Actuator (FCV, PCV)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_ckv = y_cv + 26.0
        _draw_check_valve_sample(ctx, x0, y_ckv)
        ctx.text(
            (x0 + 85, y_ckv + 3.0),
            text="Check / Non-Return Valve (CKV)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_psv = y_ckv + 26.0
        _draw_relief_valve_sample(ctx, x0, y_psv)
        ctx.text(
            (x0 + 85, y_psv + 3.0),
            text="Safety Relief Valve (PSV)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_smp = y_psv + 26.0
        _draw_sampling_valve_sample(ctx, x0, y_smp)
        ctx.text(
            (x0 + 85, y_smp + 3.0),
            text="In-Line Sampling Valve (V-SMP)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Section 3: ISA-5.1 Instrumentation
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

        y_inst = y_sec3 + 26.0
        _draw_balloon_sample(ctx, x0, y_inst, tag_text="FIT")
        ctx.text(
            (x0 + 85, y_inst + 3.0),
            text="Field-Mounted Instrument Balloon",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

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

        # Section 4: Equipment Models
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

        y_eq1 = y_sec4 + 28.0
        _draw_mixer_sample(ctx, x0, y_eq1)
        ctx.text(
            (x0 + 85, y_eq1 + 3.0),
            text="Continuous Stirred Tank Mixer (Mixer)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_eq2 = y_eq1 + 30.0
        _draw_daf_sample(ctx, x0, y_eq2)
        ctx.text(
            (x0 + 85, y_eq2 + 3.0),
            text="Flotation Separator (DAF)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        y_eq3 = y_eq2 + 28.0
        _draw_membrane_sample(ctx, x0, y_eq3)
        ctx.text(
            (x0 + 85, y_eq3 + 3.0),
            text="Tubular Reactor / Membrane (UV/US, NF)",
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )

        # Render any custom entries appended
        if self.custom_entries:
            y_curr = y_eq3 + 28.0
            for entry in self.custom_entries:
                if y_curr > y1 - 15.0:
                    break
                label = self._get_entry_label(entry)
                self._draw_custom_item(ctx, entry, x0, y_curr, label)
                y_curr += 24.0

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

        # Partition custom entries by section index (1..4)
        custom_sec1 = []
        custom_sec2 = []
        custom_sec3 = []
        custom_sec4 = []

        for e in all_custom:
            sec_target = self._normalize_section(e.get("section") if isinstance(e, dict) else 4)
            if sec_target == 1:
                custom_sec1.append(e)
            elif sec_target == 2:
                custom_sec2.append(e)
            elif sec_target == 3:
                custom_sec3.append(e)
            else:
                custom_sec4.append(e)

        units = (
            list(flowsheet.unitOperations.values()) if hasattr(flowsheet, "unitOperations") else []
        )
        streams = list(flowsheet.streams.values()) if hasattr(flowsheet, "streams") else []

        # ---------------- Section 1: Lines & Streams ----------------
        sec1_items: list[tuple[str, str]] = []  # (kind, label)
        # Always emit process stream if streams exist or as standard default
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
        pumps: list[Any] = []
        control_valves: list[Any] = []
        check_valves: list[Any] = []
        safety_valves: list[Any] = []
        sampling_valves: list[Any] = []
        other_valves: list[Any] = []

        for u in units:
            cname = u.__class__.__name__
            uid = u.id.upper()
            uname = getattr(u, "name", "").lower()

            if (
                "pump" in cname.lower()
                or uid.startswith(("P-", "P_"))
                or (len(uid) >= 2 and uid[0] == "P" and uid[1:].isdigit())
            ):
                pumps.append(u)
            elif (
                cname == "ControlValve"
                or (hasattr(u, "actuator") and u.actuator is not None)
                or uid.startswith(("FCV", "PCV", "TCV", "LCV"))
                or "control" in uname
            ):
                control_valves.append(u)
            elif cname == "CheckValve" or uid.startswith("CKV") or "check" in uname:
                check_valves.append(u)
            elif (
                cname in ("SafetyReliefValve", "RuptureDisc")
                or uid.startswith(("PSV", "PRV", "SRV"))
                or "safety" in uname
                or "relief" in uname
            ):
                safety_valves.append(u)
            elif (
                cname in ("GrabSamplingTee", "NeedleValve")
                or uid.startswith(("SMP", "V-SMP", "SP"))
                or "sample" in uname
                or "sampling" in uname
            ):
                sampling_valves.append(u)
            elif "valve" in cname.lower() or uid.startswith("V-") or uid.startswith("V_"):
                other_valves.append(u)

        if pumps:
            pump_ids = [p.id for p in pumps]
            if len(pump_ids) == 1:
                sec2_items.append(("pump", f"Centrifugal Pump ({pump_ids[0]})"))
            elif len(pump_ids) > 1:
                sec2_items.append(("pump", f"Centrifugal Pump ({pump_ids[0]} .. {pump_ids[-1]})"))
            else:
                sec2_items.append(("pump", "Centrifugal Pump"))

        if control_valves:
            sec2_items.append(("control_valve", "Control Valve with Actuator (FCV, PCV)"))
        if check_valves:
            sec2_items.append(("check_valve", "Check / Non-Return Valve (CKV)"))
        if safety_valves:
            sec2_items.append(("relief_valve", "Safety Relief Valve (PSV)"))
        if sampling_valves:
            sec2_items.append(("sampling_valve", "In-Line Sampling Valve (V-SMP)"))
        if other_valves:
            first_v = other_valves[0]
            sec2_items.append(("valve", f"Process Valve ({first_v.__class__.__name__})"))

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
        equipment_map: dict[str, tuple[str, str]] = {}  # key -> (draw_type, label)
        for u in units:
            cname = u.__class__.__name__
            uid = u.id.upper()
            uname = getattr(u, "name", "").lower()

            # Skip units belonging to sections 1, 2, or 3
            if (
                cname == "StreamFlag"
                or "StreamFlag" in type(u).__name__
                or u in pumps
                or u in control_valves
                or u in check_valves
                or u in safety_valves
                or u in sampling_valves
                or u in other_valves
                or u in instruments
            ):
                continue

            if "mixer" in cname.lower() or "mixer" in uname:
                equipment_map["Mixer"] = ("mixer", "Continuous Stirred Tank Mixer (Mixer)")
            elif "flotation" in cname.lower() or "daf" in uid or "daf" in uname:
                equipment_map["FlotationCell"] = ("daf", "Flotation Separator (DAF)")
            elif "membrane" in cname.lower() or "tubular" in cname.lower():
                equipment_map["MembraneModule"] = (
                    "membrane",
                    "Tubular Reactor / Membrane (UV/US, NF)",
                )
            elif cname == "Vessel":
                equipment_map["Vessel"] = ("vessel", f"Vertical Process Vessel ({u.id})")
            elif cname == "HorizontalVessel":
                equipment_map["HorizontalVessel"] = (
                    "horizontal_vessel",
                    f"Horizontal Process Vessel ({u.id})",
                )
            elif cname == "JacketedVessel":
                equipment_map["JacketedVessel"] = (
                    "jacketed_vessel",
                    f"Jacketed Process Vessel ({u.id})",
                )
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
                equipment_map["HeatExchanger"] = ("exchanger", f"Heat Exchanger ({cname})")
            elif "distillation" in cname.lower():
                equipment_map["Distillation"] = ("distillation", "Distillation Column")
            else:
                equipment_map[cname] = (
                    "generic",
                    f"{cname} ({u.name or u.id})",
                )

        sec4_items = list(equipment_map.values())

        # ---------------- Dynamic Rendering Coordinates ----------------
        y_curr = y0 + 26.0

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
                y_curr += 20.0

            for entry in custom_sec1:
                if y_curr > y1 - 15.0:
                    break
                lbl = self._get_entry_label(entry)
                self._draw_custom_item(ctx, entry, x0, y_curr, lbl)
                y_curr += 20.0

            y_curr += 8.0

        # Draw Section 2 if items exist
        if sec2_items or custom_sec2:
            y_curr = self._render_section_header(
                ctx, x0, y_curr, x1, "2. VALVES & MOTIVE EQUIPMENT"
            )
            for kind, label in sec2_items:
                if y_curr > y1 - 15.0:
                    break
                if kind == "pump":
                    _draw_pump_sample(ctx, x0, y_curr)
                elif kind == "control_valve":
                    _draw_control_valve_sample(ctx, x0, y_curr)
                elif kind == "check_valve":
                    _draw_check_valve_sample(ctx, x0, y_curr)
                elif kind == "relief_valve":
                    _draw_relief_valve_sample(ctx, x0, y_curr)
                elif kind == "sampling_valve":
                    _draw_sampling_valve_sample(ctx, x0, y_curr)
                else:
                    _draw_isolation_valve_sample(ctx, x0, y_curr)
                ctx.text(
                    (x0 + 85, y_curr + 3.0),
                    text=label,
                    fontFamily="Arial",
                    textColor=(0, 0, 0, 255),
                    fontSize=6.5,
                    textAnchor="start",
                )
                y_curr += 26.0

            for entry in custom_sec2:
                if y_curr > y1 - 15.0:
                    break
                lbl = self._get_entry_label(entry)
                self._draw_custom_item(ctx, entry, x0, y_curr, lbl)
                y_curr += 26.0

            y_curr += 8.0

        # Draw Section 3 if instruments or custom entries exist
        if instruments or custom_sec3:
            y_curr = self._render_section_header(
                ctx, x0, y_curr, x1, "3. INSTRUMENTATION (ISA-5.1)"
            )
            if instruments:
                _draw_balloon_sample(ctx, x0, y_curr, tag_text=sample_tag_prefix)
                ctx.text(
                    (x0 + 85, y_curr + 3.0),
                    text="Field-Mounted Instrument Balloon",
                    fontFamily="Arial",
                    textColor=(0, 0, 0, 255),
                    fontSize=6.5,
                    textAnchor="start",
                )
                y_curr += 24.0

                # Render tag code table
                half = (len(detected_tags) + 1) // 2
                col1 = detected_tags[:half]
                col2 = detected_tags[half:]

                for idx in range(max(len(col1), len(col2))):
                    if y_curr > y1 - 15.0:
                        break
                    if idx < len(col1):
                        tag, desc = col1[idx]
                        ctx.text(
                            (x0 + 18, y_curr),
                            text=f"• {tag}:",
                            fontFamily="Arial",
                            textColor=(0, 0, 0, 255),
                            fontSize=6.0,
                            textAnchor="start",
                        )
                        ctx.text(
                            (x0 + 48, y_curr),
                            text=desc,
                            fontFamily="Arial",
                            textColor=(70, 70, 70, 255),
                            fontSize=5.5,
                            textAnchor="start",
                        )
                    if idx < len(col2):
                        tag, desc = col2[idx]
                        ctx.text(
                            (x0 + 190, y_curr),
                            text=f"• {tag}:",
                            fontFamily="Arial",
                            textColor=(0, 0, 0, 255),
                            fontSize=6.0,
                            textAnchor="start",
                        )
                        ctx.text(
                            (x0 + 225, y_curr),
                            text=desc,
                            fontFamily="Arial",
                            textColor=(70, 70, 70, 255),
                            fontSize=5.5,
                            textAnchor="start",
                        )
                    y_curr += 16.0

            for entry in custom_sec3:
                if y_curr > y1 - 15.0:
                    break
                lbl = self._get_entry_label(entry)
                self._draw_custom_item(ctx, entry, x0, y_curr, lbl)
                y_curr += 20.0

            y_curr += 8.0

        # Draw Section 4 if equipment or custom entries exist
        if sec4_items or custom_sec4:
            y_curr = self._render_section_header(ctx, x0, y_curr, x1, "4. MAJOR EQUIPMENT ICONS")
            for kind, label in sec4_items:
                if y_curr > y1 - 15.0:
                    break
                if kind == "mixer":
                    _draw_mixer_sample(ctx, x0, y_curr)
                elif kind == "daf":
                    _draw_daf_sample(ctx, x0, y_curr)
                elif kind == "membrane":
                    _draw_membrane_sample(ctx, x0, y_curr)
                elif kind == "vessel":
                    _draw_vessel_sample(ctx, x0, y_curr)
                elif kind == "horizontal_vessel":
                    _draw_horizontal_vessel_sample(ctx, x0, y_curr)
                elif kind == "jacketed_vessel":
                    _draw_jacketed_vessel_sample(ctx, x0, y_curr)
                elif kind == "exchanger":
                    _draw_exchanger_sample(ctx, x0, y_curr)
                elif kind == "distillation":
                    _draw_distillation_sample(ctx, x0, y_curr)
                else:
                    _draw_generic_equipment_sample(ctx, x0, y_curr, label=label)
                ctx.text(
                    (x0 + 85, y_curr + 3.0),
                    text=label,
                    fontFamily="Arial",
                    textColor=(0, 0, 0, 255),
                    fontSize=6.5,
                    textAnchor="start",
                )
                y_curr += 26.0

            for entry in custom_sec4:
                if y_curr > y1 - 15.0:
                    break
                lbl = self._get_entry_label(entry)
                self._draw_custom_item(ctx, entry, x0, y_curr, lbl)
                y_curr += 26.0

    def _render_section_header(self, ctx, x0: float, y: float, x1: float, title: str) -> float:
        ctx.text(
            (x0 + 10, y + 9.0),
            text=title,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=7.0,
            textAnchor="start",
        )
        ctx.line(
            (x0 + 10, y + 12.0),
            (x1 - 10, y + 12.0),
            lineColor=(200, 200, 200, 255),
            lineSize=0.5,
        )
        return y + 24.0

    def _normalize_section(self, raw_section: Any) -> int:
        if raw_section in (1, "1", "lines", "piping"):
            return 1
        if raw_section in (2, "2", "valves", "motive"):
            return 2
        if raw_section in (3, "3", "instruments", "instrumentation"):
            return 3
        if raw_section in (4, "4", "equipment"):
            return 4
        if isinstance(raw_section, str):
            s = raw_section.strip().upper()
            if "PIPING" in s or "STREAM" in s or "LINE" in s:
                return 1
            if "VALVE" in s or "MOTIVE" in s or "PUMP" in s:
                return 2
            if "INSTRUMENT" in s or "ISA" in s:
                return 3
            if "EQUIPMENT" in s:
                return 4
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

    def _draw_custom_item(self, ctx, entry: Any, x0: float, y: float, label: str) -> None:
        if isinstance(entry, dict) and callable(entry.get("draw")):
            entry["draw"](ctx, x0 + 45, y)
        else:
            sym = entry.get("symbol", "").lower() if isinstance(entry, dict) else ""
            if sym in ("line", "stream", "dashed"):
                _draw_line_sample(ctx, x0, y, line_type="process")
            elif sym in ("valve",):
                _draw_isolation_valve_sample(ctx, x0, y)
            elif sym in ("pump",):
                _draw_pump_sample(ctx, x0, y)
            elif sym in ("circle", "balloon"):
                _draw_balloon_sample(ctx, x0, y, tag_text="TAG")
            else:
                _draw_generic_equipment_sample(ctx, x0, y, label=label)

        ctx.text(
            (x0 + 85, y + 3.0),
            text=label,
            fontFamily="Arial",
            textColor=(0, 0, 0, 255),
            fontSize=6.5,
            textAnchor="start",
        )
