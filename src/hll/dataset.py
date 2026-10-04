"""Build the Inspect dataset for the PLL eval."""
from inspect_ai.dataset import MemoryDataset, Sample

from . import ll_space as ll
from . import pll
from .moves import DEFAULT_MOVESET

# How orientations are assigned to the 284 PLL states.
#   "balanced": each state once, orientations spread evenly and shuffled by seed   -> 284 samples (default)
#   "all":      every (state, orientation) pair                                    -> 6,816 samples
#   <int>:      each state once, all in that orientation index (0..23)            -> 284 samples


def problem_ids(orientations="balanced", seed=0):
    if orientations == "balanced":
        return [pll.problem_id(o, s) for s, o in zip(pll.PLL_STATES, pll.balanced_orientations(seed))]
    if orientations == "all":
        return list(range(pll.N_PROBLEMS))
    if isinstance(orientations, int) and 0 <= orientations < pll.N_ORIENTATIONS:
        return [pll.problem_id(orientations, s) for s in pll.PLL_STATES]
    raise ValueError(f"orientations must be 'balanced', 'all' or an int 0..23, got {orientations!r}")


def make_sample(pid, moveset=DEFAULT_MOVESET):
    o, state = pll.from_problem_id(pid)
    case, pre, post = pll.CASES[state]
    ref = pll.reference_solution(state)
    return Sample(
        id=pid,
        input=pll.render_input(pid, moveset),
        target=" ".join(ref),
        metadata={
            "problem_id": pid,
            "config_id": pll.config_id(pid),
            "state_rank": pll.PLL_RANK[state],      # cluster key: the 24 colourings of a state are one unit
            "orientation": o,
            "colours": dict(zip(("top", "front", "right"), ll.ORIENTATIONS[o])),
            "case": case,
            "pre_auf": " ".join(pre),
            "post_auf": " ".join(post),
            "reference_len": len(ref),
            "facelets": pll.problem_facelets(pid),  # what the scorer starts from
            "moveset": moveset,
        },
    )


def pll_dataset(orientations="balanced", seed=0, moveset=DEFAULT_MOVESET):
    return MemoryDataset([make_sample(p, moveset) for p in problem_ids(orientations, seed)], name="pll")
