# Last-layer configuration space

This spec defines the set of cube configurations the eval draws from, and the
canonical representation everything else (rendering, prompts, grading) should
agree on. `spec/ll_space.py` is the reference implementation; every number below
can be reproduced by running `python3 spec/ll_space.py`.

## 1. What a configuration is

A **configuration** is a physical 3x3 cube photographed from one fixed viewpoint, where:

- Exactly one layer is unsolved: the **last layer (LL)**, which faces up.
- Everything else (the first two layers and the bottom face) is solved.
- The camera looks down at the up-front-right corner, so three faces are visible:
  the **top** (the LL face) and two **sides**. The left visible side is **F**; the
  right visible side is **R**.
- Any of the 6 colours can be on top, in any of the 4 rotations about the vertical
  axis (**colour neutral**).
- The LL can be in any reachable state, at any AUF, **except** solved or solved up
  to an AUF.

## 2. Frame and notation

Everything is expressed in the **camera frame**: U = top, F = left visible side,
R = right visible side, and D, B, L opposite them. Moves use standard WCA
notation in this frame (`U` is clockwise as seen from above, and so on).

Faces in the canonical representation are labelled by **letters** (`U R F D L B`),
not colours. A sticker's letter says which centre it belongs to. Colours enter
only through the orientation (§4).

## 3. Last-layer state

### Slots and pieces

The LL has 4 corner slots and 4 edge slots, in Kociemba order:

| index | corner slot | facelets (top sticker first, then clockwise) | edge slot | facelets |
|---|---|---|---|---|
| 0 | URF | U9, R1, F3 | UR | U6, R2 |
| 1 | UFL | U7, F1, L3 | UF | U8, F2 |
| 2 | ULB | U1, L1, B3 | UL | U4, L2 |
| 3 | UBR | U3, B1, R3 | UB | U2, B2 |

Facelets are numbered 1–9 in reading order on each face, as seen in the usual
unfolded net: U is viewed from above with B at the top edge, D is viewed from below
with F at the top edge, and the four sides are viewed head-on with U at the top.

### State tuple

An LL state is `(cp, co, ep, eo)`, four length-4 tuples:

- `cp[i]`: which corner piece sits in corner slot `i`, using the slot indices above
  (piece *j* is the piece that belongs in slot *j*).
- `co[i]` ∈ {0,1,2}: the corner's U-coloured sticker sits on facelet `co[i]` of the
  slot's facelet list. 0 means it is on top, and 1 or 2 means it is one or two steps
  clockwise from the top. Formally, sticker *k* of the piece lands on facelet `(k + co[i]) mod 3`.
- `ep[i]`: which edge piece sits in edge slot `i`.
- `eo[i]` ∈ {0,1}: 0 if the edge's U-coloured sticker is on top, 1 if it is flipped.

### Reachability constraints

- `parity(cp) == parity(ep)`
- `sum(co) ≡ 0 (mod 3)`
- `sum(eo) ≡ 0 (mod 2)`

These give 4!·4!/2 · 3³ · 2³ = **62,208** reachable LL states. AUF is already part
of the state: a U-layer turn is just a permutation, so it needs no separate parameter.

### Exclusions

There are 4 trivial states: solved, `U`, `U2` and `U'` (no twist or flip, and `cp = ep`
is a pure rotation). Removing them leaves **62,204** non-trivial LL states.

## 4. Colour orientation

The reference colour scheme is the Western (BOY) one: white up, green front, red
right, yellow down, blue back, orange left. An orientation fixes which colour is on
each face. It is fully determined by the (top, front) pair, because the right
colour follows from chirality (right = up × front). That gives 6 × 4 = **24** orientations.
Mirror images are excluded because they are not physical cubes.

| idx | top | front | right | | idx | top | front | right | | idx | top | front | right |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | W | G | R | | 8 | G | W | O | | 16 | R | W | G |
| 1 | W | B | O | | 9 | G | Y | R | | 17 | R | Y | B |
| 2 | W | R | B | | 10 | G | R | W | | 18 | R | G | Y |
| 3 | W | O | G | | 11 | G | O | Y | | 19 | R | B | W |
| 4 | Y | G | O | | 12 | B | W | R | | 20 | O | W | B |
| 5 | Y | B | R | | 13 | B | Y | O | | 21 | O | Y | G |
| 6 | Y | R | G | | 14 | B | R | Y | | 22 | O | G | W |
| 7 | Y | O | B | | 15 | B | O | W | | 23 | O | B | Y |

D, B and L take the opposite colours of U, F and R.

## 5. Size of the space

| | count |
|---|---|
| reachable LL states, including AUF | 62,208 |
| minus solved and AUF-only states | −4 |
| non-trivial LL states | **62,204** |
| × colour orientations | ×24 |
| **total configurations** | **1,492,896** |
| PLL subset (`co`, `eo` all zero, non-trivial) | 284 × 24 = 6,816 |

## 6. Representations

### Canonical letter string

`facelets(state)` returns a 54-character string in Kociemba order: U1–U9, R1–R9,
F1–F9, D1–D9, L1–L9, B1–B9. Each character is a face letter. This is the
**colour-free canonical form**. It depends only on the LL state, not the orientation.

### Coloured string

`coloured_facelets(config_id)` applies the orientation's letter→colour map to the
canonical string. This is what a renderer draws and what a perception subtask
would ask a model to read back.

### Configuration ID

```
config_id = orientation_index * 62204 + state_rank      # 0 .. 1,492,895
```

`state_rank` is the position of the state in the lexicographic order of
`(cp, co, ep, eo)` among the non-trivial states, which is the order `ll_states()`
yields them in. `from_config_id` inverts this.

Examples:

- `config_id 0`: orientation 0 (W/G/R), with the UL and UB edges flipped.
- `config_id 1,492,895`: orientation 23 (O/B/Y).

## 7. Visibility: two-sided recognition is always sufficient

The view shows 14 of the 20 non-centre LL stickers:

- **Visible:** U1–U4 and U6–U9 (8), F1–F3 (3), R1–R3 (3)
- **Hidden:** L1–L3, B1–B3 (6)
- The lower two rows of F and R are visible but always solved, so they carry no information.

**Every one of the 62,204 states produces a distinct view** (verified by exhaustive
enumeration). The visible stickers determine the hidden ones as follows:

1. **Front corners (URF, UFL, UBR):** each shows at least two stickers, so the
   piece and its twist can be read directly.
2. **Back corner (ULB):** the piece is whichever corner is left over. Its twist
   follows from its one visible sticker (U1), or equivalently from the twist-sum constraint.
3. **Front edges (UF, UR):** both stickers are visible.
4. **Back edges (UL, UB):** each shows one sticker. A side colour on top identifies
   the piece and shows it is flipped. If both show the top colour, the two
   remaining pieces could go either way round, and **permutation parity** decides.

Case 4's double-top-colour situation is the hard part of recognition. It applies to
**15,548 states (25%)**, and to **all 284 PLL states**. In PLL, both back edges
always show the top colour.

A single U/F/R view is therefore always sufficient input; no instance in this
space is ambiguous.

## 8. Properties the rest of the eval can rely on

- **Answers don't depend on colour.** Moves are defined in the camera frame, so a
  sequence solves `(orientation, state)` exactly when it solves `(orientation', state)`.
  Grading only needs the 62,204 canonical states. Colour orientation affects only
  perception.
- **Solved means fully solved.** After the moves, every face is a single colour. The
  default assumes no whole-cube rotations, so the cube stays in the camera frame.
  Whether rotations are allowed is a solution-format decision (§9).
- **No symmetry reduction.** States related by a `y` conjugation or by a mirror are
  kept as distinct configurations, because they need different answers (different
  AUFs, mirrored algs). Grouping by case (OLL, PLL or ZBLL name) is metadata on top
  of this space, not a change to it.

## 9. Out of scope for this spec

- Rendering: camera angle, lighting, synthetic vs. photo.
- Solution grammar: wide moves, slice moves, rotations, and whether a trailing AUF is required.
- Sampling strategy and subsets beyond PLL.
- A move simulator for grading. The facelet conventions here are what it must match.
  Its first test should apply known LL algorithms to a solved cube and check that
  the results land in this space with the expected facelet strings; the facelet
  layout in §3 has not yet been checked against a move simulator.
