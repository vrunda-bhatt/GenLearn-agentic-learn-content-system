from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import DATA_DIR, MEMORY_PATH


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "runs").mkdir(parents=True, exist_ok=True)


@dataclass
class MemoryStore:
    path: Path = MEMORY_PATH
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path = MEMORY_PATH) -> "MemoryStore":
        ensure_data_dirs()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = {
                "version": 1,
                "runs": [],
                "failure_patterns": {},
                "topic_memory": {},
            }
        return cls(path=path, data=data)

    def summary_for_topic(self, topic: str) -> dict[str, Any]:
        topic_memory = self.data.get("topic_memory", {}).get(topic, {})
        return {
            "topic": topic,
            "common_failures": topic_memory.get("common_failures", []),
            "successful_fixes": topic_memory.get("successful_fixes", []),
            "recent_runs": [
                run for run in self.data.get("runs", []) if run.get("topic") == topic
            ][-3:],
        }

    def record_run(self, run_record: dict[str, Any]) -> None:
        runs = self.data.setdefault("runs", [])
        runs.append(run_record)
        self._update_failure_patterns(run_record)
        self._update_topic_memory(run_record)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=True), encoding="utf-8")

    def _update_failure_patterns(self, run_record: dict[str, Any]) -> None:
        patterns = self.data.setdefault("failure_patterns", {})
        for attempt in run_record.get("attempts", []):
            for criterion in attempt.get("failed_criteria", []):
                entry = patterns.setdefault(criterion, {"count": 0, "examples": []})
                entry["count"] += 1
                if len(entry["examples"]) < 5:
                    entry["examples"].append(
                        {
                            "topic": run_record.get("topic"),
                            "attempt": attempt.get("attempt_number"),
                            "root_cause": attempt.get("root_cause"),
                        }
                    )

    def _update_topic_memory(self, run_record: dict[str, Any]) -> None:
        topic = run_record.get("topic")
        if not topic:
            return
        topic_memory = self.data.setdefault("topic_memory", {}).setdefault(
            topic,
            {"common_failures": [], "successful_fixes": []},
        )
        for attempt in run_record.get("attempts", []):
            for criterion in attempt.get("failed_criteria", []):
                if criterion not in topic_memory["common_failures"]:
                    topic_memory["common_failures"].append(criterion)
            fix = attempt.get("fix_applied")
            if fix and fix not in topic_memory["successful_fixes"]:
                topic_memory["successful_fixes"].append(fix)
