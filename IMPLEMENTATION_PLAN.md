# Implementation plan

Delivered in small batches, one at a time, each closed by offline tests and a dated entry in
[`docs/WORK_LOG.md`](docs/WORK_LOG.md) (commands run, results, cost, limits).

| Batch | Agent | Scope | Exit criterion | Status |
| --- | --- | --- | --- | --- |
| 0 | Codex | Read the PDF, inspect inputs, draft the required documents | Contracts written, risks listed, inputs untouched | Done |
| 1 | Codex | CLI, strict loading, Unicode, New York time, share classes, offline audit | Input and time-zone tests pass; audit on the real files | Done |
| 2 | Codex | Model client, versioned prompt, strict schema, validation, cache, budget, metrics | Simulated tests offline; small paid pilot validated | Done |
| 3 | Codex | Targeted review, composition, time-decay scoring, CSV export | Scoring tests (0/7/14 days, DST…) pass; first CSV files | Done |
| 4 | Codex | Full 100-article runs (prompts v4, v5), error analysis | Calls, tokens and cost measured | Done |
| 5 | Claude Code | Audit, one-command `run`, usage report, prompt v6 with roles, 3-pass vote | Evaluators can run it; CSV reproducible from the code | Done |
| 6 | Claude Code | Accuracy reference, choice of the delivered version, publication | Every version scored; clean-clone check | Done (0.933 retained) |
| 7 | User | Presentation of approach, results and limits | — | To do |

Batches 0–4 fit the 4–6 hour envelope of the assignment; batches 5–6 went beyond it at the
user's request, to obtain a reproducible command and a measured result.

## Decisions

| Question | Decision | Why |
| --- | --- | --- |
| Prefilter the company list? | No, send the full universe | A prefilter loses brands and subsidiaries |
| Who decides the label? | The model, inside a schema that forces neutral roles | Reading comprehension is needed; the PDF fixes what is neutral |
| Invalid model answer | Retry with the validator's reason, bounded; never `neutral` | Errors must stay visible |
| Missing source or false match | Lexical alert → constrained review, never an automatic edit | Code is reliable at detection, not at judgement |
| One pass or three? | Three passes + majority vote | Measured 0.933 vs 0.920–0.924 for one v6 pass, for ~1.5× the cost |
| Which output to deliver? | The best version on the blind reference | Chosen by measurement, not by preference |
| Publication | Public repository without the supplied data or the PDF | Confidential material |

## Budget

The user authorised 5 USD for the first trials, then 10 USD, then up to 100 USD on
14 October. Total spent on the whole project, every experiment included: 14.70 USD
(conservative, counting interrupted calls whose cost is unknown).
