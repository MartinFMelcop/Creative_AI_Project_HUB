# P04 — A água sob Darsen

**0.2.0**. A complete dark-fantasy story in Portuguese and English, in five connected scenes.
Baldino has diverted water to his daughter and falsified maintenance records.
A dead inspector, a failing cistern and a forced visit to Aevren's tomb expose
the cost. Sava's grief/expertise and Nera's public-water duty change the response.
The physical operation ends; the death, injury and accountability remain.

## Read

**English — The Water Beneath Darsen**

- [EPUB 3](dist/the-water-beneath-darsen-0.2.0.epub): complete English translation, `en-US` metadata/document language, distinct identifier and chapter navigation.
- [A5 PDF](dist/the-water-beneath-darsen-0.2.0.pdf): 27 pages, linked contents/bookmarks, embedded licensed serif fonts and full notices.
- [English manuscript](story.en.md): all five scenes, aligned with the Portuguese paragraph sequence for comparison.

The English edition translates the actual current story, including Baldino’s
falsification, Sava’s constrained permission, the contact/joint limits, physical
operation and remaining consequences. Codex translated and reviewed it under
Martin’s direction; there is no independent translator/reader or canon approval.
[Translation choices](provenance.json) record waterworks terminology, the source’s
awkward guard/beam wording and the inferred shrouding term. Structural alignment
and text identity do not certify semantic fidelity or literary quality.

**Portuguese — A água sob Darsen, preserved 0.1.0**

- [Reflowable EPUB](dist/a-agua-sob-darsen-0.1.0.epub): EPUB 3, Portuguese language
  metadata and chapter navigation; use an EPUB reader that accepts local files.
- [A5 PDF](dist/a-agua-sob-darsen-0.1.0.pdf): 28 pages, chapter bookmarks, linked
  contents, embedded Unicode serif faces and complete font-license notices.
- [Editable manuscript](story.md): the same full narrative in Markdown.

Download the binary file from GitHub before opening it; the blob page is not an
ebook reader. Neither edition needs this repository, Python, an account or an
online service for reading. This is a standalone seed adaptation, **not B01
restoration or ratified canon**. No historical manuscript appears in the current
checkout/archive; its absence prevents comparison or revision of that manuscript.

## Creative scope and provenance

The maintained P04 seed supplies Baldino's narration, Aevren's reconstruction of
old knowledge and cosmopolitan Darsen. Sava/Nera/Lesto/Eno/Tila, local waterworks,
the incident and corpse-binding limits are newly written for this story. No year
or broader cosmology is asserted. Baldino survives and recounts witnessed events;
post-death narration or ghosts are not needed in this adaptation.

Corpse movement requires contact and intact tissue; broken joints remain broken.
It produces no answer from Lesto and supplies no resurrection. Sava allows limited
use under emergency pressure and insists on returning the body. That constrained
permission is part of the conflict, not a claim of uncomplicated consent.

Text and editorial review are by Codex under Martin's portfolio direction. Martin
has not supplied a reader review or canon approval for this story. [Provenance](provenance.json)
identifies source boundaries, new decisions and the real production files.
DejaVu Serif fonts are copied unchanged from the installed distribution under
their [license](fonts/LICENSE.txt); the PDF also includes its notices. The EPUB
uses the reader's fonts. No external story, illustration or audio was imported.

## Build and verify

Use Pandoc **3.1.11.1**, Python 3.12 and ReportLab **4.4.9** for the tested build;
Poppler supplies `pdftotext`, `pdfinfo` and `pdffonts` for checks. Font sources are
included. Install ReportLab in a suitable virtual environment if needed.

```bash
python3 tools/build.py
python3 tools/check_editions.py
# Produce or check the English edition explicitly:
python3 tools/build.py --edition en
python3 tools/check_editions.py --edition all
# Rebuild both languages without overwriting the delivered editions:
python3 tools/build.py --edition all --out /tmp/darsen-editions
python3 tools/check_editions.py --edition all --dist /tmp/darsen-editions
```

Official EPUBCheck **5.4.0** was downloaded to scratch and its GitHub asset digest
verified before execution. With its extracted package and Java:

```bash
java -jar /path/to/epubcheck.jar dist/a-agua-sob-darsen-0.1.0.epub
java -jar /path/to/epubcheck.jar dist/the-water-beneath-darsen-0.2.0.epub
```

Both delivered EPUBs report zero fatals/errors/warnings in recorded checks. Checks compare every
narrative heading and paragraph in source, EPUB spine and extracted PDF; inspect
navigation/language, font embedding/Unicode and PDF metadata. Rebuilds also pass
the same content checks. Container timestamps/IDs are not a byte-reproducible
artifact contract. Normal integrity checks do not regenerate the editions.

## Review boundaries

[English execution/editorial review](../../evidence/lich-cistern/ENGLISH_RUN.json)
records exact manuscript/EPUB/PDF identity, language/navigation/font checks, official
EPUBCheck, isolated rebuilds, controlled language/omission rejection, actual PDF
rasters and packaged XHTML/CSS at 360/900px via a local HTTP preview. This is not
a tested ebook-device or assistive-technology workflow. The English PDF identifies
its language but is still untagged. The Portuguese source, metadata, two shipped
editions, stylesheet and font files remain byte-for-byte unchanged.


[Execution/editorial evidence](../../evidence/lich-cistern/RUN.json) records
format checks, PDF raster inspection and first-chapter XHTML layout at 360/900px.
That Chromium view is an EPUB content inspection, not a tested Kindle/Apple
Books/Kobo workflow. Source and rendered-page review are by the implementing agent.
Format validity, word/page counts and matching text do not prove literary quality.
The PDF is untagged; assistive technology and hardware readers remain unverified.

Editorial passes corrected the water shortage's cause, demonstrated why Aevren
cannot pull the brake himself, kept corpse/witness/injury knowledge consistent,
and removed a contrived object-return ending. The narrative now ends with a
specific testimony/grief interaction rather than a moral speech. Reader response,
canon fit against the unavailable manuscript and commercial interest remain open.

Next compare independent Portuguese/English reader and translator reactions to the physical climax, voices and constrained permission; assess device reading alongside native play, musical practice and real P11 handoffs before choosing further work.
