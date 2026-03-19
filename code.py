import os
import pygame
import sys
import math
from levels import LEVELS

# --- 1. SETTINGS & CONSTANTS ---
pygame.init()
_mixer_ok = False
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    _mixer_ok = True
except pygame.error:
    pass

TILE_SIZE = 30
FPS = 60

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PINK = (255, 182, 193)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
PURPLE = (160, 32, 240)
DEEP_BLUE = (30, 30, 255)

UI_HEIGHT = 50

GHOST_COLORS = {
    "Blinky": RED,
    "Pinky": PINK,
    "Inky": CYAN,
    "Clyde": ORANGE,
}

# Active level data is loaded at runtime from levels.py
ORIGINAL_MAP = []
LEVEL_MAP = []
PLAYER_START = (0, 0)
FRUIT_POSITION = (0, 0)
FRUIT_SPAWN_SCORES = []
POWER_PELLET_POSITIONS = []
MAGNET_POWERUP_POSITIONS = []
GHOST_EXIT = (0, 0)
GHOST_CONFIGS = []
COLS = 0
ROWS = 0
WIDTH = 0
HEIGHT = UI_HEIGHT
current_level_index = 0

POWERUP_DURATION_FRAMES = FPS * 8
MAGNET_DURATION_FRAMES = FPS * 8
FRUIT_DURATION_FRAMES = FPS * 8
LEVEL_CLEAR_DURATION_FRAMES = FPS * 2
LEVEL_CLEAR_BLINK_INTERVAL = 8
MAGNET_RADIUS_PIXELS = int(TILE_SIZE * 3.0)


def place_power_pellets():
    for col, row in POWER_PELLET_POSITIONS:
        if LEVEL_MAP[row][col] != 1:
            LEVEL_MAP[row][col] = 4 if (col, row) in MAGNET_POWERUP_POSITIONS else 3


def reset_board_map():
    for r in range(ROWS):
        for c in range(COLS):
            LEVEL_MAP[r][c] = ORIGINAL_MAP[r][c]
    place_power_pellets()


def draw_magnet_icon(surface, center_x, center_y, radius=9):
    # Horseshoe body
    pygame.draw.arc(
        surface,
        CYAN,
        (center_x - radius, center_y - radius, radius * 2, radius * 2),
        math.pi * 0.15,
        math.pi * 0.85,
        4
    )
    # Magnet tips
    tip_offset = int(radius * 0.72)
    tip_y = center_y + int(radius * 0.32)
    tip_size = max(2, radius // 3)
    pygame.draw.rect(surface, RED, (center_x - tip_offset - tip_size, tip_y, tip_size, tip_size))
    pygame.draw.rect(surface, WHITE, (center_x - tip_offset, tip_y, tip_size, tip_size))
    pygame.draw.rect(surface, RED, (center_x + tip_offset, tip_y, tip_size, tip_size))
    pygame.draw.rect(surface, WHITE, (center_x + tip_offset - tip_size, tip_y, tip_size, tip_size))

pygame.display.set_caption("Pac-Man: Life and Death")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)
large_font = pygame.font.SysFont("Arial", 48, bold=True)

_SOUNDS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "third_party")
_KENNEY_AUDIO = os.path.join(_SOUNDS_ROOT, "kenney_digital-audio", "Audio")


def _load_sound(path):
    if not _mixer_ok or not os.path.isfile(path):
        return None
    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        return None


snd_wakka = _load_sound(os.path.join(_SOUNDS_ROOT, "pacman_wakka.wav"))
snd_power_pellet = _load_sound(os.path.join(_KENNEY_AUDIO, "powerUp5.ogg"))
snd_magnet_pickup = _load_sound(os.path.join(_KENNEY_AUDIO, "phaseJump2.ogg"))
snd_ghost_eaten = _load_sound(os.path.join(_KENNEY_AUDIO, "pepSound4.ogg"))
snd_death = _load_sound(os.path.join(_KENNEY_AUDIO, "lowDown.ogg"))
snd_fruit = _load_sound(os.path.join(_KENNEY_AUDIO, "powerUp1.ogg"))
snd_level_clear = _load_sound(os.path.join(_KENNEY_AUDIO, "highUp.ogg"))

_BGM_PATH = os.path.join(_SOUNDS_ROOT, "pacman_background_music.ogg")
_bgm_enabled = False
if _mixer_ok and os.path.isfile(_BGM_PATH):
    try:
        pygame.mixer.music.load(_BGM_PATH)
        pygame.mixer.music.set_volume(0.22)
        pygame.mixer.music.play(-1)
        _bgm_enabled = True
    except pygame.error:
        pass


def pause_bgm():
    if _bgm_enabled:
        pygame.mixer.music.pause()


def resume_bgm():
    if _bgm_enabled:
        pygame.mixer.music.unpause()


def stop_bgm():
    if _bgm_enabled:
        pygame.mixer.music.stop()


def restart_bgm():
    if _bgm_enabled:
        pygame.mixer.music.play(-1)


def play_eat_sounds(counts):
    if counts["power"] and snd_power_pellet:
        snd_power_pellet.play()
    if counts["magnet"] and snd_magnet_pickup:
        snd_magnet_pickup.play()
    if counts["pellet"] and snd_wakka:
        snd_wakka.play()


# --- 2. THE PLAYER CLASS ---
class Player:
    def __init__(self, start_col, start_row):
        self.start_col = start_col
        self.start_row = start_row

        self.speed = 2
        self.score = 0
        self.lives = 3 # NEW: The safety net
        self.death_timer = 0 # NEW: Tracks the death animation
        self.power_timer = 0
        self.magnet_timer = 0

        self.reset_position()

    def collect_tile(self, row, col):
        ate_powerup = False
        eat_kind = None
        tile = LEVEL_MAP[row][col]
        if tile == 0:
            LEVEL_MAP[row][col] = 2
            self.score += 10
            eat_kind = "pellet"
        elif tile == 3:
            LEVEL_MAP[row][col] = 2
            self.score += 50
            self.power_timer = POWERUP_DURATION_FRAMES
            ate_powerup = True
            eat_kind = "power"
        elif tile == 4:
            LEVEL_MAP[row][col] = 2
            self.score += 50
            self.magnet_timer = MAGNET_DURATION_FRAMES
            eat_kind = "magnet"
        return ate_powerup, eat_kind

    def collect_nearby_pellets(self):
        ate_powerup = False
        counts = {"pellet": 0, "power": 0, "magnet": 0}
        for row in range(ROWS):
            for col in range(COLS):
                tile = LEVEL_MAP[row][col]
                if tile != 0:
                    continue
                pellet_x = (col * TILE_SIZE) + (TILE_SIZE // 2)
                pellet_y = (row * TILE_SIZE) + (TILE_SIZE // 2)
                if math.hypot(self.x - pellet_x, self.y - pellet_y) <= MAGNET_RADIUS_PIXELS:
                    ap, kind = self.collect_tile(row, col)
                    ate_powerup = ate_powerup or ap
                    if kind:
                        counts[kind] += 1
        return ate_powerup, counts

    def clear_powerups(self):
        self.power_timer = 0
        self.magnet_timer = 0

    def reset_position(self):
        # We need to call this whenever we lose a life or clear the board
        self.x = (self.start_col * TILE_SIZE) + (TILE_SIZE // 2)
        self.y = (self.start_row * TILE_SIZE) + (TILE_SIZE // 2)
        self.dx = 0; self.dy = 0
        self.queued_dx = 0; self.queued_dy = 0
        self.direction = 0
        self.anim_counter = 0
        self.death_timer = 0

    def update(self, keys):
        ate_powerup = False
        cleared_board = False
        eat_counts = {"pellet": 0, "power": 0, "magnet": 0}

        if keys[pygame.K_LEFT]:
            self.queued_dx = -self.speed; self.queued_dy = 0
        elif keys[pygame.K_RIGHT]:
            self.queued_dx = self.speed; self.queued_dy = 0
        elif keys[pygame.K_UP]:
            self.queued_dx = 0; self.queued_dy = -self.speed
        elif keys[pygame.K_DOWN]:
            self.queued_dx = 0; self.queued_dy = self.speed

        if self.queued_dx != 0 and self.queued_dx == -self.dx:
            self.dx = self.queued_dx; self.dy = 0
            self.direction = math.pi if self.dx < 0 else 0
        if self.queued_dy != 0 and self.queued_dy == -self.dy:
            self.dx = 0; self.dy = self.queued_dy
            self.direction = 3 * math.pi / 2 if self.dy < 0 else math.pi / 2

        at_center_x = (self.x % TILE_SIZE) == (TILE_SIZE // 2)
        at_center_y = (self.y % TILE_SIZE) == (TILE_SIZE // 2)

        if at_center_x and at_center_y:
            col = int(self.x // TILE_SIZE); row = int(self.y // TILE_SIZE)
            q_col = (col + (1 if self.queued_dx > 0 else -1 if self.queued_dx < 0 else 0)) % COLS
            q_row = row + (1 if self.queued_dy > 0 else -1 if self.queued_dy < 0 else 0)

            queued_in_bounds = 0 <= q_row < ROWS
            if queued_in_bounds and LEVEL_MAP[q_row][q_col] != 1:
                self.dx = self.queued_dx; self.dy = self.queued_dy
                if self.dx > 0: self.direction = 0
                elif self.dx < 0: self.direction = math.pi
                elif self.dy > 0: self.direction = math.pi / 2
                elif self.dy < 0: self.direction = 3 * math.pi / 2
            else:
                curr_col = (col + (1 if self.dx > 0 else -1 if self.dx < 0 else 0)) % COLS
                curr_row = row + (1 if self.dy > 0 else -1 if self.dy < 0 else 0)
                curr_in_bounds = 0 <= curr_row < ROWS
                if (not curr_in_bounds) or LEVEL_MAP[curr_row][curr_col] == 1:
                    self.dx = 0; self.dy = 0

        self.x += self.dx; self.y += self.dy
        if self.x < 0: self.x += WIDTH
        elif self.x > WIDTH: self.x -= WIDTH

        current_col = int(self.x // TILE_SIZE); current_row = int(self.y // TILE_SIZE)
        ap_tile, kind_tile = self.collect_tile(current_row, current_col)
        ate_powerup = ate_powerup or ap_tile
        if kind_tile:
            eat_counts[kind_tile] += 1

        if self.power_timer > 0:
            self.power_timer -= 1
        if self.magnet_timer > 0:
            ap_mag, mag_counts = self.collect_nearby_pellets()
            ate_powerup = ate_powerup or ap_mag
            for k in eat_counts:
                eat_counts[k] += mag_counts[k]
            self.magnet_timer -= 1

        has_pellets_left = any(0 in row or 3 in row or 4 in row for row in LEVEL_MAP)
        if not has_pellets_left:
            cleared_board = True

        return ate_powerup, cleared_board, eat_counts

    def draw(self, surface, game_state):
        # Don't draw if dead-dead
        if game_state == "GAME_OVER": return

        radius = (TILE_SIZE // 2) - 4

        # --- NEW: Death Animation Logic ---
        if game_state == "DYING":
            # Timer goes up to 60 frames (1 second). Progress is a 0.0 to 1.0 multiplier.
            progress = self.death_timer / 60.0

            # The mouth opens all the way to 180 degrees (math.pi) until he folds out of existence
            mouth_angle = min(math.pi, progress * math.pi)

            # If the angle hits exactly pi, the polygon disappears, so we just stop drawing
            if progress >= 0.95: return
        else:
            # Normal chomping animation
            if self.dx != 0 or self.dy != 0:
                self.anim_counter += 0.3
                mouth_angle = abs(math.sin(self.anim_counter)) * (math.pi / 4)
            else:
                mouth_angle = math.pi / 6

        start_angle = self.direction + mouth_angle
        end_angle = self.direction + (2 * math.pi) - mouth_angle

        points = [(self.x, self.y)]
        steps = 15
        for i in range(steps + 1):
            current_angle = start_angle + (i * ((end_angle - start_angle) / steps))
            points.append((self.x + radius * math.cos(current_angle), self.y + radius * math.sin(current_angle)))
        pygame.draw.polygon(surface, YELLOW, points)


# --- 3. THE GHOST CLASS ---
class Ghost:
    def __init__(self, start_col, start_row, color, name, spawn_delay_frames):
        # Save these so we can reset properly when Pac-Man dies
        self.home_col = start_col
        self.home_row = start_row
        self.initial_spawn_delay = spawn_delay_frames

        self.color = color
        self.name = name
        self.speed = 2
        self.frightened_flash_timer = 0

        self.reset_position()

    def reset_position(self):
        # NEW: Send them back to the cage
        self.x = (self.home_col * TILE_SIZE) + (TILE_SIZE // 2)
        self.y = (self.home_row * TILE_SIZE) + (TILE_SIZE // 2)
        self.state = 'trapped'
        self.spawn_timer = self.initial_spawn_delay
        self.dx = 0; self.dy = 0

    def update(self, target_player, blinky_ref, power_active):
        if self.state == 'trapped':
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self.state = 'exiting'
            return

        if self.state == 'exiting':
            exit_x = (GHOST_EXIT[0] * TILE_SIZE) + (TILE_SIZE // 2)
            exit_y = (GHOST_EXIT[1] * TILE_SIZE) + (TILE_SIZE // 2)

            if self.x < exit_x: self.dx = self.speed; self.dy = 0
            elif self.x > exit_x: self.dx = -self.speed; self.dy = 0
            elif self.y > exit_y: self.dx = 0; self.dy = -self.speed
            else:
                self.state = 'chasing'

            self.x += self.dx; self.y += self.dy
            return

        at_center_x = (self.x % TILE_SIZE) == (TILE_SIZE // 2)
        at_center_y = (self.y % TILE_SIZE) == (TILE_SIZE // 2)

        if at_center_x and at_center_y:
            col = int(self.x // TILE_SIZE); row = int(self.y // TILE_SIZE)

            p_col = int(target_player.x // TILE_SIZE)
            p_row = int(target_player.y // TILE_SIZE)

            t_col, t_row = p_col, p_row

            if self.name == "Pinky":
                p_dx = target_player.dx // target_player.speed if target_player.dx != 0 else 0
                p_dy = target_player.dy // target_player.speed if target_player.dy != 0 else 0
                t_col = p_col + (p_dx * 4); t_row = p_row + (p_dy * 4)

            elif self.name == "Inky":
                p_dx = target_player.dx // target_player.speed if target_player.dx != 0 else 0
                p_dy = target_player.dy // target_player.speed if target_player.dy != 0 else 0
                pivot_col = p_col + (p_dx * 2); pivot_row = p_row + (p_dy * 2)
                b_col = int(blinky_ref.x // TILE_SIZE); b_row = int(blinky_ref.y // TILE_SIZE)
                t_col = pivot_col + (pivot_col - b_col); t_row = pivot_row + (pivot_row - b_row)

            elif self.name == "Clyde":
                dist_sq = (col - p_col)**2 + (row - p_row)**2
                if dist_sq < 64:
                    t_col, t_row = 0, ROWS - 1

            possible_moves = [
                (0, -self.speed, col, row - 1),
                (-self.speed, 0, (col - 1) % COLS, row),
                (0, self.speed, col, row + 1),
                (self.speed, 0, (col + 1) % COLS, row)
            ]

            valid_moves = []
            for move_dx, move_dy, n_col, n_row in possible_moves:
                if not (0 <= n_row < ROWS):
                    continue
                if LEVEL_MAP[n_row][n_col] == 1: continue
                if move_dx != 0 and move_dx == -self.dx: continue
                if move_dy != 0 and move_dy == -self.dy: continue
                distance = (n_col - t_col)**2 + (n_row - t_row)**2
                valid_moves.append((distance, move_dx, move_dy))

            if valid_moves:
                if power_active:
                    valid_moves.sort(key=lambda x: x[0], reverse=True)
                else:
                    valid_moves.sort(key=lambda x: x[0])
                self.dx = valid_moves[0][1]; self.dy = valid_moves[0][2]

        self.x += self.dx; self.y += self.dy
        if self.x < 0: self.x += WIDTH
        elif self.x > WIDTH: self.x -= WIDTH

    def draw(self, surface, game_state):
        # We don't draw the ghosts if Pac-Man is currently folding into himself
        if game_state == "DYING": return

        body_points = [
            (-14, 4), (-14, -6), (-10, -12), (-4, -15), (4, -15), (10, -12), (14, -6),
            (14, 4), (10, 15), (5, 10), (0, 15), (-5, 10), (-10, 15)
        ]
        real_points = [(self.x + px, self.y + py) for px, py in body_points]
        draw_color = DEEP_BLUE if getattr(player, "power_timer", 0) > 0 else self.color
        pygame.draw.polygon(surface, draw_color, real_points)

        eye_color = WHITE
        iris_color = BLUE
        left_eye_pos = (self.x - 6, self.y - 4)
        right_eye_pos = (self.x + 6, self.y - 4)

        pygame.draw.circle(surface, eye_color, left_eye_pos, 4)
        pygame.draw.circle(surface, eye_color, right_eye_pos, 4)

        iris_x = 2 if self.dx > 0 else -2 if self.dx < 0 else 0
        iris_y = 2 if self.dy > 0 else -2 if self.dy < 0 else 0

        pygame.draw.circle(surface, iris_color, (left_eye_pos[0] + iris_x, left_eye_pos[1] + iris_y), 2)
        pygame.draw.circle(surface, iris_color, (right_eye_pos[0] + iris_x, right_eye_pos[1] + iris_y), 2)


def load_level(level_index, keep_progress=False):
    global current_level_index, ORIGINAL_MAP, LEVEL_MAP
    global PLAYER_START, FRUIT_POSITION, FRUIT_SPAWN_SCORES
    global POWER_PELLET_POSITIONS, MAGNET_POWERUP_POSITIONS, GHOST_EXIT, GHOST_CONFIGS
    global COLS, ROWS, WIDTH, HEIGHT
    global screen, player, ghosts, blinky
    global fruit_active, fruit_timer, next_fruit_index

    previous_score = player.score if keep_progress and "player" in globals() else 0
    previous_lives = player.lives if keep_progress and "player" in globals() else 3

    current_level_index = level_index % len(LEVELS)
    level_data = LEVELS[current_level_index]

    ORIGINAL_MAP = [row[:] for row in level_data["map"]]
    PLAYER_START = level_data["player_start"]
    FRUIT_POSITION = level_data["fruit_position"]
    FRUIT_SPAWN_SCORES = list(level_data["fruit_spawn_scores"])
    POWER_PELLET_POSITIONS = list(level_data["power_pellets"])
    MAGNET_POWERUP_POSITIONS = list(level_data["magnet_powerups"])
    GHOST_EXIT = level_data["ghost_exit"]
    GHOST_CONFIGS = list(level_data["ghost_spawns"])

    LEVEL_MAP = [row[:] for row in ORIGINAL_MAP]
    ROWS = len(LEVEL_MAP)
    COLS = len(LEVEL_MAP[0])
    WIDTH = COLS * TILE_SIZE
    HEIGHT = (ROWS * TILE_SIZE) + UI_HEIGHT

    place_power_pellets()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    player = Player(PLAYER_START[0], PLAYER_START[1])
    player.score = previous_score
    player.lives = previous_lives

    ghosts = [
        Ghost(col, row, GHOST_COLORS[name], name, spawn_delay)
        for col, row, name, spawn_delay in GHOST_CONFIGS
    ]
    blinky = next((ghost for ghost in ghosts if ghost.name == "Blinky"), ghosts[0])

    fruit_active = False
    fruit_timer = 0
    next_fruit_index = 0


# --- 4. MAIN GAME SETUP ---
screen = None
player = None
ghosts = []
blinky = None
fruit_active = False
fruit_timer = 0
next_fruit_index = 0
load_level(0, keep_progress=False)


def reset_game():
    global game_state, level_clear_timer, fruit_active, fruit_timer, next_fruit_index
    load_level(0, keep_progress=False)
    game_state = "PLAYING"
    level_clear_timer = 0
    fruit_active = False
    fruit_timer = 0
    next_fruit_index = 0
    restart_bgm()


# NEW: The core state machine
game_state = "PLAYING" # Can be: PLAYING, PAUSED, LEVEL_CLEAR, DYING, GAME_OVER
level_clear_timer = 0

# --- 5. GAME LOOP ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                if game_state == "PLAYING":
                    game_state = "PAUSED"
                    pause_bgm()
                elif game_state == "PAUSED":
                    game_state = "PLAYING"
                    resume_bgm()
            elif event.key == pygame.K_ESCAPE and game_state == "PAUSED":
                game_state = "PLAYING"
                resume_bgm()
            elif event.key == pygame.K_r and game_state in ("PAUSED", "GAME_OVER"):
                reset_game()
            elif event.key == pygame.K_q and game_state in ("PAUSED", "GAME_OVER"):
                running = False
            elif event.key == pygame.K_n and game_state in ("PLAYING", "PAUSED", "LEVEL_CLEAR"):
                if game_state == "PAUSED":
                    resume_bgm()
                load_level(current_level_index + 1, keep_progress=True)
                game_state = "PLAYING"
                level_clear_timer = 0
                fruit_active = False
                fruit_timer = 0
                next_fruit_index = 0

    # --- LOGIC UPDATES ---
    if game_state == "PLAYING":
        keys = pygame.key.get_pressed()
        ate_powerup, cleared_board, eat_counts = player.update(keys)
        play_eat_sounds(eat_counts)

        if ate_powerup:
            # Quick turnaround when the player grabs a power pellet.
            for ghost in ghosts:
                if ghost.state == "chasing":
                    ghost.dx *= -1
                    ghost.dy *= -1

        if cleared_board:
            game_state = "LEVEL_CLEAR"
            if snd_level_clear:
                snd_level_clear.play()
            level_clear_timer = 0
            player.dx = 0
            player.dy = 0
            player.queued_dx = 0
            player.queued_dy = 0
            fruit_active = False
            fruit_timer = 0

        if game_state == "PLAYING":
            if next_fruit_index < len(FRUIT_SPAWN_SCORES) and player.score >= FRUIT_SPAWN_SCORES[next_fruit_index]:
                fruit_active = True
                fruit_timer = FRUIT_DURATION_FRAMES
                next_fruit_index += 1

            if fruit_active:
                fruit_timer -= 1
                if fruit_timer <= 0:
                    fruit_active = False

                fruit_col, fruit_row = FRUIT_POSITION
                fruit_x = (fruit_col * TILE_SIZE) + (TILE_SIZE // 2)
                fruit_y = (fruit_row * TILE_SIZE) + (TILE_SIZE // 2)
                if math.hypot(player.x - fruit_x, player.y - fruit_y) < TILE_SIZE // 2:
                    fruit_active = False
                    player.score += 100
                    if snd_fruit:
                        snd_fruit.play()

            for ghost in ghosts:
                ghost.update(player, blinky, player.power_timer > 0)

                # THE COLLISION CHECK
                # We use the Pythagorean theorem to check distance between centers.
                # If it's less than half a tile, we have a collision.
                distance = math.hypot(player.x - ghost.x, player.y - ghost.y)
                if distance < TILE_SIZE // 2:
                    if player.power_timer > 0 and ghost.state == "chasing":
                        player.score += 200
                        ghost.reset_position()
                        if snd_ghost_eaten:
                            snd_ghost_eaten.play()
                    else:
                        game_state = "DYING"
                        player.clear_powerups()
                        player.death_timer = 0
                        pause_bgm()
                        if snd_death:
                            snd_death.play()

    elif game_state == "LEVEL_CLEAR":
        level_clear_timer += 1
        if level_clear_timer >= LEVEL_CLEAR_DURATION_FRAMES:
            load_level(current_level_index + 1, keep_progress=True)
            game_state = "PLAYING"

    elif game_state == "DYING":
        player.death_timer += 1

        # When the animation hits 60 frames (1 full second)
        if player.death_timer >= 60:
            player.lives -= 1
            if player.lives > 0:
                # Still have lives left? Reset the board positions.
                player.reset_position()
                player.clear_powerups()
                for ghost in ghosts:
                    ghost.reset_position()
                game_state = "PLAYING"
                resume_bgm()
            else:
                # No lives left. Game Over.
                game_state = "GAME_OVER"
                stop_bgm()


    # --- DRAWING ---
    screen.fill(BLACK)

    # Draw the map
    for row_idx, row in enumerate(LEVEL_MAP):
        for col_idx, tile in enumerate(row):
            if tile == 1:
                wall_color = BLUE
                if game_state == "LEVEL_CLEAR":
                    blink_on = (level_clear_timer // LEVEL_CLEAR_BLINK_INTERVAL) % 2 == 0
                    wall_color = WHITE if blink_on else BLUE
                wall_rect = pygame.Rect(col_idx * TILE_SIZE, row_idx * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, wall_color, wall_rect, 2)
            elif tile == 0:
                pygame.draw.circle(screen, WHITE, (col_idx * TILE_SIZE + TILE_SIZE // 2, row_idx * TILE_SIZE + TILE_SIZE // 2), 4)
            elif tile == 3:
                pygame.draw.circle(screen, WHITE, (col_idx * TILE_SIZE + TILE_SIZE // 2, row_idx * TILE_SIZE + TILE_SIZE // 2), 9)
            elif tile == 4:
                center_x = col_idx * TILE_SIZE + TILE_SIZE // 2
                center_y = row_idx * TILE_SIZE + TILE_SIZE // 2
                draw_magnet_icon(screen, center_x, center_y, 9)

    if fruit_active:
        fruit_col, fruit_row = FRUIT_POSITION
        fruit_x = (fruit_col * TILE_SIZE) + (TILE_SIZE // 2)
        fruit_y = (fruit_row * TILE_SIZE) + (TILE_SIZE // 2)
        pygame.draw.circle(screen, RED, (fruit_x, fruit_y), 10)
        pygame.draw.circle(screen, GREEN, (fruit_x - 5, fruit_y - 9), 4)
        pygame.draw.circle(screen, PURPLE, (fruit_x + 5, fruit_y - 9), 4)

    # Draw the entities (passing in the game state so they know how to behave)
    player.draw(screen, game_state)
    for ghost in ghosts:
        ghost.draw(screen, game_state)

    # UI: Score
    score_text = font.render(f"SCORE: {player.score}", True, WHITE)
    screen.blit(score_text, (10, ROWS * TILE_SIZE + 10))

    # UI: Lives (Right aligned)
    lives_text = font.render(f"LIVES: {player.lives}", True, YELLOW)
    screen.blit(lives_text, (WIDTH - 150, ROWS * TILE_SIZE + 10))

    if player.magnet_timer > 0:
        magnet_text = font.render("MAGNET", True, CYAN)
        magnet_rect = magnet_text.get_rect(center=(WIDTH // 2, ROWS * TILE_SIZE + (UI_HEIGHT // 2)))
        screen.blit(magnet_text, magnet_rect)

    # UI: Game Over Overlay
    if game_state == "LEVEL_CLEAR":
        clear_text = font.render("LEVEL CLEAR!", True, YELLOW)
        clear_rect = clear_text.get_rect(center=(WIDTH // 2, ROWS * TILE_SIZE + (UI_HEIGHT // 2)))
        screen.blit(clear_text, clear_rect)

    if game_state == "GAME_OVER":
        # Draw a dimming overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(150) # Transparency
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        # Draw the text right in the middle
        go_text = large_font.render("GAME OVER", True, RED)
        text_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        screen.blit(go_text, text_rect)

        restart_text = font.render("Press R to Restart or Q to Quit", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        screen.blit(restart_text, restart_rect)

    if game_state == "PAUSED":
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        paused_text = large_font.render("PAUSED", True, YELLOW)
        paused_rect = paused_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        screen.blit(paused_text, paused_rect)

        controls_text = font.render("Press P or Esc to Resume", True, WHITE)
        controls_rect = controls_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
        screen.blit(controls_text, controls_rect)

        restart_text = font.render("Press R to Restart or Q to Quit", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45))
        screen.blit(restart_text, restart_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()