#!/usr/bin/env python3
"""Run exactly pinned VEA-032/R09 in an isolated location; no artistic approval.

This adapter consumes a verified R09 archive without copying historical outputs,
proposing new decisions, or requiring Unity/Arena. See README.md for boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

PINNED_ARCHIVE_SHA256 = '66b30aad1801d20efb93d68d97daaf4598840c816269af1bb89e1a558300d3ff'
PREFIX = 'NORTH_STAR_VEA_032_R09/'
SOURCES = {
    'src/vea032_calibration.py': '30ca742b59edbe0cd766f4c3fa9e3d4714e97898d569201ab9efc2a83d6c695d',
    'src/vea032_visual_diagnostics.py': 'd3d891f40a2378597c750b592b1b3cbe51a5a034dc4068a0614574d12769550d',
    'src/test_calibration.py': '2951d4728cc407537e5d38c21ba8fec358e77e739aa15e3286daeaaa6fcd837f',
    'recovered_sources/vea021/graph.py': '0703c7cadb7bacfb06c4b0769d6d573a5b79c7dccd0fa904fa9b829290e59ba1',
    'recovered_sources/northstar_vea020/render.py': '584120b0117a3bb85439fc1f81b3e136c9b2650887e86fd31da5028f539f6d8a',
    'recovered_sources/northstar_vea020/__init__.py': 'aae268c242d54d5066e84cb7e37976af64d5f7684d75766881843136cadd2071',
}
INPUT_FILES = {
    'input/VEA_032_R04_CENA_EDITAVEL.json',
    'input/VEA_032_R04_ARQUEADA.png',
    'input/VEA_032_R04_ARQUEADA.ora',
    'input/EDITORIAL_DECISIONS_R08.json',
    'input/NORTH_STAR_VEA_032_R07_DECISOES_45.json',
}
MAX_ARCHIVE = 25_000_000
MAX_UNCOMPRESSED = 35_000_000


class IntegrationError(ValueError):
    """A tested provenance, archive, output or execution restriction failed."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_archive(path: Path) -> list[zipfile.ZipInfo]:
    if not path.is_file() or path.stat().st_size > MAX_ARCHIVE:
        raise IntegrationError('MISSING_OR_OVERSIZED_R09_ARCHIVE')
    if digest(path.read_bytes()) != PINNED_ARCHIVE_SHA256:
        raise IntegrationError('R09_ARCHIVE_HASH_MISMATCH')
    with zipfile.ZipFile(path) as z:
        infos=z.infolist()
        if len(infos)>90 or sum(i.file_size for i in infos)>MAX_UNCOMPRESSED:
            raise IntegrationError('R09_ARCHIVE_LIMIT')
        if z.testzip() is not None:
            raise IntegrationError('R09_ARCHIVE_CRC')
        seen=set()
        for info in infos:
            name=info.filename
            parts=PurePosixPath(name).parts
            if (name in seen or not name.startswith(PREFIX) or
                    PurePosixPath(name).is_absolute() or '..' in parts or '\\' in name or
                    (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise IntegrationError('UNSAFE_R09_ARCHIVE_MEMBER')
            seen.add(name)
        needed=set(SOURCES)|INPUT_FILES
        if not all(PREFIX+x in seen for x in needed):
            raise IntegrationError('R09_REQUIRED_SOURCE_MISSING')
        for name,expected in SOURCES.items():
            if digest(z.read(PREFIX+name)) != expected:
                raise IntegrationError('R09_SOURCE_HASH_MISMATCH')
        return infos


def _write_selected(archive: Path, target: Path) -> None:
    with zipfile.ZipFile(archive) as z:
        for name in sorted(set(SOURCES)|INPUT_FILES):
            out=target/name
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(z.read(PREFIX+name))


def _verify_authority(root: Path) -> None:
    editorial=json.loads((root/'input/EDITORIAL_DECISIONS_R08.json').read_text(encoding='utf-8'))
    grants=json.loads((root/'input/NORTH_STAR_VEA_032_R07_DECISOES_45.json').read_text(encoding='utf-8'))
    ids=[x for lot in editorial['editorial_lots'] for x in lot['ids']]
    approved=[x['id'] for x in grants['approved']]
    if not (len(ids)==len(set(ids))==73 and len(approved)==len(set(approved))==45
            and not set(ids)&set(approved) and len(editorial['semantic_links'])==10
            and editorial['hold_ids']==[f'VEA-ART-{i:04}' for i in range(31,35)]
            and editorial['implementation_authorized_by_editorial'] is False):
        raise IntegrationError('R09_AUTHORITY_CROSSOVER')


def run(archive: Path, output: Path, python: str=sys.executable) -> dict:
    archive=archive.resolve();output=output.resolve()
    check_archive(archive)
    if output.exists():
        raise IntegrationError('OUTPUT_ALREADY_EXISTS')
    with tempfile.TemporaryDirectory(prefix='northstar-vea-r10-') as td:
        source=Path(td)
        _write_selected(archive,source)
        _verify_authority(source)
        # The pinned R09 source contains the only reviewed renderer/transaction code.
        # Run in a clean temp source tree; export only generated evidence to output.
        tests=subprocess.run([python,'-m','unittest','discover','-s','src','-p','test_calibration.py','-v'],
            cwd=source,capture_output=True,text=True,timeout=180,check=False)
        if tests.returncode:
            raise IntegrationError('R09_TESTS_FAILED: '+(tests.stdout+tests.stderr)[-2500:])
        output.mkdir(parents=True,exist_ok=False)
        (output/'R09_TESTS.log').write_text(tests.stdout+tests.stderr,encoding='utf-8')
        process=subprocess.run([python,'src/vea032_calibration.py','--input',str(source/'input'),
            '--output',str(output/'rendered')],cwd=source,capture_output=True,text=True,timeout=240,check=False)
        (output/'R09_RUN.log').write_text(process.stdout+process.stderr,encoding='utf-8')
        if process.returncode:
            raise IntegrationError('R09_RENDER_FAILED: '+(process.stdout+process.stderr)[-2500:])
        evidence=json.loads((output/'rendered/EXECUTION_EVIDENCE.json').read_text(encoding='utf-8'))
        variants=evidence.get('variants',[])
        if not (len(variants)==3 and evidence.get('approved_investigations')==45
                and evidence.get('editorial_decisions')==73 and
                evidence.get('protected_0031_0034')=='PENDING_AUTHOR' and
                evidence.get('implementation_authorization_from_editorial') is False and
                all(v.get('ora_readback')=='EXACT_MATCH' and v.get('changed_pixels_vs_baseline',0)>0 for v in variants)):
            raise IntegrationError('R09_EVIDENCE_UNEXPECTED')
        result={'schema':'northstar.vea.r10.pinned-integration.v1','archive_sha256':PINNED_ARCHIVE_SHA256,
            'origin':'VEA-032/R09','test_exit_code':tests.returncode,'tests_reported':16,
            'variants':[{'id':v['id'],'changed_pixels':v['changed_pixels_vs_baseline']} for v in variants],
            'art_decision':'NOT_EVALUATED','arena':'NOT_RUN','unity':'NOT_RUN',
            'remote_publication':'NOT_ASSERTED','editorial_not_implementation':True}
        (output/'R10_INTEGRATION.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True,type=Path,help='Pinned original R09 zip')
    parser.add_argument('--output',required=True,type=Path,help='New directory outside protected source')
    args=parser.parse_args()
    try:
        print(json.dumps(run(args.archive,args.output),indent=2))
    except (IntegrationError,OSError,ValueError,subprocess.TimeoutExpired,zipfile.BadZipFile) as exc:
        parser.exit(1,'R10_BLOCKED: '+str(exc)+'\n')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
