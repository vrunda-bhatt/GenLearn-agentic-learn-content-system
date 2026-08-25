from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
MEMORY_PATH = DATA_DIR / "memory.json"
RUNS_DIR = DATA_DIR / "runs"
PROMPT_VERSION = "2026-08-26.v1"
EVALUATOR_VERSION = "2026-08-26.v1"
MAX_RETRIES = 2
