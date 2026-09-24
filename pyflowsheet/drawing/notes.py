class GeneralNotes:
    """ASME General Notes Block in lower drawing field."""

    def __init__(
        self,
        notes: list[str] | None = None,
        rect: tuple[tuple[float, float], tuple[float, float]] = (
            (-30.0, 660.0),
            (860.0, 820.0),
        ),
    ):
        self.id = "drawing_notes"
        self.rect = rect
        if notes is not None:
            self.notes = list(notes)
        else:
            self.notes = [
                "ALL PROCESS PIPING SIZED FOR 100 M^3/HR NOMINAL LIQUID THROUGHPUT.",
                "INSTRUMENTATION TAGGING PER ISA-5.1 IDENTIFICATION STANDARD.",
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
        for idx, note in enumerate(self.notes):
            ny = y_text + idx * 16.0
            if ny > y1 - 20.0:
                break
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
                text=str(note),
                fontFamily="Arial",
                textColor=(50, 50, 50, 255),
                fontSize=6.0,
                textAnchor="start",
            )

        # Reference standards notice along bottom
        ctx.text(
            (x0 + 12, y1 - 8.0),
            text=(
                "STANDARDS APPLICABLE: ANSI/ASME Y14.1 (FORMAT), "
                "ISA-5.1 (INSTRUMENTATION), ASME B31.3 (PROCESS PIPING)."
            ),
            fontFamily="Arial",
            textColor=(100, 100, 100, 255),
            fontSize=5.5,
            textAnchor="start",
        )

        ctx.endGroup()
