from __future__ import annotations

from typing import Literal

from ..core import Port
from .bodies import BaseValve

ActuatorKind = Literal["manual", "pneumatic", "electric", "solenoid", "piston"]
ActuatorType = ActuatorKind
FailureKind = Literal["none", "fail_closed", "fail_open", "fail_locked", "fail_indeterminate"]
FailureMode = FailureKind


class ControlValve(BaseValve):
    """ANSI/ISA-5.1 composite control valve consisting of a valve body, stem,
    actuator symbol (manual, pneumatic diaphragm, electric motor, solenoid, or piston),
    and failure mode indicator arrow/marker.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        body_type: str = "globe",
        actuator: ActuatorKind = "pneumatic",
        failure_mode: FailureKind = "fail_closed",
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] = (30.0, 20.0),
        actuator_height: float = 24.0,
        description: str = "",
    ):
        self.body_type = body_type.lower()
        self.actuator = actuator.lower()
        self.failure_mode = failure_mode.lower()
        self.actuator_height = actuator_height
        super().__init__(id, name or id, position=position, size=size, description=description)
        self.updatePorts()

    def updatePorts(self) -> None:
        super().updatePorts()
        # Top actuator connection port for signal line
        act_height = getattr(self, "actuator_height", 24.0)
        act_y_rel = -(act_height * 1.1) / self.size[1]
        self.ports["Actuator"] = Port("Actuator", self, (0.5, act_y_rel), (0, -1))
        self.ports["Signal"] = Port("Signal", self, (0.5, act_y_rel), (0, -1))

    def _draw_actuator(self, ctx, cx: float, stem_top: float) -> None:
        w, _ = self.size
        aw = w * 0.9
        ah = self.actuator_height * 0.7
        act_top = stem_top - ah

        if self.actuator == "pneumatic":
            # Diaphragm dome (semicircle or dome)
            ctx.chord(
                [(cx - aw / 2.0, act_top), (cx + aw / 2.0, stem_top + ah * 0.2)],
                180,
                360,
                self.fillColor,
                self.lineColor,
                self.lineSize,
                closePath=True,
            )
        elif self.actuator == "electric":
            # Circle with 'M' (motor)
            r = ah / 2.0
            ctx.circle(
                [(cx - r, stem_top - ah), (cx + r, stem_top)],
                self.fillColor,
                self.lineColor,
                self.lineSize,
            )
            ctx.text(
                (cx, stem_top - ah / 2.0 + 3.0),
                text="M",
                fontFamily=self.fontFamily,
                textColor=self.textColor,
                fontSize=9,
                textAnchor="middle",
            )
        elif self.actuator == "solenoid":
            # Rectangle with 'S'
            ctx.rectangle(
                [(cx - aw / 2.0, act_top), (cx + aw / 2.0, stem_top)],
                self.fillColor,
                self.lineColor,
                self.lineSize,
            )
            ctx.text(
                (cx, stem_top - ah / 2.0 + 3.0),
                text="S",
                fontFamily=self.fontFamily,
                textColor=self.textColor,
                fontSize=9,
                textAnchor="middle",
            )
        elif self.actuator == "piston":
            # Cylinder box
            ctx.rectangle(
                [(cx - aw / 2.0, act_top), (cx + aw / 2.0, stem_top)],
                self.fillColor,
                self.lineColor,
                self.lineSize,
            )
            ctx.line(
                (cx - aw / 2.0, stem_top - ah / 2.0),
                (cx + aw / 2.0, stem_top - ah / 2.0),
                self.lineColor,
                1.0,
            )
        elif self.actuator == "manual":
            # T-handle / handwheel
            ctx.line((cx, stem_top), (cx, act_top), self.lineColor, self.lineSize)
            ctx.line(
                (cx - aw / 2.0, act_top),
                (cx + aw / 2.0, act_top),
                self.lineColor,
                self.lineSize * 1.5,
            )

    def _draw_failure_mode(self, ctx, cx: float, stem_mid: float) -> None:
        arm = 4.0
        if self.failure_mode == "fail_closed":
            # Down arrow
            ctx.line((cx, stem_mid - arm), (cx, stem_mid + arm), self.lineColor, self.lineSize)
            ctx.line(
                (cx - 3, stem_mid + arm - 3),
                (cx, stem_mid + arm),
                self.lineColor,
                self.lineSize,
            )
            ctx.line(
                (cx + 3, stem_mid + arm - 3),
                (cx, stem_mid + arm),
                self.lineColor,
                self.lineSize,
            )
        elif self.failure_mode == "fail_open":
            # Up arrow
            ctx.line((cx, stem_mid - arm), (cx, stem_mid + arm), self.lineColor, self.lineSize)
            ctx.line(
                (cx - 3, stem_mid - arm + 3),
                (cx, stem_mid - arm),
                self.lineColor,
                self.lineSize,
            )
            ctx.line(
                (cx + 3, stem_mid - arm + 3),
                (cx, stem_mid - arm),
                self.lineColor,
                self.lineSize,
            )
        elif self.failure_mode == "fail_locked":
            # Cross (X)
            ctx.line((cx - 3, stem_mid - 3), (cx + 3, stem_mid + 3), self.lineColor, self.lineSize)
            ctx.line((cx - 3, stem_mid + 3), (cx + 3, stem_mid - 3), self.lineColor, self.lineSize)
        elif self.failure_mode == "fail_indeterminate":
            # Bidirectional arrows
            ctx.line((cx, stem_mid - arm), (cx, stem_mid + arm), self.lineColor, self.lineSize)
            ctx.line(
                (cx - 3, stem_mid - arm + 3),
                (cx, stem_mid - arm),
                self.lineColor,
                self.lineSize,
            )
            ctx.line(
                (cx + 3, stem_mid - arm + 3),
                (cx, stem_mid - arm),
                self.lineColor,
                self.lineSize,
            )
            ctx.line(
                (cx - 3, stem_mid + arm - 3),
                (cx, stem_mid + arm),
                self.lineColor,
                self.lineSize,
            )
            ctx.line(
                (cx + 3, stem_mid + arm - 3),
                (cx, stem_mid + arm),
                self.lineColor,
                self.lineSize,
            )

    def draw(self, ctx) -> None:
        # 1. Draw valve body
        self._draw_opposing_triangles(ctx)
        x, y = self.position
        w, h = self.size
        cx = x + w / 2.0
        cy = y + h / 2.0

        if self.body_type == "globe":
            r = min(w, h) * 0.22
            ctx.circle(
                [(cx - r, cy - r), (cx + r, cy + r)],
                self.lineColor,
                self.lineColor,
                self.lineSize,
            )
        elif self.body_type == "ball":
            r = min(w, h) * 0.25
            ctx.circle(
                [(cx - r, cy - r), (cx + r, cy + r)],
                self.fillColor,
                self.lineColor,
                self.lineSize,
            )
        elif self.body_type == "butterfly":
            r = min(w, h) * 0.4
            ctx.line(
                (cx - r * 0.6, cy + r),
                (cx + r * 0.6, cy - r),
                self.lineColor,
                self.lineSize * 1.5,
            )
        elif self.body_type == "needle":
            needle_top = (cx, y - h * 0.2)
            needle_tip = (cx, cy + h * 0.3)
            ctx.line(needle_top, needle_tip, self.lineColor, self.lineSize)
            ctx.line((cx - 3, cy + 2), needle_tip, self.lineColor, self.lineSize)
            ctx.line((cx + 3, cy + 2), needle_tip, self.lineColor, self.lineSize)
        elif self.body_type == "diaphragm":
            ctx.chord(
                [(cx - w * 0.25, y - h * 0.2), (cx + w * 0.25, cy)],
                180,
                360,
                self.fillColor,
                self.lineColor,
                self.lineSize,
                closePath=True,
            )
        elif self.body_type == "plug":
            pw, ph = w * 0.2, h * 0.7
            ctx.rectangle(
                [(cx - pw / 2.0, cy - ph / 2.0), (cx + pw / 2.0, cy + ph / 2.0)],
                self.fillColor,
                self.lineColor,
                self.lineSize,
            )
        elif self.body_type == "check":
            ctx.line((cx, y), (cx, y + h), self.lineColor, self.lineSize * 1.5)

        # 2. Draw stem from body to actuator
        stem_top = y - self.actuator_height * 0.4
        ctx.line((cx, cy), (cx, stem_top), self.lineColor, self.lineSize)

        # 3. Draw actuator symbol
        self._draw_actuator(ctx, cx, stem_top)

        # 4. Draw failure mode indicator
        stem_mid = (y + stem_top) / 2.0
        self._draw_failure_mode(ctx, cx, stem_mid)

        super().draw(ctx)


__all__ = [
    "ActuatorKind",
    "ActuatorType",
    "ControlValve",
    "FailureKind",
    "FailureMode",
]
