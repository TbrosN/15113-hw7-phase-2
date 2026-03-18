import pygame
import sys
import math

# --- 1. SETTINGS & CONSTANTS ---
pygame.init()

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

# Master map copy
ORIGINAL_MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 0, 1, 1, 1, 2, 1, 2, 1, 1, 1, 0, 1, 1, 1, 1],
    [2, 2, 2, 1, 0, 1, 2, 2, 2, 2, 2, 2, 2, 1, 0, 1, 2, 2, 2],
    [1, 1, 1, 1, 0, 1, 2, 1, 1, 2, 1, 1, 2, 1, 0, 1, 1, 1, 1],
    [2, 2, 2, 2, 0, 2, 2, 1, 2, 2, 2, 1, 2, 2, 0, 2, 2, 2, 2],
    [1, 1, 1, 1, 0, 1, 2, 1, 1, 1, 1, 1, 2, 1, 0, 1, 1, 1, 1],
    [2, 2, 2, 1, 0, 1, 2, 2, 2, 2, 2, 2, 2, 1, 0, 1, 2, 2, 2],
    [1, 1, 1, 1, 0, 1, 2, 1, 1, 1, 1, 1, 2, 1, 0, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

PLAYER_START = (1, 1)
FRUIT_POSITION = (9, 11)
FRUIT_SPAWN_SCORES = [250, 750]
POWER_PELLET_POSITIONS = [(1, 3), (17, 3), (1, 15), (17, 15)]
GHOST_EXIT = (9, 7)
GHOST_CONFIGS = [
    (9, 9, RED, "Blinky", 0),
    (9, 9, PINK, "Pinky", FPS * 2),
    (8, 9, CYAN, "Inky", FPS * 4),
    (10, 9, ORANGE, "Clyde", FPS * 6),
]

LEVEL_MAP = [[tile for tile in row] for row in ORIGINAL_MAP]
COLS = len(LEVEL_MAP[0])
ROWS = len(LEVEL_MAP)
WIDTH = COLS * TILE_SIZE
UI_HEIGHT = 50
HEIGHT = (ROWS * TILE_SIZE) + UI_HEIGHT

POWERUP_DURATION_FRAMES = FPS * 8
FRUIT_DURATION_FRAMES = FPS * 8
LEVEL_CLEAR_DURATION_FRAMES = FPS * 2
LEVEL_CLEAR_BLINK_INTERVAL = 8


def place_power_pellets():
    for col, row in POWER_PELLET_POSITIONS:
        if LEVEL_MAP[row][col] != 1:
            LEVEL_MAP[row][col] = 3


def reset_board_map():
    for r in range(ROWS):
        for c in range(COLS):
            LEVEL_MAP[r][c] = ORIGINAL_MAP[r][c]
    place_power_pellets()


reset_board_map()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man: Life and Death")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)
large_font = pygame.font.SysFont("Arial", 48, bold=True)


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

        self.reset_position()

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
        if LEVEL_MAP[current_row][current_col] == 0:
            LEVEL_MAP[current_row][current_col] = 2
            self.score += 10
        elif LEVEL_MAP[current_row][current_col] == 3:
            LEVEL_MAP[current_row][current_col] = 2
            self.score += 50
            self.power_timer = POWERUP_DURATION_FRAMES
            ate_powerup = True

        if self.power_timer > 0:
            self.power_timer -= 1

        has_pellets_left = any(0 in row or 3 in row for row in LEVEL_MAP)
        if not has_pellets_left:
            cleared_board = True

        return ate_powerup, cleared_board

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


# --- 4. MAIN GAME SETUP ---
player = Player(PLAYER_START[0], PLAYER_START[1])
ghosts = [Ghost(*ghost_config) for ghost_config in GHOST_CONFIGS]
blinky = next((ghost for ghost in ghosts if ghost.name == "Blinky"), ghosts[0])

# NEW: The core state machine
game_state = "PLAYING" # Can be: PLAYING, LEVEL_CLEAR, DYING, GAME_OVER
level_clear_timer = 0

fruit_active = False
fruit_timer = 0
next_fruit_index = 0

# --- 5. GAME LOOP ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- LOGIC UPDATES ---
    if game_state == "PLAYING":
        keys = pygame.key.get_pressed()
        ate_powerup, cleared_board = player.update(keys)

        if ate_powerup:
            # Quick turnaround when the player grabs a power pellet.
            for ghost in ghosts:
                if ghost.state == "chasing":
                    ghost.dx *= -1
                    ghost.dy *= -1

        if cleared_board:
            game_state = "LEVEL_CLEAR"
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
                    else:
                        game_state = "DYING"
                        player.death_timer = 0

    elif game_state == "LEVEL_CLEAR":
        level_clear_timer += 1
        if level_clear_timer >= LEVEL_CLEAR_DURATION_FRAMES:
            reset_board_map()
            player.reset_position()
            player.power_timer = 0
            for ghost in ghosts:
                ghost.reset_position()
            game_state = "PLAYING"

    elif game_state == "DYING":
        player.death_timer += 1

        # When the animation hits 60 frames (1 full second)
        if player.death_timer >= 60:
            player.lives -= 1
            if player.lives > 0:
                # Still have lives left? Reset the board positions.
                player.reset_position()
                for ghost in ghosts:
                    ghost.reset_position()
                game_state = "PLAYING"
            else:
                # No lives left. Game Over.
                game_state = "GAME_OVER"


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
        text_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(go_text, text_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()