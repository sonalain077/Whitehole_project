# Submitted results

Byte-for-byte copies of the retained run `output/run-v6-vote3/` (the `output/`
folder itself is local and not versioned). Nothing here was edited by hand.

| File | Source in the run | Content |
| --- | --- | --- |
| `entities.csv` | `final/entities.csv` | `id,ticker,label`, 233 rows |
| `scores.csv` | `final/scores.csv` | `ticker,value`, 112 tickers |
| `export_manifest.json` | `final/run_manifest.json` | as-of time, half-life, counts, SHA-256 of inputs and CSVs |
| `run_report.json` | `run_report.json` | passes, targeted reviews, vote, alerts, calls, tokens, cost |
| `vote_report.json` | `vote/vote_report.json` | votes and agreement level for every pair |

Produced by `python -m aie2609 run --passes 3 --max-attempts 3 --max-cost-usd 15
--output-dir output/run-v6-vote3` on 2026-10-14 with prompt
`entity-sentiment-v6-roles`. The SHA-256 of both CSV files match
`export_manifest.json`; check them with `Get-FileHash` or `sha256sum`.

Accuracy and its limits: [`review/reference-v1/README.md`](../review/reference-v1/README.md).
