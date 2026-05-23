"""Tests for Normalizer"""

from datetime import datetime

import pytest

from github_profiler.aggregators import Normalizer
from github_profiler.domain import SignalType, Strength


class TestNormalizer:
    """Test normalizer transformations"""

    def test_dependency_to_strong(self) -> None:
        normalizer = Normalizer()
        signals = [
            {"technology_id": "fastapi", "signal_type": "dependency", "value": "fastapi==0.115.0"}
        ]

        evidences = normalizer.normalize(signals)

        assert len(evidences) == 1
        assert evidences[0].technology_id == "fastapi"
        assert evidences[0].signal_type == SignalType.DEPENDENCY
        assert evidences[0].strength == Strength.STRONG
        assert evidences[0].detector == "dependency_detector"
        assert evidences[0].value == "fastapi==0.115.0"

    def test_import_to_medium(self) -> None:
        normalizer = Normalizer()
        signals = [
            {
                "technology_id": "fastapi",
                "signal_type": "import",
                "value": "from fastapi import FastAPI",
            }
        ]

        evidences = normalizer.normalize(signals)

        assert len(evidences) == 1
        assert evidences[0].strength == Strength.MEDIUM
        assert evidences[0].detector == "import_detector"

    def test_path_to_medium(self) -> None:
        normalizer = Normalizer()
        signals = [{"technology_id": "docker", "signal_type": "path", "value": "Dockerfile"}]

        evidences = normalizer.normalize(signals)

        assert len(evidences) == 1
        assert evidences[0].strength == Strength.MEDIUM
        assert evidences[0].detector == "path_detector"

    def test_keyword_to_weak(self) -> None:
        normalizer = Normalizer()
        signals = [{"technology_id": "fastapi", "signal_type": "keyword", "value": "FastAPI"}]

        evidences = normalizer.normalize(signals)

        assert len(evidences) == 1
        assert evidences[0].strength == Strength.WEAK
        assert evidences[0].detector == "keyword_detector"

    def test_normalize_with_context(self) -> None:
        normalizer = Normalizer()
        signal = {
            "technology_id": "fastapi",
            "signal_type": "import",
            "value": "from fastapi import FastAPI",
        }

        evidence = normalizer.normalize_signal(signal, repo="test/repo", file_path="src/main.py")

        assert evidence.repo == "test/repo"
        assert evidence.file_path == "src/main.py"
        assert isinstance(evidence.detected_at, datetime)

    def test_unknown_signal_type(self) -> None:
        normalizer = Normalizer()

        signals = [
            {
                "technology_id": "unknown",
                "signal_type": "unknown",
                "value": "test",
            }
        ]

        with pytest.raises(ValueError):
            normalizer.normalize(signals)
