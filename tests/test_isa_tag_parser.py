from pyflowsheet.instruments.tag import ISATag, parse_isa_tag


def test_parse_simple_flow_transmitter():
    tag = parse_isa_tag("FIT-101")
    assert isinstance(tag, ISATag)
    assert tag.raw == "FIT-101"
    assert tag.letters == "FIT"
    assert tag.loop_number == "101"
    assert tag.display_top == "FIT"
    assert tag.display_bottom == "101"
    assert tag.measured_variable == "F"
    assert tag.functions == "IT"


def test_parse_pressure_control_valve():
    tag = parse_isa_tag("PCV-102")
    assert tag.letters == "PCV"
    assert tag.loop_number == "102"
    assert tag.display_top == "PCV"
    assert tag.display_bottom == "102"
    assert tag.measured_variable == "P"
    assert tag.functions == "CV"


def test_parse_differential_pressure_indicator_transmitter():
    tag = parse_isa_tag("PDIT-203A")
    assert tag.letters == "PDIT"
    assert tag.loop_number == "203A"
    assert tag.display_top == "PDIT"
    assert tag.display_bottom == "203A"
    assert tag.measured_variable == "PD"
    assert tag.functions == "IT"


def test_parse_tag_without_hyphen():
    tag = parse_isa_tag("TI104")
    assert tag.letters == "TI"
    assert tag.loop_number == "104"
    assert tag.display_top == "TI"
    assert tag.display_bottom == "104"


def test_parse_tag_prefix_area():
    # E.g. Area 10 - LIC - 204
    tag = parse_isa_tag("10-LIC-204")
    assert tag.letters == "LIC"
    assert tag.loop_number == "10-204"
    assert tag.display_top == "LIC"
    assert tag.display_bottom == "10-204"


def test_invalid_or_fallback_tag():
    tag = parse_isa_tag("XY_CUSTOM")
    assert tag.raw == "XY_CUSTOM"
    assert tag.display_top == "XY"
    assert tag.display_bottom == "CUSTOM"
