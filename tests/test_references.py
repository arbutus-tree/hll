"""Checks of the simulation backend against things we did not write.

GOLDEN: facelet strings produced by an independent hand-written simulator (since removed) and found
identical to magiccube on all 54 moves and 3,000 random sequences. They pin the behaviour so a library
upgrade that changes a slice or rotation convention fails here.

kociemba: an unrelated two-phase solver. It must accept every PLL state as a valid cube, and its
solutions must solve the state under our adaptor. This checks the facelet layout of SPEC.md section 3.
"""
import random

import pytest

from hll import ll_space as ll
from hll import pll
from hll.moves import MOVESETS, apply_moves, is_solved, parse_moves

GOLDEN = [
    ("Dw Lw' U2 Bw Bw' z' Rw' D L2 S' Bw R2 E' B2 Bw2 M Lw2 Bw'",
     "BRLLBBFUFLDBFLFLURURULDDLFDBUFFFBDLBDBRBRDRLUDDRRURUUF"),
    ("Bw2 Rw2 M Bw z' S D' E2 U' U' S' Bw S S' Lw'",
     "BDFBDLDUURFDRBRBDLLRFLLFDBRBUDBULBDFRRFUFULLLRBUDRFUFU"),
    ("E2 B2 Rw2 D2 Fw Lw2 Dw Rw' D'",
     "RDULDUDFFRBBUBFDRLBRDULLUFBFLRBUURRDUDLBFFUDLLRBDRLFBF"),
    ("Rw2 z' Uw' Dw2 D S' S U' E L2 D Rw2 x Bw' S Bw U",
     "UDUBDBBDBLLLDFDDFBDFDLRRLRRBFFUUUDUURRRFBUFBUFBFLLLRRL"),
    ("R' Uw' Rw' M y' Fw2 M2 S' M2 L2 Fw' F y2 Dw2",
     "DDUDUDRRULFFRLURLUUUBRBDRBDDUBBDUDLLBBBLRFFRFRLLFFBFFL"),
    ("Bw2 S Fw' Rw R' L x' M' Fw S2 Bw' D' R2 Lw2 Dw'",
     "LFLLBLDDDLUULUUBBBFRFFLFLLUUBRUFRUURDDRDDRFFFBDBBRBDRR"),
    ("Dw R' Lw2 B2 Uw Bw' y Rw2 S y2 z' Fw2 L Uw2 L' S2 R' S'",
     "RBRFFBBBLURFFLLBLBDLFDUULUDBRLBBFLLUFDRFRRDUUDDUUDRRDF"),
    ("Bw' z2 Bw2 F2 R Uw2 Uw Bw' Bw x' Uw2 Fw' U2 S Uw' z' M' Fw x Lw Uw L'",
     "DDFLUBBUURRDRRFFFRUFFDFFRBLBUDBDDUDBBULRLBLLDRRLLBUULF"),
    ("M2 L' Dw' U D' R' Bw E'",
     "LLLUFBUULURUBLLBDDRRFFUUBFUDURBBRDDRDLFRRDFDRBBBFDFFLL"),
    ("D2 x2 F Lw' Lw' R' Bw2 Dw' M' Lw' Rw2 F2 D2 z' M Rw2 F2",
     "BDLBLRUFULDBUUFRLLRDBFFLFUDRRBDRFLUDRRFLDUFLDDBURBBFBU"),
]


@pytest.mark.parametrize("seq,expected", GOLDEN)
def test_golden_vectors(seq, expected):
    assert apply_moves(ll.SOLVED, parse_moves(seq, "pll")) == expected


def test_golden_vectors_cover_every_kind_of_move():
    used = {m for seq, _ in GOLDEN for m in parse_moves(seq, "pll")}
    for kind in ("U", "Dw", "Bw", "M", "E", "S", "x", "y", "z"):
        assert any(m.startswith(kind) for m in used), kind


def test_kociemba_accepts_and_solves_every_pll_state():
    kociemba = pytest.importorskip("kociemba")
    for s in pll.PLL_STATES:
        f = ll.facelets(s)
        sol = kociemba.solve(f).split()          # raises on an invalid cube
        assert apply_moves(f, parse_moves(" ".join(sol), "face")) == ll.SOLVED


def test_kociemba_agrees_on_random_face_turn_states():
    kociemba = pytest.importorskip("kociemba")
    rng = random.Random(3)
    faces = sorted(MOVESETS["face"])
    for _ in range(40):
        f = apply_moves(ll.SOLVED, [rng.choice(faces) for _ in range(rng.randint(5, 30))])
        sol = kociemba.solve(f).split()
        assert apply_moves(f, parse_moves(" ".join(sol), "face")) == ll.SOLVED
