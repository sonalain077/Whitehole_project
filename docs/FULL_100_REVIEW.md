# Full runs on the 100 articles

This document records the successive full runs and why each result was or was not
retained. The retained version and its measurement are summarised at the end; the
command-by-command trace is in [WORK_LOG.md](WORK_LOG.md).

## First full pass — prompt v4 (13 October)

Run requested before aggregation. Unchanged sources: `news.json` and `sp500.csv`.
Model `gpt-5.6-terra`, prompt `entity-sentiment-v4-rcorcf`, low effort, structured output
and the usual validation. Budget available at the start: 3.8541396 USD, after keeping
the earlier unknown reservation.

The first pass is in `output/full-100-v4`, with all 100 articles. The targeted review is
in `output/full-100-targeted-review` and contains only the eight flagged articles. No
manual merge or correction of classifications was made.

- 100 articles completed, 87 calls and 13 results reused from a compatible cache.
- No retry, no unknown cost in this run.
- 217 article/ticker pairs: 70 positive, 93 neutral and 54 negative.
- 11 articles with a validated empty list.
- 1,186,925 input tokens, of which 401,276 provider cache reads and 785,388 provider
  cache writes; 16,733 output tokens.
- Run cost: **2.2450432 USD**. It does not include the original cost of the 13 locally
  reused results, already counted in earlier trials.

### Adjusting the deterministic check

The first measurement produced 45 alerts. Most were false: the ordinary words
`target`, `block` and `southern`, the person's name Rollins, and the parenthesised
acronyms `(MA)` and `(CMS)` were confused with companies or tickers.

The fix `entity-coverage-v3` with registry `entity-aliases-v2`:

- excludes ambiguous short forms while keeping full legal names and explicitly tagged
  tickers;
- no longer treats every upper-case parenthesis as a ticker;
- keeps certain aliases and the Everpure ambiguity without automatic addition.

After the fix, only eight articles are flagged: N012, N013, N038, N070, N076, N077,
N084 and N091. The 75 offline tests pass.

### Targeted review

Eight calls, no retry or local cache, **0.2281222 USD**. 115,346 input tokens, of which
34,916 cache reads and 80,406 cache writes; 1,673 output.

| Article | Proposed additions | Reason |
| --- | --- | --- |
| N012 | STT neutral | SPDR brand |
| N013 | NWSA neutral; WBD neutral | Wall Street Journal; CNN found by the review |
| N038 | SBUX neutral | Starbucks as an incidental location |
| N070 | JPM neutral | Name of the JP Morgan conference |
| N076 | BLK neutral | iShares brand |
| N077 | NWSA neutral | Wall Street Journal |
| N084 | none | P, PNR and CMG already correctly distinguished |
| N091 | IVZ neutral | Invesco QQQ Trust |

No removal and no label change. If the eight proposals replaced their eight initial
rows, the result would have 225 pairs: 70 positive, 101 neutral and 54 negative.

The success of structural validation does not prove the semantic correctness of the
100 articles. The review uses the same model, so it is not independent ground truth.
Additional cost of this test: **2.4731654 USD**.

## Prompt v5 pass

Prompt `entity-sentiment-v5-rcorcf` adds a rule and two synthetic examples to separate
central news from historical performance or a small peer move cited as a comparison,
and handles separately the effects of an agreement for each party. Registry
`entity-aliases-v3` adds CNN → WBD.

The coherent full result is in `output/full-100-v5-final`: 100 articles, 220 pairs
(62 positive, 105 neutral, 53 negative), 11 empty articles. Compared with the v4
composition plus targeted review, 29 articles change: seven pairs added, twelve
removed and 23 label changes. The intended fixes are obtained (NVDA/N069,
GOOGL-NFLX-RDDT/N091 and AAPL/N095 become neutral), but the pass is not better overall:
it drops neutral sources, brands or subsidiaries (STT, NWSA, WBD, SBUX, BLK in eight
articles, PCAR/N078, CMCSA/N082), adds two false `XYZ` in N023 and N100 by confusing the
social network X with Block, labels BAC/N092 negative for publishing a downgrade of Nike
(against the analyst-bank rule), and labels NVDA/N076 positive from old results despite
the central unfavourable insider-selling topic. Known cost of the v5 runs:
**2.6571634 USD**.

Conclusion at that time: keep the v5 rule, but do not promote its raw JSON.

## Composition and deterministic safeguards

`compose` materialised the v4 + targeted review composition in
`output/composition-audit-v3/`: 100 articles and 225 pairs, but `ready_for_scoring` is
`false`. Seven alerts block it: CMCSA missing in N030, N047 and N061; CMCSA and PSKY
missing in N048; NWSA missing in N066; XOM/N100 based on the false SpaceX → Exxon Mobil
match. The v5 candidate has fifteen blocking alerts and differs on 29 articles.

Registry `entity-aliases-v5`: CNBC and NBC News → CMCSA, CBS and CBS News → PSKY,
Barron's → NWSA, Kenworth → PCAR; `X → XYZ` and `SpaceX → XOM` forbidden. The checks
never change a classification: they only keep a doubtful composition out of scoring.

A first joint review of the six articles added all the sources and removed XOM/N100,
but also changed three labels and removed SCHW/N066; that batch was rejected. The
`additions-only` mode then made the invariants executable: any removal or change of an
existing label invalidates the answer. The retained composition,
`output/composition-final-v3/`, has 230 pairs (70 positive, 106 neutral, 54 negative),
zero blocking alerts and `ready_for_scoring=true`. Exported to `output/final-results-v1/`
(111 tickers). This phase added **0.3314652 USD** of known cost.

This manual chain of runs is not reproducible by a single command, and its baseline
prompt (v4) is no longer in the code. It was therefore replaced.

## End-to-end command, prompt v5 (`run-final-v1`)

`run --max-cost-usd 4 --output-dir output/run-final-v1`: `completed`, zero blocking
alerts, 232 pairs (63 positive, 119 neutral, 50 negative), 112 tickers. 114 calls for
3.0187697 USD, i.e. **0.030 USD per article** for one cold pass (0.026 classification,
0.004 for 13 targeted reviews). 86 % of the cost is provider cache writes.

## Prompt v6 with roles, three passes and vote (`run-v6-vote3`, retained)

Prompt `entity-sentiment-v6-roles` asks for the role of every company and forbids a
directional label for the roles the assignment defines as neutral. A first single-pass
run stopped on N064 (an evidence excerpt paraphrased twice); retries now carry the
validator's reason. `run --passes 3 --max-attempts 3`: `completed`, zero blocking
alerts, 233 pairs (61 positive, 117 neutral, 55 negative), 112 tickers. The three
passes agree on 224 of 239 proposed pairs (93.7 %); the vote keeps 9 pairs by majority
and drops 6 proposed by a single pass. Passes 2 and 3 cost about 0.006 USD per article
thanks to the provider cache.

## Measurement and choice

All six complete versions were compared on every disagreement plus 25 random checks of
the consensus ([`review/reference-v1`](../review/reference-v1/README.md), adjudicated by
the agent). Estimated pair accuracy: manual composition 0.878, `run-final-v1` 0.907,
single v6 passes 0.920–0.924, **three passes with vote 0.933**. The ranking holds on
the 20 non-debatable disputed cases (9, 17, 16–17 and 19 correct). The retained version
is `output/run-v6-vote3/final/`, copied to `results/`. These values describe the
supplied articles only and are not investment recommendations.
