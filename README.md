# Entity-level news sentiment for the S&P 500

Reads 100 financial news articles, finds which S&P 500 companies each one mentions,
labels the implication for **each** company (`positive`, `neutral`, `negative`) and
aggregates a time-decayed score per ticker.

```text
news.json + sp500.csv  ──►  aie2609 run  ──►  entities.csv (id,ticker,label)
                                              scores.csv   (ticker,value)
```

`weight = 0.5 ** (days / 7)` with `days` measured to 2026-09-29 00:00 New York time;
`value = Σ label × weight` with labels +1 / 0 / −1.

## Run it

Python 3.12+. Put `news.json` and `sp500.csv` in the repository root (they are not
published here) and set `OPENAI_API_KEY` (environment variable or `.env`, see `.env.example`).

```bash
python -m venv .venv                      # Windows: use .venv\Scripts\python.exe below
.venv/bin/python -m pip install -r requirements.txt  # tzdata + this project
.venv/bin/python -m unittest discover -s tests       # 100 offline tests, no key needed
.venv/bin/python -m aie2609 run --max-cost-usd 10    # end to end, ~4.5 USD, ~25 min
```

While it runs, one line per article and per step shows progress (pass, article id, number of
companies, calls and cost so far; flagged articles and their review; vote; export). At the end
it prints its status, the output paths, and calls, tokens and cost per article. The CSV files
are in `output/run-<timestamp>/final/`. `aie2609 usage --run-dir <dir>` shows
the same summary later; `aie2609 run --dry-run` previews the requests without a key.

## Results (submitted in [`results/`](results/README.md))

| | |
| --- | --- |
| Pairs in `entities.csv` | 233 (61 positive, 117 neutral, 55 negative) |
| Tickers in `scores.csv` | 112 |
| Agreement of 3 independent passes | 93.7 % of pairs |
| Estimated pair accuracy | **0.933** (one pass of the previous prompt: 0.907) |
| Cost | 0.030 USD per article for one pass, ~0.045 for the delivered 3 passes |

Accuracy is measured on an agent-adjudicated reference, not on human ground truth; method
and limits in [`review/reference-v1/README.md`](review/reference-v1/README.md).

**Presentation** (approach, decisions, analysis of the results, limits):
[`docs/presentation.pdf`](docs/presentation.pdf).

## How it works

1. **Code** loads and checks both files strictly (dates, duplicates, invisible Unicode,
   share classes `GOOG → GOOGL`, …).
2. **`gpt-5.6-terra`** reads each article with the full company list and returns, per
   company, a role (subject, counterparty, rating issuer, source, comparison…), a label and
   an exact quote. The JSON schema makes roles such as "bank issuing the rating" neutral.
3. **Code** validates every answer, flags likely omissions or false matches, and sends only
   those articles back to the model for a constrained review.
4. This runs **three times independently**; code keeps the majority answer per pair and
   computes the scores.

Diagrams of the pipeline and of how the project was built with two coding agents:
[`ARCHITECTURE.md`](ARCHITECTURE.md).

## Repository map

| Path | What it is |
| --- | --- |
| `src/aie2609/` | The pipeline (one module per responsibility, see ARCHITECTURE) |
| `tests/` | Offline tests with a fake model client |
| `results/` | Submitted CSV files and run reports |
| `review/reference-v1/` | Accuracy measurement of every version |
| `AGENTS.md`, `CLAUDE.md` | Rules and context given to the coding agents (Codex, then Claude Code) |
| `ARCHITECTURE.md`, `DATA_MODEL.md`, `IMPLEMENTATION_PLAN.md` | Design, contracts, plan |
| `docs/` | Presentation (PDF), work log, prompt design, data quality, earlier reviews |

## Limits

- Accuracy is estimated, not certified; companies missed by every version are not measured.
- Results describe these 100 articles only and are not investment advice.
