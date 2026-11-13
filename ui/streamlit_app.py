"""Small UI over the same service the API uses. Run: streamlit run ui/streamlit_app.py."""

from __future__ import annotations

import streamlit as st

from agritrace.service import TraceService, build_service

SAMPLES = [
    "Trace BIS-031 upstream",
    "Which lots are downstream of wheat lot BLE-0457?",
    "Is biscuit lot BIS-031 covered by CERT-77, and is that certificate valid on 2026-11-13?",
    "Which certificates are expired?",
    "What did the mill audit say about mixed lots?",
    "What is the downstream recall impact of BLE-0457?",
]


@st.cache_resource
def service() -> TraceService:
    return build_service()


def main() -> None:
    st.set_page_config(page_title="AgriTrace", layout="wide")
    st.title("AgriTrace")
    st.caption("Fictional agrifood chain: wheat BLE-0457 → flour FAR-118 → biscuits BIS-031, certificate CERT-77.")
    engine = service()
    actors = ["regulator"] + [row.id + " — " + row.name for row in engine.store.require_index().dataset.actors]
    choice = st.selectbox("Act as", actors)
    actor_id = "" if choice == "regulator" else choice.split(" — ")[0]
    question = st.text_input("Question", SAMPLES[0])
    for sample in SAMPLES:
        if st.button(sample):
            question = sample
    if st.button("Ask", type="primary"):
        principal = engine.principal_from_actor(actor_id or "regulator")
        result = engine.ask(question, thread_id=f"ui-{actor_id or 'regulator'}", principal=principal)
        st.session_state["result"] = result.model_dump()
    result = st.session_state.get("result")
    if not result:
        return
    st.write(f"Status: **{result['status']}** · route `{result['route']}`")
    st.code(result["answer"])
    st.write("Citations: " + ", ".join(item["id"] for item in result["citations"][:16]))
    if result["status"] == "needs_approval":
        column_a, column_b = st.columns(2)
        if column_a.button("Approve recall"):
            follow = engine.ask(
                "",
                thread_id=result["thread_id"],
                principal=engine.principal_from_actor(actor_id or "regulator"),
                human_decision="approve",
            )
            st.session_state["result"] = follow.model_dump()
            st.rerun()
        if column_b.button("Reject recall"):
            follow = engine.ask(
                "",
                thread_id=result["thread_id"],
                principal=engine.principal_from_actor(actor_id or "regulator"),
                human_decision="reject",
            )
            st.session_state["result"] = follow.model_dump()
            st.rerun()


if __name__ == "__main__":
    main()
else:
    main()
