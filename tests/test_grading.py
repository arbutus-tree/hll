import pytest

from hll import pll
from hll.grading import grade


def sol(moves):
    return f"reasoning...\n<solution>{moves}</solution>"


def reference(pid):
    return " ".join(pll.reference_solution(pll.from_problem_id(pid)[1]))


def test_reference_passes_and_reports_length():
    for pid in (0, 1, 283, 284, 6815):
        g = grade(pid, sol(reference(pid)))
        assert g.solved and g.reason == "ok" and g.n_moves > 0


def test_rotated_ending_is_accepted():
    # Aa written without closing rotation ends the cube rotated; still solved
    pid = next(i for i in range(284) if pll.CASES[pll.PLL_STATES[i]][0] == "Aa" and not pll.CASES[pll.PLL_STATES[i]][1] and not pll.CASES[pll.PLL_STATES[i]][2])
    ref = reference(pid).split()
    assert ref[-1] == "x'"
    assert grade(pid, sol(" ".join(ref[:-1]))).solved
    assert grade(pid, sol(" ".join(ref[:-1] + ["y"]))).solved       # any final orientation


def test_alternate_spellings_accepted():
    pid = 5
    ref = reference(pid)
    spelled = ref.replace("R2", "R2'")
    assert grade(pid, sol(spelled)).solved


def test_failure_reasons():
    assert grade(0, "no tag").reason == "no_solution_tag"
    assert grade(0, sol("")).reason == "empty"
    assert grade(0, sol("   ")).reason == "empty"
    for bad in ("R U2' foo", "(R U)", "R U R'.", "Q", "R2'2"):
        assert grade(0, sol(bad)).reason == "invalid_move", bad
    assert grade(0, sol("R U R'")).reason == "not_solved"
    assert grade(0, sol("R U R'")).n_moves == 3


def test_last_tag_wins():
    pid = 3
    text = f"<solution>R</solution> actually: <solution>{reference(pid)}</solution>"
    assert grade(pid, text).solved


def test_face_moveset_rejects_extended_moves():
    pid = next(i for i in range(284) if pll.CASES[pll.PLL_STATES[i]][0] == "H")
    ref = reference(pid)
    assert "M" in ref
    assert grade(pid, sol(ref), "pll").solved
    assert grade(pid, sol(ref), "face").reason == "invalid_move"
