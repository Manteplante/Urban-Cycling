from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "04_app"

# Guardrails: app code must not depend on silver layer access.
FORBIDDEN_PATTERNS = {
    r"02_data[/\\]silver": "Direct silver path reference",
    r"\bSILVER_PATH\b": "Silver path constant usage",
    r"\bload_silver\s*\(": "Silver loader call",
    r"from\s+services\.load_data\s+import": "Legacy load_data import",
    r"import\s+services\.load_data\b": "Legacy load_data module import",
}


def main() -> int:
    offenders: list[tuple[str, int, str, str]] = []

    for path in sorted(APP_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern, reason in FORBIDDEN_PATTERNS.items():
                if re.search(pattern, line, flags=re.IGNORECASE):
                    rel = path.relative_to(PROJECT_ROOT).as_posix()
                    offenders.append((rel, lineno, reason, line.strip()))

    if not offenders:
        print("OK: 04_app is gold-only (no silver access patterns found).")
        return 0

    print("ERROR: Found app code that bypasses gold-only data access:")
    for rel, lineno, reason, line in offenders:
        print(f"- {rel}:{lineno} | {reason} | {line}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
