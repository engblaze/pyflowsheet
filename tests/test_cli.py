import json

from pyflowsheet.cli import main


def test_cli_no_args(capsys):
    ret = main([])
    assert ret == 0
    captured = capsys.readouterr()
    assert "usage: pyflowsheet" in captured.out


def test_cli_validate_valid_file(capsys):
    ret = main(["validate", "examples/water_treatment_flowsheet_v2.yaml"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Specification is valid" in captured.out
    assert "WATER_TREATMENT_V2" in captured.out


def test_cli_validate_invalid_file(tmp_path, capsys):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        """
schema_version: "1.0"
components:
  equipment:
    - id: "E1"
      type: "Vessel"
streams:
  - id: "S1"
    from: { unit: "E1", port: "Out" }
    to: { unit: "MISSING", port: "In" }
""",
        encoding="utf-8",
    )
    ret = main(["validate", str(bad_yaml)])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Validation error" in captured.err or "Validation error" in captured.out


def test_cli_validate_missing_file(capsys):
    ret = main(["validate", "nonexistent_file.yaml"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Input file not found" in captured.err


def test_cli_validate_syntax_error(tmp_path, capsys):
    broken_yaml = tmp_path / "broken.yaml"
    broken_yaml.write_text(": - invalid yaml :", encoding="utf-8")
    ret = main(["validate", str(broken_yaml)])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Validation error" in captured.err
    assert "Invalid YAML syntax" in captured.err


def test_cli_validate_unexpected_exception(tmp_path, monkeypatch, capsys):
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("schema_version: '1.0'", encoding="utf-8")

    def mock_validate(path):
        raise RuntimeError("Disk failure")

    monkeypatch.setattr("pyflowsheet.cli.validate_yaml_file", mock_validate)
    ret = main(["validate", str(yaml_file)])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error validating" in captured.err
    assert "Disk failure" in captured.err


def test_cli_render_creates_svg(tmp_path, capsys):
    out_svg = tmp_path / "output.svg"
    ret = main(["render", "examples/water_treatment_flowsheet_v2.yaml", "-o", str(out_svg)])
    assert ret == 0
    assert out_svg.exists()
    assert "<svg" in out_svg.read_text(encoding="utf-8")


def test_cli_render_missing_file(capsys):
    ret = main(["render", "nonexistent_file.yaml"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Input file not found" in captured.err


def test_cli_render_invalid_file(tmp_path, capsys):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        """
schema_version: "1.0"
components:
  equipment:
    - id: "E1"
      type: "Vessel"
streams:
  - id: "S1"
    from: { unit: "E1", port: "Out" }
    to: { unit: "MISSING", port: "In" }
""",
        encoding="utf-8",
    )
    ret = main(["render", str(bad_yaml)])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Validation error" in captured.err


def test_cli_render_syntax_error(tmp_path, capsys):
    broken_yaml = tmp_path / "broken.yaml"
    broken_yaml.write_text(": - invalid yaml :", encoding="utf-8")
    ret = main(["render", str(broken_yaml)])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Validation error" in captured.err
    assert "Invalid YAML syntax" in captured.err


def test_cli_render_unexpected_exception(tmp_path, monkeypatch, capsys):
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("schema_version: '1.0'", encoding="utf-8")

    def mock_from_yaml(path):
        raise RuntimeError("Render failure")

    monkeypatch.setattr("pyflowsheet.cli.Flowsheet.from_yaml", mock_from_yaml)
    ret = main(["render", str(yaml_file)])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error loading" in captured.err
    assert "Render failure" in captured.err


def test_cli_export_schema(tmp_path, capsys):
    out_schema = tmp_path / "flowsheet.schema.json"
    ret = main(["export-schema", "-o", str(out_schema)])
    assert ret == 0
    assert out_schema.exists()

    schema_data = json.loads(out_schema.read_text(encoding="utf-8"))
    assert "$defs" in schema_data or "properties" in schema_data
    assert "schema_version" in schema_data.get("properties", {})


def test_cli_export_schema_stdout(capsys):
    ret = main(["export-schema"])
    assert ret == 0
    captured = capsys.readouterr()
    schema_data = json.loads(captured.out)
    assert "schema_version" in schema_data.get("properties", {})
