# Historical reference library

This library separates preserved source bytes, readable snapshots, discovery
metadata and active adaptations. [Catalog](catalog.json) records availability;
[reference instructions](AGENTS.md) define the historical-data boundary.

- [Rave Master](rave-master/README.md): pinned source tree; 589 readable original
  text/code/data files, 140 explicit exclusions from 729 observed files.
- [Literary collection](literature/lich/README.md): supplied attachment and older
  inspection records distinguished. The oversized attachment is unavailable;
  no historical manuscript, cover, PDF or authority-policy bytes were imported.
- [Earlier selected archive](../archive/legacy-source-extracts-v0.2.0.zip): unchanged
  175 Rave and three WebSocket texts, with its original registry/hash contract.
- [North Star](../north-star/README.md): strategic program; no runtime integration.

From the maintained lab directory, Python 3.10+ and its standard library suffice:

```bash
python3 tools/reference_library.py check
python3 tools/reference_library.py find --topic combat
python3 tools/reference_library.py find --module RM_ACT1 --name dialogue
python3 tools/reference_library.py find --name Game.exe --include-excluded
python3 tools/reference_library.py find --collection REF-LICH-ATTACHMENT
```

Queries return exact original/local paths, status and hashes; an unavailable
collection returns zero local files. They never import or execute legacy code.
Catalog integrity and preserved bytes are checked offline in ordinary checkouts;
CI needs no upstream clone or large attachment download. Exclusions are inventory
records, not downloadable placeholder payloads. Raw historical links/formulas/
reports may be obsolete; source integrity does not prove their correctness,
execution, redistribution rights or independent creative approval.

Raw Rave snapshots have scoped Git attributes: no EOL conversion and historical
whitespace retained, including original CRLF/hard breaks. Current source/docs
retain normal style checks. Snapshot hashes and staged Git blobs, rather than
rewriting old formatting, establish byte identity; this is not a general check
bypass for active projects.
