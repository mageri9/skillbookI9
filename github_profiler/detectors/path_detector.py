"""Path Detector — MEDIUM signal layer

Detects technologies from file paths/filenames:
- Dockerfile, docker-compose.yml
- manage.py (Django)
- pytest.ini (pytest)
- *.py (Python language)
"""

import fnmatch
from typing import Any


class PathDetector:
    """Detects technologies from file paths"""

    def __init__(self, rules: dict[str, Any]) -> None:
        self.rules = rules

    def detect(self, file_path: str) -> list[dict[str, Any]]:
        detected = []

        for tech_id, tech in self.rules.items():
            for pattern in tech.get("paths", []):
                if fnmatch.fnmatch(file_path, pattern):
                    detected.append(
                        {
                            "technology_id": tech_id,
                            "signal_type": "path",
                            "value": pattern,
                            "matched_path": file_path,
                        }
                    )

        return detected
