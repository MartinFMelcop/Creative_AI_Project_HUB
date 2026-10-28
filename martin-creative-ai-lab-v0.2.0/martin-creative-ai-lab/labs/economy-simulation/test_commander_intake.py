"""Adversarial archive boundaries for the non-executing research intake."""
import importlib.util, io, pathlib, stat, tempfile, unittest, zipfile
spec=importlib.util.spec_from_file_location('commander_intake',pathlib.Path(__file__).with_name('commander-intake.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ArchiveBoundary(unittest.TestCase):
    def inspect(self,name='safe/a.txt',mode=stat.S_IFREG|0o644,repeat=False):
        with tempfile.TemporaryDirectory() as td:
            path=pathlib.Path(td)/'input.zip'
            with zipfile.ZipFile(path,'w') as z:
                i=zipfile.ZipInfo(name);i.external_attr=mode<<16;z.writestr(i,b'content')
                if repeat:z.writestr(name,b'other')
            return m.inspect_archive(path)
    def test_normal_file(self):self.assertEqual(self.inspect()[0]['member_count'],1)
    def test_no_execution(self):self.assertEqual(self.inspect('run.py')[1]['run.py'],b'content')
    def test_parent_traversal(self):
        with self.assertRaises(ValueError):self.inspect('../escape')
    def test_absolute(self):
        with self.assertRaises(ValueError):self.inspect('/escape')
    def test_windows_drive(self):
        with self.assertRaises(ValueError):self.inspect('C:/escape')
    def test_windows_separator(self):
        with self.assertRaises(ValueError):self.inspect('safe\\escape')
    def test_symlink(self):
        with self.assertRaises(ValueError):self.inspect('link',stat.S_IFLNK|0o777)
    def test_special(self):
        with self.assertRaises(ValueError):self.inspect('fifo',stat.S_IFIFO|0o644)
    def test_duplicate(self):
        with self.assertRaises(ValueError):self.inspect(repeat=True)
    def test_dot_segment(self):
        with self.assertRaises(ValueError):self.inspect('safe/./a')
    def test_corrupt_archive(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'bad.zip';p.write_bytes(b'not zip')
            with self.assertRaises(zipfile.BadZipFile):m.inspect_archive(p)
if __name__=='__main__':unittest.main()
