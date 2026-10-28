#!/usr/bin/env python3
"""Recompute finite-suite policy endpoints; does not replace authoritative C# replay."""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import statistics


def mean(values):
    return statistics.fmean(values) if values else None


def variance(values):
    return statistics.variance(values) if len(values) > 1 else None


def summarize(report, expected_source=None):
    if report.get('schema') != 'eclipse-policy-evaluation-v1':
        raise ValueError('Unsupported report schema')
    source = report.get('source_hash', '')
    if len(source) != 64 or any(c not in '0123456789abcdef' for c in source):
        raise ValueError('Invalid source closure')
    if expected_source is not None and source != expected_source:
        raise ValueError('Unexpected source closure')
    c = report['configuration']
    scenarios = c['scenarios']; rosters = c['rosters']; seeds = c['seeds']
    if not scenarios or len(rosters) < 2 or not any(r['held_out'] for r in rosters) or not any(not r['held_out'] for r in rosters):
        raise ValueError('Missing scenario or roster boundary')
    if c['baseline'] == c['candidate'] or c['max_actions'] not in range(1,161):
        raise ValueError('Invalid policy comparison/budget')
    if any(len(r['opponents']) != 3 for r in rosters):
        raise ValueError('Need exactly three opponents')
    if len(set(seeds)) != len(seeds) or not seeds:
        raise ValueError('Duplicate/missing seed')
    if len({x['id'] for x in scenarios}) != len(scenarios) or len({x['id'] for x in rosters}) != len(rosters):
        raise ValueError('Duplicate scenario/roster')
    expected = {f"{s['id']}/{r['id']}/{seed}/{seat}/{rotation}/{arm}"
                for s, r, seed, seat, rotation, arm in itertools.product(
                    scenarios, rosters, seeds, range(4), range(3), ('baseline', 'candidate'))}
    games = report['games']; by_id = {}
    roster_by_id = {r['id']: r for r in rosters}
    for g in games:
        identity = f"{g['scenario']}/{g['roster']}/{g['seed']}/{g['focal_seat']}/{g['rotation']}/{g['arm']}"
        if identity != g['id'] or identity not in expected or identity in by_id:
            raise ValueError('Unexpected/duplicate game unit')
        by_id[identity] = g
        roster = roster_by_id[g['roster']]
        if g['held_out'] != roster['held_out']:
            raise ValueError('Holdout metadata mismatch')
        policies = []; next_opponent = 0
        for seat in range(4):
            if seat == g['focal_seat']:
                policies.append(c[g['arm']])
            else:
                policies.append(roster['opponents'][(next_opponent + g['rotation']) % 3]); next_opponent += 1
        if policies != g['policies']:
            raise ValueError('Policy assignment mismatch')
        winners = g['winners']
        if len(set(winners)) != len(winners) or any(type(x) is not int or x not in range(4) for x in winners):
            raise ValueError('Invalid winner set')
        complete = g['status'] == 'complete'
        if g['status'] not in ('complete', 'interrupted') or complete != bool(winners) or complete != (g['error'] is None):
            raise ValueError('Incomplete/terminal denominator mismatch')
        member = g['focal_seat'] in winners
        fraction = 1 / len(winners) if member else 0
        if (g['winner_member'] != member or g['fractional_credit'] != fraction
                or g['exclusive_win'] != (member and len(winners) == 1)
                or g['multiwinner_tie'] != (len(winners) > 1)):
            raise ValueError('Forged winner/fraction endpoint')
        if complete and (not g['reason'] or abs(sum(1 / len(winners) for _ in winners) - 1) > 1e-12):
            raise ValueError('Invalid complete result')
        if not complete and (not g['error'] or g['reason'] is not None):
            raise ValueError('Interrupted game has invented result')
        if len(g['actions']) > c['max_actions']:
            raise ValueError('Declared action budget exceeded')
    if set(by_id) != expected:
        raise ValueError('Missing complete game assignment')
    pairs = {}
    for identity, g in by_id.items():
        key = identity.rsplit('/', 1)[0]
        pairs.setdefault(key, {})[g['arm']] = g
    if any(set(pair) != {'baseline', 'candidate'} for pair in pairs.values()):
        raise ValueError('Missing paired counterpart')

    def endpoints(group):
        complete = [g for g in group if g['status'] == 'complete']
        return {'executions': len(group), 'complete': len(complete), 'interrupted': len(group)-len(complete),
                'exclusive_focal_wins': sum(g['exclusive_win'] for g in complete),
                'multiwinner_games': sum(g['multiwinner_tie'] for g in complete),
                'focal_winner_memberships': sum(g['winner_member'] for g in complete),
                'fractional_credit_sum': sum(g['fractional_credit'] for g in complete),
                'fractional_credit_mean_complete': mean([g['fractional_credit'] for g in complete]),
                'gate_claim_games': sum(g['reason'] == 'gate claimed' for g in complete),
                'deadline_games': sum(g['reason'] != 'gate claimed' for g in complete),
                'accepted_actions': sum(len(g['actions']) for g in group)}

    def comparison(group):
        base = [g for g in group if g['arm'] == 'baseline']; cand = [g for g in group if g['arm'] == 'candidate']
        complete = all(g['status'] == 'complete' for g in group)
        b = mean([g['fractional_credit'] for g in base]); a = mean([g['fractional_credit'] for g in cand])
        return {'baseline': endpoints(base), 'candidate': endpoints(cand),
                'delta': a-b if complete else None, 'comparative_valid': complete}

    families = []
    for s, r, seed in itertools.product(scenarios, rosters, seeds):
        group = [g for g in games if (g['scenario'], g['roster'], g['seed']) == (s['id'], r['id'], seed)]
        result = comparison(group)
        families.append({'scenario': s['id'], 'roster': r['id'], 'seed': seed, **result})
    roster_results = {}
    for r in rosters:
        rid = r['id']; group = [g for g in games if g['roster'] == rid]; f = [x for x in families if x['roster'] == rid]
        result = comparison(group); valid = result['comparative_valid']
        bv = [x['baseline']['fractional_credit_mean_complete'] for x in f]
        cv = [x['candidate']['fractional_credit_mean_complete'] for x in f]
        differences = [x['delta'] for x in f]
        cov = statistics.covariance(bv, cv) if valid and len(f)>1 else None
        result.update({'held_out': r['held_out'], 'family_count': len(f),
                       'family_delta_min': min(differences) if valid else None,
                       'family_delta_max': max(differences) if valid else None,
                       'family_delta_median': statistics.median(differences) if valid else None,
                       'positive_family_count': sum(x>0 for x in differences) if valid else None,
                       'negative_family_count': sum(x<0 for x in differences) if valid else None,
                       'baseline_candidate_family_covariance': cov,
                       'paired_difference_family_variance': variance(differences) if valid else None,
                       'sum_unpaired_arm_family_variances': variance(bv)+variance(cv) if valid and len(f)>1 else None,
                       'by_scenario': {s['id']: comparison([g for g in group if g['scenario']==s['id']]) for s in scenarios},
                       'by_focal_seat': {str(seat): comparison([g for g in group if g['focal_seat']==seat]) for seat in range(4)}})
        roster_results[rid] = result
    all_complete = all(g['status']=='complete' for g in games)
    robust = all_complete and all(r['delta'] >= .05 and all(s['delta'] >= 0 for s in r['by_scenario'].values()) for r in roster_results.values())
    return {'schema_version': 1, 'kind': 'finite_deterministic_suite_analysis',
            'source_closure_sha256': source, 'experiment_id': c['experiment_id'],
            'unit': 'Complete multiplayer game; assignments and arms nested in scenario/seed/roster family, not independent seats.',
            'endpoints': endpoints(games), 'paired_assignments': len(pairs), 'families': families, 'rosters': roster_results,
            'decision': 'ROBUST_FINITE_SUITE_IMPROVEMENT' if robust else 'NO_ROBUST_IMPROVEMENT' if all_complete else 'INCONCLUSIVE_INTERRUPTED',
            'threshold': 'Each roster delta>=0.05 and each scenario-by-roster delta>=0, with all executions complete.',
            'uncertainty': 'Exact finite-suite ranges and descriptive family covariance/variance; no sampling model, population CI, pure initiative identification or unseen-world claim.',
            'limits': 'Recomputed endpoints and assignment matching do not independently verify trace legality or actual winner authority. Run authoritative C# verify and expected source/config closure checks before this analysis. No CommanderSIM/Magic/North Star outcome inference.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path); parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source-hash')
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Refusing existing output')
    try:
        raw=args.report.read_bytes(); result=summarize(json.loads(raw), args.source_hash)
        result['report_sha256']=hashlib.sha256(raw).hexdigest()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        print(result['decision'])
        return 0
    except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
        parser.exit(2, 'Refused report: '+str(e)+'\n')

if __name__=='__main__':
    raise SystemExit(main())
