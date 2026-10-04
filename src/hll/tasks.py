from inspect_ai import Task, task
from inspect_ai.solver import generate

from .dataset import pll_dataset
from .scorer import cube_solved

# Bump when a change can alter results or the task interface (prompt, pool, grading, defaults).
VERSION = 1


@task
def pll(orientations: str | int = "balanced", seed: int = 0, moves: str = "pll") -> Task:
    """Solve a PLL case from a two-faces-visible view of the cube.

    Args:
      orientations: "balanced" (284 samples, each PLL state once), "all" (6,816), or an int 0..23 to
        show every state in one colour orientation.
      seed: seeds the orientation assignment for "balanced".
      moves: allowed move set. "pll" = face turns, wide turns, slices and rotations; "face" = the 18 face turns.
    """
    return Task(
        dataset=pll_dataset(orientations, seed, moves),
        solver=generate(),
        scorer=cube_solved(moves),
        version=VERSION,
    )
