import pytest

from hll import ll_space as ll
from hll.moves import MOVESETS, MoveError, apply_moves, canonical, invert, is_solved, parse_moves, rotation_fix


def run(moves, start=ll.SOLVED):
    return apply_moves(start, moves.split() if isinstance(moves, str) else moves)


def test_sizes():
    assert len(MOVESETS["face"]) == 18
    assert len(MOVESETS["pll"]) == 54


@pytest.mark.parametrize("tok,expect", [
    ("R", "R"), ("R'", "R'"), ("R2", "R2"), ("R2'", "R2"), ("r", "Rw"), ("Rw'", "Rw'"), ("u2", "Uw2"),
    ("M2'", "M2"), ("x", "x"), ("z'", "z'"),
    ("R2''", None), ("2R", None), ("X", None), ("RW", None), ("Rww", None), ("m", None), ("R'2", None), ("", None),
])
def test_canonical(tok, expect):
    assert canonical(tok) == expect


def test_parse_respects_moveset():
    assert parse_moves("R U r' M2' x", "pll") == ["R", "U", "Rw'", "M2", "x"]
    for bad in ("r", "M", "x", "Rw"):
        with pytest.raises(MoveError):
            parse_moves(bad, "face")
    with pytest.raises(MoveError):
        parse_moves("", "pll")
    with pytest.raises(MoveError):
        parse_moves("(R U)", "pll")


def test_turn_directions():
    # R clockwise from the right: the F column rises onto U.
    after_r = run("R")
    assert [after_r[ll.idx("U", n)] for n in (3, 6, 9)] == ["F"] * 3
    # U clockwise from above: the R sticker moves onto F.
    after_u = run("U")
    assert [after_u[ll.idx("F", n)] for n in (1, 2, 3)] == ["R"] * 3


def test_inverses_and_orders():
    from hll.moves import MOVESETS
    for m in MOVESETS["pll"]:
        assert run(invert([m]), run([m])) == ll.SOLVED, m
    for base in ["U", "R", "F", "D", "L", "B", "Rw", "Uw", "M", "E", "S", "x", "y", "z"]:
        assert run([base] * 4) == ll.SOLVED
        assert run([base + "2"] * 2) == ll.SOLVED


@pytest.mark.parametrize("a,b", [
    ("x", "R M' L'"), ("y", "U E' D'"), ("z", "F S B'"),          # rotations as stacks of layers
    ("Rw", "R M'"), ("Lw", "L M"), ("Uw", "U E'"), ("Dw", "D E"), ("Fw", "F S"), ("Bw", "B S'"),  # wide turns
    ("x2", "x x"),
])
def test_identities(a, b):
    assert run(a) == run(b)


def test_centres_move_only_for_slices_wide_rotations():
    for m in ["U", "R", "F", "D", "L", "B"]:
        assert rotation_fix(run(m)) == []
    assert rotation_fix(run("x")) == ["x'"] and rotation_fix(run("y2")) == ["y2"]
    assert len(rotation_fix(run("x y"))) == 2
    assert is_solved(run("x")) and is_solved(run("y z")) and not is_solved(run("R"))
    assert not is_solved(run("M"))


def test_rotation_conjugation_convention():
    # After y, R turns the face that was at the back: y R == B y.
    assert run("y R") == run("B y")
    assert run("x U") == run("F x")        # x carries the front to the top
