"""
CS3810 Mini-Project 1 - Part 1: The Environment (30 points)
============================================================

Implement the VacuumWorld class below. Do not change any method name or
signature: run_tests.py and the grading harness call them exactly as written.

Reminders from the handout (Section 1.2):

  * A state is ((row, col), frozenset_of_dirty_cells). It must be HASHABLE,
    because your searches will put states into sets and dictionaries. Use a
    tuple for the position and a frozenset for the dirt - a plain set will
    raise TypeError the first time you add it to your explored set.

  * result() must NOT mutate the state it is given. Build and return a new
    one. This is the single most common bug in this project: if you mutate,
    every state sitting in your frontier silently becomes the same state.

  * get_actions() must return actions in the canonical order below, filtered
    down to the legal ones. Illegal actions are never generated: no CLEAN in
    a clean cell, no move into a wall or an obstacle. Determinism here is
    what makes your node counts comparable with everyone else's.
"""

# The canonical action order. Filter this list; do not reorder it.
ACTION_ORDER = ['MOVE_UP', 'MOVE_DOWN', 'MOVE_LEFT', 'MOVE_RIGHT', 'CLEAN']

# Row/column offsets for the four movement actions.
DELTAS = {
    'MOVE_UP': (-1, 0),
    'MOVE_DOWN': (1, 0),
    'MOVE_LEFT': (0, -1),
    'MOVE_RIGHT': (0, 1),
}


class VacuumWorld:
    """A vacuum-cleaning robot problem on a rectangular grid."""

    def __init__(self, grid, start, dirty):
        """
        Args:
            grid:  List of strings or list of lists; '#' marks an obstacle.
            start: Tuple (row, col) - the robot's starting position.
            dirty: Iterable of (row, col) tuples that begin dirty.

        Suggested attributes to set here: self.grid, self.rows, self.cols,
        self.start, self.dirty.
        """
        self.grid = [list(row) for row in grid]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.rows > 0 else 0
        self.start = tuple(start)
        
        iterated_dirty_cells = []
        for i in dirty:
            iterated_dirty_cells.append(tuple(i))
        self.dirty =  frozenset(iterated_dirty_cells)

        if(not(self.is_passable(self.start))):
            raise ValueError("you shall not pass")
        blocked = []

        for i in self.dirty:
            if(not(self.is_passable(i))):
                blocked.append(i)
        if(blocked):
            raise ValueError("blocked dirty cells: {}".format(blocked))

    # -- helpers ---------------------------------------------------------
    # These two are not graded directly and not called by the test harness,
    # but get_actions() and result() are much shorter if you write them.

    def in_bounds(self, pos):
        """Return True if pos is inside the grid."""
        row, col = pos
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_passable(self, pos):
        """Return True if pos is in bounds and is not an obstacle."""
        return self.in_bounds(pos) and self.grid[pos[0]][pos[1]] != '#'

    # -- problem interface -----------------------------------------------

    def initial_state(self):
        """Return the initial state as ((row, col), frozenset(dirty))."""
        return (self.start, self.dirty)

    def is_goal(self, state):
        """Return True if the dirty set in `state` is empty."""
        return not(state[1])

    def get_actions(self, state):
        """Return a list of legal action names available in `state`.

        Legal means: moves stay in bounds and off obstacles, and CLEAN is
        only offered when the robot's current cell is dirty. Return the
        actions in ACTION_ORDER order.
        """
        (row, col), dirty = state
        actions = []

        for i in ACTION_ORDER:
            if(i == 'CLEAN'):
                if((row, col) in dirty):
                    actions.append(i)
            else:
                row1, col1 = DELTAS[i]
                if(self.is_passable((row + row1, col + col1))):
                    actions.append(i)
        return actions

    def result(self, state, action):
        """Return the successor state produced by applying `action`.

        Must not modify `state`.
        """
        pos, dirty = state
        if(action == 'CLEAN'):
            return (pos, dirty - {pos})
        if(action in DELTAS):
            drow, dcol = DELTAS[action]
            target = (pos[0] + drow, pos[1] + dcol)
            if(not(self.is_passable(target))):
                return state
            return (target, dirty)
        raise ValueError("Invalid action {}: {}".format(action, state))

    def action_cost(self, state, action):
        """Return the cost of `action` in `state` (always 1 here).""" # Then just set it as 1?? why is this necessary
        return 1 #???

    # -- debugging -------------------------------------------------------

    def render(self, state=None):
        """Return a printable picture of `state` (defaults to the initial state).

        Use the same characters as test_grids.py: '#' obstacle, 'R' robot,
        'D' dirty, '*' robot on a dirty cell, '.' clean and empty.

        This is not graded for correctness, but you will use it constantly
        while debugging. Write it first.
        """
        if(state == None):
            state = self.initial_state()
        robot, dirty = state
        lines = []
        for i in range(self.rows):
            tableau = []
            for j in range(self.cols):
                c = (i, j)
                if(self.grid[i][j] == '#'):
                    tableau.append('#')
                elif(c == robot and c in dirty):
                    tableau.append('*')
                elif(c == robot):
                    tableau.append('R')
                elif(c in dirty):
                    tableau.append('D')
                else:
                    tableau.append('.')
            lines.append(''.join(tableau))
        return '\n'.join(lines)

    def __str__(self):
        return self.render()


if(__name__ == "__main__"):
    # Quick manual check once you have implemented the class:
    from test_grids import EXAMPLE, parse_grid

    grid, start, dirty = parse_grid(EXAMPLE)
    problem = VacuumWorld(grid, start, dirty)
    print(problem.render())
    print("initial state:", problem.initial_state())
    print("legal actions:", problem.get_actions(problem.initial_state()))
