"""Print the running example: BLE-0457 -> FAR-118 -> BIS-031 under CERT-77."""

from __future__ import annotations

from agritrace.service import build_service

QUESTIONS = [
    "Trace BIS-031 upstream",
    "Which lots are downstream of wheat lot BLE-0457?",
    "Is biscuit lot BIS-031 covered by CERT-77, and is that certificate valid on 2026-11-13?",
    "Which certificates are expired?",
    "What did the mill audit say about mixed lots?",
    "Where was OIL-009 produced and is the chain complete?",
    "What is the downstream recall impact of BLE-0457?",
]


def main() -> None:
    service = build_service()
    print("AgriTrace demo (mock LLM, in-memory graph)")
    print("Running example: wheat BLE-0457 -> flour FAR-118 -> biscuits BIS-031, certificate CERT-77")
    print(f"as_of={service.settings.as_of.isoformat()} findings={service.quality.findings}")
    for number, question in enumerate(QUESTIONS, start=1):
        result = service.ask(question, thread_id=f"demo-{number}")
        print("\n" + "=" * 72)
        print(f"Q{number}: {question}")
        print(f"status={result.status} route={result.route}")
        print(result.answer)
        print("citations:", ", ".join(item.id for item in result.citations[:12]))
        if result.status == "needs_approval":
            approved = service.ask("", thread_id=f"demo-{number}", human_decision="approve")
            print("\n-- human approves --")
            print(f"status={approved.status}")
            print(approved.answer)


if __name__ == "__main__":
    main()
