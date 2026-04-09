import pygame
import math
import random
from settings import ENEMY_SPEED, SKY_HEIGHT, BRICK_H, SCREEN_HEIGHT
from mortar_graph import MortarGraph

# Base snake colours
SNAKE_GREEN      = (50, 200, 70)
SNAKE_GREEN_DARK = (30, 140, 45)

PENULTIMATE_Y = SKY_HEIGHT + BRICK_H

SEG_RADIUS  = 5
SEG_SPACING = 9


class SnakeEnemy(pygame.sprite.Sprite):
    NUM_SEGMENTS = 18
    SEG_SPACING  = SEG_SPACING

    # Subclasses override these to change colour
    COLOR_MAIN   = SNAKE_GREEN
    COLOR_DARK   = SNAKE_GREEN_DARK
    TONGUE_COLOR = (200, 30, 30)   # red

    def __init__(self, graph: MortarGraph, start_node: tuple[int, int], speed: float = ENEMY_SPEED):
        super().__init__()
        self.graph = graph
        self.speed = speed

        self.current_node: tuple[int, int]        = start_node
        self.prev_node:    tuple[int, int] | None  = None
        self.target_node:  tuple[int, int]         = start_node

        self.fx = float(start_node[0])
        self.fy = float(start_node[1])

        self.reached_top = False
        self.egg_nodes: set[tuple[int, int]] = set()

        self._trail: list[tuple[float, float]] = [(self.fx, self.fy)]

        sz = SEG_RADIUS * 2 + 2
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(int(self.fx), int(self.fy)))

        self._pick_next_target()

    # ------------------------------------------------------------------
    def get_colors(self) -> tuple:
        """Return (main_color, dark_color) reflecting current visual state."""
        return self.COLOR_MAIN, self.COLOR_DARK

    # ------------------------------------------------------------------
    def hit(self) -> bool:
        """Called when struck by a dropping. Returns True if the enemy should die."""
        return True

    # ------------------------------------------------------------------
    def _choose_from(self, choices: list[tuple[int, int]]) -> tuple[int, int]:
        """Select the next node from filtered candidates. Override for biased movement."""
        return random.choice(choices)

    def _pick_next_target(self):
        neighbours = self.graph.adjacency.get(self.current_node, [])

        up_or_side = [n for n in neighbours if n[1] <= self.current_node[1]]
        no_reverse = [n for n in up_or_side if n != self.prev_node]
        choices    = no_reverse if no_reverse else up_or_side

        if not choices:
            self.reached_top = True
            return

        # Penultimate-row egg steering (same for all types)
        if self.current_node[1] == PENULTIMATE_Y and self.egg_nodes:
            up_to_egg = [n for n in choices if n[1] < self.current_node[1] and n in self.egg_nodes]
            if up_to_egg:
                choices = up_to_egg
            else:
                nearest_x = min(self.egg_nodes, key=lambda e: abs(e[0] - self.current_node[0]))[0]
                side   = [n for n in choices if n[1] == self.current_node[1]]
                toward = [n for n in side if (n[0] - self.current_node[0]) * (nearest_x - self.current_node[0]) > 0]
                choices = toward or side or choices

        self.target_node = self._choose_from(choices)

    # ------------------------------------------------------------------
    def update(self):
        if self.reached_top:
            return

        tx, ty = self.target_node
        dx = tx - self.fx
        dy = ty - self.fy
        dist = math.hypot(dx, dy)

        if dist <= self.speed:
            self.fx, self.fy = float(tx), float(ty)
            self.prev_node    = self.current_node
            self.current_node = self.target_node

            if self.current_node in self.graph.top_nodes:
                self.reached_top = True
                return

            self._pick_next_target()
        else:
            self.fx += self.speed * dx / dist
            self.fy += self.speed * dy / dist

        self._trail.append((self.fx, self.fy))
        max_trail = self.NUM_SEGMENTS * self.SEG_SPACING + 4
        if len(self._trail) > max_trail:
            self._trail = self._trail[-max_trail:]

        self._redraw()

    # ------------------------------------------------------------------
    def _sample_trail(self) -> list[tuple[int, int]]:
        positions: list[tuple[int, int]] = []
        prev_pos = None
        step     = 0.0

        for i in range(len(self._trail) - 1, -1, -1):
            pos = self._trail[i]
            if prev_pos is not None:
                step += math.hypot(prev_pos[0] - pos[0], prev_pos[1] - pos[1])
            if prev_pos is None or step >= self.SEG_SPACING:
                step = 0.0
                positions.append((int(pos[0]), int(pos[1])))
                if len(positions) >= self.NUM_SEGMENTS:
                    break
            prev_pos = pos

        return positions

    def get_segment_rects(self) -> list[pygame.Rect]:
        r = SEG_RADIUS
        return [pygame.Rect(cx - r, cy - r, r * 2, r * 2) for cx, cy in self._sample_trail()]

    # ------------------------------------------------------------------
    def _head_colour(self) -> tuple:
        return self.COLOR_MAIN

    def _redraw(self):
        self.image.fill((0, 0, 0, 0))
        r  = SEG_RADIUS
        cx = cy = r + 1
        pygame.draw.circle(self.image, self._head_colour(), (cx, cy), r)
        pygame.draw.circle(self.image, (0, 0, 0), (cx + 2, cy - 2), 2)
        self.rect.center = (int(self.fx), int(self.fy))

    def draw_body(self, surface):
        r = SEG_RADIUS
        for i, (cx, cy) in enumerate(self._sample_trail()):
            col = self.COLOR_MAIN if i % 2 == 0 else self.COLOR_DARK
            pygame.draw.circle(surface, col, (cx, cy), r)

    def draw_tongue(self, surface):
        if self.reached_top:
            return
        dx = self.target_node[0] - self.fx
        dy = self.target_node[1] - self.fy
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        ndx, ndy = dx / dist, dy / dist   # unit vector toward target
        px,  py  = -ndy, ndx              # perpendicular
        hx,  hy  = int(self.fx), int(self.fy)

        STEM  = SEG_RADIUS + 5   # length of stem from head centre
        FORK  = 4                # length of each fork prong
        SPREAD = 2               # sideways spread of fork

        tip_x = hx + int(ndx * STEM)
        tip_y = hy + int(ndy * STEM)
        pygame.draw.line(surface, self.TONGUE_COLOR, (hx, hy), (tip_x, tip_y), 2)
        # two fork prongs
        for sign in (+1, -1):
            fx2 = tip_x + int(ndx * FORK + px * SPREAD * sign)
            fy2 = tip_y + int(ndy * FORK + py * SPREAD * sign)
            pygame.draw.line(surface, self.TONGUE_COLOR, (tip_x, tip_y), (fx2, fy2), 2)


# ======================================================================
class Racer(SnakeEnemy):
    """Fast-climbing snake that strongly prefers upward movement."""

    COLOR_MAIN   = (130, 130, 140)   # gray
    COLOR_DARK   = (70,  70,  82)    # dark gray
    TONGUE_COLOR = (130, 0, 160)     # purple
    UP_WEIGHT    = 5                 # upward moves are 5× more likely than sideways

    def _choose_from(self, choices: list[tuple[int, int]]) -> tuple[int, int]:
        weights = [
            self.UP_WEIGHT if n[1] < self.current_node[1] else 1
            for n in choices
        ]
        return random.choices(choices, weights=weights)[0]


# ======================================================================
class Tanker(SnakeEnemy):
    """Armoured snake that requires two hits to kill."""

    COLOR_MAIN     = (140, 88,  42)   # brown (full health)
    COLOR_DARK     = (95,  58,  25)   # dark brown
    COLOR_HIT      = (196, 158, 98)   # tan (damaged)
    COLOR_HIT_DARK = (158, 122, 68)   # darker tan
    TONGUE_COLOR   = (140, 10,  10)   # dark red

    def __init__(self, graph: MortarGraph, start_node: tuple[int, int], speed: float = ENEMY_SPEED):
        super().__init__(graph, start_node, speed)
        self.health = 2

    def get_colors(self) -> tuple:
        if self.health >= 2:
            return self.COLOR_MAIN, self.COLOR_DARK
        return self.COLOR_HIT, self.COLOR_HIT_DARK

    def hit(self) -> bool:
        self.health -= 1
        self._redraw()   # update head sprite colour immediately
        return self.health <= 0

    def _head_colour(self) -> tuple:
        return self.COLOR_MAIN if self.health >= 2 else self.COLOR_HIT

    def draw_body(self, surface):
        r = SEG_RADIUS
        main = self.COLOR_MAIN if self.health >= 2 else self.COLOR_HIT
        dark = self.COLOR_DARK if self.health >= 2 else self.COLOR_HIT_DARK
        for i, (cx, cy) in enumerate(self._sample_trail()):
            col = main if i % 2 == 0 else dark
            pygame.draw.circle(surface, col, (cx, cy), r)


# ======================================================================
class DeadSnake:
    """Purely-visual death animation — not a sprite, no collision."""

    def __init__(self, trail: list, color_main: tuple, color_dark: tuple):
        self._trail     = list(trail)
        self.color_main = color_main
        self.color_dark = color_dark
        self._vx        = random.uniform(-1.5, 1.5)
        self._vy        = -5.0    # initial upward pop
        self._gravity   = 0.35
        self._ox        = 0.0    # accumulated x offset
        self._oy        = 0.0    # accumulated y offset
        self._done      = False

    def update(self):
        self._vy += self._gravity
        self._ox += self._vx
        self._oy += self._vy
        if self._trail:
            min_y = min(p[1] for p in self._trail)
            if min_y + self._oy > SCREEN_HEIGHT + 40:
                self._done = True

    @property
    def done(self) -> bool:
        return self._done

    def _sample_trail(self) -> list[tuple[int, int]]:
        positions: list[tuple[int, int]] = []
        prev_pos = None
        step     = 0.0
        for i in range(len(self._trail) - 1, -1, -1):
            pos = self._trail[i]
            if prev_pos is not None:
                step += math.hypot(prev_pos[0] - pos[0], prev_pos[1] - pos[1])
            if prev_pos is None or step >= SEG_SPACING:
                step = 0.0
                positions.append((int(pos[0]), int(pos[1])))
                if len(positions) >= SnakeEnemy.NUM_SEGMENTS:
                    break
            prev_pos = pos
        return positions

    def draw(self, surface: pygame.Surface):
        ox = int(self._ox)
        oy = int(self._oy)
        r  = SEG_RADIUS
        positions = self._sample_trail()
        for i, (cx, cy) in enumerate(positions):
            col = self.color_main if i % 2 == 0 else self.color_dark
            pygame.draw.circle(surface, col, (cx + ox, cy + oy), r)
        # Dead-eye X on the head segment (index 0)
        if positions:
            hx, hy = positions[0][0] + ox, positions[0][1] + oy
            d = max(1, r - 3)
            pygame.draw.line(surface, (0, 0, 0), (hx - d, hy - d), (hx + d, hy + d), 2)
            pygame.draw.line(surface, (0, 0, 0), (hx + d, hy - d), (hx - d, hy + d), 2)
