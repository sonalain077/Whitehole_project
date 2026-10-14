# AIE2609 — entity-level news sentiment for the S&P 500

Python command-line pipeline: `news.json` + `sp500.csv` → `entities.csv` + `scores.csv`.
For every article, `gpt-5.6-terra` identifies the companies of the supplied universe
and the role each one plays; code validates every answer, resolves share classes,
reviews flagged articles, combines independent passes by majority vote and computes:

```text
weight = 0.5 ** (age_in_days / 7)          # as_of = 2026-09-29T00:00 America/New_York
score(ticker) = sum(label_value × weight)  # positive = +1, neutral = 0, negative = -1
```

## Quick start

Python 3.12+. Put `news.json` and `sp500.csv` in the repository root (they are not
published here) and set `OPENAI_API_KEY` as an environment variable or in a local
`.env` file (see `.env.example`).

```bash
python -m venv .venv
# Linux/macOS: .venv/bin/python   Windows: .venv\Scripts\python.exe
.venv/bin/python -m pip install --require-hashes -r build-requirements.lock -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m unittest discover -s tests          # offline, no key needed
.venv/bin/python -m aie2609 run --max-cost-usd 10       # end to end (paid)
```

Tested with Python 3.12.10 on Windows. The only runtime dependency is `tzdata`
(time-zone data for Windows), pinned with hashes. Without the two input files, the
8 tests that read them are reported as skipped.

## End-to-end command

`run` writes a new directory `output/run-<UTC timestamp>/` (or `--output-dir`, which
must not exist) and prints calls, retries, tokens per category, total cost, cost per
article and cost per step. Defaults are the configuration measured as the most
reliable: three passes combined by majority vote, up to three attempts per article.
Expected cost with a cold provider cache: about 4.5 USD, i.e. 0.045 USD per article.
`--passes 1` costs about 1.5 times less, because passes 2 and 3 read the provider cache.

Each pass runs these steps in `pass-N/` (directly in the run directory with `--passes 1`):

1. `classify/` — every article with the active prompt (`entity-sentiment-v6-roles`).
2. `review/<ID>/` — only articles with a blocking alert. A missing reliable alias
   (for example the Wall Street Journal for NWSA) is reviewed in `additions-only`
   mode; a forbidden alias (for example the social network X mapped to Block, XYZ)
   gets a targeted review that may remove it. An invalid or incomplete review is
   rejected and the validated first-pass result is kept.
3. `compose/` — composition with provenance and quality alerts.

Then `vote/` keeps every pair proposed by a strict majority of passes with its
majority label (a label tie becomes `neutral` and is counted), `compose/` checks the
vote, and `final/` holds `entities.csv`, `scores.csv` and their manifest.
`run_report.json` summarises passes, reviews, vote, alerts and cost;
`vote/vote_report.json` gives the votes and agreement level of every pair
(`unanimous`, `majority`, `label_tie`, `dropped_minority`).

When the validator rejects an answer, the next attempt sends the model the fixed
rejection reason (never the rejected text); attempts stay bounded by `--max-attempts`.
The run always writes the CSV files when every step succeeds; if blocking alerts
remain, its status is `completed_with_alerts` and the manifest records
`ready_for_scoring: false`. A network error, an exhausted budget or an unknown cost
stops the run (`status: failed`). `--dry-run` previews the requests without a key.

Re-read the usage of any run without the API:

```bash
.venv/bin/python -m aie2609 usage --run-dir output/run-v6-vote3   # add --json for machine output
```

## Current state

**Retained version: `output/run-v6-vote3/final/`**, copied byte for byte to
[`results/`](results/README.md), produced by `run --passes 3` with prompt
`entity-sentiment-v6-roles`.

- 100 articles; 500 canonical companies after grouping dual share classes.
- 233 article/ticker pairs: 61 `positive`, 117 `neutral`, 55 `negative`; 112 tickers
  in `scores.csv`. Status `completed`, zero blocking alerts.
- Stability: the three independent passes agree on 224 of the 239 proposed pairs
  (93.7 %); the vote keeps 9 pairs at two votes to one and drops 6 pairs proposed by
  a single pass.
- Measured accuracy on the reference [`review/reference-v1`](review/reference-v1/README.md),
  adjudicated by the coding agent with the assignment's definitions, with the user
  reviewing part of the debatable cases (it is not an independent human gold standard).
  Estimated pair accuracy: **0.933** for the retained version, 0.907 for
  `run-final-v1` (one pass, prompt v5) and 0.878 for the earlier manual composition.
  On the 20 non-debatable disputed cases: 19, 17 and 9 correct.
- Cost: 0.030 USD per article measured for one cold pass (`run-final-v1`), about
  0.045 USD per article estimated for three passes. The retained run itself cost
  2.97 USD because 65 answers were replayed from an interrupted run.
- 100 offline tests pass.
- Total API spend for the whole project, all experiments included: 14.70 USD
  (committed, conservative) out of an authorised 100 USD.

Earlier versions remain local evidence: `output/run-final-v1/` (one pass, prompt v5)
and `output/final-results-v1/` (manual composition from prompt v4, not reproducible
with the current command).

## Repository map

| Path | Content |
| --- | --- |
| `src/aie2609/` | Pipeline package (module map in `ARCHITECTURE.md`) |
| `tests/` | Offline test suite with a fake model client |
| `results/` | Submitted `entities.csv`, `scores.csv` and run reports |
| `review/reference-v1/` | Accuracy reference, per-version scores and limits |
| `docs/` | Work log, prompt design, data quality, review history |
| `AGENTS.md`, `CLAUDE.md` | Rules and context given to the coding agent |

`output/`, `.cache/` and `.env` are local and ignored by Git, as are the supplied
inputs, the assignment PDF and review files that quote article text.

## Other commands (no API)

```bash
.venv/bin/python -m aie2609 audit                          # validate both inputs
.venv/bin/python -m aie2609 prepare-reference --version A=path/classifications.json \
    --version B=other/classifications.json --spot-checks 25 --output-dir review/reference-new
.venv/bin/python -m aie2609 score-reference --dir review/reference-new
```

`prepare-reference` turns every article/ticker pair on which versions disagree into
a case to adjudicate, plus a random sample of unanimous pairs. `cases.csv` and
`GUIDE.md` do not show which version proposed what; `key.json` keeps that for
scoring. `score-reference` reports, per version, correct disputed cases, errors,
the measured accuracy of the consensus and an estimated accuracy over all pairs.

The single-step commands `classify`, `review`, `compose` and `export` remain for
diagnosis; `export` alone refuses a composition with blocking alerts.
`prepare-evaluation` and `evaluate` are the earlier two-version review tools.
Every output directory must be new; no other model is used if `gpt-5.6-terra` fails.

## Limits

- Structural validation does not prove that a sentiment is right; accuracy is
  estimated on an agent-adjudicated reference, not on the evaluators' reference.
- Pairs omitted by every version are not measured by the reference.
- The review step uses the same model as the first pass.
- The brand/subsidiary registry (`src/aie2609/entity_aliases.json`) is deliberately
  limited to relationships observed in the data.
- Results describe the supplied articles only; they are not investment advice.

## Detailed documentation

- [AGENTS.md](AGENTS.md) — working and security rules given to the agent.
- [CLAUDE.md](CLAUDE.md) — Claude Code context built on top of AGENTS.md.
- [ARCHITECTURE.md](ARCHITECTURE.md) — code versus model, modules, cost model.
- [DATA_MODEL.md](DATA_MODEL.md) — contracts and exact formula.
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — batches and status.
- [docs/PROMPT_DESIGN.md](docs/PROMPT_DESIGN.md) — prompt structure and versions.
- [docs/FULL_100_REVIEW.md](docs/FULL_100_REVIEW.md) — full runs and their analysis.
- [docs/DATA_QUALITY.md](docs/DATA_QUALITY.md) — input data quality report.
- [docs/WORK_LOG.md](docs/WORK_LOG.md) — commands, costs and decisions, in order.
