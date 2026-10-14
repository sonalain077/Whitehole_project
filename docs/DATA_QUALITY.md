# Data quality report

Read-only inspection on 12 October 2026 with PowerShell and Node, without the API, then
confirmed by the Python audit (`python -m aie2609 audit`) and completed on 14 October.

| Check | Observed result | What the pipeline does |
| --- | --- | --- |
| Articles | 100 | Generic loader, no hard-coded count |
| Fields | `id`, `date`, `headline`, `body` everywhere | Missing or non-string fields are rejected; extra fields are reported and ignored |
| Duplicate ids or JSON keys | None | Rejected if present |
| Date format | 100 match `YYYY-MM-DDTHH:MM` | Strict pattern; ambiguous or nonexistent New York times and dates after `as_of` are rejected |
| Date range | 2026-08-25T06:53 to 2026-09-28T16:20 | Elapsed time measured in UTC |
| Reference rows | 503 rows, 11 sectors, no duplicate symbol | Duplicates and malformed rows rejected |
| Dual share classes | `GOOGL/GOOG`, `FOXA/FOX`, `NWSA/NWS`, plus `BRK.B` | Canonicalised to 500 companies; one row per company per article |
| Identical content after normalisation | None | Repeated content would be reported, never silently merged |
| Replacement character U+FFFD | None in the articles | — |
| Zero-width space U+200B | 6 in N027 and 10 in N100, splitting the name "Tesla" and the ticker | Removed from the in-memory copy and reported by the audit |
| Cyrillic look-alike letters | N003 and N098 write "Tesla" with Cyrillic Т, е, ѕ and а | Not normalised (no arbitrary transliteration); the model recognises Tesla from context and the coverage alert flags the missing lexical anchor; TSLA is found in every run |
| Non-ASCII names in the reference file | `Brown–Forman` (en dash), `Estée Lauder` | Kept as is |
| Companies named by their brand or publication | Waymo, YouTube, The Wall Street Journal, CNN, CNBC, iShares, SPDR, Xbox, KeyBanc, Visible Alpha… | Model maps to the parent; `entity_aliases.json` triggers a review if a known alias is missing |
| Words that are also ticker names | "Target", "Block", "Southern", "X" (social network), index "Nasdaq" | Short generic names are excluded from lexical hints; `X → XYZ` and `SpaceX → XOM` are forbidden associations |

In N027 and N100, U+200B splits the Tesla name and/or the TSLA ticker: a plain lexical
match would miss these entities. The look-alike Unicode letters in N003 and N098 are a
case a production pipeline should flag explicitly; the current audit reports only
U+200B, which is a known limit.

## SHA-256 of the sources

```text
AIE2609_Project.pdf
8bafe85dc0e06eaf59f4be17d45fc6c6d126b3f5f49818522f03a541bb157195

news.json
2bd735fcee63c39d6a41c7a07764bd09b9199d3eeedda951b2546fb94ebc6354

sp500.csv
ce3136f433a6bd493a0c5b7a4d1e18e40f58f5fdf13bf989402cc6e0bffb7b7c
```

These hashes let anyone check that the inputs did not change; every run manifest
records them too.
