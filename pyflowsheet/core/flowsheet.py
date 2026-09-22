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

    def connect(self, name, fromPort, toPort, line_type: str = "process"):
        """Connect two ports of two unit operations with a stream.

        Args:
            name (string): The identifier/name of the stream.
            fromPort (Port): The source port from which to route the stream
            toPort (Port): The destination port to which to route the stream
            line_type (string): ANSI/ISA-5.1 line type ('process', 'pneumatic',
                'electric', 'digital', 'capillary')
        """
        if name in self.streams:
            raise ValueError(
                "The id of the stream is already used within the flowsheet. "
                "Please provide a unique id. If you want to override a specific stream, "
                "access it directly with the flowsheet.streams[] accessor."
            )

        self.streams[name] = Stream(name, fromPort, toPort, line_type=line_type)
        return self.streams[name]

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

        has_unrouted = any(
            not s.calculated_route and len(s.manualRouting) == 0 for s in self.streams.values()
        )
        if (has_unrouted or self.showGrid) and len(self.unitOperations) > 0:
            matrix, minx, miny = self._calcGrid()
            grid = Grid(matrix=matrix)
        else:
            matrix, minx, miny = None, 0, 0
            grid = None

        for s in self.streams.values():
            ctx.startGroup(s.id)
            s.draw(ctx, grid, minx, miny)
            ctx.endGroup()

        if self.showGrid and grid is not None:
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

    def auto_layout(
        self,
        origin: tuple[float, float] = (60.0, 100.0),
        bay_width: float = 160.0,
        bay_height: float = 120.0,
        force_reposition: bool = False,
    ) -> None:
        """Executes automated two-tier macro layout, obstacle-avoiding orthogonal routing,
        stream crossover bridge detection, and collision-free label placement.
        """
        from collections import defaultdict

        from ..layout.crossover import CrossoverDetector
        from ..layout.inline import InlineSequencer
        from ..layout.labels import LabelPlacementSolver
        from ..layout.macro import MacroLayoutSolver
        from ..layout.router import OrthogonalRouter
        from ..layout.spatial import AABB, SpatialIndex

        # 1. Tier 1: Macro Layout
        units_spec = []
        for uid, u in self.unitOperations.items():
            pos = u.position
            if force_reposition and not (
                getattr(u, "fixed", False) or getattr(u, "is_fixed", False)
            ):
                pos = (0.0, 0.0)
            spec = {
                "id": uid,
                "size": u.size,
                "position": pos,
                "layout_hints": getattr(u, "layout_hints", None),
                "fixed": getattr(u, "fixed", False) or getattr(u, "is_fixed", False),
            }
            units_spec.append(spec)

        streams_spec = []
        for s in self.streams.values():
            u_from = getattr(s.fromPort, "unitoperation", getattr(s.fromPort, "parent", None))
            u_to = getattr(s.toPort, "unitoperation", getattr(s.toPort, "parent", None))
            from_id = u_from.id if u_from is not None else None
            to_id = u_to.id if u_to is not None else None
            if from_id and to_id:
                streams_spec.append((s.id, from_id, to_id))

        macro_solver = MacroLayoutSolver(
            units=units_spec,
            streams=streams_spec,
            origin=origin,
            bay_width=bay_width,
            bay_height=bay_height,
        )
        resolved_positions = macro_solver.solve()

        for uid, pos in resolved_positions.items():
            if uid in self.unitOperations:
                self.unitOperations[uid].position = pos

        # 2. Build Spatial Index of Equipment Obstacles
        spatial_index = SpatialIndex()
        for uid, u in self.unitOperations.items():
            box = AABB(
                u.position[0],
                u.position[1],
                u.position[0] + u.size[0],
                u.position[1] + u.size[1],
            )
            spatial_index.insert(uid, box, data=u)

        # 3. Tier 2: Orthogonal Routing
        obstacles = [item[1] for item in spatial_index.all_items()]
        router = OrthogonalRouter(grid_size=10.0, turn_penalty=60.0)

        routed_streams: dict[str, list[tuple[float, float]]] = {}
        for s in self.streams.values():
            if not s.manualRouting:
                p_start = s.fromPort.get_position()
                n_start = s.fromPort.normal
                p_end = s.toPort.get_position()
                n_end = s.toPort.normal

                route = router.route(
                    start=p_start,
                    start_normal=n_start,
                    end=p_end,
                    end_normal=n_end,
                    obstacles=obstacles,
                )
                s.calculated_route = route
                routed_streams[s.id] = route
            else:
                pts = [s.fromPort.get_position()]
                for step in s.manualRouting:
                    pts.append((pts[-1][0] + step[0], pts[-1][1] + step[1]))
                pts.append(s.toPort.get_position())
                s.calculated_route = pts
                routed_streams[s.id] = pts

        # 4. Stream Crossover Bridges
        crossover_detector = CrossoverDetector(bridge_radius=6.0)
        bridges = crossover_detector.find_crossings(routed_streams)
        bridges_by_stream: dict[str, list[Any]] = defaultdict(list)
        for b in bridges:
            bridges_by_stream[b.bridging_stream].append(b)

        for sid, stream_obj in self.streams.items():
            stream_obj.crossover_bridges = bridges_by_stream.get(sid, [])

        # 5. Inline Component Sequencing & Knockout Masks
        sequencer = InlineSequencer()
        for s in self.streams.values():
            s.knockout_masks = []
            seq = getattr(s, "line_sequence", None)
            if not seq and hasattr(s, "associated_components") and s.associated_components:
                if isinstance(s.associated_components, dict):
                    seq = s.associated_components.get("line_sequence", [])
                else:
                    seq = getattr(s.associated_components, "line_sequence", [])
            if seq and s.calculated_route:
                sizes = {uid: self.unitOperations[uid].size for uid in self.unitOperations}
                placements = sequencer.sequence(s.calculated_route, seq, sizes)
                for cid, placement in placements.items():
                    if cid in self.unitOperations:
                        u = self.unitOperations[cid]
                        u.position = (
                            placement.center[0] - u.size[0] / 2.0,
                            placement.center[1] - u.size[1] / 2.0,
                        )
                    s.knockout_masks.append(placement.knockout_box)

        # 6. Stream Label Positioning
        label_solver = LabelPlacementSolver()
        for s in self.streams.values():
            if len(s.calculated_route) >= 2 and s.labelOffset == (0, 10):
                try:
                    lw = max(len(s.id) * 8.0, 30.0)
                    pos, _ = label_solver.place_stream_label(
                        stream_id=s.id,
                        waypoints=s.calculated_route,
                        label_size=(lw, 12.0),
                        spatial_index=spatial_index,
                    )
                    start_pt = s.calculated_route[0]
                    s.labelOffset = (pos[0] - start_pt[0], pos[1] - start_pt[1])
                except Exception:
                    pass

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

            line_type = getattr(s, "line_type", "process")
            flowsheet.connect(s.id, from_port, to_port, line_type=line_type)
            stream_obj = flowsheet.streams[s.id]

            if s.manual_routing:
                stream_obj.manualRouting = [tuple(pt) for pt in s.manual_routing]
            if s.label_offset != (0.0, 10.0):
                stream_obj.labelOffset = tuple(s.label_offset)
            if getattr(s, "associated_components", None):
                stream_obj.associated_components = s.associated_components
                if hasattr(s.associated_components, "line_sequence"):
                    stream_obj.line_sequence = s.associated_components.line_sequence

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
            if hasattr(s, "line_type") and s.line_type:
                s_data["line_type"] = s.line_type
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
