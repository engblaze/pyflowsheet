from __future__ import annotations

import re
from dataclasses import dataclass

# Standard ISA-5.1 two-letter measured variable combinations
MULTI_LETTER_VARIABLES = {"PD", "TD", "FD", "LD", "FF", "TE", "TT", "PT", "LT", "FT"}


@dataclass
class ISATag:
    raw: str
    letters: str
    loop_number: str
    measured_variable: str = ""
    modifiers: str = ""
    functions: str = ""

    @property
    def display_top(self) -> str:
        return self.letters

    @property
    def display_bottom(self) -> str:
        return self.loop_number


def parse_isa_tag(tag_str: str) -> ISATag:
    """Parses an ANSI/ISA-5.1 tag string into functional letter components and loop numbers.

    Examples:
        'FIT-101'   -> letters='FIT', loop='101'
        'PDIT-203A' -> letters='PDIT', loop='203A', variable='PD', functions='IT'
        '10-LIC-204'-> letters='LIC', loop='10-204'
    """
    raw = tag_str.strip()

    # Match optional area prefix, letters, and loop identifier
    # Examples: 'FIT-101', '10-LIC-204', 'TI104', 'PCV_102'
    match = re.match(
        r"^(?:(\d+)[-_])?([A-Za-z]+)[-_]?([0-9]+[A-Za-z0-9]*)$",
        raw,
    )
    if match:
        area_prefix, letters_raw, loop_raw = match.groups()
        letters = letters_raw.upper()
        loop = f"{area_prefix}-{loop_raw}" if area_prefix else loop_raw

        # Decompose letters into variable and functions
        var = ""
        funcs = ""
        if len(letters) >= 2 and letters[:2] in MULTI_LETTER_VARIABLES:
            var = letters[:2]
            funcs = letters[2:]
        elif len(letters) >= 1:
            var = letters[:1]
            funcs = letters[1:]

        return ISATag(
            raw=raw,
            letters=letters,
            loop_number=loop,
            measured_variable=var,
            functions=funcs,
        )

    # Fallback for custom or non-standard tags (e.g. 'XY_CUSTOM')
    parts = re.split(r"[-_]", raw, maxsplit=1)
    if len(parts) == 2:
        return ISATag(raw=raw, letters=parts[0].upper(), loop_number=parts[1])
    return ISATag(raw=raw, letters=raw.upper(), loop_number="")
