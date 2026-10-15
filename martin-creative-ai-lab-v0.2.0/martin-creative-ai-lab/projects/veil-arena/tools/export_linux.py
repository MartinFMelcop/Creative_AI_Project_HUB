#!/usr/bin/env python3
"""Export the actual Godot game with the verified official Linux release template."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_SHA = '2c78919325d7f29fa7607287c7c1eeac367ea4c94e7b8b6f5f4c6b20492f73d0'
ARCHIVE_SHA = '3fbe2c0e2dec9d537ab9ec97bcf8da91dcf23357fc51f67092dd068d839290a8'


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def run_engine(command, env):
    result = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end='')
    # Godot can return zero after a script parse failure during import.
    if result.returncode or 'SCRIPT ERROR:' in result.stdout or 'ERROR:' in result.stdout:
        raise RuntimeError('Godot import/export failed; no distribution was published.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--templates', type=Path, help='Official 4.6.3 standard TPZ; full published digest is checked.')
    group.add_argument('--template', type=Path, help='Already extracted official linux_release.x86_64; exact digest is checked.')
    p.add_argument('--godot', default='godot')
    p.add_argument('--output', type=Path, default=ROOT/'dist/veilbreak-linux-0.6.0.zip')
    args = p.parse_args()
    engine = shutil.which(args.godot)
    if not engine:
        p.error('Godot executable unavailable.')
    version = subprocess.check_output([engine, '--version'], text=True).strip()
    if version != '4.6.3.stable.official.7d41c59c4':
        p.error('Use the pinned standard Godot 4.6.3 editor.')
    with tempfile.TemporaryDirectory(prefix='veilbreak-export-') as scratch:
        work = Path(scratch)
        if args.templates:
            if digest(args.templates) != ARCHIVE_SHA:
                p.error('Official export-template archive digest mismatch.')
            with zipfile.ZipFile(args.templates) as z:
                template = work/'linux_release.x86_64'
                template.write_bytes(z.read('templates/linux_release.x86_64'))
        else:
            template = args.template.resolve()
        if digest(template) != TEMPLATE_SHA:
            p.error('Official Linux release-template digest mismatch.')
        # A fresh staging project avoids modifying the maintained preset or using its import cache.
        stage = work/'project'
        stage.mkdir()
        for name in ['project.godot', 'arena.tscn', 'arena.gd', 'sound.gd', 'motion.gd', 'controls.gd']:
            shutil.copyfile(ROOT/name, stage/name)
            uid = ROOT/(name+'.uid')
            if uid.exists():
                shutil.copyfile(uid, stage/uid.name)
        shutil.copytree(ROOT/'media', stage/'media', ignore=shutil.ignore_patterns('masters'))
        preset = (ROOT/'export_presets.cfg').read_text()
        preset += '\ncustom_template/release='+json.dumps(str(template))+'\ndebug/export_console_wrapper=0\n'
        (stage/'export_presets.cfg').write_text(preset)
        env = os.environ.copy()
        for key, folder in [('XDG_DATA_HOME','data'), ('XDG_CONFIG_HOME','config'), ('XDG_CACHE_HOME','cache')]:
            env[key] = str(work/folder)
        bundle = work/'Veilbreak'
        bundle.mkdir()
        run_engine([engine,'--headless','--path',str(stage),'--editor','--import','--quit'], env)
        run_engine([engine,'--headless','--path',str(stage),'--export-release','Linux',str(bundle/'veilbreak.x86_64')], env)
        if not (bundle/'veilbreak.x86_64').is_file() or not (bundle/'veilbreak.pck').is_file():
            p.error('The engine did not produce the executable and resource pack.')
        for name in ['GODOT-LICENSE.txt','GODOT-COPYRIGHT.txt']:
            shutil.copyfile(ROOT/'third-party'/name, bundle/name)
        shutil.copyfile(ROOT/'media/provenance.json', bundle/'ASSET-PROVENANCE.json')
        (bundle/'README.txt').write_text('''Veilbreak 0.6.0 — The Bell Warden

Linux x86_64 desktop prototype. Extract the entire Veilbreak folder, then run
./veilbreak.x86_64 (or open it from your file manager). Keep veilbreak.pck beside it.
Godot, .NET, Python, Node and the source checkout are not required to play.
Your operating system still needs a display/audio stack and OpenGL 3.3 support.
If an archive tool drops the executable permission: chmod +x veilbreak.x86_64

Keyboard: WASD/arrows move; J blade; K seal; L parry; Space dodge; Enter begin/resume/restart;
Escape pause; F1 tactics; M sound. P opens practice from menus or leaves a drill.
Close the window to exit.
Mapped gamepad: left stick/D-pad move; west (X) blade; north (Y) seal; LB parry; east (B) dodge;
south (A) begin/resume/next take/restart; Start pause; Back tactics; RB sound; R3 practice.
The blade/seal aim toward the Warden when preparation begins. Press per action;
holding a combat button does not repeat. Controller loss pauses; resume explicitly.
Parry close sweeps within 110px: guard is live 60-180ms after pressing L/LB.
It costs 20 resolve; success recovers 8 and opens the Warden for a 1.2s counter.
A missed guard recovers until 380ms. Charge, wave and violet echo bypass guard.

Sweep practice repeats the actual phase-one close sweep, stopping for review.
Time L/LB then land J/X during the real opening; costs and collision are unchanged.
Early/late/out-of-range guards and dodging do not count as a clean parry + counter.
Enter/A starts another take; P/R3 leaves practice for the title/full trial.
Practice is not a trial victory or evidence of human learning.

This is an evaluation prototype. Physical controller models, other platforms,
independent enjoyment/accessibility and commercial readiness remain unverified.
Godot and its third-party notices accompany the engine. ASSET-PROVENANCE.json
records AI-generated paintings and original synthesized audio; no new project
license, exclusive rights or commercial clearance is granted by this package.
Source and author context: https://github.com/MartinFMelcop/Creative_AI_Project_HUB
''')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix('.zip.tmp')
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for file in sorted(bundle.iterdir()):
                info = zipfile.ZipInfo('Veilbreak/'+file.name, (1980,1,1,0,0,0))
                info.create_system = 3
                info.external_attr = (0o100755 if file.suffix=='.x86_64' else 0o100644)<<16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, file.read_bytes(), compresslevel=9)
        temporary.replace(args.output)
        args.output.with_suffix('.zip.sha256').write_text(digest(args.output)+'  '+args.output.name+'\n')
        print('EXPORTED', args.output, args.output.stat().st_size, 'bytes; official runtime and actual game resources.')


if __name__ == '__main__':
    main()
