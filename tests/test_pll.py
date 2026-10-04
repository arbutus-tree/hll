from collections import Counter

import pytest

from hll import ll_space as ll
from hll import pll
from hll.moves import apply_moves, invert, is_solved


def test_pool_sizes():
    assert pll.N_PLL == 284 and pll.N_PROBLEMS == 6816
    assert all(not any(s[1]) and not any(s[3]) for s in pll.PLL_STATES)


def test_every_alg_is_a_pll_in_all_aufs():
    """Each of the 21 algs, conjugated by any AUF pair, must stay within the PLL set (catches typos)."""
    by_faces = {ll.facelets(s) for s in pll.PLL_STATES}
    for name, alg in pll.ALGS.items():
        closed = pll._closed(alg)
        for pre in pll._AUF:
            for post in pll._AUF:
                faces = apply_moves(ll.SOLVED, invert(pre + closed + post))
                assert faces in by_faces, (name, pre, post)


def test_cases_cover_pool_with_expected_symmetry_counts():
    assert set(pll.CASES) == set(pll.PLL_STATES)
    counts = Counter(c for c, _, _ in pll.CASES.values())
    assert len(counts) == 21
    # AUF-distinct states per case, from the case's symmetry group
    assert counts["H"] == 4 and counts["Na"] == 4 and counts["Nb"] == 4
    assert counts["E"] == 8 and counts["Z"] == 8
    assert all(counts[c] == 16 for c in counts if c not in ("H", "Na", "Nb", "E", "Z"))


def test_reference_solution_solves_everything_and_rotations_are_exercised():
    uses_rotation = uses_slice = 0
    for pid in range(pll.N_PLL):      # orientation 0; the answer does not depend on colour (SPEC.md section 8)
        o, s = pll.from_problem_id(pid)
        ref = pll.reference_solution(s)
        assert pll.check_solved(pid, ref), (pid, ref)
        uses_rotation += any(m[0] in "xyz" for m in ref)
        uses_slice += any(m[0] in "MES" for m in ref)
    assert uses_rotation and uses_slice


def test_reference_solution_is_not_trivially_shorter_than_it_looks():
    # the reference must beat "the empty answer": the unsolved state is not solved
    for s in pll.PLL_STATES:
        assert not is_solved(ll.facelets(s))


def test_balanced_orientations_are_balanced_and_seeded():
    a = pll.balanced_orientations(0)
    assert len(a) == 284 and set(a) == set(range(24))
    counts = Counter(a)
    assert set(counts.values()) <= {11, 12}
    assert a == pll.balanced_orientations(0) and a != pll.balanced_orientations(1)


def test_prompt_matches_view():
    text = pll.render_input(0)
    assert text.count("<solution>") == 1
    assert "whatever its final orientation" in text
    assert "Do not use whole-cube rotations" in pll.render_input(0, "face")
    # all three grids appear with the right shape
    coloured = ll.coloured_facelets(pll.config_id(0))
    assert " ".join(coloured[ll.idx("U", n)].lower() for n in (1, 2, 3)) in text
