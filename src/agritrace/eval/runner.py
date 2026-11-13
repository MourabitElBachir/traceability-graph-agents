"""Score the labelled questions. Exit 1 when any case misses an expected id or phrase."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from agritrace.security.guardrails import mentioned_ids
from agritrace.service import TraceService, build_service


def load_cases() -> list[dict[str, Any]]:
    payload = json.loads(files("agritrace.eval").joinpath("dataset.json").read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = payload["cases"]
    return cases


def _blob(result: Any) -> str:
    return result.answer + "\n" + " ".join(item.id for item in result.citations)


def score_case(service: TraceService, case: dict[str, Any], index: int) -> dict[str, Any]:
    result = service.ask(str(case["question"]), thread_id=f"eval-{index}-{case['id']}")
    text = _blob(result)
    ids = set(mentioned_ids(text)) | {item.id for item in result.citations}
    missing_ids = [item for item in case.get("expect_ids") or [] if item not in ids]
    missing_phrases = [item for item in case.get("expect_phrases") or [] if item not in text]
    forbidden_ids = [item for item in case.get("forbid_ids") or [] if item in ids]
    forbidden_phrases = [item for item in case.get("forbid_phrases") or [] if item in text]
    status_ok = result.status == case.get("status", result.status)
    ok = status_ok and not missing_ids and not missing_phrases and not forbidden_ids and not forbidden_phrases
    return {
        "id": case["id"],
        "ok": ok,
        "status": result.status,
        "missing_ids": missing_ids,
        "missing_phrases": missing_phrases,
        "forbidden_ids": forbidden_ids,
        "forbidden_phrases": forbidden_phrases,
    }


def run(service: TraceService | None = None) -> list[dict[str, Any]]:
    service = service or build_service()
    return [score_case(service, case, index) for index, case in enumerate(load_cases())]


def main() -> None:
    rows = run()
    passed = sum(1 for row in rows if row["ok"])
    print(f"eval {passed}/{len(rows)}")
    for row in rows:
        mark = "ok" if row["ok"] else "FAIL"
        print(f"  {mark} {row['id']} status={row['status']}")
        if not row["ok"]:
            print(f"    missing_ids={row['missing_ids']}")
            print(f"    missing_phrases={row['missing_phrases']}")
            print(f"    forbidden_ids={row['forbidden_ids']}")
            print(f"    forbidden_phrases={row['forbidden_phrases']}")
    if passed != len(rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
