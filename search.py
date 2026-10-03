"""
CS3810 Mini-Project 1 - Part 2: The Search Algorithms (100 points)
==================================================================

Implement dfs_search, astar_search, and idastar_search below. Do not change
the signatures or the return shapes: run_tests.py and the grading harness
unpack them exactly as documented.

You may NOT use a library implementation of DFS, A*, or IDA* (networkx,
simpleai, aima-python, ...). Using heapq, collections.deque, and the
provided PriorityQueue is expected and fine.

Metric definitions - use these, and say which you used in your report:

    nodes_expanded      A node is EXPANDED when it is removed from the
                        frontier and its successors are generated. Do not
                        count nodes that were merely generated.

    max_frontier_size   The largest number of live entries the frontier
                        ever held. For the PriorityQueue helper this is
                        len(queue), not len(queue.heap).

    iterations          (IDA* only) The number of depth-limited passes,
                        i.e. how many times the f-cost threshold was set.
                        A search that succeeds on the first threshold has
                        iterations == 1.

Suggested order of work: DFS first, then A*, then IDA*.
"""

import math

from priority_queue import PriorityQueue

# Sentinel used by the IDA* recursion to report success. Returning a plain
# number means "the smallest f-value I saw above the threshold".
FOUND = 'FOUND'


def dfs_search(problem):
    """
    Perform Depth-First Search.

    Args:
        problem: VacuumWorld instance

    Returns:
        Tuple (solution_path, nodes_expanded, max_frontier_size)
        solution_path: List of actions, or None if no solution
        nodes_expanded: Number of nodes expanded during search
        max_frontier_size: Maximum size of frontier during search

    Requirements:
        * Iterative, with an explicit stack. Do NOT recurse - you will hit
          Python's recursion limit on the larger grids.
        * Cycle detection with an explored set, or DFS will not terminate.
        * Returns the FIRST solution found. It will not be optimal, and it
          is not supposed to be.

    Hint: push (state, path_so_far) pairs. Push successors in reversed()
    order if you want the stack to explore them in ACTION_ORDER order.
    """
    start = problem.initial_state()
    stack = [(start, [])]
    explored = set()
    nodes_expanded = 0
    max_frontier_size = len(stack)

    while stack:
        state, solution_path = stack.pop()
        if(state in explored):
            continue
        
        if(problem.is_goal(state)):
            return solution_path, nodes_expanded, max_frontier_size

        explored.add(state)
        nodes_expanded += 1 #I miss ++
        # Reversed to keep the correct order of actions, cause it's a stack 
        for i in reversed(problem.get_actions(state)):
            child = problem.result(state, i)
            if(not(child in explored)):
                stack.append((child, solution_path + [i]))
        max_frontier_size = max(max_frontier_size, len(stack))

    solution_path = None
    return solution_path, nodes_expanded, max_frontier_size

def astar_search(problem, heuristic):
    """
    Perform A* Search.

    Args:
        problem: VacuumWorld instance
        heuristic: Function h(state, problem) -> estimated cost to goal

    Returns:
        Tuple (solution_path, nodes_expanded, max_frontier_size)

    Requirements:
        * Priority queue ordered by f(n) = g(n) + h(n).
        * Handle REOPENING: if you find a cheaper path to a state you have
          already expanded, you must be able to improve it. The provided
          PriorityQueue supports this - pushing an item already in the
          queue replaces its priority instead of duplicating it.
        * With an admissible heuristic this MUST return an optimal
          solution. run_tests.py checks that against known optimal costs.

    Hint: keep a dict g[state] of best-known cost-so-far and a dict
    came_from[state] = (parent_state, action) to rebuild the path at the
    end. A helper like _reconstruct() below keeps the main loop readable.
    """
    start = problem.initial_state()
    current_frontier = PriorityQueue()
    current_frontier.push(start, heuristic(start, problem))
    g = {start: 0}
    came_from = {start: None}
    nodes_expanded = 0
    max_frontier_size = len(current_frontier)

    while current_frontier:
        state = current_frontier.pop()
        if(problem.is_goal(state)):
            return _reconstruct(came_from, state), nodes_expanded, max_frontier_size

        nodes_expanded += 1
        for i in problem.get_actions(state):
            child = problem.result(state, i)
            g1 = g[state] + problem.action_cost(state, i)
            if(not(child in g) or g1 < g[child]):
                g[child] = g1
                came_from[child] = (state, i)
                f = g1 + heuristic(child, problem)
                current_frontier.push(child, f)
        max_frontier_size = max(max_frontier_size, len(current_frontier))

    solution_path = None
    return solution_path, nodes_expanded, max_frontier_size


def _reconstruct(came_from, state):
    """Walk came_from backwards from `state` and return the action list.

    Args:
        came_from: Dict mapping state -> (parent_state, action)
        state: The goal state reached by the search

    Returns:
        List of actions from the initial state to `state`.
    """
    actions = []
    while came_from[state]!=None:
        state, action = came_from[state]
        actions.append(action)
    actions.reverse()
    return actions


def idastar_search(problem, heuristic):
    """
    Perform Iterative Deepening A* Search.

    Args:
        problem: VacuumWorld instance
        heuristic: Function h(state, problem) -> estimated cost to goal

    Returns:
        Tuple (solution_path, nodes_expanded, iterations)
        iterations: Number of depth-limited iterations performed

    Requirements:
        * Iterative deepening on an f-cost THRESHOLD, not on depth. The
          next threshold is the smallest f-value that exceeded the current
          one.
        * Linear space: no explored set carried across iterations. You may
          track the states on the current path to avoid immediate cycles.
        * Returns an optimal solution.

    Structure that works (write DFS and A* first - this will make far more
    sense once you have both):

        threshold = h(start)
        loop:
            result = search(start, g=0, threshold)
            if result is FOUND:    return the path
            if result is infinite: return None (no solution)
            threshold = result

    where search(state, g, threshold) returns FOUND, or the smallest
    f-value it saw that exceeded the threshold, or math.inf.
    """
    start = problem.initial_state()
    path = [] # solution path isn't mentioned anywhere here, and solution_path is annoying to write instead of path
    on_path = {start} # solution path isn't mentioned anywhere here, and on_solution_path is annoying to write
    num_nodes_expanded = {'nodes_expanded': 0}
    threshold = heuristic(start, problem)
    empty_cells = 0
    for row in range(problem.rows):
        for col in range(problem.cols):
            if(problem.is_passable((row, col))):
                empty_cells += 1
    # there's probably a cleaner way to do this in one line, but not sure ^

    max_cost = len(start[1]) * empty_cells
    iterations = 0
    while True:
        iterations += 1
        result = search(problem, heuristic, start, 0, threshold, path, on_path, num_nodes_expanded)
        if(result == FOUND):
            return list(path), num_nodes_expanded['nodes_expanded'], iterations
        if(result > max_cost):
            return None, num_nodes_expanded['nodes_expanded'], iterations
        threshold = result

# helper method for idastar_search
def search(problem, heuristic, state, g, threshold, path, on_path, counts):
    f = g + heuristic(state, problem)
    if(f > threshold):
        return f
    if(problem.is_goal(state)):
        return FOUND

    counts['nodes_expanded'] += 1
    smallest = math.inf
    for action in problem.get_actions(state):
        child = problem.result(state, action)
        if(child in on_path):
            continue
        path.append(action)
        on_path.add(child)
        result = search(problem, heuristic, child,
                        g + problem.action_cost(state, action),
                        threshold, path, on_path, counts)
        if(result == FOUND):
            return FOUND
        path.pop()
        on_path.remove(child)
        smallest = min(smallest, result)
    return smallest

if(__name__ == "__main__"):
    # Quick manual check once you have implemented an algorithm:
    from test_grids import EXAMPLE, parse_grid
    from vacuum_world import VacuumWorld
    from heuristics import h2

    grid, start, dirty = parse_grid(EXAMPLE)
    problem = VacuumWorld(grid, start, dirty)

    path, expanded, frontier = astar_search(problem, h2)
    print("A* on the example grid (optimal cost is 14)")
    print("  cost     :", len(path) if path else None)
    print("  expanded :", expanded)
    print("  frontier :", frontier)
    print("  plan     :", path)
