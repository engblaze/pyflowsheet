import heapq
from math import pow

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.heuristic import null
from pathfinding.core.node import GridNode, Node
from pathfinding.core.util import SQRT2
from pathfinding.finder.a_star import AStarFinder

# Ensure Node and GridNode support index access (step[0], step[1]) across pathfinding versions
if not hasattr(Node, "__getitem__"):

    def _node_getitem(self, index):
        if hasattr(self, "x") and hasattr(self, "y"):
            if index == 0:
                return self.x
            elif index == 1:
                return self.y
            elif index == 2 and getattr(self, "grid_id", None) is not None:
                return self.grid_id
        raise IndexError(f"Node index {index} out of range")

    Node.__getitem__ = _node_getitem

if not hasattr(GridNode, "__getitem__"):

    def _gridnode_getitem(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        elif index == 2 and self.grid_id is not None:
            return self.grid_id
        raise IndexError(f"GridNode index {index} out of range")

    GridNode.__getitem__ = _gridnode_getitem


def distance(a, b):
    return pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2)


def compressPath(path):
    if len(path) < 2:
        return path
    deltaPath = []
    newPath = []

    newPath.append(path[0])

    for i, n in enumerate(path[1:]):
        deltaPath.append((n[0] - path[i][0], n[1] - path[i][1]))

    for i, delta in enumerate(deltaPath[1:]):
        lastDelta = deltaPath[i]
        if delta[0] != lastDelta[0] or delta[1] != lastDelta[1]:
            newPath.append(path[i + 1])
    newPath.append(path[-1])
    return newPath


def rectifyPath(path, grid, end):

    if len(path) < 2:
        return path

    newPath = []

    containsBends = True

    while containsBends:
        i = 0
        containsBends = False
        while i < len(path) - 2:
            if (
                path[i][0] == path[i + 1][0]
                and path[i][1] > path[i + 2][1]
                and path[i + 1][0] > path[i + 2][0]
            ):
                print("Up/Left-Bend detected")
                containsBends = True

                newNode = (path[i + 2][0], path[i][1])
                path.remove(path[i])
                path.remove(path[i])
                path.remove(path[i])
                path.insert(i, newNode)

            i += 1
    for n in path:
        newPath.append(n)
    # newPath.append(path[-2])
    # newPath.append(path[-1])
    # newPath.append(path[])

    return newPath


class Pathfinder(AStarFinder):
    def __init__(self, turnPenalty=150):
        super().__init__(diagonal_movement=DiagonalMovement.never, heuristic=null)

        self.turnPenalty = turnPenalty
        return

    def process_node(self, *args, **kwargs):
        """
        Check if the given node is part of the path by calculating its
        cost and add or remove it from our path.
        Supports both modern pathfinding (graph, node, parent, end, open_list, open_value)
        and legacy pathfinding (node, parent, end, open_list, open_value).
        """
        if len(args) >= 5 and hasattr(args[0], "calc_cost"):
            graph = args[0]
            node = args[1]
            parent = args[2]
            end = args[3]
            open_list = args[4]
            open_value = args[5] if len(args) > 5 else kwargs.get("open_value", True)
            ng = parent.g + graph.calc_cost(parent, node, self.weighted)
        else:
            graph = None
            node = args[0]
            parent = args[1]
            end = args[2]
            open_list = args[3]
            open_value = args[4] if len(args) > 4 else kwargs.get("open_value", True)
            ng = self.calc_cost(parent, node)

        lastDirection = (
            None
            if parent.parent is None
            else (parent.x - parent.parent.x, parent.y - parent.parent.y)
        )
        currentDirection = (node.x - parent.x, node.y - parent.y)
        turned = (
            0
            if lastDirection is None
            else (
                lastDirection[0] != currentDirection[0] or lastDirection[1] != currentDirection[1]
            )
        )

        ng += self.turnPenalty * turned

        if not node.opened or ng < node.g:
            node.g = ng
            if graph is not None:
                node.h = node.h or self.apply_heuristic(node, end, graph=graph)
            else:
                node.h = node.h or self.apply_heuristic(node, end) * self.weight
            # f is the estimated total cost from start to goal
            node.f = node.g + node.h
            node.parent = parent

            if hasattr(open_list, "push_node"):
                open_list.push_node(node)
                node.opened = open_value
            else:
                if not node.opened:
                    heapq.heappush(open_list, node)
                    node.opened = open_value
                else:
                    # the node can be reached with smaller cost.
                    # Since its f value has been updated, we have to
                    # update its position in the open list
                    open_list.remove(node)
                    heapq.heappush(open_list, node)

    def calc_cost(self, node_a, node_b):
        """
        get the distance between current node and the neighbor (cost)
        """
        if node_b.x - node_a.x == 0 or node_b.y - node_a.y == 0:
            # direct neighbor - distance is 1
            ng = 1
        else:
            # not a direct neighbor - diagonal movement
            ng = SQRT2

        # weight for weighted algorithms
        if self.weighted:
            ng *= node_b.weight

        return node_a.g + ng
