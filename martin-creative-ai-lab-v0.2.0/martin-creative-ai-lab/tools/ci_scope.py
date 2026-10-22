#!/usr/bin/env python3
"""Select affected retained consumers; integrity checks must always run separately.

Inputs are repository-relative Git paths. Unknown executable/shared contracts trigger
all jobs. Documentary changes do not require unrelated historical player rebuilds.
Empty/manual/new-branch scopes run every retained contract. This routes existing
verification; it neither retires a consumer nor removes its tests.
"""
import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess

WORKSPACE = 'martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/'
JOBS = ('native_arena', 'eclipse_economy', 'chat_evaluation',
        'north_star_authority', 'north_star_remote', 'north_star_csharp')
PROTOTYPE = ('native_arena', 'north_star_authority', 'north_star_remote')
NETWORK = ('north_star_authority', 'north_star_remote')
INTEGRITY_TOOLS = {
    'validate_repo.py', 'test_validate_repo.py', 'check_manifest.py',
    'test_check_manifest.py', 'reference_library.py', 'test_reference_library.py',
    'brain_query.py', 'test_brain_query.py', 'benchmark_brain_query.py',
    'brain_vocabulary.json', 'brain_retrieval_cases.json', 'inventory_origins.py',
    'test_inventory_origins.py', 'check_transformation.py', 'test_transformation.py',
}


def normalized_path(value):
    if not isinstance(value, str) or not value or '\0' in value:
        raise ValueError('Changed paths must be nonempty repository-relative strings')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or value != path.as_posix():
        raise ValueError('Changed paths must use canonical repository-relative Git paths')
    return value


def affected(path):
    """Return required consumer keys for one path, without consulting file existence."""
    path = normalized_path(path)
    if path.startswith(('.github/workflows/', '.github/actions/')):
        return JOBS
    if not path.startswith(WORKSPACE):
        if path in {'AGENTS.md', 'README.md', 'SEED.md', 'MANIFEST.sha256'} or path.startswith('docs/'):
            return ()
        return JOBS
    relative = path[len(WORKSPACE):]
    if relative in {'AGENTS.md', 'README.md', 'SEED.md', 'MANIFEST.sha256', 'projects/README.md',
                    'north-star/README.md', 'north-star/DESIGN.md', 'north-star/capabilities.json'}:
        return ()
    if relative.startswith(('docs/', 'registry/', 'brains/', 'knowledge/')):
        return ()
    if relative.startswith('labs/') and (relative.endswith('.md') or relative in
                                       {'labs/origins.json', 'labs/source-inventory.json'}):
        return ()
    if relative.startswith(('north-star/csharp/', 'labs/rpg-systems/', 'evidence/rpg-progression/',
                            'references/rave-master/', 'labs/economy-simulation/', 'evidence/economy-crafting/',
                            'labs/world-gameplay/', 'evidence/world-loadout/',
                            'labs/networking-persistence/', 'evidence/persistent-expedition/',
                            'labs/narrative-continuity/', 'evidence/narrative-continuity/',
                            'labs/input-timing/', 'evidence/input-timing/')):
        return ('north_star_csharp',)
    if relative.startswith('references/'):
        return ()  # Source availability and pins are owned by unconditional integrity.
    if relative.startswith('north-star/prototype/authority/'):
        return NETWORK
    if relative.startswith('north-star/prototype/'):
        # Core model, packed delivery and verification helpers cross these seams.
        # Keep this conservative until a narrower dependency is actually established.
        return PROTOTYPE
    if relative.startswith(('projects/eclipse-fair/', 'projects/cinderwatch/',
                            'evidence/eclipse-fair/', 'evidence/cinderwatch/')):
        return ('eclipse_economy',)
    if relative.startswith(('projects/veil-arena/', 'labs/combat-response/', 'evidence/combat-response/',
                            'evidence/veil-arena/')):
        return ('native_arena',)
    if relative.startswith(('projects/realtime-integration-lab/', 'projects/tokyo80s/',
                            'projects/waystone-dialogue/', 'evaluations/',
                            'evidence/realtime-chat/', 'evidence/tokyo80s/',
                            'evidence/waystone-dialogue/', 'evidence/evaluation-task/')):
        return ('chat_evaluation',)
    if relative.startswith(('projects/lich-cistern/', 'evidence/lich-cistern/', 'evidence/brain-retrieval/')):
        return ()  # Their actual format/source checks remain in unconditional integrity.
    if relative.startswith('evidence/north-star-'):
        return PROTOTYPE
    if relative == 'tools/check_calibration.py':
        return ('chat_evaluation',)
    if relative.startswith('tools/') and relative[len('tools/'):] in INTEGRITY_TOOLS:
        return ()
    if relative.endswith('.md') and relative.startswith(('labs/', 'shared/')):
        return ()
    return JOBS  # New shared tools, runtime roots and unclassified dependencies fail broad.


def classify(paths, full=False):
    paths = list(paths)
    if full or not paths:
        return dict.fromkeys(JOBS, True)
    selected = set()
    for path in paths:
        selected.update(affected(path))
    return {name: name in selected for name in JOBS}


def git_output(repo, *arguments):
    result = subprocess.run(['git', '-C', str(repo), *arguments], capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('Git scope inspection failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout


def commit_id(repo, revision):
    # Resolve before diffing so options and ambiguous/missing revisions cannot change scope.
    return git_output(repo, 'rev-parse', '--verify', '--end-of-options', revision + '^{commit}').decode('ascii').strip()


def changed_paths(repo, base, head):
    before, after = commit_id(repo, base), commit_id(repo, head)
    data = git_output(repo, 'diff', '--no-ext-diff', '--no-textconv', '--name-only', '-z',
                      '--no-renames', before, after, '--')
    # Disabling rename detection intentionally retains both the deleted and added path.
    return [name.decode('utf-8', 'surrogateescape') for name in data.split(b'\0') if name]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--base', help='Base Git commit/ref; compare against --head')
    source.add_argument('--path', action='append', help='Actual repository-relative path; repeat as needed')
    source.add_argument('--full', action='store_true', help='Run all retained consumer contracts')
    parser.add_argument('--head', help='Head Git commit/ref (default HEAD with --base)')
    parser.add_argument('--output', type=Path, help='Append fixed boolean keys to the GitHub output file')
    args = parser.parse_args(argv)
    try:
        if args.head and not args.base:
            raise ValueError('--head requires --base')
        paths = args.path or []
        if args.base and not (len(args.base) in (40, 64) and set(args.base) == {'0'}):
            workspace = Path(__file__).resolve().parents[1]
            repo = git_output(workspace, 'rev-parse', '--show-toplevel').decode('utf-8').strip()
            paths = changed_paths(repo, args.base, args.head or 'HEAD')
        result = classify(paths, full=args.full)
        if args.output:
            with args.output.open('a', encoding='utf-8') as output:
                output.write(''.join(f'{key}={str(value).lower()}\n' for key, value in result.items()))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'FAIL: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
