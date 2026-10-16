"""Exercise package rejection boundaries using the actual shipped player."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import check_linux

PACKAGE = check_linux.ROOT / 'dist/eclipse-fair-linux-0.6.0.zip'

class PackageChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='eclipse-package-check-')
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name) / 'player.zip'

    def damaged(self, mutate):
        with ZipFile(PACKAGE) as src, ZipFile(self.target, 'w') as dst:
            info = json.loads(src.read('EclipseFair/BUILD-INFO.json'))
            entries = [(copy.copy(e), src.read(e.filename)) for e in src.infolist()]
            entries = mutate(entries, info)
            for e, data in entries:
                if e.filename == 'EclipseFair/BUILD-INFO.json':
                    data = json.dumps(info).encode()
                dst.writestr(e, data)
        self.target.with_suffix('.zip.sha256').write_text(hashlib.sha256(self.target.read_bytes()).hexdigest() + '  player.zip\n')

    def test_real_delivered_bundle(self):
        self.assertTrue(check_linux.check(PACKAGE)['runtime_included'])

    def test_missing_runtime_even_with_rewritten_inventory(self):
        def mutate(entries, info):
            name = check_linux.export_linux.DATA + '/libcoreclr.so'
            del info['files_sha256'][name]
            return [(e,b) for e,b in entries if e.filename != 'EclipseFair/' + name]
        self.damaged(mutate)
        with self.assertRaisesRegex(AssertionError,'Missing runtime'):check_linux.check(self.target)

    def test_stale_source_identity(self):
        def mutate(entries, info):
            info['source_sha256']['Native/Main.cs'] = '0'*64
            return entries
        self.damaged(mutate)
        with self.assertRaisesRegex(AssertionError,'Stale'):check_linux.check(self.target)

    def test_executable_permission_required(self):
        def mutate(entries, info):
            for e,_ in entries:
                if e.filename.endswith('/eclipse-fair.x86_64'):e.external_attr=0o100644<<16
            return entries
        self.damaged(mutate)
        with self.assertRaises(AssertionError):check_linux.check(self.target)

    def test_unsafe_path_rejected_before_reading_payload(self):
        with ZipFile(self.target,'w') as z:z.writestr('../outside','bad')
        with self.assertRaises(AssertionError):check_linux.check(self.target)

if __name__ == '__main__':unittest.main()
