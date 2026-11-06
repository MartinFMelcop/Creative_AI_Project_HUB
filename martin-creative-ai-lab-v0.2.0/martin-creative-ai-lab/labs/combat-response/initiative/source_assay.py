#!/usr/bin/env python3
"""Bind literal initiative requirements and compare SAME original Python/C# policies.

No preserved script is executed. Numeric initiative is explicitly original destination
policy; source requirements do not recover a historical initiative algorithm.
"""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/'
SOURCE = BASE + 'RM_CORE/DATA/CORE/REGRAS_DE_COMBATE.csv'
SOURCE_SHA256 = 'f2c97e85ce573c50aa1959ec81221882c4fff4d164126fc22c5e6c9dd64c17e9'
EXPECTED = {
    'FLW-002': ('Cada unidade tem 1 ação por turno. Habilidades/passivas podem conceder pontos de ação que geram turnos extras.', '1 ação'),
    'FLW-003': ('A rodada termina quando todas as unidades vivas no início da rodada tiveram pelo menos 1 turno.', 'A'),
    'FLW-005': ('Ao fim da rodada: tick de DOT, geração leve de SP, expiração de efeitos por rodada, e checagens finais.', 'Sim'),
    'INI-001': ('A iniciativa é recalculada no início de cada rodada com variação controlada baseada em AGI.', 'B'),
    'INI-002': ('Empate na ordem: desempate por RNG.', 'RNG'),
    'INI-004': ('A UI exibe a fila de turnos (timeline) para leitura do fluxo.', 'Ativa'),
    'INI-005': ('A variação controla pequenas mudanças na fila a cada rodada (não é ordem fixa).', 'Ativa'),
}
HELPERS = [BASE + p for p in [
    'RM_ACT1/DATA/DEV/RGSS/RM_COMBAT_RUNTIME.rb',
    'RM_DIST/RMXP_BASE/ScriptsCustom/RM_COMBAT_RUNTIME.rb',
]]
HELPER_METHODS = ['clamp', 'safe_ratio', 'hit_chance', 'crit_chance', 'raw_damage', 'mitigate', 'apply_chance', 'final_duration', 'dot_tick', 'reapply_duration']


def source_rows():
    data = (ROOT / SOURCE).read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError('Preserved combat source identity differs')
    rows = {}
    for row in csv.reader(data.decode('utf-8-sig').splitlines()):
        if row and row[0] in EXPECTED:
            if len(row) != 10 or row[0] in rows or (row[4], row[5]) != EXPECTED[row[0]]:
                raise ValueError('Literal selected initiative row differs: ' + row[0])
            rows[row[0]] = row
    if set(rows) != set(EXPECTED):
        raise ValueError('Missing literal selected initiative rows')
    return rows


def helper_assay():
    result = []
    for name in HELPERS:
        raw = (ROOT / name).read_bytes()
        text = raw.decode('utf-8-sig')
        methods = re.findall(r'^  def self\.(\w+)\(', text, flags=re.M)
        if methods != HELPER_METHODS:
            raise ValueError('Previously inspected helper method inventory changed: ' + name)
        marker = '# - This module is a helper/API; full integration into RMXP battle loop can be done in follow-up AJ(s).'
        if marker not in text:
            raise ValueError('Inspected helper boundary declaration changed')
        result.append(dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw), methods=methods,
                           observed_boundary=marker, executed=False,
                           limit='These inspected files supply formula helpers, not an initiative scheduler. Not a claim of global absence or historical Ruby execution.'))
    return result


def cases():
    return [dict(style=style, seed=seed, rounds=32)
            for style in ['heavy', 'quick']
            for seed in [0, 1, 2, 17, 0x4e535441, 0xffffffff]]


def simulate(case):
    style, state = case['style'], case['seed']
    agility = {'heavy': 8, 'quick': 16}[style]
    def draw():
        nonlocal state
        state = (state * 1664525 + 1013904223) & 0xffffffff
        return state
    rounds = []
    for number in range(1, case['rounds'] + 1):
        player = agility + draw() % 13 - 6
        target = 12 + draw() % 13 - 6
        first = player > target or (player == target and draw() & 1 == 0)
        rounds.append(dict(round=number, playerScore=player, targetScore=target,
                           seedState=state, order=['player', 'target'] if first else ['target', 'player']))
    return dict(style=style, seed=case['seed'], rounds=rounds)


def exact(expected, actual):
    # Canonical JSON also distinguishes boolean versus integer and float coercion.
    if json.dumps(expected, sort_keys=True, separators=(',', ':')) != json.dumps(actual, sort_keys=True, separators=(',', ':')):
        raise ValueError('Native results differ from SAME independent original-policy inputs')


def outside(path):
    path = path.resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('New output outside maintained source required')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--export-cases', type=Path)
    parser.add_argument('--native', type=Path)
    args = parser.parse_args()
    rows, helpers = source_rows(), helper_assay()
    inputs = cases()
    expected = [simulate(case) for case in inputs]
    rounds = [r for case in expected for r in case['rounds']]
    ties = [r for r in rounds if r['playerScore'] == r['targetScore']]
    if not ties or len({tuple(r['order']) for r in rounds}) != 2:
        raise ValueError('Declared controls must exercise ties and both actual orders')
    defective = json.loads(json.dumps(expected))
    defective[0]['rounds'][0]['order'].reverse()
    try:
        exact(expected, defective)
    except ValueError:
        defect_rejected = True
    else:
        raise ValueError('False queue comparator survived')
    if args.export_cases:
        outside(args.export_cases).write_text(json.dumps(inputs, indent=2) + '\n')
    if args.native:
        report = json.loads(args.native.read_text())
        exact(expected, report['vectors'])
    report = dict(schema_version=1, source=SOURCE, source_sha256=SOURCE_SHA256,
                  source_rows=rows, helpers=helpers, cases=inputs, expected_vectors=expected,
                  case_count=len(inputs), round_count=len(rounds), score_tie_count=len(ties),
                  same_cases_compared=args.native is not None, false_queue_report_rejected=defect_rejected,
                  original_policy='uint32 LCG1664525/1013904223; player draw then target draw, each%13-6; score AGI+jitter descending; equal score extra draw lowbit0 gives player first. Heavy AGI8/Quick16 versus target12; seeds/cases explicit.',
                  source_boundary='INI002 generic tie RNG is adapted to equal numeric scores, not recovered AGI formula. FLW005 only existing DOT/duration/final-state subset; no SP regeneration. FLW003 living-start one-turn subset; no bonus turns or complete historical scheduler.',
                  limits='Literal source requirements and SAME original deterministic policy controls. Not historical Ruby/RMXP, independently sampled people, balance, full combat, Unity/Windows/Steam or canon approval.')
    outside(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f'PASS: {len(rows)} literal rows; {len(inputs)} same-input cases/{len(rounds)} rounds; C# compared={args.native is not None}')


if __name__ == '__main__':
    main()
