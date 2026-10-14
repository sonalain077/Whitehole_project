# Work log

Chronological record of what was asked, done, run and verified. Amounts are in USD.
Entries up to 13 October were written by the Codex agent and those of 14 October by
Claude Code; both followed `AGENTS.md`.

## 2026-10-12 — iteration 0

**Request:** plan and initialise the project, starting with a methodical agent context,
then work iteratively and safely.

**Done:** text reading of the five pages of the assignment through the PDF character
tables; inspection of the inputs; creation of the five required documents, this log,
the data quality report, the exclusions and a minimal Python skeleton. The PDF was not
modified. No visual rendering check of the source PDF.

**Choices:** local Python pipeline; initial target version 3.12; code for contracts and
arithmetic, mandatory model for comprehension; cache and budget from the first API
client. No application framework, premature business dependencies or fake logic
presented as an implementation.

**Checks run:** file inventory; JSON parsing with Node; CSV with `Import-Csv`; search
for empty fields, duplicates and invisible characters; hashes with
`Get-FileHash -Algorithm SHA256`. Results in `DATA_QUALITY.md`. The JSON count was
checked with Node (100) after noticing that a PowerShell array wrapper counted the
whole array as a single element.

**Final review:** 12 files created and checked; local Markdown links resolve, files end
with a newline, no replacement characters. The three SHA-256 hashes recomputed match the
initial sources. These document and integrity checks do not replace Python tests.

**Limits:** `git`, `python`, `py`, `uv` and `pdftotext` not available in the inspected
terminal. No venv, Git repository, lock file, Python test or classification run created
or executed. No API call or classification cost.

**Next:** batch 1 of the plan: tooling, ingestion, normalisation and offline audit.

## 2026-10-12 — iteration 1

**Goal:** provide an offline audit CLI, strictly validate both inputs, normalise without
modifying the sources, handle the New York time zone and produce a testable canonical
universe.

**Done:** modules `errors`, `models`, `normalization`, `dates`, `ingestion`, `audit`,
`cli` and entry point `python -m aie2609`. The `audit` command has human and JSON
output. JSON keys, CSV columns, fields, types, duplicates, ambiguous/nonexistent dates,
future articles and share classes are validated. Raw and normalised texts stay separate
in memory.

**Environment:** official Python 3.12.10 installed locally in `.tools`, valid Authenticode
signature (Python Software Foundation) and MD5 matching the release page. `tzdata==2026.5`
and `setuptools==82.0.1` locked with their SHA-256. `.venv` created and the package
installed in editable mode. Official MinGit 2.56.0.windows.2, SHA-256 checked, installed
in `.tools`; local repository initialised on `main`, with no commit and no remote. Local
tools, venv and downloads are ignored by Git.

**Checks:** Python compilation succeeds and `pip check` reports no broken dependency.
After an expected first failure due to the missing IANA database on Windows, `tzdata`
was added; the 15 initial tests then pass. The real audit returns 100 articles, 503
source rows, 500 canonical companies, dates from 2026-08-25T06:53 to 2026-09-28T16:20 and
two non-blocking anomalies: 6 U+200B in `N027`, 10 in `N100`. The final review confirms
16 tests, including the exit code of a CLI error, and the original hashes of the three
sources. No API call.

**Limits:** the CLI does not classify any article yet and does not produce the CSV files.
The execution sandbox has a different Windows owner from the folder: the agent's Git
commands use `-c safe.directory=...` when needed; this does not modify the global
configuration.

**Next:** batch 2: client for the mandatory model, prompt, strict validation, cache,
budget and metrics with simulated tests before any real call.

## 2026-10-12 — iteration 2, offline validation

**Request:** start extraction and classification with the model key provided for the
project. The key must not be shared in the conversation.

**Done:** `classify` command with selection by ids or limit, offline preview, prompt
`entity-sentiment-v1`, strict JSON Schema, validation of tickers, labels, duplicates and
exact excerpts. Standard Responses transport, cache keyed by the request hash, budget in
`Decimal` and durable reports before every call. The internal result holds a separate
analysis per article and company. CSV files and scoring stay in batch 3.

**Choices:** standard library `urllib`, no new SDK; fixed OpenAI endpoint, redirects
refused, no model substitution, key only from the environment. Bounded retries for an
invalid answer or an identified rate limit; a lost network response is not automatically
resent. An unknown cost stays explicit and its reservation is kept. Local and provider
caches are counted separately. The local cap is an estimate.

**Initial prompt:** each company's own role, neutral incidental mentions, brand/subsidiary
mapping, partner/investor versus parent, look-alike Unicode names confirmed by context.
The excerpt must keep the spelling of the normalised text. No input editing. The
`REVIEW_SET.md` set proposes eight articles to annotate; it is not a validated human
reference and no semantic quality score is claimed.

**API documentation checked:** official `gpt-5.6-terra` page, Responses, Structured
Outputs and cache categories. Dated prices and links recorded in `ARCHITECTURE.md` and in
the usage code. The real key's contract and compatibility with the expected fields are to
be confirmed in the small trial.

**Checks run:**

- `python -m unittest discover -s tests -v` in the venv: 54 tests pass, offline. Covered:
  validation, replayed and corrupted cache, budget overrun, counted retries, missing usage,
  truncated answer, timeout, refusal/incompleteness, no redirect, CLI preview without client.
- `python -m pip check`: no broken dependency; `compileall -q src tests` succeeds. No
  extra dependency installed in batch 2.
- `python -m aie2609 audit`: 100 articles, 503 rows and 500 canonical companies, the same
  two U+200B anomalies as in batch 1.
- `classify --ids N001 N002 N027 --dry-run`: three requests prepared with no call or
  artifact, cumulative first-attempt reservation 0.5156135 USD, a conservative estimate,
  not a measured or guaranteed cost.
- SHA-256 of the three sources unchanged; local Markdown links and encoding checked; no
  API key pattern in code or documents. Git state reviewed, no commit or push.

**Limits and next:** no API call or cost. `OPENAI_API_KEY` is absent from the inspected
process; budget requested, no answer yet. Batch 2 is implemented and technically
validated offline; the real trial and the prediction review remain. Proposed trial:
N001, N002, N027, one attempt each, then inspection of analyses and costs before extending.

## 2026-10-12 — first trial budget confirmed

The user authorises "max 5 usd" for the first trial: a cumulative 5 USD cap, retries
included; this authorisation persists and must not be asked again. Start with N001, N002
and N027, one attempt each, then review the results before any extension. Never reset
this cap by creating a new run directory after an error.

Check limited to the presence of `OPENAI_API_KEY`, without displaying any value: absent
from the process, from the Windows user variables and from the machine variables. No API
call, no spend. The key still has to be configured locally. No code changed.

## 2026-10-13 — simpler local configuration

**Request:** use `.env` to avoid PowerShell input commands.

**Done:** `config.py`, loaded only by `classify` after argument and budget validation,
before building the client. Reads only `OPENAI_API_KEY` in the current folder; a non-empty
environment variable wins; no execution or interpolation; errors without secret content.
An empty `.env` was created in exclusive mode so as never to overwrite an existing file;
`.env.example` stays without a key. The `.env` exclusion already existed.

**Checks:** 60 tests pass with `unittest discover -s tests -q`, offline. Tests for simple
and quoted formats, BOM, environment priority, missing/empty file, duplicates, invalid
encoding, no leak in errors and no loading during preview. No API call.

**Next:** fill the key locally, then run the small trial already authorised within the
cumulative 5 USD budget.

## 2026-10-13 — first API pilot and review of omissions

**Authorisation:** key saved by the user in `.env`, then confirmation that it was saved.
Cumulative 5 USD budget already authorised. No key value displayed or copied into
reports; only its presence was checked.

**Run:** N001, N002 and N027, one attempt per article and per variant, mandatory model
`gpt-5.6-terra`. First launch blocked by the sandbox network; diagnosis without
authentication: `PermissionError / WinError 10013`. Relaunched with approved network
access, in a new directory, with the budget reduced by the initial reservation, kept as a
precaution. No endpoint change.

| Directory | Version | Result | Known cost USD | Unknown reservation USD |
| --- | --- | --- | --- | --- |
| output/pilot-001 | v1 | Network failure on the first article | 0 | 0.173757 |
| output/pilot-002 | v1 | 3 articles, 3 validated answers | 0.0789105 | 0 |
| output/pilot-003 | v2 | 3 articles, 3 validated answers; retained | 0.0787458 | 0 |
| output/pilot-004 | v3 experimental | 3 articles, 3 validated answers; not retained | 0.0791863 | 0 |

The three completed runs report 98,835 input tokens and 1,470 output tokens in total
(cache categories in their `usage.json`). Nine answers received and one failed local
attempt. Known cumulative cost **0.2368426 USD**; cost of the network attempt unknown in
the report. Conservative commitment **0.4105996 USD**, initial budget balance
**4.5894004 USD**. No unknown cost was replaced by zero and no budget was renewed between
variants.

**Assisted review:** reading of the three articles, check of the reference file and
comparison of the results. v1 misses GS in N002 and GOOGL via Waymo in N027. v2 requires a
paragraph-by-paragraph inventory, with analyst banks, sources and comparisons, before
sentiment; GS is recovered. v3 clarifies known parent links and raises reasoning from low
to medium; it still misses GS and GOOGL. Back to prompt v2 and low reasoning, without
editing results. The separate effect of each of the two v3 changes is not isolated by
this trial. The Waymo case remains a limit to solve, not a success. The review table is in
`REVIEW_SET.md`, with no claim of independent human validation.

**Final checks:** 60 offline tests pass after going back to v2. Current request hashes
match `pilot-003` exactly; its answers pass the validator again; the hashes of both inputs
match the manifest. Git ignores `.env`, outputs and cache. No commit, push, secret
exposure or source editing.

**Status:** API integration validated on a small trial; semantic recall still
insufficient on a subsidiary mention. Before the 100-article run, improve recall and check
on articles distinct from those used to tune the prompt.

## 2026-10-13 — prompt redesign following RCORCF

**Request:** improve the system prompt following Rôle, Contexte, Objectif, Résultat,
Contraintes, Format (Role, Context, Objective, Expected result, Constraints, Format), with
detailed examples, and explain the two version tags.

**Done:** `SYSTEM_PROMPT` rewritten in six sections in `classification.py`, instructions
in English and bilingual headings. Ten synthetic examples with their own universe,
article, complete JSON object and teaching note. Detailed rules for neutrality,
subsidiaries, sources, classes, identity uncertainty, mixed news, timing, Unicode, exact
evidence and malicious instructions inside the data. Model, schema, low effort and input
handling unchanged.

**Versions:** `entity-sentiment-v4-rcorcf` active for the next calls; v3 had already been
used in a trial, its number is not recycled. Normalisation kept at `nfc-lf-u200b-v1`, since
its policy did not change. The v2 pilot remains a historical comparison, not evidence about
v4. Versions, cache, examples and limits documented in `PROMPT_DESIGN.md`.

**References:** official OpenAI Prompt engineering and Reasoning best practices guides;
links in `PROMPT_DESIGN.md`. RCORCF is the structure explicitly requested by the user.

**Checks run:** `unittest discover -s tests -q`: 62 tests pass. New checks read the
examples directly from the prompt and verify their JSON, labels, tickers, uniqueness,
order and exact evidence. Another test checks that each of the two tags invalidates the
cache independently. Real preview on N001/N002/N027 succeeded, indicative cumulative
reservation 0.6177635 USD, no call or spend. Keys differ from the v2 pilot; hashes of both
inputs unchanged.

**Limits and next:** no v4 API result yet; semantic quality still to measure. The examples
are not an independent test set, notably Waymo, inspired by a known omission.

## 2026-10-13 — RCORCF prompt retest

**Request:** retest to see what the new prompt gives. Run on
the same three articles for a direct comparison with v2, with no change of prompt, model,
parameters or code.

**Command:** `python -m aie2609 classify --ids N001 N002 N027 --max-cost-usd 4.5894004
--max-attempts 1 --output-dir output/pilot-005`, with the venv and the required network
access, after reading the previous commitments. Model `gpt-5.6-terra`, prompt
`entity-sentiment-v4-rcorcf`, low effort.

**Result:** three validated answers, three calls, zero retries, zero local cache, nine
article/ticker pairs. N001 and N002 keep the same tickers and labels as v2. N027 adds
GOOGL neutral to TSLA negative, with an exact excerpt mentioning Waymo. GS neutral is
present in N002. Detailed table in `REVIEW_SET.md`; no manual editing of outputs.

**Usage:** 40,884 input tokens, of which 9,332 cache reads and 31,543 cache writes; 677
output tokens. Reported cost **0.0888659 USD**. Known cumulative cost **0.3257085 USD**.
The 0.173757 USD reservation of the first network failure is kept; total commitment
**0.4994655 USD**, conservative balance **4.5005345 USD**.

**Checks:** manifest completed, right version, request hashes matching the current code,
nine entries revalidated, labels compared with v2, both sources intact. No code change in
this retest, so no new run of the test suite is claimed.

**Limit:** favourable result on known cases, including Waymo taught by a prompt example.
No generalisable accuracy rate and no independent human validation.

## 2026-10-13 — test on ten more articles

**Request:** test ten examples. Selection of N003, N029, N054, N063, N064, N070, N077,
N084, N096 and N097, all distinct from the earlier pilots. Full reading and provisional
expectations recorded in `docs/REVIEW_10.md` BEFORE the calls, with explicit alternatives
for ambiguous cases.

**Run:** prompt v4 RCORCF, mandatory model and low effort unchanged. Dry run succeeded,
indicative cumulative reservations 2.0546625 USD. First run with the remaining budget
4.5005345 USD and one attempt per article in `output/review-010`: four successes then
rejection of N064, cost 0.1322405 USD. As the exact reason was not logged, the cause of
this rejection cannot be established afterwards from the kept artifacts.

**Limited fix:** `runner.py` now keeps the validator's fixed diagnostic in
`validation_error` and in the final message, with no raw answer, excerpt or secret. New
non-disclosure test; 63 tests pass. Neither prompt, schema nor acceptance criteria were
changed to get around the failure.

**Resume:** new directory `output/review-010-resume`, budget 4.368294 USD after deducting
the first run, at most two attempts. Four results replayed from the cache, six new calls
all valid. N064 needed two calls in total.

**Result:** ten articles completed, 28 pairs. Eight articles match the agent's prior
expectations or alternatives. JPM is missing in N070 despite the conference name, NWSA in
N077 despite the WSJ. NFLX negative is a sentiment disagreement to adjudicate. The Unicode
cases, neutrality of unaffected actors, Everpure homonyms and the N096 empty list are
handled correctly according to this provisional review.

**Cost:** 11 calls in total; 0.1322405 + 0.1469120 = **0.2791525 USD**, rejection
included. 149,790 input tokens (60,340 cache reads, 89,417 cache writes) and 3,623 output.
Known cumulative project cost **0.6048610 USD**; earlier unknown reservation
**0.173757 USD**; total commitment **0.7786180 USD**; conservative balance **4.2213820 USD**.

**Checks:** 63 offline tests pass after the diagnostics change; manifest completed, ten
distinct ids, request hashes matching, 28 entries and evidence revalidated, both sources
intact. `.env` and results ignored by Git. No commit or push.

**Next:** adjudicate the reported cases and improve the secondary-mention check before
the full set. Prompt kept unchanged so that this evaluation stays comparable.

## 2026-10-13 — lexical check and second pass on ten articles

**Request:** apply the proposed improvements and check the outputs. Added `review.py`, CLI
command `review`, limited runner extension points for the request and the difference
report. Advisory name/ticker hints, strict validation of the initial file, separate cache,
same model and same budget/retry limits. Review prompt `entity-review-v1`, lexical rules
`explicit-name-ticker-v1`; base prompt v4 and normalisation unchanged.

**Tests:** 71 tests pass. Eight new tests cover exact hints, false positives of common
words, a cache distinct per proposal, invalid input, simulated review and cache, no forced
addition, removals/label changes without mutating the initial result, and dry run without
key or network client.

**Run:** `python -m aie2609 review --classifications
output/review-010-resume/classifications.json --dry-run`, then the same command without
dry run with `--max-cost-usd 4.221382 --max-attempts 2 --output-dir output/verification-010`.
Ten calls completed, no retry, no local cache.

**Result:** NWSA neutral added in N077, but P neutral removed in N084. JPM still missing
in N070; Netflix still negative in N077. 28 pairs, one addition, one removal, no label
change. The P regression is reported by `unresolved_hints_after`. Irrelevant NDAQ alerts
in N003 and N070. The review is not adopted automatically.

**Cost:** 141,562 input tokens (44,496 cache reads, 97,036 cache writes), 1,911 output;
**0.2744812 USD** additional. Known cumulative **0.8793422 USD**; unknown reservation
**0.173757 USD**; total commitment **1.0530992 USD**, conservative balance **3.9469008 USD**.

**Checks:** manifest completed, ten distinct ids, ten request keys recomputed and
matching, 28 entities and excerpts revalidated, hashes of both sources and of the first
classification unchanged. No result edited, no commit or push.

**Limits and next:** this second pass shows no net coverage gain; the same model can
reinforce or introduce an error. Test a targeted fix without losing justified entities.

## 2026-10-13 — versioned aliases and targeted review

**Goal:** generalise the check without building an exhaustive subsidiary database. Added
`entity_aliases.json` with certain relationships, the ambiguous Everpure and names excluded
from automatic generation. Legal-name variants still come from the CSV. `review` selects
alerts by default; `--all` keeps the full mode. No alias directly produces a classification.

**Implementation:** `entity-coverage-v2` emits `candidate_tickers`, separates reliable and
ambiguous aliases, recognises tickers explicitly introduced by "ticker" or "symbol" and
excludes the short form Nasdaq from company matching. `entity-review-v2-targeted`
strengthens the preservation of explicitly justified entities. Packaged registry, version
and hash traced. Difference report moved to schema 2 with `review_reasons` and
`alias_version`.

**Offline check:** 74 tests pass. The real dry run selects only N070, N077 and N084.

**Real run:** `python -m aie2609 review --classifications
output/review-010-resume/classifications.json --max-cost-usd 3.9469008 --max-attempts 2
--output-dir output/targeted-review-003`. Three calls, cost **0.0927612 USD**.

**Result:** JPM neutral added to N070, NWSA neutral added to N077, P neutral kept with PNR
negative and CMG neutral in N084. No NDAQ. NFLX stays negative, a documented semantic
disagreement rather than a manual correction. The targeted review costs 66 % less than the
general one. No result file merged or edited. Known cumulative **0.9721034 USD**, unknown
reservation **0.173757 USD**, commitment **1.1458604 USD**, balance **3.8541396 USD**.

## 2026-10-13 — full test on the 100 articles

**Request:** test the 100 articles before scoring. Dry run: 100 potential requests,
theoretical maximum reservation 20.5746125 USD; real sequential control bounded by the
conservative balance 3.8541396 USD.

**First pass:** `classify --limit 100 --max-cost-usd 3.8541396 --max-attempts 2
--output-dir output/full-100-v4`. 100 articles, 87 calls, 13 results replayed from the
cache, no retry or unknown spend. 217 pairs: 70 positive, 93 neutral, 54 negative; 11
empty lists. 1,186,925 input tokens (401,276 cache reads, 785,388 cache writes) and 16,733
output. Cost 2.2450432 USD.

**Defect found:** the v2 check flagged 45 articles, mostly because `target`, `block`,
`southern`, Rollins, `(MA)` and `(CMS)` were mapped to TGT, XYZ, SO, ROL, MA and CMS. No
review call was made on that noisy list. Versioned fix: `entity-aliases-v2`,
`entity-coverage-v3`, no general matching of parenthesised tickers and ambiguous short
forms blocked. Non-regression test added; **75 tests pass**. Eight plausible alerts.

**Targeted review:** `review --classifications output/full-100-v4/classifications.json
--max-cost-usd 1.6090964 --max-attempts 2 --output-dir output/full-100-targeted-review`.
Eight calls, 0.2281222 USD. Additions: STT/N012; NWSA and WBD/N013; SBUX/N038; JPM/N070;
BLK/N076; NWSA/N077; IVZ/N091. No removal or label change.

**Check:** two completed manifests, 100 ids, 225 pairs after in-memory composition, evidence
and keys revalidated, hashes of sources, registry and first output matching. No written
merge or manual edit.

**Budget:** batch cost 2.4731654 USD; known cumulative 3.4452688 USD; earlier unknown
reservation 0.173757 USD; conservative commitment 3.6190258 USD; balance of the 5 USD
**1.3809742 USD**.

## 2026-10-13 — preparation of the last full pass

**Request:** apply the small adjustments from the semantic review, then rerun the 100
articles before the automatic composition.

**Changes:** `entity-sentiment-v5-rcorcf` specifies that historical performance or a small
peer move cited only as a comparison stays neutral, and requires judging each party of an
agreement separately. Two synthetic examples cover these decisions. `entity-aliases-v3`
adds CNN → WBD. No existing result edited.

**Check:** offline dry run on 100 articles: new prompt version and new cache keys;
theoretical maximum reservation 21.1006125 USD. The first run of the 75 tests revealed an
incomplete N013 fixture, fixed to include AMZN before testing the WBD alert; the **75 tests
pass**.

**Run:** cap raised explicitly to 10 USD. A first call blocked by the network keeps an
unknown reservation of 0.176203 USD. A resume validates N001–N090 for 2.3567970 USD, then a
512-token pass validates N091–N096 and is also billed for an incomplete N097 answer, for
0.1828785 USD. The coherent run `output/full-100-v5-final`, at 1,024 tokens, replays 90
cached answers and makes ten calls for 0.1174879 USD.

**Result:** 220 pairs (62 positive, 105 neutral, 53 negative); 11 empty lists. Compared with
v4 + targeted review: 29 articles change, seven additions, twelve removals and 23 label
changes. Intended fixes N069/N091/N095 obtained. Regressions: two false XYZ from the social
network X, lost neutral mentions, BAC/N092 hit by the Nike downgrade, NVDA/N076 dominated by
an old favourable context. v5 is therefore not promoted automatically.

**Budget:** known v5 cost 2.6571634 USD; known cumulative 6.1024322 USD; unknown reservations
0.349960 USD; conservative commitment 6.4523922 USD out of 10 USD.

## 2026-10-13 — controlled composition and v4/v5 cross-audit

**Goal:** materialise the v4 + targeted review composition without manual editing, then
prevent its use for scoring while omissions or clearly doubtful associations remain.

**Implementation:** `composition.py` and the offline `compose` command. Baseline and
candidate must cover exactly the 100 articles. Every review overlay must be `completed`,
reference the baseline hash, have the same ids in its classifications and change report,
and keep no unresolved reliable alert. Output keeps provenance per article, compares
tickers and labels and separates blocking and advisory alerts. Registry
`entity-aliases-v5`: CNBC/NBC News → CMCSA, CBS/CBS News → PSKY, Barron's → NWSA and
Kenworth → PCAR; `X → XYZ` and `SpaceX → XOM` forbidden.

**Run:** `python -m aie2609 compose --news news.json --universe sp500.csv --baseline
output/full-100-v4/classifications.json --review-dir output/full-100-targeted-review
--candidate output/full-100-v5-final/classifications.json --output-dir
output/composition-audit-v3`. No key, no network call.

**Result:** 100 articles, 225 pairs, `ready_for_scoring=false`. Seven blocking alerts on six
articles: CMCSA/N030, CMCSA/N047, CMCSA-PSKY/N048, CMCSA/N061, NWSA/N066 and the false
XOM/N100. The v5 candidate has fifteen blocking alerts and 29 disagreements.

**Check:** **79 tests pass**; `compileall` passes. No API call.

## 2026-10-13 — strict resolution of the six blocking alerts

**Decision:** a first review of the six articles (0.1741450 USD) found all the sources but
also changed GS/MS in N047, AMZN in N048 and removed SCHW/N066. Structurally valid but
rejected as an overlay: none of these changes was part of the coverage need.

**Hardening:** `review --ids` allows an explicit selection validated against the initial
file. `review --additions-only` extends the prompt and, above all, makes Python reject any
removal or label change, including from the cache. `compose` recomputes each diff and checks
that it matches `review_changes.json` exactly, and enforces the additions-only contract.

**Run:** compliant answers for N030/N047/N048/N061 replayed from the cache in
`output/composition-additions-review-4`. N066 needed two bounded calls and 0.0105296 USD
before keeping SCHW and adding NWSA. N100 isolated in `output/composition-n100-review-cached`:
zero new calls, XOM removed only. An earlier N100 attempt hit a network error before
measurable usage; its 0.179378 USD reservation stays unknown. The interrupted additions-only
run cost 0.1467906 USD.

**Result:** `output/composition-final-v2/` is reproducible and `ready_for_scoring=true`:
100 articles, 230 pairs, zero blocking alerts. Exact differences from the previous
composition: CMCSA/N030, CMCSA/N047, CMCSA-PSKY/N048, CMCSA/N061, NWSA/N066 added, all
neutral; XOM/N100 removed; no label change.

**Check:** **81 tests pass**. Additional known cost of the phase 0.3314652 USD. Cumulative:
6.4338974 USD known + 0.529338 USD reserved/unknown = 6.9632354 USD.

## 2026-10-13 — time-decay scoring and CSV generation

**Goal:** turn only the approved composition into the deliverables, without key or network.
`composition_report.json` now contains the hash of the composed JSON; `export` refuses a
report that is not ready or a different hash.

**Implementation:** `scoring.py`, version `time-decay-v1`, and the `export` command. Dates
converted to UTC before subtracting from `2026-09-29T00:00` New York. Weight
`0.5 ** (days / 7)`, labels `+1/0/-1`, `math.fsum` for stable summation. A future date is
refused. UTF-8 CSV files written atomically, sorted, with the exact columns.

**Run:** deterministic regeneration in `output/composition-final-v3/`, then `export
--composition-dir output/composition-final-v3 --output-dir output/final-results-v1`: 100
articles, 230 rows in `entities.csv`, 111 tickers in `scores.csv`, 26 zero scores.

**Check:** **86 tests pass**: weights at 0, 7 and 14 days, half a week, the switch to summer
time measured as 23 real hours, exact cancellation, a neutral-only company, a future date and
the export contract. No API cost.

## 2026-10-13 — human sample of the disagreements

**Goal:** make the open semantic differences visible and allow a simple human evaluation,
without automatically promoting v4 or v5.

**Implementation:** `evaluation.py` and the offline commands `prepare-evaluation` and
`evaluate`. A presence difference becomes the label `absent`; accepted decisions are
`positive`, `neutral`, `negative`, `absent` and `uncertain`. Article-derived cells are
protected against formula execution in a spreadsheet.

**Artifacts:** `review/human-evaluation-v1/disagreements.csv` lists 39 differing decisions on
27 articles; `sample.csv` holds ten varied cases. **88 tests pass**.

## 2026-10-14 — audit and end-to-end command

**Audit finding (Claude Code, at the user's request):** the assignment requires a command the
evaluators can run. The pipeline needed `classify`, `review`, `compose` and `export` chained by
hand; simulating the current code offline, the composition of the v5 pass carried 15 blocking
alerts and `export` refused to write the CSV files. None of the 100 requests of the active
prompt was in the local cache (key differs: 4,096 output tokens instead of 1,024). The
delivered CSV files came from prompt v4, no longer in the code, plus hand-selected overlays.

**Implementation:** `pipeline.py` and the `run` command, reusing the existing steps, each in
its own subdirectory. Only articles with a blocking alert are reviewed, with a mode per cause:
`additions-only` for a missing reliable alias, targeted review for a forbidden alias. A review
that is invalid or leaves a reliable hint unresolved is rejected and the first pass is kept.
`export_scores(allow_alerts=True)` lets `run` alone write the CSV files with
`ready_for_scoring: false`; `export` stays strict.

**Check:** **92 tests pass**. Offline rehearsal on the 100 real articles with a fake client
replaying the v5 answers: the 15 known blocking alerts are reviewed in the right mode and
composition and export complete. `run` without `--max-cost-usd` is refused. No API call.

## 2026-10-14 — real end-to-end run

**Command:** `python -m aie2609 run --max-cost-usd 4 --output-dir output/run-final-v1`, with a
budget explicitly granted by the user.

**Result:** `completed`, exit code 0. Classification: 101 calls for 100 articles (one invalid
N064 answer refused then asked again), 2.6307188 USD. Thirteen articles had a blocking alert:
twelve omissions reviewed in `additions-only` mode and one false XYZ in N100 in targeted mode;
all applied, 0.3880509 USD. Zero blocking alerts. 232 pairs (63 positive, 119 neutral, 50
negative), 112 tickers. Total: 114 calls, **3.0187697 USD, i.e. 0.030187697 USD per article**,
no local cache, no unknown cost. Independent checks: exact headers, no ticker outside the
universe, no duplicate, scores recomputed with a maximum difference of 0.0.

**Comparison with `final-results-v1`:** 19 pairs differ, mostly incidental peer moves made
neutral by the v5 rule. On the user's ten-case sample, `run-final-v1` agrees 4/10 against 8/10
for the old composition; that sample was drawn from v4/v5 disagreements.

**Budget:** known cumulative 9.4526671 USD; conservative commitment 9.9820051 USD.

## 2026-10-14 — LLM usage visibility

**Done:** `summarize_usage` and `format_usage` in `usage.py`; offline command
`usage --run-dir`; `run_report.json` now holds tokens and cost per category and per step;
`run` prints that summary; a warning appears when results come from the local cache.

**Check:** **93 tests pass**. `usage` on `output/run-final-v1`: 114 calls, 1 retry, 1,615,380
input tokens (579,371 cache reads, 1,035,667 cache writes, 342 ordinary), 26,087 output,
3.0187697 USD. The categories add up to the recorded cost. 86 % of the cost is provider cache
writes.

## 2026-10-14 — CLAUDE.md and prompt v6 with roles

**CLAUDE.md:** Claude Code context that imports `AGENTS.md` (`@AGENTS.md`) instead of
duplicating it and adds what cannot be inferred from the code: what to read when, exact
commands of the Windows environment, Git off PATH with a different owner, traps already paid
for, and the definition of done.

**Prompt v6:** `entity-sentiment-v6-roles`, `role` field, strict schema with two `anyOf`
branches and `$defs` for the ticker enumeration, `require_role=True` for live answers (older
artifacts without a role stay readable). Registry `entity-aliases-v6` adds Xbox → MSFT, Citi →
C, KeyBanc → KEY, Truist → TFC and Visible Alpha → SPGI. **95 tests pass**.

## 2026-10-14 — v6 pilot, N064 failure, vote and reference

**Budget:** the user authorises up to 100 USD in total for the project.

**v6 pilot:** `classify --ids N039 N047 N058 N091 N095 --max-cost-usd 1 --output-dir
output/pilot-v6-roles`: 5 calls, 0.1532555 USD, no invalid answer; the `anyOf`/`$defs` schema is
accepted by the API.

**Single-pass v6 run:** `run --max-cost-usd 6 --output-dir output/run-v6-roles` stopped in a
controlled way at `classify` after 63 articles and 1.5984818 USD: N064 cited a non-exact excerpt
twice; the validator refused it and no result was invented.

**Fixes:** a rejected attempt is retried with the validator's fixed reason
(`with_validation_feedback`, never the rejected text). `--passes 3` adds independent passes
through cache replicas and a strict majority vote. `prepare-reference` and `score-reference`
build a blind reference and estimate accuracy per version. **100 tests pass.**

## 2026-10-14 — three-pass v6 run and reference

**Command:** `run --passes 3 --max-attempts 3 --max-cost-usd 15 --output-dir
output/run-v6-vote3`. `completed`, zero blocking alerts, 233 pairs (61 positive, 117 neutral,
55 negative), 112 tickers. 278 calls, 5 retries, 65 answers replayed from the local cache.
N064 refused once then validated thanks to the feedback. Run cost 2.9692577 USD.

**Cost:** passes 2 and 3 cost about 0.006 USD per article against 0.026 for a cold pass,
because the common prefix (instructions, universe and schema, ~14,000 tokens) is read from the
provider cache. Estimated cold cost of three passes: about 0.045 USD per article.

**Stability:** 224 of 239 pairs identical across the three passes (93.7 %). Vote: 224
unanimous, 9 majority, 0 ties, 6 pairs proposed by a single pass and dropped.

**Reference:** six versions (manual, run-final-v1, the three v6 passes and the vote): 239
pairs, 203 unanimous, 36 disputed, plus 25 random checks of the consensus, i.e. 61 cases in
`review/reference-v1/`.

**Budget:** known cumulative 14.1736621 USD + 0.529338 USD of old unknown reservations =
14.7030001 USD out of the 100 USD authorised.

## 2026-10-14 — adjudication and choice of the delivered version

**Adjudication:** the user asked the agent to adjudicate the 61 cases rather than doing it by
hand. Decisions and limits in `review/reference-v1/README.md`: adjudicator Claude, not a human;
the assignment's definitions; `key.json` opened only after scoring; some labels already seen in
conversation; 21 decisions marked debatable. The user read the reasoning of several debatable
cases and approved the set.

**Score:** estimated accuracy manual 0.878, run-final-v1 0.907, v6 passes 0.920 to 0.924,
**v6-vote3 0.933**. The ranking holds without the debatable cases (9, 17, 16–17 and 19 of 20).
Consensus checks: 24 of 25.

**Decision:** deliver `output/run-v6-vote3/final/`. `run` defaults to this configuration
(`--passes 3`, `--max-attempts 3`). Independent check of the delivered CSV files: exact
headers, 233 rows, no ticker outside the universe, no duplicate, scores recomputed with a
difference of 0.0, manifest `completed` and `ready_for_scoring=true`. **100 tests pass.**

## 2026-10-14 — repository publication

**Request:** public GitHub repository without the supplied data, author "Son".

**Preparation:** `results/` holds exact copies of the CSV files and manifests of
`output/run-v6-vote3` (SHA-256 identical to the manifest). Excluded by `.gitignore`: the
confidential PDF, `news.json`, `sp500.csv` and the four review files quoting article text.
The 8 tests that read the real data are skipped, and reported as such, when it is absent.
Search for secrets and personal paths before committing: no real value found. Author set in
the local repository only, not globally.

**Check:** clean clone: 69 files, no PDF, data or `.env`; code loaded from the clone; 92 tests
pass and 8 are skipped. Pushed to `https://github.com/sonalain077/Whitehole_project`; the remote
commit is identical to the local one.

## 2026-10-14 — agent files and a shorter entry point

**Request:** make `AGENTS.md` and `CLAUDE.md` follow the usual conventions and state clearly
that the project was started with Codex under `AGENTS.md`, then taken over by Claude Code with
a fresh context acting as a second opinion (reviewer of Codex's work, judge of the model's
outputs); make the repository understandable in about 15 minutes.

**Done:** `AGENTS.md` condensed into the standard sections (project, setup and commands,
rules, model and budget, code and tests, security, working loop) without changing its intent.
`CLAUDE.md` imports it and states Claude Code's role, what to read on demand, environment,
commands, known traps and the definition of done. `README.md` reduced to what it does, how to
run it, results, how it works and a repository map. `ARCHITECTURE.md` now opens with a Mermaid
diagram of the pipeline and ends with a diagram of how the project was built with the two
agents. `IMPLEMENTATION_PLAN.md` reduced to the batch table (with the agent of each batch),
the main decisions and the budget; the detailed history stays in this log.

## 2026-10-14 — progress output during a run

**Finding (user):** a full run printed nothing for about 25 minutes, only the final summary.

**Done:** a progress log on stderr through the `aie2609` logger, enabled by the CLI for `run`,
`classify` and `review`: one line per classified article (pass, position, id, number of
companies, local cache or number of calls, cost of the step so far), the number of flagged
articles, one line per targeted review (alerts, status, added and removed tickers), warnings
for rejected answers and rate-limit retries, the vote counts and the export counts. Ids, steps,
statuses and costs only, never article text or the key. The package installs a `NullHandler`, so
tests and library use stay silent. **101 tests pass** (new test: progress lines present,
article text absent).

**Check:** `run --max-cost-usd 10 --output-dir output/log-demo` replayed from the local cache:
404 progress lines, 337 cached answers and 2 real calls (0.0478937 USD). The pass-1 review of
N066 had been rejected after three attempts in `run-v6-vote3`, so nothing was cached; this time
it was accepted on its second attempt. The vote moved by one pair (225 unanimous, 8 majority)
but `entities.csv` is identical to `results/entities.csv`.

**Incident:** while preparing a clean clone for the user, a relative path resolved against the
project instead of the clone, and the project's `.venv` was re-pointed to the clone's `src`. It
was found when a new test could not see the new code, and fixed by reinstalling the project in
editable mode; no file of the project was affected.

## Format of the next entries

For each batch: goal; changes; decisions and useful alternatives; verification commands actually
run and their results; limits; next step. Record every prompt change and its reason. Never store
a key, a raw API answer or a long copy of an article here.
