from pathlib import Path
import unittest


class ScaffoldingLayoutTest(unittest.TestCase):
    def test_key_paths_exist(self) -> None:
        root = Path(__file__).resolve().parent.parent
        expected_paths = [
            root / 'mobile' / 'lib' / 'main.dart',
            root / 'server' / 'app' / 'main.py',
            root / 'shared' / 'models' / 'receipt_submission.json',
            root / 'templates' / 'reimbursements' / 'excel',
            root / 'docs' / 'architecture_overview.md',
            root / 'docs' / 'setup.md',
        ]

        for path in expected_paths:
            self.assertTrue(path.exists(), msg=f'Missing expected scaffold path: {path}')


if __name__ == '__main__':
    unittest.main()
