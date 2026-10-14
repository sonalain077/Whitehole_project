# Test strategy

The `unittest` suite makes no network call: the model is replaced by a fake client
returning prepared Responses payloads. Tests that read the supplied `news.json` and
`sp500.csv` are skipped (and reported as skipped) when those files are absent, as in a
fresh clone of the public repository.

| Area | Behaviours covered |
| --- | --- |
| Inputs | Invalid JSON/CSV, duplicate keys and ids, missing fields, U+200B, canonical share classes, invalid/ambiguous/nonexistent dates, future article |
| Model answers | Strict schema, tickers outside the universe, labels, roles and the neutral-only roles, exact evidence, duplicates, refusals and incomplete answers, prompt examples |
| Runner | Bounded retries with validator feedback, cache replay and tamper detection, budget before sending, unknown cost after a network error, rate-limit retry, cache replicas |
| Review and composition | Lexical hints, additions-only enforcement, change reports, forbidden aliases, candidate comparison |
| Scoring and export | Weights at 0/7/14 days, fraction of a day, daylight-saving change, cancellation, zero neutral score, sorting, hashes, exact CSV contract |
| End-to-end run | Single pass without review, missing mention fixed by an additions-only review, rejected review exported with alerts, three passes with vote, existing output refused |
| Usage and reference | Usage summary and `usage` command, blind reference cases, per-version scoring, invalid decisions reported with their case |

Command:

```bash
.venv/bin/python -m unittest discover -s tests -v     # Windows: .venv\Scripts\python.exe
```

A command that discovers zero tests does not validate the pipeline. Any future API
integration test must be explicitly enabled and bound to the user's budget.
