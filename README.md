*This project has been created as part of the 42 curriculum by enaimami, sukonukc.*

# A-Maze-ing

## Description

A-Maze-ing is a maze generator written in Python with **nothing but the
standard library**. It reads a plain text configuration file, generates a
random but reproducible maze, hides a visible **"42"** inside it, solves it
with a breadth-first search, writes the result to a file using a hexadecimal
wall encoding, and displays the whole board in the terminal with an
interactive menu.

The program can build two very different boards from the same grid:

| Mode | What you get |
|---|---|
| `PERFECT=True` | A **perfect maze**: exactly one path between the entry and the exit, no loop at all, dead-ends everywhere. |
| `PERFECT=False` | A **playable board**, directly usable by a Pac-Man-like game: fully connected, open corners and centre, at least two independent routes, and **no dead-end at all**. |

Corridors are never wider than two cells: no `3x3` area is ever fully open.

The generation logic lives in a self-contained package, `mazegen`, that knows
nothing about the configuration file, the terminal or this project, and is
shipped as an installable wheel so that later projects can reuse it.

## Instructions

### Requirements

Python 3.10 or later. The program itself needs **no third-party package**.
`flake8`, `mypy` and `build` are development tools only and are never
imported at run time.

### Install the development tools

```sh
make install
```

### Run

```sh
make run
```

or, directly:

```sh
python3 a_maze_ing.py config.txt
```

The configuration file is the only argument. Any other number of arguments
prints a usage message on the standard error and exits with the code `1`, as
does every error the program can meet.

### Interactive menu

Once the maze is drawn, the following menu is served:

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Toggle the animations
5. Quit
Choice? (1-5):
```

1. builds a brand new maze from a seed derived from the current one, rewrites
   the output file and replays its generation on screen;
2. shows or hides the shortest path, tracing it step by step when it appears;
3. moves the walls to the next colour of the palette;
4. turns the animations on or off;
5. leaves.

An answer outside of `1-5` only prints a short warning. `Ctrl-C` and
`Ctrl-D` leave the program cleanly, animation included.

### Check the code

```sh
make lint
make lint-strict
```

Both targets run `flake8 .` and `mypy .`, the second one with `--strict`.

### Run the tests

The tests are not part of the submission and are not graded, but they are
kept in the repository:

```sh
python3 -m unittest discover -s tests -t .
```

### Build the reusable package

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install build
python3 -m build --wheel
```

The wheel lands in `dist/`. A prebuilt copy,
`mazegen-1.0.0-py3-none-any.whl`, sits at the root of the repository, and can
be installed with `pip install mazegen-1.0.0-py3-none-any.whl`.

### Clean

```sh
make clean
```

## Configuration file

One `KEY=VALUE` pair per line. Empty lines and lines starting with `#` are
ignored. The key is compared exactly, in upper case; the key and the value are
both stripped of their surrounding spaces; the line is split on its **first**
equal sign.

| Key | Required | Value |
|---|---|---|
| `WIDTH` | yes | Number of cells on the horizontal axis, at least `2`. |
| `HEIGHT` | yes | Number of cells on the vertical axis, at least `2`. |
| `ENTRY` | yes | Entry cell, written `x,y`, inside the board. |
| `EXIT` | yes | Exit cell, written `x,y`, inside the board and different from `ENTRY`. |
| `OUTPUT_FILE` | yes | Path of the file to write, not empty. |
| `PERFECT` | yes | `True` or `False`, in any case. |
| `SEED` | no | Integer making the run reproducible. When it is absent, a seed is drawn and printed on the console. |

Parsing is strict on purpose: a line without an equal sign, an unknown key, a
key written twice, a value that is not a number, a cell outside of the board,
an entry equal to the exit — each of them stops the program with its own
message on the standard error and the exit code `1`. `SEED` is the only key
added to the mandatory ones; it exists because the subject requires
reproducibility.

The default configuration shipped with the repository:

```
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
```

### Output file

The output file holds `HEIGHT` lines of `WIDTH` lowercase hexadecimal digits,
one digit per cell, then an empty line, then the entry, the exit and the
shortest path:

```
91395555139555515393
...
c5546c446c5555546c56

0,0
19,14
EESENEEEEEESSENNEEEEEEESSENESSSSSSWWWSEEESSSSSS
```

Each digit packs the four walls of its cell. A bit set to `1` means the wall
is **closed**:

| Bit | Value | Direction |
|---|---|---|
| 0 | 1 | North |
| 1 | 2 | East |
| 2 | 4 | South |
| 3 | 8 | West |

So `3` is `0011`: north and east closed, south and west open. `a` is `1010`:
east and west closed. A cell of the "42" pattern is `f`, all four walls
closed. Every line ends with `\n`.

## The generation algorithm

The maze is carved with an **iterative recursive backtracker**, also known as
a randomised depth-first search, run on an explicit stack:

1. A `random.Random` instance is created from the seed. Every random decision
   of the run comes from that single instance, and the global functions of the
   `random` module are never used, so a seed fully determines a maze.
2. The cells drawing the "42" are computed and sealed. They are pushed out of
   the corridor graph, so the carving simply never visits them.
3. Starting from the entry, the walk pushes cells on a stack, opening a wall
   towards a randomly chosen unvisited neighbour, and pops back when a cell has
   no unvisited neighbour left. When the stack empties, every corridor cell has
   been visited exactly once: the result is a **spanning tree**, which is
   already the perfect maze asked by `PERFECT=True`.
4. When `PERFECT=False`, the tree is then **braided**: every dead-end gets one
   of its remaining walls opened, preferably towards another dead-end so that
   two of them disappear at once. Candidates that would open a full `3x3` area
   are discarded. If the board still offers fewer than two independent routes,
   extra walls are opened at random until it does.
5. The board is validated against every rule of the subject. A failure restarts
   the whole attempt from a derived seed, up to 32 times, after which a clear
   error is raised.
6. The shortest path is finally solved with a breadth-first search.

No step of the generation, of the solving or of the validation uses recursion:
everything runs on an explicit `list` used as a stack or on a
`collections.deque`, so a large board can never raise a `RecursionError`.

### Why this algorithm

* **It is a natural fit for both modes.** A depth-first walk produces a
  spanning tree, and a spanning tree *is* a perfect maze: `PERFECT=True` needs
  no extra work. The playable board is then one braiding pass away, so a single
  algorithm covers the two very different boards the subject asks for, instead
  of one algorithm per mode.
* **It handles the "42" for free.** Because the pattern cells are removed from
  the graph before carving, the walk simply flows around them. Nothing has to
  be repaired afterwards.
* **It is linear and predictable.** Every cell is pushed and popped once, so
  the cost grows with the number of cells, and the memory is the stack, never
  the call stack.
* **Its bias is the right one.** A depth-first walk produces long, winding
  corridors, which reads much better in a terminal than the short, bushy
  corridors of Prim's or Kruskal's algorithms. On the perfect board this gives
  a genuinely long solution; on the playable board the long corridors survive
  the braiding and keep the chase interesting.
* **It is honest about its cost.** The known drawback is the depth of the
  stack, which can reach the number of cells. Running it iteratively removes
  that risk entirely.

### The "42" pattern

The pattern is a bitmap kept as a single data constant in
`mazegen/pattern.py`. Its cells are sealed with their four walls, so they show
up as `f` in the output file and as a solid block on screen:

```
X...XXX
X.....X
X.....X
XXX.XXX
..X.X..
..X.X..
..X.XXX
```

The bitmap is first tried at the centre of the board, then at every other
position, ordered by growing distance from that centre. A position is kept
only when it covers neither the entry, the exit, the four corners nor the
centre cell, and when sealing it leaves the corridor graph connected **and**
leaves every remaining corridor cell with at least two corridor neighbours.
That last rule is what makes a board with no dead-end at all possible: a
corridor cell walled in on three sides could never be braided.

A board needs to be about `9x9` or larger to host the pattern. On a smaller
board no valid position exists, so the pattern is skipped, an error message is
printed on the standard error, and the generation carries on normally, as the
subject allows.

## Bonuses

### A board with no dead-end at all

The subject tolerates a couple of dead-ends on a playable board and rewards a
perfectly braided one. This generator aims at **zero**, and reaches it: the
provided analysis script confirms it with `--max-dead-ends 0`.

Two things make it possible. The braiding pass keeps opening walls until no
corridor cell has a single exit left, preferring to join two dead-ends at
once. And, more importantly, the "42" pattern is only allowed to land where it
leaves **every** corridor cell at least two corridor neighbours, so the pattern
itself can never trap a cell against a wall. A naive `42` bitmap, five rows
tall, hides one-cell pockets inside the counters of the digits, and those
pockets are permanent dead-ends no amount of braiding can open; the taller
bitmap used here has counters two cells deep, which removes them.

### Animated generation and solving

When the output is a terminal, the program does not print the finished maze
straight away:

* **Generation** is replayed wall by wall. What is shown is the real
  depth-first walk, not a fake reveal: the generator records the walls it
  opened in `build_steps()`, and the renderer opens them again on a fresh grid,
  frame by frame. The braiding that turns the tree into a playable board is
  part of the replay, so the loops can be watched appearing after the carving.
* **The solution** is traced one cell at a time from the entry to the exit when
  it is switched on with the menu entry `2`.

Frames are drawn over each other by moving the cursor back up over the board,
so nothing above the maze scrolls away. The number of frames is capped, which
keeps a large board no slower to watch than a small one, and the animations are
skipped entirely when the output is not a terminal, so piping the program or
running it from a script behaves exactly as before. The menu entry `4` turns
them off.

## Reusable code

Everything under `mazegen/` is reusable. The package depends on nothing but
the standard library, imports no other module of this repository, reads and
writes no file, and prints nothing: it is pure computation. The parts specific
to this project — the configuration format, the output file, the renderer and
the menu — live in `app/`, which imports `mazegen` and never the other way
round.

### Install

```sh
pip install mazegen-1.0.0-py3-none-any.whl
```

### Basic usage

```python
from mazegen import MazeGenerator

generator = MazeGenerator(
    width=20,
    height=15,
    entry=(0, 0),
    exit_=(19, 14),
    perfect=False,
    seed=42,
)
generator.generate()
```

### Custom parameters

`width` and `height` are the size of the board in cells, and must both be at
least `2`. `entry` and `exit_` are `(x, y)` cells, where `x` is the column and
`y` the row counted from the top; they must lie inside the board and differ
from each other. `perfect` selects the generation mode. `seed` makes a
generation reproducible: the same seed and the same parameters always rebuild
the same maze. It may be omitted, in which case a random seed is drawn and
exposed as `generator.seed`.

### Accessing the structure

```python
generator.cells            # list[list[int]], packed wall bits per row
generator.pattern_cells    # frozenset[tuple[int, int]], the "42" cells
generator.to_hex_lines()   # list[str], one hexadecimal row per line
generator.seed             # int, the seed this maze can be rebuilt from
```

`cells` is the internal structure: one integer per cell, where bit 0 is the
north wall, bit 1 the east wall, bit 2 the south wall and bit 3 the west wall,
a bit set to `1` meaning a closed wall. `to_hex_lines()` is the same board in
the format of the output file.

### Accessing a solution

```python
generator.solution()             # [(0, 0), (1, 0), (1, 1), ...]
generator.solution_directions()  # "ESSE..."
```

`solution()` returns the shortest path from the entry to the exit as a list of
cells, and `solution_directions()` returns the same path as a string of the
letters `N`, `E`, `S` and `W`.

### Replaying a generation

```python
generator.build_steps()    # [((0, 0), (1, 0)), ((1, 0), (1, 1)), ...]
```

`build_steps()` returns the walls the generation opened, in order, as pairs of
neighbouring cells: first the depth-first carving, then the braiding. Opening
them one by one on a fresh grid holding only `pattern_cells` rebuilds the very
same maze, which is how this program animates the generation. The package
itself draws nothing; it only hands the steps over.

### Errors

Every failure raises a subclass of `MazeError`: `InvalidParametersError` for
unusable constructor arguments, and `MazeGenerationError` when no board
matching the requested rules could be built.

```python
from mazegen import MazeError, MazeGenerator

try:
    generator = MazeGenerator(2, 2, (0, 0), (1, 1), perfect=False)
    generator.generate()
except MazeError as error:
    print(f"Error: {error}")
```

### Licence

`mazegen` is released under the MIT licence, written in full in
[LICENSE.md](LICENSE.md). It explicitly allows any later project to reuse,
modify, redistribute and repackage the generator.

## Repository layout

```
a_maze_ing.py     command line entry point, error handling and exit code
config.txt        default configuration
mazegen/          the reusable package
    grid.py           wall bits, and the only two functions that change them
    pattern.py        placement of the "42" bitmap
    generator.py      MazeGenerator, orchestration of a generation
    solver.py         breadth-first shortest path
    validator.py      every rule of the subject, checked
    errors.py         the exception hierarchy
app/              the parts specific to this project
    config.py         strict parsing of the configuration file
    writer.py         output file
    renderer.py       ASCII and ANSI rendering
    menu.py           interactive session
tests/            unit tests, neither submitted nor graded
```

A single design rule holds the wall coherence together: **only
`Grid.open_wall` and `Grid.close_wall` ever change a wall**, and both of them
update the two cells sharing it. No other line of the project assigns a cell
value. Coherence is therefore built in, not tested in afterwards.

## Resources

Classic references on maze generation and graph theory:

* Jamis Buck, *Mazes for Programmers*, Pragmatic Bookshelf, 2015 — the
  reference book on generation algorithms, braiding and rendering.
* Jamis Buck, *Maze Generation: Recursive Backtracking*,
  <https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking>
* Walter D. Pullen, *Think Labyrinth: Maze Algorithms*,
  <https://www.astrolog.org/labyrnth/algrithm.htm> — the vocabulary of perfect,
  braided and unicursal mazes.
* Wikipedia, *Maze generation algorithm*,
  <https://en.wikipedia.org/wiki/Maze_generation_algorithm>
* Wikipedia, *Spanning tree* and *Circuit rank*, for the `E - V + 1` count
  used to prove that a playable board really offers several routes.
* Python documentation: `random.Random`, `collections.deque`, `typing`,
  PEP 257 for the docstrings, PEP 484 for the type hints.
* ANSI escape codes, <https://en.wikipedia.org/wiki/ANSI_escape_code>
* Python Packaging User Guide, <https://packaging.python.org>, and the
  Hatchling documentation, for the wheel.
* Choose a License, <https://choosealicense.com/licenses/mit/>, to pick and
  understand the MIT licence.

### How AI was used

Anthropic's Claude, through Claude Code, was used as a pair-programming
assistant on this project. Concretely:

* **Reading the subject.** Cross-checking our reading of the subject, and
  raising the one place where its text and its screenshots disagree: the
  screenshot of the output file shows `# entry (x,y)` comments next to the
  coordinates, while the text only asks for three lines. We chose to write raw
  values, so that a strict parser reading the file never meets an unexpected
  comment.
* **The pattern bitmap.** Working out that a naive `42` bitmap traps corridor
  cells in one-cell pockets, which makes the "no dead-end at all" bonus
  impossible, and designing the taller bitmap whose counters are two cells
  deep so that every corridor cell keeps at least two neighbours.
* **Boilerplate.** Writing the repetitive parts: docstrings, type hints,
  configuration parsing branches and their error messages.
* **The animation.** Finding a way to animate the generation without letting
  the reusable package print anything: recording the opened walls in
  `build_steps()` and replaying them in the renderer, rather than passing a
  drawing callback down into the generator.
* **Review and testing.** Reviewing the modules for dead code and for
  violations of our own rules, and writing the unit test suite, including the
  independent checker that re-reads the output file and verifies the wall
  coherence, the connectivity, the loop count, the dead-end count, the `3x3`
  rule and the optimality of the path without reusing our own validator.

Every design decision — the algorithm, the module boundaries, the strict
configuration format, the rendering — was ours; the assistant was used to
challenge them, to speed up the mechanical parts and to test the result.

## Team and project management

### Roles

| Member | Responsibility |
|---|---|
| sukonukc | Generation core: `grid.py`, `generator.py`, `pattern.py`, `solver.py`, `validator.py`. Packaging of `mazegen` and the licence. |
| enaimami | Program layer: `config.py`, `writer.py`, `renderer.py`, `menu.py`, `a_maze_ing.py`. Makefile, tests and documentation. |

The split follows the boundary the subject already draws between the reusable
module and the project that uses it, which let us work on the two halves at
the same time with a single agreed contract: the public API of
`MazeGenerator`.

### Planning, and how it evolved

Our initial plan had four phases: agree on the data structure, write the
generator, write the program around it, then document and package. It held,
with two corrections.

The first correction came from the `3x3` rule. We had planned braiding as a
last cosmetic pass; it turned out to interact with both the `3x3` rule and the
"42" pattern, so it had to become a first-class step with its own candidate
filtering, and the validator had to be written *before* the braiding rather
than after it, so that we could measure what we were doing.

The second came from the pattern. We had assumed any readable `42` bitmap
would do, and discovered that the obvious five-row one forces two permanent
dead-ends, which quietly costs the bonus. Redesigning the bitmap and adding
the "every corridor cell keeps two neighbours" rule to the placement search
cost us a day we had not planned, and changed the smallest board that can host
the pattern from `5x7` to about `9x9`.

### What worked well

* **Deciding early that a single function may change a wall.** Wall coherence,
  which the subject insists on, then became impossible to break by accident.
* **Writing the validator early and running it over hundreds of boards.** Every
  rule of the subject is checked by code, on every size and both modes, instead
  of being checked by eye on one screenshot.
* **Keeping `mazegen` sealed off.** The package reads no file, prints nothing
  and imports nothing local, so the packaging step at the end was a formality.
* **The retry loop.** Rather than trying to make every random draw succeed, the
  generator validates and restarts from a derived seed. It keeps the algorithms
  simple and the guarantees strong.

### What could be improved

* **The `3x3` check is recomputed more often than it needs to be.** Every
  candidate wall re-inspects the blocks around it. It is fast enough at the
  sizes we care about, but an incremental counter would scale better.
* **The renderer costs one character per cell,** so a wide board eventually
  overflows a terminal. Scrolling, or a compact mode, would help.
* **We validated small boards late.** Discovering that a `2x2` playable board
  is mathematically impossible, since it cannot offer two independent routes,
  should have come from the first day's reasoning, not from a test run.
* **Only one generation algorithm.** Prim's or Kruskal's would have made a nice
  comparison of the corridor shapes they produce, but stayed out of scope.

### Tools

Python 3.10+ and its standard library only. `flake8` and `mypy`, both wired
into `make lint` and `make lint-strict`, and both kept at zero warning
throughout, including under `--strict`. `unittest` for the tests. `build` and
`hatchling` for the wheel, with the version read straight from
`mazegen/__init__.py` so that it can never drift from `pyproject.toml`. Git
for the history. Claude Code as described above.
