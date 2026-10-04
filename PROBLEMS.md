# PLL problem pool and I/O format

The concrete problem set for the simple last-layer eval. It sits on top of the configuration space in
[SPEC.md](SPEC.md) (frame, facelet layout, orientations). `spec/pll_problems.py` is the reference
implementation: `python3 spec/pll_problems.py` prints a sample prompt and runs the self-checks below.

Sampling, scoring aggregation and run structure are deliberately **not** specified here.

## 1. Problem pool

A problem is one (PLL state, colour orientation) pair:

- **State**: any non-trivial LL state with all corners and edges oriented (`co = eo = 0`). That is any PLL
  case at any pre/post AUF, with the top face fully solved. Solved and AUF-only states are excluded. This gives **284** states.
- **Orientation**: any of the 24 colour-neutral (top, front) colour assignments (SPEC.md §4).

**284 × 24 = 6,816 problems.**

`problem_id = orientation_index * 284 + state_rank`, where `state_rank` is the index in lexicographic
`(cp, co, ep, eo)` order among the 284 states. `config_id(pid)` maps back to the 1.49M-configuration
id of SPEC.md §6. Colour only affects what the model sees (SPEC.md §8), so there are 284 distinct
answers' worth of states, each shown in 24 colourings.

`python3 spec/pll_problems.py export` writes the pool as JSONL (`id`, `config_id`, `orientation`, `colours`, `input`).

## 2. Input

A fixed text prompt (`PROMPT` in the script) with three 3×3 grids filled in. Everything the model needs is in it.

- **U**: the top face, viewed from above with the back edge at the top, rows top to bottom.
- **F**: the left visible side, viewed head-on.
- **R**: the right visible side, viewed head-on.
- Stickers are lowercase colour letters `w y g b r o`, space-separated. Lowercase is used so a blue sticker `b`
  can't be mistaken for the move `B`.
- Grids are in the facelet order of SPEC.md §3 (row-major from the top-left of each view), so the
  F and R grids include the two solved lower rows. These show the F and R centre colours.
- The prompt states the opposite-colour pairs and that D, L, B are opposite U, R, F, so the model can
  infer the hidden faces. It also states the move notation, the 18-move set, that rotations are
  not allowed, and the answer format.

By SPEC.md §7 the visible stickers determine the whole state, so every prompt has exactly one answer state.

## 3. Output

The response may contain anything (reasoning etc.). The answer is the contents of the **last**
`<solution>...</solution>` tag, as a whitespace-separated move list.

### Notation and allowed moves

WCA outer-face turns in the camera frame of SPEC.md §2 (U top, **F = left visible face**, **R = right
visible face**), `X`, `X'`, `X2` for X in `U R F D L B`: **18 moves**. The set is the constant
`MOVESET` and is a parameter of `parse_moves` and `grade`, so it can be narrowed later (e.g. to ⟨U, R⟩).
Not allowed: wide moves (`Rw`, `r`), slice moves (`M E S`), whole-cube rotations (`x y z`), `2'`, `U2'`,
lowercase letters, and anything else.

Face-turn moves never move centres, so "solved" can't be satisfied by a rotation in disguise.

### Grading

Each response gets a binary result from `grade(pid, response, moveset)`:

1. No `<solution>` tag, an empty sequence, or any token that isn't exactly one allowed move: **fail**.
2. Otherwise apply the moves to the problem's 54-facelet state. Solved means the result equals the canonical
   solved string (`UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB`): **pass**, else **fail**.

There is no length cap and no optimality requirement in the grade, and no partial credit. `grade` also returns
the move count so that length can be analysed later.

## 4. Verification

`selftest()` in the script checks, and the numbers above come from it:

- Turn directions and inverses of the facelet-level move simulator.
- All 6,816 problems are solvable and the grader accepts a known solution for each. The solutions are the inverse
  of a word in `U` and four PLL algorithms (T, Ua, Aa, Y) that reaches that state from solved.
- This also confirms that the facelet layout in SPEC.md §3 matches a real move simulator (the open item in
  SPEC.md §9).
- Rejection of untagged, empty, rotation, and malformed answers.
