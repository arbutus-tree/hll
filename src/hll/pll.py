"""The PLL problem pool, its case labels, and the text rendering of a problem. See PROBLEMS.md.

Pure Python with no dependency on inspect_ai, so the spec can be checked on its own.
"""
import random

from . import ll_space as ll
from .moves import DEFAULT_MOVESET, MOVESETS, apply_moves, invert, is_solved, rotation_fix

# ---------------------------------------------------------------------------
# Problem pool
# ---------------------------------------------------------------------------

PLL_STATES = [s for s in ll.NONTRIVIAL if not any(s[1]) and not any(s[3])]  # 284
N_PLL = len(PLL_STATES)
N_ORIENTATIONS = len(ll.ORIENTATIONS)                                        # 24
N_PROBLEMS = N_PLL * N_ORIENTATIONS                                          # 6,816
PLL_RANK = {s: i for i, s in enumerate(PLL_STATES)}


def problem_id(orientation_index, state):
    return orientation_index * N_PLL + PLL_RANK[state]


def from_problem_id(pid):
    o, r = divmod(pid, N_PLL)
    return o, PLL_STATES[r]


def config_id(pid):
    """The id of the same configuration in the full 1.49M-configuration space of SPEC.md."""
    o, s = from_problem_id(pid)
    return ll.config_id(o, s)


def balanced_orientations(seed=0):
    """One orientation per PLL state: every orientation used 11 or 12 times, assignment shuffled by seed.

    Returns a list indexed by state rank.
    """
    orients = [i % N_ORIENTATIONS for i in range(N_PLL)]
    random.Random(seed).shuffle(orients)
    return orients


# ---------------------------------------------------------------------------
# Cases: the 21 PLLs, each with a textbook algorithm (as typically written, rotations and all)
# ---------------------------------------------------------------------------

# Each alg SOLVES its case. Written the way they usually appear, so they exercise the full notation:
# slices (H, Z), rotations (Aa, Ab, E, V), D-turns (Aa, Ab, E, Ga-Gd, Ra) and L-turns (Ja).
ALGS = {
    "Aa": "x R' U R' D2 R U' R' D2 R2",
    "Ab": "x R2 D2 R U R' D2 R U' R",
    "E": "x' R U' R' D R U R' D' R U R' D R U' R' D'",
    "F": "R' U' F' R U R' U' R' F R2 U' R' U' R U R' U R",
    "Ga": "R2 U R' U R' U' R U' R2 U' D R' U R D'",
    "Gb": "R' U' R U D' R2 U R' U R U' R U' R2 D",
    "Gc": "R2 U' R U' R U R' U R2 U D' R U' R' D",
    "Gd": "R U R' U' D R2 U' R U' R' U R' U R2 D'",
    "H": "M2 U M2 U2 M2 U M2",
    "Ja": "R' U L' U2 R U' R' U2 R L",
    "Jb": "R U R' F' R U R' U' R' F R2 U' R'",
    "Na": "R U R' U R U R' F' R U R' U' R' F R2 U' R' U2 R U' R'",
    "Nb": "R' U R U' R' F' U' F R U R' F R' F' R U' R",
    "Ra": "R U' R' U' R U R D R' U' R D' R' U2 R'",
    "Rb": "R' U2 R U2 R' F R U R' U' R' F' R2",
    "T": "R U R' U' R' F R2 U' R' U' R U R' F'",
    "Ua": "R U' R U R U R U' R' U' R2",
    "Ub": "R2 U R U R' U' R' U' R' U R'",
    "V": "R' U R' U' y R' F' R2 U' R' U R' F R F",
    "Y": "F R U' R' U' R U R' F' R U R' U' R' F R F'",
    "Z": "M' U M2 U M2 U M' U2 M2",
}
assert len(ALGS) == 21

_AUF = ([], ["U"], ["U2"], ["U'"])


def _closed(alg):
    """alg followed by whatever whole-cube rotation puts the centres back (empty for most algs)."""
    alg = alg.split()
    return alg + rotation_fix(apply_moves(ll.SOLVED, alg))


def _build_cases():
    """Map each PLL state to (case, pre-AUF, post-AUF) such that `pre + alg + post` solves it.

    The problem state is the one that `pre + alg + post` (closed up with a rotation if the alg
    ends rotated) takes to solved, i.e. the state reached by running its inverse from solved.
    Symmetric cases (H, Z, N, ...) have several decompositions; the one with fewest AUF turns wins.
    """
    by_faces = {ll.facelets(s): s for s in PLL_STATES}
    found = {}
    for name, alg in ALGS.items():
        closed = _closed(alg)
        for a, pre in enumerate(_AUF):
            for b, post in enumerate(_AUF):
                solution = pre + closed + post
                faces = apply_moves(ll.SOLVED, invert(solution))
                state = by_faces.get(faces)
                if state is None:
                    continue    # AUF-only/solved (impossible for a real alg) or not a PLL (bad alg)
                cand = ((pre != []) + (post != []), name, a, b)
                if state not in found or cand < found[state][0]:
                    found[state] = (cand, name, pre, post)
    return {s: v[1:] for s, v in found.items()}


CASES = _build_cases()      # state -> (case name, pre-AUF, post-AUF)


def case_name(state):
    return CASES[state][0]


def reference_solution(state):
    """A textbook solution: pre-AUF, the case's alg, post-AUF (with a closing rotation if the alg needs one)."""
    name, pre, post = CASES[state]
    return pre + _closed(ALGS[name]) + post


# ---------------------------------------------------------------------------
# Input: text rendering of the two-sided recognition image
# ---------------------------------------------------------------------------

HEADER = """\
A 3x3 Rubik's cube is solved except for its top layer. You are looking down at the corner \
where the top face (U), the front face (F, the left side of your view) and the right face \
(R, the right side of your view) meet.

Sticker colours: w=white, y=yellow, g=green, b=blue, r=red, o=orange. \
This is a standard cube.

U face, viewed from above, back edge at the top:
{U}

F face, viewed head-on, top edge at the top:
{F}

R face, viewed head-on, top edge at the top:
{R}

The remaining faces (D, L, B) are hidden.

Give a sequence of moves that solves the cube, so that every face is a single colour again.
"""

_FACE_NOTATION = """\
Moves: U, D, L, R, F, B turn that face 90 degrees clockwise as seen looking directly at \
that face. A trailing ' means counterclockwise and a trailing 2 means a half turn, \
e.g. R, R', R2. Use only these 18 moves. Faces are named as in the picture above: \
U is the top, F the face on the left, R the face on the right, D the bottom, \
L the hidden left face, B the hidden back face. Do not use whole-cube rotations.
"""

_FULL_NOTATION = """\
You may use standard speedcubing notation. Moves are named by position, as in the picture above: \
U is the top, F the face on the left, R the face on the right, D the bottom, \
L the hidden left face, B the hidden back face, and these names stay attached to those positions \
even after you rotate the whole cube.

Face turns: U, D, L, R, F, B turn that face 90 degrees clockwise as seen looking directly at that face.
Wide turns: Rw (or r) turns the R face together with the middle layer, in the same direction as R. \
Likewise Lw/l, Uw/u, Dw/d, Fw/f, Bw/b.
Slice turns: M is the middle layer between L and R, turning in the same direction as L; \
E is the middle layer between U and D, same direction as D; S is the middle layer between F and B, same direction as F.
Rotations: x turns the whole cube like R, y like U, z like F.
Any of these may be followed by ' (counterclockwise) or 2 (half turn), e.g. R', R2, M2, x'.

The cube counts as solved when every face is a single colour, whatever its final orientation.
"""

_FOOTER = """\
Write the moves separated by spaces inside <solution></solution> tags, with no parentheses.
"""

NOTATION = {"face": _FACE_NOTATION, "pll": _FULL_NOTATION}
assert set(NOTATION) == set(MOVESETS)


def _grid(coloured, face):
    base = ll.FACES.index(face) * 9
    return "\n".join(" ".join(coloured[base + 3 * r + c].lower() for c in range(3)) for r in range(3))


def render_input(pid, moveset=DEFAULT_MOVESET):
    """The full prompt text for a problem. Deterministic function of (problem id, moveset)."""
    coloured = ll.coloured_facelets(config_id(pid))
    head = HEADER.format(U=_grid(coloured, "U"), F=_grid(coloured, "F"), R=_grid(coloured, "R"))
    return head + "\n" + NOTATION[moveset] + "\n" + _FOOTER


def problem_facelets(pid):
    """Canonical letter string (colour-free) of the problem's starting state."""
    return ll.facelets(from_problem_id(pid)[1])


def check_solved(pid, moves):
    """Does this move list (canonical names) solve the problem?"""
    return is_solved(apply_moves(problem_facelets(pid), moves))
