"""Level data and small helpers for Pac-Man."""


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


LEVEL_ONE_MAP = [
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
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

DEFAULT_GHOST_SPAWNS = [
    (9, 9, "Blinky", 0),
    (9, 9, "Pinky", 120),
    (8, 9, "Inky", 240),
    (10, 9, "Clyde", 360),
]

LEVEL_ONE = build_level(
    map_data=LEVEL_ONE_MAP,
    player_start=(1, 1),
    fruit_position=(9, 11),
    power_pellets=[(1, 3), (17, 3), (1, 15), (17, 15)],
    magnet_powerups=[(1, 3), (17, 15)],
    ghost_exit=(9, 7),
    ghost_spawns=DEFAULT_GHOST_SPAWNS,
    fruit_spawn_scores=[250, 750],
)

# Minimal generated variant: same maze with extra wall rows to change window height.
LEVEL_TWO = add_wall_padding(LEVEL_ONE, pad_top=1, pad_bottom=1)

LEVELS = [LEVEL_TWO, LEVEL_ONE]
