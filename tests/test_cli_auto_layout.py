from pathlib import Path

from pyflowsheet.cli import main


def test_cli_render_with_auto_layout(tmp_path: Path):
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "CLI_AUTO_TEST"
  name: "CLI Auto Layout"
components:
  equipment:
    - id: "V1"
      type: "Vessel"
    - id: "P1"
      type: "Pump"
    - id: "V2"
      type: "Vessel"
streams:
  - id: "S01"
    from:
      unit: "V1"
      port: "Out"
    to:
      unit: "P1"
      port: "In"
  - id: "S02"
    from:
      unit: "P1"
      port: "Out"
    to:
      unit: "V2"
      port: "In"
"""
    input_file = tmp_path / "flowsheet.yaml"
    output_file = tmp_path / "output.svg"
    input_file.write_text(yaml_content, encoding="utf-8")

    exit_code = main(["render", str(input_file), "-o", str(output_file), "--auto-layout"])
    assert exit_code == 0
    assert output_file.exists()
    svg_data = output_file.read_text(encoding="utf-8")
    assert "<svg" in svg_data
    assert "V1" in svg_data
    assert "P1" in svg_data
    assert "V2" in svg_data


def test_cli_render_with_auto_layout_and_flags(tmp_path: Path):
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "CLI_AUTO_FLAGS"
  name: "CLI Auto Layout With Flags"
components:
  equipment:
    - id: "T1"
      type: "Vessel"
    - id: "T2"
      type: "Vessel"
streams:
  - id: "S01"
    from:
      unit: "T1"
      port: "Out"
    to:
      unit: "T2"
      port: "In"
"""
    input_file = tmp_path / "flowsheet.yaml"
    output_file = tmp_path / "output_grid_ports.svg"
    input_file.write_text(yaml_content, encoding="utf-8")

    exit_code = main(
        [
            "render",
            str(input_file),
            "-o",
            str(output_file),
            "--auto-layout",
            "--show-grid",
            "--show-ports",
        ]
    )
    assert exit_code == 0
    assert output_file.exists()
    svg_data = output_file.read_text(encoding="utf-8")
    assert "<svg" in svg_data
    assert "RoutingGrid" in svg_data


def test_cli_render_auto_layout_with_hints(tmp_path: Path):
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "CLI_HINTS"
  name: "CLI Layout Hints"
components:
  equipment:
    - id: "R1"
      type: "Vessel"
      layout_hints:
        stage: 0
    - id: "R2"
      type: "Vessel"
      layout_hints:
        stage: 2
streams:
  - id: "S01"
    from:
      unit: "R1"
      port: "Out"
    to:
      unit: "R2"
      port: "In"
"""
    input_file = tmp_path / "hints.yaml"
    output_file = tmp_path / "hints.svg"
    input_file.write_text(yaml_content, encoding="utf-8")

    exit_code = main(["render", str(input_file), "-o", str(output_file), "--auto-layout"])
    assert exit_code == 0
    assert output_file.exists()
    svg_data = output_file.read_text(encoding="utf-8")
    assert "<svg" in svg_data
    assert "R1" in svg_data
    assert "R2" in svg_data


def test_cli_render_auto_layout_error_handled(tmp_path: Path, monkeypatch, capsys):
    yaml_content = """
schema_version: "1.0"
metadata:
  id: "CLI_ERR"
  name: "CLI Err"
components:
  equipment:
    - id: "E1"
      type: "Vessel"
"""
    input_file = tmp_path / "err.yaml"
    output_file = tmp_path / "err.svg"
    input_file.write_text(yaml_content, encoding="utf-8")

    def mock_auto_layout(*args, **kwargs):
        raise RuntimeError("Layout solver exploded")

    monkeypatch.setattr("pyflowsheet.core.flowsheet.Flowsheet.auto_layout", mock_auto_layout)

    exit_code = main(["render", str(input_file), "-o", str(output_file), "--auto-layout"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error rendering" in captured.err
    assert "Layout solver exploded" in captured.err
