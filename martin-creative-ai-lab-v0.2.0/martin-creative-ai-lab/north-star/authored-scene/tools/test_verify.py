"""Guard actual forward dependency coverage without unrelated reverse consumers."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('authored_verify', Path(__file__).with_name('verify.py'))
method = importlib.util.module_from_spec(spec)
spec.loader.exec_module(method)


class DependencyCoverage(unittest.TestCase):
    def test_actual_closure_includes_owner_not_unrelated_consumers(self):
        names = method.inputs()
        for name in ('north-star/authored-scene/Host/Room.cs',
                     'north-star/csharp/Narrative/RequestExpedition.cs',
                     'north-star/csharp/Crossing/Session.cs',
                     'north-star/csharp/Domain/Progression.cs'):
            self.assertIn(name, names)
        self.assertNotIn('north-star/csharp/Recovery/Journal.cs', names)
        self.assertNotIn('north-star/csharp/Audio/Sound.cs', names)

    def fixture(self, folder):
        root = Path(folder) / 'workspace'
        scene = root / 'north-star/authored-scene'
        csharp = root / 'north-star/csharp'
        (scene / 'Checks').mkdir(parents=True)
        (csharp / 'Narrative').mkdir(parents=True)
        (csharp / 'global.json').write_text('{}')
        (csharp / 'Narrative/SCENE.md').write_text('authored contract')
        return root, scene, csharp

    def test_external_project_reference_is_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as folder:
            root, scene, csharp = self.fixture(folder)
            (scene / 'Checks/NorthStar.AuthoredSceneChecks.csproj').write_text(
                '<Project><ItemGroup><ProjectReference Include="../../../../outside.csproj" /></ItemGroup></Project>')
            with patch.multiple(method, ROOT=root, SCENE=scene, CSHARP=csharp):
                with self.assertRaisesRegex(ValueError, 'escapes maintained'):
                    method.inputs()

    def test_explicit_wildcard_requires_inventory_instead_of_false_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root, scene, csharp = self.fixture(folder)
            (scene / 'Checks/NorthStar.AuthoredSceneChecks.csproj').write_text(
                '<Project><ItemGroup><Compile Include="../*.cs" /></ItemGroup></Project>')
            with patch.multiple(method, ROOT=root, SCENE=scene, CSHARP=csharp):
                with self.assertRaisesRegex(ValueError, 'wildcard'):
                    method.inputs()


if __name__ == '__main__':
    unittest.main()
