# CS3810 Mini-Project 1 — Getting Started

Unzip this folder, `cd` into it, and run:

```bash
python run_tests.py
```

Everything will say `SKIP`. That is correct — nothing is implemented yet.
Your job is to turn those into `PASS`.

## What's in here

| File | Yours to write? | What it is |
|------|-----------------|------------|
| `vacuum_world.py` | **Yes** | Part 1 — the environment. Start here. |
| `search.py` | **Yes** | Part 2 — DFS, A\*, IDA\*. |
| `heuristics.py` | **Yes** | Part 3 — `h0`, `h1`, `h2`, and the optional `h3`. |
| `experiments.py` | **Partly** | Part 4 — the measurement harness is written; the table and the two plots are yours. |
| `test_grids.py` | No | The graded grids. Do not modify. |
| `priority_queue.py` | No | A heap with decrease-key. Use it in A\*. |
| `run_tests.py` | No | Smoke tests. Graders run their own copy. |

Every function you need to write raises `NotImplementedError` with a note
saying which part it belongs to. Delete that line and write the function.

## Suggested order

1. **`VacuumWorld.render()` first.** It is not graded for correctness, but you
   will look at it a hundred times. Being able to *see* a state is the
   difference between a two-hour bug and a ten-minute one.
2. The rest of `VacuumWorld`. Run `python vacuum_world.py` — it prints the
   example grid and its legal actions.
3. `manhattan`, `h0`, `h1`, `h2` in `heuristics.py`. These are a few lines each,
   and the searches need them.
4. `dfs_search`. Run `python run_tests.py` — Part 1, Part 3, and Part 2a should
   go green.
5. `astar_search`. Run `python search.py` for a quick check on the example grid
   (optimal cost there is 14).
6. `idastar_search`. Hardest of the three; much easier once the other two work.
7. `python experiments.py --quick` to confirm the harness runs, then the full
   sweep, then your table and plots.

## Running the experiments

```bash
python experiments.py --quick            # three small grids, fast
python experiments.py                    # the full graded set, 60s per config
python experiments.py --timeout 120      # if your machine is slow
python experiments.py --grids g6_corridor
```

Results land in `results.csv`. The full sweep takes several minutes, and some
IDA\* configurations on `g5_rooms` and `g6_corridor` will hit the timeout —
that is expected and it is a result worth reporting, not a bug to hide.

## Two bugs that will cost you an evening

**Mutating state.** If `result()` changes the state it was handed instead of
returning a new one, every state sitting in your frontier quietly becomes the
same object, and your search will return nonsense with no error message. The
test `result does not mutate the state it is given` catches this.

**Unhashable states.** A state must be `((row, col), frozenset(...))`. A plain
`set` cannot go in a `set` or be a dict key, and you will get `TypeError:
unhashable type` the moment you build your explored set.

## Before you submit

```bash
python run_tests.py
```

Zero failures. Then check the deliverables list in Section 7 of the handout —
code, `results.csv`, `figures/`, `report.pdf`, `README.md`, `AI_USE.md`.

Remember what the points are actually for: 130 for working code, 70 for the
heuristic arguments, the experiments, and the report. `run_tests.py` only
checks the first 130. It cannot tell you whether your analysis is any good.
