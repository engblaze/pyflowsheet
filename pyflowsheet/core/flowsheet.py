from pathlib import Path
from typing import Any, TextIO

import yaml
from pathfinding.core.grid import Grid

from .stream import Stream


class Flowsheet:
    def __init__(self, id: str, name: str, description: str = ""):
        """Generates a new Flowsheet Object.

        The Flowsheet object represent a Process Flow Diagram (PFD). A Flowsheet
        is made up of unit operations, streams and annotations.

        Args:
            id (str): Short identifier of the flowsheet
            name (str): A human readable, longer name
            description (str, optional): A text describing the process task. Defaults to "".
        """
        self.id = id
        self.name = name
        self.description = description
        self.lineColor = (64, 64, 64, 255)
        self.fillColor = (255, 255, 255, 255)
        self.textColor = (0, 0, 0, 255)
        self.size = (512, 512)
        self.position = (0, 0)
        self.lineSize = 2
        self.unitOperations = {}
        self.annotations = []
        self.streams = {}
        self.showGrid = False
        self.showPorts = False
        self.tables = []
        self.settings = {}

    def addAnnotations(self, elements):
        for e in elements:
            self.annotations.append(e)
        return

    def addUnits(self, units):
        """Add a list of units to the flowsheet in one go.

        Args:
            units (List[UnitOperation]): A list of UnitOperation objects
        """
        for u in units:
            self.unitOperations[u.id] = u
        return

    def unit(self, unitoperation):
        """Add a new unit operation to the flowsheet and return a reference

        Raises:
            ValueError: If None is passed this function will raise a ValueError.
                        If the id of the UnitOperation is already present in the flowsheet
                        a value error will be raised.

        Returns:
            UnitOperation: The UnitOperation object passed into the function as an argument.
        """
        if unitoperation is None:
            raise ValueError(
                "unitoperation must be an object derived from the UnitOperation class!"
            )
        if unitoperation.id in self.unitOperations:
            raise ValueError(
                "The id of unitoperation is already used within the flowsheet. "
                "Please provide a unique id. If you want to override a specific unit operation, "
                "access it directly with the flowsheet.unitoperations[] accessor."
            )
        self.unitOperations[unitoperation.id] = unitoperation
        return unitoperation

    def connect(self, name, fromPort, toPort):
        """Connect two ports of two unit operations with a stream.

        Args:
            name (string): The identifier/name of the stream.
            fromPort (Port): The source port from which to route the stream
            toPort (Port): The destination port to which to route the stream
        """
        if name in self.streams:
            raise ValueError(
                "The id of the stream is already used within the flowsheet. "
                "Please provide a unique id. If you want to override a specific stream, "
                "access it directly with the flowsheet.streams[] accessor."
            )

        self.streams[name] = Stream(name, fromPort, toPort)
        return

    def _calcGrid(self):
        """Private helper function to rasterize canvas and generate course grid for pathfinding.
        This functions scans the entire canvas area and tests if a unit intersects the grid point.
        If any unit does so, the point is marked as "impassable" for pathfinding.

        Returns:
            [2d-list]: The reachability matrix of the canvas area
            [int]    : The minimum x coordinate of the canvas (upper-left)
            [int]    : The minimum y coordinate of the canvas (upper-left)
        """
        minx = min([u.position[0] for u in self.unitOperations.values()])
        maxx = max([u.position[0] + u.size[0] for u in self.unitOperations.values()])
        miny = min([u.position[1] for u in self.unitOperations.values()])
        maxy = max([u.position[1] + u.size[1] for u in self.unitOperations.values()])

        gridsize = 10

        minx = int(minx / gridsize - 8) * gridsize
        miny = int(miny / gridsize - 8) * gridsize
        maxx = int(maxx / gridsize + 8) * gridsize
        maxy = int(maxy / gridsize + 8) * gridsize

        grid = []

        for y in range(miny, maxy, gridsize):
            row = []
            for x in range(minx, maxx, gridsize):
                intersectionFound = False

                for u in self.unitOperations.values():
                    if u.intersectsPoint((x, y)):
                        intersectionFound = True

                if intersectionFound:
                    row.append(0)
                else:
                    row.append(1)
            grid.append(row)

        return grid, minx, miny

    def _drawGrid(self, grid, ctx, minx, miny):
        ctx.startGroup("RoutingGrid")

        for y in range(grid.height):
            for x in range(grid.width):
                sx = minx + x * 10
                sy = miny + y * 10
                if not grid.node(x, y).walkable:
                    ctx.circle(
                        [(sx - 5, sy - 5), (sx + 5, sy + 5)],
                        (0, 0, 0, 255),
                        (0, 0, 0, 255),
                        1,
                    )
                else:
                    w = int(max(255 - 10 * grid.node(x, y).weight, 0))
                    ctx.circle(
                        [(sx - 5, sy - 5), (sx + 5, sy + 5)],
                        (w, w, w, 255),
                        (0, 0, 0, 255),
                        1,
                    )

        ctx.endGroup()
        return

    def callout(self, text, position):
        from ..annotations import TextElement

        element = TextElement(text, position)
        self.annotations.append(element)
        return

    def draw(self, ctx):
        """Draws the process flow diagram with the help of the context passed as an argument.

        This function has 3 stages. In the first stage, the reachability map of the
        diagram is calculated, which is used in the second stage to route the streams
        using Dykstra's algorithm. In the third stage, the unit operations are drawn.

        The unit operation draw loop has two stages. In the first stage the icon is drawn with
        transformations applied. In the second stage the text layer is drawn without any
        transformations (i.e. rotation) applied.

        Args:
            ctx ([type]): A drawing context providing abstraction for primitive drawing functions.

        Returns:
            [type]: The same context as was passed in
        """

        matrix, minx, miny = self._calcGrid()
        grid = Grid(matrix=matrix)

        for s in self.streams.values():
            ctx.startGroup(s.id)
            s.draw(ctx, grid, minx, miny)
            ctx.endGroup()

        if self.showGrid:
            self._drawGrid(grid, ctx, minx, miny)

        # print(grid.grid_str(show_weight=True))
        for u in self.unitOperations.values():
            ctx.startGroup(u.id)
            ctx.startTransformedGroup(u)
            u.draw(ctx)
            ctx.endGroup()
            u.drawTextLayer(ctx, self.showPorts)
            ctx.endGroup()

        for e in self.annotations:
            ctx.startGroup(e.id)
            e.draw(ctx)
            e.drawTextLayer(ctx)
            ctx.endGroup()

        return ctx

    @classmethod
    def _from_schema(cls, schema: Any) -> "Flowsheet":
        """Builds a Flowsheet instance from an already validated FlowsheetSchema."""
        from ..schema import instantiate_unit

        flowsheet = cls(
            id=schema.metadata.id,
            name=schema.metadata.name,
            description=schema.metadata.description,
        )

        # 1. Instantiate all unit operations (equipment, stream flags, generic units)
        for eq in schema.components.all_units():
            unit = instantiate_unit(eq)
            flowsheet.unit(unit)

        # 2. Connect streams
        for s in schema.streams:
            from_unit = flowsheet.unitOperations[s.from_endpoint.unit]
            to_unit = flowsheet.unitOperations[s.to_endpoint.unit]

            from_port = from_unit[s.from_endpoint.port]
            to_port = to_unit[s.to_endpoint.port]

            flowsheet.connect(s.id, from_port, to_port)
            stream_obj = flowsheet.streams[s.id]

            if s.manual_routing:
                stream_obj.manualRouting = [tuple(pt) for pt in s.manual_routing]
            if s.label_offset != (0.0, 10.0):
                stream_obj.labelOffset = tuple(s.label_offset)

        # 3. Preserve tables and settings
        if getattr(schema, "tables", None):
            flowsheet.tables = [t.model_dump(by_alias=True) for t in schema.tables]
        else:
            flowsheet.tables = getattr(flowsheet, "tables", [])

        flowsheet.settings = dict(schema.settings)

        return flowsheet

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Flowsheet":
        """Builds and validates a Flowsheet instance from a Python dictionary specification."""
        from ..schema import validate_dict

        schema = validate_dict(data)
        return cls._from_schema(schema)

    @classmethod
    def from_yaml(cls, source: str | Path | TextIO) -> "Flowsheet":
        """Loads and validates a Flowsheet instance from a YAML string, filepath, or file stream."""
        from ..schema import validate_yaml_file, validate_yaml_string

        if isinstance(source, Path):
            schema = validate_yaml_file(source)
        elif isinstance(source, str):
            if "\n" in source or "\r" in source:
                schema = validate_yaml_string(source)
            elif source.lower().endswith((".yaml", ".yml")):
                schema = validate_yaml_file(Path(source))
            else:
                try:
                    path = Path(source)
                    is_file = path.is_file()
                except OSError:
                    is_file = False

                if is_file:
                    schema = validate_yaml_file(path)
                else:
                    schema = validate_yaml_string(source)
        elif hasattr(source, "read"):
            schema = validate_yaml_string(source.read())
        else:
            raise TypeError(f"Unsupported source type for from_yaml: {type(source)}")

        return cls._from_schema(schema)

    def to_dict(self) -> dict[str, Any]:
        """Serializes this Flowsheet into a dictionary conforming to FlowsheetSchema."""
        from ..core.enums import HorizontalLabelAlignment, VerticalLabelAlignment
        from ..unitoperations import StreamFlag

        equipment_list = []
        stream_flags_list = []

        rev_h = {
            HorizontalLabelAlignment.Center: "Center",
            HorizontalLabelAlignment.Left: "Left",
            HorizontalLabelAlignment.Right: "Right",
            HorizontalLabelAlignment.LeftOuter: "LeftOuter",
            HorizontalLabelAlignment.RightOuter: "RightOuter",
        }
        rev_v = {
            VerticalLabelAlignment.Center: "Center",
            VerticalLabelAlignment.Top: "Top",
            VerticalLabelAlignment.Bottom: "Bottom",
        }

        for u in self.unitOperations.values():
            u_data = {
                "id": u.id,
                "name": u.name,
                "type": u.__class__.__name__,
                "description": u.description,
                "position": [float(u.position[0]), float(u.position[1])],
                "size": [float(u.size[0]), float(u.size[1])],
                "rotation": float(u.rotation),
            }

            if hasattr(u, "capLength") and u.capLength is not None:
                u_data["cap_length"] = float(u.capLength)

            if u.internals:
                u_data["internals"] = [{"type": i.__class__.__name__} for i in u.internals]

            if u.ports:
                u_data["ports"] = [
                    {
                        "id": p.name,
                        "position": [float(p.relativePosition[0]), float(p.relativePosition[1])],
                        "normal": [float(p.normal[0]), float(p.normal[1])],
                        "intent": p.intent,
                    }
                    for p in u.ports.values()
                ]

            if (
                u.horizontalLabelAlignment != HorizontalLabelAlignment.Center
                or u.verticalLabelAlignment != VerticalLabelAlignment.Bottom
                or u.textOffset != (0, 20)
            ):
                u_data["text_anchor"] = {
                    "horizontal": rev_h.get(u.horizontalLabelAlignment, "Center"),
                    "vertical": rev_v.get(u.verticalLabelAlignment, "Bottom"),
                    "offset": [float(u.textOffset[0]), float(u.textOffset[1])],
                }

            if isinstance(u, StreamFlag):
                stream_flags_list.append(u_data)
            else:
                equipment_list.append(u_data)

        streams_list = []
        for s in self.streams.values():
            s_data = {
                "id": s.id,
                "from": {
                    "unit": s.fromPort.parent.id,
                    "port": s.fromPort.name,
                },
                "to": {
                    "unit": s.toPort.parent.id,
                    "port": s.toPort.name,
                },
            }
            if s.manualRouting:
                s_data["manual_routing"] = [[float(pt[0]), float(pt[1])] for pt in s.manualRouting]
            if s.labelOffset != (0, 10):
                s_data["label_offset"] = [float(s.labelOffset[0]), float(s.labelOffset[1])]
            streams_list.append(s_data)

        return {
            "schema_version": "1.0",
            "metadata": {
                "id": self.id,
                "name": self.name,
                "description": self.description,
            },
            "components": {
                "equipment": equipment_list,
                "stream_flags": stream_flags_list,
            },
            "streams": streams_list,
            "tables": getattr(self, "tables", []),
            "settings": getattr(self, "settings", {}),
        }

    def to_yaml(self, filepath: str | Path | None = None) -> str:
        """Serializes this Flowsheet into a YAML string, writing to filepath if provided."""
        data = self.to_dict()
        yaml_str = yaml.dump(data, sort_keys=False, default_flow_style=False, indent=2)
        if filepath is not None:
            Path(filepath).write_text(yaml_str, encoding="utf-8")
        return yaml_str
