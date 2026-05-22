"""Import Detector — MEDIUM signal layer

Detects imports/requires in:
- Python (.py): import x, from y import z
- JavaScript/TypeScript (.js, .ts): import x, require('x')
"""

import re
from typing import Any


class ImportDetector:
    """Detects technologies from import statements"""

    def __init__(self, rules: dict[str, Any]) -> None:
        self.rules = rules

    def detect(self, file_path: str, content: str) -> list[dict[str, Any]]:
        """Detect technologies in import statements"""
        detected = []

        if file_path.endswith(".py"):
            detected = self._detect_python(content)
        elif (
            file_path.endswith(".js")
            or file_path.endswith(".ts")
            or file_path.endswith(".jsx")
            or file_path.endswith(".tsx")
        ):
            detected = self._detect_javascript(content)

        return detected

    def _detect_python(self, content: str) -> list[dict[str, Any]]:
        """Detect Python imports"""
        detected = []

        # import x
        import_pattern = r"^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)"

        # from y import z
        from_pattern = r"^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import"

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check import x
            match = re.match(import_pattern, line)
            if match:
                module = match.group(1).split(".")[0]  # Top-level module
                detected.extend(self._check_import(module))

            # Check from y import z
            match = re.match(from_pattern, line)
            if match:
                module = match.group(1).split(".")[0]
                detected.extend(self._check_import(module))

        return detected

    def _detect_javascript(self, content: str) -> list[dict[str, Any]]:
        """Detect JavaScript/TypeScript imports"""
        detected = []

        # import x from 'y'
        import_pattern = r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
        # const x = require('y')
        require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'

        for line in content.split("\n"):
            # ES6 import
            match = re.search(import_pattern, line)
            if match:
                module = match.group(1).split("/")[0]
                if module.startswith("@"):
                    # Scoped packages: @scope/name
                    parts = module.split("/")
                    if len(parts) >= 2:
                        module = f"{parts[0]}/{parts[1]}"
                        detected.extend(self._check_import(module))

            # require()
            match = re.search(require_pattern, line)
            if match:
                module = match.group(1).split("/")[0]
                if module.startswith("@"):
                    parts = module.split("/")
                    if len(parts) >= 2:
                        module = f"{parts[0]}/{parts[1]}"
                        detected.extend(self._check_import(module))

        return detected

    def _check_import(self, module: str) -> list[dict[str, Any]]:
        """Check if import matches any technology"""
        detected = []
        module_lower = module.lower()

        for tech_id, tech in self.rules.items():
            imports = [imp.lower() for imp in tech.get("imports", [])]
            if module_lower in imports:
                detected.append(
                    {
                        "technology_id": tech_id,
                        "signal_type": "import",
                        "value": module,
                    }
                )
        return detected
