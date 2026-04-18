from __future__ import annotations

import re
import time
from pathlib import Path


class PromptStore:
    def __init__(self, repo_root: Path) -> None:
        self.prompts_dir = repo_root / "agents"

    def save_enhanced_prompt(self, title: str, content: str, target_file: str = "") -> str:
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        file_name = target_file.strip() or self._slugify(title) + ".agents.md"
        if not file_name.endswith(".md"):
            file_name = file_name + ".md"
        output_path = self.prompts_dir / file_name
        output_path.write_text(content, encoding="utf-8")
        return str(output_path)

    def save_enhanced_prompt_if_better(
        self,
        *,
        title: str,
        content: str,
        target_file: str = "",
        min_improvement: float = 2.0,
        min_score: float = 45.0,
        cooldown_seconds: int = 0,
    ) -> dict:
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        file_name = target_file.strip() or self._slugify(title) + ".agents.md"
        if not file_name.endswith(".md"):
            file_name = file_name + ".md"
        output_path = self.prompts_dir / file_name

        new_score = self._score_prompt_quality(content)
        result = {
            "file": str(output_path),
            "new_score": round(new_score, 2),
            "old_score": None,
            "improvement": None,
            "saved": False,
            "decision": "skipped",
            "reason": "",
        }

        if new_score < min_score:
            result["reason"] = f"New prompt score {new_score:.2f} below minimum {min_score:.2f}."
            return result

        if output_path.exists():
            if cooldown_seconds > 0:
                age_seconds = time.time() - output_path.stat().st_mtime
                if age_seconds < cooldown_seconds:
                    remaining = int(cooldown_seconds - age_seconds)
                    result["reason"] = (
                        f"Prompt is in cooldown. Retry after {remaining} seconds."
                    )
                    result["cooldown_remaining_seconds"] = max(0, remaining)
                    return result

            old_content = output_path.read_text(encoding="utf-8")
            old_score = self._score_prompt_quality(old_content)
            improvement = new_score - old_score
            result["old_score"] = round(old_score, 2)
            result["improvement"] = round(improvement, 2)
            if improvement < min_improvement:
                result["reason"] = (
                    f"Improvement {improvement:.2f} is below threshold {min_improvement:.2f}."
                )
                return result

        output_path.write_text(content, encoding="utf-8")
        result["saved"] = True
        result["decision"] = "saved"
        result["reason"] = "Prompt passed quality gate and was persisted."
        return result

    def _slugify(self, text: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
        return cleaned or "enhanced-agent"

    def _score_prompt_quality(self, text: str) -> float:
        normalized = text.strip()
        if not normalized:
            return 0.0

        score = 0.0
        lowered = normalized.lower()
        words = re.findall(r"\b\w+\b", normalized)
        word_count = len(words)

        if normalized.startswith("---") and normalized.count("---") >= 2:
            score += 15
        if "description:" in lowered:
            score += 8
        if "tools:" in lowered:
            score += 8

        sections = [
            "mission",
            "goals",
            "deliverables",
            "workflow",
            "definition of done",
            "rules",
            "constraints",
            "acceptance criteria",
        ]
        for section in sections:
            if section in lowered:
                score += 5

        if word_count < 40:
            score += 5
        elif word_count < 120:
            score += 11
        elif word_count < 900:
            score += 16
        else:
            score += 10

        action_terms = [
            "must",
            "should",
            "validate",
            "return",
            "risks",
            "next action",
            "test",
            "acceptance",
            "scope",
            "objective",
        ]
        action_hits = sum(1 for term in action_terms if term in lowered)
        score += min(12, action_hits * 1.5)

        placeholders = ["tbd", "todo", "<", ">", "lorem ipsum"]
        placeholder_hits = sum(1 for token in placeholders if token in lowered)
        if placeholder_hits:
            score -= min(18, placeholder_hits * 3)

        return max(0.0, min(100.0, score))
