"""Rules Loader — load and validate detection rules from JSON"""

import json
from pathlib import Path
from typing import Any


class RulesLoader:
    """Loads technology detection rules from JSON"""

    def __init__(self, rules_path: Path = Path("rules/technologies.json")):
        self.rules_path = rules_path
        self._rules: dict[str, Any] | None = None

    def load(self) -> dict[str, Any]:
        """Load rules from JSON file"""
        if self._rules is None:
            with open(self.rules_path) as f:
                self._rules = json.load(f)
        return self._rules

    def get_technology(self, tech_id: str) -> dict[str, Any] | None:
        """Get rules for specific technology"""
        rules = self.load()
        return rules.get(tech_id)

    def get_all_technologies(self) -> list[str]:
        """Get all technology IDs"""
        rules = self.load()
        return list(rules.keys())
