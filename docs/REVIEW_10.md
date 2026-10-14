# RCORCF test on ten other articles — 13 October 2026

## Selection and expectations before the calls

Frozen prompt: `entity-sentiment-v4-rcorcf`, model `gpt-5.6-terra`, low effort, at most
one attempt per article. None of these ten articles had been processed in the earlier
pilots. Targeted, non-random selection to vary the difficulties. Some themes resemble
the prompt examples, notably the Microsoft pilot customer; this is not a test fully
independent of the design choices.

The expectations below were set by the agent after reading the texts and the reference
file, BEFORE requesting the predictions. They are provisional annotations to be checked
by a human, not certified ground truth. The facts in the dataset are treated as given,
without external verification.

| Article | Provisional expectations | Checkpoint |
| --- | --- | --- |
| N003 | F negative; TSLA negative | Homoglyphs of Tesla and TSLA, Cybertruck context; Rivian and Reuters outside the universe |
| N029 | MSFT neutral | Pilot with no commercial commitment; startup and TSMC outside the universe |
| N054 | DAL, HD, KO, UPS neutral | Companies named without established operational disruption despite the negative headline |
| N063 | AAPL, GOOGL neutral | App removal, platforms explicitly not involved in the leak; unnamed banks excluded |
| N064 | COIN positive; AAPL, MSFT, NVDA, TSLA, NWSA neutral | New contract opportunity for Coinbase, underlyings with no implication of their own; WSJ as source |
| N070 | JNJ positive; JPM neutral | Product and subsidiary mapped to J&J, incidental JP Morgan conference |
| N077 | GOOGL positive or neutral; NFLX positive or neutral; NWSA neutral | Favourable new initiatives facing stronger competition; ambiguous net sentiment to adjudicate |
| N084 | PNR negative; CMG neutral; P neutral | Everpure filtration belongs to Pentair; homonym P is distinct, temporary drop then recovery; customer without closures |
| N096 | No eligible entity | Do not add unnamed investors or partners of OpenAI/Anthropic |
| N097 | BA negative; GE negative or neutral; RTX, LMT, NWSA, BLK, STT neutral | Main effect on Boeing; small GE move to adjudicate; WSJ and iShares/SPDR fund brands |

The links WSJ → News Corp, iShares → BlackRock and SPDR → State Street are identity
inferences known to the agent, not relationships supplied by the CSV. Their inclusion
and the mention of JPM in a conference name deserve explicit human review. Alternative
sentiments are declared in advance so that no prediction can be turned into a correct
result after the fact.

Thirty article/ticker pairs are proposed in total, subject to these adjudications. An
empty list is expected for N096. Compare company presence, sentiments and textual
exactness of evidence separately. Never change outputs to match the expectations.

## Results

Complete run: `output/review-010-resume/classifications.json`.

| Article | Result | Comparison with the prior expectations |
| --- | --- | --- |
| N003 | F negative; TSLA negative | As expected; the Tesla name written with look-alike characters is recognised |
| N029 | MSFT neutral | As expected; no benefit attributed to the mere pilot customer |
| N054 | DAL, HD, KO, UPS neutral | As expected; no contamination by the negative tone of the incident |
| N063 | AAPL, GOOGL neutral | As expected; platforms with no implication of their own in the leak |
| N064 | COIN positive; AAPL, MSFT, NVDA, NWSA, TSLA neutral | As expected after a technical retry; WSJ mapped to News Corp |
| N070 | JNJ positive | JPM missing despite "JP Morgan Healthcare Conference"; an omission under our incidental-mention rule, to confirm with a human |
| N077 | GOOGL neutral; NFLX negative | NWSA missing despite the WSJ; Netflix label disagrees with the prior alternatives, to adjudicate |
| N084 | CMG neutral; P neutral; PNR negative | As expected; the two Everpure companies are distinguished and the customer does not inherit the recall |
| N096 | Empty list | As expected; no unnamed investor or partner added |
| N097 | BA negative; GE, RTX, LMT, NWSA, BLK, STT neutral | Within the prior alternatives, subject to the brand inferences and the GE label |

Twenty-eight pairs produced out of the thirty proposed in the provisional review, with
no extra pair. Two omissions and one sentiment disagreement are reported. Eight
articles fully match the expectations or alternatives declared before the calls. This
measures agreement with THIS agent review, not certified production accuracy or an
independent human validation.

For Netflix, the chosen evidence mentions falling engagement, while the text also
covers content acquisitions meant to offset it. The negative label may reflect that
difficulty; the net implication must be adjudicated without changing the expectations
afterwards to hide the disagreement. The News Corp omission is separate from that
adjudication: the WSJ is explicitly cited in the article.

## Execution and cost

The first run `output/review-010` stopped on N064 after four valid results and one
rejected answer. Its exact reason was not kept by the initial log and the invalid
answer was not saved: do not invent the cause. A fixed `validation_error` diagnostic
was added for future errors, without answer text or key; the non-disclosure tests and
the full suite pass (63). Prompt, schema and validations unchanged.

The resumed run in a new directory reuses the four cached results and completes the
other six without a new failure. N064 therefore needed two calls in total, all counted.
Model results were not edited.

| Run | Calls | Local cache | Cost USD |
| --- | --- | --- | --- |
| review-010, interrupted | 5 | 0 | 0.1322405 |
| review-010-resume, completed | 6 | 4 | 0.1469120 |
| Total for the ten-article test | 11 | 4 replays | 0.2791525 |

Cumulative tokens: 149,790 input, of which 60,340 provider cache reads and 89,417
provider cache writes; 3,623 output. Cost per article of the complete test, rejected
answer included: 0.02791525 USD. The cost of the resume alone must not be presented as
the cost of the ten initial classifications.

Known cumulative project cost: 0.6048610 USD; unknown reservation kept from the first
network failure: 0.173757 USD; conservative balance of the 5 USD: 4.2213820 USD.

Checks: ten distinct ids, completed manifest, correct version and request hashes,
revalidation of the 28 entries and exact evidence, both sources intact. Data, outputs
and caches were not edited by hand.

Proposed next step: human review of the reported cases, then a targeted improvement of
the secondary-mention check. Do not conclude that the RCORCF examples alone guarantee
completeness on the 100 articles.

## Experimental second pass — 13 October 2026

Run `output/verification-010`, prompt `entity-review-v1` added to RCORCF v4, same model
and low effort. The initial proposal and the lexical hints are sent, but not the
expectations of this review. No initial result modified.

| Case | First pass | Second pass | Provisional assessment |
| --- | --- | --- | --- |
| N077, News Corp | NWSA missing | NWSA neutral, excerpt quoting The Wall Street Journal | Omission fixed |
| N070, conference | JPM missing | JPM still missing | Omission kept, to adjudicate with a human |
| N084, Everpure storage | P neutral | P removed | Regression: the distinct company is explicitly named; lexical check does not cover P |
| N077, Netflix | NFLX negative | NFLX negative | Sentiment disagreement unchanged |

The other eight articles keep the same tickers and labels. Still 28 pairs in total: one
addition, one removal, no sentiment change. Two pairs are missing compared with the
thirty provisionally expected (JPM and now P). Seven articles fully match the initial
expectations, against eight before the review. This is still agreement with the
agent's annotations, not an accuracy score on a human-validated set.

The lexical hints also flag NDAQ in N003 and N070 because of "Nasdaq": these alerts do
not justify automatically adding the company. With the CSV names alone they detect
neither the JP Morgan variant nor the WSJ brand. Their value here is to make the
removal of P visible, not to guarantee completeness or correct brand mapping.

**Decision:** keep this output as a proposal to examine. The first pass remains the
comparison point; no merge and no manual correction. Before adopting a new strategy,
adjudicate the human cases and check regressions on the same criteria, then on
distinct articles.

**Execution:** ten calls, zero retries, zero local cache; 141,562 input tokens (44,496
cache reads, 97,036 cache writes), 1,911 output. Additional cost **0.2744812 USD**;
known cumulative **0.8793422 USD**, unknown reservation kept **0.173757 USD**,
conservative balance **3.9469008 USD**. 71 offline tests pass. Ten requests and 28 pairs
revalidated, hashes of the sources and of the initial result unchanged; `.env`, cache
and outputs ignored by Git.

## Targeted review v2 — 13 October 2026

After freezing registry `entity-aliases-v1` and rules `entity-coverage-v2`, the dry run
selects only N070, N077 and N084. The targeted mode received neither the expectations
of this document nor the expected corrections; it receives the article, the reference
file, the first proposal and the deterministic hints.

| Case | Targeted v2 result | Adjudication |
| --- | --- | --- |
| N070 | JPM neutral added; JNJ positive kept | As expected |
| N077 | NWSA neutral added; GOOGL neutral kept | Coverage as expected |
| N077 | NFLX stays negative | Disagreement kept with our neutral preference; a genuinely mixed case |
| N084 | P neutral, PNR negative and CMG neutral kept | v1 regression fixed |
| Nasdaq | No NDAQ added | False positive removed |

Entity coverage reaches the thirty provisionally expected pairs once the three targeted
proposals are applied to the seven unchanged results. This measurement still depends
on the agent's annotation. The v2 result remains a separate artifact; no manual or
automatic merge was made.

Run `output/targeted-review-003`: three calls, no retry or local cache, 43,025 input
tokens (9,976 cache reads and 33,040 cache writes), 679 output tokens,
**0.0927612 USD**. That is about 66 % cheaper than the general review of the ten
articles (0.2744812 USD), while fixing its observed regression. This ratio does not
predict the share of alerts on 100 articles. Known cumulative **0.9721034 USD**,
unknown reservation **0.173757 USD**, conservative balance **3.8541396 USD**.

The 74 offline tests pass. The three answers, evidence, request keys, hashes of the
registry, of the initial classification and of both sources were revalidated. The next
iteration can address aggregation and the CSV files, keeping the NFLX disagreement
among the quality limits.
