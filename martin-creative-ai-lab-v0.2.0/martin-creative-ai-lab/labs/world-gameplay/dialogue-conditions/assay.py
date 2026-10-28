#!/usr/bin/env python3
"""Inspect preserved dialogue-condition contracts; never execute historical Ruby."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source'
NAMES = [
    'RM_ACT1/DATA/DEV/RGSS/RM_DIALOGUE_SCORING_RUNTIME.rb',
    'RM_DIST/RMXP_BASE/ScriptsCustom/RM_DIALOGUE_SCORING_RUNTIME.rb',
    'RM_ACT1/DATA/DEV/DIALOGUE_VARIANTS.csv',
    'RM_DIST/RMXP_BASE/Data/RM_CSV/DIALOGUE_VARIANTS.csv',
]
EXPECTED = [
    '07682a3205ea2850d748e4f3ffeef7febe51df1ddb10d5e8689bef7d26d1a735',
    '07682a3205ea2850d748e4f3ffeef7febe51df1ddb10d5e8689bef7d26d1a735',
    '7434223aa7fe25a8449796d1648b04257efa355bced6d62a0224e3b3f2606787',
    '7434223aa7fe25a8449796d1648b04257efa355bced6d62a0224e3b3f2606787',
]


def identities():
    return {str((SOURCE / name).relative_to(ROOT)): hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
            for name in NAMES}


def span(text, first, last):
    start = text.index(first)
    end = text.index(last, start) + len(last)
    return {'first_line': text[:start].count('\n') + 1,
            'last_line': text[:end].count('\n') + 1,
            'sha256': hashlib.sha256(text[start:end].encode()).hexdigest()}


def inspect():
    before = identities()
    if list(before.values()) != EXPECTED:
        raise ValueError('Preserved dialogue source identities differ')
    data = [(SOURCE / name).read_bytes() for name in NAMES]
    if data[0] != data[1] or data[2] != data[3]:
        raise ValueError('Recorded DEV/DIST identity agreement changed')
    reader = csv.DictReader(io.StringIO(data[2].decode('utf-8-sig')))
    rows = list(reader)
    if len(rows) != 29 or len(reader.fieldnames) != 26 or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError('Actual dialogue variant shape changed')
    expressions = sorted(set(row['ConditionsExpr'] for row in rows))
    if len(expressions) != 23:
        raise ValueError('Actual distinct expression count changed')
    text = data[0].decode()
    risks = {
        'unknown_character_skip': '# unknown char: skip\n        i += 1' in text,
        'prefix_parse_without_exhaustion': 'def parse\n        parse_or\n      end' in text,
        'missing_closing_parenthesis_not_checked': 'node = parse_or\n          eat(")")\n          return node' in text,
        'missing_primary_becomes_true': 'return [:lit, true] if tok == nil' in text,
        'empty_expression_true': 'return true if expr == ""' in text,
        'exception_fallback_differs': 'rescue\n        fallback_eval(expr, state, rel, tagset, flags, trace, npc_id)' in text,
        'recent_suffix_removed_before_query': 'eid = $1' in text,
    }
    if not all(risks.values()):
        raise ValueError('Static parser boundary observations changed')
    sections = {
        'conditions_module': span(text, '  module ConditionsExpr', '\n  module DialogueScoring'),
        'tokenizer_skip': span(text, '        # unknown char: skip', '      out\n    end'),
        'prefix_parser': span(text, '      def parse\n', '      def parse_or\n'),
        'public_eval': span(text, '    def self.eval(expr,', '    def self.count_atoms(node)'),
        'comparison': span(text, '    def self.eval_cmp(key,', '    def self.eval_node(node,'),
    }
    probes = [
        {'input': 'Coins>=1 !', 'risk': 'unknown_character_skip', 'strict_destination': 'reject unknown character'},
        {'input': 'Coins>=1 trailing', 'risk': 'prefix_parse_without_exhaustion', 'strict_destination': 'reject unconsumed suffix'},
        {'input': '(Coins>=1', 'risk': 'missing_closing_parenthesis_not_checked', 'strict_destination': 'reject missing closing parenthesis'},
        {'input': 'Coins>=1 &', 'risk': 'missing_primary_becomes_true', 'strict_destination': 'reject missing operand'},
        {'input': '', 'risk': 'empty_expression_true', 'strict_destination': 'reject empty private service permission; preserve legitimate unconditional source dialogue separately'},
    ]
    scalar = [row for row in rows if row['ConditionsExpr'] and not any(fn + '(' in row['ConditionsExpr'] for fn in ['HasTag', 'HasFlag', 'HasRecentEvent'])]
    if before != identities():
        raise ValueError('Sources changed during static inspection')
    return {
        'schema_version': 1, 'kind': 'dialogue_condition_static_source_inspection',
        'source_sha256': before, 'source_stable': True, 'runtime_variants_identical': True,
        'table_variants_identical': True, 'variant_rows_per_copy': 29, 'columns': 26,
        'distinct_expressions': expressions,
        'variant_conditions': [{'variant_id': row['VariantID'], 'expression': row['ConditionsExpr']} for row in rows],
        'nonempty_scalar_comparison_rows': [{'variant_id': row['VariantID'], 'expression': row['ConditionsExpr']} for row in scalar],
        'declared_grammar': 'Comparison == != < <= > >= (plus source = alias), & before |, parentheses; source also declares HasTag/HasFlag/HasRecentEvent queries.',
        'static_source_risks': risks, 'source_sections': sections,
        'declared_negative_probes': probes,
        'probe_method': 'These are inputs motivated by exact inspected source branches and expected strict-destination refusals. No Ruby evaluation result is asserted; actual C# probe execution belongs to its separate instrument.',
        'comparison_boundary': 'Source resolves relation before state and then key_0_100 fallback. Integer-looking strings compare numerically; otherwise only equality/inequality use exact strings. Destination typed/missing-key/coercion policy must be explicit, never silently called source equivalence.',
        'private_authority_decision': 'Reject direct permissive source parser/fallback as complete private paid-service permission authority. Empty unconditional dialogue remains a legitimate separate source case; no collection-wide rejection.',
        'remaining': 'Function-query bindings, recent-event suffix semantics, full candidate filtering, scoring/tie breaks, personality axes/state deltas, dialogue/catalog fiction and actual Ruby/RGSS/RMXP execution remain unresolved unless separately implemented and verified.',
        'ruby_executed': False, 'rgss_executed': False, 'rmxp_executed': False,
        'limits': 'Static exact-byte source inspection and declared negative inputs, not historical execution, human psychology/relationship validation, North Star canon or commercial clearance.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == ROOT or ROOT in args.output.resolve().parents:
        parser.error('Output must be a new external file')
    if args.output.exists():
        parser.error('Output already exists')
    result = inspect()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print('PASS: identical DEV/DIST runtime/table pairs;29rows/23expressions inspected statically, no Ruby execution')
