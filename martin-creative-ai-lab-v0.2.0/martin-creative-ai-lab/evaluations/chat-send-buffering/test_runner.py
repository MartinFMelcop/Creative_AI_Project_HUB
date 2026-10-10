"""Exercise export boundaries and gates that can invalidate an artifact result."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("task_runner", Path(__file__).with_name("run.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class TaskRunnerTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.workspace = Path(self.scratch.name) / "candidate"
        runner.prepare(self.workspace)

    def test_export_has_only_starter_and_brief_without_reference_or_history(self):
        paths = {p.relative_to(self.workspace).as_posix()
                 for p in self.workspace.rglob("*") if p.is_file()}
        self.assertEqual(paths, {*runner.FILES, "BRIEF.md", "task-manifest.json"})
        client = (self.workspace / "public/client.js").read_bytes()
        self.assertEqual(client, runner.git_bytes(runner.BASELINE, "public/client.js"))
        self.assertNotEqual(client, (runner.PROJECT / "public/client.js").read_bytes())
        self.assertEqual(runner.read_submission(self.workspace), client)

    def test_export_never_overwrites_an_existing_workspace(self):
        user_file = self.workspace / "keep.txt"
        user_file.write_text("existing user work")
        with self.assertRaises(FileExistsError):
            runner.prepare(self.workspace)
        self.assertEqual(user_file.read_text(), "existing user work")

    def test_support_file_change_is_rejected_before_execution(self):
        (self.workspace / "server.cjs").write_text("changed server")
        record = runner.check(self.workspace)
        self.assertEqual(record["status"], "rejected")
        self.assertIn("server.cjs", record["reason"])
        self.assertEqual(record["commands"], [])

    def test_reference_or_extra_file_in_submission_is_rejected(self):
        (self.workspace / "answer.js").write_text("reference")
        self.assertEqual(runner.check(self.workspace)["gate"], "submission_scope")

    def test_missing_client_is_a_rejected_submission(self):
        (self.workspace / "public/client.js").unlink()
        self.assertEqual(runner.check(self.workspace)["status"], "rejected")

    def test_linked_client_cannot_substitute_an_external_artifact(self):
        client = self.workspace / "public/client.js"
        client.unlink()
        client.symlink_to(runner.PROJECT / "public/client.js")
        self.assertEqual(runner.check(self.workspace)["status"], "rejected")

    def test_complete_results_distinguish_acceptance_and_rejection(self):
        accepted = "# tests 17\n# pass 17\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n"
        rejected = accepted.replace("# pass 17", "# pass 15").replace("# fail 0", "# fail 2")
        self.assertEqual(runner.classify_tap(accepted, 0)[0], "accepted")
        self.assertEqual(runner.classify_tap(rejected, 1)[0], "rejected")
        self.assertEqual(runner.classify_tap(accepted, 1)[0], "inconclusive")

    def test_incomplete_or_skipped_execution_is_never_accepted(self):
        for output in ("", "# tests 0\n# pass 0\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n",
                       "# tests 17\n# pass 16\n# fail 0\n# cancelled 0\n# skipped 1\n# todo 0\n"):
            with self.subTest(output=output):
                self.assertEqual(runner.classify_tap(output, 0)[0], "inconclusive")


if __name__ == "__main__":
    unittest.main()
