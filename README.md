# Pac-Man (15113 HW7 Phase 2)

A polished Pac-Man-style game built with `pygame`, now with multiple levels, bonus systems, and game-state UI overlays.

## Features

- Classic pellet collection, scoring, and life system
- Four ghosts with distinct chase behaviors (`Blinky`, `Pinky`, `Inky`, `Clyde`)
- Power pellets that trigger frightened ghost behavior
- Magnet powerups (custom feature) that vacuum nearby pellets through walls
- Timed bonus fruit spawns at score milestones
- Level clear wall-blink animation before advancing
- Multi-level support with per-level maps, spawns, and metadata
- Pause menu (`P`/`Esc`) plus restart/quit options in pause and game-over states
- Fun sound effects and background music

## Controls

- Arrow keys: Move Pac-Man
- `P`: Pause / unpause
- `Esc`: Resume while paused
- `R`: Restart from pause or game over
- `Q`: Quit from pause or game over

## How to Run

1. Install dependencies:
   - `uv sync`
2. Start the game:
   - `uv run python code.py`

If you are not using `uv`, install `pygame` manually and run `python code.py`.

## Project Structure

- `code.py`: Main game loop, entities, rendering, collisions, and state machine
- `levels.py`: Level definitions and helpers for generating level variants

## Gameplay Notes

- Clearing all pellets/powerups completes the current level and loads the next one.
- Losing a life resets player/ghost positions and clears active powerups.
- Ghosts can be eaten during power mode for bonus points.
- The magnet powerup is shown with a custom magnet icon on the map and as UI text when active.