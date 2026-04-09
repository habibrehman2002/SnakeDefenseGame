import pygame
from settings import SCREEN_HEIGHT

DROP_SPEED = 6

# Bird-poop palette
DROP_WHITE  = (250, 250, 232)   # main body
DROP_GREY   = (205, 205, 188)   # shadow / underside
DROP_DARK   = (170, 168, 148)   # outline accent


class Dropping(pygame.sprite.Sprite):
    """A pigeon dropping — teardrop shape, falls straight down."""

    W = 12
    H = 20

    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self._draw()
        self.rect = self.image.get_rect(centerx=x, top=y)
        self.fy   = float(self.rect.y)

    def _draw(self):
        W, H = self.W, self.H

        # --- tail drip (narrow oval at the top) ---
        tail_rect = pygame.Rect(W // 2 - 2, 0, 5, 9)
        pygame.draw.ellipse(self.image, DROP_WHITE, tail_rect)

        # --- main blob (wider oval, lower portion) ---
        blob_rect = pygame.Rect(1, H // 2 - 3, W - 2, H // 2 + 2)
        pygame.draw.ellipse(self.image, DROP_WHITE, blob_rect)

        # --- shadow on the right of the blob ---
        shadow_rect = pygame.Rect(W // 2, H // 2, W // 2 - 2, H // 2 - 1)
        pygame.draw.ellipse(self.image, DROP_GREY, shadow_rect)

        # --- subtle dark outline on blob ---
        pygame.draw.ellipse(self.image, DROP_DARK, blob_rect, 1)

    def update(self):
        self.fy     += DROP_SPEED
        self.rect.y  = int(self.fy)
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
