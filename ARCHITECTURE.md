# Architecture

Requirements come from the assignment (pages 2 to 5). Choices: a sequential
command-line pipeline, local files, one runtime dependency (`tzdata`), no web
interface or long-running service. History of how each part was reached is in
[`docs/WORK_LOG.md`](docs/WORK_LOG.md).

## Flow

```text
news.json + sp500.csv → strict loading / normalisation → canonical universe
   → per pass: classify every article → validate → targeted review of alerted
     articles → deterministic composition with quality alerts
   → majority vote over passes → composition check → time-decay scoring
   → entities.csv + scores.csv + manifests + usage report
                       ↕
        local cache of validated answers (one replica per pass)
```

## What the code does, what the model does, and why

| Step | Owner | Why |
| --- | --- | --- |
| Reading, input schemas, Unicode, dates | Code | Deterministic, testable rules |
| Allowed universe and dual share classes | Code | Prevents invented tickers and double counting |
| Finding the companies an article mentions, brands/subsidiaries to parent, role of each company (subject versus mention), label per company | `gpt-5.6-terra` | Needs reading comprehension of the article in context |
| Neutral label for roles the assignment defines as neutral | Code (JSON schema) and model | The schema makes a directional label impossible for those roles |
| Schema, tickers, labels, roles, exact evidence, duplicates | Code | A model answer is not trusted data |
| Detecting likely omissions and forbidden aliases (`entity_aliases.json`) | Code | Lexical checks are cheap and reproducible; they only trigger a review |
| Reviewing an alerted article | Model, constrained by code | Code rejects removals or label changes in `additions-only` mode |
| Combining passes (majority vote), weighting, summing, sorting, writing | Code | Fixed formula; reproducible arithmetic |
| Measuring accuracy | Human/agent adjudication, scored by code | Structure does not prove semantic correctness |

The model never computes the score, never sees other articles and has no tools.

## Modules (`src/aie2609/`)

- `cli.py` — subcommands; data errors map to exit code 2.
- `ingestion.py`, `normalization.py`, `dates.py`, `audit.py` — strict loading of both
  inputs (duplicate keys and ids, missing fields, malformed rows), NFC and U+200B
  removal on an in-memory copy, New York times with ambiguous or nonexistent local
  times rejected, read-only audit report.
- `classification.py` — prompt (`SYSTEM_PROMPT`, `PROMPT_VERSION`), strict JSON schema
  and `validate_entities`.
- `llm.py` — HTTPS Responses client on the standard library (`urllib`): fixed OpenAI
  endpoint, redirects refused, response size capped, no fallback model.
- `runner.py` — `Classifier`: cache, bounded attempts with validator feedback, budget
  reservation, durable checkpoints, manifest.
- `review.py` — lexical coverage hints and `ReviewClassifier` (second pass on
  alerted articles, same model, `additions-only` mode enforced by code).
- `composition.py` — applies validated review overlays, keeps provenance, raises
  blocking and advisory alerts.
- `pipeline.py` — the `run` command: passes, reviews, composition, `majority_vote`,
  export, run report.
- `scoring.py` — time-decay formula and CSV export with manifest.
- `usage.py` — prices, token accounting, budget, usage summary.
- `reference.py` — blind adjudication cases and per-version accuracy;
  `evaluation.py` — earlier two-version review sample.
- `entity_aliases.json` — versioned configuration: brands, publications,
  subsidiaries, ambiguous names and forbidden associations observed in the data.

## Model strategy

One complete article per request, together with the full canonical universe (no
lexical prefilter, which could lose brands and subsidiaries). Responses API with a
strict JSON-schema `text.format`, `reasoning.effort=low`, `store=false`,
`service_tier=default` and at most 4,096 output tokens. Instructions and data are in
separate messages; article text is treated as untrusted data.

Prompt `entity-sentiment-v6-roles` (details in
[`docs/PROMPT_DESIGN.md`](docs/PROMPT_DESIGN.md)) asks first for the role of every
company: `subject`, `counterparty` and `affected_peer` may carry any label;
`rating_issuer`, `source`, `comparison` and `other_mention` are always neutral, as the
assignment defines neutral ("the bank issuing the rating, a media source, a customer,
a location, a size comparison"). The schema has two `anyOf` branches, so the decoder
cannot pair those roles with a directional label, and the validator checks it again.
Thirteen synthetic examples are checked by the tests. Each entity carries an exact
evidence excerpt; this improves traceability but proves neither the right parent nor
completeness.

## Reliability mechanisms

- **Validation**: unknown keys, tickers outside the universe, invalid labels or roles,
  duplicates, evidence that is not an exact excerpt, incomplete or refused responses
  are all errors; nothing is converted to `neutral`.
- **Validator feedback**: a rejected answer is retried with the fixed rejection reason
  (never the rejected text). Attempts are bounded (3 by default in `run`) and billed.
- **Coverage checks**: a reliable alias missing from the answer (for example the Wall
  Street Journal → NWSA) triggers an `additions-only` review; a forbidden association
  (social network X → Block, SpaceX → Exxon) triggers a targeted review that may
  remove it. Hints never add an entity or a label by themselves.
- **Independent passes and vote**: with `--passes 3` each pass uses its own cache
  replica (`replica` enters the cache key; replica 0 shares the ordinary cache).
  `majority_vote` keeps pairs proposed by a strict majority with their majority label;
  a label tie becomes `neutral` and is counted. This trades about 1.5 times the cost
  for less sampling variance and a per-pair agreement level.
- **Fail closed**: an unresolved blocking alert is exported only by `run`, with status
  `completed_with_alerts` and `ready_for_scoring: false`; `export` alone refuses it.
  A transport error, an exhausted budget or an unknown cost stops the run.

## Reproducibility and errors

The SHA-256 cache key covers normalised content, date, canonical universe,
normalisation version, prompt, schema, model, parameters and replica. The article id
is excluded: two ids with identical content and date may share an analysis while
remaining two articles for scoring. A cached answer is validated again on replay; a
corrupted cache entry stops the run. Outputs are sorted and sums use `math.fsum`. A new
API call may vary; the cache replays a validated result exactly.

A 429 error explicitly coded `rate_limit_exceeded` allows a bounded wait and retry
without releasing the reserved cost. A network interruption, a key or quota error or
unverifiable consumption stops the run; there is no implicit transport retry.
Validation errors are recorded as fixed reasons in `validation_error`, never with the
rejected content. Final exports are written only after complete processing.

## Usage and cost

Every attempt records article, status, model, response id, input tokens, provider
cache reads and writes, output tokens (reasoning included) and duration. API usage is
authoritative; missing values stay unknown, never zero. Prices for the standard tier
and short context, checked on 2026-10-12: input 2 USD per million tokens, cache read
0.20, cache write 2.50, output 12
([model page](https://developers.openai.com/api/docs/models/gpt-5.6-terra),
[prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)).

```text
cost = ((input - cache_read - cache_write) × input_price
        + cache_read × cache_read_price
        + cache_write × cache_write_price
        + output × output_price) / 1_000_000
```

Cost per article of a full run = total cost of its attempts / number of articles.
`run_report.json` and `aie2609 usage` report calls, retries, local cache replays,
tokens and cost per category, per step and per article, and warn when replays make
the figure lower than a cold run. Measured: one cold pass costs 0.030 USD per article
(`run-final-v1`: 3.02 USD, 86 % of it provider cache writes, because each request
repeats a ~14,000-token prefix of instructions, universe and schema). Passes 2 and 3
read that prefix from the provider cache and cost about 0.006 USD per article, so
three passes cost about 0.045 USD per article. The main lever for further savings is
reusing that cached prefix, for example by running passes or batches back to back.

Before each call a conservative reservation (UTF-8 bytes of the request plus 4,096,
plus the maximum output) is checked against the budget and written before sending; it
is replaced by the measured cost afterwards. Requests above 200,000 estimated tokens
are refused. After an interruption the reservation remains and `total_cost_usd` is
`null`, distinct from zero dollars. This local control is not a provider-side ceiling;
the key's own spend cap is an additional protection.

## Security and proportion

The key comes from `OPENAI_API_KEY` or a local `.env` loaded only by paid commands; an
existing non-empty variable wins; the loader reads that single key, does no parent
directory search, interpolation or execution, and never prints it. Caches, run
outputs and `.env` are ignored by Git. No telemetry and no network access other than
the required API during an authorised run. Input files are never written; output
paths that would overwrite an input or the cache are refused. Tests use simulated
responses and make no network call.
