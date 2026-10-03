"""
CS3810 Mini-Project 1 - Test Grids
===================================

This file is COMPLETE. Do not modify it. Your submission will be graded
against this file plus additional hidden grids in the same format.

Grid art format (one character per cell):

    '.'  free, clean cell
    '#'  obstacle (impassable)
    'R'  robot starting position (clean cell)
    'D'  dirty cell
    '*'  robot starting position on a cell that is also dirty

Every grid has exactly one 'R' or '*'. Every dirty cell is reachable from
the start.

Usage
-----
    from test_grids import GRIDS, EXAMPLE, parse_grid
    from vacuum_world import VacuumWorld

    grid, start, dirty = parse_grid(EXAMPLE)
    problem = VacuumWorld(grid, start, dirty)

    for name, art in GRIDS.items():
        grid, start, dirty = parse_grid(art)
        problem = VacuumWorld(grid, start, dirty)
        ...
"""

# ---------------------------------------------------------------------------
# The worked example from the assignment handout (Section 1.1).
# Use this one while you are debugging. It is NOT part of the graded set.
# ---------------------------------------------------------------------------

EXAMPLE = [
    "R.D.",
    ".#.D",
    "D#..",
    "..D.",
]

# ---------------------------------------------------------------------------
# The six graded grids, ordered roughly by difficulty.
#
# name              size   free cells   dirty cells
# ----------------  -----  -----------  -----------
# g1_tiny            3x3        8            2
# g2_open            4x4       16            3
# g3_blocks          4x4       14            5
# g4_pillars         5x5       21            6
# g5_rooms           5x5       21            7
# g6_corridor        6x6       29            9
# ---------------------------------------------------------------------------

G1_TINY = [
    "R..",
    ".#D",
    "D..",
]

G2_OPEN = [
    "R..D",
    "....",
    ".D..",
    "D...",
]

G3_BLOCKS = [
    "R.D.",
    ".#.D",
    "D#.D",
    "..D.",
]

G4_PILLARS = [
    "R..D.",
    ".#.#.",
    "D...D",
    ".#.#.",
    "D.D.D",
]

G5_ROOMS = [
    "R.#.D",
    ".D#.D",
    "...D.",
    "D.#..",
    "D.#.D",
]

G6_CORRIDOR = [
    "R.D..D",
    ".D....",
    "#####.",
    "D..D..",
    ".D#.D.",
    "D..#.D",
]

GRIDS = {
    "g1_tiny": G1_TINY,
    "g2_open": G2_OPEN,
    "g3_blocks": G3_BLOCKS,
    "g4_pillars": G4_PILLARS,
    "g5_rooms": G5_ROOMS,
    "g6_corridor": G6_CORRIDOR,
}


# ---------------------------------------------------------------------------
# Parsing helper (complete - just call it)
# ---------------------------------------------------------------------------

def parse_grid(art):
    """Convert grid art into the arguments VacuumWorld expects.

    Args:
        art: List of equal-length strings using the characters described
             at the top of this file.

    Returns:
        Tuple (grid, start, dirty) where
            grid:  List of strings containing only '.' and '#'
            start: Tuple (row, col)
            dirty: Frozenset of (row, col) tuples

    Raises:
        ValueError: If the art is ragged, has no start, or has two starts.
    """
    if not art:
        raise ValueError("empty grid")

    width = len(art[0])
    if any(len(row) != width for row in art):
        raise ValueError("all rows must have the same length")

    grid = []
    start = None
    dirty = set()

    for r, row in enumerate(art):
        cells = []
        for c, ch in enumerate(row):
            if ch == '#':
                cells.append('#')
                continue
            cells.append('.')
            if ch in ('R', '*'):
                if start is not None:
                    raise ValueError("grid has more than one start position")
                start = (r, c)
            if ch in ('D', '*'):
                dirty.add((r, c))
            if ch not in ('.', 'R', 'D', '*'):
                raise ValueError("unknown grid character: %r" % ch)
        grid.append("".join(cells))

    if start is None:
        raise ValueError("grid has no start position ('R' or '*')")

    return grid, start, frozenset(dirty)


def describe(art):
    """Return a one-line summary of a grid, handy for experiment tables."""
    grid, start, dirty = parse_grid(art)
    rows, cols = len(grid), len(grid[0])
    free = sum(row.count('.') for row in grid)
    return "%dx%d, %d free cells, %d dirty, start=%s" % (
        rows, cols, free, len(dirty), start)


if __name__ == "__main__":
    print("Example grid: %s" % describe(EXAMPLE))
    for name, art in GRIDS.items():
        print("%-14s %s" % (name, describe(art)))
