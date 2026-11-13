"""Load the fictional ERP extract. Used by `python -m agritrace.ingest`."""

from __future__ import annotations

from agritrace.service import build_service


def main() -> None:
    service = build_service()
    print("ingested", service.store.stats())
    print("quality_findings", service.quality.findings)


if __name__ == "__main__":
    main()
