# Data contracts

Output and scoring requirements come from the assignment, page 4; the error
policies below are our choices.

## Inputs

`news.json`: array of objects with `id`, `date`, `headline`, `body`, all non-empty
strings. `id` must be unique; `date` follows exactly `YYYY-MM-DDTHH:MM` in New York
local time. The supplied file has 100 articles; the loader is generic and does not
hard-code that number.

`sp500.csv`: columns `symbol,security,gics_sector,headquarters,date_added`. Ticker and
name are required for classification; the other columns are metadata. No ticker may
be inferred from real-world S&P 500 membership: the supplied file defines the
universe. It has 503 rows.

Policies: UTF-8 (leading BOM tolerated); reject missing required fields, wrong
types, duplicate JSON keys, duplicate CSV columns, malformed rows, duplicate symbols
and duplicate article ids. Extra fields are reported and explicitly ignored. Empty
inputs and any date error are rejected before any token is spent.

## Normalisation and identity

- Keep the sources; keep raw and normalised text separately in memory.
- Normalise to Unicode NFC and line endings to LF; remove U+200B found in names or
  tickers and record the anomaly. Do not strip every Unicode format character and do
  not transliterate names.
- Strip surrounding spaces of structural fields; never remove punctuation from text or
  from tickers such as `BRK.B`.
- Detect and report repeated content. Distinct ids remain distinct articles for
  aggregation; never merge them silently.
- Apply `GOOG → GOOGL`, `FOX → FOXA`, `NWS → NWSA`; `BRK.B` is the designated class.
  A class alias never authorises an output outside the universe.
- A canonical company has one row per article. Duplicate classifications are errors,
  especially when their labels differ.

## Dates and aggregation

Dates are interpreted in `America/New_York`. Ambiguous or nonexistent local times are
rejected rather than silently given an offset. `tzdata` provides the zone on Windows.
Instants are converted to UTC before subtraction to measure real elapsed time,
including across daylight-saving changes.

```text
as_of = 2026-09-29 00:00 America/New_York
days = (as_of_utc - article_date_utc).total_seconds() / 86400
weight = 0.5 ** (days / 7)
label_value = {positive: +1, neutral: 0, negative: -1}
value(ticker) = sum(label_value × weight)
```

Choice: an article later than `as_of` is rejected with an explicit error rather than
having its age truncated to zero. No averaging, normalisation by article count or extra
weighting. Intermediate contributions are not rounded. Stable summation with
`math.fsum`; decimal serialisation precise enough to rebuild the float, never
`NaN`/infinity and no negative zero.

## Model answer

A strict object containing a list `entities`. Each item: `ticker`, `role`, `label` and
`evidence` (a short exact excerpt of the normalised headline or body). The article id
comes from the code, not the model. An empty list is allowed when no company of the
universe is identified; it still appears as a processed article. All fields are
validated and unexpected fields are rejected.

| Field | Values |
| --- | --- |
| `ticker` | canonical ticker of the supplied universe (enforced by the schema) |
| `role` | `subject`, `counterparty`, `affected_peer` (any label); `rating_issuer`, `source`, `comparison`, `other_mention` (always `neutral`) |
| `label` | `positive`, `neutral`, `negative` |
| `evidence` | 1 to 500 characters, an exact substring of the headline or the body |

The schema has two `anyOf` branches so that an always-neutral role cannot be generated
with a directional label; the validator checks the same rule, including on cached
answers. A duplicate canonical company is rejected. Entities are sorted by ticker.
Incomplete answers and refusals are errors. Answers produced before prompt v6 have no
`role` and remain readable; live answers must have one. The evidence and the role stay
internal; the submitted CSV files gain no column. The structural validator does not
detect omissions; that is the job of the coverage checks and the reference.

## Classification run artifacts

- `classifications.json`: `schema_version: 1`, array `articles`, each with `id` and
  `entities`; an empty list is kept. Written only after the whole selection is valid.
- `usage.json`: `schema_version: 1`, prices and their check date, call and local cache
  counters, known tokens, known and unknown costs, budget, and the detail of every
  attempt. USD amounts are decimal strings or `null`. The uncached cost per article is
  computed only for a selection fully processed without local cache or unknown cost.
- `run_manifest.json`: `schema_version: 1`, status `running`, `completed` or `failed`,
  model, prompt version, replica, SHA-256 of the sources, selected ids and a preview of
  reservations and cache keys.

The manifest is authoritative for success. Writes go to a temporary file followed by
an atomic replace. A hard stop may leave `running` and an `in_flight` attempt: that is
not a complete result. Run directories must be new and separate from cache and inputs.

## Targeted review

`review` reads an initial `classifications.json`, strictly validated against the
current articles and universe, and writes the same classification schema into a new
directory plus `review_changes.json` (`schema_version: 2`): for each id the coverage
hints, review reasons, `missing_before`, `unresolved_hints_after`, `added`, `removed`
and `label_changes`. Several `candidate_tickers` in a hint mean an ambiguity to
resolve, not several additions. In `additions-only` mode the validator rejects any
removal or label change, including from the cache.

## Composition

`compose` reads a complete baseline, zero or more completed review directories and
optionally a complete candidate. A review is applied only if its manifest references
the baseline hash, its ids match `review_changes.json`, its declared changes match the
classifications exactly and no reliable hint remains unresolved; two reviews cannot
replace the same article. Output: `classifications.json` and `composition_report.json`
(version, hashes, provenance per article, blocking and advisory alerts, differences
with the candidate). Omissions of a reliable alias and forbidden aliases are blocking;
missing anchors, ambiguity and a possible analyst role transfer are advisory.
`ready_for_scoring` is true only without blocking alerts and, when a candidate is
given, without disagreement with it.

## End-to-end run (`run`)

`output/run-<timestamp>/` contains, for each pass `pass-N/` (or directly at the root
with `--passes 1`), `classify/`, `review/<ID>/` and `compose/`; then `vote/`
(`classifications.json` and `vote_report.json`), `compose/` (check of the vote),
`final/` and `run_report.json`.

- `vote_report.json`: `schema_version: 1`, `vote_version`, number of passes, counts
  (`unanimous`, `majority`, `label_tie`, `dropped_minority`) and, for each proposed
  pair, its votes per pass, final label (or `absent`) and agreement level.
- `run_report.json`: pipeline and prompt versions, budget, per-pass classification
  usage, reviews (mode, blocking alerts before, status, cost), vote counts,
  composition counts, output paths and the usage summary (calls, retries, tokens and
  cost per category, per step and per article). Status `completed`,
  `completed_with_alerts` or `failed` with the failing step.

## Submitted exports

| File | Exact columns | Constraints |
| --- | --- | --- |
| `entities.csv` | `id,ticker,label` | One row per canonical article/company pair; existing id; allowed ticker; label `positive`, `neutral` or `negative` |
| `scores.csv` | `ticker,value` | One row for every ticker present in `entities.csv`, including zero scores |

UTF-8 with a header, no added index, written with the `csv` module. Order: `(id,
ticker)` for entities, `ticker` for scores. A valid run with no entity produces two
header-only files, never confused with an error. `export` requires a composition with
`ready_for_scoring=true` whose `classifications.json` hash matches; `run` may export a
composition with alerts and then records `ready_for_scoring: false`. The export
manifest records reference time, time zone, half-life, counts and the SHA-256 of
sources and both CSV files.

## Accuracy reference

`prepare-reference` writes `cases.csv` (`case,id,ticker,company,human_decision,
human_notes`), `GUIDE.md` (article text and excerpts, without version labels),
`key.json` (labels of every version per case, kind `disputed` or `spot_check`) and
`manifest.json`. Decisions: `positive`, `neutral`, `negative`, `absent`, `uncertain`
or empty. `score-reference` ignores empty and uncertain decisions, reports any invalid
value with its case id, and estimates each version's accuracy by scoring unanimous
pairs at the measured consensus accuracy. It never modifies a classification.
