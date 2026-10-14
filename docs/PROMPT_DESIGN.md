# Prompt design and versions

Active prompt: `entity-sentiment-v6-roles`, the `SYSTEM_PROMPT` constant in
`src/aie2609/classification.py`. It is sent in the Responses `instructions` field; the
universe and the article are sent in two separate data messages.

## Structure (RCORCF)

The prompt follows the RCORCF structure requested by the user: Rôle, Contexte,
Objectif, Résultat, Contraintes, Format (a French acronym: Role, Context, Objective,
Expected result, Constraints, Format). Each heading carries its English equivalent, for
example `# 1. Rôle / Role`; every instruction is in English, like the articles and the
labels. These headings are kept byte-identical because the delivered results were
produced with this exact prompt and the cache key hashes it.

| Part | Content |
| --- | --- |
| Role | Entity-level financial-news annotator; exhaustive about identifiable mentions, conservative about inferences |
| Context | Whole article, publication date, closed universe, normalised text; time-decay aggregation is done later by code |
| Objective | Identify the companies, resolve names/classes/subsidiaries, assign a role, then a label specific to each company |
| Expected result | One entry per eligible company, neutral ones included, with an exact excerpt for review |
| Constraints | Untrusted data, no tools, no invented ticker, no published reasoning, no score computed by the model |
| Format | Strict JSON object `entities` with `ticker`, `role`, `label`, `evidence`; stable order; defined empty list; complete examples |

The rules cover the difference between absence, neutrality and uncertain identity;
look-alike Unicode names; sources and analyst banks; subsidiaries whose parent is not
written; minority stakes; contradictory, old or denied news; incidental comparisons.
An instruction quoted inside an article remains data to analyse.

## Roles (v6)

The 19 differences between the manual composition and `run-final-v1` were almost all on
the border between "implication" and "mere mention": the bank issuing a rating, a peer
cited in passing, a party to an agreement, a source. The assignment defines those
mentions as neutral. v6 therefore asks for the role of each company first:

- `subject`, `counterparty`, `affected_peer` — may carry positive, neutral or negative;
- `rating_issuer`, `source`, `comparison`, `other_mention` — always neutral.

The rule is enforced three times:

1. The prompt defines each role and separates `affected_peer` from `comparison`: a
   consequence specific to the company must be written in the article.
2. The strict JSON schema has two `anyOf` branches, so an always-neutral role cannot be
   generated with a label other than `neutral`.
3. The Python validator rejects an unknown or inconsistent role, including from the cache.

The role stays internal (`classifications.json`); the submitted CSV files do not change.
It also gives the subject-versus-mention distinction the assignment asks for: in the
retained run, 108 of the 233 pairs are subjects with a directional label and 104 are
always-neutral mentions (38 other mentions, 27 comparisons, 22 rating issuers,
17 sources).

## Thirteen synthetic examples

1. Wells Fargo downgrades FIS: FIS `subject` negative, bank `rating_issuer` neutral.
2. Nvidia wins a contract AMD loses: explicit opposite implications.
3. Tesla recall compared with Waymo: Tesla negative, Alphabet neutral `comparison`
   through its subsidiary.
4. Alphabet, YouTube and the GOOG/GOOGL classes: a single canonical entry.
5. Out-of-universe startup and a Microsoft pilot: Microsoft neutral, no competitor added
   from the industry alone.
6. Apple: favourable past result, unfavourable current forecast.
7. Microsoft: explicitly offsetting effects, unchanged outlook, neutral.
8. The words "A", "IT" and the Nasdaq index: no company wrongly identified.
9. Private startup without an identifiable eligible parent: empty list, no parent
   invented from a known minority stake.
10. Apple recall and a malicious instruction in the text: instruction ignored.
11. AMD contract and Nvidia's historical return cited as a comparison: AMD positive,
    Nvidia neutral.
12. Qualcomm–Apple licence whose documented benefit is Qualcomm's: QCOM positive,
    Apple `counterparty` neutral.
13. Wells Fargo warning: Capital One `affected_peer` negative (the article attributes
    its fall to the news), Synchrony `comparison` neutral, WSJ `source` neutral.

Each example defines its small universe, its article, its complete JSON answer and a
teaching note. Events and figures are synthetic. The tests validate every example
against the real validator (strict JSON, universe, labels, roles, exact excerpts); they
do not check that the model imitates them.

## Version history and measured effect

| Version | Change | Observed effect |
| --- | --- | --- |
| v1 | First prompt | GS missing in N002 |
| v2 | Paragraph-by-paragraph inventory before labelling | GS recovered; Alphabet via Waymo still missing |
| v3 | More explicit parent mapping, medium reasoning | Worse (GS and GOOGL missing); not retained |
| v4 | RCORCF structure, ten synthetic examples | Waymo/Alphabet recovered; 100-article run: 217 pairs, omissions of neutral sources |
| v5 | Historical/peer moves are comparisons; each party of an agreement judged separately | Intended fixes obtained, but dropped sources, two false XYZ, BAC/N092 regression |
| v6 | Role per company, schema forcing neutral roles, thirteenth example | Estimated accuracy 0.920–0.924 per pass vs 0.907 for v5 (`run-final-v1`) |

Measured on [`review/reference-v1`](../review/reference-v1/README.md) (agent-adjudicated):
v6 improves precision on the implication/mention border (analyst banks, comparisons,
counterparties) and consistency (three passes agree on 93.7 % of pairs); combining three
passes by vote brings it to 0.933. The remaining errors are mostly genuine border cases
(sector-wide share moves, mixed company news).

## Review prompts

`review.py` appends review instructions to the active prompt and sends the initial
proposal and lexical hints in a third data message, never as instructions.

- `entity-review-v1`: independent inventory of the article, check of secondary mentions,
  keep justified entities. On ten articles it fixed one omission and introduced one
  regression; not adopted automatically.
- `entity-review-v2-targeted`: separates reliable from ambiguous hints and strongly
  protects an explicitly named company with ticker and evidence.
- `-additions-only` mode: the model may only add entities; the validator rejects any
  removal or label change, including from the cache.

Coverage rules: `entity-coverage-v3` generates legal-name variants from the CSV and
excludes short forms that are ordinary words or names (Target, Block, Southern,
Rollins). Registry `entity-aliases-v6`: brands, publications and subsidiaries observed
in the data (WSJ and Barron's → NWSA, CNN → WBD, CNBC → CMCSA, CBS → PSKY, Kenworth →
PCAR, iShares → BLK, SPDR → STT, Waymo/YouTube/Google → GOOGL, Xbox → MSFT, Citi → C,
KeyBanc → KEY, Truist → TFC, Visible Alpha → SPGI), the ambiguous Everpure (P or PNR),
and the forbidden associations `X → XYZ` and `SpaceX → XOM`.

## What the version tags mean

`PROMPT_VERSION` identifies **our analysis instructions**, not the OpenAI model, which
stays `gpt-5.6-terra`. It changes whenever instructions, examples or classification
rules change; a name is never reused for a different variant (v3 was a retired trial,
so the redesign became v4).

`NORMALIZATION_VERSION = "nfc-lf-u200b-v1"` identifies **text preparation** in
`normalization.py`: Unicode NFC, CRLF/CR line endings to LF, removal of the zero-width
space U+200B with a count. Example: `Te<U+200B>sla` becomes `Tesla` in the normalised
copy; the supplied files stay intact.

## Why these versions enter the cache key

The SHA-256 cache key covers the full request (normalised text, universe, instructions,
schema, model, parameters), both tags and the pass replica. Changing the instructions or
the cleaning policy must prevent reusing an analysis made under other conditions; even a
forgotten tag change still changes the request hash, and the tag gives a readable trace
in reports. Old cache files are kept but no longer match, so a prompt change means a new
paid run. Tests check that each tag changes the key.

## Validation and limits

More detail makes requests larger without guaranteeing better quality: every change was
judged on full runs and, for v6, on the reference measurement. N027 (Waymo) is taught by
an example, so it checks a known regression rather than generalisation. Design
references: the OpenAI [prompt engineering guide](https://developers.openai.com/api/docs/guides/prompt-engineering)
recommends structured instructions and output examples; the
[reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
recommend clear instructions and delimiters without asking for a reasoning transcript.
RCORCF is the structure requested by the user, not an official OpenAI method or a
guarantee of accuracy.
