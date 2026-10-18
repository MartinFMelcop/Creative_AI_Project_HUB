# Three-brain consultation library

The five supplied documents below retain their exact attachment bytes. They are
durable knowledge sources, not agents, executable instructions, experiment logs
or evidence that a model has been trained. Specific author authorization is
required to change them; ordinary implementation commits must not rewrite or
automatically regenerate them.

| Source | Role | Chapters |
|---|---|---:|
| [Engineering Brain](ENGINEERING_BRAIN.md) | Requirements, architecture, trade-offs, reliability and technical evaluation | 49 |
| [Scientific Brain](SCIENTIFIC_BRAIN.md) | Questions, competing hypotheses, experiments, uncertainty and validity | 85 |
| [Creative Brain](CREATIVE_BRAIN.md) | Virgo Diamond's character fantasy, world, classes, narrative, art and audio | 100 |
| [Consultation catalog](CATALOGO_DE_CONSULTA.json) | Supplied chapter IDs, titles, questions and editorial categories | 234 entries |
| [Collection index](BIBLIOTECA_DE_CONHECIMENTO_APLICADO.md) | Source selection and interpretation conventions | — |

[integrity.json](integrity.json) pins each original file's byte count and SHA-256.
The checker reads these pins; it never repairs sources or updates the pins.
The README, pins and consultation tool are operational wrappers outside the five
protected documents. Historical sources remain in `references/`; contextual,
revisable findings remain in `knowledge/`.

## Selective activation before improvements

Consider engineering, science and creation for every task, including low relevance.
Read current work state and use `overview` when domain orientation is needed; it
returns supplied volume/part names and counts, without inventing summaries. Reuse a
current overview while source identity is unchanged. Known chapter IDs go directly
to `get`; do not search or emit detailed indices to rediscover them. Retrieve complete
pertinent chapters, apply their principles to alternatives/risks/checks, and briefly
record IDs and practical consequences. Trivial tasks need no separate activation report.

Current user decisions, platform safety and authorization prevail. Preserve D/A/H/E/V:
a located chapter, detailed proposal or lexical match is not truth, approved canon,
implemented behavior or independent validation. The collection does not train a model.

## Local deterministic consultation

From the maintained laboratory directory, using Python's standard library:

```bash
python3 tools/brain_query.py overview
python3 tools/brain_query.py search 'classes especializações' --metadata-only
python3 tools/brain_query.py search 'avatar customization' --metadata-only --relaxed
python3 tools/brain_query.py get CRE-009 CRE-010
python3 tools/brain_query.py check
# Full catalog and legacy full-chapter search remain available:
python3 tools/brain_query.py indexes
python3 tools/brain_query.py search 'proveniência'
python3 tools/test_brain_query.py
```

All commands validate the same five source pins, catalog and links before returning
anything. `get` retains complete byte-faithful chapter text after UTF-8 decoding,
with original question/status, section, anchors and line ranges. Discovery is not a
substitute for reading that content. Known ID lookup does not depend on vocabulary.
Inherited fragment differences remain visible in `check` and source locations.

### Compatibility and search boundaries

- **Default search:** unchanged all-significant-term matching in supplied title,
  question, section and preview; original stop words, weights, catalog tie order,
  full content and JSON shape remain. Case/accents are ignored. No expansion.
- **`--metadata-only`:** projects those same results to ID/title/question/domain,
  original editorial status and source location, score and match kind. It omits full
  content and preview. This flag controls output; it does not independently relax search.
- **`--relaxed`:** opt-in exploratory retrieval using the versioned operational
  [vocabulary](../tools/brain_vocabulary.json), outside the protected sources. Explicit
  inflections/translations use strength 80, literal terms 100 and directed related terms
  30. It does not stem arbitrary words, correct typos or call a remote service.

Relaxed matching weights title/question/preview by 10/5/1, sums each field's best
match, and uses low-weight source text only when the metadata has no match for that
term. The reason names `content` for this fallback, without emitting the body.
Character/player context contributes half weight but is not a mandatory anchor when
other terms exist. Unknown significant terms remain mandatory literal constraints.
Two-anchor queries require both; longer queries need at least two thirds of anchors.
Ranking uses coverage, weighted score, match strength and supplied catalog order.

`match` distinguishes `exact_id`, `literal_all` (all anchors, not exact sentence meaning),
`expanded_all`, `related` and `partial`; reasons name normalized source terms/fields and
unmatched anchors. It reports ignored function words, optional context and uninterpreted
qualifiers such as "only". It does not infer exclusion, negation, intent or an answer
from word co-occurrence. Twelve or more eligible candidates trigger a heuristic `broad`
warning before limiting output; scores/warnings are not calibrated probabilities or
human relevance judgments. Read the source and refine ambiguous queries.

Relaxed queries are bounded to 4,096 characters and 64 distinct terms. The small
vocabulary is incomplete and domain-specific; source-only fallback can increase recall
and unrelated co-occurrences. It must not silently discard unknown words to manufacture
a match. Missing matches stay visible. Full catalog inspection remains appropriate
when deliberate broad coverage is needed. No matches returns `[]` with status 0;
invalid input or corrupt sources returns an English stderr error and status 2.

### Reproduce the retrieval evaluation

```bash
python3 tools/benchmark_brain_query.py --output /tmp/brain-retrieval.json
```

The [cases](../tools/brain_retrieval_cases.json) identify the preserved Git baseline
and small, implementing-agent-curated targets. The runner executes actual old/current
CLIs, compares unchanged legacy output (including all 234 complete chapters), tests
negative/malformed/corruption controls and records candidate IDs and UTF-8 stdout bytes.
It names a source commit only when all measured implementation files match that commit;
uncommitted work is identified by hashes with a null revision. Missing history fails
clearly; CI's integrity job already obtains full history. It never fetches implicitly.
`--compare` can require exact recorded identities/results before writing new output.

Output bytes include JSON formatting; they are not measured Codex tokens, billing,
agent productivity or human relevance. No comparable Codex session telemetry is
collected. Full source validation still occurs on compact commands; no latency gain
is claimed. Keep raw benchmark output/transcripts off the public tree and publish
only the small summary needed to reproduce or contest the result.

## Integrity findings and limits

The supplied catalog and internal links use collapsed heading fragments. Some
headings containing an em dash produce double hyphens in GitHub-style fragments,
while their supplied links use one. `check` explicitly lists 44 inherited link
occurrences across 26 affected headings as `source_warnings`; unrecognized local
targets are errors. All 234 chapter records and 422 local links are inspected.
The sources remain unchanged because no integrity correction was authorized.
Use the returned file/line range or `source_fragment` to reach these chapters.
No claim is made that these inherited links were repaired.

Checks cover UTF-8, original hashes/sizes, complete sequential chapter numbering,
catalog IDs/titles/parts/questions/editorial categories/anchors and local Markdown
targets. Remote citations are not fetched. Hashes and structural consistency do
not establish scientific accuracy, rights in cited works, creative canon,
independent validation or implemented gameplay.
