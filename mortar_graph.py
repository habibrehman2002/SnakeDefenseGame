import pygame
from collections import defaultdict
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, SKY_HEIGHT, BRICK_W, BRICK_H


class MortarGraph:
    """
    Graph of every mortar-joint intersection on the brick wall.

    Nodes  – (x, y) tuples at each crossing of a bed joint and a head joint.
    Edges  – pairs of adjacent nodes along the same mortar segment.
    Adjacency – dict mapping each node to its list of neighbours.

    Coordinate convention
    ---------------------
    Head joints (vertical) are placed at the left edge of each mortar gap:
      even rows → x = 0, 80, 160 … 800
      odd rows  → x = 0, 40, 120 … 800   (half-brick offset)
    Bed joints (horizontal) sit at every row boundary:
      y = SKY_HEIGHT, SKY_HEIGHT + BRICK_H, … SCREEN_HEIGHT
    """

    def __init__(self):
        self.nodes:     list[tuple[int, int]]                        = []
        self.edges:     list[tuple[tuple[int,int], tuple[int,int]]]  = []
        self.adjacency: dict[tuple[int,int], list[tuple[int,int]]]   = {}
        self._build()

    # ------------------------------------------------------------------
    def _row_xs(self, row: int) -> list[int]:
        """Sorted x-coordinates of all head joints for the given brick row."""
        offset = (BRICK_W // 2) if row % 2 == 1 else 0
        xs: list[int] = []
        x = offset
        while x <= SCREEN_WIDTH:
            if 0 < x < SCREEN_WIDTH:
                xs.append(x)
            x += BRICK_W
        return xs

    # ------------------------------------------------------------------
    def _build(self):
        node_set: set[tuple[int, int]]           = set()
        adj:      defaultdict[tuple, set[tuple]] = defaultdict(set)

        num_rows = round((SCREEN_HEIGHT - SKY_HEIGHT) / BRICK_H)   # 19

        # ---- vertical edges (head joints, one per column per row) ----
        for r in range(num_rows):
            y_top = SKY_HEIGHT + r * BRICK_H
            y_bot = SKY_HEIGHT + (r + 1) * BRICK_H

            for x in self._row_xs(r):
                n_top = (x, y_top)
                n_bot = (x, y_bot)
                node_set.add(n_top)
                node_set.add(n_bot)
                adj[n_top].add(n_bot)
                adj[n_bot].add(n_top)

        # ---- horizontal edges (bed joints, connect all nodes at same y) ----
        by_y: defaultdict[int, list[int]] = defaultdict(list)
        for (x, y) in node_set:
            by_y[y].append(x)

        for y, xs in by_y.items():
            s = sorted(xs)
            for x1, x2 in zip(s, s[1:]):
                n1, n2 = (x1, y), (x2, y)
                adj[n1].add(n2)
                adj[n2].add(n1)

        # ---- materialise ----
        self.nodes     = list(node_set)
        self.adjacency = {k: list(v) for k, v in adj.items()}

        seen: set[tuple] = set()
        for node, neighbours in self.adjacency.items():
            for nb in neighbours:
                key = (min(node, nb), max(node, nb))
                if key not in seen:
                    seen.add(key)
                    self.edges.append((node, nb))

        # Nodes on the very bottom row — valid spawn points
        self.bottom_nodes = [n for n in self.nodes if n[1] == SCREEN_HEIGHT]
        # Nodes on the very top row — reaching one triggers reached_top
        self.top_nodes    = {n for n in self.nodes if n[1] == SKY_HEIGHT}

    # ------------------------------------------------------------------
    def draw(self, surface,
             edge_colour: tuple = (170, 80, 220),
             node_colour: tuple = (230, 50, 150),
             node_radius: int   = 3) -> None:
        """Draw all edges then all nodes on top – call after the background blit."""
        for (n1, n2) in self.edges:
            pygame.draw.line(surface, edge_colour, n1, n2, 1)
        for node in self.nodes:
            pygame.draw.circle(surface, node_colour, node, node_radius)
