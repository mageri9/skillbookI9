"""Evidence Model — normalized signals with strength

Evidence = Signal + Strength + Detector
No float confidence scores, only literals
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .signal import SignalType


class Strength(Enum):
    """Evidence strength — deterministic categories only"""

    STRONG = "strong"  # dependency declaration
    MEDIUM = "medium"  # import statement
    WEAK = "weak"  # keyword match


@dataclass(frozen=True)
class Evidence:
    """Normalized evidence for aggregation"""

    technology_id: str
    signal_type: SignalType  # import, dependency, path, keyword
    strength: Strength
    detector: str  # which detector found this: "import_detector", etc.
    repo: str
    file_path: str
    value: str  # raw value: "fastapi==0.115", "from fastapi import FastAPI"
    detected_at: datetime  # when detection occurred

    def to_dict(self) -> dict[str, Any]:
        return {
            "technology_id": self.technology_id,
            "signal_type": self.signal_type,
            "strength": self.strength.value,
            "detector": self.detector,
            "repo": self.repo,
            "file_path": self.file_path,
            "value": self.value,
            "detected_at": self.detected_at.isoformat(),
        }
