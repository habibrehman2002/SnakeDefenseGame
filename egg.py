import pygame
import random
import math
from settings import SKY_HEIGHT

# Sprite canvas — nest at bottom, egg sits inside it
SPRITE_W = 72
SPRITE_H = 40

# Egg dimensions
EGG_W = 16
EGG_H = 23

# How many nests get a leaf
_LEAF_CHANCE = 0.35

# Egg colours — pale cream-white with a slight blue tint
_EGG_BASE  = (240, 238, 228)
_EGG_LIGHT = (252, 250, 244)
_EGG_SHADE = (195, 185, 165)

# Nest / twig colours
_TWIG_DARK  = (72, 42, 12)
_TWIG_MID   = (110, 70, 26)
_TWIG_LIGHT = (158, 118, 60)

# Leaf colours
_LEAF_DARK  = (40, 105, 35)
_LEAF_MAIN  = (62, 150, 50)
_LEAF_LIGHT = (88, 185, 70)


class Egg(pygame.sprite.Sprite):
    def __init__(self, node: tuple[int, int]):
        super().__init__()
        self.node = node

        # Per-game randomness for leaf presence/orientation
        self.has_leaf   = random.random() < _LEAF_CHANCE
        self._leaf_side = random.choice((-1, 1))
        self._leaf_angle = random.uniform(20, 45) * self._leaf_side

        # Stable straw layout per column (same column always gets the same twigs)
        self._straw_rng = random.Random(node[0])

        self.image = pygame.Surface((SPRITE_W, SPRITE_H), pygame.SRCALPHA)
        self._draw()
        self.rect = self.image.get_rect(midbottom=(node[0], SKY_HEIGHT))

    # ------------------------------------------------------------------ #
    def _draw(self):
        surf = self.image
        cx = SPRITE_W // 2  # 21

        nest_top = SPRITE_H - 16   # y where nest rim begins (24)
        nest_cx  = cx
        nest_rx  = 18              # half-width of bowl
        nest_ry  = 8               # half-height of bowl ellipse

        # ── Straw / twig lines (drawn first, mostly behind the bowl fill) ──
        rng = self._straw_rng
        rng.seed(self.node[0])     # reset so re-draw always looks the same
        for _ in range(14):
            x1 = rng.randint(nest_cx - nest_rx + 2, nest_cx + nest_rx - 2)
            y1 = rng.randint(nest_top - 2, nest_top + 10)
            angle = rng.uniform(-0.6, 0.6)
            length = rng.randint(8, 16)
            x2 = int(x1 + length * math.cos(angle))
            y2 = int(y1 + length * math.sin(angle))
            col = rng.choice((_TWIG_DARK, _TWIG_MID, _TWIG_LIGHT))
            pygame.draw.line(surf, col, (x1, y1), (x2, y2), 1)

        # ── Leaf (tucked under nest rim, drawn before bowl) ────────────────
        if self.has_leaf:
            self._draw_leaf(surf, cx, nest_top)

        # ── Bowl fill ──────────────────────────────────────────────────────
        bowl_rect = pygame.Rect(nest_cx - nest_rx, nest_top, nest_rx * 2, nest_ry * 2)
        pygame.draw.ellipse(surf, _TWIG_MID, bowl_rect)

        # Inner lighter concave area
        inner = pygame.Rect(nest_cx - nest_rx + 5, nest_top + 3, (nest_rx - 5) * 2, nest_ry * 2 - 5)
        pygame.draw.ellipse(surf, _TWIG_LIGHT, inner)

        # Bowl rim outline
        pygame.draw.ellipse(surf, _TWIG_DARK, bowl_rect, 2)

        # ── Egg (sits inside the bowl) ─────────────────────────────────────
        ex = cx - EGG_W // 2
        ey = nest_top - EGG_H + 11  # egg bottom dips 11 px into the nest
        pygame.draw.ellipse(surf, _EGG_BASE, (ex, ey, EGG_W, EGG_H))
        # Soft highlight upper-left
        pygame.draw.ellipse(surf, _EGG_LIGHT, (ex + 3, ey + 2, 5, 8))
        # Outline
        pygame.draw.ellipse(surf, _EGG_SHADE, (ex, ey, EGG_W, EGG_H), 1)

    # ------------------------------------------------------------------ #
    def _draw_leaf(self, surf: pygame.Surface, cx: int, nest_top: int):
        lw, lh = 22, 11
        leaf_surf = pygame.Surface((lw + 6, lh + 6), pygame.SRCALPHA)

        # Main leaf body
        pygame.draw.ellipse(leaf_surf, _LEAF_MAIN, (3, 2, lw, lh))
        # Highlight
        pygame.draw.ellipse(leaf_surf, _LEAF_LIGHT, (4, 3, lw // 2 - 1, lh // 2))
        # Midrib vein
        pygame.draw.line(leaf_surf, _LEAF_DARK, (3, lh // 2 + 2), (lw + 2, lh // 2 + 2), 1)

        rotated = pygame.transform.rotate(leaf_surf, self._leaf_angle)

        # Position: pokes out from the nest rim on one side
        if self._leaf_side < 0:
            x = cx - 28
        else:
            x = cx + 4
        y = nest_top - 6
        surf.blit(rotated, (x, y))
