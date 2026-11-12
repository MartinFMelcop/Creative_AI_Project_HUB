# North Star VEA-032/R10 — pinned R09 integration adapter

Status: **SOURCE-BOUND PORTABLE ADAPTER / NO ART APPROVAL / NO UNITY OR ARENA EXECUTION**.

This directory belongs to the existing labs/visual-animation destination. It does **not** create a twelfth lab, new product engine, autonomous aesthetic assessor, or R08 implementation authority. The adapter runs the actual R09 renderer/validator/diagnostic code from a **pinned, user-supplied R09 ZIP** with an isolated temporary source tree. Only output evidence is retained. The R09 ZIP is deliberately not embedded in this repository: the original 13 MB archive includes old asset files and authored artwork whose retention and publication rights need separate review. This is an **external-source adapter**, not full vendoring of the R09 source and assets.

## Source and provenance

- Original: NORTH_STAR_VEA_032_R09_MONTAGEM_E_CALIBRACAO.zip, SHA-256 66b30aad1801d20efb93d68d97daaf4598840c816269af1bb89e1a558300d3ff.
- Reuses six exact source files from R09: the original VEA-020 renderer, VEA-021 art-operation validator, R07 visual diagnostics, R09 calibration program and its 16-test suite.
- Extracted R04 baseline, R08 editorial-only overlay and R07 45-investigation overlay are strictly inputs. Their original file bytes are never edited.
- For the separately held package, contact the asset/source owner; there is no public repository download URI. Do not invent a public asset URL, publish source media, or substitute a same-named ZIP.
- Historical owner permissions, creation provenance and rights must be reconciled before republishing source images or using them commercially.

## Run (local, user-supplied archive)

Prerequisites from R09: Python 3.13, Pillow 12.3.0, NumPy 2.3.5, CairoSVG 2.8.2 and system Cairo. Pin and verify runtime before comparing exact PNG hashes across machines.

```sh
python3 -m unittest discover -s labs/visual-animation/vea-calibration -p 'test_runner.py' -v
python3 labs/visual-animation/vea-calibration/runner.py \
  --archive /path/to/NORTH_STAR_VEA_032_R09_MONTAGEM_E_CALIBRACAO.zip \
  --output /tmp/vea-r10-new-output
```

Output directory must not exist. The adapter first verifies the complete ZIP SHA-256 and the six source hashes, then checks 73 editorial-only IDs, 45 individual research approvals, 10 semantic links and the four pending exceptions. It executes the original 16 R09 tests and the three variants, verifying ORA readback and nonzero visible change. Results are written under the provided output root. An incomplete failed run is retained and **must not be passed off as a success**. Output belongs outside the maintained repository.

## Boundaries and next step

- L01-D01=B; L01-D02–D31=A; FAST-01=A. Editorial R08 decisions G02–G09 do not grant implementation or art acceptance.
- 737 historical original critiques, 45 individually authorized investigations, 73 distinct editorial IDs, ten non-merging links; 0031–0034 remain PENDING_AUTHOR.
- No artistic rating, accepted design, new RF/RNF/HU, Unity Editor, Windows, engine selection, Arena S4 tests, paid model, production asset or canon approval.
- Arena C05-P01–P07 and R51/R60/R61/INT-C01-001 remain open; Arena S4 S1 remains EXECUTION_HOLD_BY_AUTHOR.
- Full in-repository vendoring of R09 source and authored assets is a **separate step dependent on rights/provenance and repository-size approval**. Do not imply this adapter removes that dependency.
