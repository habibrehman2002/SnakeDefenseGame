# SNAKE DEFENSE

## Play the game

The game can be played online at https://habibrehman2002.github.io/SnakeDefenseGame/

## Running the game locally

Requires Python with Pygame in the `snakegame` conda environment (user manages env activation):

```bash
python main.py
```

The entry point uses `asyncio` (for pygbag web compatibility): `main.py` → instantiates `Game` and calls `asyncio.run(game.run())`.

## Web build

A GitHub Actions workflow (`.github/workflows/pygbag.yml`) builds the game for the browser via pygbag and deploys to the `gh-pages` branch. Trigger manually via `workflow_dispatch`. Build output lands in `build/web/`.

## Controls

| Action     | Keys                  |
|------------|-----------------------|
| Move left  | Left Arrow / A        |
| Move right | Right Arrow / D       |
| Attack     | Space (drop a poop)   |
| Pause      | Escape                |
| Debug graph| G (toggles overlay)   |

## Architecture

### Entry point
`main.py` → instantiates `Game` and calls `asyncio.run(game.run())`.

### Game loop (`game.py`)
`Game` owns all sprite groups and the main loop (`_handle_events` → `_update` → `_draw`). Key state:
- `self.enemies` / `self.droppings` / `self.eggs` — sprite groups for collision logic
- `self.dead_snakes: list[DeadSnake]` — plain objects, purely visual, no collision
- `self._egg_map: dict[tuple, Egg]` — O(1) node→egg lookup for when a snake reaches the top
- Difficulty parameters (`current_speed`, `current_interval`, `current_drop_cooldown`) recalculated every frame from `self.score`
- `self.state` — `"start"` | `"controls"` | `"playing"`
- `self.paused` / `self.game_over` — sub-states within `"playing"`
- `self.high_score` — tracked in memory (not persisted to disk)

### Player (`player.py`)
`Player` is a pigeon sprite that patrols the sky strip. It pre-renders two animation frames (wing up / wing down) and flips horizontally when moving left. A sine-wave bob is applied each frame in sync with the wing cycle. Attacking drops a `Dropping` from the player's position subject to a per-frame cooldown (`DROP_COOLDOWN = 40` frames starting value).

### Navigation graph (`mortar_graph.py`)
`MortarGraph` builds a graph of every mortar-joint intersection on the brick wall. Nodes are `(x, y)` tuples. `bottom_nodes` are spawn points (y == SCREEN_HEIGHT); `top_nodes` are egg positions (y == SKY_HEIGHT). Toggle debug overlay with **G**.

### Enemy system (`enemy.py`)
`SnakeEnemy` is the base class. Subclasses override class attributes and hooks:
- `COLOR_MAIN`, `COLOR_DARK`, `TONGUE_COLOR` — visual identity
- `_choose_from(choices)` — movement bias (Racer overrides for upward weight)
- `hit() -> bool` — returns True when the enemy should die; Tanker overrides for 2-hit health
- `get_colors() -> (main, dark)` — current colours accounting for damage state (used to initialise `DeadSnake`)

Navigation: `_pick_next_target` filters neighbours to never go down, avoids reversing, and steers toward eggs when on the penultimate row (`PENULTIMATE_Y = SKY_HEIGHT + BRICK_H`).

Body rendering is split: `draw_body()` draws segment circles directly onto the surface (called before `all_sprites.draw`); the head sprite (`self.image`) is drawn by `all_sprites.draw`; `draw_tongue()` is called after `all_sprites.draw` so it renders on top.

`DeadSnake` is a plain (non-sprite) object that captures a trail snapshot on death and applies parabolic arc physics (`vy` starting at −5, gravity 0.35) each frame until off-screen.

### Difficulty scaling
Recalculated every frame from `self.score` (not time-based):
- `capped_step = min(score, 80) // 10` — caps speed and player stats at 80 points
- Enemy interval step is uncapped and doubles in rate after 100 points
- Spawn pool: green only < 20pts; + Racer ≥ 20pts; + Tanker ≥ 40pts

### Screen layout
```
y=0
  ┌─────────────────────┐  ← SKY_HEIGHT = 152 px  (player + eggs live here)
  │         sky         │
  ├─────────────────────┤  ← wall top / top_nodes / egg baseline
  │     brick wall      │    16 rows × BRICK_H(28) px
  │   (enemies climb)   │
  └─────────────────────┘  ← SCREEN_HEIGHT = 600 / bottom_nodes / spawn points
```

Brick layout: `BRICK_W=80`, `BRICK_H=28`, `MORTAR_T=4`. Odd brick rows are offset by `BRICK_W//2` (running bond). The background is pre-rendered once into `self.background` in `_build_background`.
