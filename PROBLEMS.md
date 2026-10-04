# PLL problem pool and I/O format

The concrete problem set for the simple last-layer eval. It sits on top of the configuration space in
[SPEC.md](SPEC.md) (frame, facelet layout, orientations). Code: `src/hll/pll.py` (pool, cases, prompt),
`src/hll/moves.py` (notation, simulator), `src/hll/grading.py`. Checked by `pytest`.

Sampling is in §5. Run structure (epochs, models) is left to Inspect.

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

### Case labels

Every state is `pre-AUF · case · post-AUF` for one of the **21 PLL cases** (`ALGS` in `pll.py`, one textbook alg
per case, written the way they usually appear, with slices, rotations and D/L turns). Each state is labelled with the
decomposition that uses the fewest AUF turns (ties broken by `(case, pre, post)`); symmetric cases (H, Na, Nb: 4 states,
E, Z: 8, all others 16) have several. Labels are metadata for analysis. They are not shown to the model and do not affect grading.

> The case *names* of the algs were written from memory and could not be cross-checked against a published list in the
> authoring environment. The tests prove each alg is a valid PLL, that the 21 are distinct and that together they cover all 284 states,
> and the symmetry counts match theory, but not that, say, `Gb` is what the community calls Gb. Check `ALGS` against a reference
> before reporting per-case results by name.

## 2. Input

A fixed text prompt (`HEADER` + notation + `_FOOTER` in `pll.py`) with three 3×3 grids filled in.

- **U**: the top face, viewed from above with the back edge at the top, rows top to bottom.
- **F**: the left visible side, viewed head-on.
- **R**: the right visible side, viewed head-on.
- Stickers are lowercase colour letters `w y g b r o`, space-separated. Lowercase is used so a blue sticker `b`
  can't be mistaken for the move `B`.
- Grids are in the facelet order of SPEC.md §3, so the F and R grids include the two solved lower rows.
- The prompt does not state which colours are opposite each other. Knowing how a standard cube is
  coloured (and so what the hidden faces are) is part of the task. It does state the notation and the answer format.

By SPEC.md §7 the visible stickers determine the whole state, so every prompt has exactly one answer state.

The input is produced by `render_input`. Later modalities (images, other layouts) replace this function; nothing downstream depends on the text.

## 3. Output

The response may contain anything (reasoning etc.). The answer is the contents of the **last**
`<solution>...</solution>` tag, as a whitespace-separated move list. No parentheses, no commas.

### Notation (`pll` move set, the default)

54 moves, covering everything in typical PLL algorithms. Each takes `'` or `2`; `2'` is accepted as a spelling of `2`.

| kind | moves | meaning |
|---|---|---|
| face turns | `U R F D L B` | 90° clockwise looking at that face |
| wide turns | `Rw` or `r`, likewise `Lw/l Uw/u Dw/d Fw/f Bw/b` | the face plus the middle layer, same direction as the face |
| slices | `M E S` | middle layers; `M` follows `L`, `E` follows `D`, `S` follows `F` |
| rotations | `x y z` | whole cube, following `R`, `U`, `F` |

Face names are **positions**: after a rotation, `R` is whichever face is now on the right (the standard convention; `y R ≡ B y`).

The `face` move set (the 18 face turns) is kept as a parameter for ablations.

### Grading

Each response gets a binary result from `grade(pid, response, moveset)`:

1. No `<solution>` tag, an empty sequence, or any token that isn't one allowed move: **fail**, with a machine-readable reason
   (`no_solution_tag`, `empty`, `invalid_move`).
2. Otherwise apply the moves to the problem's 54-facelet state. **Solved means every face is a single colour**, in any final
   whole-cube orientation: **pass**; else `not_solved`.

There is no length cap and no optimality requirement, and no partial credit. `grade` returns the move count so that length
can be analysed later (a long non-algorithmic solution and a recalled textbook alg both pass; their lengths differ).

## 4. Verification (`tests/`)

- Turn directions, inverses and orders of the simulator; the identities `x = R M' L'`, `Rw = R M'`, `y R = B y`, etc., which pin down the slice and rotation conventions.
- Every one of the 21 algs stays inside the PLL set under all 16 AUF pairs (catches typos); cases cover all 284 states with the expected symmetry counts.
- Every one of the 6,816 problems is solved by its reference solution (case alg with AUFs, closed with a rotation where the alg ends rotated).
- Grader: rotated endings, alternate spellings, each failure reason, last-tag-wins, move set restrictions.
- Dataset and an Inspect run with a scripted solver, end to end through the scorer and its metrics.

## 5. Sampling

The default task uses the 284 states **once each**, with colour orientations assigned by a seeded shuffle so that every orientation appears 11 or 12 times (`orientations="balanced"`). `orientations="all"` gives all 6,816;
an integer fixes one orientation. Sample ids are `problem_id`, so a sample is the same problem under every variant.
Standard errors are clustered by state, because the colourings of one state are not independent.
