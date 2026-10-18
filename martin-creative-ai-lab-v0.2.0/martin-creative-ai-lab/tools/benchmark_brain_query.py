#!/usr/bin/env python3
"""Compare actual CLI output against a preserved Git tool; retain compact evidence only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/brain_query.py"
CASES = ROOT / "tools/brain_retrieval_cases.json"
VOCABULARY = ROOT / "tools/brain_vocabulary.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def invoke(tool, args, brains=None):
    command = [sys.executable, str(tool), "--brains-dir", str(brains or ROOT / "brains"), *args]
    process = subprocess.run(command, capture_output=True, timeout=15)
    return process.returncode, process.stdout, process.stderr


def success(tool, args):
    code, raw, error = invoke(tool, args)
    if code:
        raise ValueError(f"CLI failed ({code}) for {args}: {error.decode(errors='replace')[-1200:]}")
    return raw, json.loads(raw)


def implementation_revision(prefix):
    """Name a real source commit only when every measured implementation file matches it."""
    files = [TOOL, VOCABULARY, CASES, Path(__file__).resolve()]
    paths = [p.relative_to(ROOT).as_posix() for p in files]
    result = subprocess.run(["git", "log", "-1", "--format=%H", "--", *paths],
                            cwd=ROOT, capture_output=True, text=True, timeout=10)
    revision = result.stdout.strip()
    if result.returncode or not revision:
        return None
    for path, file in zip(paths, files):
        blob = subprocess.run(["git", "show", f"{revision}:{prefix}/{path}"],
                              cwd=ROOT, capture_output=True, timeout=10)
        if blob.returncode or blob.stdout != file.read_bytes():
            return None
    return revision


def benchmark(baseline_ref=None):
    cases = json.loads(CASES.read_text())
    baseline_ref = baseline_ref or cases["baseline_ref"]
    revision = subprocess.run(["git", "rev-parse", "--verify", "--end-of-options", baseline_ref + "^{commit}"],
                              cwd=ROOT, capture_output=True, text=True, timeout=10)
    if revision.returncode:
        raise ValueError("Baseline revision unavailable; obtain its history without rewriting it")
    revision = revision.stdout.strip()
    prefix = ROOT.relative_to(Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip()))
    original = subprocess.run(["git", "show", f"{revision}:{prefix}/tools/brain_query.py"],
                              cwd=ROOT, capture_output=True, timeout=10)
    if original.returncode:
        raise ValueError("Brain tool unavailable in baseline revision")
    with tempfile.TemporaryDirectory(prefix="brain-retrieval-benchmark-") as directory:
        old = Path(directory) / "baseline.py"
        old.write_bytes(original.stdout)
        compatibility = {}
        for name, args in (("check", ["check"]), ("indexes", ["indexes"]),
                           ("get_all", ["get", *[f"{p}-{i:03d}" for p, n in
                            (("ENG",49),("SCI",85),("CRE",100)) for i in range(1,n+1)]])):
            before, _ = success(old, args)
            after, _ = success(TOOL, args)
            if before != after:
                raise ValueError("Legacy output changed: " + name)
            compatibility[name] = {"identical": True, "bytes": len(after), "sha256": digest(after)}
        overview_raw, overview = success(TOOL, ["overview"])
        if sum(v["chapter_count"] for v in overview) != 234 or len(overview_raw) >= compatibility["indexes"]["bytes"] / 10:
            raise ValueError("Compact discovery is incomplete or not substantially smaller")
        rows = []
        for case in cases["cases"]:
            query = case["query"]
            before, before_data = success(old, ["search", query])
            literal, literal_data = success(TOOL, ["search", query])
            if before != literal:
                raise ValueError("Legacy search changed: " + query)
            meta, meta_data = success(TOOL, ["search", query, "--metadata-only"])
            full, full_data = success(TOOL, ["search", query, "--relaxed"])
            compact, hits = success(TOOL, ["search", query, "--relaxed", "--metadata-only"])
            ids = lambda data: [c["id"] for c in data]
            if ids(meta_data) != ids(literal_data) or ids(hits) != ids(full_data):
                raise ValueError("Metadata changed search membership/order: " + query)
            for found in hits:
                if "content" in found or "preview" in found:
                    raise ValueError("Compact output leaked full content/preview")
            if case["kind"] in ("primary", "extension") and not set(case["targets"]).intersection(ids(hits)):
                raise ValueError("Missing declared source target: " + query)
            if case["kind"] == "negative" and hits:
                raise ValueError("Negative query gained candidates: " + query)
            if case["kind"] == "ambiguous" and (not hits or not all(c["match"]["broad"] for c in hits)):
                raise ValueError("Ambiguous query lacks its broad-match warning")
            rows.append({**case, "baseline_ids": ids(before_data), "relaxed_ids": ids(hits),
                         "bytes": {"legacy_full": len(before), "strict_metadata": len(meta),
                                   "relaxed_full": len(full), "relaxed_metadata": len(compact)},
                         "matches": [{"id": c["id"], "kind": c["match"]["kind"],
                                      "score": c["search_score"], "source_only": any(t.get("field")=="content"
                                      for t in c["match"].get("terms", []))} for c in hits]})
        errors = []
        for args in (["get", "ENG-999"], ["search", ""], ["search", "a e de"],
                     ["search", "combat", "--limit", "0"], ["search", "combat", "--limit", "abc"]):
            a, b = invoke(old, args), invoke(TOOL, args)
            if a[0] != 2 or b[0] != 2 or a[1] or b[1]:
                raise ValueError("Malformed input no longer rejects without output")
            errors.append({"args": args, "baseline_exit": a[0], "current_exit": b[0]})
        # Exercise the CLI pin boundary on a disposable corruption, never alter live pins.
        broken = Path(directory) / "brains"
        broken.mkdir()
        for name in ("ENGINEERING_BRAIN.md", "SCIENTIFIC_BRAIN.md", "CREATIVE_BRAIN.md",
                     "CATALOGO_DE_CONSULTA.json", "BIBLIOTECA_DE_CONHECIMENTO_APLICADO.md", "integrity.json"):
            (broken / name).write_bytes((ROOT / "brains" / name).read_bytes())
        with (broken / "CREATIVE_BRAIN.md").open("ab") as file:
            file.write(b"\n")
        for args in (["overview"], ["search", "combat", "--metadata-only", "--relaxed"], ["get", "CRE-010"]):
            code, raw, error = invoke(TOOL, args, broken)
            if code != 2 or raw or b"integrity mismatch" not in error:
                raise ValueError("Corrupted sources did not block discovery/retrieval")
        primary = [c for c in rows if c["kind"]=="primary"]
        score = lambda key: sum(bool(set(c["targets"]) & set(c[key])) for c in primary)
        report = {"schema_version": 1, "baseline_revision": revision,
                  "baseline_tool_sha256": digest(original.stdout),
                  "implementation": {"revision": implementation_revision(prefix),
                      "benchmark_sha256": digest(Path(__file__).read_bytes()),
                      "tool_sha256": digest(TOOL.read_bytes()),
                      "vocabulary_sha256": digest(VOCABULARY.read_bytes()),
                      "cases_sha256": digest(CASES.read_bytes())},
                  "units": "UTF-8 stdout bytes, including JSON formatting/newline; no token, billing or latency measurement.",
                  "judgment_scope": cases["judgment_scope"],
                  "discovery": {"indexes_bytes": compatibility["indexes"]["bytes"],
                                "overview_bytes": len(overview_raw)},
                  "compatibility": compatibility, "malformed_inputs": errors,
                  "integrity_controls": "Three new/direct CLI paths reject disposable corruption with no stdout; live pins untouched.",
                  "primary_target_hit_at_5": {"baseline": score("baseline_ids"),
                                             "relaxed": score("relaxed_ids"), "cases": len(primary)},
                  "queries": rows}
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", help="Override the preserved comparison revision; never fetched automatically")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path, help="Require exact recorded identities, sizes, IDs and controls")
    args = parser.parse_args()
    try:
        report = benchmark(args.baseline_ref)
        if args.compare and report != json.loads(args.compare.read_text()):
            raise ValueError("Benchmark differs from recorded identities/results; inspect the changes")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
        print(f"PASS: {len(report['queries'])} queries, exact legacy outputs, full retrieval and corruption controls; "
              f"discovery {report['discovery']['indexes_bytes']} -> {report['discovery']['overview_bytes']} bytes; "
              f"primary target hits {report['primary_target_hit_at_5']}.")
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
