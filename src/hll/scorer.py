"""Inspect scorer: parse the answer, simulate it, and check the cube is solved."""
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, grouped, scorer, stderr
from inspect_ai.solver import TaskState

from . import grading


@scorer(metrics=[
    accuracy(),
    stderr(cluster="state_rank"),            # colourings of one state are not independent samples
    grouped(accuracy(), "case"),             # per-PLL-case accuracy
])
def cube_solved(moveset: str = "pll"):
    async def score(state: TaskState, target: Target) -> Score:
        meta = state.metadata
        text = state.output.completion
        g = grading.grade(meta["problem_id"], text, moveset)
        return Score(
            value=CORRECT if g.solved else INCORRECT,
            answer=grading.extract_solution(text),
            explanation=g.reason if not g.detail else f"{g.reason}: {g.detail}",
            metadata={"reason": g.reason, "n_moves": g.n_moves,
                      "reference_len": meta["reference_len"], "case": meta["case"]},
        )
    return score
