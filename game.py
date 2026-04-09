import asyncio
import pygame
import random
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    WHITE, RED,
    SKY_BLUE, BRICK_RED, BRICK_SHADE, MORTAR,
    BRICK_W, BRICK_H, MORTAR_T, SKY_HEIGHT,
    ENEMY_SPEED, ENEMY_SPAWN_INTERVAL,
    ENEMY_SPEED_MAX, ENEMY_INTERVAL_MIN,
    SPEED_INCREMENT, INTERVAL_DECREMENT,
    PLAYER_SPEED, DROP_COOLDOWN,
)
from player import Player
from enemy import SnakeEnemy, Racer, Tanker, DeadSnake
from mortar_graph import MortarGraph
from dropping import Dropping
from egg import Egg


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 56)

        # Pre-render the static background (sky + walls) once
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
        self._build_background()

        # Build mortar-joint graph (used for enemy navigation)
        self.graph = MortarGraph()
        self.show_graph = False   # toggle with G

        self.high_score = 100
        self.running = True
        self.state = "start"  # "start" | "controls" | "playing"

    # ------------------------------------------------------------------
    def _build_background(self):
        """Pre-render sky strip + full brick-wall face."""

        # --- Sky strip ---
        self.background.fill(SKY_BLUE, (0, 0, SCREEN_WIDTH, SKY_HEIGHT))

        # --- Brick wall (fills everything below the sky) ---
        wall_top = SKY_HEIGHT
        wall_h   = SCREEN_HEIGHT - wall_top

        # Mortar base (the whole wall area becomes mortar colour)
        self.background.fill(MORTAR, (0, wall_top, SCREEN_WIDTH, wall_h))

        # Draw each brick row
        row = 0
        y   = wall_top
        while y < SCREEN_HEIGHT:
            # Odd rows are offset by half a brick width → classic running bond
            offset = (BRICK_W // 2) if (row % 2 == 1) else 0
            x = -offset          # start left of screen so offset rows fill edge
            while x < SCREEN_WIDTH:
                # Brick face rect (subtract mortar gap on right and bottom)
                bx = x
                by = y
                bw = BRICK_W - MORTAR_T
                bh = BRICK_H - MORTAR_T

                # Clamp to screen width
                if bx < 0:
                    bw += bx   # trim left overhang
                    bx = 0
                if bx + bw > SCREEN_WIDTH:
                    bw = SCREEN_WIDTH - bx

                # Clamp to wall bottom
                if by + bh > SCREEN_HEIGHT:
                    bh = SCREEN_HEIGHT - by

                if bw > 0 and bh > 0:
                    # Main brick face
                    pygame.draw.rect(
                        self.background, BRICK_RED, (bx, by, bw, bh)
                    )
                    # Subtle darker band at the bottom of each brick (depth)
                    shade_h = max(3, bh // 5)
                    pygame.draw.rect(
                        self.background, BRICK_SHADE,
                        (bx, by + bh - shade_h, bw, shade_h)
                    )

                x += BRICK_W
            y   += BRICK_H
            row += 1

        # Hard shadow line where sky meets wall
        pygame.draw.line(
            self.background, (50, 35, 20),
            (0, SKY_HEIGHT), (SCREEN_WIDTH, SKY_HEIGHT), 3
        )

    # ------------------------------------------------------------------
    def reset(self):
        self.all_sprites = pygame.sprite.Group()
        self.enemies     = pygame.sprite.Group()
        self.droppings   = pygame.sprite.Group()
        self.eggs        = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)

        # Place an egg at every other top node (sorted by x) → 5 eggs
        self._egg_map: dict[tuple[int, int], Egg] = {}
        sorted_top = sorted(self.graph.top_nodes, key=lambda n: n[0])
        for node in sorted_top[::2]:
            egg = Egg(node)
            self.eggs.add(egg)
            self.all_sprites.add(egg)
            self._egg_map[node] = egg

        self.dead_snakes: list[DeadSnake] = []

        self.score            = 0
        self.spawn_timer      = 0
        self.current_speed    = float(ENEMY_SPEED)
        self.current_interval = int(ENEMY_SPAWN_INTERVAL)
        self.current_drop_cooldown = DROP_COOLDOWN
        self.running      = True
        self.game_over    = False
        self.paused       = False
        self.final_score  = 0   # score frozen at death for the death screen
        self.state        = "playing"

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    def _spawn_enemy(self):
        start = random.choice(self.graph.bottom_nodes)
        if self.score >= 40:
            pool = [SnakeEnemy, Racer, Tanker]
        elif self.score >= 20:
            pool = [SnakeEnemy, Racer]
        else:
            pool = [SnakeEnemy]
        enemy = random.choice(pool)(self.graph, start, speed=self.current_speed)
        self.enemies.add(enemy)
        self.all_sprites.add(enemy)

    # ------------------------------------------------------------------
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.state == "start":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_start_click(event.pos)
                continue

            if self.state == "controls":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_controls_click(event.pos)
                continue

            # ── state == "playing" ────────────────────────────────────────
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not self.game_over:
                        self.paused = not self.paused
                if self.paused:
                    continue
                if event.key == pygame.K_g:
                    self.show_graph = not self.show_graph
                if event.key == pygame.K_SPACE and not self.game_over:
                    drop = self.player.release_dropping(self.current_drop_cooldown)
                    if drop:
                        self.droppings.add(drop)
                        self.all_sprites.add(drop)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.paused:
                    self._handle_pause_click(event.pos)
                elif self.game_over:
                    self._handle_death_click(event.pos)

    # ------------------------------------------------------------------
    def _handle_pause_click(self, pos: tuple[int, int]):
        for label, rect in self._pause_buttons():
            if rect.collidepoint(pos):
                if label == "Resume":
                    self.paused = False
                elif label == "Controls":
                    self._controls_origin = "pause"
                    self.state = "controls"
                elif label == "Restart":
                    self.reset()
                elif label == "Quit":
                    self.state = "start"

    def _handle_death_click(self, pos: tuple[int, int]):
        for label, rect in self._death_buttons():
            if rect.collidepoint(pos):
                if label == "Restart":
                    self.reset()
                elif label == "Quit":
                    self.state = "start"

    def _handle_start_click(self, pos: tuple[int, int]):
        for label, rect in self._start_buttons():
            if rect.collidepoint(pos):
                if label == "Play":
                    self.reset()
                elif label == "Controls":
                    self._controls_origin = "start"
                    self.state = "controls"

    def _start_buttons(self) -> list[tuple[str, pygame.Rect]]:
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2 + 20
        w, h, gap = 180, 44, 14
        buttons = []
        for i, label in enumerate(["Play", "Controls"]):
            rect = pygame.Rect(0, 0, w, h)
            rect.centerx = cx
            rect.top = cy + i * (h + gap)
            buttons.append((label, rect))
        return buttons

    def _handle_controls_click(self, pos: tuple[int, int]):
        _, rect = self._back_button()
        if rect.collidepoint(pos):
            origin = getattr(self, "_controls_origin", "start")
            if origin == "pause":
                self.state = "playing"
            else:
                self.state = "start"

    def _back_button(self) -> tuple[str, pygame.Rect]:
        rect = pygame.Rect(0, 0, 140, 40)
        rect.centerx = SCREEN_WIDTH // 2
        rect.bottom = SCREEN_HEIGHT - 30
        return ("Back", rect)

    def _death_buttons(self) -> list[tuple[str, pygame.Rect]]:
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2 + 60
        w, h, gap = 180, 44, 14
        buttons = []
        for i, label in enumerate(["Restart", "Quit"]):
            rect = pygame.Rect(0, 0, w, h)
            rect.centerx = cx
            rect.top = cy + i * (h + gap)
            buttons.append((label, rect))
        return buttons

    def _pause_buttons(self) -> list[tuple[str, pygame.Rect]]:
        """Return (label, rect) for each pause-menu button."""
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        w, h, gap = 180, 44, 14
        labels = ["Resume", "Controls", "Restart", "Quit"]
        buttons = []
        for i, label in enumerate(labels):
            rect = pygame.Rect(0, 0, w, h)
            rect.centerx = cx
            rect.top = cy - h + i * (h + gap)
            buttons.append((label, rect))
        return buttons

    # ------------------------------------------------------------------
    def _update(self):
        if self.state != "playing" or self.paused or self.game_over:
            return

        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # Tell each snake which egg positions currently exist
        egg_positions = {egg.node for egg in self.eggs}
        for enemy in list(self.enemies):
            enemy.egg_nodes = egg_positions
            enemy.update()
            if enemy.reached_top:
                # Kill the egg at this node (if still there), then the snake
                egg = self._egg_map.get(enemy.current_node)
                if egg and egg.alive():
                    egg.kill()
                    self._egg_map.pop(enemy.current_node, None)
                    if not self.eggs:
                        self.game_over   = True
                        self.final_score = self.score
                        if self.score > self.high_score:
                            self.high_score = self.score
                enemy.kill()

        # Update droppings and check against every body segment
        self.droppings.update()
        for drop in list(self.droppings):
            if not drop.alive():
                continue
            for enemy in list(self.enemies):
                if any(drop.rect.colliderect(r) for r in enemy.get_segment_rects()):
                    drop.kill()
                    if enemy.hit():   # returns True when enemy should die
                        main_col, dark_col = enemy.get_colors()
                        self.dead_snakes.append(DeadSnake(enemy._trail, main_col, dark_col))
                        enemy.kill()
                        self.score += 1
                    break

        # Animate and cull finished death animations
        for dead in self.dead_snakes:
            dead.update()
        self.dead_snakes = [d for d in self.dead_snakes if not d.done]

        # Difficulty scaling — one step per 10 points
        # Speed / player stats cap at 80 points (8 steps)
        capped_step = min(self.score, 80) // 10

        # Interval: normal rate up to 100, then double rate beyond 100
        if self.score < 100:
            interval_step = self.score // 10
        else:
            interval_step = 10 + ((self.score - 100) // 10) * 2

        self.current_speed    = min(ENEMY_SPEED_MAX,    ENEMY_SPEED          + capped_step   * SPEED_INCREMENT)
        self.current_interval = max(ENEMY_INTERVAL_MIN, ENEMY_SPAWN_INTERVAL - interval_step * INTERVAL_DECREMENT)

        # Player stats use the capped step so they stop scaling after 80 points
        capped_interval   = max(ENEMY_INTERVAL_MIN, ENEMY_SPAWN_INTERVAL - capped_step * INTERVAL_DECREMENT)
        interval_ratio    = capped_interval    / ENEMY_SPAWN_INTERVAL
        speed_ratio       = self.current_speed / ENEMY_SPEED
        self.current_drop_cooldown = max(10, int(DROP_COOLDOWN * interval_ratio * 1.25))
        self.player.move_speed     = int(PLAYER_SPEED * speed_ratio)

        # Spawn enemies
        self.spawn_timer += 1
        if self.spawn_timer >= self.current_interval:
            self.spawn_timer = 0
            self._spawn_enemy()

    # ------------------------------------------------------------------
    def _draw(self):
        if self.state == "start":
            self._draw_start_menu()
            pygame.display.flip()
            return
        if self.state == "controls":
            self._draw_controls_menu()
            pygame.display.flip()
            return

        self.screen.blit(self.background, (0, 0))
        if self.show_graph:
            self.graph.draw(self.screen)
            dbg = self.font.render(
                f"speed {self.current_speed:.1f}  interval {self.current_interval}",
                True, (230, 50, 150),
            )
            self.screen.blit(dbg, (6, SKY_HEIGHT + 6))
        # Draw snake bodies first so head (sprite rect) renders on top
        for enemy in self.enemies:
            enemy.draw_body(self.screen)  # type: ignore[attr-defined]
            enemy.draw_tongue(self.screen)  # type: ignore[attr-defined]
        for dead in self.dead_snakes:
            dead.draw(self.screen)
        self.all_sprites.draw(self.screen)
            

        # HUD
        score_surf = self.font.render(f"Score: {self.score}", True, WHITE)
        # eggs_surf  = self.font.render(f"Eggs: {len(self.eggs)}", True, YELLOW)
        # self.screen.blit(score_surf, (10, SCREEN_HEIGHT - 30))
        self.screen.blit(score_surf, (10, 12))
        # self.screen.blit(eggs_surf,  (SCREEN_WIDTH - eggs_surf.get_width() - 10, SCREEN_HEIGHT - 30))

        if self.game_over:
            self._draw_death_menu()

        if self.paused:
            self._draw_pause_menu()

        pygame.display.flip()

    # ------------------------------------------------------------------
    def _draw_menu_base(self):
        """Draw the shared background used by start/controls menus."""
        self.screen.blit(self.background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

    def _draw_button(self, label: str, rect: pygame.Rect):
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)
        bg_color = (90, 90, 110) if hovered else (50, 50, 65)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=8)
        text = self.font.render(label, True, WHITE)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_start_menu(self):
        self._draw_menu_base()
        cx = SCREEN_WIDTH // 2

        title = self.big_font.render(TITLE, True, WHITE)
        self.screen.blit(title, title.get_rect(center=(cx, SCREEN_HEIGHT // 2 - 60)))

        for label, rect in self._start_buttons():
            self._draw_button(label, rect)

    def _draw_controls_menu(self):
        self._draw_menu_base()
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        title = self.big_font.render("Controls", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(cx, cy - 120)))

        blurb = self.font.render("Defend your eggs from the incoming snakes!", True, (200, 200, 200))
        self.screen.blit(blurb, blurb.get_rect(center=(cx, cy + 90)))

        controls = [
            ("Move Left",  "Left Arrow / A"),
            ("Move Right", "Right Arrow / D"),
            ("Attack",     "Space"),
            ("Pause",      "Escape"),
        ]
        line_h = 32
        top = cy - 70
        label_x = cx - 20
        key_x   = cx + 20
        for i, (action, key) in enumerate(controls):
            y = top + i * line_h
            action_surf = self.font.render(action, True, (200, 200, 200))
            key_surf    = self.font.render(key,    True, WHITE)
            self.screen.blit(action_surf, action_surf.get_rect(right=label_x, centery=y))
            self.screen.blit(key_surf,    key_surf.get_rect(left=key_x,    centery=y))

        self._draw_button(*self._back_button())

    # ------------------------------------------------------------------
    def _draw_death_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        title = self.big_font.render("GAME OVER", True, (220, 80, 80))
        self.screen.blit(title, title.get_rect(center=(cx, cy - 90)))

        new_best = self.final_score > 0 and self.final_score == self.high_score
        score_text = f"Score: {self.final_score}"
        if new_best:
            score_text += "  NEW BEST!"
        score_surf = self.font.render(score_text, True, WHITE)
        self.screen.blit(score_surf, score_surf.get_rect(center=(cx, cy - 30)))

        hs_surf = self.font.render(f"High Score: {self.high_score}", True, (200, 190, 120))
        self.screen.blit(hs_surf, hs_surf.get_rect(center=(cx, cy + 5)))

        for label, rect in self._death_buttons():
            self._draw_button(label, rect)

    # ------------------------------------------------------------------
    def _draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        title = self.big_font.render("PAUSED", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 90)))

        for label, rect in self._pause_buttons():
            self._draw_button(label, rect)

    # ------------------------------------------------------------------
    async def run(self):
        while self.running:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()
            await asyncio.sleep(0)
        pygame.quit()
