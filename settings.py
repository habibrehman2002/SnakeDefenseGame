SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600   # SKY_HEIGHT( used to be 108, now 152) + 16 brick rows × 28px
FPS = 60
TITLE = "SNAKE DEFENSE"

# Colors
BLACK        = (0, 0, 0)
WHITE        = (255, 255, 255)
RED          = (200, 50, 50)
YELLOW       = (230, 200, 0)
SKY_BLUE     = (100, 210, 230)   # cyan-ish sky matching rough draft
BRICK_RED    = (158, 60, 38)     # main brick face
BRICK_SHADE  = (120, 44, 26)     # darker bottom edge of brick
MORTAR       = (185, 168, 145)   # mortar joint colour
PIGEON_GRAY    = (148, 148, 158)
PIGEON_LIGHT   = (190, 190, 200)
PIGEON_NECK    = (100, 90, 120)
PIGEON_BEAK    = (210, 155, 60)
PIGEON_EYE     = (210, 60, 60)
PIGEON_FEET    = (210, 140, 80)
EGG_COLOR      = (245, 238, 215)
EGG_SHADE      = (200, 188, 160)

# Brick dimensions (each slot includes the mortar gap on right/bottom)
BRICK_W         = 80   # brick slot width  (face = BRICK_W - MORTAR_T)
BRICK_H         = 28   # brick slot height (face = BRICK_H - MORTAR_T)
MORTAR_T        = 4    # mortar thickness in pixels

# Sky strip at top — player patrols here above the wall
SKY_HEIGHT = 152 # used to be 108

# Player (pigeon — wider than tall, perched on wall top)
PLAYER_SPEED     = 4    # starting move speed (px/frame)
PLAYER_WIDTH     = 34
PLAYER_HEIGHT    = 30
PLAYER_Y         = 64   # bottom of sprite aligns near wall top
DROP_COOLDOWN    = 40   # starting frames between droppings

# Enemy — initial values; Game ramps these over time
ENEMY_SPEED          = 1.5   # starting px/frame
ENEMY_SIZE           = 22
ENEMY_SPAWN_INTERVAL = 120   # starting frames between spawns
ENEMY_SPEED_MAX      = 5.0
ENEMY_INTERVAL_MIN   = 30
DIFFICULTY_FRAMES    = 1800  # frames between difficulty steps (~30 s at 60 fps)
SPEED_INCREMENT      = 0.2
INTERVAL_DECREMENT   = 10

