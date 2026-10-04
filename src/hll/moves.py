"""Move notation policy, plus a thin adaptor over `magiccube` for the actual cube simulation.

What we own here: which spellings are accepted (`canonical`), which moves are allowed in a given eval
(`MOVESETS`), parsing a model's answer (`parse_moves`), and converting between our 54-letter Kociemba
facelet strings (SPEC.md) and the library's cube. What the library owns: turning moves into a new cube
state. Moves act on positions in space (R is whichever face is on the viewer's right), the standard
convention; after `y`, `R` turns the face that used to be at the back.
"""
import re

from magiccube import Cube

from . import ll_space as ll

# ---------------------------------------------------------------------------
# Notation
# ---------------------------------------------------------------------------

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
# Simulation (delegated to magiccube)
# ---------------------------------------------------------------------------

# magiccube works in colours with its default scheme (white up, green front, red right, yellow down,
# orange left, blue back) and takes faces in U L F R B D order. Our letters are Kociemba order U R F D L B.
_LETTER_TO_COLOUR = {"U": "W", "R": "R", "F": "G", "D": "Y", "L": "O", "B": "B"}


def _to_cube(facelets):
    faces = {f: facelets[9 * i:9 * i + 9] for i, f in enumerate(ll.FACES)}
    return Cube(3, "".join(_LETTER_TO_COLOUR[ch] for f in "ULFRBD" for ch in faces[f]))


def apply_moves(facelets, moves):
    """Apply canonical moves to a 54-letter facelet string; returns the new string."""
    cube = _to_cube(facelets)
    if moves:
        cube.rotate(" ".join(moves))
    return cube.get_kociemba_facelet_positions()


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
