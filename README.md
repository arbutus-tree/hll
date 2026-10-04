# hll: last-layer eval

An [Inspect AI](https://inspect.aisi.org.uk) eval. A model sees two sides and the top of a 3x3 cube that is solved
except for the last layer, and must write a move sequence that solves it. The first task, `pll`, uses the 284
PLL states (any PLL case at any AUF), in any of the 24 colour orientations.

- [SPEC.md](SPEC.md): the configuration space (facelet layout, orientations, what is visible).
- [PROBLEMS.md](PROBLEMS.md): the PLL problem pool, prompt, notation, grading and sampling.

## Run

```
pip install -e '.[dev]'
inspect eval hll/pll --model <provider/model>          # 284 samples
inspect eval hll/pll --model <provider/model> -T orientations=all     # 6,816 samples
inspect eval hll/pll --model <provider/model> -T moves=face           # face turns only
pytest
```

Task parameters: `orientations` (`balanced` | `all` | 0..23), `seed`, `moves` (`pll` | `face`).
Data is generated deterministically at load time from this repo, so there is nothing to download.

## Layout

```
src/hll/ll_space.py   configuration space (SPEC.md)           } no inspect_ai needed
src/hll/moves.py      notation policy and parser; simulation via magiccube }
src/hll/pll.py        pool, 21 PLL algs/cases, prompt          }
src/hll/grading.py    answer extraction and grading            }
src/hll/dataset.py    Inspect samples (ids, metadata, target)
src/hll/scorer.py     scorer and metrics (accuracy, clustered stderr, per-case accuracy)
src/hll/tasks.py      @task pll, with VERSION
tests/
```

Each sample records `case`, the pre/post AUF, the reference solution (as `target`) and its length in metadata; each score records
`reason`, `n_moves` and `reference_len`. These are the hooks for separating recalled algorithms from derived solutions.

## Status

Scaffold. Not yet done: baseline runs, a published listing (the Inspect Evals register wants a pinned commit and logs from two models),
image input, the dimensions beyond PLL.
