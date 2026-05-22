"""Keyword Detector — WEAK signal layer

Detects keywords in file content.
Keywords are weak because they often appear in:
- Comments
- Documentation
- Examples
- Tutorials

Use as fallback only.
"""

from typing import Any


class KeywordDetector:
    """Detects technologies from keywords (weak signal)"""

    def __init__(self, rules: dict[str, Any]) -> None:
        self.rules = rules

    def detect(self, content: str) -> list[dict[str, Any]]:
        detected = []
        content_lower = content.lower()

        for tech_id, tech in self.rules.items():
            for keyword in tech.get("keywords", []):
                keyword_lower = keyword.lower()
                if keyword_lower in content_lower:
                    detected.append(
                        {"technology_id": tech_id, "signal_type": "keyword", "value": keyword}
                    )

        # Deduplicate by technology_id
        seen = set()
        unique = []
        for d in detected:
            if d["technology_id"] not in seen:
                seen.add(d["technology_id"])
                unique.append(d)

        return unique
