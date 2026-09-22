import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pyflowsheet import Flowsheet, StreamFlag, SvgContext, Vessel


def test_flowsheet_from_dict_and_to_dict_roundtrip():
    data = {
        "schema_version": "1.0",
        "metadata": {
            "id": "ROUNDTRIP_TEST",
            "name": "Roundtrip Flowsheet",
            "description": "Testing serialization roundtrip",
        },
        "components": {
            "equipment": [
                {
                    "id": "V1",
                    "name": "Feed Tank",
                    "type": "Vessel",
                    "position": [100.0, 100.0],
                    "size": [40.0, 80.0],
                },
                {
                    "id": "V2",
                    "name": "Product Tank",
                    "type": "Vessel",
                    "position": [300.0, 100.0],
                    "size": [40.0, 80.0],
                },
            ]
        },
        "streams": [
            {
                "id": "S1",
                "from": {"unit": "V1", "port": "Out"},
                "to": {"unit": "V2", "port": "In"},
                "manual_routing": [[20.0, 0.0], [0.0, 50.0]],
            }
        ],
    }

    pfd = Flowsheet.from_dict(data)
    assert pfd.id == "ROUNDTRIP_TEST"
    assert len(pfd.unitOperations) == 2
    assert isinstance(pfd.unitOperations["V1"], Vessel)
    assert isinstance(pfd.unitOperations["V2"], Vessel)
    assert "S1" in pfd.streams
    assert pfd.streams["S1"].manualRouting == [(20.0, 0.0), (0.0, 50.0)]

    exported = pfd.to_dict()
    assert exported["metadata"]["id"] == "ROUNDTRIP_TEST"
    assert len(exported["components"]["equipment"]) == 2
    assert len(exported["streams"]) == 1
    assert exported["streams"][0]["id"] == "S1"


def test_flowsheet_from_yaml_file_and_to_yaml(tmp_path):
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "FILE_TEST"
  name: "File Test Flowsheet"
components:
  equipment:
    - id: "V101"
      name: "Reactor"
      type: "Vessel"
      position: [100, 100]
  stream_flags:
    - id: "Feed"
      name: "Raw Feed"
      type: "StreamFlag"
      position: [20, 100]
streams:
  - id: "S01"
    from: { unit: "Feed", port: "Out" }
    to: { unit: "V101", port: "In" }
"""
    yaml_file = tmp_path / "test_flowsheet.yaml"
    yaml_file.write_text(yaml_content, encoding="utf-8")

    pfd = Flowsheet.from_yaml(yaml_file)
    assert pfd.id == "FILE_TEST"
    assert "V101" in pfd.unitOperations
    assert isinstance(pfd.unitOperations["V101"], Vessel)
    assert "Feed" in pfd.unitOperations
    assert isinstance(pfd.unitOperations["Feed"], StreamFlag)
    assert "S01" in pfd.streams

    out_yaml = tmp_path / "out_flowsheet.yaml"
    pfd.to_yaml(out_yaml)
    assert out_yaml.exists()

    reloaded = Flowsheet.from_yaml(Path(out_yaml))
    assert reloaded.id == "FILE_TEST"


def test_load_water_treatment_v2_yaml_and_render(tmp_path):
    pfd = Flowsheet.from_yaml("examples/water_treatment_flowsheet_v2.yaml")
    assert pfd.id == "WATER_TREATMENT_V2"
    assert len(pfd.unitOperations) == 8  # 4 equipment + 4 stream flags
    assert len(pfd.streams) == 9

    out_svg = str(tmp_path / "water_treatment.svg")
    ctx = SvgContext(out_svg)
    pfd.draw(ctx)
    svg_str = ctx.render(saveFile=True)

    root = ET.fromstring(svg_str)
    assert root.tag.endswith("svg")


def test_flowsheet_from_yaml_invalid_type():
    with pytest.raises(TypeError, match="Unsupported source type for from_yaml"):
        Flowsheet.from_yaml(12345)
