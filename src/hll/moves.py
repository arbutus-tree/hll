"""Move notation and a facelet-level cube simulator, in the camera frame of SPEC.md.

Every move is a rotation of the stickers lying in some set of layers about a fixed axis, so face turns,
wide turns, slices and whole-cube rotations all come from one table. Moves always act on *positions in
space* (R is whichever face is currently on the viewer's right), which is the standard convention.
After `y`, for example, `R` turns the face that used to be at the back.
"""
import re

from . import ll_space as ll

# ---------------------------------------------------------------------------
# Notation
# ---------------------------------------------------------------------------

AXIS = {"U": (0, 1, 0), "R": (1, 0, 0), "F": (0, 0, 1), "D": (0, -1, 0), "L": (-1, 0, 0), "B": (0, 0, -1)}

# canonical base move -> (named face whose direction it follows, layers counted from that face's outer
# layer: 1 = outer, 0 = middle, -1 = far side).
_BASE = {}
for _f in "URFDLB":
    _BASE[_f] = (_f, (1,))                  # face turn
    _BASE[_f + "w"] = (_f, (1, 0))          # wide turn: outer + middle layer
_BASE["M"] = ("L", (0,))                    # slices follow L, D, F respectively
_BASE["E"] = ("D", (0,))
_BASE["S"] = ("F", (0,))
_BASE["x"] = ("R", (1, 0, -1))              # rotations follow R, U, F
_BASE["y"] = ("U", (1, 0, -1))
_BASE["z"] = ("F", (1, 0, -1))

FACE_TURNS = tuple(f for f in "URFDLB")
WIDE_TURNS = tuple(f + "w" for f in "URFDLB")
SLICES = ("M", "E", "S")
ROTATIONS = ("x", "y", "z")

_TOKEN_RE = re.compile(r"(?:([URFDLB])w|([urfdlb])|([URFDLBMESxyz]))(2'|2|')?")
_QUARTERS = {None: 1, "'": 3, "2": 2, "2'": 2}
_SUFFIX = {1: "", 2: "2", 3: "'"}


def canonical(token):
    """Canonical name of a move token, or None if it is not valid notation.

    Accepted spellings: `R`, `R'`, `R2`, `R2'` (a half turn written with either direction), wide turns as
    `Rw` or `r`, slices `M E S`, rotations `x y z`. Canonical form uses `Rw` and drops the `2'` spelling.
    """
    m = _TOKEN_RE.fullmatch(token)
    if not m:
        return None
    wide, lower, plain, suffix = m.groups()
    if wide:
        base = wide + "w"
    elif lower:
        base = lower.upper() + "w"
    else:
        base = plain
    return base + _SUFFIX[_QUARTERS[suffix]]


def _expand(bases):
    return frozenset(b + s for b in bases for s in ("", "'", "2"))


# Named sets of allowed moves, as canonical names.
MOVESETS = {
    "face": _expand(FACE_TURNS),                                                   # 18
    "pll": _expand(FACE_TURNS + WIDE_TURNS + SLICES + ROTATIONS),                  # 54: everything in typical PLL algs
}
DEFAULT_MOVESET = "pll"


class MoveError(ValueError):
    pass


def parse_moves(text, moveset=DEFAULT_MOVESET):
    """Split on whitespace; each token must be one move in the moveset. Returns canonical names."""
    allowed = MOVESETS[moveset] if isinstance(moveset, str) else moveset
    toks = text.split()
    if not toks:
        raise MoveError("empty move sequence")
    out = []
    for t in toks:
        c = canonical(t)
        if c is None:
            raise MoveError(f"not a move: {t!r}")
        if c not in allowed:
            raise MoveError(f"move not allowed here: {t!r}")
        out.append(c)
    return out


def invert(moves):
    flip = {"": "'", "'": "", "2": "2"}
    out = []
    for m in reversed(moves):
        base = m.rstrip("'2")
        out.append(base + flip[m[len(base):]])
    return out


# ---------------------------------------------------------------------------
# Simulator on the 54-facelet string (Kociemba order, camera frame)
# ---------------------------------------------------------------------------

def _sticker_pos(face, n):
    """Cubie coordinates (x right, y up, z front) of facelet n (1..9), per SPEC.md §3 layout."""
    r, c = divmod(n - 1, 3)
    return {"U": (c - 1, 1, r - 1), "R": (1, 1 - r, 1 - c), "F": (c - 1, 1 - r, 1),
            "D": (c - 1, -1, 1 - r), "L": (-1, 1 - r, c - 1), "B": (1 - c, 1 - r, -1)}[face]


def _rot_cw(v, axis):
    """Rotate v by -90 degrees about axis (clockwise when seen from outside along axis)."""
    cx = ll.cross(axis, v)
    d = sum(a * b for a, b in zip(axis, v))
    return tuple(-cx[i] + axis[i] * d for i in range(3))


def _build_quarter_turns():
    pts = [(_sticker_pos(f, n), AXIS[f]) for f in ll.FACES for n in range(1, 10)]
    where = {pt: i for i, pt in enumerate(pts)}
    perms = {}
    for name, (face, layers) in _BASE.items():
        axis = AXIS[face]
        perm = list(range(54))                 # perm[i] = facelet that sticker i moves to
        for i, (p, nrm) in enumerate(pts):
            if sum(a * b for a, b in zip(p, axis)) in layers:
                perm[i] = where[(_rot_cw(p, axis), _rot_cw(nrm, axis))]
        perms[name] = perm
    return perms


_QUARTER = _build_quarter_turns()


def apply_moves(facelets, moves):
    f = list(facelets)
    for m in moves:
        base = m.rstrip("'2")
        perm = _QUARTER[base]
        for _ in range(_QUARTERS[m[len(base):] or None]):
            g = f[:]
            for i, j in enumerate(perm):
                g[j] = f[i]
            f = g
    return "".join(f)


def is_solved(facelets):
    """Every face a single colour. Counts a cube that ended up in a different whole-cube orientation."""
    return all(len(set(facelets[9 * i:9 * i + 9])) == 1 for i in range(6))


CENTRES = [ll.idx(f, 5) for f in ll.FACES]
_ROTATION_MOVES = tuple(r + s for r in ROTATIONS for s in ("", "'", "2"))


def rotation_fix(facelets):
    """Shortest whole-cube rotation sequence that puts the centres back where they belong (possibly [])."""
    frontier = [([], facelets)]
    seen = {tuple(facelets[i] for i in CENTRES)}
    if "".join(facelets[i] for i in CENTRES) == ll.FACES:
        return []
    while frontier:
        nxt = []
        for seq, f in frontier:
            for r in _ROTATION_MOVES:
                g = apply_moves(f, [r])
                key = tuple(g[i] for i in CENTRES)
                if "".join(key) == ll.FACES:
                    return seq + [r]
                if key not in seen:
                    seen.add(key)
                    nxt.append((seq + [r], g))
        frontier = nxt
    raise AssertionError("unreachable: centres are a rotation of the canonical ones")
