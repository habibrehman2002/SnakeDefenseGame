import math
import pygame
from settings import (
    SCREEN_WIDTH, PLAYER_SPEED, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_Y,
    PIGEON_GRAY, PIGEON_LIGHT, PIGEON_NECK, PIGEON_BEAK, PIGEON_EYE, PIGEON_FEET,
    DROP_COOLDOWN,
)
from dropping import Dropping

W = PLAYER_WIDTH
H = PLAYER_HEIGHT

# Wing animation: alternate every N frames
_WING_PERIOD   = 12   # frames per half-cycle (flap up / flap down)
_BOB_AMPLITUDE = 3   # pixels of vertical travel


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # Pre-render both animation frames (right-facing)
        self._frame_down = self._render_frame(wing_up=False)
        self._frame_up   = self._render_frame(wing_up=True)

        self._anim_tick    = 0
        self._total_tick   = 0   # continuous counter for bob sine wave
        self._wing_up      = False
        self._facing_right = True

        self.image = self._frame_down.copy()
        self.rect  = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom  = PLAYER_Y

        self._drop_cooldown = 0
        self.move_speed     = PLAYER_SPEED

    # ------------------------------------------------------------------
    def _render_frame(self, wing_up: bool) -> pygame.Surface:
        SH = H + 6   # extra pixels below body for feet
        surf = pygame.Surface((W, SH), pygame.SRCALPHA)


        # --- Tail ---
        tail_pts = [(-2, H // 2 + 4), (-4, H ), (8, H // 2 + 8)]
        pygame.draw.polygon(surf, (100, 100, 110), tail_pts)

        # --- Body ---
        body_rect = pygame.Rect(2, H // 2 - 2, W - 8, H // 2 + 2)
        pygame.draw.ellipse(surf, PIGEON_GRAY, body_rect)

        # --- Wing (raised when wing_up, lowered otherwise) ---
        wing_y = H // 2 - 6 if wing_up else H // 2
        wing_h = H // 2 - 2 if wing_up else H // 2 - 4
        wing_rect = pygame.Rect(5, wing_y, W - 14, wing_h)
        pygame.draw.ellipse(surf, PIGEON_LIGHT, wing_rect)

        # Wing tip: extra oval jutting slightly upward when raised
        if wing_up:
            tip_rect = pygame.Rect(8, wing_y - 4, W - 22, 10)
            pygame.draw.ellipse(surf, PIGEON_LIGHT, tip_rect)

        # --- Neck ---
        neck_rect = pygame.Rect(W - 14, H // 2 - 6, 10, 10)
        pygame.draw.ellipse(surf, PIGEON_NECK, neck_rect)

        # --- Head ---
        hx, hy = W - 8, H // 2 - 5
        pygame.draw.circle(surf, PIGEON_GRAY, (hx, hy), 8)

        # --- Beak ---
        beak_pts = [(hx + 6, hy), (hx + 16, hy + 1), (hx + 6, hy + 2)]
        pygame.draw.polygon(surf, PIGEON_BEAK, beak_pts)

        # --- Eye ---
        pygame.draw.circle(surf, PIGEON_EYE, (hx + 3, hy - 2), 2)
        pygame.draw.circle(surf, (0, 0, 0), (hx + 3, hy - 2), 1)

        # --- Feet ---
        feet_y = H + 2   # extended into the extra surface height
        pygame.draw.line(surf, PIGEON_FEET, (W // 2 - 4, H // 2 + 12), (W // 2 - 4, feet_y), 2)
        pygame.draw.line(surf, PIGEON_FEET, (W // 2 + 2, H // 2 + 12), (W // 2 + 2, feet_y), 2)
        pygame.draw.line(surf, PIGEON_FEET, (W // 2 - 4, feet_y), (W // 2 - 8, feet_y), 1)
        pygame.draw.line(surf, PIGEON_FEET, (W // 2 - 4, feet_y), (W // 2,     feet_y), 1)
        pygame.draw.line(surf, PIGEON_FEET, (W // 2 + 2, feet_y), (W // 2 - 2, feet_y), 1)
        pygame.draw.line(surf, PIGEON_FEET, (W // 2 + 2, feet_y), (W // 2 + 6, feet_y), 1)

        return surf

    # ------------------------------------------------------------------
    def update(self, keys):
        moving_left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        if moving_left:
            self.rect.x -= self.move_speed
            self._facing_right = False
        if moving_right:
            self.rect.x += self.move_speed
            self._facing_right = True

        # Advance wing animation
        self._anim_tick  += 1
        self._total_tick += 1
        if self._anim_tick >= _WING_PERIOD:
            self._anim_tick = 0
            self._wing_up = not self._wing_up

        base = self._frame_up if self._wing_up else self._frame_down
        self.image = base if self._facing_right else \
                     pygame.transform.flip(base, True, False)

        self.rect.left  = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)

        # Bob vertically in sync with the wing cycle.
        # sin peaks positive at mid-down-stroke (bird sinks) and
        # peaks negative at mid-up-stroke (bird rises).
        phase = self._total_tick / (2 * _WING_PERIOD)
        bob = round(_BOB_AMPLITUDE * -1 * math.sin(2 * math.pi * phase))
        self.rect.bottom = PLAYER_Y + bob

        if self._drop_cooldown > 0:
            self._drop_cooldown -= 1

    # ------------------------------------------------------------------
    def release_dropping(self, cooldown: int = DROP_COOLDOWN) -> "Dropping | None":
        if self._drop_cooldown == 0:
            self._drop_cooldown = cooldown
            return Dropping(self.rect.centerx, self.rect.bottom)
        return None
