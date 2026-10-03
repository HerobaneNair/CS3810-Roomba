"""
CS3810 Mini-Project 1 - Part 4: Experiment Harness (30 points)
==============================================================

The measurement plumbing is written for you: this file runs every
grid x algorithm x heuristic combination in a subprocess with a timeout,
and writes the raw numbers to results.csv.

    python experiments.py                 # full run, 60s timeout per config
    python experiments.py --quick         # small grids only, for a fast check
    python experiments.py --timeout 120   # be more patient
    python experiments.py --grids g5_rooms g6_corridor

What is left for YOU is at the bottom of the file: turning results.csv into
the table and the two plots your report needs. That part is graded; this
part is not.

A note on timeouts. Some configurations are genuinely infeasible - IDA* with
a weak heuristic on the larger grids will re-expand millions of nodes. A row
marked TIMEOUT is a real finding and belongs in your table. Do not delete it,
and do not raise the timeout until the number is "nicer". Discuss it.

A note on runtime. Compare NODE COUNTS across algorithms; they are a property
of the algorithm. Wall-clock time is a property of your laptop, your Python
version, and what else you had open. Use it as supporting evidence only.
"""

import argparse
import csv
import multiprocessing as mp
import os
import queue as queue_mod
import sys
import time

from test_grids import GRIDS, EXAMPLE, parse_grid

# Every combination the harness will try.
ALGORITHMS = ['dfs', 'astar', 'idastar']
HEURISTIC_NAMES = ['h0', 'h1', 'h2', 'h3']

# DFS ignores the heuristic, so it is run once per grid with this label.
NO_HEURISTIC = '-'

QUICK_GRIDS = ['g1_tiny', 'g2_open', 'g3_blocks']

CSV_FIELDS = [
    'grid', 'rows', 'cols', 'n_dirty',
    'algorithm', 'heuristic', 'status',
    'cost', 'nodes_expanded', 'max_frontier', 'iterations', 'seconds',
]


# ---------------------------------------------------------------------------
# Running one configuration
# ---------------------------------------------------------------------------

def build_problem(grid_name):
    """Construct a VacuumWorld for a named grid."""
    from vacuum_world import VacuumWorld
    art = EXAMPLE if grid_name == 'example' else GRIDS[grid_name]
    grid, start, dirty = parse_grid(art)
    return VacuumWorld(grid, start, dirty)


def run_single(algorithm, grid_name, heuristic_name):
    """Run one configuration and return a result dict. Runs in a subprocess."""
    from search import dfs_search, astar_search, idastar_search
    from heuristics import HEURISTICS

    problem = build_problem(grid_name)
    started = time.perf_counter()

    if algorithm == 'dfs':
        plan, expanded, frontier = dfs_search(problem)
        iterations = None
    elif algorithm == 'astar':
        plan, expanded, frontier = astar_search(problem, HEURISTICS[heuristic_name])
        iterations = None
    elif algorithm == 'idastar':
        plan, expanded, iterations = idastar_search(problem, HEURISTICS[heuristic_name])
        frontier = None
    else:
        raise ValueError("unknown algorithm: %s" % algorithm)

    elapsed = time.perf_counter() - started

    return {
        'status': 'ok',
        'cost': None if plan is None else len(plan),
        'nodes_expanded': expanded,
        'max_frontier': frontier,
        'iterations': iterations,
        'seconds': round(elapsed, 4),
    }


def _worker(out, algorithm, grid_name, heuristic_name):
    """Subprocess entry point. Puts (status, payload) on the queue."""
    sys.setrecursionlimit(100000)
    try:
        out.put(('ok', run_single(algorithm, grid_name, heuristic_name)))
    except NotImplementedError as exc:
        out.put(('skip', str(exc)))
    except Exception as exc:  # noqa: BLE001 - report anything the student hits
        out.put(('error', '%s: %s' % (type(exc).__name__, exc)))


def run_with_timeout(algorithm, grid_name, heuristic_name, timeout):
    """Run one configuration in a subprocess, killing it after `timeout` seconds."""
    out = mp.Queue()
    proc = mp.Process(target=_worker,
                      args=(out, algorithm, grid_name, heuristic_name))
    started = time.perf_counter()
    proc.start()
    try:
        status, payload = out.get(timeout=timeout)
    except queue_mod.Empty:
        status, payload = 'timeout', None
    finally:
        if proc.is_alive():
            proc.terminate()
        proc.join()

    elapsed = round(time.perf_counter() - started, 4)

    if status == 'ok':
        return payload
    if status == 'timeout':
        return {'status': 'TIMEOUT', 'cost': None, 'nodes_expanded': None,
                'max_frontier': None, 'iterations': None, 'seconds': elapsed}
    if status == 'skip':
        return {'status': 'SKIP', 'cost': None, 'nodes_expanded': None,
                'max_frontier': None, 'iterations': None, 'seconds': None}
    return {'status': 'ERROR (%s)' % payload, 'cost': None,
            'nodes_expanded': None, 'max_frontier': None,
            'iterations': None, 'seconds': elapsed}


# ---------------------------------------------------------------------------
# The full sweep
# ---------------------------------------------------------------------------

def configurations(grid_names):
    """Yield (algorithm, grid, heuristic) triples to measure."""
    for grid_name in grid_names:
        yield ('dfs', grid_name, NO_HEURISTIC)
        for algorithm in ('astar', 'idastar'):
            for heuristic_name in HEURISTIC_NAMES:
                yield (algorithm, grid_name, heuristic_name)


def sweep(grid_names, timeout, out_path='results.csv'):
    """Run every configuration and write results.csv. Returns the rows."""
    rows = []
    print("%-13s %-8s %-4s %-10s %s" % (
        'grid', 'algo', 'h', 'status', 'nodes / cost / time'))
    print('-' * 68)

    for algorithm, grid_name, heuristic_name in configurations(grid_names):
        problem_art = EXAMPLE if grid_name == 'example' else GRIDS[grid_name]
        grid, _, dirty = parse_grid(problem_art)

        result = run_with_timeout(algorithm, grid_name, heuristic_name, timeout)
        row = {
            'grid': grid_name,
            'rows': len(grid),
            'cols': len(grid[0]),
            'n_dirty': len(dirty),
            'algorithm': algorithm,
            'heuristic': heuristic_name,
        }
        row.update(result)
        rows.append(row)

        if result['status'] == 'ok':
            detail = "%s nodes, cost %s, %.2fs" % (
                result['nodes_expanded'], result['cost'], result['seconds'])
        else:
            detail = ''
        print("%-13s %-8s %-4s %-10s %s" % (
            grid_name, algorithm, heuristic_name, result['status'], detail))

    with open(out_path, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in CSV_FIELDS})

    print('-' * 68)
    print("wrote %d rows to %s" % (len(rows), out_path))
    return rows


# ---------------------------------------------------------------------------
# YOUR WORK STARTS HERE
# ---------------------------------------------------------------------------

def make_table(rows):
    """Write the results as Markdown tables to results_table.md and print them.

    The first table pivots nodes expanded into a grid x configuration matrix
    so the algorithms can be compared at a glance. The second lists every
    required measurement (cost, nodes expanded, max frontier or iterations,
    runtime), one section per grid. Frontier (DFS, A*) and iterations (IDA*)
    share a column because each algorithm reports only one of them.
    """
    # Imported here, not at the top: the sweep starts a fresh process per
    # run, and each one re-imports this file.
    import pandas as pd

    frame = pd.DataFrame(rows)
    names = {'dfs': 'DFS', 'astar': 'A*', 'idastar': 'IDA*'}
    frame['config'] = [names[algorithm] if heuristic == NO_HEURISTIC
                       else '%s/%s' % (names[algorithm], heuristic)
                       for algorithm, heuristic in zip(frame['algorithm'], frame['heuristic'])]
    for column in ('cost', 'nodes_expanded', 'max_frontier', 'iterations'):
        frame[column] = pd.to_numeric(frame[column]).map('{:,.0f}'.format).replace('nan', '-')
    frame['seconds'] = pd.to_numeric(frame['seconds']).map('{:.3f}'.format).replace('nan', '-')
    frame['memory'] = frame['max_frontier'].where(frame['algorithm'] != 'idastar',
                                                  frame['iterations'] + ' iter')
    frame['summary'] = frame['nodes_expanded'].where(frame['status'] == 'ok', frame['status'])

    configs = list(dict.fromkeys(frame['config']))
    lines = ['# Results', '', '## Nodes expanded (grid x configuration)', '',
             '| grid | dirt | %s |' % ' | '.join(configs),
             '|---|---:|' + '---:|' * len(configs)]
    for grid_name, subset in frame.groupby('grid', sort=False):
        cells = subset.set_index('config').loc[configs, 'summary']
        lines.append('| %s | %d | %s |' % (grid_name, subset['n_dirty'].iloc[0],
                                           ' | '.join(cells)))

    lines += ['', '## Full measurements', '']
    columns = ['config', 'status', 'cost', 'nodes_expanded', 'memory', 'seconds']
    for grid_name, subset in frame.groupby('grid', sort=False):
        first = subset.iloc[0]
        lines += ['### %s (%dx%d, %d dirty)' % (grid_name, first['rows'], first['cols'],
                                                first['n_dirty']),
                  '',
                  '| config | status | cost | nodes expanded | '
                  'max frontier / iterations | seconds |',
                  '|---|---|---:|---:|---:|---:|']
        lines += ['| %s |' % ' | '.join(entry) for entry in subset[columns].values.tolist()]
        lines.append('')

    text = '\n'.join(lines)
    with open('results_table.md', 'w', encoding='utf-8') as handle:
        handle.write(text)
    print(text)
    print("wrote results_table.md")


# I used matplot lib for the plots 
# (https://matplotlib.org/stable/gallery/scales/log_demo.html)
# (Meant specifically to satisfy: "Any code or text adapted from another source must be cited in a comment or footnote")
# It's 
def plot_scaling(rows):
    """Plot #1 - how does each algorithm scale with the amount of dirt?

    Suggested shape: x = number of dirty cells, y = nodes expanded, one line
    per algorithm (hold the heuristic fixed at h2). A log scale on y will
    probably help; say in the caption why you chose it.

    Save to figures/scaling.png.
    """
    # The log scale on y is used because node counts grow exponentially with the number of dirty cells
    import matplotlib.pyplot as plt
    import pandas as pd

    frame = pd.DataFrame(rows)
    frame['nodes_expanded'] = pd.to_numeric(frame['nodes_expanded'])
    top = frame['nodes_expanded'].max() * 3

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, algorithm, heuristic in [
        ('DFS', 'dfs', NO_HEURISTIC), 
        ('A* (h2)', 'astar', 'h2'),
        ('IDA* (h2)', 'idastar', 'h2')]:
        subset = frame[(frame['algorithm'] == algorithm) & (frame['heuristic'] == heuristic)].sort_values('n_dirty')
        solved = subset[subset['status'] == 'ok']
        line, = ax.plot(solved['n_dirty'], solved['nodes_expanded'],
                        marker='o', label=label)
        timed_out = subset[subset['status'] != 'ok']
        if len(timed_out):
            ax.scatter(timed_out['n_dirty'], [top] * len(timed_out), marker='x',
                       s=80, color=line.get_color())
    ax.set_yscale('log')
    ax.set_xticks(sorted(frame['n_dirty'].unique()))
    ax.set_xlabel('num dirty cells')
    ax.set_ylabel('nodes expanded (log)')
    ax.set_title('Nodes expanded vs amount of dirt')
    ax.grid(True, which='both', alpha=0.3)
    ax.legend()
    fig.tight_layout()
    os.makedirs('figures', exist_ok=True)
    fig.savefig('figures/scaling.png', dpi=150)
    plt.close(fig)
    print("saved to figures/scaling.png")


# Grouped bars follow the matplotlib gallery's "Grouped bar chart with labels"
# example (https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html):
# each series is drawn with ax.bar() at the group positions shifted by
# width * multiplier, and ax.set_xticks() puts the group names under the middle.
def plot_heuristics(rows):
    """Plot #2 - what does a better heuristic buy you?

    Suggested shape: A* nodes expanded under h0 vs h1 vs h2 (and h3 if you
    did the bonus), grouped by grid. This is the evidence for your answer to
    discussion question 2.

    Save to figures/heuristics.png.
    """
    import matplotlib.pyplot as plt
    import pandas as pd

    frame = pd.DataFrame(rows)
    frame['nodes_expanded'] = pd.to_numeric(frame['nodes_expanded'])
    astar = frame[(frame['algorithm'] == 'astar') & (frame['status'] == 'ok')]
    grids = list(frame.sort_values('n_dirty', kind='stable')['grid'].drop_duplicates())
    heuristics = [name for name in HEURISTIC_NAMES if (astar['heuristic'] == name).any()]
    positions = list(range(len(grids)))
    width = 0.8 / len(heuristics)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for multiplier, heuristic in enumerate(heuristics):
        counts = astar[astar['heuristic'] == heuristic].set_index('grid')['nodes_expanded']
        ax.bar([x + width * multiplier for x in positions],
               [counts.get(grid, 0) for grid in grids],
               width, label=heuristic)
    ax.set_xticks([x + width * (len(heuristics) - 1) / 2 for x in positions], grids)
    ax.set_yscale('log')
    ax.set_ylabel('A* nodes (log)')
    ax.set_title('Effect of heuristic on A*')
    ax.grid(True, axis='y', which='both', alpha=0.3)
    ax.legend(title='heuristic')
    fig.tight_layout()
    os.makedirs('figures', exist_ok=True)
    fig.savefig('figures/heuristics.png', dpi=150)
    plt.close(fig)
    print("saved to figures/heuristics.png")


# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[2])
    parser.add_argument('--timeout', type=float, default=60.0,
                        help="seconds per configuration (default: 60)")
    parser.add_argument('--quick', action='store_true',
                        help="only the three smallest grids")
    parser.add_argument('--grids', nargs='+', metavar='NAME',
                        help="specific grids to run (default: all six)")
    parser.add_argument('--out', default='results.csv',
                        help="where to write the raw results")
    parser.add_argument('--analyze', action='store_true',
                        help="also run your table and plot functions")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.grids:
        grid_names = args.grids
    elif args.quick:
        grid_names = QUICK_GRIDS
    else:
        grid_names = list(GRIDS)

    unknown = [g for g in grid_names if g != 'example' and g not in GRIDS]
    if unknown:
        print("unknown grid(s): %s" % ', '.join(unknown))
        print("available: example, %s" % ', '.join(GRIDS))
        return 2

    rows = sweep(grid_names, args.timeout, args.out)

    if args.analyze:
        make_table(rows)
        plot_scaling(rows)
        plot_heuristics(rows)

    return 0


if __name__ == "__main__":
    # The multiprocessing guard above is required on Windows and macOS.
    sys.exit(main())
