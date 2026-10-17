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

## Lightweight activation before improvements

1. Read all three indices and the current work state.
2. Classify engineering, science and creative relevance, including low relevance.
3. Retrieve only the complete chapters pertinent to the question.
4. Apply their useful principles to alternatives, assumptions, risks and checks.
5. Record the IDs and practical consequence briefly in the affected decision or
   evidence. A trivial task needs no standalone activation report.

Current user decisions, platform safety and authorization prevail. Preserve the
Creative Brain's distinction between direct author decisions, documented
directions, hypotheses and actual validated results. An index entry, an old
source or a general recommendation does not supersede current specific evidence.

## Local deterministic consultation

From the maintained laboratory directory, using Python's standard library:

```bash
python3 tools/brain_query.py check
python3 tools/brain_query.py indexes
python3 tools/brain_query.py get ENG-027 SCI-004 CRE-008
python3 tools/brain_query.py search 'proveniência'
python3 tools/brain_query.py search 'Como preservar dados de modo que possam ser localizados, compreendidos e reutilizados?'
python3 tools/test_brain_query.py
```

Each retrieval returns the original chapter text, file, part, heading, line range,
catalog anchor and source heading fragment. Search matches IDs, titles, questions,
parts and supplied previews; it requires every meaningful query term, ignores
case/diacritics, and breaks equal scores by supplied catalog order. It does not
invent synonyms, search the web or claim semantic understanding. No matches is
an empty JSON list with exit status 0. Invalid input or an inconsistent collection
has an English error on stderr and exit status 2. All commands validate the same
source pins and structure before returning results.

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
