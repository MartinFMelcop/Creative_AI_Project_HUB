#!/usr/bin/env python3
"""Read-only audit for the finite author-supplied P08 V6 archive; never executes it."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
from zipfile import ZipFile

archive, output = map(Path, sys.argv[1:])
sha = lambda data: hashlib.sha256(data).hexdigest()
root = 'P08_AUDIO_RESEARCH_V6/'
with ZipFile(archive) as z:
    entries = z.infolist()
    assert sum(i.file_size for i in entries) < 100 * 1024 * 1024
    names = set()
    folded = set()
    files = {}
    for item in entries:
        name = item.filename
        p = PurePosixPath(name)
        assert not p.is_absolute() and '..' not in p.parts
        assert '\\' not in name and ':' not in name and '\x00' not in name
        assert name.rstrip('/') == p.as_posix() and name.startswith(root)
        assert name not in names and name.casefold() not in folded
        names.add(name); folded.add(name.casefold())
        mode = item.external_attr >> 16
        kind = stat.S_IFMT(mode)
        assert not (item.flag_bits & 1)
        assert kind in (0, stat.S_IFDIR if item.is_dir() else stat.S_IFREG)
        if not item.is_dir():
            data = z.read(item)
            assert len(data) == item.file_size
            files[name[len(root):]] = {'bytes': len(data), 'sha256': sha(data), 'mode': mode}
    assert z.testzip() is None
    manifest_name = 'evidence/MANIFEST_SHA256.txt'
    declared = {}
    for line in z.read(root + manifest_name).decode().splitlines():
        digest, name = line.split('  ', 1)
        assert name not in declared and len(digest) == 64
        declared[name] = digest
    assert set(declared) == set(files) - {manifest_name}
    assert all(files[n]['sha256'] == h for n, h in declared.items())
    inventory = json.loads(z.read(root + 'governance/WHOLE_PACKAGE_MEDIA_INVENTORY.json'))
    media = {n: v for n, v in files.items() if Path(n).suffix.lower() in ('.wav', '.mid', '.midi')}
    rights = {row['path']: row for row in inventory['assets']}
    assert len(rights) == len(inventory['assets']) == len(media) == 48
    assert set(rights) == set(media)
    assert all(rights[n]['sha256'] == v['sha256'] for n, v in media.items())
    assert all(row['distribution'] == 'RESEARCH_REVIEW_ONLY' and row['rights_status'] == 'UNVERIFIED' for row in rights.values())
result = {
    'schema': 'p08.finite-archive-readonly-audit.v1',
    'archive_name': archive.name, 'bytes': archive.stat().st_size,
    'sha256': sha(archive.read_bytes()), 'root': root.rstrip('/'),
    'files': len(files), 'manifest_entries': len(declared),
    'crc_paths_types_encryption_duplicates_manifest_and_media_identity': 'PASS',
    'media': {'wav': sum(n.endswith('.wav') for n in media), 'midi': sum(n.endswith(('.mid', '.midi')) for n in media), 'publicly_cleared': 0},
    'archive_changed': False,
    'scope': 'Read-only rerun confirms the same inventory used by the earlier isolated extraction. No script is executed and no media is published by this audit.'
}
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
