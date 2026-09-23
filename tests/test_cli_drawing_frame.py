from pathlib import Path

import pytest

from pyflowsheet.cli import main


def test_cli_render_with_drawing_frame(tmp_path: Path):
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(
        """
schema_version: "1.0"
metadata:
  id: "CLI_TEST"
  title: "CLI TEST FLOWSHEET"
  drawing_number: "DWG-CLI-01"
  sheet_size: "D"
components:
  equipment: []
streams: []
""",
        encoding="utf-8",
    )
    svg_file = tmp_path / "output.svg"

    ret = main(["render", str(yaml_file), "-o", str(svg_file)])
    assert ret == 0
    content = svg_file.read_text(encoding="utf-8")
    assert 'id="drawing_border"' in content
    assert 'id="title_block"' in content


def test_cli_render_with_no_drawing_frame(tmp_path: Path):
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(
        """
schema_version: "1.0"
metadata:
  id: "CLI_TEST"
  title: "CLI TEST FLOWSHEET"
  drawing_number: "DWG-CLI-01"
  sheet_size: "D"
components:
  equipment: []
streams: []
""",
        encoding="utf-8",
    )
    svg_file = tmp_path / "output_no_frame.svg"

    ret = main(["render", str(yaml_file), "-o", str(svg_file), "--no-drawing-frame"])
    assert ret == 0
    content = svg_file.read_text(encoding="utf-8")
    assert 'id="drawing_border"' not in content
    assert 'id="title_block"' not in content


def test_cli_render_explicit_drawing_frame_flag(tmp_path: Path):
    yaml_file = tmp_path / "plain.yaml"
    yaml_file.write_text(
        """
schema_version: "1.0"
metadata:
  id: "PLAIN_TEST"
  name: "Plain Flowsheet"
components:
  equipment: []
streams: []
""",
        encoding="utf-8",
    )
    svg_file = tmp_path / "plain_with_frame.svg"

    ret = main(["render", str(yaml_file), "-o", str(svg_file), "--drawing-frame"])
    assert ret == 0
    content = svg_file.read_text(encoding="utf-8")
    assert 'id="drawing_border"' in content
    assert 'id="title_block"' in content


def test_cli_render_explicit_drawing_frame_with_metadata(tmp_path: Path):
    yaml_file = tmp_path / "meta.yaml"
    yaml_file.write_text(
        """
schema_version: "1.0"
metadata:
  id: "META_TEST"
  title: "META FLOWSHEET"
  drawing_number: "DWG-META-02"
  sheet_size: "C"
components:
  equipment: []
streams: []
""",
        encoding="utf-8",
    )
    svg_file = tmp_path / "meta_with_frame.svg"

    ret = main(["render", str(yaml_file), "-o", str(svg_file), "--drawing-frame"])
    assert ret == 0
    content = svg_file.read_text(encoding="utf-8")
    assert 'id="drawing_border"' in content
    assert 'id="title_block"' in content
    assert "DWG-META-02" in content


def test_cli_render_no_drawing_frame_on_plain_yaml(tmp_path: Path):
    yaml_file = tmp_path / "plain2.yaml"
    yaml_file.write_text(
        """
schema_version: "1.0"
metadata:
  id: "PLAIN_2"
  name: "Plain 2"
components:
  equipment: []
streams: []
""",
        encoding="utf-8",
    )
    svg_file = tmp_path / "plain_no_frame.svg"

    ret = main(["render", str(yaml_file), "-o", str(svg_file), "--no-drawing-frame"])
    assert ret == 0
    content = svg_file.read_text(encoding="utf-8")
    assert 'id="drawing_border"' not in content
    assert 'id="title_block"' not in content


def test_cli_help_includes_drawing_frame_options(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc_info:
        main(["render", "--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "--drawing-frame" in captured.out
    assert "--no-drawing-frame" in captured.out
