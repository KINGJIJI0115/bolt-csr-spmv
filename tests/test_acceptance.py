"""Run with python3 -O tests/test_acceptance.py; checks stay active under -O."""
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('course_run', ROOT / 'scripts/run.py')
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)

class AcceptanceTests(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(entry.acceptance_status(['a'], []), 'validated')
        self.assertEqual(entry.acceptance_status(['a'], ['a']), 'needs_review')
        self.assertEqual(entry.acceptance_status([], []), 'no_candidate_selected')

    def test_corrupt_input_rejected_before_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'input').write_bytes(b'corrupt')
            (root / 'content-manifest.json').write_text(json.dumps({'input': '0' * 64}))
            with mock.patch.object(entry, 'ROOT', root), mock.patch('sys.argv', ['run.py', 'verify']), mock.patch.object(entry.subprocess, 'run') as child:
                with self.assertRaisesRegex(RuntimeError, 'input'):
                    entry.main()
                child.assert_not_called()

if __name__ == '__main__':
    unittest.main()
