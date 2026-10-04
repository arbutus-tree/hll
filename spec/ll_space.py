"""Reference enumeration of the last-layer (LL) image configuration space.

See SPEC.md. Run `python3 spec/ll_space.py` to reproduce every count in the spec.
"""
from collections import Counter
from itertools import permutations, product

# Kociemba facelet order: U1..U9, R1..R9, F1..F9, D1..D9, L1..L9, B1..B9.
FACES = "URFDLB"
def idx(face, n):  # n is 1-based
    return FACES.index(face) * 9 + (n - 1)

# Last-layer slots, in Kociemba order. Each facelet triple/pair starts with the U sticker
# and runs clockwise (corners).
CORNER_SLOTS = ["URF", "UFL", "ULB", "UBR"]
CORNER_FACELETS = [
    (idx("U", 9), idx("R", 1), idx("F", 3)),
    (idx("U", 7), idx("F", 1), idx("L", 3)),
    (idx("U", 1), idx("L", 1), idx("B", 3)),
    (idx("U", 3), idx("B", 1), idx("R", 3)),
]
EDGE_SLOTS = ["UR", "UF", "UL", "UB"]
EDGE_FACELETS = [
    (idx("U", 6), idx("R", 2)),
    (idx("U", 8), idx("F", 2)),
    (idx("U", 4), idx("L", 2)),
    (idx("U", 2), idx("B", 2)),
]

SOLVED = "".join(f * 9 for f in FACES)

# The 14 LL stickers visible in a U/F/R corner view, and the 6 hidden ones.
VISIBLE = [idx("U", n) for n in (1, 2, 3, 4, 6, 7, 8, 9)] + \
          [idx("F", n) for n in (1, 2, 3)] + [idx("R", n) for n in (1, 2, 3)]
HIDDEN = [idx("B", n) for n in (1, 2, 3)] + [idx("L", n) for n in (1, 2, 3)]


def parity(p):
    return sum(1 for i in range(4) for j in range(i + 1, 4) if p[i] > p[j]) % 2


def ll_states():
    """All 62,208 reachable LL states as (cp, co, ep, eo) tuples, lexicographic order."""
    for cp in permutations(range(4)):
        for co in product(range(3), repeat=4):
            if sum(co) % 3:
                continue
            for ep in permutations(range(4)):
                if parity(cp) != parity(ep):
                    continue
                for eo in product(range(2), repeat=4):
                    if sum(eo) % 2:
                        continue
                    yield cp, co, ep, eo


def facelets(state):
    cp, co, ep, eo = state
    f = list(SOLVED)
    for i in range(4):
        for k in range(3):
            # sticker k of the piece sitting in slot i lands on facelet (k + co) of the slot
            f[CORNER_FACELETS[i][(k + co[i]) % 3]] = CORNER_SLOTS[cp[i]][k]
        for k in range(2):
            f[EDGE_FACELETS[i][(k + eo[i]) % 2]] = EDGE_SLOTS[ep[i]][k]
    return "".join(f)


def is_trivial(state):
    """Solved or solved-up-to-AUF: no twist/flip and the permutation is a pure U-turn."""
    cp, co, ep, eo = state
    if any(co) or any(eo):
        return False
    return any(cp == tuple((i + k) % 4 for i in range(4)) and ep == cp for k in range(4))


# Reference colour scheme (Western/BOY): white up, green front, red right,
# yellow down, blue back, orange left. Axes: x = right, y = up, z = front.
COLOUR_VEC = {"W": (0, 1, 0), "Y": (0, -1, 0), "G": (0, 0, 1),
              "B": (0, 0, -1), "R": (1, 0, 0), "O": (-1, 0, 0)}
COLOUR_ORDER = "WYGBRO"
OPPOSITE = {"W": "Y", "Y": "W", "G": "B", "B": "G", "R": "O", "O": "R"}


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def orientations():
    """The 24 (top, front, right) colour triples, ordered by (top, front) in COLOUR_ORDER."""
    out = []
    for top in COLOUR_ORDER:
        for front in COLOUR_ORDER:
            if front in (top, OPPOSITE[top]):
                continue
            rv = cross(COLOUR_VEC[top], COLOUR_VEC[front])  # right = up x front
            right = next(c for c, v in COLOUR_VEC.items() if v == rv)
            out.append((top, front, right))
    return out


def colour_map(orientation):
    top, front, right = orientation
    return {"U": top, "F": front, "R": right,
            "D": OPPOSITE[top], "B": OPPOSITE[front], "L": OPPOSITE[right]}


NONTRIVIAL = [s for s in ll_states() if not is_trivial(s)]
RANK = {s: i for i, s in enumerate(NONTRIVIAL)}
ORIENTATIONS = orientations()


def config_id(orientation_index, state):
    return orientation_index * len(NONTRIVIAL) + RANK[state]


def from_config_id(cid):
    o, r = divmod(cid, len(NONTRIVIAL))
    return o, NONTRIVIAL[r]


def coloured_facelets(cid):
    o, state = from_config_id(cid)
    cmap = colour_map(ORIENTATIONS[o])
    return "".join(cmap[c] for c in facelets(state))


def main():
    allstates = list(ll_states())
    states = [s for s in allstates if not is_trivial(s)]
    print(f"reachable LL states (incl. AUF):      {len(allstates)}")
    print(f"excluded trivial (solved + 3 AUFs):   {len(allstates) - len(states)}")
    print(f"non-trivial LL states:                {len(states)}")
    print(f"colour orientations:                  24")
    print(f"total configurations:                 {len(states) * 24}")
    print("\norientations (index: top front right):")
    for i, o in enumerate(ORIENTATIONS):
        print(f"  {i:2d}: {' '.join(o)}")
    for cid in (0, 1, 62204, 1492895):
        o, st = from_config_id(cid)
        print(f"config {cid}: orientation={o} state={st}\n  letters={facelets(st)}\n  colours={coloured_facelets(cid)}")

    for name, sub in [("all LL", states),
                      ("PLL (oriented)", [s for s in states if not any(s[1]) and not any(s[3])])]:
        groups = Counter("".join(facelets(s)[i] for i in VISIBLE) for s in sub)
        sizes = Counter(groups.values())
        unique = sizes.get(1, 0)
        print(f"\n[{name}] states={len(sub)}  distinct views={len(groups)}  "
              f"uniquely-identified states={unique} ({unique / len(sub):.2%})")
        print("  states per view -> number of views:", dict(sorted(sizes.items())))
        # Back edges both showing the top colour: only permutation parity tells them apart.
        need_parity = sum(1 for s in sub if s[3][2] == 0 and s[3][3] == 0)
        print(f"  states needing parity (UL and UB both show U on top): {need_parity}")


if __name__ == "__main__":
    main()
