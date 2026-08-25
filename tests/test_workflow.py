from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GenLearnWorkflowTests(unittest.TestCase):
    def _run_cli(self, *args: str) -> dict:
        env = os.environ.copy()
        env.pop("GENLEARN_LLM_BASE_URL", None)
        env.pop("GENLEARN_LLM_API_KEY", None)
        env.pop("GENLEARN_LLM_MODEL", None)
        with tempfile.TemporaryDirectory() as temp_dir:
            env["GENLEARN_DATA_DIR"] = temp_dir
            completed = subprocess.run(
                [sys.executable, "-m", "genlearn.cli", *args],
                cwd=PROJECT_ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(completed.stdout)

    def test_default_run_passes_without_llm_env(self) -> None:
        result = self._run_cli("--topic", "Introduction to RAG")
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["inject_fault"])
        self.assertTrue(result["claims"])
        self.assertEqual(result["evaluation"]["rubric"]["source"], "deterministic")

    def test_fault_injection_repairs_and_passes_without_llm_env(self) -> None:
        result = self._run_cli("--topic", "Introduction to RAG", "--inject-fault")
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["inject_fault"])
        self.assertGreaterEqual(len(result["rejection_log"]), 1)
        self.assertEqual(result["evaluation"]["fact_check"]["passed"], True)
        self.assertEqual(result["evaluation"]["hard_validation"]["passed"], True)
        self.assertEqual(result["evaluation"]["rubric"]["passed"], True)


if __name__ == "__main__":
    unittest.main()
