# Review of the analyses — initial sample

Status: N001, N002 and N027 analysed through the API and reviewed by the agent on
13 October; no independent human validation. This document is not a ground-truth set
and does not support an accuracy claim. Article facts are treated within the
assignment, without external verification or enrichment.

## Selection

| Article | What to check while reading the full text |
| --- | --- |
| N001 | Distinguish the rated company from the bank issuing the recommendation; keep neutral mentions |
| N002 | Classify each company separately and keep only the supplied universe |
| N003 | Recognise look-alike Unicode spellings from the product context; distinguish news from past recalls |
| N027 | Check mentions after U+200B removal, without altering the sources |
| N029 | The main subject may be outside the universe; a pilot customer does not automatically inherit the sentiment of the fundraising |
| N070 | Map product and subsidiary to the explicit parent; also examine incidental mentions, including a conference name |
| N077 | Assess competitors separately, map brands and examine the media source; avoid dual classes |
| N096 | A company outside the universe does not become eligible because an investor or partner is known; consider an empty list |

First technical trial run on `N001 N002 N027`. Extend later to the distinct articles
above within budget, after consolidating the observed omissions.

## Assisted review of the pilot — 13 October 2026

Reviewer: Codex agent, after reading the predictions and the full text. These are
therefore neither independent annotations nor a benchmark.

| Article / ticker | Expected by the review | v1 (pilot-002) | v2 (pilot-003, retained) | Reason |
| --- | --- | --- | --- | --- |
| N001 / FIS | negative | negative | negative | Downgrade and lower guidance |
| N001 / FISV | negative | negative | negative | Guidance problems mentioned for Fiserv |
| N001 / MS, WFC | neutral | neutral | neutral | Banks issuing the recommendations, no established implication of their own |
| N002 / COIN, XYZ | positive | positive | positive | Raised targets with a favourable recommendation |
| N002 / GS | neutral | omitted | neutral | Goldman Sachs issues the recommendation; eligible mention |
| N027 / TSLA | negative | negative | negative | Share drop and investigation |
| N027 / GOOGL | neutral | omitted | omitted | Waymo is a fleet comparison; parent link inferred, absent from the CSV |

Microstrategy and Circle are outside the supplied universe; omitting them is not an
error. The mention of the Nasdaq index in N001 is not enough to identify the operating
company NDAQ. The Waymo/Alphabet link is a knowledge inference of the model/agent to be
validated in review; no external business source was consulted.

Prompt v2 asks for an inventory of every paragraph before assigning labels, notably
banks, sources and comparisons. A v3 variant clarifying the use of known parent links
and using `reasoning.effort=medium` was tested in `pilot-004`: GS and GOOGL are missing
there. That variant is not retained. Neither results nor caches were corrected by hand.

Current limit: extraction completeness is guaranteed neither by the JSON schema nor by
an extra instruction. Before a full run, consider a dedicated check of forgotten
mentions and evaluate it on the other review articles, not only on the three cases used
to tune the prompt.

Later redesign requested by the user: RCORCF v4 and ten teaching examples. The v4 API
result is in `output/pilot-005`. N027 is now a development case taught explicitly
through a synthetic Waymo example; do not count it as an independent evaluation of the
new version.

## RCORCF v4 retest — 13 October 2026

| Article | Classifications obtained |
| --- | --- |
| N001 | FIS negative; FISV negative; MS neutral; WFC neutral |
| N002 | COIN positive; GS neutral; XYZ positive |
| N027 | GOOGL neutral; TSLA negative |

The nine pairs match our assisted review of these three articles. Compared with v2,
GOOGL is added through the Waymo comparison excerpt; no other ticker or label changes.
Goldman Sachs, recovered by v2 and lost in the v3 trial, is kept. The excerpts pass the
exact-presence check in the normalised text. No result was edited.

Three calls, no retry, no local cache used: 0.0888659 USD, 40,884 input tokens and 677
output tokens. This small set, already used to design the prompt, does not demonstrate
quality on the other articles.

## Method

Extension run on ten other articles, with the agent's expectations recorded before the
calls: [REVIEW_10.md](REVIEW_10.md). Disagreements are kept there; these are still not
independent human annotations.

1. Before looking at the prediction, read the normalised headline and body. Note every
   identifiable company, its canonical ticker in the CSV, its role, the expected label
   and the supporting excerpt. Note uncertain cases.
2. Compare with the objects in `classifications.json`: omissions, unjustified additions,
   wrong parent, sentiment attributed to the wrong company, an old fact wrongly
   dominating new information, forgotten neutrality.
3. Record the decisions in a review table: `article_id`, `ticker`, `expected_label`,
   `predicted_label`, `error_type`, `rationale`, `reviewer`. Never edit the results
   produced by the pipeline directly.
4. Fix the prompt or the code for a recurring error; change its version, regenerate
   within budget and keep the trace of the disagreement. Keep a few other articles for
   a check after the fix to limit overfitting.

When annotations exist, measure separately the precision/recall of article-ticker pairs
and the label accuracy on correctly detected pairs. Report the number of cases, the
adjudications and the limited sample size. An exact excerpt validates textual
traceability, not the correctness of the label, of the brand-parent link or the
completeness of the companies found.

The later, larger measurement is [`review/reference-v1`](../review/reference-v1/README.md).
