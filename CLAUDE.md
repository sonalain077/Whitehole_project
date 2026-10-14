# CLAUDE.md

@AGENTS.md

## Role of Claude Code in this project

Codex built the pipeline under `AGENTS.md` (12–13 October). Claude Code took over on
14 October with a **fresh context**, deliberately not the agent that wrote the code, to act
as a second opinion:

1. **Reviewer of Codex's work** — audit the repository against the PDF before changing
   anything: can the evaluators run it? Are the submitted CSV files reproducible?
2. **Builder of the fixes** found by that audit, following the same rules and batch loop.
3. **Second-model judge** of `gpt-5.6-terra`'s outputs — adjudicate disagreements between
   versions in `review/reference-v1/`, always labelled as agent decisions, never as human
   ground truth.

Claude does not replace the pipeline model: every classification still comes from
`gpt-5.6-terra`. Decisions on budget, publication and the delivered version stay with the user.

## Read on demand

| Need | Source |
| --- | --- |
| Business requirements | `AIE2609_Project.pdf` (local) |
| How to run, current results | `README.md` |
| Pipeline and build workflow diagrams, code vs model | `ARCHITECTURE.md` |
| Contracts and formula | `DATA_MODEL.md` |
| What was tried and why | last entries of `docs/WORK_LOG.md` (not the whole file) |
| Usage of a run | `python -m aie2609 usage --run-dir output/<run>` |
| Measured accuracy | `review/reference-v1/README.md` |

## Environment (Windows, PowerShell 5.1)

- Python: `.\.venv\Scripts\python.exe` (3.12); no `python` on PATH.
- Git: `.\.tools\mingit\cmd\git.exe -c safe.directory=<repo path, forward slashes> ...`,
  because `.git` belongs to the Windows account used by Codex. Never change the global config.
- The supplied inputs, the PDF and `.env` are local only; the public repository excludes them.

## Commands

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests              # offline, must stay green
.\.venv\Scripts\python.exe -m aie2609 run --max-cost-usd <USD>        # PAID: 3 passes + vote (~4.5 USD)
.\.venv\Scripts\python.exe -m aie2609 run --passes 1 --max-cost-usd <USD>   # PAID: one pass (~3 USD)
.\.venv\Scripts\python.exe -m aie2609 usage --run-dir output/<run>    # calls, tokens, cost
.\.venv\Scripts\python.exe -m aie2609 score-reference --dir review/reference-v1
```

Never quote an accuracy figure that `score-reference` did not produce.

## Traps already paid for

- The cache key hashes the whole request (prompt, schema, universe, `max_output_tokens`,
  replica): any prompt edit means a new paid run, and `run` would no longer reproduce
  `results/`. Bump `PROMPT_VERSION` with every prompt change.
- A new prompt fixes some cases and breaks others (v4 → v5: 39 changed pairs). Compare
  versions pair by pair before retaining one.
- Valid JSON can still be wrong: rating banks labelled negative, the social network X mapped
  to Block, SpaceX to Exxon. Fix the class of error in code or `entity_aliases.json`.
- One article (N064) paraphrased its evidence and stopped a run; retries now carry the
  validator's reason. Use `--max-attempts 3` for full runs.
- 86 % of a cold pass's cost is provider cache writes of the ~14k-token prefix.

## Definition of done

Offline tests green with a new test for new behaviour; for paid runs, `usage` totals, status,
blocking alerts and a diff against `results/`; `README.md`, `IMPLEMENTATION_PLAN.md` and a
dated `docs/WORK_LOG.md` entry updated with the commands actually run.
