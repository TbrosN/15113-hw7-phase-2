"""Level data and small helpers for Pac-Man."""

import glob
import os
import statistics

_LEVELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels")

# Default ghost roster: name and spawn delay (frames), assigned to G markers in read order.
_DEFAULT_GHOST_ROSTER = [
    ("Blinky", 0),
    ("Pinky", 120),
    ("Inky", 240),
    ("Clyde", 360),
]

_DEFAULT_FRUIT_SPAWN_SCORES = [250, 750]


def clone_map(map_data):
    return [row[:] for row in map_data]


def shift_point(point, delta_col, delta_row):
    col, row = point
    return (col + delta_col, row + delta_row)


def shift_points(points, delta_col, delta_row):
    return [shift_point(point, delta_col, delta_row) for point in points]


def shift_ghost_spawns(ghost_spawns, delta_col, delta_row):
    shifted = []
    for col, row, name, spawn_delay in ghost_spawns:
        shifted.append((col + delta_col, row + delta_row, name, spawn_delay))
    return shifted


def build_level(
    map_data,
    player_start,
    fruit_position,
    power_pellets,
    magnet_powerups,
    ghost_exit,
    ghost_spawns,
    fruit_spawn_scores,
):
    return {
        "map": clone_map(map_data),
        "player_start": player_start,
        "fruit_position": fruit_position,
        "power_pellets": list(power_pellets),
        "magnet_powerups": list(magnet_powerups),
        "ghost_exit": ghost_exit,
        "ghost_spawns": list(ghost_spawns),
        "fruit_spawn_scores": list(fruit_spawn_scores),
    }


def add_wall_padding(level, pad_left=0, pad_right=0, pad_top=0, pad_bottom=0):
    source_map = level["map"]
    source_cols = len(source_map[0])
    padded_cols = source_cols + pad_left + pad_right
    wall_row = [1] * padded_cols

    padded_map = [wall_row[:] for _ in range(pad_top)]
    for row in source_map:
        padded_map.append(([1] * pad_left) + row[:] + ([1] * pad_right))
    padded_map.extend([wall_row[:] for _ in range(pad_bottom)])

    return build_level(
        map_data=padded_map,
        player_start=shift_point(level["player_start"], pad_left, pad_top),
        fruit_position=shift_point(level["fruit_position"], pad_left, pad_top),
        power_pellets=shift_points(level["power_pellets"], pad_left, pad_top),
        magnet_powerups=shift_points(level["magnet_powerups"], pad_left, pad_top),
        ghost_exit=shift_point(level["ghost_exit"], pad_left, pad_top),
        ghost_spawns=shift_ghost_spawns(level["ghost_spawns"], pad_left, pad_top),
        fruit_spawn_scores=level["fruit_spawn_scores"],
    )


def _level_txt_sort_key(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    return (int(stem), stem) if stem.isdigit() else (10**9, stem)


def _pad_rows(lines):
    stripped = [line.rstrip("\r\n") for line in lines]
    if not stripped:
        raise ValueError("level file is empty")
    width = max(len(row) for row in stripped)
    if width == 0:
        raise ValueError("level file has no level content")
    return [row + (" " * (width - len(row))) for row in stripped]


def _infer_ghost_exit(map_data, ghost_cells, preferred_col):
    rows = len(map_data)
    cols = len(map_data[0])
    if not ghost_cells:
        return (preferred_col, max(0, rows // 2))

    min_ghost_row = min(r for _, r in ghost_cells)
    target_row = min_ghost_row - 1
    if target_row < 0:
        target_row = min_ghost_row + 1

    def walkable(col, row):
        if not (0 <= row < rows and 0 <= col < cols):
            return False
        return map_data[row][col] != 1

    if walkable(preferred_col, target_row):
        return (preferred_col, target_row)

    for delta in range(1, cols):
        for sign in (-1, 1):
            c = preferred_col + sign * delta
            if walkable(c, target_row):
                return (c, target_row)

    for r in range(target_row, -1, -1):
        if walkable(preferred_col, r):
            return (preferred_col, r)

    return (preferred_col, max(0, min_ghost_row - 1))


def _default_fruit_position(map_data):
    rows = len(map_data)
    cols = len(map_data[0])
    center = cols // 2
    for r in range(rows - 2, 0, -1):
        for d in range(cols):
            candidates = [center] if d == 0 else []
            if d > 0:
                if center - d >= 0:
                    candidates.append(center - d)
                if center + d < cols:
                    candidates.append(center + d)
            for c in candidates:
                if map_data[r][c] in (0, 2):
                    return (c, r)
    for r in range(rows - 1, -1, -1):
        for c in range(cols):
            if map_data[r][c] in (0, 2):
                return (c, r)
    return (center, max(1, rows // 2))


def parse_level_text(text, fruit_spawn_scores=None):
    """
    Parse a level from ASCII art.

    # wall (1)   . pellet (0)   space open, no pellet (2)
    P player     G ghost spawn (walkable, 2); roster cycles Blinky→Clyde, +360f delay per wave
    O power pellet (counts as path + power list)
    M magnet power-up (path + power + magnet lists)
    F fruit spawn cell (walkable, 2)
    E ghost-exit target tile (walkable, 2) — optional; inferred if omitted
    - treated like wall (decorative door)
    """
    if fruit_spawn_scores is None:
        fruit_spawn_scores = _DEFAULT_FRUIT_SPAWN_SCORES

    rows_raw = text.splitlines()
    padded = _pad_rows(rows_raw)
    height = len(padded)
    width = len(padded[0])

    player_cells = []
    ghost_cells = []
    power_pellets = []
    magnet_powerups = []
    fruit_cells = []
    exit_cells = []

    map_data = [[0] * width for _ in range(height)]

    for r, line in enumerate(padded):
        if len(line) != width:
            raise ValueError(f"row {r} width {len(line)} != expected {width}")
        for c, ch in enumerate(line):
            if ch == "#" or ch == "-":
                map_data[r][c] = 1
            elif ch == ".":
                map_data[r][c] = 0
            elif ch == " ":
                map_data[r][c] = 2
            elif ch == "O":
                map_data[r][c] = 0
                power_pellets.append((c, r))
            elif ch in ("M", "m"):
                map_data[r][c] = 0
                power_pellets.append((c, r))
                magnet_powerups.append((c, r))
            elif ch == "P":
                map_data[r][c] = 2
                player_cells.append((c, r))
            elif ch == "G":
                map_data[r][c] = 2
                ghost_cells.append((c, r))
            elif ch == "F":
                map_data[r][c] = 2
                fruit_cells.append((c, r))
            elif ch == "E":
                map_data[r][c] = 2
                exit_cells.append((c, r))
            else:
                raise ValueError(f"unknown character {ch!r} at ({c}, {r})")

    if len(player_cells) != 1:
        raise ValueError(f"expected exactly one P (player), found {len(player_cells)}")
    player_start = player_cells[0]

    if not ghost_cells:
        raise ValueError("expected at least one G (ghost spawn)")

    roster_n = len(_DEFAULT_GHOST_ROSTER)
    ghost_spawns = []
    for i, (gc, gr) in enumerate(ghost_cells):
        name, base_delay = _DEFAULT_GHOST_ROSTER[i % roster_n]
        wave = i // roster_n
        delay = base_delay + 360 * wave
        ghost_spawns.append((gc, gr, name, delay))

    if exit_cells:
        ghost_exit = exit_cells[0]
        if len(exit_cells) > 1:
            raise ValueError("expected at most one E (ghost exit)")
    else:
        mean_col = int(round(statistics.mean(c for c, _ in ghost_cells)))
        ghost_exit = _infer_ghost_exit(map_data, ghost_cells, mean_col)

    if fruit_cells:
        fruit_position = fruit_cells[0]
        if len(fruit_cells) > 1:
            raise ValueError("expected at most one F (fruit spawn)")
    else:
        fruit_position = _default_fruit_position(map_data)

    return build_level(
        map_data=map_data,
        player_start=player_start,
        fruit_position=fruit_position,
        power_pellets=power_pellets,
        magnet_powerups=magnet_powerups,
        ghost_exit=ghost_exit,
        ghost_spawns=ghost_spawns,
        fruit_spawn_scores=fruit_spawn_scores,
    )


def load_level_from_path(path, fruit_spawn_scores=None):
    with open(path, encoding="utf-8") as f:
        return parse_level_text(f.read(), fruit_spawn_scores=fruit_spawn_scores)


def discover_level_paths(directory=_LEVELS_DIR):
    pattern = os.path.join(directory, "*.txt")
    paths = [p for p in glob.glob(pattern) if os.path.isfile(p)]
    paths.sort(key=_level_txt_sort_key)
    return paths


def load_levels_from_directory(directory=_LEVELS_DIR):
    paths = discover_level_paths(directory)
    if not paths:
        raise FileNotFoundError(f"no level .txt files in {directory!r}")
    return [load_level_from_path(p) for p in paths]


LEVELS = load_levels_from_directory()
