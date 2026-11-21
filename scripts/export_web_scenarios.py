"""Write the precomputed plans the web demo reads."""

from __future__ import annotations

import json
from pathlib import Path

from agritrace.optimization.web_catalog import catalog


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / "web" / "public" / "data" / "scenarios.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = catalog()
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
