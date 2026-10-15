# P04 — A água sob Darsen

**0.3.0.** A complete five-scene dark-fantasy story in Portuguese and English.
Baldino has diverted water to his daughter and falsified maintenance records.
A dead inspector, a failing cistern and an emergency use of the body expose
the cost. The operation ends; grief, injury and accountability remain.

## Read

| Language | Reading files | Editable manuscript |
|---|---|---|
| Portuguese — *A água sob Darsen* | [EPUB 3](dist/a-agua-sob-darsen-0.3.0.epub) · [A5 PDF](dist/a-agua-sob-darsen-0.3.0.pdf) | [story.md](story.md) |
| English — *The Water Beneath Darsen* | [EPUB 3](dist/the-water-beneath-darsen-0.3.0.epub) · [A5 PDF](dist/the-water-beneath-darsen-0.3.0.pdf) | [story.en.md](story.en.md) |

Download EPUB/PDF files before opening them in a reader; GitHub's source page is
not an ebook reader. The downloaded books need no repository, account or service.
EPUBs provide chapter navigation and language metadata. PDFs provide linked
contents, chapter bookmarks and embedded licensed DejaVu Serif fonts. Each PDF
scene keeps its final three paragraphs together.

The revision makes Sava's initial refusal change the rescue plan before she
proposes limited use of her brother's body. It distinguishes the iron operating
lever from the wooden rope support, keeps the aftermath in chronological order
and makes Baldino acknowledge the falsified repair to Lesto's family. Both
languages carry the complete revised story.

Earlier reading editions remain available: Portuguese 0.1.0
[EPUB](dist/a-agua-sob-darsen-0.1.0.epub) / [PDF](dist/a-agua-sob-darsen-0.1.0.pdf),
and English 0.2.0 [EPUB](dist/the-water-beneath-darsen-0.2.0.epub) /
[PDF](dist/the-water-beneath-darsen-0.2.0.pdf). They contain the earlier text;
the current producer builds 0.3.0 from the maintained manuscripts.

## Creative scope and sources

This is a standalone adaptation, **not restored B01 or ratified canon**. Codex
wrote the original story from the maintained P04 seed under Martin Melcop Neto's
portfolio direction, before historical manuscripts were available. Codex also
translated and revised it; no independent reader, translator or authorial canon
approval is claimed.

The recovered [literary library](../../references/literature/lich/README.md) now
contains ten main-book and eight OVA PDFs. Revision 0.3.0 compares selected actual
Book I passages, with source hashes and physical pages in
[Source comparison](SOURCE_COMPARISON.md). This is a bounded craft comparison,
not a review of the whole collection. Conflicting historical version labels and
the unavailable authority policy remain unresolved.

Baldino remains alive and responsible for his choices in this adaptation.
Sava, Nera, Lesto, Eno, Tila, the waterworks and their incident are new. Movement
of a corpse requires contact and intact tissue; it supplies no answer from Lesto,
resurrection or repair of broken joints. Sava's permission remains constrained
by the emergency. Archive recovery does not replace these adaptation decisions
or make the story North Star canon.

[Provenance](provenance.json) records origins, translation decisions and artifact
identity. No external story, illustration or audio was imported. Included font
files retain their [license](fonts/LICENSE.txt); the PDF includes its notices.

## Build and verify

The tested production stack is Python 3.12, Pandoc **3.1.11.1** and ReportLab
**4.4.9**. Poppler provides `pdftotext`, `pdfinfo` and `pdffonts`. Font sources
are included. From this directory:

```sh
python3 tools/build.py --edition all
python3 tools/check_editions.py --edition all
# Rebuild without replacing delivered files:
python3 tools/build.py --edition all --out /tmp/darsen-editions
python3 tools/check_editions.py --edition all --dist /tmp/darsen-editions
```

The checker compares every narrative heading/paragraph in the manuscripts,
EPUB spine and extracted PDF, plus metadata, navigation and font properties.
These are format/content checks, not semantic translation or literary proof.
Container timestamps/IDs are not a byte-reproducible build contract.

[Revision execution](../../evidence/lich-cistern/REVISION_RUN.json) identifies the
baseline, actual revised artifacts, executed checks and review limits. Official
EPUBCheck 5.4.0 is configured in CI; the local download proxy was unavailable for
this revision. Consult the associated commit’s CI for its official conformance result.
Earlier [Portuguese](../../evidence/lich-cistern/RUN.json) and
[English](../../evidence/lich-cistern/ENGLISH_RUN.json) records concern their
original editions, including their recorded official EPUBCheck runs.

## Review limits

The source comparison and before/after reading assessment are Codex judgments.
Text identity and valid formats do not establish literary quality or independent
semantic approval. PDFs remain untagged; assistive technology, hardware ebook
readers, reader response and commercial demand remain unverified. No North Star
runtime consumer exists.

Next observe independent Portuguese/English readers following the mechanism,
Sava's changed decision and Baldino's final testimony. Compare those findings
with other portfolio needs before choosing another milestone.
