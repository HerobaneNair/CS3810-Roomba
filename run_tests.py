"""
CS3810 Mini-Project 1 - Smoke Tests
====================================

Run this before you submit:

    python run_tests.py

Graders run it first. If it reports a FAIL, your submission is not ready.

These are SMOKE tests, not the grading rubric. Passing everything here means
your code runs and agrees with the spec on the cases below; it does not mean
you have earned full marks. The report, the experiments, and the heuristic
arguments are graded separately by a human.

Anything you have not implemented yet shows up as SKIP, not FAIL, so this is
useful from day one. Run it early and often.

This file is COMPLETE. Do not modify it - the graders use their own copy.
"""

import sys
import traceback

from test_grids import EXAMPLE, GRIDS, parse_grid

# Known optimal costs, computed by the instructor's reference solution.
# Every admissible heuristic must produce exactly these costs with A* and
# with IDA*.
EXPECTED_OPTIMAL = {
    'example': 14,
    'g1_tiny': 7,
    'g2_open': 12,
    'g3_blocks': 15,
    'g4_pillars': 19,
    'g5_rooms': 25,
    'g6_corridor': 32,
}

ALL_ART = dict(GRIDS)
ALL_ART['example'] = EXAMPLE

CANONICAL_ORDER = ['MOVE_UP', 'MOVE_DOWN', 'MOVE_LEFT', 'MOVE_RIGHT', 'CLEAN']

_TESTS = []


def test(part, name):
    """Register a test function."""
    def wrap(fn):
        _TESTS.append((part, name, fn))
        return fn
    return wrap


class Failure(Exception):
    pass


def check(condition, message):
    if not condition:
        raise Failure(message)


def check_equal(got, want, message):
    if got != want:
        raise Failure("%s\n      expected: %r\n      got:      %r"
                      % (message, want, got))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def build(name):
    """Construct a VacuumWorld for a named grid."""
    from vacuum_world import VacuumWorld
    grid, start, dirty = parse_grid(ALL_ART[name])
    return VacuumWorld(grid, start, dirty)


def walk(problem, actions):
    """Apply a sequence of actions from the initial state, returning the state."""
    state = problem.initial_state()
    for action in actions:
        state = problem.result(state, action)
    return state


def validate_plan(problem, plan, label):
    """Check that `plan` is executable from the initial state and reaches the goal."""
    check(plan is not None, "%s returned None - no solution found" % label)
    state = problem.initial_state()
    for i, action in enumerate(plan):
        legal = problem.get_actions(state)
        check(action in legal,
              "%s: action %d (%s) is not legal in the state reached so far "
              "(legal actions were %s)" % (label, i, action, legal))
        state = problem.result(state, action)
    check(problem.is_goal(state),
          "%s: plan of length %d finished without cleaning everything "
          "(%d dirty cells left)" % (label, len(plan), len(state[1])))


def sample_states(problem, limit=40):
    """Collect a handful of reachable states by breadth-first expansion."""
    seen = [problem.initial_state()]
    index = 0
    while index < len(seen) and len(seen) < limit:
        state = seen[index]
        index += 1
        for action in problem.get_actions(state):
            nxt = problem.result(state, action)
            if nxt not in seen:
                seen.append(nxt)
                if len(seen) >= limit:
                    break
    return seen


# ---------------------------------------------------------------------------
# Part 1 - the environment
# ---------------------------------------------------------------------------

@test("Part 1", "initial_state has the documented shape and is hashable")
def t_initial_shape():
    problem = build('example')
    state = problem.initial_state()
    check(isinstance(state, tuple) and len(state) == 2,
          "initial_state() must return a 2-tuple (position, dirty_set)")
    pos, dirty = state
    check(isinstance(pos, tuple) and len(pos) == 2,
          "position must be a (row, col) tuple")
    check(isinstance(dirty, frozenset),
          "the dirty set must be a frozenset (a plain set is not hashable)")
    check_equal(pos, (0, 0), "example grid starts at (0, 0)")
    check_equal(sorted(dirty), [(0, 2), (1, 3), (2, 0), (3, 2)],
                "example grid dirty cells")
    hash(state)  # raises TypeError if the state is unhashable


@test("Part 1", "is_goal is true only when nothing is dirty")
def t_is_goal():
    problem = build('example')
    start = problem.initial_state()
    check(not problem.is_goal(start), "the initial state is not a goal")
    check(problem.is_goal(((0, 0), frozenset())),
          "a state with an empty dirty set is a goal")


@test("Part 1", "get_actions respects bounds, obstacles, and dirt")
def t_get_actions():
    problem = build('example')
    start = problem.initial_state()

    check_equal(problem.get_actions(start), ['MOVE_DOWN', 'MOVE_RIGHT'],
                "at (0,0): up and left leave the grid, and the cell is clean "
                "so CLEAN must not be offered")

    on_dirt = walk(problem, ['MOVE_RIGHT', 'MOVE_RIGHT'])
    check_equal(problem.get_actions(on_dirt),
                ['MOVE_DOWN', 'MOVE_LEFT', 'MOVE_RIGHT', 'CLEAN'],
                "at (0,2): the cell is dirty, so CLEAN is legal and comes last")

    by_wall = walk(problem, ['MOVE_DOWN'])
    check_equal(problem.get_actions(by_wall), ['MOVE_UP', 'MOVE_DOWN'],
                "at (1,0): left leaves the grid and right is the obstacle (1,1)")


@test("Part 1", "get_actions is deterministic and in canonical order")
def t_action_order():
    problem = build('example')
    for state in sample_states(problem, limit=25):
        actions = problem.get_actions(state)
        check_equal(problem.get_actions(state), actions,
                    "two calls on the same state must return the same list")
        positions = [CANONICAL_ORDER.index(a) for a in actions]
        check(positions == sorted(positions),
              "actions must come back in ACTION_ORDER order, got %s" % actions)
        check(len(set(actions)) == len(actions),
              "get_actions returned a duplicate action: %s" % actions)


@test("Part 1", "result does not mutate the state it is given")
def t_result_immutable():
    problem = build('example')
    state = problem.initial_state()
    before = (tuple(state[0]), frozenset(state[1]))
    problem.result(state, 'MOVE_DOWN')
    problem.result(state, 'MOVE_RIGHT')
    check_equal(state, before,
                "result() modified its argument - build and return a NEW state")


@test("Part 1", "result moves and cleans correctly")
def t_result_correct():
    problem = build('example')
    start = problem.initial_state()

    moved = problem.result(start, 'MOVE_DOWN')
    check_equal(moved[0], (1, 0), "MOVE_DOWN from (0,0)")
    check_equal(moved[1], start[1], "moving must not change the dirty set")

    on_dirt = walk(problem, ['MOVE_RIGHT', 'MOVE_RIGHT'])
    cleaned = problem.result(on_dirt, 'CLEAN')
    check_equal(cleaned[0], (0, 2), "CLEAN must not move the robot")
    check((0, 2) not in cleaned[1], "CLEAN must remove the cell from the dirty set")
    check_equal(len(cleaned[1]), len(on_dirt[1]) - 1,
                "CLEAN must remove exactly one dirty cell")


@test("Part 1", "action_cost is 1 for every action")
def t_action_cost():
    problem = build('example')
    state = problem.initial_state()
    for action in problem.get_actions(state):
        check_equal(problem.action_cost(state, action), 1,
                    "every action costs 1 in this problem")


# ---------------------------------------------------------------------------
# Part 3 - heuristics (tested before Part 2 because the searches need them)
# ---------------------------------------------------------------------------

@test("Part 3", "manhattan distance")
def t_manhattan():
    from heuristics import manhattan
    check_equal(manhattan((0, 0), (0, 0)), 0, "distance to itself")
    check_equal(manhattan((0, 0), (3, 2)), 5, "distance (0,0) -> (3,2)")
    check_equal(manhattan((3, 2), (0, 0)), 5, "distance is symmetric")


@test("Part 3", "h0 is zero and h1 counts dirty cells")
def t_h0_h1():
    from heuristics import h0, h1
    problem = build('example')
    for state in sample_states(problem, limit=20):
        check_equal(h0(state, problem), 0, "h0 must always be 0")
        check_equal(h1(state, problem), len(state[1]),
                    "h1 must be the number of remaining dirty cells")


@test("Part 3", "h2 dominates h1 and is zero at the goal")
def t_h2():
    from heuristics import h1, h2
    problem = build('example')
    goal = ((0, 0), frozenset())
    check_equal(h2(goal, problem), 0, "every heuristic must be 0 at a goal state")
    for state in sample_states(problem, limit=40):
        check(h2(state, problem) >= h1(state, problem),
              "h2 must be >= h1 at every state (it adds a non-negative term)")


@test("Part 3", "h1 and h2 are admissible on every graded grid")
def t_admissible():
    from heuristics import h1, h2
    for name, optimal in sorted(EXPECTED_OPTIMAL.items()):
        problem = build(name)
        start = problem.initial_state()
        for label, fn in (('h1', h1), ('h2', h2)):
            value = fn(start, problem)
            check(value <= optimal,
                  "%s overestimates on %s: h=%d but the optimal cost is %d. "
                  "An inadmissible heuristic breaks A*'s optimality guarantee."
                  % (label, name, value, optimal))


@test("Part 3", "h3 bonus: admissible and dominates h2")
def t_h3():
    from heuristics import h2, h3
    problem = build('example')
    h3(problem.initial_state(), problem)  # raises NotImplementedError -> SKIP

    goal = ((0, 0), frozenset())
    check_equal(h3(goal, problem), 0, "h3 must be 0 at a goal state")
    for state in sample_states(problem, limit=40):
        check(h3(state, problem) >= h2(state, problem),
              "to earn the bonus, h3 must dominate h2 (h3 >= h2 everywhere)")
    for name, optimal in sorted(EXPECTED_OPTIMAL.items()):
        p = build(name)
        value = h3(p.initial_state(), p)
        check(value <= optimal,
              "h3 overestimates on %s: h=%d but the optimal cost is %d"
              % (name, value, optimal))


# ---------------------------------------------------------------------------
# Part 2 - the search algorithms
# ---------------------------------------------------------------------------

@test("Part 2a", "DFS returns an executable plan and sane metrics")
def t_dfs():
    from search import dfs_search
    for name in ('example', 'g1_tiny', 'g2_open', 'g3_blocks'):
        problem = build(name)
        result = dfs_search(problem)
        check(isinstance(result, tuple) and len(result) == 3,
              "dfs_search must return (plan, nodes_expanded, max_frontier_size)")
        plan, expanded, frontier = result
        validate_plan(problem, plan, "DFS on %s" % name)
        check(isinstance(expanded, int) and expanded > 0,
              "nodes_expanded must be a positive int, got %r" % (expanded,))
        check(isinstance(frontier, int) and frontier > 0,
              "max_frontier_size must be a positive int, got %r" % (frontier,))


@test("Part 2b", "A* returns optimal plans with h1 and h2")
def t_astar():
    from search import astar_search
    from heuristics import h1, h2
    for name in ('example', 'g1_tiny', 'g2_open', 'g3_blocks', 'g4_pillars'):
        problem = build(name)
        for label, fn in (('h1', h1), ('h2', h2)):
            result = astar_search(build(name), fn)
            check(isinstance(result, tuple) and len(result) == 3,
                  "astar_search must return (plan, nodes_expanded, max_frontier_size)")
            plan, expanded, frontier = result
            validate_plan(problem, plan, "A*/%s on %s" % (label, name))
            check_equal(len(plan), EXPECTED_OPTIMAL[name],
                        "A* with the admissible heuristic %s must be optimal on %s"
                        % (label, name))
            check(isinstance(expanded, int) and expanded > 0,
                  "nodes_expanded must be a positive int")
            check(isinstance(frontier, int) and frontier > 0,
                  "max_frontier_size must be a positive int")


@test("Part 2b", "A* expands no more nodes with h2 than with h0")
def t_astar_informed():
    from search import astar_search
    from heuristics import h0, h2
    for name in ('g3_blocks', 'g4_pillars'):
        _, uninformed, _ = astar_search(build(name), h0)
        _, informed, _ = astar_search(build(name), h2)
        check(informed <= uninformed,
              "on %s, A* expanded %d nodes with h2 but only %d with h0 - a "
              "dominant heuristic should never expand more. Check that you "
              "order the frontier by f = g + h, not by h alone."
              % (name, informed, uninformed))


@test("Part 2c", "IDA* returns optimal plans and counts iterations")
def t_idastar():
    from search import idastar_search
    from heuristics import h2
    for name in ('example', 'g1_tiny', 'g2_open', 'g3_blocks'):
        problem = build(name)
        result = idastar_search(build(name), h2)
        check(isinstance(result, tuple) and len(result) == 3,
              "idastar_search must return (plan, nodes_expanded, iterations)")
        plan, expanded, iterations = result
        validate_plan(problem, plan, "IDA* on %s" % name)
        check_equal(len(plan), EXPECTED_OPTIMAL[name],
                    "IDA* with an admissible heuristic must be optimal on %s" % name)
        check(isinstance(iterations, int) and iterations >= 1,
              "iterations must be a positive int, got %r" % (iterations,))
        check(isinstance(expanded, int) and expanded > 0,
              "nodes_expanded must be a positive int")


@test("Part 2", "A* and IDA* agree, and both beat DFS on cost")
def t_agreement():
    from search import dfs_search, astar_search, idastar_search
    from heuristics import h2
    for name in ('example', 'g2_open', 'g3_blocks'):
        astar_plan, _, _ = astar_search(build(name), h2)
        ida_plan, _, _ = idastar_search(build(name), h2)
        dfs_plan, _, _ = dfs_search(build(name))
        check_equal(len(ida_plan), len(astar_plan),
                    "A* and IDA* must find the same optimal cost on %s" % name)
        check(len(astar_plan) <= len(dfs_plan),
              "on %s the optimal plan (%d) is longer than DFS's plan (%d), "
              "which is impossible - one of them is wrong"
              % (name, len(astar_plan), len(dfs_plan)))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    width = 62
    passed = failed = skipped = 0
    current_part = None
    failures = []

    print("=" * width)
    print("CS3810 Mini-Project 1 - smoke tests")
    print("=" * width)

    for part, name, fn in _TESTS:
        if part != current_part:
            print("\n%s" % part)
            current_part = part
        try:
            fn()
        except NotImplementedError as exc:
            skipped += 1
            print("  SKIP  %s" % name)
            print("        (not implemented yet: %s)" % exc)
        except Failure as exc:
            failed += 1
            failures.append((name, str(exc)))
            print("  FAIL  %s" % name)
            print("        %s" % exc)
        except Exception:
            failed += 1
            trace = traceback.format_exc().strip().splitlines()[-1]
            failures.append((name, trace))
            print("  ERROR %s" % name)
            print("        %s" % trace)
            for line in traceback.format_exc().strip().splitlines()[-4:-1]:
                print("        %s" % line.strip())
        else:
            passed += 1
            print("  PASS  %s" % name)

    print("\n" + "=" * width)
    print("%d passed, %d failed, %d skipped" % (passed, failed, skipped))

    if failed:
        print("\nNOT READY TO SUBMIT - fix the failures above.")
    elif skipped:
        print("\nNothing is broken, but %d test(s) are still skipped." % skipped)
        print("Anything other than the h3 bonus needs to be implemented.")
    else:
        print("\nAll smoke tests pass. Now do the experiments and the report -")
        print("that is 70 of the 200 points, and these tests do not check it.")
    print("=" * width)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
