"""Reference implementation of the PLL problem pool and its input/output format.

See PROBLEMS.md. Builds on spec/ll_space.py (SPEC.md).

    python3 spec/pll_problems.py            # print pool size, a sample prompt, run self-checks
    python3 spec/pll_problems.py export     # dump the whole pool as JSONL on stdout
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ll_space as ll  # noqa: E402

# ---------------------------------------------------------------------------
# Problem pool
# ---------------------------------------------------------------------------

PLL_STATES = [s for s in ll.NONTRIVIAL if not any(s[1]) and not any(s[3])]  # 284
N_PLL = len(PLL_STATES)
N_PROBLEMS = N_PLL * 24                                                      # 6,816
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


# ---------------------------------------------------------------------------
# Input: text rendering of the two-sided recognition image
# ---------------------------------------------------------------------------

COLOUR_NAMES = {"W": "white", "Y": "yellow", "G": "green", "B": "blue", "R": "red", "O": "orange"}

PROMPT = """\
A 3x3 Rubik's cube is solved except for its top layer. You are looking down at the corner \
where the top face (U), the front face (F, the left side of your view) and the right face \
(R, the right side of your view) meet.

Sticker colours: w=white, y=yellow, g=green, b=blue, r=red, o=orange. \
Opposite colours are white-yellow, green-blue and red-orange. \
This is a normal (non-mirrored) cube.

U face, viewed from above, back edge at the top:
{U}

F face, viewed head-on, top edge at the top:
{F}

R face, viewed head-on, top edge at the top:
{R}

The remaining faces (D, L, B) are hidden. D, L and B are the colours opposite to U, R and F \
respectively.

Give a sequence of moves that solves the cube, so that every face is a single colour \
again with the cube still in the orientation shown (no whole-cube rotations).

Moves: U, D, L, R, F, B turn that face 90 degrees clockwise as seen looking directly at \
that face. A trailing ' means counterclockwise and a trailing 2 means a half turn, \
e.g. R, R', R2. Use only these 18 moves. Faces are named as in the picture above: \
U is the top, F the face on the left, R the face on the right, D the bottom, \
L the hidden face opposite R, B the hidden face opposite F.

Write the moves separated by spaces inside <solution></solution> tags.
"""


def _grid(coloured, face, rows=(0, 1, 2)):
    base = ll.FACES.index(face) * 9
    return "\n".join(" ".join(coloured[base + 3 * r + c].lower() for c in range(3)) for r in rows)


def render_input(pid):
    """The full prompt text for a problem. Deterministic function of the problem id."""
    cid = config_id(pid)
    coloured = ll.coloured_facelets(cid)
    return PROMPT.format(U=_grid(coloured, "U"), F=_grid(coloured, "F"), R=_grid(coloured, "R"))


# ---------------------------------------------------------------------------
# Output: move sequence
# ---------------------------------------------------------------------------

MOVESET = tuple(f + m for f in "URFDLB" for m in ("", "'", "2"))   # the 18 outer-face turns
MOVE_RE = re.compile(r"[URFDLB]['2]?")
SOLUTION_RE = re.compile(r"<solution>(.*?)</solution>", re.DOTALL)


def extract_solution(response):
    """Contents of the last <solution>...</solution> tag in a response, or None."""
    found = SOLUTION_RE.findall(response)
    return found[-1] if found else None


def parse_moves(text, moveset=MOVESET):
    """Split on whitespace; every token must be exactly one allowed move. Returns a list or raises ValueError."""
    toks = text.split()
    if not toks:
        raise ValueError("empty move sequence")
    for t in toks:
        if not MOVE_RE.fullmatch(t) or t not in moveset:
            raise ValueError(f"invalid or disallowed move {t!r}")
    return toks


# ---------------------------------------------------------------------------
# Move simulator on the 54-facelet string (Kociemba order, camera frame)
# ---------------------------------------------------------------------------

NORMAL = {"U": (0, 1, 0), "R": (1, 0, 0), "F": (0, 0, 1), "D": (0, -1, 0), "L": (-1, 0, 0), "B": (0, 0, -1)}


def _sticker_pos(face, n):
    """Cubie coordinates (x right, y up, z front) of facelet n (1..9) on a face, per SPEC.md §3 layout."""
    r, c = divmod(n - 1, 3)
    return {"U": (c - 1, 1, r - 1), "R": (1, 1 - r, 1 - c), "F": (c - 1, 1 - r, 1),
            "D": (c - 1, -1, 1 - r), "L": (-1, 1 - r, c - 1), "B": (1 - c, 1 - r, -1)}[face]


def _cross(a, b):
    return ll.cross(a, b)


def _rot_cw(v, axis):
    """Rotate v by -90 degrees about axis (clockwise when seen from outside along axis)."""
    cx = _cross(axis, v)
    d = sum(a * b for a, b in zip(axis, v))
    return tuple(-cx[i] + axis[i] * d for i in range(3))


def _build_quarter_turns():
    pts = [(_sticker_pos(f, n), NORMAL[f]) for f in ll.FACES for n in range(1, 10)]
    where = {pt: i for i, pt in enumerate(pts)}
    perms = {}
    for face, axis in NORMAL.items():
        perm = list(range(54))                 # perm[i] = facelet that sticker i moves to
        for i, (p, nrm) in enumerate(pts):
            if sum(a * b for a, b in zip(p, axis)) == 1:
                perm[i] = where[(_rot_cw(p, axis), _rot_cw(nrm, axis))]
        perms[face] = perm
    return perms


_QUARTER = _build_quarter_turns()


def apply_moves(facelets, moves):
    f = list(facelets)
    for m in moves:
        perm = _QUARTER[m[0]]
        reps = {"": 1, "2": 2, "'": 3}[m[1:]]
        for _ in range(reps):
            g = f[:]
            for i, j in enumerate(perm):
                g[j] = f[i]
            f = g
    return "".join(f)


def invert(moves):
    inv = {"": "'", "'": "", "2": "2"}
    return [m[0] + inv[m[1:]] for m in reversed(moves)]


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

def grade(pid, response, moveset=MOVESET):
    """Binary grade of a raw model response. Returns (solved, reason, n_moves)."""
    sol = extract_solution(response)
    if sol is None:
        return False, "no <solution> tag", 0
    try:
        moves = parse_moves(sol, moveset)
    except ValueError as e:
        return False, str(e), 0
    _, state = from_problem_id(pid)
    final = apply_moves(ll.facelets(state), moves)
    if final != ll.SOLVED:
        return False, "cube not solved", len(moves)
    return True, "ok", len(moves)


# ---------------------------------------------------------------------------
# Self-checks
# ---------------------------------------------------------------------------

ALGS = {
    "T": "R U R' U' R' F R2 U' R' U' R U R' F'",
    "Ua": "R U' R U R U R U' R' U' R2",
    "Aa": "R' F R' B2 R F' R' B2 R2",
    "Y": "F R U' R' U' R U R' F' R U R' U' R' F R F'",
}


def selftest():
    # Turn conventions: R is clockwise from the right, so the F column rises onto U.
    after_r = apply_moves(ll.SOLVED, ["R"])
    assert [after_r[ll.idx("U", n)] for n in (3, 6, 9)] == ["F"] * 3
    after_u = apply_moves(ll.SOLVED, ["U"])
    assert [after_u[ll.idx("F", n)] for n in (1, 2, 3)] == ["R"] * 3   # U cw: R sticker moves to F
    for f in "URFDLB":
        for m in MOVESET:
            if m[0] == f:
                assert apply_moves(apply_moves(ll.SOLVED, [m]), invert([m])) == ll.SOLVED
        assert apply_moves(ll.SOLVED, [f] * 4) == ll.SOLVED

    # Every PLL facelet string is reached by words in U and a few PLL algs, and the
    # inverse word is a solution the grader accepts.
    gens = {"U": ["U"], "U'": ["U'"], "U2": ["U2"]}
    for name, a in ALGS.items():
        gens[name] = a.split()
        gens[name + "'"] = invert(a.split())
    seen = {ll.SOLVED: []}
    frontier = [ll.SOLVED]
    while frontier:
        nxt = []
        for s in frontier:
            for g in gens.values():
                t = apply_moves(s, g)
                if t not in seen:
                    seen[t] = seen[s] + g
                    nxt.append(t)
        frontier = nxt
    pll_faces = {ll.facelets(s): s for s in PLL_STATES}
    assert set(pll_faces) <= set(seen), "some PLL states not reachable: facelet layout or sim mismatch"
    # The sim must never leave the PLL set (stickers outside the LL stay put).
    assert set(seen) <= set(pll_faces) | {ll.facelets(s) for s in ll.ll_states() if ll.is_trivial(s)}
    ok = 0
    for pid in range(N_PROBLEMS):
        o, s = from_problem_id(pid)
        word = invert(seen[ll.facelets(s)])
        good = grade(pid, "<solution>" + " ".join(word) + "</solution>")
        assert good[0], (pid, good)
        ok += 1
    assert not grade(0, "no tag")[0]
    assert not grade(0, "<solution>R U2' B</solution>")[0]
    assert not grade(0, "<solution>x R</solution>")[0]
    assert not grade(0, "<solution></solution>")[0]
    assert len(PLL_STATES) == 284 and N_PROBLEMS == 6816
    return ok


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "export":
        for pid in range(N_PROBLEMS):
            o, s = from_problem_id(pid)
            print(json.dumps({"id": pid, "config_id": config_id(pid), "orientation": o,
                              "colours": dict(zip(("top", "front", "right"), ll.ORIENTATIONS[o])),
                              "input": render_input(pid)}))
        return
    print(f"PLL states: {N_PLL}   orientations: 24   problems: {N_PROBLEMS}")
    print(f"\n--- problem 0 ---\n{render_input(0)}")
    print(f"self-test passed; {selftest()} problems verified solvable end to end by the grader")


if __name__ == "__main__":
    main()
