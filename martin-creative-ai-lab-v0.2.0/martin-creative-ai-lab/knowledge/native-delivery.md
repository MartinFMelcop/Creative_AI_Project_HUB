# Native delivery — verify the recipient runtime separately

**Question/context:** can the current North Star adventure run without its editor
or checkout? Baseline `6a4ecb8` delivers only a project and engine-dependent PCK.
**Sources:** ENG-004/015, SCI-017, CRE-007 A, prior P01/P05/P06 delivery patterns and
[actual release execution](../evidence/north-star-linux-player/RUN.json).

**Observation:** raw PCK/template pairing lacks the exported global class cache;
the official release also disables editor script/path overrides. Fresh official
export and an explicit opt-in actual-scene check run both approach/return journeys,
profile reentry and embedded source verification with no developer-tool PATH.
The default release window accepts real synthetic OS edit/move/pause keys and
reloads its default-path profile. A missing companion PCK fails. The runtime costs
about 27 MB compressed, versus roughly 0.3 MB of game PCK.

**Negative/control:** the first 12s window-discovery bound saw only the Godot splash.
Matched release/editor probes reached the real title at 12–16s. Waiting at most
30s for the actual scene, then requiring capture/input receipt, corrects the
instrument rather than product timing. Export cache/UID metadata changes archive
bytes; compare embedded source and executed behavior independently of that identity.

**Interpretation/consequence:** compilation, editor tests and static ZIP metadata
cannot substitute for recipient-runtime execution. Preserve a small optional delivery
when bundling a much larger runtime; validate actual payloads, permissions and notices.
**Validity:** one Linux x86_64/software-display environment, fixed policies and synthetic
input, not independent user installation, general hardware coverage, creative approval,
accessibility, fun or commercial evidence. This is not a generic export-framework claim.
