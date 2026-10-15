# P04 0.3.0 — bounded source comparison and revision

**Date:** 2026-10-15. **Reviewer/editor:** Codex under Martin Melcop Neto's
portfolio direction. This note records implementing-agent reading judgments,
not independent reader feedback or canon approval.

The audience is readers of a complete short story. They should be able to follow
the rescue, see Sava affect what happens to her brother's body, and understand
what Baldino admits afterward. The revision retains the story's separate
adaptation identity rather than making it conform to the recovered books.

## Actual source and limits

The sampled source is Book I, *O Mundo Depois da Tumba*, in collection
`REF-LICH-MAIN-PDFS`:

- [Original PDF](../../references/literature/lich/snapshots/main-pdfs-2ccc075083f1/source/01_O_Mundo_Depois_da_Tumba.pdf), SHA-256
  `5a5e9ca5c259fed8a2c8431d73ee8224e87c52aa99ac8a26ff82a8d78f40afb1`.
- [Preserved searchable text](../../references/literature/lich/snapshots/main-pdfs-2ccc075083f1/text/01_O_Mundo_Depois_da_Tumba.txt), SHA-256
  `99dffb3dfce7072c8c1f7faf2a7becbaba4101908836b8151591f9c187d51784`.

The PDF title page declares v0.2.87; metadata declares v0.2.88 and a noncanonical
legacy draft. Neither establishes current literary authority. The original ZIP,
editable historical manuscripts and authority policy remain unavailable. These
pages do not supersede later historical decisions or establish North Star canon.
The [library guide](../../references/literature/lich/README.md) preserves those
version boundaries.

Page numbers below are **1-based physical PDF pages**, including cover/front
matter. Actual `pdftotext -f FIRST -l LAST -enc UTF-8 -eol unix` extractions for
4–7, 116–119 and 137–141 match the corresponding preserved derivative bytes.
Only these passages were selected for this comparison; no collection-wide
continuity or literary review is claimed.

| Physical pages | Observed passage | Decision for the adaptation |
|---|---|---|
| 4–7 | Baldino maintains floor 73, has existed for centuries and does not need ordinary bodily sustenance. | Keep P04's living narrator, daughter, injury and culpability. Their difference is deliberate; importing undead longevity would change this story's conflict. |
| 116–119 | Orvek bargains over payment and repair, tests the bridge and stops Aevren using magic that could loosen its brace. | Let practical expertise determine action. Clarify the waterworks' distinct supports and moving parts; do not import Orvek, the bridge or its dialogue. |
| 137–138 | Garran rejects magical intervention; Aevren withdraws instead of continuing to argue for it. | Give refusal an observable consequence before a new proposal. Sava's emergency remains different: the later permission is pressured, limited and uneasy. |
| 140–141 | Darsen's furnishings/clothes accommodate different bodies; old structures have acquired current uses. | Retain a civic setting expressed through work and access. These pages do not require replacing P04's local Saelir workers or adopting the source's population history. |

## Alternatives and selected scope

A source-alignment rewrite would replace the living Baldino/Tila relationship,
embodied risks and much of the local premise. Expanding lore or flashbacks would
interrupt the single night's pressure. Merely explaining the mechanism more
would leave the dramatic decision unchanged. The selected approach revises the
existing rescue and aftermath in both languages, primarily scenes 3–5, retaining
five complete scenes and the final shared testimony.

## Before and after: editorial assessment

| Baseline weakness | Revised behavior on the page | Remaining question |
|---|---|---|
| Sava says no, then moves to permission through mechanical questions; refusal causes no change of plan. | Nera starts evacuation/upstream closure, Aevren packs papers and Sava unties the rope. Sava herself reopens the rescue under explicit limits, including stopping and returning Lesto before boxes. | Does the intervening action make her decision legible without implying free, uncomplicated consent? |
| The original operating beam and the spare rope support share the same name amid repeated pulls and slips. | An iron operating lever aligns the chain; a wooden brace carries ropes. Brake, contact, misalignment and release remain separate causes. | Can a reader follow the climax without rereading? The scene still demands spatial attention. |
| The ending moves to three days later and then back to the first afternoon without a transition. Baldino's final account begins with the body's later injury. | Morning, afternoon and next-day preparation now follow in order. At the family gathering Baldino names his falsified repair before describing the brake. | Does this admission preserve discomfort without sounding like absolution? |

Codex's assessment is that changed actions now carry the disagreement, physical
nouns better support the tension, and the final encounter exposes Baldino's
responsibility more directly. The story preserves Sava's earlier stop/resume
instruction, Aevren's dangerous distraction by his papers, bodily damage and
loss. Lesto does not speak or return to life. Sitting beside Sava is participation
in an unfinished account, not forgiveness.

The PT/EN revision retains the opening incident, new cast and local rules.
Earlier Portuguese 0.1.0 and English 0.2.0 reading files remain separate historical
artifacts. [Revision execution](../../evidence/lich-cistern/REVISION_RUN.json)
records the technical before/after evidence; matching paragraphs, valid files
and agent review cannot establish reader comprehension or literary excellence.
