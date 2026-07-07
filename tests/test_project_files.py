from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class ProjectFileTests(unittest.TestCase):
    def test_workflow_pushes_on_master_branch(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "gladosCheck.yml").read_text(encoding="utf-8")

        self.assertIn("branches: [ master ]", workflow)
        self.assertNotIn("branches: [ main ]", workflow)

    def test_docs_and_workflow_do_not_reference_railgun(self):
        for relative_path in ["README.md", ".github/workflows/gladosCheck.yml"]:
            content = (REPO_ROOT / relative_path).read_text(encoding="utf-8").lower()

            self.assertNotIn("railgun", content)


if __name__ == "__main__":
    unittest.main()
