from typing import Dict, List

from app.knowledge.exceptions import CircularReferenceError


def check_for_cycles(edges: Dict[str, List[str]]) -> None:
    """Raise CircularReferenceError if the directed graph in `edges` has a cycle.

    `edges` maps a node key to the node keys it depends on. The knowledge base
    hierarchy (vendor -> product -> edition -> module -> capability/framework)
    is acyclic by construction, but this guard runs on every import so a
    malformed batch (e.g. a copy-paste error creating an indirect loop) is
    rejected instead of silently corrupting data.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {node: WHITE for node in edges}
    path: List[str] = []

    def visit(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in edges.get(node, []):
            color.setdefault(neighbor, WHITE)
            state = color[neighbor]
            if state == GRAY:
                cycle_start = path.index(neighbor)
                raise CircularReferenceError(path[cycle_start:] + [neighbor])
            if state == WHITE:
                visit(neighbor)
        path.pop()
        color[node] = BLACK

    for node in list(edges):
        if color[node] == WHITE:
            visit(node)
