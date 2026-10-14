# Implementation plan

Goal: deliver a simple, reproducible and explained solution within the 4 to 6 hour
envelope given by the assignment. Durations are indicative, excluding waiting for
access, installation and API latency. One active batch at a time.

| Batch | Scope | Exit criterion | Estimate | Status |
| --- | --- | --- | --- | --- |
| 0 | Read the assignment, inspect inputs, draft the five required documents and the skeleton | Contracts traced, risks identified, sources intact | 25 min | Done |
| 1 | Environment, CLI, strict loading, Unicode, dates, canonical universe, audit without API | Input and time-zone tests pass; audit command on the real files | 45 min | Done |
| 2 | Client for the mandatory model, versioned prompt, schema, validation, cache, budget and metrics | Offline simulated tests; explicit errors; small bounded real trial if access available | 70 min | Done; omissions documented for review |
| 3 | Controlled composition, aggregation, stable exports and run manifest | Arithmetic tests and simulated integration pass; no partial final output | 40 min | Done |
| 4 | Full run, review, error analysis and targeted correction | 100 articles processed; outputs validated; calls, tokens and cost per article measured | 55 min | Done |
| 5 | End-to-end command, reliability measurement, choice of the delivered version | One command produces the CSV files; accuracy measured per version | — | Done: `output/run-v6-vote3/final/` (prompt v6 with roles, 3 passes + vote, estimated accuracy 0.933 on `review/reference-v1`) |
| 6 | Results analysis, presentation and submission | Clean-clone check, deliverables and limits reviewed | 35 min | Repository published and checked from a clean clone; presentation to do |

Indicative total for batches 0 to 4 and 6: 4 h 30. Batch 5 went beyond the core
envelope at the user's request (best result and measured reliability). Keep a margin
for anomalies and API access.

## Batch 1 — first code iteration

1. Make Python and Git available; create the venv, initialise Git locally, check the
   exclusions. No remote or implicit push.
2. Install only the retained dependencies; produce a lock file and record the versions
   actually tested, including time-zone data on Windows.
3. Implement `python -m aie2609 --help` and an offline audit mode.
4. Load both formats with contextual errors, preserve the sources, normalise only the
   copies and canonicalise share classes.
5. Test invalid data, duplicates, U+200B, time zones and order invariance.

Expected evidence: command, real audit summary and passing tests in the log.

## Batch 2 — extraction and classification

Process the whole article with the complete reference list of canonical names and
tickers from the start. Avoid a lexical prefilter that could lose brands and
subsidiaries. Let the model identify the companies and their implication, with an
internal textual evidence. Code then validates structure and constraints.

Write simulated answers for: a model that invents a ticker, unknown label, broken JSON,
duplicates, missing evidence, network interruption and budget overrun. Prepare a small
human review set covering several company roles. Document the limits of brand/parent
links that the reference file alone cannot certify. No invented accuracy benchmark
without annotations.

Prerequisites for the real test: key available locally, access to `gpt-5.6-terra`,
price checked and budget chosen. Never switch model to work around missing access.

Status on 12 October: `classify` command, preview, validated cache, durable reports and
simulated tests available. Prices and the Responses contract checked in the official
documentation. User budget: 5 USD maximum for the first trial, retries included. Key
absent from the process and from the inspected Windows user/machine variables: no real
call. The [review set](docs/REVIEW_SET.md) is selected, with no reference annotations
and no accuracy measurement.

Addition on 13 October: at the user's request, automatic loading of the key from a
local `.env` ignored by Git, without a new dependency. Model and budget unchanged;
configuration tests and the offline suite pass.

Trial on 13 October: access confirmed, three articles processed per variant. Retained
version `entity-sentiment-v2`, result `output/pilot-003`. Goldman Sachs is recovered in
N002; Alphabet via Waymo is still missing in N027. A v3 variant with more explicit
parent mapping and medium reasoning did not improve the result; back to v2, with no
editing of outputs. Known cumulative cost 0.2368426 USD; unknown reservation 0.173757
USD; conservative balance 4.5894004 USD. Details of every attempt in the log.

Redesign requested by the user: RCORCF prompt v4, ten synthetic examples and version
documentation. Offline validation only: 62 tests pass; no new spend. The v2 result
remains the API comparison point, without claiming to measure v4.

RCORCF retest requested and run: `output/pilot-005`, three validated answers, nine
article/ticker pairs. GS stays neutral and GOOGL via Waymo is now present as neutral;
no other label or coverage change compared with v2. Retest cost 0.0888659 USD;
conservative balance 4.5005345 USD. These are known development cases, not an
independent quality measurement.

Next test requested: ten distinct articles, expectations recorded before the calls in
`docs/REVIEW_10.md`. Run completed after one technical retry: 28 pairs, omissions
JPM/N070 and NWSA/N077, disagreement NFLX/N077. Prompt v4 frozen. Test cost 0.2791525
USD; 63 tests pass after adding the validation reason to diagnostics.

Extension requested and run: advisory lexical check and `review` command, review prompt
`entity-review-v1`. 71 offline tests pass. Run `output/verification-010`: ten calls,
0.2744812 USD; NWSA/N077 added, P/N084 regressively removed, JPM/N070 still missing.
Both results stay separate: no net gain shown and no automatic promotion.

Next targeted correction done: registry `entity-aliases-v1`, coverage
`entity-coverage-v2` and prompt `entity-review-v2-targeted`. The command selects
reliable omissions and ambiguous mentions by default, with `--all` for the general
mode. On N070/N077/N084: JPM and NWSA added, P kept, no NDAQ; NFLX stays negative.
Three calls, 0.0927612 USD. 74 tests pass. The mechanism improves coverage of this
sample at low cost, without being a generalisable measurement.

Full test requested next: 100 articles completed in `output/full-100-v4`, 87 calls and
13 cache replays, cost 2.2450432 USD. The first alert analysis showed 37 false signals
caused by common words or acronyms; `entity-coverage-v3` and `entity-aliases-v2` remove
them and leave eight plausible cases. Their review costs 0.2281222 USD and adds eight
neutral pairs with no removal or label change. 75 tests pass.

Before composition, prompt v5 adds a rule and two synthetic examples for incidental
market comparisons and asymmetric agreements; registry v3 adds CNN → WBD. The full v5
pass produces 220 pairs and fixes the targeted cases, but introduces omissions and two
false XYZ. Batch 3 therefore composes validated proposals and keeps alerts, without
automatically promoting the latest pass.

Deterministic composition implemented with provenance, hashes, review validation and
optional comparison with a candidate. Registry `entity-aliases-v5` adds CNBC, CBS News,
Barron's and Kenworth, and forbids `X → XYZ` and `SpaceX → XOM`. On the 100 articles,
the v4 + eight reviews composition has 225 pairs but is blocked by seven alerts; v5 has
fifteen blocking alerts and 29 disagreements.

The six affected articles were then reviewed in bounded groups. The `additions-only`
mode makes the validator reject any removal or label change; it prevented the
regressive removal of SCHW/N066. The final v2 composition has 230 pairs, zero blocking
alerts and `ready_for_scoring=true`.

Scoring and export done with `time-decay-v1`: `output/final-results-v1/` has 230
entities and 111 tickers. Tests cover 0/7/14 days, fraction of a day, daylight-saving
change, cancellation, zero neutral score, future date, sorting, hashes and the CSV
contract.

## Batch 3 — scoring and output contract

Test the weights at 0, 7 and 14 days, a fraction of a day and a daylight-saving change.
Check a negative score, cancellation, a neutral-only company and one row per canonical
pair. Sort the exports. A run succeeds only when every article has a validated result,
including a justified empty list.

## Batch 5 — end-to-end command and measured choice

- `run` chains classification, targeted reviews, composition and export; `run_report`
  and `usage` report calls, tokens and cost per article (one cold pass: 0.030 USD).
- Prompt v6 adds a role per company and a two-branch schema that forces `neutral` for
  the roles the assignment defines as neutral; rejected answers are retried with the
  validator's reason.
- `--passes 3` runs independent passes and keeps the majority; passes agree on 93.7 %
  of pairs.
- `prepare-reference` / `score-reference` measure every candidate version on all their
  disagreements plus spot checks of the consensus. Retained: three passes with vote
  (0.933), ahead of one v6 pass (0.920–0.924), `run-final-v1` (0.907) and the manual
  composition (0.878).

## Batch 6 — results and submission

- Explain the salient tickers with their articles and weighted contributions, coverage
  concentration and confidence limits.
- Every correction triggers a regeneration; never edit the CSV files.
- Rehearse the command from a clean clone (done: 92 tests pass, 8 skipped without the
  supplied data).
- Check confidentiality, absence of secrets and presence of every deliverable (done
  before publication).

## Decisions and open points

| Point | Current position | When resolved |
| --- | --- | --- |
| Python / Git missing from the terminal | Local runtimes checked in the ignored `.tools` folder; reproducible `.venv` | Batch 1 |
| Access and price of the mandatory model | Prices checked on 12 October; Responses access confirmed on 13 October | Batch 2 |
| User budget | 100 USD authorised on 14 October; 14.1736621 USD known + 0.529338 USD reserved for unknown attempts; conservative commitment 14.7030001 USD | Tracked in reports and the log |
| Time zone and "CET" deadline | New York inputs certain; submission on 14 October, 18:00 Paris time | Before submission |
| Subsidiaries not described by the CSV | Traceable model inference + review + versioned registry; no external source | Batches 2, 4 and 5 |
| Model stability | Cache and contracts stable; no promise of API determinism; three-pass vote measured | Batches 2, 4 and 5 |
| Publication | Public repository without the supplied data, the PDF or files quoting articles | Batch 6 |
