This is a simple version of pacman with pellets, powerups, bonus fruit, and
a level-clear wall blinking animation.
The grid has each tile at the same size, so a different sized level would
require a different sized window. The file begins with some global constants
such as the level map, colors and sizes that will be needed by multiple
functions. Then it moves into player and ghost classes and then finishes with
the game loop that calles methods of the above classes and draws the board. You
can also reference the diagram below:

main.py
│
├── 1. Imports (pygame, sys, math)
│
├── 2. Settings & Constants
│   ├── Grid & Window Variables (TILE_SIZE, FPS, WIDTH, HEIGHT)
│   ├── Color Definitions
│   └── ORIGINAL_MAP / LEVEL_MAP (The 2D array grid)
│
├── 3. Classes
│   │
│   ├── class Player (Pac-Man)
│   │   ├── __init__(self, start_col, start_row)  # Setup speed, score, lives
│   │   ├── reset_position(self)                  # Sends Pac-Man back to start
│   │   ├── update(self, keys)                    # Movement queue, grid locking, eating
│   │   └── draw(self, surface, game_state)       # Polygon rendering and death animation
│   │
│   └── class Ghost (Blinky, Pinky, Inky, Clyde)
│       ├── __init__(self, start_col, start_row, color, name, delay) # Setup personality
│       ├── reset_position(self)                  # Sends ghost back to the center cage
│       ├── update(self, target_player, blinky_ref) # Pathfinding and AI targeting logic
│       └── draw(self, surface, game_state)       # Draws the dome body and directional eyes
│
├── 4. Main Game Setup
│   ├── Instantiate Player object
│   ├── Instantiate Ghost objects (with distinct personalities and delays)
│   └── Initialize 'game_state' machine ("PLAYING", "DYING", "GAME_OVER")
│
└── 5. Main Game Loop (while running:)
    ├── Event Handling (Window close)
    ├── Logic Updates
    │   ├── PLAYING: Update player/ghosts, check for collisions
    │   └── DYING: Run death timer, deduct lives, trigger resets or Game Over
    ├── Drawing Loop
    │   └── Render background, map tiles, pellets, entities, and UI text
    └── Screen Update (pygame.display.flip & clock tick)