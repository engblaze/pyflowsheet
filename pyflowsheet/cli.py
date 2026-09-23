import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .backends import SvgContext
from .core import Flowsheet
from .schema import FlowsheetSchema, FlowsheetValidationError, validate_yaml_file


def render_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file not found: {input_path}\n")
        return 1

    output_path = Path(args.output) if args.output else input_path.with_suffix(".svg")

    try:
        flowsheet = Flowsheet.from_yaml(input_path)
    except FlowsheetValidationError as e:
        sys.stderr.write(f"Validation error in '{input_path}':\n{e}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Error loading '{input_path}': {e}\n")
        return 1

    flowsheet.showGrid = args.show_grid
    flowsheet.showPorts = args.show_ports

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        force_reposition = getattr(args, "force_reposition", False)
        if getattr(args, "auto_layout", False) or force_reposition:
            flowsheet.auto_layout(force_reposition=force_reposition)

        ctx = SvgContext(str(output_path))
        flowsheet.draw(ctx)
        ctx.render(saveFile=True)
    except Exception as e:
        sys.stderr.write(f"Error rendering '{input_path}': {e}\n")
        return 1

    print(f"✓ Rendered flowsheet '{flowsheet.id}' to {output_path}")
    return 0


def validate_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file not found: {input_path}\n")
        return 1

    try:
        schema = validate_yaml_file(input_path)
    except FlowsheetValidationError as e:
        sys.stderr.write(f"✗ Validation error in '{input_path}':\n{e}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"✗ Error validating '{input_path}': {e}\n")
        return 1

    units_count = len(schema.components.all_units())
    streams_count = len(schema.streams)
    tables_count = len(schema.tables)

    print(f"✓ Specification is valid: {input_path}")
    print(f"  ID: {schema.metadata.id}")
    print(f"  Name: {schema.metadata.name}")
    print(f"  Units: {units_count} | Streams: {streams_count} | Tables: {tables_count}")
    return 0


def export_schema_command(args: argparse.Namespace) -> int:
    schema_json = FlowsheetSchema.model_json_schema()
    formatted = json.dumps(schema_json, indent=args.indent)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(formatted, encoding="utf-8")
        print(f"✓ Exported Flowsheet JSON Schema to {out_path}")
    else:
        sys.stdout.write(formatted + "\n")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pyflowsheet",
        description=(
            "Pyflowsheet CLI: Process Flow Diagram compiler, validator, and schema exporter"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # render
    render_parser = subparsers.add_parser("render", help="Render a YAML flowsheet to SVG")
    render_parser.add_argument("input", help="Path to input YAML flowsheet file")
    render_parser.add_argument("-o", "--output", help="Path to destination SVG file")
    render_parser.add_argument(
        "--show-grid", action="store_true", help="Display the routing collision grid"
    )
    render_parser.add_argument(
        "--show-ports", action="store_true", help="Display port connection dots on units"
    )
    render_parser.add_argument(
        "--auto-layout",
        action="store_true",
        help="Automatically compute macro equipment positions and orthogonal stream routing.",
    )
    render_parser.add_argument(
        "--force-reposition",
        action="store_true",
        help="Force recalculation of equipment positions, overriding explicit YAML coordinates.",
    )

    # validate
    validate_parser = subparsers.add_parser(
        "validate", help="Validate a YAML flowsheet specification"
    )
    validate_parser.add_argument("input", help="Path to input YAML flowsheet file")

    # export-schema
    schema_parser = subparsers.add_parser(
        "export-schema", help="Export Pydantic JSON Schema for IDE validation"
    )
    schema_parser.add_argument(
        "-o",
        "--output",
        help="Path to output JSON schema file (prints to stdout if omitted)",
    )
    schema_parser.add_argument("--indent", type=int, default=2, help="Indentation for JSON output")

    parsed_args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if parsed_args.command == "render":
        return render_command(parsed_args)
    elif parsed_args.command == "validate":
        return validate_command(parsed_args)
    elif parsed_args.command == "export-schema":
        return export_schema_command(parsed_args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
