import pytest
from inspect_ai import Task, eval
from inspect_ai.dataset import MemoryDataset
from inspect_ai.model import ModelOutput
from inspect_ai.solver import solver

from hll import pll
from hll.dataset import pll_dataset, problem_ids
from hll.scorer import cube_solved
from hll.tasks import VERSION, pll as pll_task


def test_default_dataset():
    ds = pll_dataset()
    assert len(ds) == 284
    ids = [s.id for s in ds]
    assert len(set(ids)) == 284
    assert {s.metadata["state_rank"] for s in ds} == set(range(284))
    assert {s.metadata["case"] for s in ds} == set(pll.ALGS)
    assert [s.id for s in pll_dataset(seed=0)] == ids and [s.id for s in pll_dataset(seed=1)] != ids


def test_variants():
    assert len(problem_ids("all")) == 6816
    assert len(problem_ids(7)) == 284 and {pll.from_problem_id(p)[0] for p in problem_ids(7)} == {7}
    for bad in ("nope", 24, -1):
        with pytest.raises(ValueError):
            problem_ids(bad)


def test_sample_ids_are_stable_across_variants():
    full = {s.id: s.input for s in pll_dataset("all")}
    for s in pll_dataset("balanced"):
        assert full[s.id] == s.input


@solver
def scripted(outputs):
    """Stand-in for generate(): set the model output for each sample id directly (no model, no tokenizer)."""
    async def solve(state, generate):
        state.output = ModelOutput.from_content("mockllm/model", outputs[state.sample_id])
        return state
    return solve


def _run(samples, answers, tmp_path):
    task = Task(dataset=MemoryDataset(samples), solver=scripted(dict(zip((s.id for s in samples), answers))),
                scorer=cube_solved())
    return eval(task, model="mockllm/model", display="none", log_dir=str(tmp_path))[0]


def test_task_builds_with_defaults():
    t = pll_task()
    assert len(t.dataset) == 284 and t.version == VERSION
    assert len(pll_task(orientations="all").dataset) == 6816


def test_end_to_end_reference_answers_score_one(tmp_path):
    samples = list(pll_dataset())[:6]
    log = _run(samples, [f"<solution>{s.target}</solution>" for s in samples], tmp_path)
    assert log.status == "success"
    metrics = {m.name: m.value for m in log.results.scores[0].metrics.values()}
    assert metrics["accuracy"] == 1.0
    assert {s.scores["cube_solved"].metadata["reason"] for s in log.samples} == {"ok"}


def test_end_to_end_mixed(tmp_path):
    samples = list(pll_dataset())[:4]
    answers = [f"<solution>{samples[0].target}</solution>", "I give up", "<solution>R U</solution>", "<solution>Q</solution>"]
    log = _run(samples, answers, tmp_path)
    got = {s.id: s.scores["cube_solved"].metadata["reason"] for s in log.samples}
    assert [got[s.id] for s in samples] == ["ok", "no_solution_tag", "not_solved", "invalid_move"]
    assert {m.name for m in log.results.scores[0].metrics.values()} >= {"accuracy", "stderr"}
