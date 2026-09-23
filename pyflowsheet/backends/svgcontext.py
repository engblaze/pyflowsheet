from __future__ import annotations

import re
from math import cos, radians, sin

import svgwrite

from .foreignObject import ForeignObject


def _sanitize_xml_id(raw_id: str) -> str:
    """Sanitizes an arbitrary string into a valid SVG/XML element ID.
    Valid XML IDs must not contain spaces, slashes, ampersands, or special characters.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", str(raw_id))
    # XML IDs must start with a letter or underscore
    if sanitized and (sanitized[0].isdigit() or sanitized[0] in "-."):
        sanitized = "_" + sanitized
    return sanitized


class SvgContext:
    def __init__(self, filename, backgroundColor=(255, 255, 255)):
        self.dwg = svgwrite.Drawing(filename, profile="full")
        self.g = None
        self.gstack = []
        self.bounds = [1e6, 1e6, 200, 200]

        self.marker = self._defineArrowheadMarker()

        if backgroundColor != None:
            self.dwg.attribs["style"] = f"background-color:rgb{backgroundColor[0:3]}"
        return

    def _defineArrowheadMarker(self):
        marker = self.dwg.marker(
            insert=(2, 2),
            orient="auto",
            size=(4, 4),
        )
        path = svgwrite.path.Path(
            stroke_width=1,
        )
        path.push("M0,0")
        path.push("V4")
        path.push("L2,2")
        path.push("Z")

        marker.add(path)
        self.dwg.defs.add(marker)
        return marker

    def _updateBounds(self, rect):
        x1 = rect[0][0] - 40
        x2 = rect[1][0] + 40
        y1 = rect[0][1] - 40
        y2 = rect[1][1] + 40

        if x1 < self.bounds[0]:
            self.bounds[0] = x1
        if x2 > self.bounds[2]:
            self.bounds[2] = x2
        if y1 < self.bounds[1]:
            self.bounds[1] = y1
        if y2 > self.bounds[3]:
            self.bounds[3] = y2

    def rectangle(self, rect, fillColor, lineColor: tuple[int, int, int, int], lineSize: float):
        self._updateBounds(rect)
        if fillColor == None:
            self.g.add(
                self.dwg.rect(
                    insert=rect[0],
                    size=(f"{rect[1][0] - rect[0][0]}", f"{rect[1][1] - rect[0][1]}"),
                    fill_opacity="0",
                    stroke=f"rgb{lineColor[0:3]}",
                    stroke_width=lineSize,
                )
            )
        else:
            self.g.add(
                self.dwg.rect(
                    insert=rect[0],
                    size=(f"{rect[1][0] - rect[0][0]}", f"{rect[1][1] - rect[0][1]}"),
                    fill=f"rgb{fillColor[0:3]}",
                    stroke=f"rgb{lineColor[0:3]}",
                    stroke_width=lineSize,
                )
            )
        return

    def circle(self, rect, fillColor, lineColor: tuple[int, int, int, int], lineSize: float):
        self._updateBounds(rect)
        center = ((rect[0][0] + rect[1][0]) / 2, (rect[0][1] + rect[1][1]) / 2)
        r = (rect[1][0] - rect[0][0]) / 2
        if fillColor == None:
            self.g.add(
                self.dwg.circle(
                    center=center,
                    r=r,
                    fill_opacity="0",
                    stroke=f"rgb{lineColor[0:3]}",
                    stroke_width=lineSize,
                )
            )
        else:
            self.g.add(
                self.dwg.circle(
                    center=center,
                    r=r,
                    fill=f"rgb{fillColor[0:3]}",
                    stroke=f"rgb{lineColor[0:3]}",
                    stroke_width=lineSize,
                )
            )
        return

    def text(
        self,
        position: tuple[float, float],
        text: str,
        fontFamily: str,
        textColor: tuple[int, int, int, int],
        fontSize: int = 12,
        textAnchor: str = "middle",
    ):
        self._updateBounds([position, (position[0] + 40, position[1] + 20)])
        self.g.add(
            self.dwg.text(
                text,
                insert=position,
                fill=f"rgb{textColor[0:3]}",
                font_family=fontFamily,
                text_anchor=textAnchor,
                font_size=fontSize,
            )
        )
        return

    def line(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        lineColor: tuple[int, int, int, int],
        lineSize: float,
    ):
        self._updateBounds([start, end])

        self.g.add(
            self.dwg.line(
                start=start,
                end=end,
                stroke=f"rgb{lineColor[0:3]}",
                stroke_width=lineSize,
            )
        )
        return

    def path(
        self,
        points,
        fillColor,
        lineColor: tuple[int, int, int, int],
        lineSize: float,
        close: bool = False,
        dashArray: str = None,
        endMarker: bool = False,
    ):

        minx = min([(p[0]) for p in points])
        maxx = max([(p[0]) for p in points])
        miny = min([(p[1]) for p in points])
        maxy = max([(p[1]) for p in points])

        self._updateBounds([(minx, miny), (maxx, maxy)])

        path = svgwrite.path.Path(
            stroke=f"rgb{lineColor[0:3]}",
            stroke_width=lineSize,
        )

        if fillColor != None:
            path.attribs["fill"] = f"rgb{fillColor[0:3]}"
        else:
            path.attribs["fill"] = "none"

        if dashArray != None:
            path.attribs["stroke-dasharray"] = dashArray

        path.push(f"M {points[0][0]} {points[0][1]} ")

        for p in points[1:]:
            path.push(f"L {p[0]} {p[1]} ")

        if close:
            path.push("Z")

        if endMarker:
            path.set_markers((None, False, self.marker))
        self.g.add(path)
        return

    def raw_path(
        self,
        d_string: str,
        fillColor=None,
        lineColor: tuple[int, int, int, int] = (0, 0, 0, 255),
        lineSize: float = 2.0,
        dashArray: str | None = None,
        endMarker: bool = False,
    ):
        """Appends an SVG path element with an explicit path data `d` attribute string."""
        path = svgwrite.path.Path(
            d=d_string,
            stroke=f"rgb{lineColor[0:3]}",
            stroke_width=lineSize,
        )
        if fillColor is not None:
            path.attribs["fill"] = f"rgb{fillColor[0:3]}"
        else:
            path.attribs["fill"] = "none"

        if dashArray is not None:
            path.attribs["stroke-dasharray"] = dashArray

        if endMarker:
            path.set_markers((None, False, self.marker))

        coords = [
            (float(x), float(y))
            for x, y in re.findall(r"[ML]\s*([-+]?\d*\.?\d+)[\s,]+([-+]?\d*\.?\d+)", d_string)
        ]
        if coords:
            minx = min(p[0] for p in coords)
            maxx = max(p[0] for p in coords)
            miny = min(p[1] for p in coords)
            maxy = max(p[1] for p in coords)
            self._updateBounds([(minx, miny), (maxx, maxy)])

        if self.g is not None:
            self.g.add(path)
        else:
            self.dwg.add(path)

    def chord(
        self,
        rect,
        startAngle: float,
        endAngle: float,
        fillColor,
        lineColor: tuple[int, int, int, int],
        lineSize: float,
        closePath=True,
    ):
        self._updateBounds(rect)

        p = svgwrite.path.Path(
            fill=f"rgb{fillColor[0:3]}" if fillColor else "none",
            stroke=f"rgb{lineColor[0:3]}",
            stroke_width=lineSize,
        )
        center = ((rect[0][0] + rect[1][0]) / 2, (rect[0][1] + rect[1][1]) / 2)
        rh = (rect[1][0] - rect[0][0]) / 2
        rv = (rect[1][1] - rect[0][1]) / 2

        start_rad = radians(startAngle)
        end_rad = radians(endAngle)

        start = (center[0] + rh * cos(start_rad), center[1] + rv * sin(start_rad))
        end = (center[0] + rh * cos(end_rad), center[1] + rv * sin(end_rad))

        direction = "+" if endAngle > startAngle else "-"
        largeArc = True if endAngle - startAngle >= 180 else False
        if closePath:
            p.push(f"M {center[0]} {center[1]} ")
            p.push(f"L {start[0]} {start[1]} ")
        else:
            p.push(f"M {start[0]} {start[1]} ")
        p.push_arc(end, 0, (rh, rv), largeArc, direction, True)
        if closePath:
            p.push("Z")
        self.g.add(p)
        return

    def startGroup(self, id: str, transform: str | None = None):
        if self.g is not None:
            self.gstack.append(self.g)

        safe_id = _sanitize_xml_id(id)
        self.g = self.dwg.g(id=safe_id)
        if transform:
            self.g.attribs["transform"] = transform

    def startTransformedGroup(self, element):
        if self.g is not None:
            self.gstack.append(self.g)

        safe_id = _sanitize_xml_id(element.id)
        self.g = self.dwg.g(id=safe_id + "_T")

        if element.isFlippedHorizontal:
            cx = element.position[0] + element.size[0] / 2
            self.g.attribs["transform"] = f"translate({cx},0) scale(-1,1) translate({-cx},0)"
        if element.isFlippedVertical:
            cy = element.position[1] + element.size[1] / 2
            self.g.attribs["transform"] = f"translate(0,{cy}) scale(1,-1) translate(0,{-cy})"

        if element.rotation != 0:
            cx = element.position[0] + element.size[0] / 2
            cy = element.position[1] + element.size[1] / 2
            self.g.attribs["transform"] = f"rotate({element.rotation},{cx},{cy} ) "
        return

    def endGroup(self):
        if len(self.gstack) > 0:
            parent = self.gstack.pop()
            parent.add(self.g)
            self.g = parent
        else:
            self.dwg.add(self.g)
            self.g = None
        return

    def html(self, html: str, position: tuple[float, float], size: tuple[float, float]):
        html = "<body width='100%'>" + html + "</body>"
        e = ForeignObject(
            html,
            x=f"{position[0]}",
            y=f"{position[1]}",
            width=f"{size[0]}",
            height=f"{size[1]}",
        )
        e.translate(0.2 * position[0], 0.2 * position[1])
        e.scale(0.8)

        self.g.add(e)
        return

    def image(self, image, position, size):
        """Add a bitmap image to the SVG drawing

        Args:
            image (str): base64 encoded representation of the image to be added
            position (Tuple[int,int]): Horizontal and vertical offset of the image
            size (Tuple[int,int]): Width and Height of the image
        """
        self.g.add(self.dwg.image(href=image, insert=position, size=size))
        return

    def render(self, width=None, height=None, scale=1, saveFile=True):
        """Write the content of the SVG drawing to a file and return the complete XML.
        By specifying width and height together, the user can change the aspect ratio
        of the drawing.

        Args:
            width (int optional): The width of rendered drawing in pixel. Defaults to None.
            height (int, optional): The height of rendered drawing in pixel. Defaults to None.
            scale (int, optional): A scaling factor than enlarges or shrinks the drawing.
                Can be defined in addition to width & height. Defaults to 1.
            saveFile (bool, optional): When true, the diagram is saved to file defined
                in the constructor of the SvgContext. Defaults to True.

        Returns:
            str: The string containing the xml representation of the diagram
        """

        while self.g is not None:
            self.endGroup()

        if width == None:
            width = self.bounds[2] - self.bounds[0]
        if height == None:
            height = self.bounds[3] - self.bounds[1]

        width = width * scale
        height = height * scale

        self.dwg.attribs["width"] = f"{width}px"
        self.dwg.attribs["height"] = f"{height}px"

        self.dwg.viewbox(
            self.bounds[0],
            self.bounds[1],
            self.bounds[2] - self.bounds[0],
            self.bounds[3] - self.bounds[1],
        )

        if saveFile:
            self.dwg.save()

        return self.dwg.tostring()
