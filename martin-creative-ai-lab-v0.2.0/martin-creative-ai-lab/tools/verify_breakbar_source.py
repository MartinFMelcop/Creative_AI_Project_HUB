#!/usr/bin/env python3
"""Assay selected preserved BBR rows and compare declared Python/C# transitions.

This is a literal source assay and an independent implementation of declared
destination policies, not execution of Ruby/RGSS or a complete status catalog.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/REGRAS_DE_COMBATE.csv"
SOURCE_SHA256 = "f2c97e85ce573c50aa1959ec81221882c4fff4d164126fc22c5e6c9dd64c17e9"
EXPECTED = {
    "BBR-001": ("Enquanto breakbar > 0, boss é imune a todo tipo de CC; CC consumido drena barra.", "Imune"),
    "BBR-002": ("Quando a barra chega a 0, o boss deixa de ser imune a CC (salvo imunidades do boss).", "Vulnerável"),
    "BBR-003": ("Após break, CC aplicado funciona normalmente e carrega a barra de volta.", "Sim"),
    "BBR-004": ("Quando a barra volta a 100%, o boss retorna ao estado imune a CC.", "1"),
    "BBR-005": ("Breakbar drena por aplicação de CC: Categoria Leve drena 1 ponto; Categoria Não-leve (hard CC) drena 3 pontos. DOT não drena breakbar por padrão.", "Leve=1; Não-leve=3"),
    "BBR-006": ("Boss pode declarar imunidade a CC específico mesmo pós-break.", "Por boss"),
    "BBR-010": ("Mini-bosses usam breakbar com total fixo para permitir quebra por CC.", "5"),
    "BBR-011": ("Calamidades (chefes principais) usam breakbar maior para encounters longos.", "20"),
}


def source_rows():
    data = (ROOT / SOURCE).read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Preserved combat source identity differs")
    rows = {}
    for row in csv.reader(data.decode("utf-8-sig").splitlines()):
        if row and row[0] in EXPECTED:
            if row[0] in rows or len(row) != 10:
                raise ValueError("Duplicate/malformed selected BBR row")
            if (row[4], row[5]) != EXPECTED[row[0]]:
                raise ValueError("Selected literal BBR contract differs: " + row[0])
            rows[row[0]] = row
    if set(rows) != set(EXPECTED):
        raise ValueError("Missing selected BBR contract")
    return rows


def vectors():
    # Explicit destination policy: the protected contact that reaches zero is
    # consumed; exposed eligible contact applies before restoring immunity.
    # Specific immunity neither applies, drains nor refills. Refill uses
    # the same category weight. These ordering/weight choices are not uniquely
    # specified by the source and remain separately labeled in the report.
    sequences = [
        ("light-cycle", 5, [("Light", False)] * 12),
        ("hard-clamped-cycle", 5, [("Hard", False)] * 6),
        ("mixed-cycle", 5, [("Light", False), ("Hard", False), ("Light", False),
                             ("Light", False), ("Hard", False), ("Light", False)]),
        ("specific-immunity", 5, [("Hard", True), ("Hard", False), ("Hard", False),
                                   ("Light", True), ("Hard", False), ("Hard", True),
                                   ("Hard", False), ("Light", True)]),
        ("source-capacity-twenty", 20, [("Hard", False)] * 16),
        ("unit-capacity-destination-probe", 1, [("Light", False), ("Hard", False),
                                               ("Hard", True), ("Light", True)]),
    ]
    result = []
    for identity, capacity, actions in sequences:
        phase, value, steps = "Protected", capacity, []
        for category, immune in actions:
            before_phase, before_value = phase, value
            weight = {"Light": 1, "Hard": 3}[category]
            applied, drained, refilled = False, 0, 0
            if immune:
                pass
            elif phase == "Protected":
                drained = min(value, weight)
                value -= drained
                if value == 0:
                    phase = "Exposed"
            else:
                applied = True
                refilled = min(capacity - value, weight)
                value += refilled
                if value == capacity:
                    phase = "Protected"
            steps.append(dict(category=category, immune=immune,
                              before_phase=before_phase, before_value=before_value,
                              after_phase=phase, after_value=value, applied=applied,
                              drained=drained, refilled=refilled))
        result.append(dict(id=identity, capacity=capacity, steps=steps))
    return result


def reject_defect(expected, actual):
    if actual != expected:
        raise ValueError("C# transition report differs from SAME declared Python cases")


def outside(path):
    path = path.resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("Execution output must remain outside maintained sources")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--export-cases", type=Path)
    parser.add_argument("--csharp-results", type=Path)
    args = parser.parse_args()
    rows, cases = source_rows(), vectors()
    if args.export_cases:
        outside(args.export_cases).write_text(json.dumps(cases, indent=2) + "\n")
    # A truthful-looking but false phase/report must fail the SAME exact comparator.
    defective = json.loads(json.dumps(cases))
    defective[0]["steps"][5]["applied"] = False
    try:
        reject_defect(cases, defective)
    except ValueError:
        defective_rejected = True
    else:
        raise ValueError("False result comparator negative survived")
    if args.csharp_results:
        reject_defect(cases, json.loads(args.csharp_results.read_text()))
    report = dict(schema_version=1, source=SOURCE, source_sha256=SOURCE_SHA256,
                  source_rows=rows, case_count=len(cases),
                  transition_count=sum(len(x["steps"]) for x in cases),
                  csharp_same_cases_compared=bool(args.csharp_results),
                  false_report_rejected=defective_rejected,
                  evidence_class="OBSERVED_SOURCE and RECORDED_EXECUTION",
                  destination_policies=["Independent Protected/Exposed phase resolves refill versus positive-bar ambiguity",
                                        "Zero-crossing protected CC is consumed without applying",
                                        "Exposed eligible CC applies before full-bar immunity returns",
                                        "Refill uses category drain weight; specific immune CC neither drains nor refills"],
                  limits="Literal selected source rows and declared transition cases only; no Ruby/RGSS/RMXP, full boss/status catalog, balance or human validation")
    outside(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"PASS: {len(rows)} exact BBR rows; {len(cases)} declared cases/{report['transition_count']} transitions; C# compared={bool(args.csharp_results)}")


if __name__ == "__main__":
    main()
